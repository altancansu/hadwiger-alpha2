"""RED contract — P1 large-n showpieces, existence-only (POOL-1, Wave 5; SLOW).

Above the ILP frontier the showpieces are EXISTENCE-ONLY (RESEARCH §"g(G) rigor &
cost"): a large-n (~1001-2001) TFP instance is run through heuristic search + the
trust-root verifier. A heuristic HIT that the verifier confirms is a verified
existence certificate; a MISS is RESISTANT (queued for E3) — NEVER a reported result
(zero heuristic-only claims). Pins
`alpha2.pool.sumfree.p1.run_showpiece(n, *, seed)`.

Import is FUNCTION-LOCAL; RED until Wave 5. Marked `slow` (large-n heuristic engine).
"""
import pytest


@pytest.mark.slow
def test_showpiece_hit_is_trust_root_verified():
    from alpha2.pool.sumfree.p1 import run_showpiece  # RED until Wave 5

    result = run_showpiece(1001, seed=1)
    assert result["n"] == 1001
    assert result["kind"] == "existence_only"
    if result["terminal_state"] == "VERIFIED":
        # A HIT counts only after the independent trust root passes.
        assert result["verified"] is True
        assert result["had_2"] is not None


@pytest.mark.slow
def test_showpiece_miss_is_resistant_never_a_result():
    from alpha2.pool.sumfree.p1 import run_showpiece

    result = run_showpiece(2001, seed=999)
    # Whatever the outcome, a non-HIT is RESISTANT with no exact bound — heuristic
    # resistance is never a result.
    assert result["terminal_state"] in ("VERIFIED", "RESISTANT")
    if result["terminal_state"] == "RESISTANT":
        assert result["verified"] is False
        assert result.get("had_2") is None
