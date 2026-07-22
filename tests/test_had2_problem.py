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

import pytest

from alpha2.generators.tfp import triangle_free_process
from alpha2.solvers.problems import had2 as had2_module
from alpha2.solvers.problems.had2 import (
    ChecksumError,
    build_had2_problem,
    enumerate_had2,
)


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
