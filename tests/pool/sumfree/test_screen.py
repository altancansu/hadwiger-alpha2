"""RED contract — g(G) SCREEN + the certificate-HONESTY gate (POOL-2, Wave 3/4).

THE radioactive-impossibility regression (RESEARCH Pitfall 1). The g(G) screen is a
NECESSARY-not-sufficient signal: `had_k < chi` establishes ONLY "no K_chi minor with
branch sets <=3"; it does NOT prove `had(G) < chi` (branch sets of size >=4 are not
excluded). A g>0 record is therefore an SHC_CANDIDATE queued for E3 — NEVER a
"counterexample", NEVER a "had(G) < chi" claim.

This module pins:
  * `alpha2.pool.sumfree.screen.compute_g(chi, had_k)` == (chi - had_k)/chi;
  * `alpha2.pool.sumfree.verifier.verify_gscreen_record` re-derives + re-checks g AND
    fails closed on any record string carrying a radioactive claim
    ("counterexample" / "had(G) <");
  * the honest g>0 statement carries the required literals;
  * a heuristic MISS above the ILP frontier maps to RESISTANT with g == None
    (never a g>0 point).

Imports of the modules-under-test are FUNCTION-LOCAL; bodies RED until Wave 3/4.
"""
import pytest

# The two radioactive substrings a g(G) record may NEVER contain (Pitfall 1).
_RADIOACTIVE = ("counterexample", "had(G) <")


def _all_strings(obj):
    """Yield every string value anywhere in a JSON-native record (deep walk)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _all_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _all_strings(v)


def test_compute_g_matches_killed_fixture(valid_gscreen_record):
    from alpha2.pool.sumfree.screen import compute_g  # RED until Wave 3

    rec = valid_gscreen_record
    assert compute_g(rec["chi"], rec["had_3"]) == rec["g"] == 0.0  # KILLED (packs)


def test_stdlib_verifier_rederives_and_accepts_valid_killed(valid_gscreen_record):
    from alpha2.pool.sumfree.verifier import verify_gscreen_record

    # A genuine g<=0 KILLED record with a hand-verified K_3 minor must verify.
    verify_gscreen_record(valid_gscreen_record)  # must not raise


def test_verifier_rejects_wrong_g(valid_gscreen_record):
    from alpha2.pool.sumfree.verifier import VerificationError, verify_gscreen_record

    rec = valid_gscreen_record
    rec["g"] = -0.5  # inconsistent with (chi - had_3)/chi = 0
    with pytest.raises(VerificationError):
        verify_gscreen_record(rec)


def test_honest_positive_g_statement_has_required_literals(honesty_canary_record):
    # A g>0 SHC_CANDIDATE statement must say only what the screen proves.
    stmt = honesty_canary_record["certificate_statement"]
    assert "no K_chi minor with branch sets <=3" in stmt
    assert "does not prove had(G)" in stmt
    assert "E3" in stmt


def test_honest_canary_scans_clean_of_radioactive_strings(honesty_canary_record):
    for s in _all_strings(honesty_canary_record):
        low = s.lower()
        assert "counterexample" not in low, "a g(G) record may never say 'counterexample'"
        assert "had(G) <" not in s, "a g(G) record may never claim 'had(G) < chi'"


def test_verifier_fails_closed_on_counterexample_claim(honesty_canary_record):
    # The honesty gate lives in the TRUST ROOT: a record mislabeled as a
    # "counterexample" must be refused at verify time, never stored.
    from alpha2.pool.sumfree.verifier import VerificationError, verify_gscreen_record

    rec = honesty_canary_record
    rec["certificate_statement"] = "found a counterexample: had(G) < chi on this instance"
    with pytest.raises(VerificationError):
        verify_gscreen_record(rec)


def test_verifier_fails_closed_on_had_G_less_claim(honesty_canary_record):
    from alpha2.pool.sumfree.verifier import VerificationError, verify_gscreen_record

    rec = honesty_canary_record
    rec["certificate_statement"] = "screen shows had(G) < chi"  # radioactive
    with pytest.raises(VerificationError):
        verify_gscreen_record(rec)


def test_heuristic_miss_above_frontier_is_resistant_with_g_none():
    # A heuristic MISS above the exact ILP frontier is RESISTANT, g == None —
    # it is queued for E3, never recorded as a g>0 candidate point.
    from alpha2.pool.sumfree.screen import classify_screen_outcome

    outcome = classify_screen_outcome(
        chi=200, had_k=None, heuristic_hit=False, exact_proved=False
    )
    assert outcome["terminal_state"] == "RESISTANT"
    assert outcome["g"] is None
