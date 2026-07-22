"""had_2 obstruction-enumeration semantics — ROADMAP SC3 (EXACT-02).

Proves the obstruction-based constraint generation in
`alpha2.solvers.problems.had2` is semantically identical to the legacy
Appendix C.4 O(|E_G|^2) loops, from BOTH sides:

  * SET-equality (not merely count-equality) against test-local copies of the
    naive loops at n=31 on seeds 1 and 137 — a count match with different
    members would be a masked bug;
  * the empirically-pinned structural checksum literals:
    seed-1 (131, 998, 726), seed-137 (177, 1913, 3782) for
    (single-single, single-pair, pair-pair);
  * a mutation test proving the checksum gate RAISES `ChecksumError` (a real
    raise-based mechanism, not an optimization-strippable statement) when any
    single conflict is dropped from any class;
  * refusal of a triangle-containing H at build (the enumeration is only
    total on triangle-free H);
  * an exhaustive brute-force had_2 differential at n <= 8 against CBC
    optimize — independent semantics, no import from the module under test.

The naive loops (Appendix C.4 lines 516-534, adapted to COLLECT sets instead
of adding constraints) live ONLY here as test-local reference code; they never
become a production path. Embedded-literal discipline (test_corpus_r1
precedent): expected constants are in-file literals, no cross-test imports.
"""
import random
from itertools import combinations

import pytest

from alpha2.generators.tfp import triangle_free_process
from alpha2.solvers.backend import get_backend
from alpha2.solvers.problems import had2 as had2_module
from alpha2.solvers.problems.had2 import (
    ChecksumError,
    build_had2_problem,
    enumerate_had2,
)
from alpha2.solvers.result import Status


# --------------------------------------------------------------------------- #
# LOCKED regression literals (RESEARCH Pattern 2, live-verified)
#   (nss, nsp, npp) = (single-single, single-pair, pair-pair) counts at n=31
# --------------------------------------------------------------------------- #
N31 = 31
CHECKSUM_LITERALS = {
    1: (131, 998, 726),
    137: (177, 1913, 3782),
}


def _h31(seed):
    """Regenerate the seed's triangle-free H via the frozen generator."""
    adj, _m = triangle_free_process(N31, random.Random(seed))
    return adj


# --------------------------------------------------------------------------- #
# Test-local naive reference loops — Appendix C.4, adapted to collect sets.
# These exist ONLY in this test file (never a production path) and use the
# same element conventions as enumerate_had2:
#   ss: (u, v) with u < v;  sp: (v, (a, b)) with a < b;
#   pp: frozenset({e1, e2}) of two G-edge tuples.
# --------------------------------------------------------------------------- #
def _naive_gedges(adj, n):
    return [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]


def _naive_ss(adj, n):
    # Appendix C.4: for u, for v in adj[u], if v > u -> s_u + s_v <= 1
    ss = set()
    for u in range(n):
        for v in adj[u]:
            if v > u:
                ss.add((u, v))
    return ss


def _naive_sp(adj, n, Gedges):
    # Appendix C.4: scan (v, G-edge); conflict iff {a, b} subset of N_H(v)
    sp = set()
    for v in range(n):
        for (a, b) in Gedges:
            if v == a or v == b:
                continue
            if a in adj[v] and b in adj[v]:
                sp.add((v, (a, b)))
    return sp


def _naive_pp(adj, n, Gedges):
    # Appendix C.4: ordered i < j scan over G-edge pairs with the
    # `len({a,b,c,d}) < 4` skip and the 4-way adjacency test; canonicalized
    # as frozenset({e1, e2}) to compare against the enumeration's dedup
    # convention on C4 diagonals.
    pp = set()
    for i in range(len(Gedges)):
        a, b = Gedges[i]
        for j in range(i + 1, len(Gedges)):
            c, d = Gedges[j]
            if len({a, b, c, d}) < 4:
                continue
            if c in adj[a] and d in adj[a] and c in adj[b] and d in adj[b]:
                pp.add(frozenset((Gedges[i], Gedges[j])))
    return pp


# --------------------------------------------------------------------------- #
# Test 1 — SET-equality vs the naive loops (seeds 1 AND 137, n=31)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("seed", [1, 137])
def test_set_equality_vs_naive_loops(seed):
    """LOCKED: set-equal, not count-equal — identical constraint semantics."""
    adj = _h31(seed)
    _Gedges, ss_enum, sp_enum, pp_enum = enumerate_had2(adj, N31)

    Gedges_naive = _naive_gedges(adj, N31)
    assert ss_enum == _naive_ss(adj, N31)
    assert sp_enum == _naive_sp(adj, N31, Gedges_naive)
    assert pp_enum == _naive_pp(adj, N31, Gedges_naive)


# --------------------------------------------------------------------------- #
# Test 2 — the empirically-pinned checksum literals
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("seed", [1, 137])
def test_checksum_literals(seed):
    adj = _h31(seed)
    _Gedges, ss, sp, pp = enumerate_had2(adj, N31)
    assert (len(ss), len(sp), len(pp)) == CHECKSUM_LITERALS[seed]


