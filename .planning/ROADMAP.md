# Roadmap: The α = 2 Program

## Overview

Milestone 1 rebuilds the Hadwiger α = 2 attempt as a disciplined adversary. The foundation is strictly sequential and culminates in first blood: a pinned uv-managed CPython 3.12.x environment with the Appendix C toolkit ported verbatim (Phase 1), an independently implemented trust-root verifier plus a witness-complete certificate schema (Phase 2), and the full 296-instance corpus regenerated, independently re-verified, and locked into CI (Phase 3). Only then does refactoring begin: the status-honest `ExactBackend` + CBC reference (Phase 4), then CP-SAT with the dual-backend differential gate and the had₃ escalation tier (Phase 5) — closing every soundness hole before the one tested battery CLI goes live with the author-pinned gate, profile-general search, and derived statuses (Phase 6). Pools then run certifiability-first: P0 extends the named CDM frontier past n ≤ 11 (Phase 7), the legacy seeded families scale out (Phase 8), the shared inflation operator drives P3/P6 (Phase 9), and the literature's named open cells P4/P5 are mapped and hunted (Phase 10). The escalation moat E1/E2/E3 becomes executable (Phase 11) before P7 turns the battery on itself (Phase 12). Every phase emits machine-verifiable artifacts; nothing counts as found until the independent verifier passes, and nothing counts as absent until an exact method proves it.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Pinned Environment & Verbatim Port** - uv-locked CPython 3.12.x stack; Appendix C ported byte-preserved; fingerprint test green
- [ ] **Phase 2: Trust Root & Corpus Schema** - independent stdlib-only verifier (fails closed under `python -O`); witness-complete append-only schema v1
- [ ] **Phase 3: Corpus Reproduction & CI (First Blood)** - 296/296 regenerated and independently re-verified; golden manifest frozen; verifier + reproduction run as CI on every commit
- [ ] **Phase 4: ExactBackend & CBC Reference** - status-honest exact had₂ (PROVED_OPTIMAL vs INCUMBENT_ONLY); obstruction-based encoding; seed-137 regression
- [ ] **Phase 5: CP-SAT, Differential Gate & had₃** - second engine; dual-backend agreement gates any SHC-CANDIDATE; had₃ tier proven on synthetics; assume-and-verify symmetry breaking
- [ ] **Phase 6: Kill Battery CLI (Gate, Search, Statuses)** - one tested CLI runs the 7-step runbook; author-pinned G1–G6; profile-general heuristic; derived statuses + results log
- [ ] **Phase 7: P0 — CDM Frontier** - all 1,813 MTF graphs at n=12–14 exactly adjudicated; verified CDM frontier extended past the literature's n ≤ 11
- [ ] **Phase 8: P1 & P2 — Seeded Families at Scale** - TFP critical-size sweep + showpieces toward n≈1001–2001; sum-free Cayley generalized to abelian Γ, structured vs random
- [ ] **Phase 9: P3 & P6 — Inflation Pools** - shared inflation operator; Higman–Sims complement inflations; 477,142 Ramsey(3,8,27) witnesses ingested and inflated
- [ ] **Phase 10: P4 & P5 — Literature-Frontier Pools** - generalized Kneser cells outside the pinned CLWY window; ETT crooked-graph complements under the battery
- [ ] **Phase 11: Escalation Machinery (E1/E2/E3)** - falsification harness, monotonicity audit, and survivor protocol executable before any impossibility argument is entertained
- [ ] **Phase 12: P7 — Adversarial Search** - battery-as-fitness local search over MTF space with exact-only adjudication and mandatory E3

## Phase Details

### Phase 1: Pinned Environment & Verbatim Port
**Goal**: The Appendix C toolkit runs from the repo on a pinned, reproducible interpreter, byte-identical to the historical corpus lineage — the only code changes are paths and imports.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: ENV-01, ENV-02, ENV-03, CHI-01
**Success Criteria** (what must be TRUE):
  1. `uv sync` on a clean checkout reproduces the locked environment (CPython 3.12.x exact patch, networkx 3.6.1, `pulp==3.3.2` hard-pin, ortools 9.15.6755, nauty 2.9.3, pynauty 2.8.8.1) from a committed lockfile; system Python 3.9.6 is never touched.
  2. The corpus-fingerprint test passes: regenerating n=31 seed=1 from the repo yields |E(H)|=131, ν=15, χ=16 with stored `H_edges` byte-exact against the Appendix D exemplar.
  3. The toolkit lives in a repo-relative src-layout package (no `/mnt` paths), split library + thin entry, reference algorithms unchanged — the n=31 seed=1 K₁₆ model matches Appendix D.
  4. χ(G) is computed only as n − ν(H) via Edmonds blossom (values asserted by the fingerprint test); no estimate exists anywhere in control flow.
