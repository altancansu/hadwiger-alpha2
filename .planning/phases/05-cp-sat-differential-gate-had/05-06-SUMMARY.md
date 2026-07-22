---
phase: 05-cp-sat-differential-gate-had
plan: 06
subsystem: solvers
tags: [symmetry, assume-and-verify, sb-contamination, c5-disaster, symmetry_level, cpsat, radioactive-impossibility, EXACT-06]

# Dependency graph
requires:
  - phase: 05-cp-sat-differential-gate-had
    provides: CPSATBackend.solve_had2(..., symmetry_level=<int>) — the sound SB path (Plan 01)
  - phase: 05-cp-sat-differential-gate-had
    provides: Status enum + ExactOutcome.exact_value() (< chi detection over the frozen trust contract) — Plan 01/Phase 04
provides:
  - solvers/symmetry.py — SBContaminationError + assume_and_verify(sb_outcome, rerun_no_sb, *, chi) enforcing the rerun-without-SB rule for any < chi conclusion
  - is_impossibility_flavored(outcome, chi) — guarded (< chi) detector, exact_value() reachable only after PROVED_OPTIMAL
  - solve_had2_sound_sb convenience: CP-SAT symmetry_level sound path routed through assume_and_verify with a no-SB rerun guard
  - The H=C5 "WLOG vertex 0 unused" disaster as a passing regression (invalid hand SB -> had_2=2 < 3=chi -> discipline -> 3)
affects: [05-differential-gate, 06-battery, runbook-step-4-symmetry, vertex-transitive-pools-P2-P3]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Assume-and-verify asymmetry: SB may accelerate the EXISTENCE branch, but any impossibility-flavored (< chi) SB-on outcome is rerun WITHOUT symmetry breaking before it is returned/recorded/entered into the differential gate; an unguarded attempt raises SBContaminationError"
    - "Sound SB path = CP-SAT internal symmetry_level (objective-preserving, sound by construction) — no new dependency; hand orbit/lex-leader SB (pynauty) DEFERRED, no EXACT-06 criterion needs it"
    - "stdlib-only control-flow discipline: symmetry.py imports ONLY the frozen Status enum; NO pulp/ortools/pynauty; raises-only (0 asserts, -O-correct)"

key-files:
  created:
    - src/alpha2/solvers/symmetry.py
    - tests/test_symmetry_assume_verify.py
  modified: []

key-decisions:
  - "pynauty DEFERRED (RESEARCH Open-Q2): EXACT-06's MVP is fully satisfiable without it. The C5 disaster uses a deliberately-INVALID hand constraint built inline in the test; the sound path uses CP-SAT symmetry_level. Orbit/lex-leader SB from a computed Aut(H) pays off only when vertex-transitive pools run (Phases 8-9) — deferred there, not descoped."
  - "The C5 fabrication is built INLINE in the test (cp_model + the 'vertex 0 unused' hand constraint: sv[0]==0 AND every G-edge touching 0 forced off) -> CP-SAT proves OPTIMAL objective 2, wrapped in an ExactOutcome(had_2=2). Verified live: the honest no-SB solve returns 3. The fabricated family is two singletons [(2,),(4,)]."
  - "assume_and_verify RETURNS the no-SB rerun outcome for a < chi conclusion (not the SB one); >= chi passes through UNCHANGED by identity (existence branch self-justifies, no rerun forced). is_impossibility_flavored guards exact_value() behind a PROVED_OPTIMAL check so a non-proven status can never trip NotProvedOptimal."

patterns-established:
  - "SB can accelerate existence but can NEVER own an impossibility conclusion — enforced structurally: the < chi path either reruns without SB or raises. The impossibility branch is never contaminated (CLAUDE.md radioactive-impossibility)."
  - "On/off differential as the soundness tripwire for the sound path: had_2(symmetry_level=2) == had_2(no SB) on a small vertex-transitive battery (C5 -> 3, empty-H=K5 -> 5)."

requirements-completed: [EXACT-06]

# Metrics
duration: 10min
completed: 2026-07-22
---

# Phase 05 Plan 06: Assume-and-Verify Symmetry Breaking Summary

**`solvers/symmetry.py` encodes the assume-and-verify discipline (stdlib-only, imports only the frozen `Status`): any impossibility-flavored (< χ) symmetry-broken outcome is rerun WITHOUT symmetry breaking before it can surface, or raises `SBContaminationError` — and the H=C₅ "WLOG vertex 0 unused" disaster (an invalid hand constraint that fabricates had₂=2 < 3=χ) is now a passing regression whose fabrication the discipline replaces with the honest had₂=3.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-22
- **Tasks:** 2 (TDD RED + GREEN)

