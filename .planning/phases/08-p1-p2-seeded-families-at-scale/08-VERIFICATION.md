---
phase: 08-p1-p2-seeded-families-at-scale
verified: 2026-07-23T15:10:09Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
notes:
  - "POOL-2 remains checkbox '[ ]' / traceability 'Pending' in REQUIREMENTS.md (lines 63, 135) while 08-06-SUMMARY marks requirements-completed:[POOL-2]. Documentation-sync lag only — the code goal is achieved. Recommend flipping POOL-2 to [x]/Complete."
---

# Phase 8: P1 & P2 — Seeded Families at Scale — Verification Report

**Phase Goal:** The signature TFP family (P1) and the generalized sum-free Cayley family (P2) run at scale under the battery with resistance discipline — probing the open linear-connected-matching asymptotic.
**Verified:** 2026-07-23T15:10:09Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Goal-backward reading: the phase's contract is to RUN the break-hunt with full epistemic discipline (verified existence, radioactive impossibility, zero heuristic-only claims), not to find a counterexample. Per the program's own rule (CLAUDE.md: "nothing counts as absent until an exact method proves it; heuristic resistance is never a result"), a machine-verified NEGATIVE plus a cross-examined-and-dissolved pointer is the intended, passing modal outcome. Verification judges the machinery's existence + wiring + disciplined execution — confirmed against the codebase and the byte-verified box-run artifacts, not SUMMARY prose.

### Observable Truths

