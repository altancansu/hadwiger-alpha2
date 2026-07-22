# Requirements: The α = 2 Program

**Defined:** 2026-07-21
**Core Value:** Reconstruct the *attempt* under discipline — verified existence, radioactive impossibility — so the program is maximally valuable whether Hadwiger's Conjecture holds for α = 2 or fails.

> Requirement basis: `.planning/research/FEATURES.md` (TS-1…TS-10, P0–P7, E1–E3), `.planning/research/{STACK,ARCHITECTURE,PITFALLS,SUMMARY}.md`, and the pinned gate/runbook/rules in `.planning/reference/alpha2-program-source.md` (Appendix C code, Appendix E §2/§4/§5).

## v1 Requirements

Broad scope: the full program except Lean formalization (milestone 2). Each requirement is testable and maps to exactly one roadmap phase.

### Environment & Reproducibility (ENV)

- [x] **ENV-01**: The project runs on a pinned, uv-managed CPython (3.12.x) with all dependencies version-locked (networkx 3.6.1, `pulp==3.3.2` hard-pin, ortools 9.15.6755, nauty 2.9.3, pynauty 2.8.8.1); a committed lockfile reproduces the environment. *(System Python 3.9.6 is EOL and cannot run this stack.)*
- [x] **ENV-02**: The Appendix C toolkit is ported into a repo-relative Python package (no `/mnt` paths), deterministic in (n, seed), split into library + thin CLI, with the reference algorithms unchanged.
- [x] **ENV-03**: A corpus-fingerprint test asserts canonical generator invariants (n=31 seed 1 → |E(H)|=131, ν=15, χ=16) to guard byte-reproduction across environments.
- [x] **ENV-04**: The full 296-instance corpus (284 TFP complements n=31–501, 12 sum-free Cayley p≤151, seed-137) is regenerated and independently re-verified; all 27 stored certificates reproduce.
- [x] **ENV-05**: A reproduction contract distinguishes byte-exact (heuristic, seed-derived) from semantic (exact-method) reproduction and records solver/platform versions per certificate; Linux x86_64 is the canonical reference-regeneration platform.
- [x] **ENV-06**: A test suite + CI run the verifier over the stored corpus on every commit, including a `python -O` job (assert-stripping canary) and the fingerprint test.

### Gate — G1–G6 necessary-conditions filter (GATE)

- [ ] **GATE-01**: The gate runs G1–G6 as a configurable cost-ordered chain, killing on first failure and logging the reason + seed/provenance.
- [ ] **GATE-02**: The exact G1–G6 definitions are frozen from the author's original §2 (pinned in reference Appendix E), each with a witness/reason; the reconstructed vs. original labels are reconciled with the author before the gate is trusted.
- [ ] **GATE-03**: The G5/G6 known-safe-family screen is a maintained settled/open map (proven-safe classes with citations) that grows as pools and literature settle classes, so the battery never re-spends on proven terrain.

> Gate reference (Appendix E §2): **G1** n≥31, n odd, n=2χ−1 · **G2** H=Ḡ triangle-free, diameter 2 (edge-maximal) · **G3** χ≥7, κ≥χ, δ≥χ+1, G Hamiltonian, vertex-critical, H−v has perfect matching ∀v · **G4** 8≤ω≤χ−3, ω/n≲¼ · **G5** every non-adjacent pair in an induced C₅; contains W₅, K₈, all 33 Carter unavoidables · **G6** outside every proven-safe family.

### Exact chromatic number (CHI)

- [x] **CHI-01**: χ(G) = n − ν(H) is computed exactly via Edmonds blossom, with no estimates anywhere in control flow.
- [x] **CHI-02**: Each certificate stores a maximum matching M and a Tutte–Berge witness set U, making χ = n − ν hand-checkable without trusting the matching library (and without formalizing Edmonds in Lean).

### Heuristic model search (SRCH)

- [ ] **SRCH-01**: A profile-general heuristic searches for K_χ models with size-≤2 branch sets, iterating (p′, s′) profiles with p′+s′=χ and 2p′+s′≤n (the seed-137 non-spanning fix), with per-profile local-search repair + restarts.
- [ ] **SRCH-02**: The searcher exposes instrumentation (restarts-to-solution, initial-conflict counts) for P7 fitness; "not found" is emitted only as a RESISTANT queue state, never as a result.

### Exact backends & escalation (EXACT)

