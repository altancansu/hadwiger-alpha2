---
phase: 08-p1-p2-seeded-families-at-scale
plan: 04
subsystem: pool-sumfree
tags: [pool-2, g-screen, had2-had3-tiering, differential-verdict, deterministic-budget, radioactive-impossibility, trust-root, gate-kill, e3-queue, no-wall-clock]

# Dependency graph
requires:
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 02
    provides: "Abelian Γ + sum-free generators (structured/random) + cayley_adj_abelian + verify_sumfree_maximal + RNG v2 subseeds + additive SolveParams.det_time/det_nodes on both backends"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 03
    provides: "build_gscreen_record + HONEST_G_POSITIVE_STATEMENT + honest_statement_for; stdlib verify_gscreen_record; append_gscreen_certificate (verify-at-append store on SUMFREE_CORPUS)"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 05
    provides: "measure_ilp_frontier + exact_window_max boundary (the deterministic-budget wiring pattern this plan mirrors for screen_gap)"
provides:
  - "alpha2.pool.sumfree.screen.compute_g(chi, had_k) — the shared screen-gap formula (delegates to schema._compute_g)"
  - "alpha2.pool.sumfree.screen.classify_screen_outcome(*, chi, had_k, heuristic_hit, exact_proved) — radioactive-discipline labelling (heuristic hit→KILLED g≤0; had_k<χ→SHC_CANDIDATE g>0; miss/unproved→RESISTANT g None)"
  - "alpha2.pool.sumfree.screen.screen_gap(adj, n, chi, *, det_time, det_nodes) — had_2→had_3 tiering DRIVER via differential_verdict; both backends deterministically bounded; returns ScreenOutcome(terminal_state, had_2, had_3, g, family)"
  - "alpha2.pool.sumfree.screen.trust_root_verify_family — routes an untrusted solver family through verify_certificate (SOLE authority), returns k or None"
  - "alpha2.pool.sumfree.adjudicate.adjudicate_sumfree(descriptor, *, seed, det_time, det_nodes, ...) — end-to-end per-instance g(G) runbook + honest verified certificate"
  - "alpha2.pool.sumfree.adjudicate.adjudicate_gscreen — determinism-contract entry (det_budget/det_time+det_nodes; rejects wall-clock + num_workers≠1)"
  - "alpha2.pool.sumfree.adjudicate.adjudicate_grid_point — the compact {n, kind, gate_survived, terminal_state, g, had_2, had_3} row the 08-06 sweep aggregates"
