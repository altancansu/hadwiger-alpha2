---
phase: 05-cp-sat-differential-gate-had
plan: 01
subsystem: solvers
tags: [ortools, cp-sat, cp_model, exact-backend, status-honesty, determinism, had2, trust-root]

# Dependency graph
requires:
  - phase: 04-exact-backend-cbc
    provides: "ExactBackend Protocol + lazy registry (backend.py), status-honest ExactOutcome/Status/NotProvedOptimal (result.py), checksum-gated Had2Problem (problems/had2.py), the cbc.py reference adapter this mirrors"
  - phase: 02-corpus-schema-store
    provides: "corpus.verifier.verify_certificate trust root + schema.build_record/make_backends (ortools stamp routing)"
provides:
  - "solvers/cpsat.py — CP-SAT second independent exact backend (the ONLY ortools importer), registered as 'cpsat'"
  - "map_status two-condition PROVED_OPTIMAL gate (OPTIMAL AND round(obj)==round(bound)) + FEASIBLE->INCUMBENT_ONLY honesty"
  - "Deterministic recorded mode: num_workers=1 + pinned random_seed (Open-Q4 resolved)"
  - "Guarded extraction (recompute + disjointness) inside the status gate; ortools version stamp"
  - "Two green test panels: test_cpsat_backend.py + test_cpsat_status_honesty.py"
affects: [05-04-differential-gate, 05-05-had3-backends, 05-07-dual-backend-panel, 05-06-symmetry]

# Tech tracking
tech-stack:
  added: ["ortools CP-SAT (cp_model / CpSolver) — already pinned at 9.15.6755, now wired into a backend"]
  patterns:
    - "Second exact engine as a near-line-for-line mirror of cbc.py, swapping pulp->cp_model over the SAME checksum-gated Had2Problem"
    - "Two-condition status gate: PROVED_OPTIMAL iff status==OPTIMAL AND round(objective_value)==round(best_objective_bound)"
    - "Determinism by construction: num_workers=1 + pinned random_seed; log archived (log_to_stdout=False), never interleave_search for recorded claims"
    - "Extraction confined to the status gate; CP-SAT booleans are exact so the CBC integrality loop is dropped but recompute + disjointness guards are kept"

key-files:
  created:
    - "src/alpha2/solvers/cpsat.py"
    - "tests/test_cpsat_backend.py"
    - "tests/test_cpsat_status_honesty.py"
  modified: []

key-decisions:
  - "Recorded-mode determinism = num_workers=1 + pinned module-constant random_seed (137), resolving RESEARCH Open-Q4; interleave_search deliberately NOT used (reserved for later exploration/survivor scaling)."
  - "cpsat.py is the ONLY ortools importer; it reuses the frozen build_had2_problem (no re-enumeration) and mirrors cbc.py structurally — independent encoding of an identical instance is what makes CBC-vs-CP-SAT agreement meaningful."
  - "The CBC `p.threads != 1` guard was NOT ported; CP-SAT's determinism contract is num_workers=1, so num_workers is set unconditionally (threads is not the CP-SAT knob)."
  - "Non-optimal optimize bound = round(best_objective_bound) when finite else n, always bound_source='trivial_n' — no cbc_log analog was invented."
  - "Search log archived with log_to_stdout=False (the faithful analog of CBC's msg=0 + logPath file) to keep log_search_progress on without spamming test output."

patterns-established:
  - "Pattern: a new ExactBackend is a structural copy of the frozen reference adapter — only the solver library, its status vocabulary, and the model-build calls change."
  - "Pattern: map_status is a pure function that reads the solver ONLY on the OPTIMAL branch, so the status table is unit-testable with a two-field solver stub."

requirements-completed: [EXACT-03]

# Metrics
duration: 14min
completed: 2026-07-22
---

# Phase 05 Plan 01: CP-SAT Second Exact Backend Summary

**A status-honest OR-Tools CP-SAT backend (`solvers/cpsat.py`, the only ortools importer) that translates the frozen Had2Problem, solves H=C5 to PROVED_OPTIMAL had_2=3 end-to-end through the trust root, and makes a FEASIBLE incumbent structurally unable to read as an exact value — with num_workers=1 + pinned-seed determinism.**

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-07-22
- **Tasks:** 3 (all TDD)
- **Files created:** 3

## Accomplishments
- `solvers/cpsat.py`: the second independent exact engine — reuses the checksum-gated `Had2Problem`, translates it to a CP-SAT model (Bool pair/singleton vars, AddAtMostOne conflict rows in sorted order), and returns a frozen `ExactOutcome` with an `ortools==9.15.6755` stamp.
- Status honesty is the load-bearing work: PROVED_OPTIMAL is gated on `status==OPTIMAL AND round(objective_value)==round(best_objective_bound)`; FEASIBLE(optimize)->INCUMBENT_ONLY and `exact_value()` raises `NotProvedOptimal`; INFEASIBLE(optimize)->ERROR (never PROVED_INFEASIBLE).
- Deterministic recorded mode wired and proven: `num_workers==1` + pinned `random_seed` are introspected at `solve()` time.
- End-to-end vertical slice green: C5 optimize -> PROVED_OPTIMAL=3 -> `verify_certificate` returns 3; empty-H(n=5) -> 5; decision both legs (k=3 MODEL_FOUND, k=4 PROVED_INFEASIBLE); bool `target_k` rejected; n<=8 brute-force second-engine differential.

