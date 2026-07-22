---
phase: 05-cp-sat-differential-gate-had
plan: 02
subsystem: solvers
tags: [had3, obstruction-model, checksum, seagull, branch-set-3, stdlib, backend-neutral]

# Dependency graph
requires:
  - phase: 04
    provides: "had2.py frozen pattern (ChecksumError, frozen dataclass, enumerate_/build_ with independent checksum gate); tfp.is_triangle_free"
provides:
  - "src/alpha2/solvers/problems/had3.py — Had3Problem frozen dataclass + enumerate_had3 (triple index <=1 H-edge, common-H-neighborhood conflicts) + build_had3_problem (independent structural checksum gate, raise-based)"
  - "Backend-neutral size-3 model data consumed later by both CBC and CP-SAT (Plan 05) — the shared instance that makes had_3 differential agreement meaningful"
affects: [05-03 verifier size-3 extension, 05-05 had3 CBC/CP-SAT differential, plan-05 backends]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Independent structural checksum from degrees/codegrees (not the enumeration's own lists), raise-based ChecksumError — mirrors had2, first of three had_3 guards"
    - "Connectivity-by-indexing: the triple variable index IS the size-3 connectivity constraint (<=1 internal H-edge), never widened to all triples"
    - "Conflict enumeration from the common H-neighborhood W(T), never an all-pairs scan (RESEARCH Pattern 3)"

key-files:
  created:
    - src/alpha2/solvers/problems/had3.py
    - tests/test_had3_problem.py
  modified: []

key-decisions:
  - "Reused had2's ChecksumError (imported + re-exported) rather than defining a size-3 analog — one exception vocabulary across the obstruction models"
  - "Conflict scope = seagull/Tier-1 (triple-single + triple-pair from W(T)); triple-triple (Tier-2, G-triangle-vs-G-triangle) deferred per RESEARCH, matching the plan's explicit 'singletons and G-edge pairs within W'"
  - "Checksum derived in closed form: n_triples = C(n,3) - sum_v C(deg,2); n_conflicts = sum_v C(deg,3) + sum_{u<w} C(codeg,3) — each conflict class is a 3-subset of a (co)neighborhood, giving a degree/codegree recompute fully independent of the enumeration"
  - "Size-3-forced test uses a genuine had_2 < had_3 instance (4 < 5, exhaustively found), NOT a fabricated had_2 < chi: no triangle-free H with had_2 < chi is known (296/296 killed at had_2 — that would be a Hadwiger counterexample), so had_2 < had_3 is the honest escalation signal"

patterns-established:
  - "Independent-naive-reference set-equality test for a non-local substructure (RESEARCH Pitfall 3): the test scans the DEFINITION (all cross pairs are H-edges) while the module uses the W-shortcut"

requirements-completed: [EXACT-05]

# Metrics
duration: 18min
completed: 2026-07-22
---

# Phase 5 Plan 02: had_3 Size-3 Model Data Summary

**Backend-neutral size-3 (seagull-tier) obstruction model: triple index = connected-in-G triples (<=1 internal H-edge), conflicts pruned from the common H-neighborhood, gated by an independent degrees/codegrees structural checksum — the enumeration guard for EXACT-05.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-22
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 2 (both created)

## Accomplishments
- `enumerate_had3(adj, n)` builds the triple index `((b in adj[a]) + (c in adj[a]) + (c in adj[b])) <= 1` (connectivity-by-indexing) and the triple-vs-set conflicts `(T, S)` from each triple's common H-neighborhood `W(T) = N_H(a) & N_H(b) & N_H(c)` (singletons + G-edge pairs).
- `build_had3_problem(adj, n)` re-checks triangle-freeness (raise-based `ValueError`) and passes a raise-based `ChecksumError` gate whose expected counts are recomputed independently from H's degrees/codegrees — never from the enumeration's own lists.
- Independent naive reference (definitional cross-pair-all-H-edges scan) proves the enumeration SET-equal (not just count-equal) on 4 synthetic instances; a genuine `had_2 = 4 < had_3 = 5` forced instance (found exhaustively, hand-frozen) demonstrates the model represents a load-bearing size-3 branch set `{0,5,6}`.
- Module is stdlib-only and imports no solver library (verified by a subprocess `sys.modules` check).

## Task Commits

Each task was committed atomically (TDD):

1. **Task 1: RED — triple index + conflict + checksum contract** - `0e3a563` (test)
2. **Task 2: GREEN — solvers/problems/had3.py** - `7ae780a` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `src/alpha2/solvers/problems/had3.py` - Had3Problem frozen dataclass, enumerate_had3, build_had3_problem with independent checksum gate (backend-neutral, stdlib-only)
- `tests/test_had3_problem.py` - 26 tests: connectivity-by-index set-equality vs naive reference, common-neighborhood conflict pruning, pinned checksum literals, mutation->ChecksumError, triangle refusal, backend-neutrality, size-3-forced instance

## Decisions Made
- Reused `had2.ChecksumError` (imported and re-exported via `__all__`) so tests import it from `had3`.
- Scoped conflicts to the seagull/Tier-1 set (triple-single + triple-pair from `W(T)`), per the plan's explicit "singletons and G-edge pairs within W"; Tier-2 triple-triple conflicts remain deferred (RESEARCH).
- Pinned checksum literals verified against the independent naive reference before coding: C5 `(5,0)`, K_{1,4} `(4,4)`, K_{2,3} `(1,3)`, forced-n7 `(19,6)`.
- The size-3-forced test asserts a genuine `had_2 < had_3` via test-local brute force rather than an unattainable `had_2 < chi` (documented in-test).

## Deviations from Plan

None - plan executed exactly as written. (The verify commands were run with the pinned `.venv/bin/python -m pytest` per the task toolchain instruction instead of `uv run`; identical environment, no behavioral change.)

## Issues Encountered
- Confirming a genuine size-3-forced instance required an exhaustive search: random maximal-triangle-free graphs at n=7 yield `had_2 = 4 < had_3 = 5` (chi = 4); no triangle-free H with `had_2 < chi` exists at reachable n (consistent with the 296/296-killed corpus). Resolved by pinning the had_2<had_3 instance and stating the epistemic caveat in the test.

## Verification
- `.venv/bin/python -m pytest tests/test_had3_problem.py -q` → 26 passed.
- `grep -E "import (pulp|ortools)" src/alpha2/solvers/problems/had3.py` → empty (backend-neutral).
- `.venv/bin/python -m pytest -q -m "not slow"` → 159 passed, 5 deselected (existing suite unaffected; only pre-existing pulp DeprecationWarnings).

## Next Phase Readiness
- `Had3Problem` is ready for translation by both backends in Plan 05 (the shared instance that makes CBC-vs-CP-SAT had_3 agreement meaningful).
- The trust-root verifier size-3 extension (Plan 03) is the second of the three independent guards; the had_3 differential (Plan 05) is the third.

## Self-Check: PASSED

- Files verified present: `src/alpha2/solvers/problems/had3.py`, `tests/test_had3_problem.py`, `05-02-SUMMARY.md`
- Commits verified in git log: `0e3a563` (test/RED), `7ae780a` (feat/GREEN)

---
*Phase: 05-cp-sat-differential-gate-had*
*Completed: 2026-07-22*
