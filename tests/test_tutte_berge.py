"""Tutte-Berge witness hand-check: chi = n - nu pinned BOTH directions (CHI-02).

For seed 1 AND seed 137 (n=31): the emission extractor returns U == [], nu == 15;
the stdlib-only verifier re-checks the Tutte-Berge inequality and pins chi == 16.
A synthetic star (U == [0], non-empty) exercises the GENERAL odd-component path so
it is provably not a U=[] shortcut. A wrong-chi witness mutant (chi_G=15) makes the
verifier RAISE via its n - nu != chi guard — closing the wrong-chi criterion at the
witness boundary (complements test_verifier_mutants' family-size mutant chi_G=17).
"""
import hashlib
import json
import random

import pytest

from alpha2.corpus.verifier import VerificationError, verify_chi_witness
from alpha2.invariants.witness import extract_witness


def _regen(n, seed):
    from alpha2.generators.tfp import triangle_free_process
    return triangle_free_process(n, random.Random(seed))


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _sha(edges):
    return hashlib.sha256(json.dumps(edges, separators=(",", ":")).encode()).hexdigest()


def _odd_comps(adj, n, U):
    """Independent stdlib odd-component count of H - U (test-side cross-check)."""
    keep = set(range(n)) - set(U)
    seen = set()
    c_odd = 0
    for s in keep:
        if s in seen:
            continue
        seen.add(s)
        size = 0
        stack = [s]
        while stack:
            x = stack.pop()
            size += 1
            for w in adj[x]:
                if w in keep and w not in seen:
                    seen.add(w)
                    stack.append(w)
        if size % 2 == 1:
            c_odd += 1
    return c_odd


def _record(n, seed):
    adj, m = _regen(n, seed)
    M, U, nu = extract_witness(adj, n)
    rec = {
        "H_edges": _h_edges(adj, n),
        "H_edges_sha256": _sha(_h_edges(adj, n)),
        "invariants": {
            "n": n, "num_H_edges": m, "nu_H": nu, "chi_G": n - nu,
            "omega_G": None, "had_2": n - nu,
        },
        "matching_M": M,
        "tutte_berge_U": U,
    }
    return rec, adj, M, U, nu


@pytest.mark.parametrize("seed", [1, 137])
def test_witness_pins_chi_both_directions(seed):
    n = 31
    rec, adj, M, U, nu = _record(n, seed)

    # Factor-critical corpus case: empty witness, near-perfect matching, chi=16.
    assert U == [], (seed, "expected empty Tutte-Berge witness", U)
    assert nu == 15, (seed, "nu", nu)
    assert len(M) == 15, (seed, "|M|", len(M))
    assert n - nu == 16

    # The trust root re-checks and pins chi = n - nu in both directions.
    assert verify_chi_witness(rec) is True

    # Independent arithmetic cross-check: (n - odd_comps(H-U) + |U|)//2 == nu == |M|.
    c_odd = _odd_comps(adj, n, U)
    assert c_odd == 1, (seed, "odd comps of connected odd-order H", c_odd)
    assert (n - c_odd + len(U)) // 2 == nu == len(M) == 15


def test_general_path_nonempty_witness_star():
    """Synthetic K_{1,3} star: U == [0] (NON-empty) exercises the general path.

    center 0, leaves 1,2,3; nu=1, M=[[0,1]]; H-U = 3 isolated odd components;
    (4 - 3 + 1)//2 == 1 == nu. Proves the odd-component computation actually fires
    (not a U=[] shortcut).
    """
    edges = [[0, 1], [0, 2], [0, 3]]
    star = {
        "H_edges": edges,
        "H_edges_sha256": _sha(edges),
        "invariants": {
            "n": 4, "num_H_edges": 3, "nu_H": 1, "chi_G": 3,
            "omega_G": None, "had_2": 3,
        },
        "matching_M": [[0, 1]],
        "tutte_berge_U": [0],
    }
    assert verify_chi_witness(star) is True

    # star adjacency for the independent cross-check
    adj = [set() for _ in range(4)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    assert _odd_comps(adj, 4, [0]) == 3
    assert (4 - 3 + 1) // 2 == 1


def test_cr01_negative_index_alias_in_matching_raises():
    """CR-01 soundness repro: a negative-index vertex in matching_M must RAISE.

    H = star at vertex 2 on n=3: edges (0,2),(1,2). TRUE nu=1 (both H-edges share
    vertex 2; no size-2 matching exists), so TRUE chi = n - nu = 2. The forged
    record claims nu=2 (=> chi=1) via matching_M=[[0,2],[-1,1]], where the literal
    -1 aliases adj[-1] == adj[2] through Python list-index wraparound. The `covered`
    set tracks the RAW values (0,2,-1,1) so it never sees the vertex-2 collision.
    Before the range check verify_chi_witness returned True (a soundness break);
    it must now raise VerificationError.
    """
    edges = [[0, 2], [1, 2]]
    bad = {
        "H_edges": edges,
        "H_edges_sha256": _sha(edges),
        "invariants": {
            "n": 3, "num_H_edges": 2, "nu_H": 2, "chi_G": 1,
            "omega_G": None, "had_2": 2,
        },
        "matching_M": [[0, 2], [-1, 1]],  # -1 aliases adj[-1] == adj[2] (n=3)
        "tutte_berge_U": [0],             # crafted so the U-leg ALSO yields nu=2
    }
    with pytest.raises(VerificationError):
        verify_chi_witness(bad)


def test_wrong_chi_witness_mutant_raises():
    """Good seed-1 witness with chi_G lowered to 15 (n-nu=16 != 15) MUST raise.

    This is the wrong-chi failure mode NOT catchable by verify_model_record's
    k < chi check (a lowered chi never trips k >= chi). It is caught here at the
    witness boundary via the `n - nu != chi` guard.
    """
    rec, *_ = _record(31, 1)
    rec["invariants"]["chi_G"] = 15  # n - nu = 16 != 15
    with pytest.raises(VerificationError):
        verify_chi_witness(rec)