**Plans**: 2 plans
- [x] 01-01-PLAN.md — Pinned uv env + verbatim Appendix C port (Walking Skeleton spine; invariant fingerprint green)
- [ ] 01-02-PLAN.md — Golden byte-exact fingerprint + stored-model re-verify + CHI-01 no-estimate guard

### Phase 2: Trust Root & Corpus Schema
**Goal**: An independently implemented verifier and a witness-complete certificate schema exist and are proven adversarially — before any record is ever written.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: VRF-01, VRF-02, CHI-02, ENV-05
**Success Criteria** (what must be TRUE):
  1. The verifier is stdlib-only with its own `is_conflict`, imports nothing from generator/search/solver code, consumes stored JSON only, and uses real checks (zero asserts): a `python -O` CI job proves it fails closed on a known-bad model.
  2. An adversarial mutant suite passes: the verifier refuses every mutated certificate (overlapping branch sets, H-edge pair, missing cross-adjacency, truncated family, wrong χ).
  3. Schema v1 + append-only atomic store round-trip full certificates: provenance for all three generator shapes (optional `seed` / required `params` / `graph6`), inline `H_edges` + sha256, invariants, FULL optimal families (never `fam[:χ]`), Tutte–Berge witness fields (M + U) making χ = n − ν hand-checkable both directions, verified flag, method, backend statuses + versions.
  4. The reproduction contract is encoded and documented: byte-exact (seed-derived heuristic) vs semantic (exact-method) reproduction distinguished, solver/platform versions recorded per certificate, Linux x86_64 designated the canonical reference-regeneration platform.
**Plans**: TBD

### Phase 3: Corpus Reproduction & CI (First Blood)
**Goal**: The full 296-instance corpus regenerates and independently re-verifies, and that reproduction runs as the permanent test suite — the trust anchor and regression harness for everything downstream.
**Mode:** mvp
**Depends on**: Phase 2 (Phases 1→2→3 strictly sequential; nothing downstream starts until 296/296 is green)
**Requirements**: ENV-04, ENV-06
**Success Criteria** (what must be TRUE):
  1. 296/296 regenerated and re-verified by the independent verifier from stored JSON alone (284 TFP complements n=31–501 + 12 sum-free Cayley p≤151, seed-137 included); all 27 stored certificates reproduce; seed-1 and seed-137 models byte-equal to Appendix D; every record carries its Tutte–Berge witness.
  2. The golden-hash manifest (sha256 of canonical `H_edges` per instance) is frozen and committed; the `repro/` drivers are frozen forever after.
  3. CI runs on every commit: R1 certificate validity over the full stored corpus + fingerprint test + `python -O` assert-stripping canary; R2 generator-determinism panel; R3 full pipeline replay as the release gate; a newer-Python canary catches drift on purpose.
**Plans**: TBD

### Phase 4: ExactBackend & CBC Reference
**Goal**: Exact had₂ solving lives behind a status-honest interface with CBC as the reference engine — the incumbent-as-optimum soundness hole is closed before any second engine exists.
**Mode:** mvp
**Depends on**: Phase 3 (the reproduction suite is the regression harness for this first refactor)
**Requirements**: EXACT-01, EXACT-02
**Success Criteria** (what must be TRUE):
  1. The `ExactBackend` status contract separates PROVED_OPTIMAL from INCUMBENT_ONLY: a timeout test proves a CBC incumbent can never read as an exact had₂ ("had₂ < χ from an incumbent" is unrepresentable in the battery-facing result).
  2. The CBC adapter passes the seed-137 regression — had₂ = 17, PROVED_OPTIMAL, full 17-set family extracted and independently verified — and reproduces 296-lineage exact values on the CI panel.
  3. Obstruction-based constraint generation (C₄s/cherries/H-edges of triangle-free H) replaces the O(|E_G|²) loop with an equal-count assert vs the naive loop at n=31; the structural checksum (single–single = |E(H)|, single–pair = Σ C(deg,2), pair–pair = ½ Σ C(codeg,2)) validates every model build.
  4. Decision and optimize modes both work; value and bound are always recorded with backend version.
