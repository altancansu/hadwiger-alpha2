---
phase: 08-p1-p2-seeded-families-at-scale
plan: 06
subsystem: pool-sumfree
status: code-authored, box-run-pending
tags: [pool-2, structured-vs-random-sweep, grid, canonical-dedup, observable-bank, exact-window-routing, deterministic-budget, honesty-protocol, box-run-pending]

# Dependency graph
requires:
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 02
    provides: "Abelian Γ + structured/random sum-free generators + verify_sumfree_maximal net + pynauty-canonical dedup + RNG v2 subseeds + additive SolveParams.det_time/det_nodes"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 04
    provides: "adjudicate_grid_point — the compact {n, kind, gate_survived, terminal_state, g, had_2, had_3} row this sweep aggregates"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 05
    provides: "exact_window_max — the measured ILP-window boundary the sweep reads to route non-packing outcomes (n≤window exact g>0 candidate; n>window RESISTANT E3)"
provides:
  - "alpha2.pool.sumfree.sweep.grid_descriptors(order_max, seed, non_cyclic, log_path) — odd |Γ| grid enumeration + canonical dedup of merged structured/random streams, non-cyclic all-primes-≡1-mod3 exclusion guard (logged)"
  - "alpha2.pool.sumfree.sweep.group_observables(factors) — zero-cost group-structure cross-sections (rank, exponent, prime-residue signature, cyclic?, exact |Aut| via Hillar–Rhea, elementary-abelian)"
  - "alpha2.pool.sumfree.sweep.run_sweep(...) — the instance-parallel grid driver; per-verdict determinism preserved; exact-window routing; observable bank folded in; appends plot data to paths.SUMFREE_SWEEP"
  - "alpha2.pool.sumfree.sweep.aggregate_sweep(rows, exact_window) — per-(kind, order) gate-survival / verified-g≤0 / exact-g>0 / RESISTANT-rate + structured-vs-random g / resistant-rate series"
  - "alpha2.pool.sumfree.sweep.main — the box CLI entrypoint (python -m alpha2.pool.sumfree.sweep --order-max 500 --det-time <b> --det-nodes <b>)"
