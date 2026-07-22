"""Append-only atomic store proof (VRF-02).

Every test writes to a tmp_path corpus (the real repo corpus is NEVER touched).
Proves:

  * a valid record appends (file created, one record) and a second valid record
    appends without disturbing the prefix;
  * nothing enters unverified — a record marked verified=False, or a structurally
    invalid (mutant) record, RAISES and leaves the corpus file byte-unchanged;
  * append-only prefix-immutability — tampering with an already-stored record on
    disk makes the next append RAISE (the prefix is re-verified against each
    record's own frozen H_edges_sha256);
  * atomicity — the write path uses tempfile + os.fsync + os.replace: a failure
    mid-write leaves the prior file intact and no temp file behind.
"""
import json
import os
import random

import pytest

from alpha2.corpus import store
from alpha2.corpus.schema import build_record, provenance_seed
from alpha2.corpus.store import append_certificate
from alpha2.corpus.verifier import VerificationError
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.witness import extract_witness

D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]
D3_INTERIM_MODEL = [
    [2, 20], [4, 7], [8, 18], [9, 13], [12, 27], [16, 22], [17, 24], [19, 29],
    [26, 28], [0], [1], [3], [10], [11], [21], [23],
]


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _record(seed, model, method="heuristic", omega_G=None):
    n = 31
    adj, _ = triangle_free_process(n, random.Random(seed))
    M, U, nu = extract_witness(adj, n)
    return build_record(
        provenance=provenance_seed(
            "triangle_free_process_complement", n, seed,
            "Bohman uniform triangle-free process",
        ),
        H_edges=_h_edges(adj, n),
        nu_H=nu,
        chi_G=n - nu,
        omega_G=omega_G,
        model_branch_sets=model,
        matching_M=M,
        tutte_berge_U=U,
        method=method,
    )


def test_append_valid_creates_file_with_one_record(tmp_path):
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["provenance"]["seed"] == 1


def test_second_append_preserves_prefix(tmp_path):
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)
    first = json.loads(path.read_text())[0]
    append_certificate(
        _record(137, D3_INTERIM_MODEL, "exact ILP (CBC): had_2(G)=17", omega_G=14),
        path=path,
    )
    data = json.loads(path.read_text())
    assert len(data) == 2
    assert data[0] == first  # prefix byte-identical
    assert data[1]["provenance"]["seed"] == 137


def test_unverified_record_refused_file_unchanged(tmp_path):
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)
    before = path.read_text()

    bad = _record(137, D3_INTERIM_MODEL, "exact ILP (CBC): had_2(G)=17", omega_G=14)
    bad["verified"] = False
    with pytest.raises(VerificationError):
        append_certificate(bad, path=path)
    assert path.read_text() == before  # nothing entered


def test_mutant_record_refused_file_unchanged(tmp_path):
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)
    before = path.read_text()

    mutant = _record(137, D3_INTERIM_MODEL, "exact ILP (CBC): had_2(G)=17", omega_G=14)
    # Overlap two branch sets -> verify_model_record must raise "not disjoint".
    mutant["model_branch_sets"][0] = list(mutant["model_branch_sets"][1])
    with pytest.raises(VerificationError):
        append_certificate(mutant, path=path)
    assert path.read_text() == before


def test_prefix_immutability_refuses_tampered_prior_record(tmp_path):
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)

    # Tamper with the already-stored record's integrity hash on disk.
    data = json.loads(path.read_text())
    data[0]["H_edges_sha256"] = "0" * 64
    path.write_text(json.dumps(data))

    with pytest.raises(VerificationError):
        append_certificate(_record(137, D3_INTERIM_MODEL,
                                   "exact ILP (CBC): had_2(G)=17", omega_G=14),
                           path=path)


def test_cr02_coherent_record_substitution_refused(tmp_path):
    """CR-02: swapping a prior record for a DIFFERENT but individually-valid cert
    must be detected and the next append REFUSED.

    Re-verifying self-consistency alone cannot catch this: the substitute cert
    re-verifies against itself. The per-record hash chain (chain_sha256) is what
    makes the substitution detectable -- record 0's recomputed chain diverges from
    what any subsequent state expects, so the append RAISES.
    """
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)

    # Wholesale-swap record 0 on disk for a different, individually-valid cert
    # (different seed, graph, model, provenance -- everything).
    rec137 = _record(137, D3_INTERIM_MODEL, "exact ILP (CBC): had_2(G)=17", omega_G=14)
    path.write_text(json.dumps([rec137]))

    with pytest.raises(VerificationError):
        append_certificate(_record(1, D2_MODEL), path=path)


def test_atomic_write_leaves_no_temp_and_survives_failure(tmp_path, monkeypatch):
    path = tmp_path / "corpus.json"
    append_certificate(_record(1, D2_MODEL), path=path)
    good = path.read_text()

    # No stray temp files after a successful append.
    leftovers = [p for p in os.listdir(tmp_path) if p != "corpus.json"]
    assert leftovers == [], leftovers

    # Simulate a crash mid-write: json.dump raises -> prior file intact, temp gone.
    def boom(*a, **k):
        raise OSError("simulated crash mid-write")

    monkeypatch.setattr(store.json, "dump", boom)
    with pytest.raises(OSError):
        append_certificate(_record(137, D3_INTERIM_MODEL,
                                   "exact ILP (CBC): had_2(G)=17", omega_G=14),
                           path=path)
    assert path.read_text() == good  # os.replace never ran -> old content intact
    leftovers = [p for p in os.listdir(tmp_path) if p != "corpus.json"]
    assert leftovers == [], leftovers  # temp unlinked on failure