**Plans**: TBD

### Phase 5: CP-SAT, Differential Gate & had₃
**Goal**: The complete exact-arbitration stack: a second independent engine, the cross-examination that gates every SHC-CANDIDATE, the had₃ escalation tier ready to fire same-day, and symmetry-breaking that can never contaminate an impossibility branch.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: EXACT-03, EXACT-04, EXACT-05, EXACT-06
**Success Criteria** (what must be TRUE):
  1. The CP-SAT backend agrees with CBC on every shared CI-panel instance (both PROVED_OPTIMAL, equal had₂, both families independently verified, seed-137 = 17 included); recorded claims use deterministic mode only (`num_workers=1` + pinned seed, or `interleave_search`).
  2. The differential harness makes backend disagreement release-blocking: unequal proven optima → CRITICAL, instance quarantined, batch halted; SHC-CANDIDATE is assignable only when BOTH backends prove optimality with equal had₂ < χ.
  3. had₃ works behind a flag on both backends — seagull-tier triples (⟺ ≤ 1 H-edge) first, pruned by empty common H-neighborhood, firing only on had₂ < χ — proven on synthetic size-3-forced instances; the verifier is extended to size-3 branch sets with explicit connectivity checks.
  4. Symmetry-breaking is assume-and-verify: the H=C₅ "WLOG vertex unused" disaster is a passing regression test, and every impossibility-direction run re-executes without SB.
**Plans**: TBD

### Phase 6: Kill Battery CLI (Gate, Search, Statuses)
**Goal**: One tested CLI runs the full 7-step runbook per candidate — author-pinned gate, profile-general heuristic, dual-backend exact steps, independent verification, corpus append — with derived statuses and an append-only results log.
**Mode:** mvp
**Depends on**: Phase 5 (the dual-backend SHC rule must be real from day one, never stubbed)
**Requirements**: GATE-01, GATE-02, GATE-03, SRCH-01, SRCH-02, CLI-01, CLI-02, VRF-03
**Success Criteria** (what must be TRUE):
  1. `alpha2 battery --family tfp --n 31 --seed 137` reproduces the seed-137 case study end-to-end: gate pass → exact χ=16 → heuristic miss routes onward (never a result) → both backends prove had₂=17 → verified kill appended — deterministic in (n, seed), per-step budgets, structured JSON logging.
  2. The gate runs G1–G6 as a configurable cost-ordered chain, killing on first failure with reason + witness + provenance; definitions are frozen from the author's original §2 and reconciled with the author before the gate is trusted; the criticality predicate accepts even n (the n=32 corpus row passes).
  3. The G5/G6 known-safe screen is a maintained settled/open map with citations, consulted by the gate so proven terrain is never re-hunted.
  4. The heuristic iterates non-spanning profiles (p′+s′=χ, 2p′+s′≤n) and finds the seed-137-class model the spanning profile misses; restarts-to-solution and initial-conflict instrumentation are exposed for P7 fitness.
  5. Statuses (KILLED / SHC-CANDIDATE / RESISTANT) are derived views over the immutable corpus + append-only results log — every instance's terminal state carries method + certificate reference + reason + seed/provenance, transitions never edit stored records, and RESISTANT is reachable only via exact-method timeout.
**Plans**: TBD
**Research flags**: GATE-02 requires author input (pin exact original G1–G6 §2 definitions; confirm B₇ meaning in the PST citation) — gather early, needed before the gate is trusted.

### Phase 7: P0 — CDM Frontier
**Goal**: First new science — every connected α = 2 graph at n = 12–14 is exactly adjudicated for CDM, extending the literature's verified frontier past n ≤ 11 with per-instance certificates.
**Mode:** mvp
**Depends on**: Phase 6 (battery logging + dual-backend cross-checks; CP-SAT from Phase 5)
**Requirements**: POOL-0
**Success Criteria** (what must be TRUE):
  1. The `geng -ctq | pickg -Z2` subprocess stream generates exactly 147/392/1,274 MTF graphs at n=12/13/14, with counts cross-checked against OEIS A216783 and a second generation route; provenance records (geng version, flags, shard, index, graph6) stored per instance.
  2. All 1,813 instances run the exact CDM check with the DFS reference and CP-SAT cross-check agreeing on every instance; per-instance certificates enter the corpus.
  3. The transfer lemma (maximal-triangle-free-only suffices for the whole frontier) is written up and proven in-repo.
  4. The verified CDM frontier extends past n ≤ 11 (stretch batches toward n ≤ 17 as budget allows); any CDM-less graph found is escalated immediately to the full battery and independent reproduction.
