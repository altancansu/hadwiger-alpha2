---
phase: 04-exactbackend-cbc-reference
plan: 04
subsystem: solvers
tags: [seed-137, had2-17, proved-optimal, decision-kill, trust-root, regression-as-test, slow-tier, cayley, metamorphic]

# Dependency graph
requires:
  - phase: 04-exactbackend-cbc-reference
    plan: 01
    provides: "solvers/backend.get_backend('cbc'), solvers/result.Status/ExactOutcome/SolveParams, tests/test_cbc_backend.py base panel"
  - phase: 04-exactbackend-cbc-reference
    plan: 02
    provides: "two-field PROVED_OPTIMAL gate proven under timeout; cbc_binary_version() probe; overridable backends block honored"
  - phase: 04-exactbackend-cbc-reference
    plan: 03
    provides: "obstruction enumeration proven set-equal to Appendix C.4 loops — the model build feeding these solves is pinned from both sides"
  - phase: 03-corpus-reproduction-ci-first-blood
    provides: "frozen corpus (296 records incl. the D.3 16-set seed-137 literal), frozen repro drivers, R1/R2/R3, the ci.yml -m slow release-gate selector"
provides:
  - "tests/test_seed137_regression.py — the phase capstone (slow tier): seed-137 had_2=17 PROVED_OPTIMAL, bound=17, FULL 17-set family verified through the frozen trust root via an IN-MEMORY schema-v1 record; metamorphic 17 > 16 vs the stored D.3 family; frozen corpus byte-untouched"
  - "tests/test_cbc_backend.py 296-lineage kill panel — every-commit decision-mode kills at k=chi=16 on seed-1 and seed-137 (invariant-gated regeneration, trust-root-verified families) + slow-tier Cayley p=31 (seed 5310) kill with structural gate"
