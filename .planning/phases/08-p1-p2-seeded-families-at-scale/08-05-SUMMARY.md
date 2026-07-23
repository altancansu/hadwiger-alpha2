---
phase: 08-p1-p2-seeded-families-at-scale
plan: 05
subsystem: pool-sumfree
tags: [pool-2, ilp-frontier, deterministic-budget, cp-sat, cbc, research-a4, exact-window, no-wall-clock]

# Dependency graph
requires:
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 01
    provides: "RED contract test_frontier (measure_ilp_frontier per-n proved-flag + downward-monotone) this plan makes GREEN"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 02
    provides: "SolveParams.det_time (CP-SAT max_deterministic_time) + SolveParams.det_nodes (CBC maxNodes) — the additive deterministic budgets this plan consumes; Abelian Γ + structured/random sum-free generators + cayley_adj_abelian"
provides:
  - "alpha2.pool.sumfree.frontier.measure_ilp_frontier(ns, *, det_budget|det_time|det_nodes, num_workers=1, kinds, seed, table_path) — per-n PROVED/UNPROVED table under a deterministic budget on BOTH backends; only gate survivors timed"
  - "alpha2.pool.sumfree.frontier.run_frontier_probe(det_time, det_nodes, ns) — persists the compact frontier_report (per-n bools + frontier_n + budgets + solver versions) to paths.SUMFREE_FRONTIER_REPORT; logs every probe row"
  - "alpha2.pool.sumfree.frontier.exact_window_max(report) -> int — the exact-window boundary the 08-06 sweep reads to route non-packing instances (n<=window exact g>0 candidate; n>window RESISTANT E3)"
  - "alpha2.pool.sumfree.frontier.derive_frontier_n(table) — conservative contiguous-from-bottom downward boundary"
  - "paths.SUMFREE_FRONTIER_TABLE / paths.SUMFREE_FRONTIER_REPORT — data/results artifacts for the measured frontier"
