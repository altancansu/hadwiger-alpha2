---
phase: 08-p1-p2-seeded-families-at-scale
plan: 02
subsystem: pool-sumfree
tags: [pool-2, abelian-group, sum-free, cayley, green-ruzsa, andrasfai, rng-v2, pynauty-dedup, deterministic-budget, cp-sat, cbc]

# Dependency graph
requires:
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 01
    provides: "RED contract (test_group/test_generate/test_structured/test_dedup/test_rng_v2) + Γ/descriptor fixtures this plan makes GREEN"
provides:
  - "alpha2.pool.sumfree.group.Abelian — validated invariant-factor Γ arithmetic (add/neg/elements, n≤500 cap)"
  - "alpha2.pool.sumfree.rng — sha256 stage-independent RNG v2 subseeds (subseed/gen_rng/search_rng)"
  - "alpha2.pool.sumfree.generate — structured (middle-interval, Green–Ruzsa) + random-greedy sum-free S, abelian Cayley adjacency, descriptor rebuild, raise-based verify_sumfree_maximal net"
  - "alpha2.pool.sumfree.dedup — pynauty-canonical isomorph dedup over merged (Γ,S) streams (WL/graph-hash forbidden)"
  - "SolveParams.det_time (CP-SAT max_deterministic_time) + SolveParams.det_nodes (CBC maxNodes) — additive deterministic budgets on both backends"
affects: [08-04 screen/adjudicate/schema/store/verifier, 08-05 measure_ilp_frontier (det budget), 08-06 slow sweep, 08-07 p1 showpieces]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Raise-based verify_sumfree_maximal called INSIDE every generator — an unpinned density/coset formula can never surface a bad instance (RESEARCH Open Q1/A1/A2 non-fatal)"
    - "Structured generators key off the ARITHMETIC of |Γ| (smallest prime ≡2 mod3 / all ≡1 mod3), never an I/II/III numeral (Pitfall 6)"
    - "Descriptor-driven rebuild {invariant_factors, S} — byte-identical adjacency independent of stored S order (never RNG replay)"
    - "Additive deterministic solver budgets (None default → unbounded → frozen corpus byte-unchanged); wall-clock forbidden for recorded verdicts (Pitfall 2)"
    - "Single canonical dedup convention (pynauty.certificate); WL/graph-hash forbidden as key (Pitfall 5, source-inspection guard)"

key-files:
  created:
    - src/alpha2/pool/sumfree/group.py
    - src/alpha2/pool/sumfree/rng.py
    - src/alpha2/pool/sumfree/generate.py
    - src/alpha2/pool/sumfree/dedup.py
  modified:
    - src/alpha2/solvers/result.py
    - src/alpha2/solvers/cpsat.py
    - src/alpha2/solvers/cbc.py

key-decisions:
  - "POOL-2 NOT marked complete — shared across waves 08-02..08-07; this plan lands the generation foundation only (same discipline as 08-01)"
  - "green_ruzsa 3∣n cyclic case left NotImplemented (ambiguous coset-membership, RESEARCH Open Q1) — served by the random-greedy route; the tested cyclic-prime cases use the extremal middle interval"
  - "Deterministic budgets are additive + default None → unbounded → 296-corpus reproduction byte-unchanged; map_status untouched"

requirements-completed: []

# Metrics
duration: ~20min
completed: 2026-07-23
---

# Phase 8 Plan 02: POOL-2 Generation Foundation + Deterministic Solver Budget Summary

**The POOL-2 generation spine went GREEN: a validated finite-abelian-Γ representation, three verified symmetric sum-free generators (Andrásfai middle-interval, Green–Ruzsa extremal, random-greedy maximal) each guarded by a raise-based re-check, sha256 stage-independent RNG v2 subseeds, byte-identical descriptor rebuild, pynauty-canonical dedup — plus an ADDITIVE deterministic budget on BOTH exact backends (CP-SAT `max_deterministic_time`, CBC `maxNodes`) — with the frozen `generators/cayley.py`, `data/corpus/`, and the 296-corpus reproduction byte-untouched.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-23
- **Tasks:** 3 (all `type=auto tdd=true`)
- **Files:** 4 created, 3 modified

## Accomplishments

- **Task 1 — group + RNG v2 (`cbf6d20`):** `Abelian(factors)` with `_validate_factors` (reject non-int/bool/non-positive, cap n≤500 BEFORE any enumeration — V5/T-8-05), deterministic `elements()`/`add`/`neg`; `rng.subseed(master, stage)` sha256 first-8-bytes big-endian (stage-independent, stable) + `gen_rng`/`search_rng` factories.
- **Task 2 — generators + Cayley adjacency (`1b3476e`):** `can_add` over Γ (Pattern 1); `random_maximal_symmetric_sumfree` consuming the injected rng via `shuffle`; `middle_interval_sumfree` (Andrásfai); `green_ruzsa_sumfree` keyed off the arithmetic of |Γ| (Z_31→size 10, Z_53→size 18); `cayley_adj_abelian` + `adjacency_from_descriptor` (byte-identical rebuild); `verify_sumfree_maximal` raise-based net called inside every generator; `make_descriptor` provenance emitter.
- **Task 3 — dedup + dual-backend deterministic budget (`dce28a1`):** `dedup.canonical_key` via `pynauty.certificate` (single convention; WL/graph-hash forbidden guard passes source inspection); `dedup` collapses isomorphic H, keeps the first descriptor, logs collapsed duplicates. Additive `SolveParams.det_time`/`det_nodes`; `cpsat` sets `max_deterministic_time` (num_workers=1 + pinned seed kept); `cbc` passes `maxNodes=det_nodes` (None→unbounded→byte-unchanged); `map_status` untouched.

