---
phase: 04-exactbackend-cbc-reference
plan: 03
subsystem: solvers
tags: [had2, obstruction-enumeration, differential-testing, checksum, set-equality, brute-force, tdd]

# Dependency graph
requires:
  - phase: 04-exactbackend-cbc-reference
    plan: 01
    provides: "solvers/problems/had2.py (enumerate_had2 + build_had2_problem + ChecksumError), solvers/backend.get_backend('cbc'), solvers/result.Status/ExactOutcome"
  - phase: 01-pinned-environment-verbatim-port
    provides: "generators/tfp.triangle_free_process (frozen, read-only regeneration of seed-1/seed-137 H)"
provides:
  - "tests/test_had2_problem.py — SET-equality proof of the obstruction enumeration vs test-local Appendix C.4 naive O(|E_G|^2) loops at n=31 on seeds 1 and 137; pinned checksum literals; mutation->ChecksumError non-vacuity proof; triangle-refusal; exhaustive brute-force had2 differential + alpha(H) domain sanity at n<=8"
affects: [04-04 seed-137 regression (enumeration now proven semantically identical to legacy loop), phase-05 CP-SAT backend (same Had2Problem semantics, now pinned from both sides)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Differential testing from both sides: constraint-SET equality vs the legacy naive loops (same semantics, different algorithm) AND value equality vs an exhaustive brute force (independent semantics, no shared import) — the enumeration is pinned structurally and behaviorally"
    - "Test-local reference code discipline: the Appendix C.4 naive loops and the brute-force clique search live ONLY in the test file; grep -rl 'def _naive' src/alpha2/ returns nothing"
    - "Mutation seam without touching src/: monkeypatch the module-level enumerate_had2 with a wrapper that drops exactly one element from one conflict class, then drive the REAL gate inside build_had2_problem — pytest.raises(ChecksumError) per class"

key-files:
  created:
    - "tests/test_had2_problem.py"
  modified: []

key-decisions:
  - "Mutation test drives the real checksum gate via monkeypatch of had2.enumerate_had2 rather than exposing the gate as a new module-level function: the plan preferred an additive had2.py change, but the orchestrator locked this plan to tests/test_had2_problem.py only — the monkeypatch seam exercises the identical gate code path with zero src/ modification"
  - "Brute-force reference uses a plain recursive clique search with only a cardinality bound (no heuristics) over <= 36 candidates — correctness over speed at n<=8, per plan"
  - "alpha(H) lower-bound witness computed by exhaustive 2^n subset scan (n<=8), the strongest form of the domain-sanity bound rather than a greedy witness"
  - "Panel is 9 deterministic instances: c5, empty5, matching6 closed forms + triangle_free_process seeds 1/2 at n in {6, 7, 8}"

patterns-established:
  - "Pattern: every CBC leg asserts status is Status.PROVED_OPTIMAL BEFORE calling exact_value() — no ungated value reads even in tests"

requirements-completed: [EXACT-02]

# Metrics
duration: ~8min
completed: 2026-07-21
---

# Phase 4 Plan 03: Obstruction-Enumeration Set-Equality + Brute-Force Differential Summary

**One-liner:** SC3 proven — `enumerate_had2` is SET-equal to the Appendix C.4 naive O(|E_G|²) loops at n=31 on seeds 1 and 137 (checksums (131, 998, 726) / (177, 1913, 3782) pinned in-file), the ChecksumError gate provably raises on any single dropped conflict, and an independent exhaustive brute force agrees with CBC PROVED_OPTIMAL on all 9 small-panel instances.

## What Was Built

`tests/test_had2_problem.py` (27 tests, every-commit tier, 1.5 s):

1. **Set-equality differential (seeds 1 & 137, n=31):** the Appendix C.4 naive loops — ordered i<j pair-pair scan with the `len({a,b,c,d}) < 4` skip and 4-way adjacency test, (v, G-edge) single-pair scan, H-edge single-single scan — embedded test-local and adapted to COLLECT sets with the enumeration's element conventions ((u,v) u<v; (v,(a,b)) a<b; frozenset({e1,e2})). Asserts `ss_enum == ss_naive`, `sp_enum == sp_naive`, `pp_enum == pp_naive` as SETS on both seeds — a count match with different members would be a masked bug (Pitfall 3's C4 double-count and Pitfall 4's H/G flip both fail loudly here).
2. **Checksum literals:** (len(ss), len(sp), len(pp)) == (131, 998, 726) for seed 1 and (177, 1913, 3782) for seed 137, embedded as in-file literals (test_corpus_r1 discipline, no cross-test imports).
3. **Mutation → ChecksumError:** for each conflict class in turn, a wrapper around the real `enumerate_had2` drops one deterministically-chosen element; `build_had2_problem` raises `ChecksumError` through its real gate (raise-based, never assert — not optimization-strippable). A control leg confirms the unmutated build passes.
4. **Triangle refusal:** H with triangle 0-1-2 on n=4 raises ValueError at build — the totality precondition is enforced.
5. **Brute-force differential (n≤8):** a test-local exhaustive reference (candidates = singletons + G-edges; compatible ⟺ disjoint AND joined by a G-edge; max clique by plain recursive branch-and-bound over ≤36 candidates) that imports NOTHING from `alpha2.solvers.problems.had2`. On all 9 panel instances (c5, empty5, matching6, tfp-n{6,7,8}-s{1,2}): brute == `get_backend("cbc").solve_had2(...).exact_value()` with status gated to PROVED_OPTIMAL before every value read.
6. **Domain sanity:** had₂ ≥ α(H) (exhaustive 2ⁿ subset scan) on every panel instance.

## Verification Results

- `uv run --frozen --extra dev pytest tests/test_had2_problem.py -q` — 27 passed in 1.5 s (every-commit tier, well under the ~30 s budget).
- Full suite: `uv run --frozen --extra dev pytest -q -m "not slow"` — 87 passed, 3 deselected.
- `grep -rl "def _naive" src/alpha2/` — empty (naive loops are test-local only).
- `git diff --quiet src/alpha2/corpus src/alpha2/repro src/alpha2/generators data/` — frozen artifacts untouched.
- Warnings in the run are pulp 3.3.2's own `_v4_deprecation` notices (pinned-dependency behavior, pre-existing, out of scope).

## Deviations from Plan

**1. [Rule 3 - Blocking constraint] Mutation test uses a monkeypatch seam instead of exposing the gate in had2.py**
- **Found during:** Task 1
- **Issue:** the plan's action text preferred "exposing the gate as a module-level function in had2.py" (additive), but this executor's scope is locked to `tests/test_had2_problem.py` only (04-02 runs in parallel; src/ is off-limits this plan).
- **Fix:** pytest's `monkeypatch` replaces `had2.enumerate_had2` with a thin wrapper that drops one element per class; `build_had2_problem` then exercises its REAL internal gate against the tampered sets. Identical gate code path, zero src/ modification.
- **Files modified:** tests/test_had2_problem.py only
- **Commit:** bee6b31

No other deviations — plan executed as written.

## TDD Gate Compliance

Both tasks carry `tdd="true"`, but this is a test-only plan validating the wave-1 implementation (`had2.py`, already merged into the base): there is no GREEN implementation step available, so no temporal RED state exists. Non-vacuity is instead proven structurally — the mutation tests demonstrate the gate raises when the enumeration is tampered, and the set-equality tests compare against an independently-coded reference. Commits are `test(04-03)` type per task.

## Threat Model Outcomes

- **T-4-04 (obstruction under-generation → wrong optimum):** mitigated — set-equality on both anchor seeds + pinned checksums + per-class mutation raise + independent value differential at n≤8.
- **T-4-07 (H/G flip, C4 double-count):** mitigated — both regressions fail the set-equality and checksum tests loudly; triangle-refusal enforces the totality precondition.
- **T-4-05 (gate stripped under -O):** ChecksumError path is raise-based; 04-02's -O canary covers it live.

No new security-relevant surface introduced (test-only file; no network, auth, file, or schema changes). No stubs.

## Commits

| Task | Commit | Description |
| ---- | ------ | ----------- |
| 1 | bee6b31 | test(04-03): prove set-equality vs Appendix C.4 naive loops + checksum gate |
| 2 | 623f29a | test(04-03): exhaustive brute-force had2 differential at n<=8 |

## Self-Check: PASSED

- tests/test_had2_problem.py — FOUND
- Commit bee6b31 — FOUND
- Commit 623f29a — FOUND
- 27/27 tests green; full suite 87 passed; frozen dirs clean.