affects: [08-06 slow grid sweep (drives adjudicate_grid_point over odd |Γ|=31–500)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The screen is NECESSARY-not-sufficient: a proved had_k<χ is g>0 SHC_CANDIDATE ONLY (screen), never a break — HONEST_G_POSITIVE_STATEMENT; a heuristic MISS is RESISTANT, never a g>0 point (Pitfall 1, T-8-01)"
    - "BOTH co-equal backends bounded DETERMINISTICALLY — CP-SAT det_time (max_deterministic_time, num_workers=1), CBC det_nodes (maxNodes); screen_gap RAISES if either budget absent; adjudicate_gscreen rejects wall-clock knobs + num_workers≠1 (T-8-07)"
    - "differential_verdict is the SOLE licenser: AGREED_KILL→g≤0, SHC_CANDIDATE(U<χ proved)→sound g>0 from the upper bound, INSUFFICIENT→RESISTANT; UnverifiedKill(U≥χ)→Tier-2 extract+verify; CriticalDisagreement propagates (QUARANTINE+HALT, never pick a winner)"
    - "verify_certificate is the SOLE family authority, called OUTSIDE any truth-expression; an unverifiable ≥χ upper-bound family routes conservatively to RESISTANT (never an unverified kill, never a false g>0)"
    - "runbook legs REPLICATED on the descriptor-built adj (NOT run_candidate, which regenerates from seed and ignores abelian descriptors); a HARD gate fail is a first-class KILLED-BY-GATE non-g outcome (g-plot over survivors only, T-8-13)"

key-files:
  created:
    - src/alpha2/pool/sumfree/screen.py
    - src/alpha2/pool/sumfree/adjudicate.py
  modified: []

key-decisions:
  - "screen.compute_g delegates to schema._compute_g so the emit-time and screen-time gap derivations share ONE formula (a divergence could mislabel an instance)"
  - "DEVIATION (Rule 3, conservative): the backends expose only the Tier-1 seagull solve_had3 (UPPER bound), so a rigorous Tier-2 exact had_3 is unavailable — a proved U≥χ whose extracted family does NOT certify a K_χ minor is routed to RESISTANT (E3/Tier-2 obligation) rather than an unproven g>0"
  - "POOL-2 NOT marked complete — the slow grid sweep (08-06) remains; requirements-completed: []"

patterns-established:
  - "ScreenOutcome namedtuple as the tiering's structured return; the caller (adjudicate) builds/stores the certificate"
  - "trust_root_verify_family: build a throwaway corpus record (extract_witness M/U + full family) → verify_certificate → k or None; shared by the heuristic-HIT and screen-KILL legs"

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-07-23
---

# Phase 8 Plan 04: g(G) Per-Instance Runbook — the P2 Break-Hunt Spine Summary

**The per-instance g(G) runbook is now end-to-end: a `{invariant_factors, S, tag}` descriptor is built into H = Cay(Γ, S), hard-gated (gate-kills first-class), reduced to χ = n − ν(H), and walked through the had₂ → had₃ seagull tiering — both co-equal backends bounded WITHOUT wall-clock (CP-SAT `det_time`, CBC `det_nodes`) and cross-examined by the SOLE licenser `differential_verdict` — yielding an honest, trust-root-verified, deterministic verdict: KILLED (g ≤ 0, verified K_χ family), SHC-CANDIDATE (g > 0, `HONEST_G_POSITIVE_STATEMENT` only — never a break), RESISTANT (E3 queue), or KILLED-BY-GATE, stored append-only. `screen.compute_g` / `classify_screen_outcome` turned the 2 remaining `test_screen` tests GREEN; the 321 pre-existing tests stay green.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-07-23
- **Tasks:** 2 (both `type=auto tdd=true`)
- **Files:** 2 created, 0 modified

## Accomplishments

- **Task 1 — `screen.py` (`cb32199`):** `compute_g(chi, had_k)` (delegates to `schema._compute_g` — one shared gap formula) + `classify_screen_outcome(*, chi, had_k, heuristic_hit, exact_proved)` (the radioactive-discipline truth table: heuristic hit→KILLED g≤0; exact-proved had_k<χ→SHC_CANDIDATE g>0; had_k≥χ→KILLED; otherwise→RESISTANT g None). `screen_gap(adj, n, chi, *, det_time, det_nodes)` is the tiering DRIVER: had₂ dual-backend optimize under `SolveParams(det_time, det_nodes)` → `differential_verdict` (AGREED_KILL→KILLED g≤0 with the CBC family for the caller to verify; SHC_CANDIDATE→escalate; INSUFFICIENT→RESISTANT); had₃ Tier-1 seagull the same bounded way (a proved `U<χ` is a SOUND g>0 from the upper bound; `UnverifiedKill(U≥χ)`→Tier-2 `trust_root_verify_family`). `_require_deterministic_budget` RAISES if either budget is absent; `CriticalDisagreement` propagates.
- **Task 2 — `adjudicate.py` (`21636cf`):** `adjudicate_sumfree(descriptor, *, seed, det_time, det_nodes, ...)` REPLICATES the runbook legs on the descriptor-built `adj` (build via `Abelian`+`cayley_adj_abelian`, S from the descriptor or generated for its tag with a `verify_sumfree_maximal` re-check; χ = n − `matching_number`; `run_gate` HARD fail → first-class KILLED-BY-GATE, log only; heuristic `solve` HIT → `trust_root_verify_family` (`verify_certificate`) → KILLED store; MISS → `screen_gap`). Maps the screen outcome to an honest g(G) record (KILLED carries the verified family; SHC_CANDIDATE carries `HONEST_G_POSITIVE_STATEMENT`; RESISTANT → E3-queue log, no cert) and appends via `append_gscreen_certificate`. `adjudicate_gscreen` is the determinism entry (rejects `wallclock_budget`/`time_limit_s`/unknown knobs and `num_workers≠1`); `adjudicate_grid_point` is the compact sweep row. Every step emits an `append_event(subsystem="pool/sumfree", ...)`.

## Task Commits

1. **Task 1: g(G) screen metric + had_2→had_3 tiering** — `cb32199` (feat)
2. **Task 2: adjudicate_sumfree end-to-end runbook + honest certificate** — `21636cf` (feat)

**Plan metadata:** this commit (docs: complete 08-04 plan)

## Files Created/Modified

- `src/alpha2/pool/sumfree/screen.py` (251 lines) — `compute_g`, `classify_screen_outcome`, `screen_gap`, `trust_root_verify_family`, `ScreenOutcome`
- `src/alpha2/pool/sumfree/adjudicate.py` (353 lines) — `adjudicate_sumfree`, `adjudicate_gscreen`, `adjudicate_grid_point`

## Test Results

- **This plan's target GREEN:** `tests/pool/sumfree/test_screen.py` → **8 passed** (the 2 previously-RED `compute_g` / `classify_screen_outcome` tests are now GREEN; the 6 verifier/honesty tests from 08-03 stay green).
- **No regression:** full non-slow suite → **323 passed** (= 321 pre-existing + 2 new `test_screen`). Non-slow `tests/pool/sumfree` → 50 passed, 7 deselected.
- **Contract guards verified directly:** `adjudicate_gscreen` rejects `wallclock_budget`, `time_limit_s`, `num_workers≠1`, and a fully-unbounded budget (all raise `ValueError`).
- **Runbook legs validated at dev scale:** a Z_5 descriptor runs deterministically to KILLED-BY-GATE (both runs agree); `trust_root_verify_family` returns `k=3` on the hand-verified Z_5 C_5 K_3 minor and `None` on a bogus family; the KILLED gscreen record assembles, appends (verify-at-append), and re-verifies radioactive-clean (g = 0.0). At the dev ns every odd-|Γ| structured/random instance is hard-gate-KILLED at `g1_criticality` (documented in 08-05), so the exact screen path is not solver-exercised on the Mac — that is the 08-06 box job.
- **Frozen trust root untouched:** `git status` of `src/alpha2/generators/cayley.py`, `data/corpus/`, `src/alpha2/corpus/` is empty.
- **Determinism (slow) tests:** `test_determinism.py` (`adjudicate_gscreen`, marked `slow`) is not run in the non-slow Mac session; its wall-clock-rejection + num_workers guards were exercised directly (above) and the exact double-run replay is a box/nightly gate.

## Decisions Made

- **`compute_g` delegates to `schema._compute_g`.** The emit-time gap (schema) and the screen-time gap (screen) share ONE formula — a divergence could mislabel an instance (a false KILLED/SHC boundary), so there is a single source of truth.
- **The screen returns families for the caller to verify; screen owns the Tier-2 verify.** `screen_gap` returns the CBC family on an AGREED_KILL (the caller, adjudicate, routes it through `verify_certificate`), but performs the Tier-2 `trust_root_verify_family` itself on an `UnverifiedKill(U≥χ)` — mirroring the plan's leg split.
- **POOL-2 NOT marked complete.** Shared across waves 08-02..08-07; this plan lands the adjudication spine, but the slow grid sweep (08-06) is still outstanding. Marking POOL-2 complete on the spine would violate the reporting discipline. `requirements-completed: []`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking / conservative] Tier-2 exact had₃ unavailable → unverifiable U≥χ routes to RESISTANT, not an unproven g>0**
- **Found during:** Task 1 (`screen_gap` had₃ tiering)
- **Issue:** The plan's had₃ ladder says a proved `U≥χ` whose extracted family fails verification should fall through to "exact <χ → g>0". But the backends expose only the Tier-1 seagull `solve_had3` (an UPPER bound, `value_is_upper_bound=True`); there is no Tier-2 full-had₃ exact solve to PROVE `had₃ < χ`. Emitting g>0 without that proof would be a radioactive heuristic-adjacent claim.
- **Fix:** On `UnverifiedKill(U≥χ)`, `screen_gap` extracts the family and routes it through `verify_certificate`: a verified ≥χ family → KILLED (g≤0, packs); a family that does NOT certify → **RESISTANT** (E3 / Tier-2 exact obligation), never a false g>0. This errs toward the radioactive-impossibility discipline (routing toward E3, never toward an unproven break).
- **Files modified:** `src/alpha2/pool/sumfree/screen.py`
- **Verification:** `trust_root_verify_family` returns `None` on a bogus family (verified directly); the branch returns `ScreenOutcome(RESISTANT, ...)`.
- **Committed in:** `cb32199` (Task 1 commit)