**Plans**: TBD
**Research flags**: re-derive the transfer lemma in-repo; MTF-generator cross-check options and geng res/mod tuning if throughput hurts at n=14+.

### Phase 8: P1 & P2 — Seeded Families at Scale
**Goal**: The signature TFP family and the generalized sum-free Cayley family run at scale under the battery with resistance discipline — probing the open linear-connected-matching asymptotic.
**Mode:** mvp
**Depends on**: Phase 6 (profile-general search is blocking past exact-ILP range); Phase 7 precedes by certifiability-first ordering
**Requirements**: POOL-1, POOL-2
**Success Criteria** (what must be TRUE):
  1. P1: the critical-size sweep is extended (n=31–32, many new seeds) and fully adjudicated; showpieces are pushed toward n≈1001–2001 via the heuristic + verifier engine; every kill is certificated and resistance is tracked in the derived queue.
  2. P2: the generator is generalized to arbitrary finite abelian Γ with structured (Andrásfai-interval, Green–Ruzsa-type) and random-greedy maximal sum-free sets; the structured-vs-random grid over odd |Γ| = 31–~500 runs under the battery.
  3. All new instances use RNG contract v2 (sha256 per-stage subseeds) and rebuild exactly from their stored descriptors.
  4. Zero heuristic-only claims: every reported outcome is exact-method-backed; RESISTANT instances queue for the survivor protocol.
**Plans**: TBD

### Phase 9: P3 & P6 — Inflation Pools
**Goal**: The shared inflation operator is built once and drives both open inflation families — Higman–Sims complements (the named SRG gap) and Ramsey-extremal witnesses at odd orders ≥ 31.
**Mode:** mvp
**Depends on**: Phase 6 (battery; CP-SAT stress + EXACT-06 symmetry discipline from Phase 5)
**Requirements**: POOL-3, POOL-6
**Success Criteria** (what must be TRUE):
  1. One shared inflation operator with (base-graph id, inflation vector) provenance serves both pools; inflated instances provably preserve α = 2 and pass G3 edge-maximality.
  2. P3: HS srg(100,22,0,6) is built and programmatically verified (srg parameters, triangle-freeness, vertex-transitivity); odd-order uneven inflations n ≥ 101 run exact CP-SAT with automorphism-group symmetry breaking under the assume-and-verify rule.
  3. P6: the 477,142 Ramsey(3,8,27) graphs are ingested + checksummed and verified (triangle-free, α = 7); the un-inflated 27-vertex bases are battery-run first, then stratified inflation samples at odd n ≥ 31.
  4. Every kill has a verified certificate; any had₂ < χ event hits the dual-backend gate and had₃ same-day.
**Plans**: TBD

### Phase 10: P4 & P5 — Literature-Frontier Pools
**Goal**: The 2025 literature's named open cells are mapped and hunted — generalized Kneser graphs outside the CLWY-settled window and the ETT crooked-graph complements in the thin-witness regime.
**Mode:** mvp
**Depends on**: Phase 6 (exact ω via G6; settled/open map from GATE-03 absorbs results)
**Requirements**: POOL-4, POOL-5
**Success Criteria** (what must be TRUE):
  1. P4: CLWY Theorem 3.12's exact parameter window (and intersection convention) is pinned at phase start; parameter cartography enumerates K(n,k,≥t) cells within exact/heuristic range, battery-runs out-of-window α = 2 cells prioritized by small exact ω/χ ratio, and folds settled/open results into the G5 map with citations.
  2. P5: crooked-function constructions over F_{2^m} are implemented from the ETT construction study; 𝒲₃/𝒲₅ complements are validated (triangle-free, diameter 2, K_{2,t}-free) and battery-run under heuristic + CP-SAT budgets, with remaining Eberhard 𝒲₇ primes (p ≢ 11 mod 12) included.
  3. No parameter cell is declared open without the pinned window, and no instance outcome is reported except by exact methods.
