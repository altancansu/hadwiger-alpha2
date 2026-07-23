---
phase: 08-p1-p2-seeded-families-at-scale
plan: 06
subsystem: pool-sumfree
status: complete
requirements-completed: [POOL-2]
tags: [pool-2, structured-vs-random-sweep, break-hunt, g-screen, deterministic-budget, honesty-protocol, box-run, no-break, prediction-falsified, heuristic-pointer-dissolved]

# Dependency graph
requires:
  - {phase: 08, plan: 02, provides: "Abelian Γ + structured/random generators + dedup + RNG v2 + det budgets"}
  - {phase: 08, plan: 04, provides: "adjudicate_grid_point — the compact verdict row the sweep aggregates"}
  - {phase: 08, plan: 05, provides: "exact_window_max — the measured ILP-window boundary for candidate-vs-RESISTANT routing"}
provides:
  - "alpha2.pool.sumfree.sweep — grid_descriptors / run_sweep / aggregate_sweep / main (box CLI); observable bank folded in"
  - "The executed structured-vs-random g(G) sweep dataset (data/results/phase08-box-run/, byte-verified off the now-destroyed box)"
affects: [phase-11 E3 (a weak heuristic pointer is queued, not claimed), phase-9 (reuses the sweep/adjudicate machinery)]

key-files:
  created:
    - src/alpha2/pool/sumfree/sweep.py
    - tests/pool/sumfree/test_sweep.py
    - .planning/phases/08-p1-p2-seeded-families-at-scale/08-06-OBSERVABLES.md
---

# 08-06 SUMMARY — Structured-vs-random g(G) break-hunt sweep (EXECUTED)

## What shipped
`sweep.py` (grid enumeration + canonical dedup + observable bank + instance-parallel `run_sweep` +
`aggregate_sweep` + box CLI) — 9 new tests GREEN, full non-slow suite 332 passed. The canonical sweep
was then **executed on a rented 122-core x86_64 box** (private Mac↔box SSH sync; box since destroyed,
all results byte-verified onto the Mac at `data/results/phase08-box-run/`, sha256-matched).

## Results — honest headline: NO break; the LOCKED prediction is FALSIFIED in the confirmable regime

**Exact-confirmed grid (streaming, order ~31→250):** 184 rows — **109 KILLED with `g = 0.0` exactly**
(the K_χ minor packs with size-≤3 branch sets, zero slack), 74 killed-by-gate, 1 RESISTANT.
**`max g = 0.0`; zero `g>0` candidates.** Everything packs, exactly, through **k ≈ 124** (the
confirmable frontier at feasible deterministic budgets).

**Random-greedy** verified-packs (`g=0`, trust-root verified) everywhere measured, incl. heuristically
to **k ≈ 700** (HIT_PACKS in <0.2s).

**The LOCKED prediction ("the STRUCTURED family breaks first") is FALSIFIED** in every regime we can
confirm: structured sum-free Cayley graphs pack their K_χ minors right alongside random.

## The high-k heuristic pointer — surfaced, cross-examined, substantially dissolved
A numeric gap-trend (binary-search the largest heuristic minor) initially showed structured
`green_ruzsa` `g_heuristic` climbing to 0.88–0.98 at k ≥ 178 while random stayed 0.0 — the *shape* of
the author's k>100 hypothesis. **Artifact-check (n=355, k~178) dissolved it:**
- `had_h=21` was a **25 s-budget artifact** — at 120 s the heuristic finds **K₈₉**; the "0.88 gap" was
  the tight search window, not the graph.
- Residual: even at 300 s the size-≤2 heuristic can't reach K₁₇₈ on structured (random hits χ in 0.1 s)
  — a real but **modest size-≤2 limitation**, exactly what had₃ (size-3 seagulls) is expected to close.
- **`verified=False` throughout** → per the discipline, heuristic resistance is **never a result**.

**Verdict: a weak, unconfirmable heuristic pointer — queued for E3 (Phase 11), explicitly NOT a break.**
(Record: `data/results/phase08-box-run/artifact_check_n355.txt`, `gap_trend.jsonl`.)

## Compute reality (informs Phases 9–12)
Full `|Γ|=31–500` in one shot is intractable at any *confirming* budget: the gate's clique numbers
(`omega`/`kappa`) are NP-hard (~9 min/instance at n~211) and exact solves hit 20+ min at n~180. The
**confirmable frontier is k ≈ 124**; beyond it only heuristic screening (a pointer, not a verdict) is
feasible — precisely the E3 regime. Winning execution pattern: streaming work-queue + incremental
writes + tight deterministic budgets (saturated ~118 cores, kill-safe).

## Discipline check
Zero heuristic-only claims made. Every `g=0` is exact-and-verified; the one tempting "gap opens"
signal was cross-examined and held as a pointer, not reported. Trust root, frozen 296-corpus, and
determinism-sensitive generators byte-untouched. The N_MAX=500 DoS guard was **runtime-overridden only**
(never edited in committed code) for the exploratory k>1000 heuristic screen. Observable-bank honesty
protocol (pre-registered primary vs exploratory secondary; multiple-comparison count) preserved.

## Self-Check: PASSED
POOL-2 machinery delivered and the break-hunt executed; the result is a clean verified negative plus a
dissolved-under-scrutiny pointer — the modal, epistemically-honest outcome.
