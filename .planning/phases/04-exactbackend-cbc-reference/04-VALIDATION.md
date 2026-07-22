---
phase: 4
slug: exactbackend-cbc-reference
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-21
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 (pinned since Phase 3, installed; 54-test baseline green) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`markers = ["slow: release/nightly replay gate"]` — already registered, nothing to install) |
| **Quick run command** | `uv run --frozen --extra dev pytest tests/test_solver_result.py tests/test_had2_problem.py tests/test_cbc_backend.py tests/test_cbc_status_honesty.py -q` (fast solver-unit panel; excludes `slow`) |
| **Full suite command** | `uv run --frozen --extra dev pytest -q` (includes `-m slow`: R3 replay + seed-137 optimize regression) |
| **Estimated runtime** | Quick panel ~60–90 s (dominated by the 10 s time-limited live solve in the status-honesty test + ~2.5 s/each decision-mode kills). Full suite ~3–4 min — the seed-137 optimize proof alone is ~149 s single-thread (live-verified), which is WHY it carries `@pytest.mark.slow` and joins the release gate, never the every-commit tier. |

---

## Sampling Rate

- **After every task commit:** Run the quick run command above (new-module tests only; well under 2 min)
- **After every plan wave:** Run `uv run --frozen --extra dev pytest -q -m "not slow"` plus the `-O` canary `uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py tests/test_solver_isolation.py -q`
- **Before `/gsd:verify-work`:** Full suite must be green INCLUDING `-m slow` (seed-137 optimize ~149 s + R3) — the phase gate
- **Max feedback latency:** ~90 seconds (quick tier)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | EXACT-01, EXACT-02 | T-4-01 | Locked status-mapping table + raising `exact_value()` + C5 trust-root slice encoded RED-first; verify calls raise-based (survive `-O`) | unit + integration (RED scaffold) | `uv run --frozen --extra dev pytest tests/test_solver_result.py tests/test_cbc_backend.py -q; test $? -ne 0` (RED: `alpha2.solvers` absent) | ❌ created in-task (RED-first) | ⬜ pending |
| 04-01-02 | 01 | 1 | EXACT-01 | T-4-01 / T-4-05 | `exact_value()` raises `NotProvedOptimal` unless PROVED_OPTIMAL; frozen `ExactOutcome` `__post_init__` invariants; stdlib-only zero-assert contracts | unit | `uv run --frozen --extra dev pytest tests/test_solver_result.py -q` | ✅ (from 04-01-01) | ⬜ pending |
| 04-01-03 | 01 | 1 | EXACT-01, EXACT-02 | T-4-01 / T-4-02 / T-4-04 | Two-field gate (`LpStatusOptimal AND LpSolutionOptimal`); guarded extraction (integrality + objective recompute); checksum gate on every build; pulp confined to cbc.py | integration (fast; E2E slice GREEN) | `uv run --frozen --extra dev pytest tests/test_solver_result.py tests/test_cbc_backend.py -q` | ✅ (from 04-01-01) | ⬜ pending |
| 04-02-01 | 02 | 2 | EXACT-01 | T-4-01 / T-4-02 | **Status-honesty timeout proof (SC1):** 10 s-limited seed-137 optimize lands in {INCUMBENT_ONLY, UNKNOWN} and `exact_value()` raises; UNKNOWN leg asserts `value is None` (23.25 garbage class never surfaces); bound-parse fixture pins the CBC 2.10.3 log grammar (`Upper bound: 20.879`) + trivial-n fallback provenance | integration (live time-limited solve, ~10–15 s) | `uv run --frozen --extra dev pytest tests/test_cbc_status_honesty.py -q` | ❌ created in-task | ⬜ pending |
| 04-02-02 | 02 | 2 | EXACT-01 | T-4-05 / T-4-06 | AST guards: pulp only in cbc.py, zero asserts in all solver modules (non-vacuity by injection); `-O` subprocess canary proves `NotProvedOptimal` + `ChecksumError` raise with asserts stripped; CI `-O` step extended | unit + subprocess canary | `uv run --frozen --extra dev pytest tests/test_solver_isolation.py -q && uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py tests/test_solver_isolation.py -q` | ❌ created in-task | ⬜ pending |
| 04-03-01 | 03 | 2 | EXACT-02 | T-4-04 / T-4-07 / T-4-05 | **Set-equality (not count-equality)** vs Appendix C.4 naive loops at n=31, seeds 1 & 137; checksum literals (131, 998, 726)/(177, 1913, 3782); each single-element mutation raises `ChecksumError`; triangle-containing H refused at build | unit (differential vs test-local reference) | `uv run --frozen --extra dev pytest tests/test_had2_problem.py -q -k "equality or checksum or mutation or triangle"` | ❌ created in-task | ⬜ pending |
| 04-03-02 | 03 | 2 | EXACT-02 | T-4-04 | Exhaustive brute-force had₂ == CBC PROVED_OPTIMAL on every n≤8 panel instance (independent semantics, no shared import); domain sanity had₂ ≥ α(H) | integration (fast, file < ~30 s) | `uv run --frozen --extra dev pytest tests/test_had2_problem.py -q` | ✅ (from 04-03-01) | ⬜ pending |
| 04-04-01 | 04 | 3 | EXACT-01, EXACT-02 | T-4-04 / T-4-08 | 296-lineage every-commit leg: decision-mode kills at k=χ=16 on seed-1/seed-137 (~2.5 s each) with families through raise-based `verify_certificate`; regeneration gates (\|E(H)\|==177, χ==16) before any solve is trusted; Cayley p=31 kill in `slow`; frozen corpus read-only | integration (every-commit + slow Cayley leg) | `uv run --frozen --extra dev pytest tests/test_cbc_backend.py -q -m "not slow" && uv run --frozen --extra dev pytest tests/test_cbc_backend.py -q -m slow` | ✅ (extends 04-01's file) | ⬜ pending |
| 04-04-02 | 04 | 3 | EXACT-01, EXACT-02 | T-4-01 / T-4-04 / T-4-08 | **Seed-137 regression (SC2):** had₂ == 17 PROVED_OPTIMAL, bound == 17, full 17-set family verified via in-memory schema-v1 record; metamorphic 17 > 16 vs stored D.3 record; no corpus write (`git diff --quiet data/ src/alpha2/repro`); backend_version stamped "2.10.3" | integration, `slow` (~149 s solve; 600 s ceiling) | `uv run --frozen --extra dev pytest tests/test_seed137_regression.py -q -m slow` | ❌ created in-task | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Sampling continuity: every task carries an `<automated>` command — there are no gaps, let alone 3 consecutive tasks without automated verify.

---

## Wave 0 Requirements

**Existing infrastructure covers all phase requirements.** pytest 8.3.4 is pinned and green at the 54-test baseline, and the `slow` marker is already registered in `pyproject.toml` — no framework install, no conftest, no marker registration needed.

The RED-first test scaffolds are folded into each plan's first task rather than a separate Wave 0:
- 04-01 Task 1 IS the RED scaffold (`tests/test_solver_result.py` + `tests/test_cbc_backend.py` fail at import before any production code exists; the `<automated>` command asserts non-zero exit).
- Plans 04-02, 04-03, 04-04 are test-only plans (`tdd="true"` tasks) — each creates its test file against the already-landed 04-01 API, so "MISSING test" states cannot arise.

---

## Manual-Only Verifications

All phase behaviors have automated verification. (The phase's central soundness evidence — the timeout test — is itself automated and runs in the every-commit tier.)

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none exist — RED scaffolds folded into first tasks; infra pre-exists)
- [x] No watch-mode flags
- [x] Feedback latency < 90 s (quick tier; the ~149 s seed-137 optimize is quarantined behind `-m slow`, decision-mode kills ~2.5 s stay every-commit)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-21