**2. [Rule 2 - Missing critical] `screen_gap` requires a deterministic budget on BOTH backends**
- **Found during:** Task 1
- **Issue:** A recorded screen verdict that leaves either backend unbounded would be machine-speed-dependent (T-8-07, CP-SAT #3590/#3842/#4839).
- **Fix:** `_require_deterministic_budget` RAISES `ValueError` unless BOTH `det_time` (CP-SAT) and `det_nodes` (CBC) are supplied; `adjudicate_gscreen` additionally rejects wall-clock knobs and `num_workers≠1`.
- **Files modified:** `src/alpha2/pool/sumfree/screen.py`, `src/alpha2/pool/sumfree/adjudicate.py`
- **Verification:** direct smoke test — unbounded / wall-clock / multi-worker calls all raise.
- **Committed in:** `cb32199`, `21636cf`

---

**Total deviations:** 2 auto-fixed (1 blocking/conservative, 1 missing-critical). Both preserve the radioactive-impossibility discipline; no scope creep (files_modified stayed screen.py + adjudicate.py).

## Issues Encountered

- The determinism (`adjudicate_gscreen`) tests are `slow` and the exact screen path only fires above the `g1_criticality` gate frontier — unreachable at dev ns on the Mac (per docs/COMPUTE.md, and consistent with the 08-05 finding that every dev-ns structured/random instance is hard-gate-KILLED). Resolved by validating each runbook leg directly (gate-kill determinism, `trust_root_verify_family` accept/reject, KILLED record assemble+store+re-verify) rather than through a full solver sweep, which is the 08-06 box job.

## Known Stubs

None. `screen_gap` runs both real backends through `differential_verdict`; `adjudicate_sumfree` runs the real gate + heuristic + trust root + store; the deterministic-budget guards are load-bearing (they raise). No placeholder/empty-value flows. The Tier-2 conservative-RESISTANT routing is an intentional, documented discipline choice (Deviation 1), not an unwired stub.

## Threat Flags

None — no new network endpoint, auth path, file-access pattern, or schema change beyond the plan's `<threat_model>`. The g(G) certificate append goes only to `paths.SUMFREE_CORPUS` (the isolated sum-free corpus); the frozen 296-corpus and CDM corpus are untouched.

## Next Phase Readiness

- The P2 break-hunt spine is complete: `adjudicate_grid_point` is the entry the **08-06 slow grid sweep** drives over odd |Γ| = 31–~500 (structured vs random), reading `exact_window_max` (08-05) to route non-packing instances (n ≤ window → exact g>0 candidate; n > window → RESISTANT E3).
- POOL-2 remains open (08-06 sweep outstanding); the authoritative sweep + any real large-n frontier run happen on the shared box, not this Mac session.

## Self-Check: PASSED

- `src/alpha2/pool/sumfree/screen.py` (251 lines ≥ 70 floor) and `src/alpha2/pool/sumfree/adjudicate.py` (353 lines ≥ 90 floor) exist on disk with all public symbols present.
- Task commits `cb32199` and `21636cf` present in git history.
- `test_screen` GREEN (8 passed); full non-slow suite 323 passed; frozen trust root diff empty.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Completed: 2026-07-23*
