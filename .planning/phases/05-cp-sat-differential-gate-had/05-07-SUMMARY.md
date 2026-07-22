---
phase: 05-cp-sat-differential-gate-had
plan: 07
subsystem: testing
tags: [cp-sat, cbc, differential, agreement-panel, seed-137, sc1, slow-tier, deterministic]

# Dependency graph
requires:
  - phase: 05-01
    provides: CP-SAT backend (solvers/cpsat.py) — deterministic num_workers=1 + pinned random_seed
  - phase: 05-04
    provides: solvers/differential.py — differential_verdict (the SOLE licenser) + CriticalDisagreement
  - phase: 04
    provides: frozen Status/ExactOutcome (result.py), CBC backend (cbc.py), trust root (verify_certificate), seed-137 regeneration/regression discipline
provides:
  - "tests/test_differential_panel.py: dual-backend CI agreement panel — CBC == CP-SAT PROVED_OPTIMAL with equal had_2 on C5, empty-H, tiny TFP (n=6/7/8, seeds 1/2), every agreement licensed through differential_verdict, both families independently verified"
  - "SC1 end-to-end: seed-137 (n=31, chi=16) proves had_2=17 PROVED_OPTIMAL on BOTH backends in deterministic mode, AGREED_KILL through the gate, both 17-set families verified (slow tier)"
  - "Pinned slow-tier budget: measured CP-SAT seed-137 optimize wall time (Assumption A2 resolved / RESEARCH Wave-0 measurement)"
