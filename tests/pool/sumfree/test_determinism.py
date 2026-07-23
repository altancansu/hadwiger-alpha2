"""RED contract — deterministic reported verdicts (POOL-2, Wave 4 target; SLOW).

Locked Decision 3 + CLAUDE.md CP-SAT regressions (#3590/#3842/#4839): ANY reported
impossibility / RESISTANT / had_k < chi verdict MUST be reproducible run-to-run under
`num_workers=1` + a DETERMINISTIC solver budget (`max_deterministic_time`, never
wall-clock). This test is the driver that forces the 08-02 deterministic-budget field:
it adjudicates the SAME instance twice and asserts an identical verdict.

Pins `alpha2.pool.sumfree.adjudicate.adjudicate_gscreen(descriptor, *, seed,
det_budget, num_workers=1)`. Import is FUNCTION-LOCAL; RED until Wave 4.

Marked `slow`: it runs the exact backends and is a release/nightly replay gate.
"""
import pytest


@pytest.mark.slow
def test_same_verdict_across_two_deterministic_runs():
    from alpha2.pool.sumfree.adjudicate import adjudicate_gscreen  # RED until Wave 4

    # A mid-size structured instance whose reported verdict must be stable.
    descriptor = {"invariant_factors": [31], "S": None, "tag": "structured"}

    kw = dict(seed=1, det_budget=1.0, num_workers=1)
    v1 = adjudicate_gscreen(descriptor, **kw)
    v2 = adjudicate_gscreen(descriptor, **kw)

    assert v1["terminal_state"] == v2["terminal_state"]
    assert v1["g"] == v2["g"]
    assert v1["had_3"] == v2["had_3"]


@pytest.mark.slow
def test_reported_verdict_rejects_wallclock_budget():
    # A recorded verdict may only be sought under a DETERMINISTIC budget; passing a
    # wall-clock time budget for a reportable verdict must be refused (Pitfall 2).
    from alpha2.pool.sumfree.adjudicate import adjudicate_gscreen

    descriptor = {"invariant_factors": [31], "S": None, "tag": "structured"}
    with pytest.raises((ValueError, TypeError)):
        adjudicate_gscreen(descriptor, seed=1, wallclock_budget=5.0, num_workers=1)
