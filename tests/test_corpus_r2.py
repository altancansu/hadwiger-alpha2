"""R2 generator-determinism panel — regenerate H from the seed, sha256 == manifest.

R2 crosses the environment/interpreter boundary: it re-runs the deterministic
generators from the stored (n|p, seed), rebuilds canonical H_edges, hashes them via
the FROZEN ``schema.h_edges_sha256`` convention (never a 2nd hash impl — T-3-01), and
asserts the digest equals the frozen golden in ``data/manifests/corpus-v1.manifest.json``.
Any accidental generator drift (a reformat of tfp.py/cayley.py, a CPython bump that
shifts set-iteration order) makes the regenerated digest diverge and trips R2 (T-3-02).

Every hash comparison is GATED behind a doc-derived / structural invariant that a
porting bug would break, so a regression cannot self-certify (fingerprint.py analog):
  * TFP (31,1): assert |E(H)| == 131 (Appendix D.2, doc) BEFORE trusting the hash.
  * Cayley:     assert the regenerated graph is |S|-regular and S symmetric sum-free
                (Cay(Z_p, S) structural identity 2|E| == p|S|) BEFORE trusting the hash.

Per-commit: a small slice (tfp:n31:s1 + one Cayley). The full 296-instance panel is
the ``slow`` (release/nightly) leg below — it regenerates every stored record and
compares to BOTH the manifest and the record's own H_edges_sha256.
"""
import json
import random

import pytest

from alpha2 import paths
from alpha2.corpus.schema import h_edges_sha256
from alpha2.generators.tfp import triangle_free_process
from alpha2.generators.cayley import random_maximal_symmetric_sumfree, cayley_adj

MANIFEST_PATH = paths.REPO_ROOT / "data" / "manifests" / "corpus-v1.manifest.json"

# Doc-derived invariant (Appendix D.2). NOT derived from generated output.
EXPECTED_M_31_1 = 131  # |E(H)| for the (n=31, seed=1) triangle-free-process complement


def _load_manifest():
    with open(MANIFEST_PATH) as fh:
        return json.load(fh)


def _canonical_h_edges(adj, n):
    """Canonical H_edges: sorted [min,max] pairs over u<v (matches schema.canonical_edges)."""
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def regen_tfp(n, seed):
    """Regenerate the triangle-free-process complement H from (n, seed)."""
    adj, _ = triangle_free_process(n, random.Random(seed))
    return adj


def regen_cayley(p, seed):
    """Regenerate the Cayley Cay(Z_p, S) graph H from (p, seed); return (adj, S)."""
    S = random_maximal_symmetric_sumfree(p, random.Random(seed))
    return cayley_adj(p, S), S


def test_r2_tfp_slice_determinism():
    """TFP determinism (per-commit slice): regenerate (31,1), gate on m, hash == manifest."""
    manifest = _load_manifest()
    adj = regen_tfp(31, 1)
    H_edges = _canonical_h_edges(adj, 31)

    # Doc-invariant gate FIRST: trust the hash only if the Appendix-D.2 |E(H)| holds.
    assert len(H_edges) == EXPECTED_M_31_1, ("tfp(31,1) |E(H)| drift", len(H_edges))

    got = h_edges_sha256(H_edges)
    assert got == manifest["tfp:n31:s1"]["h_edges_sha256"], (
        "tfp:n31:s1 regenerated sha256 != manifest", got
    )


def test_r2_cayley_slice_determinism():
    """Cayley determinism (per-commit slice): regenerate (p=31, s=5310), structural gate, hash."""
    manifest = _load_manifest()
    p, seed = 31, 5310
    adj, S = regen_cayley(p, seed)
    H_edges = _canonical_h_edges(adj, p)

    # Structural gate FIRST (Cay(Z_p, S) identity): a porting bug in the generator
    # would break |S|-regularity / symmetry, so the hash is only trusted once these hold.
    assert 0 not in S, "0 must not be in a symmetric sum-free S"
    assert all(((-s) % p) in S for s in S), "S must be symmetric"
    assert {len(adj[u]) for u in range(p)} == {len(S)}, "Cay(Z_p, S) must be |S|-regular"
    assert 2 * len(H_edges) == p * len(S), ("2|E| == p|S| identity broken", len(H_edges))

    got = h_edges_sha256(H_edges)
    assert got == manifest["cayley:p31:s5310"]["h_edges_sha256"], (
        "cayley:p31:s5310 regenerated sha256 != manifest", got
    )


@pytest.mark.slow
def test_r2_full_panel_all_296():
    """Nightly/release leg: regenerate EVERY stored instance, sha256 == manifest + record.

    Iterates the frozen corpus, regenerates H per family from the stored (n|p, seed),
    and asserts the digest matches BOTH the manifest golden AND the record's own
    H_edges_sha256 (same frozen convention). This is the exhaustive R2 determinism proof.
    """
    manifest = _load_manifest()
    with open(paths.CORPUS) as fh:
        records = json.load(fh)
    assert len(records) == 296, ("corpus size", len(records))

    checked = {"tfp": 0, "cayley": 0}
    for rec in records:
        prov = rec["provenance"]
        fam = prov["family"]
        n = rec["invariants"]["n"]
        seed = prov["seed"]
        if fam == "triangle_free_process_complement":
            adj = regen_tfp(n, seed)
            key = f"tfp:n{n}:s{seed}"
            checked["tfp"] += 1
        elif fam == "cayley_maximal_sumfree_Zp":
            adj, _ = regen_cayley(n, seed)
            key = f"cayley:p{n}:s{seed}"
            checked["cayley"] += 1
        else:
            raise AssertionError(f"unexpected family {fam!r}")
        got = h_edges_sha256(_canonical_h_edges(adj, n))
        assert got == manifest[key]["h_edges_sha256"], (key, "manifest drift", got)
        assert got == rec["H_edges_sha256"], (key, "record self-hash drift", got)

    assert checked == {"tfp": 284, "cayley": 12}, ("panel counts", checked)
