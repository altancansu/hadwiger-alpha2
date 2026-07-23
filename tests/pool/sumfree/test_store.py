"""RED contract — append-only g(G)-screen corpus store (POOL-2, Wave 3 target).

Mirrors the CDM store's five invariants (tests/pool/cdm/test_cdm_store.py) against
`alpha2.pool.sumfree.store.append_gscreen_certificate`, writing ONLY to a tmp_path
corpus (the real `paths.SUMFREE_CORPUS` and the frozen 296-instance corpus are NEVER
touched, T-8-02):

  * valid-append creates the file with one record;
  * a second valid append preserves the prefix byte-for-byte (data[0] == first);
  * an unverified record is REFUSED and the file is byte-unchanged;
  * a mutant record (g inconsistent with its branch-set witness) is REFUSED,
    file byte-unchanged;
  * prefix-immutability — tampering with a stored record makes the next append raise;
  * atomicity — a crash mid-write leaves the prior file intact and no temp behind.

Two DISTINCT genuinely-valid g<=0 KILLED records are embedded: Cay(Z_5, +/-1) == C_5
and Cay(Z_5, +/-2) == C_5 (distinct descriptors, distinct H_edges, isomorphic H).
Each has a hand-verified K_3 minor of G = complement(H). All imports of
`alpha2.pool.sumfree.*` are function-local so `--collect-only` stays clean; RED until
Wave 3 lands the store + verifier legs.
"""
import hashlib
import json

import pytest


def _sha(h_edges):
    canon = json.dumps(
        sorted([min(a, b), max(a, b)] for a, b in h_edges), separators=(",", ":")
    )
    return hashlib.sha256(canon.encode()).hexdigest()


def _gscreen_record(*, invariant_factors, S, H_edges, branch_sets, chi, had_3):
    return {
        "provenance": {
            "kind": "descriptor",
            "family": "sumfree_cayley",
            "tag": "random",
            "n": chi + (chi - had_3),  # placeholder n; verifier re-derives from H_edges
            "invariant_factors": list(invariant_factors),
            "S": [list(s) for s in S],
        },
        "H_edges": [list(e) for e in H_edges],
        "H_edges_sha256": _sha(H_edges),
        "chi": chi,
        "had_2": had_3,
        "had_3": had_3,
        "g": (chi - had_3) / chi,
        "model_branch_sets": [list(b) for b in branch_sets],
        "terminal_state": "KILLED",
        "certificate_statement": (
            f"had_3 = {had_3} >= chi = {chi}; verified K_chi minor (branch sets <=3); "
            "packs; g <= 0."
        ),
        "verified": True,
        "method": "heuristic K_chi HIT + trust-root verify (sumfree g-screen)",
    }


# Record 1 — Cay(Z_5, +/-1) == C_5; G = complement(C_5); K_3 = [[0],[2],[1,3,4]].
def _rec_c5_pm1():
    return _gscreen_record(
        invariant_factors=[5],
        S=[[1], [4]],
        H_edges=[[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]],
        branch_sets=[[0], [2], [1, 3, 4]],
        chi=3,
        had_3=3,
    )


# Record 2 — Cay(Z_5, +/-2) == C_5 (distinct descriptor); G = complement == C_5(+/-1);
# K_3 minor of that C_5 = [[0],[1],[2,3,4]] (0~1, 0~4, 1~2 all edges).
def _rec_c5_pm2():
    return _gscreen_record(
        invariant_factors=[5],
        S=[[2], [3]],
        H_edges=[[0, 2], [1, 3], [2, 4], [0, 3], [1, 4]],
        branch_sets=[[0], [1], [2, 3, 4]],
        chi=3,
        had_3=3,
    )


def test_append_valid_creates_file_with_one_record(tmp_path):
    from alpha2.pool.sumfree.store import append_gscreen_certificate  # RED until Wave 3

    path = tmp_path / "sumfree_corpus.json"
    append_gscreen_certificate(_rec_c5_pm1(), path=path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["provenance"]["S"] == [[1], [4]]


def test_second_append_preserves_prefix(tmp_path):
    from alpha2.pool.sumfree.store import append_gscreen_certificate

    path = tmp_path / "sumfree_corpus.json"
    append_gscreen_certificate(_rec_c5_pm1(), path=path)
    first = json.loads(path.read_text())[0]
    append_gscreen_certificate(_rec_c5_pm2(), path=path)
    data = json.loads(path.read_text())
    assert len(data) == 2
    assert data[0] == first  # prefix byte-identical
    assert data[1]["provenance"]["S"] == [[2], [3]]


def test_unverified_record_refused_file_unchanged(tmp_path):
    from alpha2.pool.sumfree.store import append_gscreen_certificate
    from alpha2.pool.sumfree.verifier import VerificationError

    path = tmp_path / "sumfree_corpus.json"
    append_gscreen_certificate(_rec_c5_pm1(), path=path)
    before = path.read_text()

    bad = _rec_c5_pm2()
    bad["verified"] = False
    with pytest.raises(VerificationError):
        append_gscreen_certificate(bad, path=path)
    assert path.read_text() == before


def test_mutant_record_refused_file_unchanged(tmp_path):
    from alpha2.pool.sumfree.store import append_gscreen_certificate
    from alpha2.pool.sumfree.verifier import VerificationError

    path = tmp_path / "sumfree_corpus.json"
    append_gscreen_certificate(_rec_c5_pm1(), path=path)
    before = path.read_text()

    # g claims a KILLED pack, but the branch-set witness is only 2 sets — cannot
    # support a K_3 minor. The stdlib verifier must re-derive and reject.
    mutant = _rec_c5_pm2()
    mutant["model_branch_sets"] = [[0], [1]]
    with pytest.raises(VerificationError):
        append_gscreen_certificate(mutant, path=path)
    assert path.read_text() == before


def test_prefix_immutability_refuses_tampered_prior_record(tmp_path):
    from alpha2.pool.sumfree.store import append_gscreen_certificate
    from alpha2.pool.sumfree.verifier import VerificationError

    path = tmp_path / "sumfree_corpus.json"
    append_gscreen_certificate(_rec_c5_pm1(), path=path)

    data = json.loads(path.read_text())
    data[0]["H_edges_sha256"] = "0" * 64  # tamper the stored integrity hash
    path.write_text(json.dumps(data))

    with pytest.raises(VerificationError):
        append_gscreen_certificate(_rec_c5_pm2(), path=path)


def test_atomic_write_leaves_no_temp_and_survives_failure(tmp_path, monkeypatch):
    import os

    from alpha2.pool.sumfree import store
    from alpha2.pool.sumfree.store import append_gscreen_certificate

    path = tmp_path / "sumfree_corpus.json"
    append_gscreen_certificate(_rec_c5_pm1(), path=path)
    good = path.read_text()

    leftovers = [p for p in os.listdir(tmp_path) if p != "sumfree_corpus.json"]
    assert leftovers == [], leftovers

    def boom(*a, **k):
        raise OSError("simulated crash mid-write")

    monkeypatch.setattr(store.json, "dump", boom)
    with pytest.raises(OSError):
        append_gscreen_certificate(_rec_c5_pm2(), path=path)
    assert path.read_text() == good  # os.replace never ran -> old content intact
    leftovers = [p for p in os.listdir(tmp_path) if p != "sumfree_corpus.json"]
    assert leftovers == [], leftovers  # temp unlinked on failure
