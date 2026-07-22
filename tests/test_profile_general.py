"""SRCH-01 profile-general heuristic regression: the seed-137 non-spanning fix.

The spanning-only ``solve()`` head (``p = n-k; s = 2*k-n; assert 2*p+s == n``) can
represent only the single SPANNING profile (15 pairs + 1 singleton = 31 vertices at
n=31, chi=16) and empirically MISSES seed-137 — whose D.3 optimum is a NON-spanning
9 pairs + 7 singletons = 25 vertices (6 unused), a shape the spanning data structure
cannot even hold.

These tests exercise the profile-general rewrite (Task 2): ``solve()`` iterates
profiles ``(p', s')`` with ``p' + s' = chi`` and ``2*p' + s' <= n``, so it can both
HOLD the non-spanning state and FIND a verified K16 model the spanning profile cannot.

The returned family is an UNTRUSTED proposal (threat T-06-13); these tests assert its
G-edge / disjointness structure directly, and cross-check via the independent
``verify.model`` verifier — never trusting the searcher's own bookkeeping.
"""
import random

import pytest

from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
from alpha2.search.heuristic import full_conflicts, solve
from alpha2.verify.model import verify_model


def _regen(n, seed):
    """Single-RNG contract v1: one rng feeds generation FIRST, then search."""
    rng = random.Random(seed)
    adj, m = triangle_free_process(n, rng)
    return adj, m, rng


def _assert_valid_kmodel(sets, adj, n, k):
    """Structurally verify a K_k model of size-<=2 branch sets (raises-only checks)."""
    assert sets is not None, "profile-general solve returned no model"
    assert len(sets) == k, (len(sets), k)
    assert all(len(s) <= 2 for s in sets), [len(s) for s in sets]
    verts = [v for s in sets for v in s]
    assert len(verts) == len(set(verts)), "branch sets are not disjoint"
    assert len(set(verts)) <= n, (len(set(verts)), n)
    # every size-2 branch set is a G-edge (i.e. NOT an H-edge)
    for s in sets:
        if len(s) == 2:
            a, b = s
            assert b not in adj[a] and a not in adj[b], ("pair is an H-edge", s)
    # all branch-set pairs adjacent in G (no conflicts) — the K_k minor condition
    assert not full_conflicts(sets, adj), "some branch-set pair is non-adjacent in G"
    # independent structural cross-check (the searcher's family is untrusted)
    assert verify_model([list(s) for s in sets], adj, n, k) is True


@pytest.mark.slow
def test_profile_general_finds_seed137_k16():
    """With a generous budget, the profile-general searcher FINDS a verified K16 model
    for seed-137 — the exact instance the spanning profile misses (SRCH-01)."""
    n = 31
    adj, m, rng = _regen(n, 137)
    assert m == 177, m
    nu = matching_number(adj, n)
    chi = n - nu
    assert chi == 16, chi

    sets, best_init, moves, restarts, elapsed = solve(adj, n, chi, rng, time_budget=90.0)

    _assert_valid_kmodel(sets, adj, n, chi)
    # The found model need NOT be spanning — the spanning profile (s=1) alone cannot
    # hold seed-137's 6-unused-vertex optimum; profile-general succeeds.
    assert restarts >= 1
    assert isinstance(best_init, int)


def test_hold_nonspanning_state():
    """The rewritten data structure can HOLD the D.3 non-spanning profile: 9 pairs +
    7 singletons = 25 vertices, 6 unused — a shape the spanning ``initial_state``
    (which pairs the entire pool, forcing 2*p + s == n) cannot represent."""
    from alpha2.search.heuristic import initial_state_profile

    n = 31
    adj, m, rng = _regen(n, 137)
    state = initial_state_profile(adj, n, 9, 7, rng)

    assert state is not None, "profile builder could not hold the non-spanning D.3 state"
    pairs = [s for s in state if len(s) == 2]
    singles = [s for s in state if len(s) == 1]
    assert len(pairs) == 9, len(pairs)
    assert len(singles) == 7, len(singles)
    assert len(pairs) + len(singles) == 16
    verts = [v for s in state for v in s]
    assert len(verts) == 25, len(verts)               # 2*9 + 7
    assert len(set(verts)) == 25, "state vertices are not disjoint"
    assert n - len(set(verts)) == 6, "expected exactly 6 unused vertices"
    # each pair is a valid G-edge (not an H-edge)
    for a, b in pairs:
        assert b not in adj[a], ("pair is an H-edge", (a, b))


def test_chi_below_half_n_does_not_raise():
    """A pool-style instance with chi < n/2 (so 2*chi - n < 0) must NOT crash — the
    old ``assert p >= 0 and s >= 0 and 2*p + s == n`` head raised here (T-06-11).
    Bounded profile enumeration replaces the assert."""
    n = 10
    adj = [set() for _ in range(n)]      # H empty => G complete; the k-arg 3 < n/2 = 5
    rng = random.Random(3)

    result = solve(adj, n, 3, rng, time_budget=0.5)   # must NOT raise (no assert)

    assert isinstance(result, tuple) and len(result) == 5


def test_sc1_starved_budget_still_misses():
    """SC1 preservation (critical): the pipeline's starved heuristic budget (0.0 s)
    must still MISS on seed-137, so ``run_candidate`` routes to the exact had_2 = 17
    kill. A better profile-general searcher must NOT 'find' under SC1's small budget
    and silently change SC1's path (the 06-02 e2e stays green)."""
    n = 31
    adj, m, rng = _regen(n, 137)
    nu = matching_number(adj, n)
    chi = n - nu

    sets, best_init, moves, restarts, elapsed = solve(adj, n, chi, rng, time_budget=0.0)

    assert sets is None, "SC1 starved-budget heuristic must miss and route to exact"
