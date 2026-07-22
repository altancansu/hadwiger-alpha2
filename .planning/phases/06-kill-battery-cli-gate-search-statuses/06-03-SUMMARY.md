---
phase: 06-kill-battery-cli-gate-search-statuses
plan: 03
subsystem: search
tags: [search, heuristic, profile-general, non-spanning, seed-137, srch-01, srch-02, determinism, instrumentation]
requires:
  - search/heuristic.py (the spanning-only solve() to generalize — SELF analog)
  - generators/tfp.py (triangle_free_process — regenerate seed-137 / seed-1)
  - invariants/matching.py (nu, hence chi = n - nu)
  - verify/model.py (independent structural verifier for the test cross-check)
provides:
  - search/heuristic.py::solve (profile-general (p',s') enumeration + instrumentation return contract)
  - search/heuristic.py::initial_state_profile (non-spanning initial-state builder; holds unused vertices)
  - search/heuristic.py::PER_RESTART_ITERS (deterministic per-restart iteration cap so restarts cycle)
affects:
  - battery/pipeline.py (unchanged caller — solve() signature + return contract preserved)
  - Plan 06-04 (RESISTANT status derivation consumes the miss=sets=None contract)
  - Phase 12 P7 (restarts-to-solution + initial-conflict instrumentation consumers)
tech-stack:
  added: []
  patterns:
    - profile-general enumeration (p',s') with p'+s'=chi, 2p'+s'<=n; round-robin restarts across profiles
    - byte-exact determinism preservation — spanning profile routed to the untouched initial_state; D.2 (seed=1) reproduces verbatim
    - deterministic per-restart iteration cap (not a wall-clock slice) so a non-solving spanning restart yields control
    - miss = sets=None (a searcher fact), never RESISTANT (SRCH-02 / T-06-10)
key-files:
  created:
    - tests/test_profile_general.py
    - tests/test_heuristic_instrumentation.py
  modified:
    - src/alpha2/search/heuristic.py
decisions:
  - Spanning profile (2p'+s'==n) is profiles[0] and uses the byte-for-byte-unchanged initial_state, so seed=1 solves it on restart 1 (3 iters) and reproduces D.2 verbatim; only NON-spanning profiles use the new initial_state_profile
  - initial_state cannot hold non-spanning states (it pairs the ENTIRE pool -> forces 2p+s==n); a NEW initial_state_profile was added rather than modifying initial_state, preserving the determinism-sensitive module byte-for-byte
  - PER_RESTART_ITERS=1000 caps inner local-search iterations so round-robin actually cycles (a spanning restart on seed-137 never stalls out — moves keep resetting `stall`); deterministic count chosen above the 3-iter D.2 solve so byte-exactness is never truncated
  - The assert was removed entirely (bounded profile enumeration replaces it); chi<n/2 pool instances no longer crash (T-06-11)
metrics:
  duration: ~30min
  tasks: 2
  files: 3
  completed: 2026-07-22
requirements: [SRCH-01, SRCH-02]
---

# Phase 6 Plan 03: Profile-general heuristic — the seed-137 non-spanning fix Summary

`search/heuristic.py:solve()` was the single hard-coded **spanning** profile
(`p = n-k; s = 2*k-n; assert 2*p+s == n`) — it can represent only 15 pairs + 1 singleton
= 31 vertices at n=31,χ=16 and **empirically MISSES seed-137**, whose D.3 optimum is a
NON-spanning 9 pairs + 7 singletons = 25 vertices (6 unused), a shape the spanning data
structure cannot even hold. This plan rewrote the profile-selection head to a
**profile-general enumeration** over `(p′, s′)` with `p′ + s′ = χ` and `2p′ + s′ ≤ n`
(SRCH-01), added a non-spanning initial-state builder, and preserved the
restarts-to-solution + initial-conflict instrumentation return contract for P7 (SRCH-02).
The local-search body and the determinism-sensitive `tuple(conf)[rng.randrange(len(conf))]`
idiom are byte-for-byte untouched; the byte-exact D.2 reproduction (seed=1) and the SC1
seed-137 e2e (which must route to the exact had₂=17 kill) both stay green.

## What Was Built

