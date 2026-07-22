---
phase: 04-exactbackend-cbc-reference
plan: 01
subsystem: solvers
tags: [pulp, cbc, ilp, had2, status-contract, exact-backend, tdd]

# Dependency graph
requires:
  - phase: 01-pinned-environment-verbatim-port
    provides: "generators/tfp.is_triangle_free (build-time re-check), invariants/matching + witness (emission-time chi witness), pulp==3.3.2 pinned in uv.lock with bundled CBC 2.10.3"
  - phase: 02-trust-root-corpus-schema
    provides: "corpus/verifier.verify_certificate (raise-based trust root), corpus/schema.build_record + provenance_params (truncation-refusing schema-v1 assembly)"
provides:
  - "src/alpha2/solvers/result.py — six-member Status enum, NotProvedOptimal, frozen SolveParams + ExactOutcome with raise-based post-init invariants and the raising exact_value() accessor (stdlib-only)"
  - "src/alpha2/solvers/backend.py — ExactBackend Protocol + register_backend/get_backend lazy registry (importing contracts never loads pulp)"
  - "src/alpha2/solvers/problems/had2.py — obstruction enumeration (H-edges/cherries/C4 diagonals, frozenset dedup) + raise-based structural checksum gate on EVERY build (ChecksumError)"
  - "src/alpha2/solvers/cbc.py — sole pulp importer; PULP_CBC_CMD adapter with the two-field PROVED_OPTIMAL gate, guarded extraction, decision mode, Upper-bound log parse, CBC banner version probe"
  - "tests/test_solver_result.py + tests/test_cbc_backend.py — status-contract units, locked mapping table, C5/empty-H E2E through verify_certificate, decision-mode legs"