| # | Truth (Success Criterion) | Status | Evidence |
|---|---------------------------|--------|----------|
| 1 | **P1** critical-size sweep extended (n=31–32, new seeds) fully adjudicated; showpieces pushed toward n≈1001–2001 via heuristic+verifier; every kill certificated; resistance in a derived queue | ✓ VERIFIED | `p1.py`: `run_p1_tfp` (n=31–32 dual-backend exact had₂ under `differential_verdict` + frozen `verify_certificate`, deterministic in (n,seed,det_budget)); `critical_sweep` aggregates many seeds and exposes `resistant_queue` = derived E3 queue; `run_showpiece` (n≈1001–2001 existence-only: heuristic HIT→trust root→dedicated `P1_SHOWPIECE_CORPUS`, MISS→RESISTANT). `test_p1_sweep` (3) + `test_showpiece` (2) pass. |
| 2 | **P2** generator generalized to arbitrary finite abelian Γ with structured (Andrásfai-interval, Green–Ruzsa) + random-greedy maximal sum-free sets; structured-vs-random grid over odd \|Γ\|=31–~500 runs under the battery | ✓ VERIFIED | `group.Abelian` (invariant factors, N_MAX=500 guard); `generate.py` `middle_interval_sumfree`/`green_ruzsa_sumfree`/`random_maximal_symmetric_sumfree` + `cayley_adj_abelian`; `sweep.grid_descriptors` (odd cyclic 31–500 + curated non-cyclic, canonical dedup) + `run_sweep`/`aggregate_sweep`. Spot-checked: H=Cay(Γ,S) triangle-free for Z_31/53/101; Green–Ruzsa builds. Box-run executed 184 rows (structured + random). |
| 3 | All new instances use RNG contract v2 (sha256 per-stage subseeds) and rebuild exactly from stored descriptors | ✓ VERIFIED | `rng.subseed = sha256("{master}:{stage}")[:8]`, `gen_rng`/`search_rng`. Spot-check: subseeds stage-independent + stable; `adjacency_from_descriptor` rebuild **byte-identical** to live gen (never RNG replay). P1 descriptor carries `H_edges`+`H_edges_sha256`. `test_rng_v2` (5) + `test_determinism` (2) pass. |
| 4 | Zero heuristic-only claims: every reported outcome exact-method-backed; RESISTANT queues for the survivor protocol | ✓ VERIFIED | Radioactive-honesty gate enforced independently in `schema._assert_honest` AND trust-root `verifier._assert_honest` (rejects "counterexample"/"had(G) <"); confirmed fails-closed under `python -O`. Heuristic HITs always routed through `verify_certificate` OUTSIDE any truth-expression; MISS→RESISTANT; `differential_verdict` sole licenser; recorded verdicts require deterministic budgets on BOTH backends (raise otherwise). Box-run: high-k pointer surfaced, cross-examined (`artifact_check_n355.txt`: had_h=21 was a 25 s budget artifact — 120 s finds K₈₉), held as E3 pointer with `verified=False`, NOT reported as a break. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/alpha2/pool/sumfree/group.py` | Abelian Γ by invariant factors, validated + bounded | ✓ VERIFIED | 71 lines; add/neg/elements; N_MAX=500 + bool/int guards |
| `src/alpha2/pool/sumfree/generate.py` | structured + random sum-free S; abelian cayley_adj; re-check | ✓ VERIFIED | middle_interval, green_ruzsa, random-greedy; `verify_sumfree_maximal` load-bearing net; descriptor rebuild |
| `src/alpha2/pool/sumfree/rng.py` | RNG v2 sha256 per-stage subseeds | ✓ VERIFIED | subseed/gen_rng/search_rng; stage-independent + stable |
| `src/alpha2/pool/sumfree/dedup.py` | canonical-cert dedup; WL-hash forbidden | ✓ VERIFIED | pynauty `certificate`; collisions logged not dropped |
| `src/alpha2/pool/sumfree/schema.py` | g(G) cert with honesty statement + terminal_state | ✓ VERIFIED | build_gscreen_record; derives g; radioactive guard |
| `src/alpha2/pool/sumfree/verifier.py` | stdlib-only trust leg, raises-only, -O safe | ✓ VERIFIED | self-contained blossom re-derives χ=n−ν; re-verifies K_χ model; honesty gate |
| `src/alpha2/pool/sumfree/store.py` | append-only, verify-at-append, hash-chained, isolated | ✓ VERIFIED | atomic write; prefix-immutability; separate `SUMFREE_CORPUS` file |
| `src/alpha2/pool/sumfree/screen.py` | g(G) metric + had₂→had₃ tiering | ✓ VERIFIED | dual-backend det-budget; trust_root_verify_family; UnverifiedKill discipline |
| `src/alpha2/pool/sumfree/adjudicate.py` | per-instance g(G) runbook driver | ✓ VERIFIED | replicates runbook on descriptor adj (not run_candidate); KILLED-BY-GATE first-class; num_workers=1 guard |
| `src/alpha2/pool/sumfree/frontier.py` | measured ILP optimality frontier | ✓ VERIFIED | both-backend det budgets; conservative frontier_n; exact_window_max |
| `src/alpha2/pool/sumfree/sweep.py` | grid driver + aggregation + observable bank | ✓ VERIFIED | odd \|Γ\| 31–500 + non-cyclic; window-adjusted effective_state; breadth-only parallelism |
| `src/alpha2/pool/sumfree/p1.py` | P1 exact sweep + showpiece existence loop | ✓ VERIFIED | run_p1_tfp / critical_sweep / run_showpiece; RNG v2; dedicated corpus |
| `src/alpha2/paths.py` additive constants | SUMFREE_CORPUS, P1_SHOWPIECE_CORPUS, SUMFREE_SWEEP beside frozen CORPUS | ✓ VERIFIED | 4 distinct corpus files; frozen `CORPUS` untouched |

### Key Link Verification

| From | To | Via | Status |
|------|----|----|--------|
| generate.py | group.py | `Abelian.add/neg` in can_add | ✓ WIRED |
| solvers/cpsat.py | `max_deterministic_time` | `SolveParams.det_time` | ✓ WIRED (lines 217, 342) |
| solvers/cbc.py | `PULP_CBC_CMD(maxNodes=...)` | `SolveParams.det_nodes` | ✓ WIRED (lines 294, 443) |
| store.py | verifier.py | verify-at-append (`verify_gscreen`) | ✓ WIRED |
| adjudicate.py | differential.differential_verdict | dual-backend licensing (via screen) | ✓ WIRED |
| adjudicate.py | store.append_gscreen_certificate | verified cert append | ✓ WIRED |
| sweep.py | adjudicate.adjudicate_grid_point | per grid point | ✓ WIRED |
| sweep.py | frontier.exact_window_max | window routing | ✓ WIRED |
| p1.py | corpus.verifier.verify_certificate + generators.tfp.triangle_free_process | existence-only + RNG v2 | ✓ WIRED |

### Data-Flow Trace (Level 4 — is the machinery producing real data?)

| Artifact | Data | Source | Real Data | Status |
|----------|------|--------|-----------|--------|
| sweep grid (box-run) | terminal_state / g | `adjudicate_grid_point` → dual-backend exact solves | 184 sweep_rows: 109 KILLED (g=0.0 exact), 74 KILLED-BY-GATE, 1 RESISTANT; **max g = 0.0, zero g>0** | ✓ FLOWING (verified negative) |
| gap_trend / artifact_check | had_heuristic / g_heuristic | heuristic binary-search, `verified` flag | pointer surfaced then dissolved (`verified=False`); NOT reported as break | ✓ FLOWING (held as E3 pointer) |
| descriptor rebuild | H adjacency | `adjacency_from_descriptor` | byte-identical to live generation | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Result | Status |
|----------|--------|--------|
| RNG v2 subseeds stage-independent + stable | True / True | ✓ PASS |
| H=Cay(Γ,S) triangle-free (Z_31/53/101 middle-interval) | all True | ✓ PASS |
| Green–Ruzsa generates (Z_35) | \|S\|=14, verify_sumfree_maximal OK | ✓ PASS |
| Descriptor rebuild byte-identical (not RNG replay) | True | ✓ PASS |
| Abelian validation guards (N_MAX=500, bool, ≤0) | all reject | ✓ PASS |
| Honesty guard rejects "counterexample"/"had(G) <" | raises | ✓ PASS |
| Verifier fails closed under `python -O` on radioactive claim | raises VerificationError | ✓ PASS |

### Test Suite

| Scope | Result | Status |
|-------|--------|--------|
| Fast subset (group, generate, structured, dedup, rng_v2, schema, store, determinism) | 42 passed in 0.31s | ✓ PASS |
| Solver-backed subset (test_screen 8, test_frontier 2, test_p1_sweep 2) | pytest exit 0 (all passed) | ✓ PASS |
| Full sumfree suite (13 files / 62 test fns) + box-run 332-passed claim | consistent; slow n=2001 showpiece not re-timed locally | ✓ (regression-clean) |

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| POOL-1 (P1 TFP at scale) | 08-07 | ✓ SATISFIED | `p1.py` exact n=31–32 sweep + existence-only showpieces + resistance tracking; REQUIREMENTS.md marks Complete |
| POOL-2 (P2 sum-free Cayley) | 08-01..08-06 | ✓ SATISFIED (in code) | Full `pool/sumfree/*` machinery + executed structured-vs-random grid; see note below |

### Anti-Patterns Found

None. Scan of `src/alpha2/pool/sumfree/*.py` for `TBD|FIXME|XXX|PLACEHOLDER|TODO|HACK|not yet implemented|coming soon` → zero matches. No stub returns; every generator self-verifies; the verifier is raises-only (no `assert`).

### Informational Note (not a gap)

`REQUIREMENTS.md` still shows `- [ ] POOL-2` (line 63) and traceability `POOL-2 | Phase 8 | Pending` (line 135), whereas `08-06-SUMMARY.md` declares `requirements-completed: [POOL-2]` and the code goal is achieved. This is a bookkeeping-sync lag, not a code deficiency. Recommend flipping POOL-2 to `[x]` / `Complete`. Does not affect phase-goal achievement.

### Human Verification Required

None that gate this phase. The full \|Γ\|=31–500 grid was executed on a rented 122-core box (since destroyed) with results byte-verified into `data/results/phase08-box-run/`; the confirmable exact frontier is k≈124 and the full grid is intractable to re-run at confirming budgets on the author's Mac — this is the documented compute reality, not a verification gap. All machinery is locally verifiable at small scale (confirmed above), and the box artifacts are present and internally consistent with the verified-negative claim. No "break" is claimed, so the program's break→E3→human-referee gate is not triggered.

### Gaps Summary

No gaps. All four Success Criteria are observably true in the codebase: the P1 and P2 machinery exists, is substantive (no stubs), is fully wired end-to-end (generation → gate → exact χ → heuristic → dual-backend had₂/had₃ → g(G) screen → trust-root verification → append-only isolated corpus), and executed under the battery with resistance discipline. The scientific outcome — a machine-verified NEGATIVE (everything packs, g=0 exactly, through the confirmable frontier), the LOCKED "structured breaks first" prediction falsified, and a high-k heuristic pointer surfaced, cross-examined, substantially dissolved, and correctly held as an E3 pointer rather than reported as a break — is a passing, epistemically-honest result for a phase whose goal was to RUN the hunt with discipline.

---

_Verified: 2026-07-23T15:10:09Z_
_Verifier: Claude (gsd-verifier)_