**Task 1 — Wave-0 RED tests: profile-general + instrumentation** (`ecd6d55`)
- `tests/test_profile_general.py`:
  - `test_profile_general_finds_seed137_k16` (**@slow**) — regenerates seed-137
    (`triangle_free_process(31, Random(137))`, single-RNG contract v1), asserts
    `m==177`, `χ==16`, then a generous-budget `solve` FINDS a verified K16 model.
    `_assert_valid_kmodel` checks structurally: 16 branch sets, size ≤ 2, disjoint,
    every size-2 set a G-edge (`b not in adj[a]`), zero `full_conflicts` (all branch-set
    pairs adjacent in G), and an independent `verify.model.verify_model` cross-check
    (the searcher's family is UNTRUSTED — T-06-13).
  - `test_hold_nonspanning_state` — `initial_state_profile(adj, 31, 9, 7, rng)` returns
    9 pairs + 7 singletons = 25 vertices, disjoint, **6 unused**, each pair a G-edge.
  - `test_chi_below_half_n_does_not_raise` — `solve(adj, 10, 3, …)` (χ < n/2, so
    2χ−n < 0) must NOT crash (the old assert raised here — T-06-11).
  - `test_sc1_starved_budget_still_misses` — the explicit SC1 guard: `time_budget=0.0`
    still returns `sets=None`, so the pipeline routes to the exact kill.
- `tests/test_heuristic_instrumentation.py`:
  - `test_solve_returns_five_tuple_instrumentation` — a HIT returns
    `(sets, best_init, moves, restarts, elapsed)` with int/float fields (SRCH-02).
  - `test_miss_returns_none_never_resistant` — a forced miss (G empty ⇒ no K_k) returns
    `sets=None`, `moves=None`, `restarts≥1` — routed to exact, NEVER RESISTANT.

**Task 2 — profile-general `solve()` head (SRCH-01/02)** (`2552da0`)
- **`initial_state_profile(adj, n, p, s, rng, tries=500)`** — new non-spanning builder:
  stops at `p` pairs and DROPS an unpairable vertex (leaving it unused) instead of
  failing the try, so it represents `2p+s ≤ n` states. `initial_state` is untouched.
- **`solve()` head rewritten**: builds `profiles = [(p', s') for s' in range(max(0, 2*k-n), k+1)]`
  with `p' = k-s'` and `2*p' + s' <= n`; round-robins restarts across the profile list.
  The **spanning** profile (`2*p'+s' == n`) is `profiles[0]` and calls the byte-exact
  `initial_state`; non-spanning profiles call `initial_state_profile`. `best_init` is the
  first restart's initial-conflict count; `restarts` accumulates across profiles; the
  moment a profile clears all conflicts it returns. On overall timeout it returns
  `(None, best_init, None, restarts, elapsed)`. **No `assert` remains.**
- **`PER_RESTART_ITERS = 1000`** — a deterministic per-restart inner-loop iteration cap so
  round-robin actually cycles (a spanning restart on seed-137 never hits `stall > 300`
  because moves keep resetting `stall`; without a cap one restart consumes the whole
  budget and the model-holding profile is never reached). The cap is a count (not a
  wall-clock slice), chosen above the 3-iteration D.2 solve so byte-exactness is intact.

## Verification

- **Profile-general + instrumentation**: `pytest tests/test_profile_general.py
  tests/test_heuristic_instrumentation.py -x -q` → **6 passed in 4.22s** (seed-137 K16
  found as 13 pairs + 3 singletons = 29/31 verts — a non-spanning model the spanning
  profile cannot hold; hold-the-state, chi<n/2 no-raise, instrumentation, miss-contract).
- **Determinism (byte-exact D.2)**: `pytest tests/test_fingerprint.py -q` → **7 passed** —
  `test_heuristic_matches_d2_exact_pinned_env` (seed=1 reproduces `D2_MODEL` verbatim) and
  `test_heuristic_reproduces` both green. seed=1 solves the spanning profile on restart 1
  (3 iters), never touching a non-spanning profile or the iteration cap.
- **SC1 preserved**: `pytest tests/test_battery_seed137_e2e.py -q` → **1 passed in 160.79s**
  — starved heuristic budget (0.0 s) still misses → dual-backend had₂=17 → AGREED_KILL →
  `verify_certificate == 17` → terminal KILLED (corpus byte-untouched).
- **No regression**: `pytest -q -m "not slow"` → **225 passed, 8 deselected** (220 prior +
  5 new fast tests; the +1 deselected is the new @slow seed-137 find).
- **Grep acceptance**: `grep -vE "^\s*#" … | grep -c "assert "` → **0**;
  `tuple(conf)[rng.randrange(len(conf))]` present verbatim (line 166);
  `heuristic.py` contains `2 * p` (2×); 208 lines (≥ 150).

## Deviations from Plan

**1. [Rule 3 — Blocking] Added `initial_state_profile` instead of reusing `initial_state` for non-spanning profiles**
- **Found during:** Task 2 (empirical prototyping before the edit).
- **Issue:** The plan's action said "each restart calling the EXISTING
  `initial_state(adj, n, p', s', rng)`", but `initial_state` pairs the **entire** pool
  (`while pool:`) and asserts `len(pairs) == p` — it structurally forces `2p+s == n` and
  returns `None` for every non-spanning profile (empirically: all `s' ≥ 2` profiles
  returned `None` instantly). It literally cannot hold the D.3 6-unused-vertex state that
  the must-have requires.
- **Fix:** Added a NEW `initial_state_profile` (stops at `p` pairs, drops unpairable
  vertices as unused) for non-spanning profiles, while routing the spanning profile to the
  untouched `initial_state` so the byte-exact D.2 reproduction is preserved. This satisfies
  both the "HOLD the non-spanning state" must-have AND the "preserve `initial_state`
  byte-for-byte" constraint — the original function is unmodified.
- **Files modified:** `src/alpha2/search/heuristic.py`
- **Commit:** `2552da0`

**2. [Rule 3 — Blocking] Added a `PER_RESTART_ITERS` per-restart iteration cap**
- **Found during:** Task 2 (a round-robin with an unbounded inner loop did **1 restart in
  60 s** — a single spanning restart consumed the whole budget and never cycled to the
  model-holding profile, so seed-137 was never found).
- **Issue:** The plan said "running the UNCHANGED local-search body", but the spanning
  restart on seed-137 never satisfies `stall > 300` (successful moves keep resetting
  `stall`), so it never yields — breaking round-robin.
- **Fix:** Added a deterministic `iters < PER_RESTART_ITERS` (=1000) guard to the inner
  while (plus `iters` counter). It is a COUNT, not a wall-clock slice, so it is fully
  deterministic; it is set above the 3-iteration D.2 solve so byte-exactness is never
  truncated. This is the only change to the inner body; the determinism idiom and all
  energy/assignment helpers are byte-for-byte unchanged.
- **Files modified:** `src/alpha2/search/heuristic.py`
- **Commit:** `2552da0`

## Threat Model Outcomes

- **T-06-10** (false RESISTANT) — mitigated: a miss returns `sets=None`; the
  instrumentation test pins `moves=None`, `restarts≥1`; the pipeline maps `None` to the
  exact-solver edge (RESISTANT only via exact timeout).
- **T-06-11** (crash on pool instance) — mitigated: the `assert` is removed (0 asserts,
  grep-verified); `test_chi_below_half_n_does_not_raise` proves χ<n/2 does not crash.
- **T-06-12** (nondeterminism via reformat) — mitigated: the
  `tuple(conf)[rng.randrange(len(conf))]` idiom is byte-for-byte intact; `heuristic.py`
  stays ruff-excluded (no `ruff format`/`--fix` run); single-RNG threading unchanged; D.2
  reproduces verbatim.
- **T-06-13** (unverified model trusted) — mitigated: the returned family is asserted
  structurally (G-edge/disjointness) AND cross-checked by the independent
  `verify.model.verify_model`; in the pipeline it remains UNTRUSTED until
  `verify_certificate` arbitrates.

## Self-Check: PASSED

- Files: `tests/test_profile_general.py`, `tests/test_heuristic_instrumentation.py` created;
  `src/alpha2/search/heuristic.py` modified — all present on disk.
- Commits: `ecd6d55` (test), `2552da0` (feat) both present in git log.