affects: [08-06 canonical box sweep (the SC2 deliverable — NOT run in this Mac session)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The sweep changes only WHAT WE RECORD, never what counts as a break: PRIMARY = the LOCKED g(G) + RESISTANT-rate structured-vs-random test; every observable-bank cross-section is SECONDARY/exploratory (hypothesis-generating, must re-test on fresh seeds); the exploratory count is recorded for multiple-comparison honesty"
    - "exact-window routing (RESEARCH §Consequence): a g>0 screen (SHC_CANDIDATE) is an exact g>0 candidate ONLY within the measured ILP window; ABOVE it a non-packing structured instance is RESISTANT (E3), NEVER a reported g>0 (effective_state re-routes it)"
    - "instance-level BREADTH-only parallelism: workers compute rows, the PARENT writes the sweep event stream in descriptor order, so contention can never reorder/flip a recorded verdict; both backends already deterministically bounded inside the adjudicator (T-8-07); run_sweep RAISES without det_time+det_nodes"
    - "the unresolved GR non-cyclic 'all primes ≡1 mod3' type-II case is EXCLUDED with a logged reason (T-8-17); the curated non-cyclic set (primes 3/5, ≢1 mod3) passes the guard; verify_sumfree_maximal runs on every generated S regardless"
    - "exact |Aut(Γ)| via the Hillar–Rhea per-prime formula is recorded as an exploratory symmetry axis (never gates a verdict — a bug there can only mislabel a group-by axis, never manufacture a break)"

key-files:
  created:
    - src/alpha2/pool/sumfree/sweep.py
    - tests/pool/sumfree/test_sweep.py
  modified: []

key-decisions:
  - "CODE AUTHORED, BOX RUN PENDING — the fast unit tests are GREEN, but the canonical |Γ|=31–500 --order-max 500 sweep (SC2) and the human-verify checkpoint (Task 3) are the box job the orchestrator drives next; this Mac session did NOT run the full grid or any -m slow sweep"
  - "POOL-2 NOT marked complete — the authoritative sweep + its plot dataset (data/results/sumfree_sweep.jsonl) and honest g>0 certificates are produced on the box; marking POOL-2 complete before the canonical sweep would violate the reporting discipline"
  - "run_sweep uses adjudicate_grid_point per descriptor (plan Task 2) and OVERRIDES the row kind with the fine-grained family (structured:green_ruzsa / structured:middle_interval / random_greedy) so the per-family series the plan requires survives adjudicate's coarse structured|random tag"
  - "chi/abs_gap recovered exactly from the recorded g + had_k (no extra solve); det_work records the deterministic BUDGET (the compact grid row does not surface consumed solver work) — an honest partial, documented"

requirements-completed: []

# Metrics
duration: ~40min
completed: 2026-07-23 (code only; box sweep pending)
---

# Phase 8 Plan 06: Structured-vs-Random g(G) Grid Sweep — CODE AUTHORED (box run pending)

**STATUS: code-authored, box-run-pending.** `sweep.py` is authored and its dev-scale
(`-m "not slow"`) unit tests are GREEN, but the canonical `|Γ|=31–500 --order-max 500`
structured-vs-random g(G) sweep (the SC2 deliverable) and the Task-3 human-verify
checkpoint have **NOT** run in this Mac authoring session — they are the box job the
orchestrator drives next (docs/COMPUTE.md). The plot dataset
`data/results/sumfree_sweep.jsonl` and any honest g>0 certificates are **pending** that
canonical run. This summary does NOT claim the sweep ran and does NOT mark POOL-2 complete.

The break-hunt driver `pool/sumfree/sweep.py` enumerates the odd-|Γ| grid (all cyclic
31–~500 plus the curated non-cyclic set, EXCLUDING the unresolved Green–Ruzsa non-cyclic
"all primes ≡1 mod3" type-II case with a logged reason), builds structured (Green–Ruzsa /
Andrásfai middle-interval) + random-greedy sum-free Cayley instances, canonically dedups
the MERGED streams (pynauty certificate; WL-hash forbidden; collisions logged not dropped),
adjudicates each survivor through `adjudicate_grid_point` under a DETERMINISTIC budget on
BOTH backends, and aggregates the falsifiable plot data (g vs |Γ|, structured vs random,
gate-survival + RESISTANT-rate) with the exact-window routing (g>0 candidate only ≤ window;
above → RESISTANT). The observable bank is folded in (had₃−had₂, abs_gap, S_density,
det_work per instance; rank / exponent / prime-residue signature / cyclic? / exact |Aut|
group-by axes) under a strict PRIMARY-vs-SECONDARY honesty protocol.

## Accomplishments

- **Task 1 — grid + canonical dedup + observable bank (`b1328e8`):** `grid_descriptors`
  (odd cyclic 31..order_max + curated non-cyclic; the `_excluded_gr_noncyclic` guard skips
  the non-cyclic all-primes-≡1-mod3 type-II case with reason "unresolved GR non-cyclic
  type-II"; per-family structured + random descriptors merged and passed through
  `dedup.dedup`, first descriptor kept, collapsed dups + structured-vs-random collisions
  LOGGED). `group_observables` computes the zero-cost cross-sections (exact |Aut| via the
  Hillar–Rhea per-prime formula, verified against |Aut(Z_p)|=p−1, |Aut(Z_3²)|=48,
  |Aut(Z_9)|=6).
- **Task 2 — run_sweep + aggregation (`ab6297e`):** `run_sweep` drives the deduped grid
  through `adjudicate_grid_point` (both backends deterministically bounded; RAISES without
  det_time+det_nodes), enriches each row with the observable bank + exact-window annotation
  (`effective_state` re-routes a g>0 screen above the window to RESISTANT), appends the plot
  data to `paths.SUMFREE_SWEEP`, and aggregates per (kind, order) into the structured-vs-
  random g / resistant-rate / gate-survival series. Instance-level parallelism is
  breadth-only with parent-serial event-stream writes (per-verdict determinism preserved).
  `main` is the box CLI entrypoint. Multiple-comparison honesty: the exploratory
  cross-section count is recorded beside the primary test.

## Task Commits

1. **Task 1: grid enumeration + canonical dedup + observable bank** — `b1328e8` (feat)
2. **Task 2: instance-parallel run_sweep + g-vs-|Γ| aggregation** — `ab6297e` (feat)

## Test Results

- **This plan's targets GREEN (dev scale, `-m "not slow"`):**
  `pytest tests/pool/sumfree -k "sweep or grid or dedup"` → 9 passed;
  `-k "sweep or resistant or aggregate"` → 11 passed (9 new `test_sweep.py` tests total).
- **No regression:** full non-slow suite → **332 passed** (= 323 pre-existing + 9 new
  `test_sweep`). Non-slow `tests/pool/sumfree` → 59 passed, 7 deselected.
- **Frozen trust root untouched:** `git diff` of `generators/cayley.py`, `data/corpus/`,
  `src/alpha2/corpus/` is empty.
- **NOT run (box job):** the `--order-max 500` canonical sweep and any `-m slow` grid — no
  `data/results/sumfree_sweep.jsonl` canonical dataset was produced on the Mac.

## Deviations from Plan

- **[Rule 2 — missing critical] fine-grained per-family kind on the sweep row.**
  `adjudicate_grid_point` reports the coarse `structured|random` tag, but the plan requires
  per-family series (structured:green_ruzsa / structured:middle_interval / random_greedy).
  `run_sweep` overrides the row `kind` with the descriptor's fine-grained family so the
  required series survives. Files: sweep.py only.
- **[Rule 3 — honest partial] `det_work` records the deterministic BUDGET, not consumed
  work.** The compact grid row does not surface actual solver work consumed to settle had₃;
  recording the deterministic (det_time, det_nodes) budget is the reproducible difficulty
  bound available without modifying `adjudicate.py` (out of scope). Documented on the row.

## Known Stubs

None. `grid_descriptors` runs the real generators + real pynauty dedup; `run_sweep` runs
the real adjudicator; the deterministic-budget guard is load-bearing (raises). The pending
item is the CANONICAL BOX SWEEP (the full grid + plot dataset), which is intentionally not
run on the Mac (docs/COMPUTE.md), NOT an unwired stub.

## Next Step (orchestrator / box)

1. Run the canonical `--order-max 500` structured-vs-random g(G) sweep on the box under a
   deterministic (det_time, det_nodes) budget, num_workers=1 per verdict, instance-parallel.
2. Verify `data/results/sumfree_sweep.jsonl` carries per-family gate-survival + dense g≤0 +
   exact g>0 (within window only) + RESISTANT-rate series across 31–~500; spot-check a g>0
   certificate for honesty; confirm two-run determinism.
3. Record the outcome (falsified / resistant-tail / inconclusive) at the Task-3 human-verify
   checkpoint, THEN finalize POOL-2 completion + the authoritative SUMMARY.

## Self-Check: PASSED

- `src/alpha2/pool/sumfree/sweep.py` (633 lines ≥ 90 floor) and `tests/pool/sumfree/test_sweep.py` exist on disk.
- Task commits `b1328e8` and `ab6297e` present in git history.
- Dev-scale sweep/grid/dedup/aggregate/resistant tests GREEN; full non-slow suite 332 passed; frozen trust root diff empty.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Status: code-authored, box-run-pending — the canonical sweep + POOL-2 completion are finalized by the orchestrator AFTER the box run.*