## Test Results

- **This plan's 5 target modules GREEN:** `test_group` + `test_rng_v2` + `test_generate` + `test_structured` + `test_dedup` → **30 passed**.
- **No regression:** the pre-existing suite (excluding the sumfree future-plan RED contracts, non-slow) → **273 passed** — the additive solver-budget edits and the 296-corpus reproduction are byte-unchanged.
- **Out of scope (still RED by design):** `test_schema/store/screen/frontier` (18) are the RED contracts for waves 08-04/08-05 — not this plan's targets.
- **Frozen trust root untouched:** `git diff` of `src/alpha2/generators/cayley.py`, `data/corpus/`, `src/alpha2/corpus/` is empty.

## Task Commits

1. **Task 1: Abelian group Γ + RNG contract v2 subseeds** — `cbf6d20` (feat)
2. **Task 2: sum-free generators (structured + random) + abelian Cayley adjacency** — `1b3476e` (feat)
3. **Task 3: canonical dedup + additive deterministic solver budget on both backends** — `dce28a1` (feat)

## Files Created/Modified

- `src/alpha2/pool/sumfree/group.py` — `Abelian` invariant-factor Γ, V5-validated (n≤500 cap), `itertools.product` enumeration, component-wise add/neg
- `src/alpha2/pool/sumfree/rng.py` — sha256 stage-independent `subseed` + `gen_rng`/`search_rng`
- `src/alpha2/pool/sumfree/generate.py` — `can_add`, `random_maximal_symmetric_sumfree`, `middle_interval_sumfree`, `green_ruzsa_sumfree`, `cayley_adj_abelian`, `adjacency_from_descriptor`, `verify_sumfree_maximal`, `make_descriptor`
- `src/alpha2/pool/sumfree/dedup.py` — `canonical_key` (pynauty.certificate) + `dedup`
- `src/alpha2/solvers/result.py` — additive `SolveParams.det_time` / `det_nodes`
- `src/alpha2/solvers/cpsat.py` — `max_deterministic_time = det_time` in both `solve_had2`/`solve_had3`
- `src/alpha2/solvers/cbc.py` — `PULP_CBC_CMD(maxNodes=det_nodes)` in both `solve_had2`/`solve_had3`

## Decisions Made

- **POOL-2 NOT marked complete.** POOL-2 is shared across waves 08-02..08-07; this plan delivers only the generation foundation. It is satisfied when the g-screen/store/verifier/adjudicate waves make the full RED contract GREEN — marking it complete on the foundation would violate the program's reporting discipline (nothing counts as found until the verifier passes). `requirements-completed: []`.
- **green_ruzsa 3∣n cyclic case left `NotImplementedError`.** The exact coset-membership formula for `3∣n` (and the non-cyclic "all primes ≡1 mod3" type) is the RESEARCH-flagged ambiguous case (Open Q1); those Γ are served by the random-greedy route / excluded from the grid. The tested cyclic-prime cases (Z_31 all-≡1-mod3, Z_53 ≡2-mod3) use the extremal middle interval, which the raise-based `verify_sumfree_maximal` confirms symmetric+sum-free+maximal.
- **Deterministic budgets are additive and default None → unbounded.** So the frozen 296-corpus reproduction path is byte-unchanged (verified: 273 pre-existing tests still green); `map_status` is untouched (a CBC node-limit stop already maps to INCUMBENT_ONLY, never a false PROVED_OPTIMAL). Wall-clock is forbidden for any recorded verdict (Pitfall 2).

## Deviations from Plan

None — plan executed exactly as written. One in-flight fix during Task 3: the dedup module docstring initially spelled "Weisfeiler", which the source-inspection guard `test_dedup_uses_canonical_certificate_never_wl_hash` forbids as a substring; reworded to "the non-canonical networkx graph hash" (this is the intended behavior of the guard — the forbidden-substring rule catches exactly this), so it is a normal RED→GREEN iteration, not a plan deviation.

## Deferred / Out of Scope

- `test_schema/store/screen/frontier` remain RED — the g(G)-screen certificate schema, append-only store, fail-closed verifier, and ILP-frontier measurement are waves 08-04/08-05. `det_time`/`det_nodes` are now available for 08-05's `measure_ilp_frontier`.
- No heavy sweeps run here (Mac authoring session per docs/COMPUTE.md); the slow grid is 08-06 on the remote box.

## TDD Gate Compliance

This plan is `type: tdd`. The RED gate (`test(...)` commits) landed in 08-01 (`09d2a55`, `f1b4f93`); this plan is the GREEN gate — three `feat(...)` commits turning the group/generate/structured/dedup/rng_v2 contract green. RED-before-GREEN is satisfied across the two-wave split; all target tests were confirmed RED at this plan's start and GREEN after each task.

## Self-Check: PASSED

All 4 created modules exist on disk; all 3 task commits (`cbf6d20`, `1b3476e`, `dce28a1`) present in git history; the frozen trust root (`generators/cayley.py`, `data/corpus/`, `src/alpha2/corpus/`) diff is empty.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Completed: 2026-07-23*