- [x] **EXACT-01**: An `ExactBackend` interface computes had₂(G) and extracts a model, with a status contract separating `PROVED_OPTIMAL` from `INCUMBENT_ONLY` (never reading an objective under a timeout as exact).
- [x] **EXACT-02**: A pulp/CBC backend implements `ExactBackend` as the reference solver (reproduces the 296) using obstruction-based constraint generation (enumerate C₄s/paths of triangle-free H) replacing the O(|E_G|²) loop, guarded by the structural-checksum assertion (conflict classes = H-edges / cherries Σ C(deg,2) / 4-cycles).
- [x] **EXACT-03**: An OR-Tools CP-SAT backend implements `ExactBackend` for scale, using deterministic single-worker / `interleave_search` for any recorded impossibility claim.
- [ ] **EXACT-04**: A differential harness cross-checks CBC and CP-SAT on shared instances (disagreement is release-blocking); an instance is tagged **SHC-CANDIDATE** only when BOTH backends prove optimality with equal had₂ < χ.
- [x] **EXACT-05**: Branch-set-3 (had₃) escalation is implemented behind a flag — triple variables ⟺ ≤1 H-edge (Chudnovsky–Seymour seagull tier first), pruned by empty common H-neighborhood; fires only on had₂ < χ; tested on synthetic size-3-forced instances.
- [ ] **EXACT-06**: Symmetry-breaking (for vertex-transitive candidates) is assume-and-verify: it may accelerate the existence branch, but the impossibility branch always reruns without it (the H=C₅ "WLOG vertex unused" disaster is a regression test).

### Verifier & corpus — the trust root (VRF)

- [x] **VRF-01**: An independent verifier (its own stdlib-only code path, sharing no logic with any searcher) checks disjointness, valid sizes, pairs/triples inducing connected G-subgraphs, and all C(χ,2) cross-adjacencies — using real checks, not `assert` (correct under `python -O`).
- [x] **VRF-02**: Nothing enters the corpus unverified; the append-only corpus stores full certificates (family/provenance, invariants ν/χ/ω, Tutte–Berge witness, the FULL optimal branch-set family — never `fam[:χ]`-truncated — verified flag, method, backend statuses + versions).
- [ ] **VRF-03**: Instance status (KILLED / SHC-CANDIDATE / RESISTANT) is a derived view over the immutable corpus + results log; transitions (e.g., RESISTANT → KILLED after a longer budget) never edit stored records.

### CLI & results log (CLI)

- [ ] **CLI-01**: One tested CLI runs the 7-step runbook per candidate (gate → exact χ → heuristic → had₂ → had₃ → verify → corpus append), deterministic in (n, seed), with per-step budgets and structured JSON logging; `--family` selects the pool.
- [ ] **CLI-02**: An append-only results log records every instance's terminal state with method + certificate reference + reason + seed/provenance.

### Candidate pools (POOL)

- [ ] **POOL-0**: **P0 CDM frontier** — exhaustively generate the 1,813 maximal-triangle-free graphs at n=12–14 (`geng -ctq | pickg -Z2`, cross-checked vs OEIS A216783 counts and a second generator), run an exact CDM checker (DFS reference + CP-SAT cross-check), prove the transfer lemma in-repo; extend the verified CDM frontier past the literature's n≤11 (stretch ≤17).
- [ ] **POOL-1**: **P1 TFP complements at scale** — reproduce the 296, extend the critical-size sweep (n=31–32, many seeds), push showpieces toward n≈1001–2001 (heuristic + verifier engine past ILP range), with resistance tracking.
- [ ] **POOL-2**: **P2 sum-free Cayley complements** — generalize to any finite abelian Γ, add structured generators (Andrásfai intervals, Green–Ruzsa types) alongside random-greedy; structured-vs-random grid, |Γ| odd 31–~500.
- [ ] **POOL-3**: **P3 Higman–Sims complement inflations** — build + verify HS srg(100,22,0,6), the shared inflation operator, odd-order uneven inflations (n≥101), CP-SAT exact with automorphism-group symmetry-breaking.
- [ ] **POOL-4**: **P4 generalized Kneser K(n,k,≥t)** — parameter cartography outside the CLWY-settled window (Thm 3.12; pin the exact window), exact ω + small-clique-ratio prioritization, settled/open cells folded into the G5 map.
- [ ] **POOL-5**: **P5 crooked-graph complements** — implement crooked-function constructions over F_{2^m} for ETT 𝒲₃/𝒲₅, plus remaining Eberhard 𝒲₇ primes (p≢11 mod 12); battery under heuristic + CP-SAT (ETT construction study is a phase-research task).
- [ ] **POOL-6**: **P6 Ramsey-extremal witnesses** — ingest + checksum the 477,142 Ramsey(3,8,27) graphs, verify (triangle-free, α=7), inflate to odd n≥31 via the shared operator with stratified sampling.
- [ ] **POOL-7**: **P7 adversarial local search** — battery-as-library with a nauty-canonical fitness cache, triangle-preserving MTF flips, fitness from gate depth + heuristic instrumentation (exact had₂−χ only at elites), lineage provenance, and mandatory E3 adjudication before anything is called "interesting."

### Escalation machinery — Phase 3 (ESC)

