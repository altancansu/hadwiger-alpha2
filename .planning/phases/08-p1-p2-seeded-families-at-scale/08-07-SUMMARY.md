---
phase: 08-p1-p2-seeded-families-at-scale
plan: 07
subsystem: pool-sumfree
tags: [pool-1, tfp, existence-only, heuristic-plus-verifier, dual-backend-exact, rng-v2, deterministic-budget, resistance-tracking, trust-root]

# Dependency graph
requires:
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 01
    provides: "P1 RED contract (test_p1_sweep + test_showpiece) this plan makes GREEN"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 02
    provides: "RNG v2 subseeds (gen_rng/search_rng) + additive SolveParams.det_time/det_nodes deterministic budgets on both backends"
provides:
  - "alpha2.pool.sumfree.p1.run_p1_tfp — one EXACT-had_2 sweep point (n=31–32), dual-backend + differential_verdict + trust root; DECIDED vs RESISTANT; deterministic in (n, seed, det_budget)"
  - "alpha2.pool.sumfree.p1.critical_sweep — many-seed n=31–32 aggregator; surfaces the RESISTANT set as the derived E3 queue (resistance tracking, SC1)"
  - "alpha2.pool.sumfree.p1.run_showpiece — large-n (≈1001–2001) EXISTENCE-ONLY: heuristic HIT → verify_certificate → dedicated P1 corpus; MISS → RESISTANT (never a result)"