affects: [08-06 slow grid sweep (reads exact_window_max to route non-packing instances)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BOTH co-equal backends bounded DETERMINISTICALLY — CP-SAT det_time (max_deterministic_time, num_workers=1), CBC det_nodes (maxNodes, threads=1); NO wall-clock time_limit_s on any timed call (T-8-07; the exact failure this plan closes)"
    - "num_workers != 1 RAISES — a recorded frontier verdict must be single-worker (CLAUDE.md #3590/#3842/#4839); cores scale breadth, never determinism of one verdict"
    - "Only gate survivors are timed; a hard-gate KILL or a generator that declines this Γ (ValueError/NotImplementedError) is recorded un-timed, never fed to a backend"
    - "frontier_n is MEASURED budget-dependent evidence (A4), a function of (n, det_time, det_nodes) — never wall-clock speed, never a theorem; derive_frontier_n is conservative contiguous-from-bottom so a blip cannot inflate the trusted window (routing errs toward E3)"
    - "measure_ilp_frontier writes NOTHING unless table_path is given (dev/unit path is side-effect-free); the authoritative report is regenerated on the box at 08-06, not on a dev machine"

key-files:
  created:
    - src/alpha2/pool/sumfree/frontier.py
  modified:
    - src/alpha2/paths.py

key-decisions:
  - "Function signature follows the RED contract (det_budget + num_workers), NOT the plan's interface sketch (det_time/det_nodes/kinds); both are supported additively"
  - "det_budget is a convenience knob: sets det_time directly, derives a coarse machine-INDEPENDENT det_nodes cap so CBC stays deterministically bounded even in the single-knob dev path; the box probe passes det_time+det_nodes explicitly"
  - "No canonical data/results/sumfree_frontier.json generated here (Mac author+unit session, docs/COMPUTE.md) — it is the box's job at 08-06"
  - "POOL-2 NOT marked complete — shared across waves 08-04..08-07; this plan lands only the frontier-measurement leg"

requirements-completed: []

# Metrics
duration: ~25min
completed: 2026-07-23
---

# Phase 8 Plan 05: Empirical ILP Optimality-Proof Frontier (RESEARCH A4) Summary

**The ILP optimality frontier is now MEASURED, not assumed: `measure_ilp_frontier` walks a group-order grid, generates structured (Green–Ruzsa, Andrásfai middle-interval) and random-greedy sum-free Cayley instances, hard-gates them, and times ONLY the survivors on BOTH co-equal backends under a FIXED deterministic budget — CP-SAT `det_time` (num_workers=1), CBC `det_nodes` (maxNodes, threads=1) — with NO wall-clock cutoff on any timed call, so the per-n PROVED/UNPROVED verdict is a reproducible function of (n, budget), never machine speed (T-8-07). `run_frontier_probe` persists the compact per-n report + the derived conservative `frontier_n`, and `exact_window_max` exposes the boundary the 08-06 sweep reads to route a non-packing instance to an exact `g>0` verdict (n ≤ window) or the RESISTANT E3 queue (n > window). test_frontier GREEN; the 319 pre-existing tests stay green.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-07-23
- **Tasks:** 2 (both `type=auto`)
- **Files:** 1 created, 1 modified

## Accomplishments

- **Task 1 — `measure_ilp_frontier` (`082cad6`):** per-n driver over `ns`; per kind generates one representative S (structured deterministic; random via `gen_rng(seed)`, gracefully skipping a Γ the generator declines with ValueError/NotImplementedError), builds H via `cayley_adj_abelian`, computes `chi = n − matching_number` + omega/kappa, runs `run_gate`, and times ONLY gate survivors: `get_backend("cbc").solve_had2(..., SolveParams(det_nodes=det_nodes))` + `get_backend("cpsat").solve_had2(..., SolveParams(det_time=det_time))`, `proved` iff BOTH `PROVED_OPTIMAL`. On a proved had_2 < chi it escalates to the Tier-1 `solve_had3` the same bounded way. `num_workers != 1` raises; a fully-unbounded budget raises. `derive_frontier_n` is the conservative contiguous-from-bottom boundary.
- **Task 2 — `run_frontier_probe` + `exact_window_max` (`54f933c`):** default coarse grid (31, 61, 101, 151, 201, 251, 301); persists the compact `frontier_report` (per-n structured-proved booleans + `frontier_n` + det budgets + solver versions) atomically (tempfile → fsync → `os.replace`) to `paths.SUMFREE_FRONTIER_REPORT`; logs every probe row via `append_event`. `exact_window_max(report)` returns the boundary the 08-06 sweep consumes (handles int- and str-keyed JSON-loaded reports; 0 when nothing proved → conservative routing to E3). Added `SUMFREE_FRONTIER_TABLE`/`SUMFREE_FRONTIER_REPORT` to `paths.py`.

## Test Results

- **This plan's target GREEN:** `tests/pool/sumfree/test_frontier.py` → **2 passed** (`test_measure_ilp_frontier_reports_proved_flag_per_n`, `test_frontier_is_monotone_downward`). At the dev ns (12, 13, 14) every structured instance is hard-gate-KILLED (g1_criticality) or the generator declines the Γ (Z_12 middle band is not sum-free), so no backend is invoked — the driver reports `proved=False` honestly and monotonicity holds trivially (fast, no heavy solve, per environment discipline).
- **No regression:** full non-slow suite → **321 passed** (= 319 pre-existing + 2 new frontier). The 2 `test_screen.py` failures are `ModuleNotFoundError: alpha2.pool.sumfree.screen` — the wave 08-04 RED contract (`compute_g`/`classify_screen_outcome`, `screen.py` not yet created), explicitly deferred in the 08-03 summary and unrelated to this plan (out of scope per the SCOPE BOUNDARY). The 319 pre-existing green are unchanged.
- **Deterministic-budget discipline verified against CLAUDE.md:** every timed call passes ONLY `SolveParams(det_time=...)` (CP-SAT) or `SolveParams(det_nodes=...)` (CBC); no `time_limit_s` is ever passed to a timed backend call. `num_workers != 1` raises. Two runs on the same (ns, budget, seed) yield the same per-n table (no wall-clock input).
- **No repo pollution:** the Task 2 smoke test used a tempdir; no canonical `data/results/sumfree_frontier*` file was created (that is the box's job at 08-06). Frozen trust root untouched.

## Task Commits

1. **Task 1: measure_ilp_frontier — per-n PROVED/UNPROVED under deterministic budget** — `082cad6` (feat)
2. **Task 2: run_frontier_probe + exact_window_max sweep boundary** — `54f933c` (feat)

## Decisions Made

- **Signature follows the RED contract, not the plan sketch.** `test_frontier` pins `measure_ilp_frontier(ns, det_budget=..., num_workers=1)` with `result[n]["proved"]` a bool; the plan's interface sketch used `det_time/det_nodes/kinds/seed`. Both are supported: `det_budget` sets `det_time` directly and derives a coarse machine-independent `det_nodes` cap (so CBC is bounded even in the single-knob path); the box probe passes `det_time`+`det_nodes` explicitly. This is a Rule 3 blocking reconciliation — the RED test is the contract.
- **`num_workers != 1` raises.** A recorded frontier verdict must be single-worker (CLAUDE.md CP-SAT #3590/#3842/#4839); the parameter is accepted for the test's call site but any value other than 1 is rejected rather than silently ignored.
- **Conservative contiguous-from-bottom `frontier_n`.** So a single hard instance above the boundary can never inflate the exact window the sweep trusts — a misrouted instance errs toward the RESISTANT E3 queue, never toward a false `g>0` claim. This honors the program's radioactive-impossibility discipline.
- **No canonical report generated here.** Per docs/COMPUTE.md the authoritative `data/results/sumfree_frontier.json` is regenerated on the shared box (08-06); this Mac session delivers the code + GREEN unit test only.
- **POOL-2 NOT marked complete.** Shared across waves 08-04..08-07; this plan lands only the frontier-measurement leg. `requirements-completed: []`.

## Deviations from Plan

- **[Rule 3 — Blocking issue] Signature reconciled to the RED contract.** See Decisions above — `det_budget`/`num_workers` (the test's kwargs) are the canonical entry; `det_time`/`det_nodes`/`kinds`/`seed` (the plan sketch) are additive. No behavioral compromise: both backends are still bounded deterministically.
- **[Rule 3 — Plumbing] Added two `paths.py` constants** (`SUMFREE_FRONTIER_TABLE`, `SUMFREE_FRONTIER_REPORT`) so the frontier artifacts resolve through the sole path authority (paths-style discipline the plan calls for). `paths.py` was not in `files_modified`, but embedding a filesystem literal anywhere else would violate the module's contract.

Otherwise the plan executed as written.

## Known Stubs

None — `measure_ilp_frontier` runs the real gate + both real backends on survivors, `run_frontier_probe` persists a real report with real solver versions, and `exact_window_max` derives the real boundary. At the dev ns nothing survives the gate (correct, honest `proved=False`), which is measured behavior, not a stub.

## Deferred / Out of Scope

- `screen.py` (`compute_g`, `classify_screen_outcome`) → wave 08-04; its 2 `test_screen` tests stay RED by design (pre-existing; not this plan's target).
- The authoritative `data/results/sumfree_frontier.json` and any real large-n frontier run → wave 08-06 on the shared box (no heavy sweep runs in this Mac author+unit session).

## Self-Check: PASSED

- `src/alpha2/pool/sumfree/frontier.py` exists (measure_ilp_frontier / run_frontier_probe / exact_window_max / derive_frontier_n present; > 60-line artifact floor).
- Commits `082cad6` and `54f933c` present in git history.
- `test_frontier` GREEN (2 passed); full non-slow suite 321 passed with the 2 out-of-scope 08-04 `screen.py` RED failures unchanged.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Completed: 2026-07-23*