- [ ] **ESC-01**: **E1 Falsification-Rule harness** — a pluggable "impossibility argument" interface runs mechanically against the corpus and must decline on every instance holding a verified model; any argument that "proves" non-existence where a model exists is auto-rejected (includes the k-level check enabled by full-family storage).
- [ ] **ESC-02**: **E2 Monotonicity Audit** — only minor-monotone invariants (Colin de Verdière μ family, allowlisted) may back an impossibility claim; a random-contraction falsifier auto-rejects non-minor-monotone invariants (banned-invariant counterexamples all live on ≤5 vertices) before any corpus run.
- [ ] **ESC-03**: **E3 survivor protocol** — RESISTANT instances get independent reproduction → scaled exact search (CP-SAT, symmetry breaking, parallel restarts, long budgets) → second family-membership audit, before any impossibility argument is entertained.

## v2 Requirements

Deferred; tracked but not in the current roadmap.

### Formalization — milestone 2 (LEAN)

- **LEAN-01**: Lean 4 + mathlib project with local `ModelLE2` / minor definitions (mathlib has no minor theory — verified), audited for statement-vacuity (statement/proof separation, polarity/positive-and-negative controls, axiom budget in CI).
- **LEAN-02**: Per-instance certificate files — α=2 by triple-exhaustion, χ=k via explicit coloring + pigeonhole (Tutte–Berge witness), had≥k from the explicit model — making Lean the corpus's third verifier before any general claim; impossibility is never claimed from Lean.

### Deferred pool depth (POOL-v2)

- **POOL-5+**: Full ETT crooked-family study and any instances beyond comfortable exact range.
- **POOL-0+**: P0 batches at n≥18 (overnight scale) beyond the 12–17 v1 target.

## Out of Scope

Explicitly excluded — the anti-features that define the program's discipline.

| Feature | Reason |
|---------|--------|
| Non-minor-monotone "impossibility" checks (rank, Frankl–Wilson, slice rank, Haemers minrank, spectral gaps, rigidity) | Contraction destroys linear structure — none is minor-monotone; exactly the airtight-feeling-but-wrong class the original session most plausibly was. Blocked by E2; must survive the E1 corpus. |
| Reporting heuristic "resistance" as a result | Resistance is a statement about the searcher (seed-137); only exact outcomes are reported. RESISTANT is an internal queue state feeding E3. |
| Any Lean impossibility claim ("we leanproofed no minor exists") | The hard direction has no certificate to formalize; a compiling file certifies its statement, not the meta-claim. Lean does existence certificates only (milestone 2). |
| Assuming HC's truth or falsity in control flow | Outcome-symmetric by design; priors may order the work queue, never gate it. |
| Reconstructing the original lost argument | Unauditable, and its one identified candidate family is 296/296 dead. We reconstruct the disciplined *attempt*. |
| Byte-exact cross-platform / cross-interpreter heuristic replay | CPython set-iteration-dependent; guarded instead by the fingerprint test (ENV-03) + semantic reproduction + per-record version stamps (ENV-05). |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 1 | Complete |
| ENV-02 | Phase 1 | Complete |
| ENV-03 | Phase 1 | Complete |
| ENV-04 | Phase 3 | Complete |
| ENV-05 | Phase 2 | Complete |
| ENV-06 | Phase 3 | Complete |
| GATE-01 | Phase 6 | Pending |
| GATE-02 | Phase 6 | Pending |
| GATE-03 | Phase 6 | Pending |
| CHI-01 | Phase 1 | Complete |
| CHI-02 | Phase 2 | Complete |
| SRCH-01 | Phase 6 | Pending |
| SRCH-02 | Phase 6 | Pending |
| EXACT-01 | Phase 4 | Complete |
| EXACT-02 | Phase 4 | Complete |
| EXACT-03 | Phase 5 | Complete |
| EXACT-04 | Phase 5 | Pending |
| EXACT-05 | Phase 5 | Complete |
| EXACT-06 | Phase 5 | Pending |
| VRF-01 | Phase 2 | Complete |
| VRF-02 | Phase 2 | Complete |
| VRF-03 | Phase 6 | Pending |
| CLI-01 | Phase 6 | Pending |
| CLI-02 | Phase 6 | Pending |
| POOL-0 | Phase 7 | Pending |
| POOL-1 | Phase 8 | Pending |
| POOL-2 | Phase 8 | Pending |
| POOL-3 | Phase 9 | Pending |
| POOL-4 | Phase 10 | Pending |
| POOL-5 | Phase 10 | Pending |
| POOL-6 | Phase 9 | Pending |
| POOL-7 | Phase 12 | Pending |
| ESC-01 | Phase 11 | Pending |
| ESC-02 | Phase 11 | Pending |
| ESC-03 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: **35 total** (ENV 6, GATE 3, CHI 2, SRCH 2, EXACT 6, VRF 3, CLI 2, POOL 8, ESC 3)
- Mapped to phases: **35**
- Unmapped: **0** ✓

---
*Requirements defined: 2026-07-21*
*Last updated: 2026-07-21 after roadmap creation (traceability mapped: 35/35 → Phases 1–12)*