affects: [phase-06-battery, phase-11-falsification-harness, SHC-CANDIDATE consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CI agreement panel: two independent encodings of ONE instance solved by both engines; agreement is a FACT only when both PROVED_OPTIMAL at equal value, and only through differential_verdict"
    - "Slow-tier dual-backend anchor: the expensive seed-137 optimality proof carries @pytest.mark.slow and joins the release gate via -m slow automatically"

key-files:
  created:
    - tests/test_differential_panel.py
  modified: []

key-decisions:
  - "The seed-137 dual-backend proof lives IN MEMORY (like the Phase-4 regression); the frozen corpus/repro/R1/manifest stay byte-untouched — corpus upgrade to the 17-set family remains deferred (Open-Q3, first consumer Phase-11)"
  - "CP-SAT seed-137 budget pinned at 1800 s max_time_in_seconds with vast headroom: measured CP-SAT optimize solve is ~0.25 s (inner) / ~0.72 s (incl. model build), ~660x faster than the ~165 s CBC reference (Assumption A2 resolved)"
  - "Every panel instance has had_2 >= chi, so every agreement is AGREED_KILL; SHC_CANDIDATE cannot arise on any known triangle-free instance (296/296 killed at had_2)"

requirements-completed: [EXACT-04, EXACT-03]

# Metrics
duration: 12min
completed: 2026-07-22
---

# Phase 5 Plan 07: Dual-Backend Agreement Panel Summary

**CBC and CP-SAT AGREE on every shared CI-panel instance — both `PROVED_OPTIMAL`, equal had_2, both families independently verified — including the seed-137 = 17 dual-backend optimality proof in deterministic mode; every agreement is licensed through `differential_verdict` (the SOLE gate), and the frozen corpus is byte-untouched. SC1 closed end-to-end.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-22
- **Tasks:** 2 (RED-then-green panel, slow-leg run + timing)
- **Files modified:** 1 (created)

## Accomplishments

- `tests/test_differential_panel.py` — the phase-5 capstone panel:
  - **`test_agreement_panel_fast`** (every-commit, ~0.9 s): C5 (had_2=3), empty-H n=5 (had_2=5), and the tiny-TFP battery n∈{6,7,8} × seeds {1,2}. Each TFP instance is regenerated from the frozen generator and gated on its pinned (m, nu, chi) invariants BEFORE any solve (R2 discipline). Both backends solve had_2 optimize; the agreement is licensed ONLY through `differential_verdict(cbc, cpsat, chi)` == "AGREED_KILL"; BOTH families are routed through the frozen trust root (`verify_certificate`).
  - **`test_seed137_dual_backend`** (`@pytest.mark.slow`): regenerate seed-137 (m==177, nu==15, chi==16), then CBC AND CP-SAT both prove had_2 = 17 `PROVED_OPTIMAL` (CP-SAT deterministic: num_workers=1 + pinned random_seed, baked into cpsat.py), AGREED_KILL through the gate (17 ≥ 16), both 17-set families independently verified, and the metamorphic anchor (17 > stored 16-set corpus family, read-only load). No corpus write.
  - **`test_backends_disagreement_would_halt`**: unequal proven optima raise `CriticalDisagreement` — the panel quarantines + halts, never picks a winner, never skips.
- **SC1 proven end-to-end** (actually executed, not merely wired): `pytest -m slow` green in 201 s; the standalone authoritative run reports `verdict=AGREED_KILL cbc_val=17 cpsat_val=17 k_cbc=17 k_cpsat=17`.
- **Assumption A2 / Wave-0 measurement resolved:** CP-SAT seed-137 optimize wall time measured (see below).

## CP-SAT seed-137 timing (Assumption A2 / Wave-0 measurement)

| Backend | Inner solve (`ExactOutcome.wall_time_s`) | Outer (incl. build) |
|---------|------------------------------------------|---------------------|
| CBC (reference) | ~164.99 s | ~165.00 s |
| **CP-SAT** | **~0.25 s** | **~0.72 s** |

- CP-SAT proves the seed-137 had_2 = 17 optimum in **~0.25 s** — roughly **660× faster** than the ~165 s single-thread CBC reference. (RESEARCH Assumption A2 anticipated "order of, or faster than, CBC's ~149 s"; CP-SAT is dramatically faster.)
- **Pinned slow-tier budget:** CP-SAT `SolveParams(time_limit_s=1800)`, CBC `time_limit_s=600`. The 1800 s CP-SAT budget is a `max_time_in_seconds` ceiling with enormous headroom; it was NOT raised (CP-SAT is far faster than CBC, not slower). The slow tier is dominated by CBC (~165 s); total `pytest -m slow` wall time ≈ 201 s.

## Task Commits

1. **Task 1: RED — dual-backend agreement panel (fast) + seed-137 slow leg** — `5d42aba` (test)
2. **Task 2: run the seed-137 dual-backend proof, record timing, pin the slow budget** — no code change (the Task-1 budget already has vast headroom; CP-SAT proved optimality in ~0.25 s). The measurement is recorded above; the frozen corpus is byte-untouched (`git status --porcelain data/` empty).

**Plan metadata:** this commit (docs: complete plan).

## Files Created/Modified

- `tests/test_differential_panel.py` — 3 tests (fast agreement panel over C5/empty/tiny-TFP, slow seed-137 dual-backend, disagreement negative control); embedded-literal discipline, trust-root calls outside truth-expressions, semantic (never byte) seed-137 contract.

## Decisions Made

- The seed-137 dual-backend proof is an IN-MEMORY schema-v1 record (both families); no `data/` write. The committed 16-set corpus record is untouched — the 17-set upgrade stays deferred (Open-Q3), no EXACT-03..06 criterion requires it.
- The CP-SAT budget was left at 1800 s (not tightened) so the slow tier tolerates slower CI hardware; the measured ~0.25 s solve documents the true cost.
- Both families (CBC's and CP-SAT's) are verified independently — a lost encoding constraint on either backend, or a family that fails to verify, fails the panel loudly rather than trusting a single value.

## Deviations from Plan

None — plan executed exactly as written. Task 2 required no budget increase (CP-SAT proved faster than CBC, the opposite of the "materially slower" contingency the plan hedged for), so it produced no code change; its timing measurement is recorded here.

## Issues Encountered

None. The plan's verify commands used `uv run`; per the executor toolchain note they were run as `.venv/bin/python -m pytest` (fast tier) and `.venv/bin/python -m pytest -m slow` (the seed-137 leg, actually executed once — 201 s, green) with identical semantics. Pre-existing PuLP `DeprecationWarning`s (PULP_CBC_CMD / LpVariable, slated for PuLP 4.0) are out of scope and untouched.

## Known Stubs

None — every panel leg runs real dual-backend solves through the real gate and the real trust root; the seed-137 leg was executed end-to-end.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- EXACT-04 agreement panel + EXACT-03 CP-SAT-at-the-anchor are closed: Phase 5's SC1 is proven end-to-end. The slow seed-137 dual-backend leg joins the release gate automatically via `-m slow`.
- Phase 6 battery (runbook step 5) can rely on a proven dual-backend agreement panel; Phase 11's falsification harness is the first consumer that may upgrade the frozen seed-137 corpus record to the 17-set family (still deferred here).

---
*Phase: 05-cp-sat-differential-gate-had*
*Completed: 2026-07-22*

## Self-Check: PASSED

Files verified present: `tests/test_differential_panel.py`.
Commit verified in git log: `5d42aba` (RED/panel test).
Tests: fast tier 2 passed (1 deselected); full non-slow suite 195 passed; slow seed-137 leg 1 passed in 201 s (both backends PROVED_OPTIMAL=17, AGREED_KILL, both families verified). Frozen corpus byte-untouched (`git status --porcelain data/` empty).