affects: [11 E3 survivor protocol (RESISTANT queue consumers)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Existence-only above the ILP frontier: heuristic proposes, verify_certificate (SOLE trust root) disposes; a MISS is RESISTANT (E3 queue), NEVER a result, NEVER an impossibility claim (SRCH-02, T-8-11)"
    - "Reported had_2 verdict = deterministic function of (n, seed, det_budget): CP-SAT det_time + CBC det_nodes (fixed pure function of det_budget), never wall-clock (CLAUDE.md determinism, Pitfall 2)"
    - "RNG contract v2 gen/search subseeds + byte-exact descriptor rebuild (never RNG replay); frozen 296-corpus untouched (sweep in-memory, showpieces to a NEW dedicated corpus — T-8-12)"
    - "differential_verdict is the SOLE licenser; a CriticalDisagreement propagates (quarantine + HALT), never pick a winner between the two exact backends"

key-files:
  created:
    - src/alpha2/pool/sumfree/p1.py
  modified: []

key-decisions:
  - "POOL-1 marked COMPLETE — unlike POOL-2 (shared across 08-02..08-07), POOL-1 (the P1/TFP track) is delivered solely by this plan; the n=31–32 exact sweep + n≈1001–2001 existence-only showpieces + resistance tracking are all GREEN and trust-root verified"
  - "run_p1_tfp reimplements the exact-had_2 slice directly rather than calling battery.run_candidate — run_candidate is RNG-v1 + wall-clock and ignores its params arg, which is incompatible with the RNG-v2 + deterministic-budget must-haves AND the determinism test (Rule 3 blocking-issue fix, files_modified scope preserved)"
  - "n=31–32 go straight to exact had_2 (no gate fast-kill): the DECIDED/RESISTANT test contract has no gate-kill terminal state, and skipping the gate is strictly MORE thorough (every instance is exact-had_2 adjudicated)"

requirements-completed: [POOL-1]

# Metrics
duration: ~45min
completed: 2026-07-23
---

# Phase 8 Plan 07: P1 (Secondary) — TFP Family at Scale Summary

**The P1 secondary track went GREEN under full discipline: a deterministic n=31–32 EXACT-had_2 critical-size sweep (dual-backend CBC + CP-SAT under `differential_verdict` and the frozen trust root, verdict a pure function of `(n, seed, det_budget)` via CP-SAT `det_time` + CBC `det_nodes` — never wall-clock), plus large-n (n≈1001–2001) EXISTENCE-ONLY showpieces where the heuristic proposes and `verify_certificate` alone disposes (HIT → verified certificate appended to a NEW dedicated P1 corpus; MISS → RESISTANT, queued for E3, never a result and never an impossibility claim) — all on RNG contract v2 with byte-exact descriptor rebuild and the frozen 296-corpus / `generators/{tfp,cayley}.py` byte-untouched.**

## Performance

- **Duration:** ~45 min (dominated by the n=32 exact solve ~4 min and the n=2001 blossom + heuristic ~21 min)
- **Completed:** 2026-07-23
- **Tasks:** 2 (both `type=auto`)
- **Files:** 1 created (`src/alpha2/pool/sumfree/p1.py`), 0 modified

## Accomplishments

- **Task 1 — TFP critical-size sweep n=31–32 (`343d7b4`):** `run_p1_tfp(n, *, seed, det_budget, num_workers=1)` builds the TFP instance from the RNG-v2 `gen_rng(seed)` subseed, computes `chi = n − nu` (exact blossom), and runs the dual-backend exact had_2 under an additive deterministic budget (`SolveParams(det_time=det_budget, det_nodes=det_budget·5000)`). `differential_verdict` (the SOLE licenser) maps the pair to **DECIDED** (AGREED_KILL routed through the trust root, or a proven SHC-CANDIDATE with had_2 < chi) or **RESISTANT** (INSUFFICIENT). `critical_sweep` aggregates a many-seed grid and exposes the RESISTANT set as the derived E3 queue (SC1). `num_workers != 1` raises (CLAUDE.md determinism).
- **Task 2 — large-n existence-only showpiece (`a091060`):** `run_showpiece(n, *, seed)` generates the TFP instance (RNG v2), computes `chi`, and runs the heuristic `solve` for a size-≤2 K_χ model. A HIT is an untrusted proposal routed through `verify_certificate` (call, bind k, compare — the SOLE authority) and, once verified, appended to the NEW dedicated `paths.P1_SHOWPIECE_CORPUS`; the terminal state is **VERIFIED**. A MISS is **RESISTANT** (E3 queue) with `had_2 = None` — heuristic resistance is never a result, and there is no exact solve at these sizes.

## Test Results

- **This plan's 2 target modules GREEN:** `test_p1_sweep` → **3 passed** (n=31, n=32, and the `(n, seed)` determinism equality); `test_showpiece` → **2 passed** (n=1001 HIT → VERIFIED path, n=2001 both-branch contract).
- **No regression:** the full non-slow suite → **321 passed** (only the 2 expected `test_screen.py` failures remain, which are the 08-04 `screen.py`/adjudicate contract — RED by design, out of this plan's scope).
- **Frozen trust root untouched:** `git status` of `data/corpus/hadwiger_alpha2_certificates.json`, `src/alpha2/generators/tfp.py`, `src/alpha2/generators/cayley.py`, and `src/alpha2/corpus/` is empty.

## Task Commits

1. **Task 1: P1 TFP critical-size sweep n=31–32 (exact, deterministic budget)** — `343d7b4` (feat)
2. **Task 2: P1 large-n showpiece existence loop (heuristic HIT → verify)** — `a091060` (feat)

## Files Created/Modified

- `src/alpha2/pool/sumfree/p1.py` (created) — `run_p1_tfp` / `critical_sweep` (exact n=31–32 sweep + derived E3 queue), `run_showpiece` (existence-only large-n), plus `_tfp_instance` (RNG-v2 gen subseed + descriptor), `_det_params` (dual-backend deterministic budget), `_h_edges`, and the two result-dict builders.

## Decisions Made

- **POOL-1 marked COMPLETE.** Unlike POOL-2 (shared across waves 08-02..08-07, still open), POOL-1 (the P1/TFP-complement track) is delivered solely by this plan. Its acceptance — "reproduce the 296 (Phase 1–3), extend the critical-size sweep (n=31–32, many seeds), push showpieces toward n≈1001–2001 past the ILP range, with resistance tracking" — is fully met with GREEN, trust-root-verified tests.
- **`run_p1_tfp` reimplements the exact-had_2 slice rather than calling `battery.run_candidate`.** `run_candidate` is RNG-v1 (single `random.Random(seed)`) + wall-clock (`time_limit_s`) and ignores its own `params` argument, so it cannot honor either the RNG-v2 / deterministic-budget must-haves or the `(n, seed)` determinism equality test. The direct slice reuses the SAME machinery (`differential_verdict` + `verify_certificate` + `schema.build_record` + `extract_witness`), stays within the `files_modified: [p1.py]` scope, and keeps every record in memory so the frozen corpus is byte-untouched. (Deviation Rule 3 — see below.)
- **The n=31–32 path goes straight to exact had_2 (no gate fast-kill).** The DECIDED/RESISTANT contract has no gate-kill terminal state; skipping the gate is strictly more thorough (every instance is exact-had_2 adjudicated) and matches the plan's "each instance exact-had₂ adjudicated" truth.
- **CBC deterministic node cap is a fixed pure function of `det_budget`** (`det_nodes = det_budget · 5000`), paired with CP-SAT `max_deterministic_time = det_budget`, so the recorded verdict is machine-speed-independent on both co-equal backends; the cap only bounds work, never turning a proof into a non-proof for a given `(n, seed, det_budget)`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking issue] Function contract follows the RED test, not the plan prose.**
- **Found during:** Task 1 (start).
- **Issue:** The plan prose names `critical_sweep(...)` / `showpiece(...)` and says to "call the existing `run_candidate(...)`", but the pinned RED contract (`tests/pool/sumfree/test_p1_sweep.py`, `test_showpiece.py`) requires `run_p1_tfp(n, *, seed, det_budget, num_workers=1)` and `run_showpiece(n, *, seed)` with a specific DECIDED/RESISTANT/VERIFIED result shape — and `run_candidate` is RNG-v1 + wall-clock and ignores its `params` arg, incompatible with the RNG-v2 + deterministic-budget must-haves and the determinism test.
- **Fix:** Implemented the pinned names/signatures and built the exact-had_2 slice directly in `p1.py` (dual-backend + `differential_verdict` + trust root under a deterministic budget). `critical_sweep` is retained as the aggregator/derived-E3-queue helper the plan's Task 1 also calls for.
- **Files modified:** `src/alpha2/pool/sumfree/p1.py`.
- **Commit:** `343d7b4`, `a091060`.

No architectural changes (Rule 4) were needed; no package installs.

## Threat Model Compliance

- **T-8-11 (heuristic miss mislabeled as a result):** MISS → RESISTANT with `had_2 = None`; existence requires `verify_certificate`. ✔
- **T-8-12 (frozen 296-corpus write):** showpieces append to the NEW `paths.P1_SHOWPIECE_CORPUS` (auto-gitignored by `data/corpus/*.json`), the sweep keeps records in memory; frozen corpus byte-untouched. ✔
- **T-8-10 (unbounded n≈2001 generation):** existence-only (no exact solve), blossom bounded, heuristic under a `time_budget`. ✔
- **T-8-SC (package installs):** zero new packages. ✔

## Deferred / Out of Scope

- `test_screen.py` (2 tests) remains RED — the g(G) per-instance runbook + adjudicate is wave 08-04 (the P2 spine), not this secondary P1 track.
- No canonical large-n push here (Mac authoring session, docs/COMPUTE.md): the n=1001/2001 runs were dev-scale unit exercises; a canonical showpiece sweep belongs on the box.
- The `p1_showpiece_certificates.json` produced by the test run is gitignored runtime output (the frozen corpus is the only tracked `data/corpus/*.json`).

## Self-Check: PASSED

`src/alpha2/pool/sumfree/p1.py` exists on disk; both task commits (`343d7b4`, `a091060`) present in git history; the frozen trust root (`data/corpus/hadwiger_alpha2_certificates.json`, `src/alpha2/generators/{tfp,cayley}.py`, `src/alpha2/corpus/`) diff is empty.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Completed: 2026-07-23*
