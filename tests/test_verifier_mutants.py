"""Adversarial mutant suite for the trust-root verifier (VRF-01, crit-2).

Each mutant is a single perturbation of a KNOWN-GOOD certificate record (Appendix
D.2, n=31 seed 1). The independent verifier MUST raise VerificationError on every
one; the unmutated good_record() must pass (returning k = 16 = had_2).

The record is a plain dict built inline (the verifier consumes JSON dicts, never
schema.py — which is Plan 02). H_edges are regenerated deterministically from the
triangle-free process so the canonical sha256 equals the frozen Phase-1 golden.
"""
import hashlib
import json
import random

import pytest

# Trust root under test. At RED (verifier absent) this import fails -> intended.
from alpha2.corpus.verifier import VerificationError, verify_model_record

GOLDEN_SHA = "3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2"

# Stored Appendix D.2 K16 model (external authority; verifies against regenerated H).
D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]


def _regen(n, seed):
    from alpha2.generators.tfp import triangle_free_process
    return triangle_free_process(n, random.Random(seed))


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _sha(edges):
    return hashlib.sha256(json.dumps(edges, separators=(",", ":")).encode()).hexdigest()


def good_record():
    """Build a KNOWN-GOOD schema-free record + its regenerated adjacency."""
    n = 31
    adj, m = _regen(n, 1)
    edges = _h_edges(adj, n)
    rec = {
        "H_edges": edges,
        "H_edges_sha256": _sha(edges),
        "invariants": {
            "n": 31, "num_H_edges": 131, "nu_H": 15, "chi_G": 16,
            "omega_G": None, "had_2": 16,
        },
        "model_branch_sets": [list(s) for s in D2_MODEL],
    }
    return rec, adj


def _where(model):
    w = {}
    for i, S in enumerate(model):
        for v in S:
            w[v] = i
    return w


# --- sanity: the good record is genuinely good ------------------------------

def test_good_record_sha_matches_golden():
    rec, _ = good_record()
    assert rec["H_edges_sha256"] == GOLDEN_SHA


def test_good_record_passes_returns_16():
    rec, _ = good_record()
    assert verify_model_record(rec) == 16


# --- five adversarial mutants: each MUST raise ------------------------------

def test_mutant_a_overlapping_sets():
    """(a) Reuse a vertex across two branch sets -> disjointness violation."""
    rec, _ = good_record()
    m = rec["model_branch_sets"]
    m[1] = [m[0][0], m[1][1]]  # inject set-0's first vertex into set 1
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_mutant_b_h_edge_pair():
    """(b) A size-2 branch set that is an H-edge (non-edge of G) -> raise."""
    rec, adj = good_record()
    m = rec["model_branch_sets"]
    w = _where(m)
    # Find an H-edge (u,v) whose endpoints sit in two DISTINCT size-2 sets.
    found = None
    for u in range(31):
        for v in sorted(adj[u]):
            if u < v and w[u] != w[v] and len(m[w[u]]) == 2 and len(m[w[v]]) == 2:
                found = (u, v)
                break
        if found:
            break
    assert found is not None, "expected an H-edge across two size-2 sets"
    u, v = found
    p, q = w[u], w[v]
    up = next(x for x in m[p] if x != u)
    vq = next(x for x in m[q] if x != v)
    m[p] = [u, v]      # this branch set is now an H-edge, not a G-edge
    m[q] = [up, vq]    # partners swapped -> vertex cover preserved (still disjoint)
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_mutant_c_missing_cross_adjacency():
    """(c) Two branch sets fully NON-adjacent in G (is_conflict True) -> raise."""
    rec, adj = good_record()
    m = rec["model_branch_sets"]
    w = _where(m)
    # Any H-edge (u,v): making both endpoints singletons forces is_conflict True
    # (the only cross pair {u,v} is an H-edge => non-adjacent in G).
    found = None
    for u in range(31):
        for v in sorted(adj[u]):
            if u < v and w[u] != w[v]:
                found = (u, v)
                break
        if found:
            break
    assert found is not None, "expected an H-edge"
    u, v = found
    m[w[u]] = [u]
    m[w[v]] = [v]
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_mutant_d_truncated_family():
    """(d) Drop the last branch set (fam[:-1]) -> k=15 < chi=16 -> raise."""
    rec, _ = good_record()
    rec["model_branch_sets"] = rec["model_branch_sets"][:-1]
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_mutant_e_wrong_chi():
    """(e) Inflate chi to 17 -> family-size check k=16 < 17 -> raise.

    NOTE: chi_G=17 (not 15). verify_model_record only checks k < chi; k >= chi is
    intentionally allowed (seed-137's 17-set family has k > chi). A LOWERED chi
    never trips this boundary — the chi != n-nu failure mode is a witness violation
    proven separately in test_tutte_berge.py via verify_chi_witness.
    """
    rec, _ = good_record()
    rec["invariants"]["chi_G"] = 17
    with pytest.raises(VerificationError):
        verify_model_record(rec)