## What Was Built

### Task 1 (RED) — `tests/test_symmetry_assume_verify.py`
Six tests pinning the disaster and the discipline before the wrapper existed:
- `test_c5_sb_fabricates_sub_chi` — builds the C₅ had₂ CP-SAT model INLINE with the invalid "vertex 0 unused" hand constraint (`sv[0]==0` and every G-edge touching vertex 0 forced off); CP-SAT proves **OPTIMAL objective 2**, a fabricated had₂=2 < 3=χ, wrapped in an `ExactOutcome`.
- `test_assume_verify_restores_had2_3` — `assume_and_verify(fabricated_2, rerun_no_sb, chi=3)` reruns without SB and returns **3**.
- `test_unguarded_sub_chi_raises` — `rerun_no_sb=None` on the < χ outcome raises `SBContaminationError`.
- `test_existence_branch_passthrough` — a genuine SB-on solve (sound path, `symmetry_level=2`) that reaches χ is returned **unchanged** (the rerun callable raises if called, proving it is not).
- `test_on_off_differential` (parametrized C₅, empty-H=K₅) — `had₂(symmetry_level=2) == had₂(no SB)`.
- `test_no_pynauty_import` — a subprocess imports `alpha2.solvers.symmetry` and asserts none of `pynauty`/`ortools`/`pulp` entered `sys.modules`.

Failed RED with `ModuleNotFoundError: No module named 'alpha2.solvers.symmetry'`.

### Task 2 (GREEN) — `src/alpha2/solvers/symmetry.py`
Stdlib-only (imports ONLY `from alpha2.solvers.result import Status`), raises-only (0 `assert`), 96 lines:
- `SBContaminationError(Exception)`.
- `is_impossibility_flavored(outcome, chi)` — `False` unless `PROVED_OPTIMAL`, then `exact_value() < chi` (the `exact_value()` read is reachable only past the status gate).
- `assume_and_verify(sb_outcome, rerun_no_sb, *, chi)` — < χ ⇒ rerun without SB (or `SBContaminationError` if no rerun); otherwise return `sb_outcome` unchanged.
- `solve_had2_sound_sb(backend, adj, n, *, mode, chi, symmetry_level, params=None)` — sound-path convenience: `symmetry_level` solve routed through `assume_and_verify` with a no-SB rerun guard.

## Verification

- `.venv/bin/python -m pytest tests/test_symmetry_assume_verify.py -q` → **7 passed** (6 tests, C₅+K₅ parametrization = 7 cases).
- `.venv/bin/python -m pytest -q -m "not slow"` → **193 passed, 5 deselected** (no regression).
- `grep -E "import (pulp|ortools|pynauty)" src/alpha2/solvers/symmetry.py` → empty (stdlib-only confirmed).
- `grep -c "assert " src/alpha2/solvers/symmetry.py` → `0` (raises-only, `-O`-correct).

## Deviations from Plan

None — plan executed exactly as written. The RESEARCH-flagged Open-Q2 (defer pynauty) was resolved as specified: no `[nauty]` extra installed, sound path via `symmetry_level`, disaster via an inline invalid hand constraint. The `uv run --frozen --extra dev pytest` verification commands were run with the equivalent `.venv/bin/python -m pytest` per the execution toolchain directive (same interpreter, same pinned env).

## Authentication Gates

None.

## Known Stubs

None. `symmetry.py` is fully wired: `assume_and_verify` consumes real `ExactOutcome`s and a real no-SB rerun callable, `solve_had2_sound_sb` drives a real backend. `solve_had2_sound_sb` is a convenience helper (not yet a differential-gate caller); its consumer wiring lands with the battery (Phase 6, runbook step 4) — this is deferred integration, not a stub blocking EXACT-06, whose success criteria are all met by the tested discipline + C₅ regression + on/off differential.

## Self-Check: PASSED

- FOUND: src/alpha2/solvers/symmetry.py
- FOUND: tests/test_symmetry_assume_verify.py
- FOUND: .planning/phases/05-cp-sat-differential-gate-had/05-06-SUMMARY.md
- FOUND commit: 0c3ec6f (RED test)
- FOUND commit: 2a7cc86 (GREEN symmetry.py)
