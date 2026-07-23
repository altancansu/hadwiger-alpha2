"""Append-only CDM corpus store (POOL-0) — mirrors tests/test_store_append_only.py.

Every test writes to a `tmp_path` corpus; the real `paths.CDM_CORPUS` and the frozen
296-instance had_2 corpus are NEVER touched (T-7-01). Proves the five store
invariants against `alpha2.pool.cdm.store.append_certificate`:

  * valid-append creates the file with one record;
  * a second valid append preserves the prefix byte-for-byte (`data[0] == first`);
  * an unverified / mutant record is REFUSED and the file is byte-unchanged;
  * prefix-immutability — tampering with a stored record makes the next append raise;
  * atomicity — a crash mid-write leaves the prior file intact and no temp behind.

Two DISTINCT valid CDM records are embedded (G = C5 and G = complement('ECxo'),
both with a brute-verified connected dominating matching). All imports of
`alpha2.pool.cdm.*` are function-local so `--collect-only` stays clean; RED until
07-03 lands the store + verifier legs.
"""
import hashlib
import json

import pytest


def _sha(h_edges):
    canon = json.dumps(
        sorted([min(a, b), max(a, b)] for a, b in h_edges), separators=(",", ":")
    )
    return hashlib.sha256(canon.encode()).hexdigest()


def _record(n, graph6, h_edges, matching_M, complement_connected=True):
    return {
        "provenance": {"kind": "graph6", "family": "mtf_complement", "n": n, "graph6": graph6},
        "H_edges": [list(e) for e in h_edges],
        "H_edges_sha256": _sha(h_edges),
        "matching_M": [list(e) for e in matching_M],
        "invariants": {"n": n, "complement_connected": complement_connected, "cdm": True},
        "verified": True,
        "method": "dfs reference + cp-sat cross-check (CDM)",
    }


# Record 1 — G = C5, H = complement(C5); M = [(0,1),(2,3)] (connected, dominating).
def _rec_c5():
    return _record(5, "DUW", [[0, 2], [0, 3], [1, 3], [1, 4], [2, 4]], [[0, 1], [2, 3]])


# Record 2 — G = complement('ECxo') on 6 vertices; M = [(0,1),(3,4)] (brute-verified).
def _rec_ecxo():
    return _record(
        6, "ECxo",
        [[0, 3], [0, 4], [1, 4], [1, 5], [2, 4], [2, 5], [3, 5]],
        [[0, 1], [3, 4]],
    )


def test_append_valid_creates_file_with_one_record(tmp_path):
    from alpha2.pool.cdm.store import append_certificate  # RED until 07-03

    path = tmp_path / "cdm_corpus.json"
    append_certificate(_rec_c5(), path=path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["provenance"]["graph6"] == "DUW"


def test_second_append_preserves_prefix(tmp_path):
    from alpha2.pool.cdm.store import append_certificate

    path = tmp_path / "cdm_corpus.json"
    append_certificate(_rec_c5(), path=path)
    first = json.loads(path.read_text())[0]
    append_certificate(_rec_ecxo(), path=path)
    data = json.loads(path.read_text())
    assert len(data) == 2
    assert data[0] == first  # prefix byte-identical
    assert data[1]["provenance"]["graph6"] == "ECxo"


def test_unverified_record_refused_file_unchanged(tmp_path):
    from alpha2.pool.cdm.store import append_certificate
    from alpha2.pool.cdm.verifier import VerificationError

    path = tmp_path / "cdm_corpus.json"
    append_certificate(_rec_c5(), path=path)
    before = path.read_text()

    bad = _rec_ecxo()
    bad["verified"] = False
    with pytest.raises(VerificationError):
        append_certificate(bad, path=path)
    assert path.read_text() == before


def test_mutant_record_refused_file_unchanged(tmp_path):
    from alpha2.pool.cdm.store import append_certificate
    from alpha2.pool.cdm.verifier import VerificationError

    path = tmp_path / "cdm_corpus.json"
    append_certificate(_rec_c5(), path=path)
    before = path.read_text()

    mutant = _rec_ecxo()
    mutant["matching_M"] = [[0, 1]]  # non-dominating: vertices 2,5 uncovered
    with pytest.raises(VerificationError):
        append_certificate(mutant, path=path)
    assert path.read_text() == before


def test_prefix_immutability_refuses_tampered_prior_record(tmp_path):
    from alpha2.pool.cdm.store import append_certificate
    from alpha2.pool.cdm.verifier import VerificationError

    path = tmp_path / "cdm_corpus.json"
    append_certificate(_rec_c5(), path=path)

    data = json.loads(path.read_text())
    data[0]["H_edges_sha256"] = "0" * 64  # tamper the stored integrity hash
    path.write_text(json.dumps(data))

    with pytest.raises(VerificationError):
        append_certificate(_rec_ecxo(), path=path)


def test_atomic_write_leaves_no_temp_and_survives_failure(tmp_path, monkeypatch):
    import os

    from alpha2.pool.cdm import store
    from alpha2.pool.cdm.store import append_certificate

    path = tmp_path / "cdm_corpus.json"
    append_certificate(_rec_c5(), path=path)
    good = path.read_text()

    leftovers = [p for p in os.listdir(tmp_path) if p != "cdm_corpus.json"]
    assert leftovers == [], leftovers

    def boom(*a, **k):
        raise OSError("simulated crash mid-write")

    monkeypatch.setattr(store.json, "dump", boom)
    with pytest.raises(OSError):
        append_certificate(_rec_ecxo(), path=path)
    assert path.read_text() == good  # os.replace never ran -> old content intact
    leftovers = [p for p in os.listdir(tmp_path) if p != "cdm_corpus.json"]
    assert leftovers == [], leftovers  # temp unlinked on failure
