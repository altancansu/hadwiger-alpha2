"""The differential agreement gate (EXACT-04) — stdlib ONLY, the SOLE licenser.

This module cross-examines two `ExactOutcome`s produced for the SAME instance by
two INDEPENDENT exact engines (CBC + CP-SAT) and returns a verdict. It is the
only component permitted to license an SHC-CANDIDATE and the only place where a
backend disagreement becomes release-blocking.

Trust-boundary discipline (mirrors `result.py` / `backend.py`):

  * stdlib ONLY. It imports the frozen `Status` enum and consumes two already-
    built `ExactOutcome`s; it imports NO solver library (no pulp, no ortools).
    Its whole job is to compare two outcomes, never to produce one.
  * Every guard RAISES — these are impossibility-adjacent checks that must
    survive `python -O`; nothing here is an optimization-strippable `assert`.
  * An `ExactOutcome.family` remains an UNTRUSTED proposal even after a verdict:
    the frozen trust root (`corpus/verifier.verify_certificate`) is still the
    ONLY component that confers truth on a family. The metamorphic guard below
    consumes the trust root's answer (a verified size k); it never re-derives it.

The verdict contract (optimize mode), from RESEARCH Pattern 2 / ARCHITECTURE
§Differential testing:

  both_proved = a.status is PROVED_OPTIMAL and b.status is PROVED_OPTIMAL
  both_proved and a.exact_value() != b.exact_value()  -> raise CriticalDisagreement
  not both_proved                                     -> "INSUFFICIENT"
  a.exact_value() < chi                               -> "SHC_CANDIDATE"
  else                                                -> "AGREED_KILL"

Two exact solvers cannot both be right about an optimum, so unequal PROVED_OPTIMAL
is a solver/encoding bug BY CONSTRUCTION: it quarantines the instance and HALTS
the batch (release-blocking) — never "best of two", never skip. Exactly one proof
(the other a timeout/incumbent/unknown) is INSUFFICIENT evidence, not a
disagreement: a single proof licenses no impossibility-flavored claim.
"""
from alpha2.solvers.result import Status


class CriticalDisagreement(Exception):
    """Release-blocking: two exact proofs conflict (or a proof undercuts a
    verified family). Quarantine the instance and HALT the batch — a solver or
    encoding-translation bug is present by construction; never skip, never pick
    a winner between backends."""


def differential_verdict(a, b, chi):
    """Cross-examine two optimize outcomes for one instance; return the verdict.

    `a` (e.g. CBC) and `b` (e.g. CP-SAT) are `ExactOutcome`s for the SAME
    instance/mode. Returns one of "SHC_CANDIDATE", "AGREED_KILL", "INSUFFICIENT";
    raises `CriticalDisagreement` when both are PROVED_OPTIMAL at UNEQUAL value.

    SHC-CANDIDATE is licensed ONLY when BOTH outcomes are PROVED_OPTIMAL with the
    SAME exact value AND that value < chi. Equal proven value >= chi is
    AGREED_KILL. Anything short of two matching proofs is INSUFFICIENT.

    Defense-in-depth (mirrors `result.__post_init__` / the backends' bool
    rejection): the gate compares two solves of ONE instance in ONE mode. Pairing
    a had_2 outcome with a had_3 outcome — or an optimize with a decision outcome
    — compares two INCOMPARABLE quantities and is a caller bug, not a verdict;
    both are rejected up front (raises-only, so `python -O` cannot strip them).
    """
    if a.problem != b.problem or a.mode != b.mode:
        raise CriticalDisagreement(
            f"mismatched outcomes: a=({a.problem},{a.mode}) b=({b.problem},{b.mode}) "
            "— the differential gate compares two solves of ONE instance/mode"
        )
    if a.mode != "optimize":
        raise ValueError("differential_verdict is an optimize-mode gate")
    both_proved = (
        a.status is Status.PROVED_OPTIMAL and b.status is Status.PROVED_OPTIMAL
    )
    if both_proved and a.exact_value() != b.exact_value():
        # Two exact solvers disagree on the optimum: quarantine + halt.
        raise CriticalDisagreement(
            f"unequal proven optima on one instance (release-blocking): "
            f"a={a.exact_value()} ({a.backend}) b={b.exact_value()} ({b.backend})"
        )
    if not both_proved:
        # A timeout/incumbent/unknown on either side: no impossibility claim,
        # no SHC-CANDIDATE from a single proof.
        return "INSUFFICIENT"
    # Both proved and equal: the value is now a FACT for this instance.
    return "SHC_CANDIDATE" if a.exact_value() < chi else "AGREED_KILL"


def assert_not_below_verified(outcome, verified_k):
    """Metamorphic guard — the verifier trumps the solver.

    A verified model of size k proves had_2 >= k. If a backend returns
    PROVED_OPTIMAL with a value BELOW a family the frozen trust root has already
    verified (a stored corpus family, or the other backend's just-verified
    family), that is a solver/encoding bug BY CONSTRUCTION: raise
    `CriticalDisagreement` — quarantine, no corpus write.

    `verified_k` MUST come from `corpus/verifier.verify_certificate` (or the
    equivalent trust-root call), never from a solver flag. A non-PROVED_OPTIMAL
    outcome is not a proof and cannot trip this guard.
    """
    if outcome.status is Status.PROVED_OPTIMAL and outcome.exact_value() < verified_k:
        raise CriticalDisagreement(
            f"proved optimum {outcome.exact_value()} ({outcome.backend}) is below "
            f"a verified family of size {verified_k}: verifier trumps solver "
            "(quarantine, no corpus write)"
        )