affects: [phase-05 CP-SAT backend (same regression constants to cross-check), phase-11 Falsification-Rule harness (first consumer of the DEFERRED 17-set corpus upgrade)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regression-as-test reconciliation (LOCKED): the true had_2=17 result lives as executable evidence in the slow tier while the frozen corpus keeps its verified 16-set D.3 literal — value claims and freeze discipline never compete"
    - "In-memory schema-v1 record through the trust root: build_record(...) + verify_certificate(rec) with zero corpus-store interaction — solver families get independently verified without any freeze amendment"
    - "Regeneration gates before solve trust (R2 discipline extended to solver tests): pinned |E|/nu/chi literals (and Cayley structural identity + stored-S equality) must pass before any solve outcome is even examined"
    - "Backend-version stamping closure: make_backends(method) then override the 'cbc' field with the probed cbc_binary_version() — the in-memory record carries 'CBC 2.10.3' instead of the Phase-2 bundled-with-pulp stub, schema.py untouched"

key-files:
  created:
    - "tests/test_seed137_regression.py"
  modified:
    - "tests/test_cbc_backend.py"

key-decisions:
  - "Corpus upgrade to the stored 17-set family DEFERRED (LOCKED plan decision, recorded here): a future deliberate freeze amendment in a single lockstep commit (frozen driver + refreeze + R1 literal), first real consumer being the Phase-11 Falsification-Rule harness — nothing in this plan touches data/, repro/, or R1/R2/R3"
  - "Docstring reworded to avoid the literal store-call token: the acceptance criterion greps for the forbidden call; keeping the token out of prose entirely (not just out of code) follows the Phase-2/3 grep-trigger caution"
  - "Cayley kill anchors chi against the committed record's stored invariants AND asserts regenerated sorted(S) equals the stored provenance params S — the read-only provenance-shape read doubles as a generator-drift tripwire"
  - "Seed-1 kill also gates |E(H)|==131 (in addition to the plan's nu/chi gates) — same embedded-literal discipline as the seed-137 leg, strengthening the regeneration gate at zero cost"

patterns-established:
  - "Pattern: every decision-kill family is routed through verify_certificate as an in-memory record with the FULL family (never truncated) — MODEL_FOUND alone never counts as a kill"

requirements-completed: [EXACT-01, EXACT-02]

# Metrics
duration: ~12min
completed: 2026-07-22
---

# Phase 4 Plan 04: seed-137 Regression + 296-Lineage CI Panel Summary

**One-liner:** ROADMAP SC2 verbatim — seed-137 had₂=17 PROVED_OPTIMAL (bound 17, full 17-set family verify_certificate-green via an in-memory schema-v1 record, ~150 s slow tier) plus every-commit decision-mode kills at k=χ=16 on seed-1/seed-137 (~3.7 s combined) and a slow-tier Cayley p=31 kill, with the frozen Phase-3 trust anchor byte-untouched.

## What Was Built

**`tests/test_seed137_regression.py`** (1 slow test + 1 read-only helper):

1. **Regeneration gates first:** `random.Random(137)` → `triangle_free_process(31, rng)`; raise-before-solve gates `|E(H)| == 177`, `ν == 15`, `χ == 16` — a drifted generator can never self-certify through a solver run.
2. **The optimality proof:** `get_backend("cbc").solve_had2(adj, 31, mode="optimize", params=SolveParams(time_limit_s=600))` — observed 161 s wall on this run (headroom held).
3. **LOCKED constants asserted:** `status is PROVED_OPTIMAL` (two-field gate by construction), `exact_value() == 17`, `bound == 17`, `len(family) == 17`, `"2.10.3"`/`"pulp==3.3.2"` in `backend_version`. Semantic contract only — never which 17-set family CBC returned (ENV-05 / A1).
4. **Trust root, in memory:** `extract_witness` → `build_record(provenance_seed(..., 137, ...), method="exact ILP (CBC): had_2(G)=17", omega_G=14, backends=<probed>)` → `verify_certificate(rec) == 17`. No store call, no data/ write; the record dies with the test.
5. **Backend-version stamping closure:** `build_record`'s `backends` kwarg (02-02 decision) is overridable — the record carries `backends.cbc == "CBC 2.10.3"` (probed) instead of the Phase-2 `bundled-with-pulp-3.3.2` stub, asserted in-test. `schema.py` untouched.
6. **Metamorphic anchor:** committed corpus loaded read-only, the (31, 137) record's stored family has `len == 16`, and `17 > 16` — a PROVED_OPTIMAL value below any stored verified family size would be a CRITICAL encoding bug (verifier trumps solver).

**`tests/test_cbc_backend.py`** extended with the 296-lineage kill panel:

- **Test A (seed-1, every-commit):** regeneration gates `|E| == 131`, `ν == 15`, `χ == 16`; decision `target_k=16` → `MODEL_FOUND`, `len(family) >= 16`; family through `extract_witness` + `build_record` + `verify_certificate` → `k >= 16`.
- **Test B (seed-137, every-commit):** same shape with the `|E| == 177` gate — the instance the heuristic misses, exact-method-resolved in seconds; the "reproduces 296-lineage exact values" every-commit leg.
- **Test C (Cayley p=31, `@pytest.mark.slow`):** seed 5310 (convention 5000 + 10·p + k); structural gate — `|S|`-regular, symmetric, loop-free — plus read-only anchor against the committed `cayley:p31:s5310` record (regenerated `sorted(S)` equals stored `params.S`; χ equals stored `chi_G`); decision kill at `k=χ=16`, family verified via `provenance_params` record.
- Every solve asserts the `pulp==3.3.2 / CBC 2.10.3` stamp; every family passes to `build_record` untruncated.

## Verification Results

- `uv run --frozen --extra dev pytest tests/test_cbc_backend.py -q -m "not slow"` — 6 passed in 3.7 s (every-commit tier, well under the ~20 s budget).
- `uv run --frozen --extra dev pytest tests/test_cbc_backend.py -q -m slow` — 1 passed in 0.8 s (Cayley kill).
- `uv run --frozen --extra dev pytest tests/test_seed137_regression.py -q -m slow` — 1 passed in 161 s (the ~149 s proof + gates/verification overhead).
- Full suite INCLUDING slow: `uv run --frozen --extra dev pytest -q` — **105 passed in 171 s** (the phase gate).
- `uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py tests/test_solver_isolation.py -q` — 7 passed.
- R1/R2 green post-change: `pytest tests/test_corpus_r1.py tests/test_corpus_r2.py -q` — 4 passed.
- `git diff --quiet data/ src/alpha2/repro src/alpha2/generators src/alpha2/corpus src/alpha2/verify tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_corpus_r3.py` — exits 0, every frozen artifact byte-identical.
- `grep -c append_certificate tests/test_seed137_regression.py` — 0; no `open(..., "w")` on any data/ path.
- No CI edit made: the slow tests join the existing release-gate `-m slow` selector automatically.

## Deviations from Plan

None - plan executed exactly as written. (One defensive refinement within plan scope: the regression test's docstring was worded to avoid the literal corpus-store call token, honoring the Phase-2/3 grep-trigger caution; seed-1's kill additionally gates `|E| == 131`, strengthening — not altering — the planned regeneration gate.)

## Deferred Items

- **Corpus upgrade to the stored 17-set seed-137 family** (explicitly NOT in this phase, per the LOCKED plan decision): a future deliberate freeze amendment in a single lockstep commit — frozen driver + refreeze + R1 `D3_MODEL` literal — whose first real consumer is the Phase-11 Falsification-Rule harness. Until then the true had₂=17 lives as this slow-tier regression's executable evidence while the corpus keeps its verified 16-set D.3 record.

## TDD Gate Compliance

Both tasks carry `tdd="true"`, but this is a test-only capstone plan over the wave-1/2 implementation (already merged into the base): no GREEN implementation step exists, so no temporal RED state is possible. Non-vacuity comes from the raise-based gates themselves (regeneration gates, `verify_certificate`, the metamorphic 17 > 16 comparison against independently stored data) and from plan 04-03's mutation/differential proofs over the same solve path. Commits are `test(04-04)` type per task.

## Threat Model Outcomes

- **T-4-01 (spoofed optimality):** mitigated — PROVED_OPTIMAL via the two-field-gated Status; `exact_value() == 17` AND `bound == 17` both asserted (coincidence is acceptance, not assumption).
- **T-4-04 (wrong optimum from a bad model build):** mitigated — metamorphic 17 > 16 vs the stored verified family; regeneration gates (|E|, ν, χ, Cayley structural identity + stored-S equality) refuse a drifted generator before any solve is trusted.
- **T-4-08 (frozen-corpus mutation):** mitigated — record stays in memory, zero store calls, `git diff --quiet` over data/, repro/, generators/, corpus/, verify/ and R1/R2/R3 verified clean post-execution.
- **T-4-03 (unstamped provenance):** mitigated — `pulp==3.3.2 / CBC 2.10.3` asserted on every outcome; the in-memory record's backends block carries the probed `CBC 2.10.3` via the overridable kwarg.
- **T-4-SC (supply chain):** accepted per plan — no package installs, test-only files, no CI edit.

No new security-relevant surface beyond the plan's threat model (test-only files; the only data/ interaction is two read-only JSON loads). No stubs.

## Commits

| Task | Commit | Description |
| ---- | ------ | ----------- |
| 1 | ce06acd | test(04-04): add every-commit 296-lineage decision-kill panel |
| 2 | 75ba14d | test(04-04): add seed-137 optimize regression - had2=17 PROVED_OPTIMAL |

## Self-Check: PASSED

- tests/test_seed137_regression.py — FOUND
- tests/test_cbc_backend.py (panel extension) — FOUND
- Commit ce06acd — FOUND
- Commit 75ba14d — FOUND
- Full suite 105 passed including slow; frozen dirs byte-clean; no data/ writes.