affects: [04-02 status-honesty timeout + AST/-O guards, 04-03 enumeration set-equality proof, 04-04 seed-137 regression, phase-05 CP-SAT backend (consumes Had2Problem + backend registry)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-field optimality gate: PROVED_OPTIMAL iff prob.status == LpStatusOptimal AND prob.sol_status == LpSolutionOptimal — prob.status alone is provably insufficient (pulp 3.3.2 maps timed-out incumbents to status=Optimal)"
    - "Raising accessor as the type-level soundness boundary: exact_value() raises NotProvedOptimal on every non-proven status; 'had2 from an incumbent' is unrepresentable"
    - "Lazy backend registry: get_backend(name) importlib-imports alpha2.solvers.{name} on demand — pulp confinement at registry level (matching.py precedent)"
    - "Guarded extraction: status gate -> integrality (1e-6 of {0,1}) -> objective recompute (decision: target constraint) -> internal disjointness; any trip maps to Status.ERROR, values never surface"
    - "Structural checksum gate on every model build: nss=|E(H)|, nsp=sum C(deg,2), npp=half sum C(codeg,2) independently recomputed; mismatch raises ChecksumError"

key-files:
  created:
    - "src/alpha2/solvers/__init__.py"
    - "src/alpha2/solvers/result.py"
    - "src/alpha2/solvers/backend.py"
    - "src/alpha2/solvers/problems/__init__.py"
    - "src/alpha2/solvers/problems/had2.py"
    - "src/alpha2/solvers/cbc.py"
    - "tests/test_solver_result.py"
    - "tests/test_cbc_backend.py"
  modified: []

key-decisions:
  - "CBC backend enforces single-thread raise-based (SolveParams.threads != 1 -> ValueError) and passes a literal threads=1 to PULP_CBC_CMD — the deterministic reference-lineage contract from CLAUDE.md made structural, not advisory"
  - "Decision-mode recompute guard checks len(family) >= target_k instead of objective equality (the decision objective is the constant 0, so the target constraint IS the recompute)"
  - "Decision-mode (Optimal, IntegerFeasible) maps to MODEL_FOUND — a stopped-with-incumbent feasibility run still yields a witness; the trust root arbitrates it like any other proposal"
  - "build_had2_problem reuses frozen generators/tfp.is_triangle_free read-only for the build-time re-check (Don't-Hand-Roll; the frozen module is imported, never modified)"

patterns-established:
  - "Pattern: status-honest solve pipeline — build_had2_problem (checksum gate) -> C.3-shape LpProblem -> PULP_CBC_CMD(msg=0, threads=1, timeLimit, logPath) -> map_status two-field gate -> guarded extraction -> ExactOutcome; Phase 5's CP-SAT adapter copies this shape over the same Had2Problem"
  - "Pattern: solver family routed through the trust root as an in-memory schema-v1 record (extract_witness -> build_record -> verify_certificate) — no corpus write, verify call outside the truth-expression"

requirements-completed: [EXACT-01, EXACT-02]

# Metrics
duration: ~12min
completed: 2026-07-22
---

# Phase 4 Plan 01: ExactBackend Contracts + CBC Reference Slice Summary

**Status-honest exact had₂ solving landed as a real vertical slice: six-status contract with raising `exact_value()`, checksum-gated obstruction enumeration, and a PULP_CBC_CMD adapter whose PROVED_OPTIMAL gate is the two-field conjunction — H=C₅ solves to PROVED_OPTIMAL had₂=3 with the family independently verified by the frozen trust root.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-22T06:35:13Z
- **Completed:** 2026-07-22T06:47Z (execution wave 1)
- **Tasks:** 3 (Task 1 TDD RED, Tasks 2–3 GREEN)
- **Files modified:** 8 created, 0 modified

## Accomplishments

- Closed the incumbent-as-optimum soundness hole at the TYPE level in the same plan that first runs a solver: `ExactOutcome.exact_value()` raises `NotProvedOptimal` for every status except PROVED_OPTIMAL, and PROVED_OPTIMAL is assigned only when `prob.status == LpStatusOptimal AND prob.sol_status == LpSolutionOptimal` (the locked regression constant).
- The full MVP slice is green end-to-end: enumeration → structural checksum gate → CBC → two-field status gate → guarded extraction → `verify_certificate`. H=C₅ optimize → PROVED_OPTIMAL, `exact_value()==3`, `bound==3`, 3-set family verified at k=3; H=empty (K₅) → had₂=5, five singletons verified at k=5.
- Both modes work: decision target_k=3 → MODEL_FOUND (family ≥ 3, `exact_value()` still raises), target_k=4 → PROVED_INFEASIBLE with value=None and family=None. Every outcome stamps `backend_version = "pulp==3.3.2 / CBC 2.10.3"` (live banner probe) and a real wall time.
- Trust boundaries hold mechanically: `result.py`/`backend.py`/`problems/had2.py` import without pulp entering `sys.modules` (verified), pulp is AST-confined to `cbc.py` (scan green), zero optimization-strippable guard statements across `solvers/` (AST scan green).
- No regression: full suite 63 passed (54 baseline + 9 new); every frozen file (`corpus/`, `verify/`, `repro/`, `generators/`, `data/`, R1/R2/R3 tests) byte-untouched — this plan composes the frozen trust primitives, it never edits them.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — status-contract units + E2E happy-path tests** - `349f980` (test)
2. **Task 2: stdlib-only contracts — result.py + backend.py (units GREEN)** - `863a82f` (feat)
3. **Task 3: engine — problems/had2.py + cbc.py (E2E slice GREEN)** - `5780765` (feat)

_TDD gate: `test(...)` 349f980 precedes `feat(...)` 863a82f/5780765 in git log; no REFACTOR commit was needed._

## Files Created/Modified

- `src/alpha2/solvers/result.py` — Status (MODEL_FOUND/PROVED_OPTIMAL/PROVED_INFEASIBLE/INCUMBENT_ONLY/UNKNOWN/ERROR), `NotProvedOptimal`, frozen `SolveParams` + `ExactOutcome` (post-init invariants: UNKNOWN/ERROR carry no value; PROVED_OPTIMAL requires value==bound), raising `exact_value()` — stdlib-only
- `src/alpha2/solvers/backend.py` — `ExactBackend` Protocol, `register_backend`/`get_backend` lazy registry; unknown name after lazy import raises ValueError — stdlib-only
- `src/alpha2/solvers/problems/had2.py` — `ChecksumError`, frozen `Had2Problem(n, Gedges, ss, sp, pp)`, `enumerate_had2` (frozenset dedup of the double C₄ discovery), `build_had2_problem` (triangle-free re-check + checksum gate on every build); Pitfall-5 documented: pair-variable indexing over G-edges IS the size-2 connectivity constraint
- `src/alpha2/solvers/cbc.py` — sole pulp importer; `map_status` (the locked table), `parse_bound` (CBC 2.10.3 "Upper bound:" grammar, trivial_n fallback), `cbc_binary_version` (subprocess banner probe, cached), `CBCBackend` with Appendix C.3 byte-compat model shape and guarded extraction; registers as "cbc"
- `tests/test_solver_result.py` — raising accessor across all five non-proven statuses, post-init refusals, frozen-instance proof
- `tests/test_cbc_backend.py` — exhaustive mapping-table test over pulp's exported constants, C5 + empty-H E2E through `verify_certificate` (call-then-compare discipline), decision-mode both legs with version-stamp assertions

## Decisions Made

- **Single-thread enforced raise-based** — `SolveParams(threads != 1)` is a rejected input for the CBC reference backend, and the literal `threads=1` is passed to `PULP_CBC_CMD`. CLAUDE.md's deterministic reference-lineage constraint became a structural guarantee instead of a convention.
- **Decision-mode recompute guard** — the plan's objective-recompute guard is mode-split: optimize compares extracted count to the reported objective (1e-6); decision (constant objective 0) checks `len(family) >= target_k`. Comparing against a constant-0 objective would be vacuous or wrong.
- **Decision (Optimal, IntegerFeasible) → MODEL_FOUND** — a stopped feasibility run that found an incumbent satisfying Σ ≥ k still produced a witness; extraction stays guarded and the verifier arbitrates. The empirically-pinned table rows from the plan are all reproduced exactly.
- **Frozen `is_triangle_free` reused read-only** for the build-time re-check rather than duplicating the loop (Don't-Hand-Roll; import-only dependency on a frozen module).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Enforced single-thread contract structurally**
- **Found during:** Task 3 (acceptance criterion requires literal `threads=1`; CLAUDE.md requires deterministic single-thread CBC)
- **Issue:** Passing `threads=p.threads` verbatim would let a caller silently run the reference backend multi-threaded, breaking the determinism contract
- **Fix:** Raise-based guard (`ValueError` on `threads != 1`) + literal `threads=1` in the PULP_CBC_CMD invocation
- **Files modified:** src/alpha2/solvers/cbc.py
- **Commit:** 5780765

No other deviations — plan executed as written.

## Known Stubs

None — every module is fully wired; no placeholder values, no unwired components. (The `bound_source="trivial_n"` fallback and `cbc_binary_version() == "unknown"` probe-failure path are defensive fallbacks specified by the plan, not stubs; both are exercised only when the CBC log/banner deviates from the pinned grammar.)

## Threat Flags

None — all security-relevant surface introduced (CBC subprocess probe, solution-file trust boundary, extraction guards) is exactly the surface enumerated in the plan's threat model (T-4-01..T-4-05), with the specified mitigations implemented.

## Next Phase Readiness

- Plan 04-02 (status-honesty timeout test + AST/-O guards) can pin: the two-field gate expression lives at `src/alpha2/solvers/cbc.py::map_status`; zero-assert already holds across `solvers/` (verified by AST scan this plan).
- Plan 04-03 (set-equality proof) consumes `enumerate_had2` — the naive C.4 loops stay test-local as planned.
- Plan 04-04 (seed-137 regression) has the full pipeline available via `get_backend("cbc").solve_had2(adj, 31, mode="optimize")`.
- Phase 5's CP-SAT backend translates the same `Had2Problem` object and registers through the same lazy registry.

## Self-Check: PASSED

- All 8 created files exist on disk
- Commits 349f980, 863a82f, 5780765 present in git log
- Full suite: 63 passed; frozen-file `git diff --quiet` clean
