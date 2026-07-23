"""RED contract — empirical ILP frontier measurement (POOL-2, Wave 4 target).

The g(G) screen is trustworthy only where the exact backend PROVES had_2 optimality
inside the deterministic budget; above that frontier a resistant instance QUEUES for
E3 rather than being called a break (RESEARCH A4 crossover). This pins
`alpha2.pool.sumfree.frontier.measure_ilp_frontier(ns, *, det_budget, num_workers=1)`,
which returns, per n, whether had_2 optimality was PROVED within budget.

Import is FUNCTION-LOCAL; RED until Wave 4. Small ns only -> NOT slow.
"""


def test_measure_ilp_frontier_reports_proved_flag_per_n():
    from alpha2.pool.sumfree.frontier import measure_ilp_frontier  # RED until Wave 4

    result = measure_ilp_frontier([12, 13], det_budget=1.0, num_workers=1)
    # One entry per requested n, each with an explicit optimality-proved boolean.
    assert set(result.keys()) == {12, 13}
    for n in (12, 13):
        assert isinstance(result[n]["proved"], bool)


def test_frontier_is_monotone_downward():
    # If had_2 optimality is NOT proved at some n within budget, it must not be
    # reported as proved at any larger n (the frontier is a downward crossover).
    from alpha2.pool.sumfree.frontier import measure_ilp_frontier

    result = measure_ilp_frontier([12, 13, 14], det_budget=1.0, num_workers=1)
    proved = [result[n]["proved"] for n in (12, 13, 14)]
    first_false = next((i for i, p in enumerate(proved) if not p), len(proved))
    assert all(not p for p in proved[first_false:]), "frontier must not re-cross upward"
