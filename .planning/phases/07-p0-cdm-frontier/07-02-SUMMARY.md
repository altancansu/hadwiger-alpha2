---
phase: 07-p0-cdm-frontier
plan: 02
subsystem: pool/cdm
tags: [cdm, dfs, reference, cp-sat, ortools, differential, hadwiger, alpha2]

# Dependency graph
requires:
  - phase: 07-01
    provides: pool/cdm package skeleton + tests/pool/cdm RED contract (has_cdm/cdm_cpsat) + n≤11 MTF oracle
  - phase: 05-solvers
    provides: solvers/cpsat.py determinism idiom (num_workers=1 + _RANDOM_SEED=137)
  - phase: 02-corpus
    provides: corpus/verifier.py stdlib-only / raises-only / -O-safe trust-leg discipline
provides:
  - src/alpha2/pool/cdm/reference.py — has_cdm(adj,n) DFS reference (trusted, solver-free arbiter)
  - src/alpha2/pool/cdm/cpsat.py — cdm_cpsat(adj,n) CP-SAT feasibility cross-check (ortools-confined)
  - the dual CDM decision core (DFS arbiter + independent CP-SAT second engine) 07-05/07-06 gate on
affects: [07-03, 07-04, 07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CDM DFS: grow-to-cover-an-undominated-vertex search — self-pruning, terminating (depth ≤ n//2), complete by the fixed-edge domination argument"
    - "Reference/cross-check split: has_cdm imports NOTHING (not even sibling cpsat); cdm_cpsat is the sole new ortools importer"
    - "Radioactive-INFEASIBLE discipline reused verbatim: num_workers=1 + random_seed=137 on every CDM solve"

key-files:
  created:
    - src/alpha2/pool/cdm/reference.py
    - src/alpha2/pool/cdm/cpsat.py
  modified:
    - tests/pool/cdm/test_cdm_n_le_11.py

decisions:
  - "A1 vertex-edge adjacency reading (w ~ e ⟺ w adjacent to ≥1 endpoint) validated by reproducing CLWY's n≤11 all-CDM result across all 105 connected MTF-complements"
  - "Wave-1 sanity threshold corrected: exactly 105 connected instances (134 − 29 complete-bipartite complements, floor(n/2) per n), not the estimated ~130"
  - "cdm_cpsat returns only a boolean verdict (never a trusted witness); SAT witnesses are routed through verify_cdm_witness in 07-03/07-06, INFEASIBLE trusted only on DFS agreement"

# Metrics
duration: 11min
completed: 2026-07-23
---

# Phase 07 Plan 02: CDM Decision Engines Summary

**The two independent CDM deciders landed GREEN — the trusted stdlib DFS arbiter `has_cdm` (reproducing CLWY's n≤11 all-CDM result across all 105 connected MTF-complements) and the ortools-confined `cdm_cpsat` cross-check (deterministic single-worker on the radioactive INFEASIBLE direction) — and they agree on every one of the 134 n≤11 fixtures with zero disagreements.**

## Performance
- **Duration:** ~11 min
- **Completed:** 2026-07-23
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- **`has_cdm(adj, n)` DFS reference** (`pool/cdm/reference.py`): the trusted, solver-free arbiter. Private `vsets_adjacent(e,f)` (disjoint-edge V-adjacency) and `dominates(M, cover)` (A1 ≥1-endpoint reading) helpers — the CDM analog of the trust root's private `_is_conflict`, imported from nowhere. The "grow to cover an undominated vertex" DFS seeds over every G-edge then extends only by edges covering a currently-undominated target while preserving matching + pairwise V-adjacency. Returns a witness M (a<b edges) or None. stdlib-only, raises-only, `-O`-importable.
- **`cdm_cpsat(adj, n)` CP-SAT cross-check** (`pool/cdm/cpsat.py`): the ONLY new ortools importer. Boolean feasibility model — per-vertex `add_at_most_one` (matching), `sum(x) >= 1` (non-empty), pairwise `x[e]+x[f] <= 1` for disjoint non-V-adjacent edges (connected), `x[e] <= sum(inc_w)` for each w non-adjacent to both endpoints of e (dominating) — all three families built in `sorted()` order. `num_workers=1` + `random_seed=_RANDOM_SEED=137` on every solve (the LOCKED radioactive-INFEASIBLE discipline). Returns only the boolean verdict.
- **A1 definition gate GREEN** and **DFS≡CP-SAT differential GREEN** on the small fixtures; independently, DFS and CP-SAT agree on all 134 n≤11 MTF-complements (0 disagreements).

## Task Commits
1. **Task 1: has_cdm DFS reference (stdlib, trusted, -O-safe)** — `f5830b9` (feat)
2. **Task 2: cdm_cpsat CP-SAT cross-check (ortools-confined, det UNSAT)** — `e54490b` (feat)

## Files Created/Modified
- `src/alpha2/pool/cdm/reference.py` — `has_cdm` DFS decider + private definition helpers; stdlib-only trust-leg discipline.
- `src/alpha2/pool/cdm/cpsat.py` — `cdm_cpsat` CP-SAT feasibility model; sole ortools importer; deterministic single-worker seed-137.
- `tests/pool/cdm/test_cdm_n_le_11.py` — corrected the wave-1 sanity threshold from `>= 120` to `== 105` (see Deviations).

## Decisions Made
- **A1 reading validated empirically.** The tersely-stated "w adjacent to edge e" is the ≥1-endpoint reading; the only independent check that this matches CLWY's CDM is reproducing their exhaustive n≤11 result, which `has_cdm` now does across all 105 connected instances. A shared-wrong reading could not have been caught by DFS≡CP-SAT agreement alone (both engines encode the same helper), which is exactly why the definition gate is the highest-priority test.
- **Reference imports nothing.** `has_cdm` deliberately does not import the sibling `cpsat` (or any solver / graph library) so the arbiter shares no code path with the engine it checks — mirroring the trust root's isolation.
- **Boolean-only cross-check.** `cdm_cpsat` returns a verdict, never a witness; a CP-SAT SAT witness is untrusted (routed through `verify_cdm_witness` in later plans) and an INFEASIBLE is trusted only under num_workers=1 + seed AND when the exhaustive DFS agrees.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the wave-1 n≤11 gate sanity threshold**
- **Found during:** Task 1 (running `test_cdm_n_le_11.py`).
- **Issue:** The wave-1 scaffold asserted `checked >= 120` with the comment "expected ~130 connected instances". The actual count of connected MTF-complements in the frozen 134-graph oracle is **105**: exactly `floor(n/2)` graphs per n are complete-bipartite complements G = K_a ⊔ K_b (disconnected, correctly carved out by the test), summing to 1+2+2+3+3+4+4+5+5 = 29 disconnected → 134 − 29 = 105 connected. `has_cdm` returned a witness for every one of those 105; only the numeric guard (an overestimate) failed.
- **Fix:** Changed the guard to `assert checked == 105` with a comment deriving the count. The fixtures (matching OEIS A216783: 61 at n=11, etc.) and the connected/disconnected split are mathematically exact and untouched — only the guess-threshold was corrected.
- **Files modified:** `tests/pool/cdm/test_cdm_n_le_11.py`
- **Commit:** `f5830b9`

## Threat Register Compliance
- **T-7-diff (nondeterministic/wrong INFEASIBLE):** mitigated — `num_workers=1` + `random_seed=137` on every `cdm_cpsat` solve; the DFS reference is the arbiter and CDM-FAIL is never reported on CP-SAT alone (agreement enforced in 07-05).
- **T-7-03 (ortools leaking outside its confined module):** mitigated — `grep -rnE "from ortools" src/alpha2/pool/cdm/` shows the import only in `cpsat.py`; `reference.py` is stdlib-only.
- **T-7-SC (package installs):** N/A — no new packages.

## Known Stubs
None. Both engines are fully implemented and decide CDM exhaustively/independently.

## Verification Results
- `pytest tests/pool/cdm/test_cdm_n_le_11.py -x` → **2 passed** (A1 gate: all 105 connected report CDM; K_3⊔K_3 reports None).
- `pytest tests/pool/cdm/test_dfs_cpsat_agree.py -m "not slow" -x` → **2 passed** (C5 both True, K_3⊔K_3 both False).
- Independent cross-check: DFS≡CP-SAT over **all 134 n≤11 fixtures → 0 disagreements**.
- `grep -rnE "from ortools" src/alpha2/pool/cdm/` → import only in `cpsat.py`. `num_workers = 1`, `random_seed = _RANDOM_SEED`, `_RANDOM_SEED = 137` all present in `cpsat.py`.
- `reference.py`: stdlib-only grep clean, zero `assert` tokens, `python -O` imports cleanly; `cpsat.py` `-O`-importable.
- `pytest --ignore=tests/pool -m "not slow"` → **239 passed** (no regression). `git status data/corpus/ src/alpha2/corpus/` → **clean** (frozen 296-corpus + trust root byte-untouched).

## Next Phase Readiness
- 07-03 (CDM trust leg: `build_cdm_record` + `verify_cdm_witness` + append-only store) and 07-04 (`stream_mtf` generation) can build on a working DFS arbiter + CP-SAT cross-check.
- 07-05/07-06 wire these two into the release-blocking differential gate over the full 1,813-instance n=12–14 frontier; the slow `test_dfs_cpsat_agree_full_batch` (geng-gated) is ready to run once `stream_mtf` lands in 07-04.

---
*Phase: 07-p0-cdm-frontier*
*Completed: 2026-07-23*

## Self-Check: PASSED

Both created files (`reference.py`, `cpsat.py`) present on disk; both task commits (`f5830b9`, `e54490b`) present in git history.
