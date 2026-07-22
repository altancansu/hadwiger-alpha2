"""SRCH-02 instrumentation contract: ``solve()`` exposes restarts-to-solution and the
initial-conflict count, and a MISS is ``sets = None`` — NEVER a RESISTANT result.

The pipeline (Plan 06-02, ``battery/pipeline.py``) maps a ``sets is None`` miss to an
UNCONDITIONAL edge to the exact had_2 backend. RESISTANT is reachable ONLY via an
exact-method timeout (``INSUFFICIENT``), NEVER via a heuristic miss (threat T-06-10 /
SRCH-02): a searcher failing to find a model is a fact about the searcher, not an
impossibility claim about the graph.
"""
import random

from alpha2.search.heuristic import solve


def test_solve_returns_five_tuple_instrumentation():
    """A HIT returns the 5-tuple (sets, best_init, moves, restarts, elapsed) with the
    instrumentation fields typed as ints (restarts-to-solution, initial-conflict count,
    moves) and elapsed a float."""
    n = 6
    adj = [set() for _ in range(n)]      # H empty => G complete: any assignment is a K_k
    rng = random.Random(0)

    result = solve(adj, n, 3, rng, time_budget=1.0)

    assert isinstance(result, tuple) and len(result) == 5
    sets, best_init, moves, restarts, elapsed = result
    assert sets is not None
    assert isinstance(best_init, int)                 # initial-conflict count (SRCH-02)
    assert isinstance(moves, int)
    assert isinstance(restarts, int) and restarts >= 1  # restarts-to-solution (SRCH-02)
    assert isinstance(elapsed, float)


def test_miss_returns_none_never_resistant():
    """A forced miss (no K_k model exists) returns ``sets = None`` with ``moves = None``
    and ``restarts >= 1`` — the searcher actually tried. The pipeline routes this to the
    exact had_2 backend; it is NEVER emitted as RESISTANT (RESISTANT is an exact-timeout
    queue state only)."""
    n = 6
    adj = [set(range(n)) - {i} for i in range(n)]     # H complete => G empty: no K_k model
    rng = random.Random(0)

    sets, best_init, moves, restarts, elapsed = solve(adj, n, n, rng, time_budget=0.5)

    assert sets is None                               # a miss — a fact about the searcher
    assert moves is None                              # miss return contract preserved
    assert restarts >= 1                              # the searcher restarted at least once
    assert isinstance(elapsed, float)
