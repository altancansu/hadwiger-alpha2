---
phase: 04-exactbackend-cbc-reference
plan: 02
subsystem: solvers
tags: [soundness, status-honesty, cbc, pulp, ast-guard, dash-O-canary, ci]
requires:
  - phase: 04-exactbackend-cbc-reference/04-01
    provides: "Status/ExactOutcome/NotProvedOptimal/SolveParams (result.py), get_backend registry (backend.py), CBCBackend.solve_had2 + parse_bound + bound_source provenance (cbc.py), checksum-gated build_had2_problem/ChecksumError (problems/had2.py)"
provides:
  - "SC1 executable proof: 10 s-limited seed-137 CBC optimize lands in {INCUMBENT_ONLY, UNKNOWN} and exact_value() raises NotProvedOptimal (tests/test_cbc_status_honesty.py)"
  - "Fixture-pinned CBC 2.10.3 stopped-run log grammar: parse_bound -> 20.879; absent line -> None; trivial_n fallback provenance asserted"
  - "Solver isolation guards: pulp pinned to solvers/cbc.py, stdlib boundary on result/backend/problems.had2, zero ast.Assert across all four solver modules (tests/test_solver_isolation.py)"
  - "Every-commit CI -O canary extended over the solver path (.github/workflows/ci.yml)"
affects: [04-04 (release-gate seed-137 regression builds on the same API), phase-05 (CP-SAT backend inherits the isolation-guard pattern)]
tech-stack:
  added: []
  patterns:
    - "AST mechanism guards (not prose greps) for import boundaries and zero-assert discipline — CHI-01/VRF-01 class applied to solvers/"
    - "-O subprocess canary with a real __debug__ branch (exit 3 sentinel) exercising raise-based solver guards"
    - "Module-scoped pytest fixture to share one live time-limited solve across multiple assertions"
key-files:
  created:
    - tests/test_cbc_status_honesty.py
    - tests/test_solver_isolation.py
  modified:
    - .github/workflows/ci.yml
decisions:
  - "Live-timeout test accepts EITHER INCUMBENT_ONLY or UNKNOWN (which occurs depends on whether CBC finds the incumbent within 10 s) — both are honest; only PROVED_OPTIMAL-on-a-stop would be the bug"
  - "Bound equality with the incumbent is deliberately NEVER asserted on stopped runs — that would smuggle optimality back through the test"
  - "First-party imports in the stdlib-boundary guard are a pinned explicit allow-list (alpha2.solvers.result, alpha2.generators.tfp), not a blanket alpha2.* pass"
  - "-O canary script drives ChecksumError by monkeypatching enumerate_had2 to drop one conflict post-enumeration (no solver run needed; canary stays sub-second)"
metrics:
  duration: "~8 min"
  completed: "2026-07-22"
  tasks: 2
  tests-added: 11
---

# Phase 4 Plan 02: SC1 Timeout Proof + Solver Isolation Guards Summary

**One-liner:** Live 10 s-limited seed-137 CBC solve proves a timed-out incumbent can never read as an exact had2 (exact_value() raises NotProvedOptimal), with the guarantee mechanism-guarded by AST isolation tests and an every-commit python -O canary over the solver path.

## What Was Built

### Task 1 — SC1 live timeout test + bound-parse fixture (`tests/test_cbc_status_honesty.py`, commit 63d9bf6)

- **THE soundness-hole proof (T-4-01):** regenerates seed-137 H via `triangle_free_process(31, random.Random(137))`, solves `mode="optimize"` with `SolveParams(time_limit_s=10)` (far below the ~149 s proof time), and asserts:
  - `outcome.status in {Status.INCUMBENT_ONLY, Status.UNKNOWN}` — both honest, either accepted;
  - `pytest.raises(NotProvedOptimal)` on `outcome.exact_value()` — the incumbent-as-optimum hole closed under live fire;
  - **garbage suppression (T-4-02):** UNKNOWN leg asserts `value is None` (the fractional-23.25 class never surfaces); INCUMBENT_ONLY leg asserts `value` is an int with a non-None bound and recorded provenance. Bound equality is never asserted.
- One solve shared across assertions via a module-scoped fixture — the live test stays in the every-commit tier (~6–12 s observed locally).
- **Bound-parse fixture:** the captured CBC 2.10.3 stopped-run log grammar embedded as an in-file literal; `parse_bound` extracts `20.879`; the optimal-run literal (no "Upper bound:" line) and empty text return `None`.
- **Fallback provenance:** on the live stopped outcome, `bound_source in {"cbc_log", "trivial_n"}` with `bound == 31` required whenever the trivial fallback fires.
- Reads/writes nothing under `data/`; `git diff --quiet data/ src/alpha2/repro` clean.

