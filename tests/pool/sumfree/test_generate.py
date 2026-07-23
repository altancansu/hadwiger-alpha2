"""RED contract — sum-free generators + Cayley adjacency (POOL-2, Wave 2 target).

Pins `alpha2.pool.sumfree.generate`: `can_add(S, group, a)`,
`random_maximal_symmetric_sumfree(group, rng)`, the structured
`middle_interval_sumfree(group)`, and `cayley_adj_abelian(group, S)`.

For EVERY generator (structured + random) the returned S must be, by an in-file
BRUTE re-check (never trusting the generator):
  (i)   symmetric        S == {neg(a) : a in S},
  (ii)  sum-free         S ∩ (S+S) == ∅,
  (iii) zero-free        identity ∉ S,
and `cayley_adj_abelian(group, S)` must be TRIANGLE-FREE (brute), so G = H̄ is α=2.

Imports of the modules-under-test are FUNCTION-LOCAL; bodies are RED until Wave 2.
"""
import random

import pytest


def _abelian(factors):
    from alpha2.pool.sumfree.group import Abelian  # RED until Wave 2

    return Abelian(factors)


# --------------------------------------------------------------------------- #
# In-file brute oracles (self-contained; do NOT call the module under test)
# --------------------------------------------------------------------------- #
def _identity(g):
    return tuple(0 for _ in g.factors)


def _assert_symmetric_sumfree_zero_free(S, g):
    Sset = set(S)
    assert _identity(g) not in Sset, "0 must not be in a sum-free connection set"
    for a in Sset:
        assert g.neg(a) in Sset, "S must be symmetric (S == -S)"
    for a in Sset:
        for b in Sset:
            assert g.add(a, b) not in Sset, "S must be sum-free (S ∩ (S+S) == ∅)"


def _triangle_free(adj):
    n = len(adj)
    for u in range(n):
        for v in adj[u]:
            if v <= u:
                continue
            if adj[u] & adj[v]:      # a common neighbour closes a triangle
                return False
    return True


@pytest.mark.parametrize("factors", [(31,), (11,), (3, 3)])
def test_random_maximal_symmetric_sumfree_is_valid_and_triangle_free(factors):
    from alpha2.pool.sumfree.generate import (
        cayley_adj_abelian,
        random_maximal_symmetric_sumfree,
    )

    g = _abelian(factors)
    rng = random.Random(1)
    S = set(random_maximal_symmetric_sumfree(g, rng))
    _assert_symmetric_sumfree_zero_free(S, g)

    adj = cayley_adj_abelian(g, S)
    assert len(adj) == g.n
    assert _triangle_free(adj), "H = Cay(Γ, S) must be triangle-free (⇒ α(H̄) = 2)"


@pytest.mark.parametrize("factors", [(31,), (53,)])
def test_middle_interval_structured_is_valid_and_triangle_free(factors):
    from alpha2.pool.sumfree.generate import (
        cayley_adj_abelian,
        middle_interval_sumfree,
    )

    g = _abelian(factors)
    S = set(middle_interval_sumfree(g))
    _assert_symmetric_sumfree_zero_free(S, g)

    adj = cayley_adj_abelian(g, S)
    assert _triangle_free(adj)


def test_can_add_rejects_a_sum_relation():
    from alpha2.pool.sumfree.generate import can_add

    g = _abelian((5,))
    # {(1,),(4,)} is sum-free; adding (2,) creates 1+1=2 (a sum relation) -> False.
    S = {(1,), (4,)}
    assert can_add(S, g, (2,)) is False


def test_can_add_accepts_a_safe_element():
    from alpha2.pool.sumfree.generate import can_add

    g = _abelian((5,))
    # empty S: adding (1,) (symmetrized with (4,)) stays sum-free -> True.
    assert can_add(set(), g, (1,)) is True


def test_cayley_adj_matches_hand_built_C5():
    from alpha2.pool.sumfree.generate import cayley_adj_abelian

    g = _abelian((5,))
    adj = cayley_adj_abelian(g, {(1,), (4,)})   # Cay(Z_5, ±1) == C_5
    assert [set(s) for s in adj] == [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {0, 3}]