# --------------------------------------------------------------------------- #
# Test 3 — mutation -> ChecksumError: the gate provably raises on any single
# dropped conflict (raise-based, never assert; non-vacuous by construction)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mutated_class", ["ss", "sp", "pp"])
def test_mutation_raises_checksum_error(mutated_class, monkeypatch):
    """Drop one element from one conflict class; build must raise ChecksumError.

    The gate lives inside build_had2_problem and recomputes expectations from
    H's degrees/codegrees independently of the enumeration. We drive the REAL
    gate with tampered sets by wrapping enumerate_had2 at module level (the
    only seam that does not modify src/): the wrapper removes exactly one
    deterministically-chosen element from the targeted class.
    """
    adj = _h31(1)
    real_enumerate = had2_module.enumerate_had2

    def tampered_enumerate(a, n):
        Gedges, ss, sp, pp = real_enumerate(a, n)
        if mutated_class == "ss":
            ss = ss - {min(ss)}
        elif mutated_class == "sp":
            sp = sp - {min(sp)}
        else:
            pp = pp - {min(pp, key=lambda fs: sorted(fs))}
        return Gedges, ss, sp, pp

    monkeypatch.setattr(had2_module, "enumerate_had2", tampered_enumerate)
    with pytest.raises(ChecksumError):
        had2_module.build_had2_problem(adj, N31)


def test_unmutated_build_passes_the_gate():
    """Control leg: the same instance builds cleanly without tampering."""
    adj = _h31(1)
    problem = build_had2_problem(adj, N31)
    assert (len(problem.ss), len(problem.sp), len(problem.pp)) == \
        CHECKSUM_LITERALS[1]


# --------------------------------------------------------------------------- #
# Test 4 — triangle-containing H refused at build
# --------------------------------------------------------------------------- #
def test_triangle_containing_h_refused_at_build():
    """H with triangle 0-1-2 (n=4): enumeration is only total on triangle-free H."""
    adj = [{1, 2}, {0, 2}, {0, 1}, set()]
    with pytest.raises(ValueError):
        build_had2_problem(adj, 4)


# --------------------------------------------------------------------------- #
# Test-local exhaustive brute-force had_2 reference — INDEPENDENT semantics.
# Imports NOTHING from alpha2.solvers.problems.had2 (that is the point of a
# differential): candidates and compatibility are re-derived here from first
# principles. Two branch sets are mutually usable iff they are disjoint AND
# joined by at least one G-edge (some a in A, b in B with a != b and
# b not in adj_H[a]). Candidate count <= 8 + C(8,2) = 36 at n <= 8 —
# trivially exhaustive, correctness over speed.
# --------------------------------------------------------------------------- #
def _brute_had2(adj, n):
    """Exhaustive had_2: max clique in the candidate-compatibility graph."""
    cands = [frozenset((v,)) for v in range(n)]
    cands += [
        frozenset((u, v))
        for u in range(n) for v in range(u + 1, n)
        if v not in adj[u]                       # size-2 branch sets are G-edges
    ]

    def compatible(A, B):
        if A & B:                                # branch sets must be disjoint
            return False
        for a in A:                              # ... and adjacent in G
            for b in B:
                if a != b and b not in adj[a]:
                    return True
        return False

    m = len(cands)
    comp = [
        [i != j and compatible(cands[i], cands[j]) for j in range(m)]
        for i in range(m)
    ]

    best = 0

    def extend(size, allowed):
        nonlocal best
        if size > best:
            best = size
        for idx, i in enumerate(allowed):
            if size + (len(allowed) - idx) <= best:
                return                           # cardinality bound only
            extend(size + 1, [j for j in allowed[idx + 1:] if comp[i][j]])

    extend(0, list(range(m)))
    return best


def _alpha_h_exhaustive(adj, n):
    """Exact alpha(H) by full subset scan (2^n <= 256 at n <= 8)."""
    best = 0
    for k in range(n, 0, -1):
        for S in combinations(range(n), k):
            if all(v not in adj[u] for u, v in combinations(S, 2)):
                return k
    return best


# --------------------------------------------------------------------------- #
# The deterministic small-instance panel (>= 9 instances)
# --------------------------------------------------------------------------- #
def _matching6_adj():
    """H = perfect matching on n=6: edges 0-1, 2-3, 4-5."""
    return [{1}, {0}, {3}, {2}, {5}, {4}]


def _c5_adj():
    """H = C5: edges 0-1, 1-2, 2-3, 3-4, 4-0."""
    return [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]


def _panel():
    """(id, adj, n) — closed-form anchors + seeded TFP at n in {6, 7, 8}."""
    instances = [
        ("c5", _c5_adj(), 5),
        ("empty5", [set() for _ in range(5)], 5),
        ("matching6", _matching6_adj(), 6),
    ]
    for n, s in [(6, 1), (6, 2), (7, 1), (7, 2), (8, 1), (8, 2)]:
        adj, _m = triangle_free_process(n, random.Random(s))
        instances.append((f"tfp-n{n}-s{s}", adj, n))
    return instances


PANEL = _panel()
PANEL_IDS = [name for name, _adj, _n in PANEL]


# --------------------------------------------------------------------------- #
# Test 5 — exhaustive differential: brute == CBC PROVED_OPTIMAL on every
# panel instance (the enumeration+adapter pipeline has no small-case bug)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name,adj,n", PANEL, ids=PANEL_IDS)
def test_brute_force_differential_n_le_8(name, adj, n):
    expected = _brute_had2(adj, n)

    out = get_backend("cbc").solve_had2(adj, n, mode="optimize")
    assert out.status is Status.PROVED_OPTIMAL   # gate BEFORE any value read
    assert out.exact_value() == expected


# --------------------------------------------------------------------------- #
# Test 6 — domain sanity: had_2 >= alpha(H) = omega(G) on every instance
# (singletons on a max clique of G are always a valid family)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name,adj,n", PANEL, ids=PANEL_IDS)
def test_domain_sanity_had2_geq_alpha_h(name, adj, n):
    alpha_h = _alpha_h_exhaustive(adj, n)

    out = get_backend("cbc").solve_had2(adj, n, mode="optimize")
    assert out.status is Status.PROVED_OPTIMAL   # gate BEFORE any value read
    assert out.exact_value() >= alpha_h