### Task 2 — solver isolation guard + -O canary + CI extension (`tests/test_solver_isolation.py`, `.github/workflows/ci.yml`, commit 36f2aa2)

- **Guard 1 (stdlib boundary):** AST walk over `result.py`, `backend.py`, `problems/had2.py` — every Import/ImportFrom resolves to `{dataclasses, enum, typing, importlib}` or the pinned first-party allow-list `{alpha2.solvers.result, alpha2.generators.tfp}` (both transitively solver-free). Any third-party name fails.
- **Guard 2 (pulp confinement, T-4-06):** AST scan of ALL modules under `src/alpha2/` — `pulp` as an import target (module- or function-level) is legal only in `solvers/cbc.py`. Includes a non-vacuity self-check (the scanner must see cbc.py's own pulp import).
- **Guard 3 (zero-assert):** `ast.Assert` count == 0 across all four solver modules (result, backend, problems/had2, cbc).
- **Guard 4 (-O canary, T-4-05):** subprocess `[sys.executable, "-O", "-c", SCRIPT]` with `PYTHONPATH=src`; exits 3 if `__debug__` is True (real branch), 4 if `NotProvedOptimal` fails to raise on a hand-built INCUMBENT_ONLY outcome, 5 if `ChecksumError` fails to raise on a deliberately mutated conflict set (one ss element dropped post-enumeration on a tiny path H), 0 iff both raised. Parent asserts rc == 0 and != 3.
- **ci.yml:** the every-commit `python -O assert-stripping canary` step's pytest file list gained exactly `tests/test_solver_isolation.py` (+ two comment lines documenting the extension). Nothing else changed; both 40-char action SHA pins byte-identical (`grep -cE '[0-9a-f]{40}'` reports 6 before and after). The release-gate `-m slow` selector untouched.

## Verification Evidence

| Check | Result |
|-------|--------|
| `uv run --frozen --extra dev pytest tests/test_cbc_status_honesty.py -q` | 6 passed (includes the live 10 s-limited solve) |
| `uv run --frozen --extra dev pytest tests/test_solver_isolation.py -q` | 5 passed |
| `uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py tests/test_solver_isolation.py -q` (the exact CI invocation) | 7 passed |
| Guard 3 non-vacuity: `assert True` injected into `src/alpha2/solvers/result.py` | test FAILED as required; injection reverted (`git diff --quiet` clean); suite green again |
| Full suite `uv run --frozen --extra dev pytest -q` | 74 passed, no regression |
| Frozen files `git diff --quiet src/alpha2/corpus src/alpha2/repro src/alpha2/generators data/` | untouched |
| SHA pin count in ci.yml | 6 before == 6 after |

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

Task 1 carried `tdd="true"` but is a test-only task against an implementation that already exists (built and committed in wave-1 plan 04-01; this plan's stated objective is the *adversarial proof* that the existing defense holds under a real timeout). There is therefore no RED-failing state to produce and no `feat(...)` commit in this plan — the passing test IS the deliverable. The plan frontmatter is `type: execute` (not `type: tdd`), so no plan-level RED/GREEN gate sequence applies.

## Known Stubs

None — both test files are fully wired against the live wave-1 solver API; no placeholders, no hardcoded-empty data paths.

## Threat Flags

None — no new network endpoints, auth paths, file-access patterns, or schema changes. The ci.yml edit adds one test path to an existing step with action SHA pins byte-identical (T-4-SC accepted disposition honored).

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 63d9bf6 | test(04-02): prove SC1 live — timed-out CBC incumbent never reads as exact had2 |
| 2 | 36f2aa2 | test(04-02): mechanism-guard the solver soundness path (AST + -O canary) |

## Notes for the Orchestrator / Next Plans

- ROADMAP SC1 is now proven **by execution**, not construction alone: the every-commit tier carries the live timeout test (~10 s ceiling by `time_limit_s`), and CI's -O canary covers the solver raises on every commit.
- 04-04's slow seed-137 optimize regression joins the release gate automatically via the existing `-m slow` selector — untouched here as instructed.
- Requirement EXACT-01 progress: this plan supplies the live-proof and erosion-guard halves; marking complete is the orchestrator's call after the wave merges.

## Self-Check: PASSED

All created files exist (test_cbc_status_honesty.py, test_solver_isolation.py, ci.yml edit, this SUMMARY); both task commits (63d9bf6, 36f2aa2) present in git log.