**Plans**: TBD
**Research flags**: pin CLWY Thm 3.12 window before declaring any cell open; P5 gated on reading ETT arXiv 2508.19646 construction sections (instance sizes may exceed exact-ILP range); Green–Ruzsa classification details for P2-style structured catalogs.

### Phase 11: Escalation Machinery (E1/E2/E3)
**Goal**: The epistemic moat is executable — every impossibility argument is mechanically cross-examined against the corpus, invariant claims are audited for minor-monotonicity at the door, and survivors get the full protocol before any impossibility argument is entertained.
**Mode:** mvp
**Depends on**: Phases 3, 5, 6 (corpus + scaled deterministic CP-SAT + CLI hook and RESISTANT queue); must complete before Phase 12
**Requirements**: ESC-01, ESC-02, ESC-03
**Success Criteria** (what must be TRUE):
  1. E1: the pluggable impossibility-argument interface (PROVES_IMPOSSIBLE / DECLINES / ERROR — errors never count as declines) runs against every corpus record holding a verified model; a synthetic deliberately-wrong argument is auto-REFUTED with the witness instance cited (positive control); k-level checks exercise full stored families up to had₂ > χ (seed-137's k=17).
  2. E2: the audit registry allowlists the Colin de Verdière μ family only; the random-contraction falsifier auto-rejects every banned invariant (rank, spectral gap, rigidity, minrank, χ itself) on the verified ≤5-vertex counterexamples before any corpus run.
  3. E3: the survivor protocol runner executes independent reproduction → scaled exact search (deterministic CP-SAT, long budgets, enumerated recorded seeds, SB-free impossibility branches) → independent reduction audit → second family-membership audit, wired to the RESISTANT queue.
  4. Enforced order: no argument reaches corpus evaluation without passing E2, and no impossibility claim is entertainable without surviving E1.
**Plans**: TBD

### Phase 12: P7 — Adversarial Search
**Goal**: The battery inverted — local search over MTF space hunts for battery-resistant graphs with the whole toolkit as a fitness function, exact-only adjudication, and mandatory survivor-protocol discipline.
**Mode:** mvp
**Depends on**: Phases 7, 11 (nauty canonical labels; E3 adjudication) + battery-as-library from Phase 6 — deliberately last
**Requirements**: POOL-7
**Success Criteria** (what must be TRUE):
  1. Triangle-preserving MTF flips run at n=31 with tiered battery-as-library fitness (gate depth + heuristic restarts/conflict instrumentation; exact had₂ − χ margins only at elite checkpoints).
  2. A nauty-canonical fitness cache dedups isomorphs, and full lineage provenance (parent canonical label, move, seed) makes every elite exactly rebuildable.
  3. Every resistant elite undergoes mandatory E3 adjudication before being called interesting even internally; only exact-method outcomes are ever reported; elites feed back into P1–P6 as new family seeds.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → … → 12. Phases 1→2→3 are strictly sequential (each is the safety net for the next); Phase 5 gates every path that can ever assign SHC-CANDIDATE; Phase 11 must precede Phase 12.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Pinned Environment & Verbatim Port | 1/2 | In progress | - |
| 2. Trust Root & Corpus Schema | 0/TBD | Not started | - |
| 3. Corpus Reproduction & CI (First Blood) | 0/TBD | Not started | - |
| 4. ExactBackend & CBC Reference | 0/TBD | Not started | - |
| 5. CP-SAT, Differential Gate & had₃ | 0/TBD | Not started | - |
| 6. Kill Battery CLI (Gate, Search, Statuses) | 0/TBD | Not started | - |
| 7. P0 — CDM Frontier | 0/TBD | Not started | - |
| 8. P1 & P2 — Seeded Families at Scale | 0/TBD | Not started | - |
| 9. P3 & P6 — Inflation Pools | 0/TBD | Not started | - |
| 10. P4 & P5 — Literature-Frontier Pools | 0/TBD | Not started | - |
| 11. Escalation Machinery (E1/E2/E3) | 0/TBD | Not started | - |
| 12. P7 — Adversarial Search | 0/TBD | Not started | - |

---
*Roadmap created: 2026-07-21 — 12 phases, 35/35 v1 requirements mapped (LEAN-* and deferred pool depth are milestone 2)*
