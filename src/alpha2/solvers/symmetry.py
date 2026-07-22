"""Assume-and-verify symmetry-breaking discipline (EXACT-06) — stdlib ONLY.

Trust-boundary contract:

  * This module is pure control-flow discipline: it imports ONLY the frozen
    `Status` enum and consumes `ExactOutcome`s (or a zero-arg rerun callable).
    It imports NO solver library — not pulp, not ortools, and NOT pynauty. The
    sound acceleration path is CP-SAT's internal `symmetry_level`
    (objective-preserving, sound by construction); hand orbit / lex-leader SB
    derived from a computed `Aut(H)` (pynauty) is DEFERRED to when
    vertex-transitive pools actually run — no EXACT-06 criterion needs it.
  * Symmetry breaking is standard but treacherous. On a vertex-transitive (or
    trivial-`Aut`) instance a "WLOG vertex 0 unused" hand constraint can be
    satisfied by NO optimum, fabricating a sub-chi (had_2 < chi) counterexample
    — the H = C5 disaster. SB may ACCELERATE the existence branch, but it may
    NEVER own an impossibility-flavored conclusion.
  * `assume_and_verify` enforces the asymmetric rule: any impossibility-flavored
    (PROVED_OPTIMAL, value < chi) SB-on outcome is rerun WITHOUT symmetry
    breaking before it is returned/recorded/entered into the differential gate;
    an unguarded attempt to surface such an outcome raises
    `SBContaminationError`. An outcome that verifies >= chi is the existence
    branch (the certificate self-justifies) and passes through unchanged.
  * Every guard here raises — these checks are impossibility-adjacent and must
    survive Python's optimized mode (`python -O`). None is an `assert`.
"""
from alpha2.solvers.result import Status


class SBContaminationError(Exception):
    """A symmetry-broken run produced an impossibility-flavored (< chi) outcome
    that was not re-verified without symmetry breaking.

    Raised when `assume_and_verify` is handed a < chi SB-on outcome and no
    no-SB rerun callable — the outcome may NEVER surface as-is, because a
    symmetry constraint satisfied by no optimum fabricates a sub-chi
    counterexample (the C5 "WLOG vertex unused" disaster).
    """


def is_impossibility_flavored(outcome, chi):
    """True iff `outcome` is an impossibility-flavored exact conclusion (< chi).

    The exact_value() read is GUARDED: it is reachable only after confirming
    PROVED_OPTIMAL (its sole legal status), so no weaker outcome can trip the
    accessor's `NotProvedOptimal`. Any non-proven status is not an
    impossibility conclusion SB could own, so it returns False.
    """
    if outcome.status is not Status.PROVED_OPTIMAL:
        return False
    return outcome.exact_value() < chi


def assume_and_verify(sb_outcome, rerun_no_sb, *, chi):
    """Enforce the assume-and-verify rule on a symmetry-broken outcome.

    Contract:
      * If `sb_outcome` is impossibility-flavored (PROVED_OPTIMAL, value < chi),
        symmetry breaking may not own it: rerun WITHOUT SB and return that no-SB
        outcome. If `rerun_no_sb` is None, raise `SBContaminationError` — the
        fabricated < chi conclusion must never surface unre-verified.
      * Otherwise (the existence branch: value >= chi, or any non-proven
        status) the outcome self-justifies and is returned UNCHANGED — no rerun
        is forced.

    `rerun_no_sb` is a zero-arg callable that re-solves the same instance with
    symmetry breaking OFF (e.g. `lambda: backend.solve_had2(adj, n,
    mode="optimize")` with no `symmetry_level`).
    """
    if is_impossibility_flavored(sb_outcome, chi):
        if rerun_no_sb is None:
            raise SBContaminationError(
                f"symmetry-broken run produced an impossibility-flavored outcome "
                f"(value={sb_outcome.value!r} < chi={chi!r}) with no no-SB rerun: "
                "SB may never own a < chi conclusion"
            )
        return rerun_no_sb()
    return sb_outcome


def solve_had2_sound_sb(backend, adj, n, *, mode, chi, symmetry_level, params=None):
    """Convenience: solve had_2 with the SOUND SB path, then assume-and-verify.

    Runs `backend.solve_had2(..., symmetry_level=symmetry_level)` — CP-SAT's
    internal, objective-preserving symmetry handling (the sound path; no new
    dependency) — and routes the result through `assume_and_verify` with a
    no-SB rerun (`symmetry_level` omitted) as the guard. Any < chi conclusion is
    therefore re-verified without symmetry breaking before it is returned.
    """
    sb_outcome = backend.solve_had2(
        adj, n, mode=mode, params=params, symmetry_level=symmetry_level
    )

    def rerun_no_sb():
        return backend.solve_had2(adj, n, mode=mode, params=params)

    return assume_and_verify(sb_outcome, rerun_no_sb, chi=chi)
