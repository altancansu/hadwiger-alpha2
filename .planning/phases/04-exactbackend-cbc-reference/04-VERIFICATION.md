---
phase: 04-exactbackend-cbc-reference
verified: 2026-07-22T07:26:49Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
---

# Phase 4: ExactBackend + CBC Reference Verification Report

**Phase Goal:** Exact had₂ solving lives behind a status-honest interface with CBC as
the reference engine — the incumbent-as-optimum soundness hole is closed before any
second engine exists.
**Verified:** 2026-07-22T07:26:49Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1 — a time-limited CBC solve returning an unproven incumbent does NOT read as PROVED_OPTIMAL; `exact_value()` raises on non-proven status; PROVED_OPTIMAL gate is the two-field `LpStatusOptimal AND LpSolutionOptimal` | ✓ VERIFIED | `src/alpha2/solvers/cbc.py:59-65` — `map_status` requires `status == pulp.LpStatusOptimal and sol_status == pulp.LpSolutionOptimal` for PROVED_OPTIMAL/MODEL_FOUND; the `(Optimal, IntegerFeasible)` pairing maps to INCUMBENT_ONLY in optimize mode. `src/alpha2/solvers/result.py:85-95` — `exact_value()` raises `NotProvedOptimal` unless `status is Status.PROVED_OPTIMAL`. Live-run proof: `uv run --frozen --extra dev pytest tests/test_cbc_status_honesty.py -q` → 6 passed (10s-limited seed-137 optimize lands in {INCUMBENT_ONLY, UNKNOWN}, `pytest.raises(NotProvedOptimal)` on `exact_value()`). |
| 2 | SC2 — seed-137 regression: had₂=17 PROVED_OPTIMAL, 17-set family verify_certificate-green via in-memory record; frozen corpus/manifest/R1-R3 byte-untouched | ✓ VERIFIED | `uv run --frozen --extra dev pytest tests/test_seed137_regression.py -q -m slow` → 1 passed in 159.57s. Asserts `status is PROVED_OPTIMAL`, `exact_value()==17`, `bound==17`, `len(family)==17`, `verify_certificate(rec)==17`, metamorphic `17 > 16` vs stored D.3 record. `git diff --quiet data/` → CLEAN after the run (data/ untouched). |
| 3 | SC3 — obstruction enumeration is SET-equal (not count-equal) to the naive loop at n=31 seeds 1 & 137; checksum formulas validated; mutation→ChecksumError | ✓ VERIFIED | `uv run --frozen --extra dev pytest tests/test_had2_problem.py -q` → 27 passed. `src/alpha2/solvers/problems/had2.py:76-101` — `build_had2_problem` independently recomputes `(nss, nsp, npp)` from H's degrees/codegrees and raises `ChecksumError` on any mismatch; test file performs set-equality diff vs test-local Appendix C.4 naive loops and asserts the pinned literals (131,998,726)/(177,1913,3782). `grep -rl "def _naive" src/alpha2/` → empty (naive loops are test-local only). |
| 4 | SC4 — decision AND optimize modes both work; value + bound + backend_version recorded | ✓ VERIFIED | `src/alpha2/solvers/cbc.py:162-262` — `solve_had2` branches on `mode in ("optimize","decision")`; `backend_version()` returns `f"pulp=={pulp.__version__} / CBC {cbc_binary_version()}"`. `tests/test_cbc_backend.py::test_decision_mode_both_legs_on_c5` (MODEL_FOUND / PROVED_INFEASIBLE legs) and `test_c5_end_to_end_proved_optimal_through_trust_root` (optimize leg) both green; `_assert_stamp` checks `"pulp==3.3.2"` and `"2.10.3"` in `backend_version` and `wall_time_s > 0` on every outcome. |
| 5 | No `assert` governs any verification/trust decision in `src/alpha2/solvers/`; raise-based; survives `python -O`; `pulp` confined to `cbc.py` | ✓ VERIFIED | `grep -rn "assert " src/alpha2/solvers/*.py src/alpha2/solvers/problems/*.py` → no matches. `uv run --frozen python -O -m pytest tests/test_solver_isolation.py tests/test_verifier_dash_O.py -q` → 6 passed (AST guards: zero `ast.Assert` across all 4 solver modules, pulp import confined to `cbc.py` across all of `src/alpha2/`, `-O` subprocess canary proves `NotProvedOptimal` and `ChecksumError` both raise with asserts stripped). |
| 6 | Scope fence held: no CP-SAT / differential-harness / had₃ / symmetry-breaking introduced by this phase | ✓ VERIFIED | `grep -rniE "ortools|cp_model|cpsat|had3|symmetry" src/ tests/` → only pre-existing references in frozen `schema.py` (record-schema field name, predates Phase 4) and `test_reproduction_contract.py` (Phase-2 schema test); `git diff --quiet` on those frozen paths → CLEAN (not touched by Phase 4). No CP-SAT backend, no differential harness, no had₃/symmetry code exists in `src/alpha2/solvers/`. |
| 7 | Full fast suite green | ✓ VERIFIED | `uv run --frozen --extra dev pytest -q -m "not slow"` → 102 passed, 5 deselected in 9.50s. |
| 8 | EXACT-01/EXACT-02 requirements traceability | ✓ VERIFIED | EXACT-01 ("ExactBackend interface... status contract separating PROVED_OPTIMAL from INCUMBENT_ONLY, never reading an objective under a timeout as exact") — satisfied by truths 1 and 5 above. EXACT-02 ("pulp/CBC backend implements ExactBackend as the reference solver... obstruction-based constraint generation... guarded by the structural-checksum assertion") — satisfied by truths 2, 3, 4 above. Both requirements claimed in PLAN frontmatter (04-01, 04-03, 04-04) and have executable, passing evidence. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/alpha2/solvers/result.py` | Status enum, NotProvedOptimal, frozen ExactOutcome with raising exact_value() | ✓ VERIFIED | 96 lines; six-member Status enum; `NotProvedOptimal`; `__post_init__` invariants (UNKNOWN/ERROR carry no value; PROVED_OPTIMAL requires value==bound); zero asserts; stdlib-only (dataclasses, enum). |
| `src/alpha2/solvers/backend.py` | ExactBackend Protocol + lazy get_backend registry | ✓ VERIFIED | Registered `get_backend("cbc")` used throughout tests; lazy import confirmed via isolation guard test. |
| `src/alpha2/solvers/problems/had2.py` | Obstruction enumeration + raise-based checksum gate | ✓ VERIFIED | 102 lines; `enumerate_had2`, `build_had2_problem`, `ChecksumError`; checksum gate independently recomputes and raises on mismatch. |
| `src/alpha2/solvers/cbc.py` | PULP_CBC_CMD adapter: two-field status gate, guarded extraction, bound parse, version probe | ✓ VERIFIED | 266 lines; `map_status` two-field gate; `_guarded_extract` (integrality + recompute + disjointness); `parse_bound`; `cbc_binary_version`; sole `import pulp` in new code (AST-confirmed). |
| `tests/test_cbc_backend.py` | E2E happy path + decision legs + 296-lineage kill panel | ✓ VERIFIED | 319 lines, 8 tests, all green; routes families through `verify_certificate`. |
| `tests/test_cbc_status_honesty.py` | SC1 live timeout proof + bound-parse fixture | ✓ VERIFIED | 6 tests green; live 10s-limited seed-137 solve exercised. |
| `tests/test_solver_isolation.py` | AST import-boundary + zero-assert guard + -O canary | ✓ VERIFIED | 4 guards, all green under both normal and `-O` execution. |
| `tests/test_had2_problem.py` | Set-equality differential + checksum literals + mutation + brute-force | ✓ VERIFIED | 27 tests green. |
| `tests/test_seed137_regression.py` | Slow capstone: had2=17 PROVED_OPTIMAL through trust root | ✓ VERIFIED | 1 test, 159.57s, green; corpus byte-untouched after run. |
| `.github/workflows/ci.yml` | -O canary extended over solver path | ✓ VERIFIED | Line 43: `python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py tests/test_solver_isolation.py -q`; SHA-pin count (6) matches pre-edit expectation. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `cbc.py` | `problems/had2.py` | `build_had2_problem` consumed for conflict rows | ✓ WIRED | `cbc.py:180` calls `build_had2_problem(adj, n)`. |
| `cbc.py` | `pulp.PULP_CBC_CMD` | msg=0, threads=1, timeLimit, logPath | ✓ WIRED | `cbc.py:209-214`. |
| `tests/test_cbc_backend.py` / `test_seed137_regression.py` | `alpha2.corpus.verifier.verify_certificate` | in-memory schema-v1 record | ✓ WIRED | Both files call `verify_certificate(rec)` and bind the return before asserting — never inside a bare assert expression. |
| `tests/test_cbc_status_honesty.py` | `alpha2.solvers.result.NotProvedOptimal` | `pytest.raises` on `exact_value()` post-timeout | ✓ WIRED | Confirmed live-passing. |
| `.github/workflows/ci.yml` | `tests/test_solver_isolation.py` | `python -O` pytest step, every commit | ✓ WIRED | Present at line 43. |

### Behavioral Spot-Checks / Live Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| SC1 timeout-honesty (live) | `uv run --frozen --extra dev pytest tests/test_cbc_status_honesty.py -q` | 6 passed in 5.99s | ✓ PASS |
| SC2 seed-137 capstone (live, slow) | `uv run --frozen --extra dev pytest tests/test_seed137_regression.py -q -m slow` | 1 passed in 159.57s | ✓ PASS |
| SC3 obstruction differential | `uv run --frozen --extra dev pytest tests/test_had2_problem.py -q` | 27 passed in 0.41s | ✓ PASS |
| `-O` canary (solver path) | `uv run --frozen python -O -m pytest tests/test_solver_isolation.py tests/test_verifier_dash_O.py -q` | 6 passed | ✓ PASS |
| Full fast suite | `uv run --frozen --extra dev pytest -q -m "not slow"` | 102 passed, 5 deselected in 9.50s | ✓ PASS |
| Frozen data untouched | `git diff --quiet data/` (post all runs) | exit 0 | ✓ PASS |
| Scope fence | `grep -rniE "ortools\|cp_model\|cpsat\|had3\|symmetry" src/ tests/` | only pre-existing frozen references | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| EXACT-01 | 04-01, 04-02, 04-04 | ExactBackend interface with status contract separating PROVED_OPTIMAL from INCUMBENT_ONLY | ✓ SATISFIED | Two-field gate + raising `exact_value()`, proven live under a real timeout (test_cbc_status_honesty.py) and under `python -O` (test_solver_isolation.py). |
| EXACT-02 | 04-01, 04-03, 04-04 | pulp/CBC reference backend, obstruction-based constraint generation, checksum-gated | ✓ SATISFIED | `problems/had2.py` obstruction enumeration set-equal to naive loop (test_had2_problem.py); checksum gate raises `ChecksumError` on mismatch; seed-137 capstone confirms the full pipeline end-to-end. |

Note: `.planning/REQUIREMENTS.md` line-level status table (lines 121-122) still lists EXACT-01/EXACT-02 as "Pending" — this is a documentation bookkeeping field, not code evidence; it does not affect this verdict but should be updated as part of phase close-out.

### Anti-Patterns Found

None. `grep -rniE "TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER|not yet implemented|not available|coming soon" src/alpha2/solvers/` returned no matches. Zero `assert` statements in any of the four solver modules (mechanically AST-guarded, non-vacuous per the isolation test's own injection-based self-check documented in 04-02-SUMMARY.md).

### Human Verification Required

None. Every phase behavior (status honesty, the timeout proof, obstruction-enumeration equivalence, the seed-137 capstone, isolation guards) has automated, executable verification, and all of it was independently re-run by this verifier (not just trusted from SUMMARY claims).

### Gaps Summary

No gaps. All observable truths derived from the ROADMAP goal and PLAN frontmatter must_haves across all four plans (04-01 through 04-04) were independently re-executed against the live codebase:

- The two-field PROVED_OPTIMAL gate (`LpStatusOptimal AND LpSolutionOptimal`) is implemented exactly as specified and proven under live timeout fire and under `python -O`.
- `exact_value()` is a raise-based accessor; a timed-out incumbent is structurally unrepresentable as an exact value.
- The seed-137 capstone (SC2) was independently re-run end-to-end (not trusted from SUMMARY) and took 159.57s, confirming had₂=17 PROVED_OPTIMAL with a verified 17-set family, and left the frozen corpus byte-identical.
- The obstruction enumeration (SC3) is set-equal to the naive reference at n=31 on both anchor seeds, with a non-vacuous raise-based checksum gate.
- Decision and optimize modes both work (SC4), with value/bound/backend_version recorded on every outcome.
- pulp is confined to `cbc.py`; zero asserts across the solver package; scope fence (no CP-SAT/had₃/symmetry/differential harness) holds — Phase 4 correctly deferred those to Phase 5 per ROADMAP.

---

_Verified: 2026-07-22T07:26:49Z_
_Verifier: Claude (gsd-verifier)_