## Task Commits

Each task was committed atomically (TDD RED -> GREEN -> hardening):

1. **Task 1: RED — CP-SAT backend panel** - `b24c7f6` (test) — failing end-to-end panel pinning the EXACT-03 contract (get_backend("cpsat") raises ValueError: intended RED).
2. **Task 2: GREEN — solvers/cpsat.py adapter** - `5db6e57` (feat) — thinnest slice that passes the panel; ortools confined to this module; `register_backend("cpsat", ...)`.
3. **Task 3: Status-honesty hardening** - `9e28d21` (test) — pure map_status table, FEASIBLE!=OPTIMAL, obj==bound gate, tight-budget live incumbent, determinism introspection.

**Plan metadata:** (this commit) — docs: SUMMARY + STATE + ROADMAP + REQUIREMENTS.

## Files Created/Modified
- `src/alpha2/solvers/cpsat.py` - CP-SAT ExactBackend adapter: map_status two-condition gate, guarded extraction, num_workers=1 + random_seed determinism, optional symmetry_level pass-through, ortools stamp, registers "cpsat". (233 lines)
- `tests/test_cpsat_backend.py` - E2E panel: C5->3 through verify_certificate, empty-H->n, decision both legs, bool target_k rejection, ortools stamp, independent n<=8 brute differential.
- `tests/test_cpsat_status_honesty.py` - FEASIBLE!=OPTIMAL (INCUMBENT_ONLY), obj==bound gate, exact_value raises off the gate, pure map_status table, determinism params introspected at solve time.

## Decisions Made
- **Determinism knob (Open-Q4):** `num_workers=1` + pinned module-constant `random_seed=137` for recorded/impossibility mode; `interleave_search` deliberately unused.
- **No threads guard ported:** CP-SAT determinism is `num_workers`, not `threads`; `num_workers=1` is set unconditionally rather than rejecting `threads != 1`.
- **Bound provenance:** non-optimal optimize bound uses `round(best_objective_bound)` when finite else `n`, always tagged `trivial_n` (no `cbc_log` analog fabricated).
- **Log discipline:** `log_search_progress=True` + `log_to_stdout=False` mirrors CBC's `msg=0` + `logPath` (archive without stdout spam).

## Deviations from Plan

None - plan executed exactly as written. The three TDD tasks (RED panel, GREEN adapter, status-honesty hardening) landed as specified; no frozen files (cbc.py, result.py, backend.py, problems/had2.py) were touched; ortools stayed confined to cpsat.py.

## Issues Encountered
- **Test-output noise risk from CP-SAT logging:** `log_search_progress=True` (mandated by the plan) can emit C-level logs that bypass pytest capture. Resolved within the plan's intent by also setting `log_to_stdout=False` — the search log stays available/archivable (the CBC `logPath` analog) without polluting the console. Not a deviation: it is the faithful reading of "archive the log" for the CP-SAT backend.

## Verification
- `.venv/bin/python -m pytest tests/test_cpsat_backend.py tests/test_cpsat_status_honesty.py -q` -> 19 passed.
- Confinement: `grep -rn "import ortools\|from ortools" src/alpha2 | grep -v cpsat.py` -> empty (only cpsat.py imports the library; schema.py/repro references are strings/comments).
- Regression: `.venv/bin/python -m pytest -q -m "not slow"` -> 133 passed, 5 deselected (only pre-existing pulp deprecation warnings, out of scope).
- Frozen files unchanged: cbc.py, result.py, backend.py, problems/had2.py all clean in `git status`.

## Next Phase Readiness
- The second engine is real and status-honest — the precondition for the differential gate (05-04), had_3-on-both-backends (05-05), and the dual-backend seed-137=17 panel (05-07).
- `solve_had2(..., symmetry_level=...)` pass-through is already present, ready for the assume-and-verify symmetry work (05-06).
- Open follow-ups tracked in RESEARCH (not blockers for 05-01): A2 CP-SAT seed-137 optimize wall-time is still unmeasured (feeds the 05-07 slow-tier budget).

## Self-Check: PASSED

- Files created: cpsat.py, test_cpsat_backend.py, test_cpsat_status_honesty.py, 05-01-SUMMARY.md — all FOUND.
- Task commits: b24c7f6 (test/RED), 5db6e57 (feat/GREEN), 9e28d21 (test/hardening) — all FOUND.
- Tests: 19 passed (both cpsat panels); 133 passed / 5 deselected full non-slow suite.

---
*Phase: 05-cp-sat-differential-gate-had*
*Completed: 2026-07-22*
