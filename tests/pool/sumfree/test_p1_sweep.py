"""RED contract — P1 TFP critical-size sweep (POOL-1, Wave 5 target; SLOW).

P1 (secondary): extend the TFP critical-size sweep to n=31/32 with new seeds, driven
through the P1 runner, producing EXACT had_2 verdicts consistent with the frozen
corpus lineage (same generator + trust-root verifier the 296-corpus uses). Pins
`alpha2.pool.sumfree.p1.run_p1_tfp(n, *, seed, det_budget, num_workers=1)`.

Import is FUNCTION-LOCAL; RED until Wave 5. Marked `slow` (n >= 14 -> exact backends).
"""
import pytest


@pytest.mark.slow
@pytest.mark.parametrize("n", [31, 32])
def test_p1_tfp_produces_exact_had2_verdict(n):
    from alpha2.pool.sumfree.p1 import run_p1_tfp  # RED until Wave 5

    verdict = run_p1_tfp(n, seed=1, det_budget=5.0, num_workers=1)
    assert verdict["n"] == n
    # An exact had_2 sweep point: either optimality PROVED (a result) or RESISTANT
    # (queued) — never a heuristic-only number.
    assert verdict["terminal_state"] in ("DECIDED", "RESISTANT")
    if verdict["terminal_state"] == "DECIDED":
        assert isinstance(verdict["had_2"], int)
        assert verdict["optimality_proved"] is True


@pytest.mark.slow
def test_p1_tfp_is_deterministic_in_seed():
    from alpha2.pool.sumfree.p1 import run_p1_tfp

    kw = dict(seed=7, det_budget=5.0, num_workers=1)
    assert run_p1_tfp(31, **kw) == run_p1_tfp(31, **kw)  # rebuildable from (n, seed)
