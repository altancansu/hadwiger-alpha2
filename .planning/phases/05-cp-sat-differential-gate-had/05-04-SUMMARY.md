---
phase: 05-cp-sat-differential-gate-had
plan: 04
subsystem: testing
tags: [cp-sat, cbc, differential, shc-candidate, metamorphic, python-O, stdlib-only]

# Dependency graph
requires:
  - phase: 05-01
    provides: CP-SAT backend (solvers/cpsat.py) + map_status producing the second independent ExactOutcome the gate cross-checks
  - phase: 04
    provides: frozen Status/ExactOutcome contract (result.py), CBC backend (cbc.py), trust root (verifier.verify_certificate)
provides:
  - "solvers/differential.py: CriticalDisagreement + differential_verdict(a,b,chi) — the SOLE licenser of SHC-CANDIDATE and the mechanism that makes CBC/CP-SAT disagreement release-blocking"
  - "assert_not_below_verified(outcome, verified_k): metamorphic verifier-trumps-solver guard generalizing the seed-137 check across the backend pair"
  - "tests/test_solver_paths_dash_O.py: the shared solver-path -O canary over the new CP-SAT and differential paths"
affects: [phase-06-battery, had_3-escalation, falsification-rule-harness, SHC-CANDIDATE consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-backend agreement gate: two ExactOutcomes -> verdict; only two equal PROVED_OPTIMAL below chi license SHC-CANDIDATE"
    - "Metamorphic guard: verifier's k trumps any solver proof (a proven value below a verified family is CRITICAL by construction)"
    - "Solver-path -O canary: raises-only guards proven fail-closed under python -O via the exit-code 0/2/3 subprocess contract"

key-files:
  created:
    - src/alpha2/solvers/differential.py
    - tests/test_differential.py
    - tests/test_solver_paths_dash_O.py
  modified: []

key-decisions:
  - "differential.py is stdlib-only (imports only Status; no pulp/ortools) and raises-only (0 asserts) — consumes two ExactOutcomes, never produces one"
  - "SHC_CANDIDATE is licensed ONLY when both PROVED_OPTIMAL with equal exact_value() < chi; equal >= chi -> AGREED_KILL; unequal proven -> CriticalDisagreement (quarantine+halt); not-both-proved -> INSUFFICIENT"
  - "Metamorphic assert_not_below_verified consumes verify_certificate's k (trust root), never re-derives it; a non-PROVED_OPTIMAL outcome cannot trip the guard"

patterns-established:
  - "Pattern: the differential gate is the single choke point for any impossibility-flavored (had_2 < chi) claim — a single backend or a best-of-two can never license one"
  - "Pattern: unequal proven optima are release-blocking, never skipped and never resolved by picking a winner"

requirements-completed: [EXACT-04]

# Metrics
duration: 10min
completed: 2026-07-22
---

# Phase 5 Plan 04: Differential Agreement Gate Summary

**stdlib-only `differential_verdict(a,b,chi)` that licenses SHC-CANDIDATE only on two equal PROVED_OPTIMAL below chi, raises `CriticalDisagreement` (quarantine + halt) on unequal proofs, and enforces verifier-trumps-solver — all fail-closed under `python -O`.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-22
- **Tasks:** 2 (RED contract, GREEN gate + -O canary)
- **Files modified:** 3 (all created)

## Accomplishments

- `solvers/differential.py` — `CriticalDisagreement` exception + `differential_verdict(a,b,chi)` implementing the RESEARCH Pattern-2 contract exactly, plus `assert_not_below_verified(outcome, verified_k)` metamorphic guard. The SOLE component permitted to license SHC-CANDIDATE or halt on disagreement.
- Backend disagreement is now release-blocking: two PROVED_OPTIMAL with unequal `exact_value()` raise `CriticalDisagreement` (never "best of two", never skip). Exactly-one-proved is `INSUFFICIENT`, not a disagreement.
- Metamorphic guard (verifier trumps solver): a PROVED_OPTIMAL value below a trust-root-verified size-k family is `CriticalDisagreement`, generalizing the seed-137 check across the CBC/CP-SAT pair.
- `tests/test_solver_paths_dash_O.py` — the shared solver-path `-O` canary: a FEASIBLE CP-SAT optimize outcome never reads as exact, and unequal proven optima still raise under `python -O`.

## Task Commits

Each task was committed atomically (TDD RED -> GREEN):

1. **Task 1: RED — differential gate contract** — `c19e84d` (test)
2. **Task 2: GREEN — differential.py + solver-path -O canary** — `9ae005a` (feat)

**Plan metadata:** this commit (docs: complete plan)

## Files Created/Modified

- `src/alpha2/solvers/differential.py` — `CriticalDisagreement`, `differential_verdict`, `assert_not_below_verified`; stdlib-only, raises-only, 0 asserts, 91 lines.
- `tests/test_differential.py` — 15 tests: AGREED_KILL (real CBC+CP-SAT on C5 and empty-H), SHC_CANDIDATE (hand-built), CriticalDisagreement on unequal proofs (message carries both values), INSUFFICIENT (single/no proof), metamorphic guard (k from `verify_certificate`), no-solver-import (clean subprocess).
- `tests/test_solver_paths_dash_O.py` — two subprocess `-O` canaries (CP-SAT path + differential path), exit-code 0/2/3 contract.

## Decisions Made

- SHC-CANDIDATE gate uses `a.exact_value() != b.exact_value()` (the raises-only exact accessor) rather than raw `.value`, keeping the comparison inside the proved-status gate.
- The `CriticalDisagreement` message surfaces both values and both backend names, so the quarantine log is self-describing.
- The metamorphic guard ignores non-PROVED_OPTIMAL outcomes: only an optimality PROOF can undercut a verified family; an incumbent/unknown is not a fact.

## Deviations from Plan

None - plan executed exactly as written. Both tasks followed the TDD RED -> GREEN flow; all acceptance criteria (stdlib-only grep empty, 0 asserts, five verdict paths + metamorphic, `-O` fail-closed on both new paths) verified green.

## Issues Encountered

None. The plan's verify commands used `uv run`; per the executor toolchain note these were run as `.venv/bin/python -m pytest` (and `.venv/bin/python -O -m pytest`) with identical semantics.

## Known Stubs

None — the gate is fully wired; every verdict path and the metamorphic guard are exercised by real or hand-built outcomes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- EXACT-04 complete: the differential gate is available for the had_3 escalation (a lost size-3 constraint surfaces as one backend > the other) and for the Phase-6 battery runbook step-5 escalation.
- The gate consumes any two `ExactOutcome`s; wiring the seed-137 dual-backend panel (Plan 05-05, `@pytest.mark.slow`) is the next differential consumer.

---
*Phase: 05-cp-sat-differential-gate-had*
*Completed: 2026-07-22*

## Self-Check: PASSED

Files verified present: `src/alpha2/solvers/differential.py`, `tests/test_differential.py`, `tests/test_solver_paths_dash_O.py`.
Commits verified in git log: `c19e84d` (RED test), `9ae005a` (GREEN feat).
Tests: 15 passed (differential + -O canary); 2 passed under `python -O`; broader solver/verifier regression 27 passed. stdlib-only grep empty; 0 asserts in differential.py.
