# The α = 2 Program

## What This Is

A disciplined, fully reproducible harness that redoes the Hadwiger **α = 2 attempt** under strict epistemic hygiene — not a reconstruction of a lost proof, but a reconstruction of the *attempt*, as a competent adversary would run it. Working in the restriction α(G) = 2 (equivalently: H = Ḡ is triangle-free), it builds an exact, certificate-emitting "kill battery" that hunts structured candidate graphs for K_χ minors, verifies every existence claim with a hand-checkable certificate, and treats every impossibility claim as radioactive until exhaustively cross-examined. It is for the author's research program on Hadwiger's Conjecture — the α = 2 case Seymour regards as the crux — and its outputs (a seeded certificate corpus, the toolkit, and datasets) bear directly on questions the current literature poses as open.

## Core Value

**Reconstruct the *attempt*, under discipline: build the adversary so that anything surviving it is a correct road to a disproof, and anything dying leaves a machine-verified result — never invent the missing hour.** The procedure is identical whether Hadwiger's Conjecture holds for α = 2 or fails, so the program is designed to be maximally valuable under both truths. When tradeoffs arise, epistemic integrity (verified existence, radioactive impossibility) wins over speed, coverage, or narrative.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current milestone scope. All are hypotheses until shipped and validated. -->

**Foundation — reproducible toolkit**

- [ ] Port the Appendix C toolkit into the repo with repo-relative paths; deterministic in (n, seed).
- [ ] Regenerate and *independently verify* the full 296-instance corpus (284 triangle-free-process complements, n = 31–501, + 12 sum-free Cayley complements, p ≤ 151); reproduce every stored certificate.
- [ ] Expose the pipeline as one tested CLI: **gate (G1–G6) → exact χ = n − ν(H) → heuristic model search → exact ILP had₂ → branch-set-3 escalation → independent verifier → corpus append.**
- [ ] Add **OR-Tools CP-SAT** as an exact backend and **nauty `geng -t`** for exhaustive generation, behind one interface; keep `pulp`/CBC as the reference solver.
- [ ] Test suite + CI: the verifier and corpus reproduction run as tests; seeds pinned; nothing rests on memory.

**The kill battery — Phase 2 runbook**

- [ ] Per-candidate procedure executing steps 1–7 in cost order, logging reason + seed on every kill, and classifying each instance KILLED / SHC-candidate / RESISTANT.

**Candidate pools — Phase 1 (P0–P7)**

- [ ] **P0 — CDM frontier:** exhaustively generate maximal triangle-free graphs on 12–14 vtx → exact connected-dominating-matching ILP; extend the verified frontier past the literature's n ≤ 11.
- [ ] **P1 — triangle-free-process complements at scale:** seeded dataset, resistance tracking, the open asymptotic (do linear connected matchings persist as n → ∞?).
- [ ] **P2 — sum-free Cayley complements:** general abelian groups, structured vs random maximal sum-free sets, larger p.
- [ ] **P3 — Higman–Sims complement inflations:** the strongly-regular case the 2025 paper could not settle.
- [ ] **P4 — generalized Kneser graphs K(n, k, ≥ t)** with small clique ratio (where the fractional-cover technique fails).
- [ ] **P5 — crooked-graph families:** Eberhard–Taranchuk–Timmons 𝒲₃, 𝒲₅ complements beyond the settled 𝒲₇ case.
- [ ] **P6 — Ramsey-extremal witnesses:** inflate maximal K₈-free graphs on 27 vtx (α = 2) to odd order ≥ 31.
- [ ] **P7 — adversarial search:** local search over edge-maximal triangle-free H (triangle-preserving flips) with the kill battery as a *fitness function*; heuristic signals only steer — exact methods alone are reported.

**Escalation — Phase 3**

- [ ] **Falsification-Rule harness:** mechanically run any proposed impossibility argument against the corpus; it must decline to prove impossibility on every instance holding a verified model.
- [ ] **Monotonicity Audit:** restrict invariant-based impossibility claims to genuinely minor-monotone invariants (Colin de Verdière μ and relatives); disqualify rank/spectral/rigidity methods at the door.
- [ ] **Survivor protocol:** independent reproduction → scaled exact search (CP-SAT, symmetry breaking, parallel restarts, long budgets) → second family-membership audit, *before* any impossibility argument is entertained.

**Deliverables**

- [ ] Seeded certificate corpus (self-contained JSON: edge lists, invariants, models, methods).
- [ ] The scripts / CLI, a running results log, and per-milestone writeups.

### Out of Scope

<!-- Explicit boundaries with reasoning, to prevent re-adding. -->

- **Lean formalization (Phase 4)** — deferred to milestone 2; the hunt toolkit must be proven first. *(Decision, not exclusion — it returns as its own milestone.)*
- **Any impossibility claim from Lean, or from non-minor-monotone invariants** (rank / Frankl–Wilson / slice rank / Haemers minrank, spectral gaps, rigidity) — disqualified by the Monotonicity Audit and the Asymmetry Principle; contraction destroys the linear structure these rely on.
- **Proving or assuming the truth of Hadwiger's Conjecture** — the program is outcome-symmetric by design; the prior leans "holds here," but that is never assumed.
- **Reporting heuristic "resistance" as a result** — resistance is a statement about the searcher until an exact method rules; only exact results are ever reported.
- **Reconstructing the original lost argument** — we reconstruct the disciplined *attempt*, not the missing hour.

## Context

**The restriction's structure.** Write H = Ḡ on n vertices. Then α(G) = 2 ⟺ H is triangle-free (with ≥ 1 edge); every color class of G is a vertex or an edge of H, so **χ(G) = n − ν(H)** (ν = maximum matching), computable exactly in polynomial time (Edmonds blossom). The chromatic half of any counterexample claim is therefore mechanical — **the entire dispute lives in the minor half.** Plummer–Stiebitz–Toft (2003): the α ≤ 2 conjecture is equivalent to every n-vertex α ≤ 2 graph containing a K_{⌈n/2⌉} minor.

**Why this restriction.** Seymour has written that if Hadwiger holds for stability number two, it is probably true in general. Hadwiger is proven for χ ≤ 6 (Robertson–Seymour–Thomas); open beyond.

**The known gap is real and large.** Duchet–Meyniel (1982) guarantees only a K_{⌈n/3⌉} minor; whether any constant above 1/3 is achievable is open (equivalent, via Thomassé / Kawarabayashi–Plummer–Toft, to linear-size *connected matchings*), with the best asymptotic bound Fox's Ω(t^{4/5} log^{1/5} t). Meanwhile Norin–Seymour (2026): every such graph has a minor on ⌈n/2⌉ vertices carrying ~98.7% of all possible edges. Read together — genuinely open, and if it fails it fails by a sliver invisible to any coarse counting, degree, or density argument. That calibrates the difficulty of the impossibility half.

**The ladder of prizes (Costa–Luu–Wood–Yip 2025): CDM ⟹ SHC ⟹ HC.** CDM = every connected α = 2 graph has a nonempty connected dominating matching; SHC (Seymour's strengthening) = the K_χ model exists with branch sets of size ≤ 2; HC = Hadwiger proper. **Certifiability runs opposite to fame:** a CDM counterexample is a single graph, finitely checkable per-instance (verified only to n ≤ 11); an SHC counterexample is *certified the moment an exact solver proves had₂(G) < χ(G)* — our ILP does exactly this; an HC counterexample needs impossibility over all models, with no known certificate. **Strategy: aim the hunt at the certifiable rungs first.**

**What "redo" means.** The original session produced an argument that no longer exists and could never be audited. Four things are known about it: it concerned α = 2 graphs, it claimed non-existence of a large clique minor, it felt airtight, and the one candidate family later identified (triangle-free-process complements) has since produced **296 / 296** instances in which the supposedly impossible minor demonstrably exists, each certificate checkable by hand. So the redo reconstructs the attempt under discipline, not the argument.

**Current status.** 296 / 296 killed across two families (284 TFP complements incl. 203 at critical sizes 31–32; 12 sum-free Cayley); 27 self-contained stored certificates, 27/27 verified; the rest verified in-run and reproducible from (n, seed). **Seed 137** is the standing lesson: the first "resistant" instance was a bug in our own profile assumption (a 177-edge, ω = 14 outlier that wanted 7 singletons where the searcher insisted on 1), dissolved by the exact ILP in one run (had₂ = 17 > 16 = χ). "Not found" is a fact about the searcher; exact methods are the arbiter.

**Tooling environment.** Python 3.9.6 is present. Web research is available via WebSearch / WebFetch / context7; the brave / firecrawl / exa MCP search providers are **not** configured in this environment, so planning research adapts to the built-in web tools.

## Constraints

- **Tech stack:** Python 3 · `networkx` (Edmonds blossom) · `pulp`/CBC (reference ILP) · **OR-Tools CP-SAT** (exact backend, added now) · **nauty `geng -t`** (exhaustive triangle-free generation, added now). Lean 4 + mathlib arrive in milestone 2.
- **The Asymmetry Principle (the central design constraint).** K_k-minor *existence* has a tiny certificate (branch sets, checkable in seconds); *non-existence* has no known certificate of any kind. All epistemic risk concentrates in the impossibility half. The machinery therefore spends existence-checking lavishly and treats every impossibility claim as radioactive. (This is also *why* a formal-verification session can feel conclusive while certifying nothing: the easy-to-formalize direction was never in doubt.)
- **The Falsification Rule.** Any proposed "no K_k minor" argument must first be mechanically executed against the certificate corpus and must decline to prove impossibility on every instance where a verified model exists. The corpus is not merely a results file — it is a falsification suite for bogus impossibility proofs, and it strengthens with every kill.
- **The Monotonicity Audit.** Invariant-based impossibility claims must use genuinely minor-monotone invariants (essentially Colin de Verdière μ and relatives). Rank methods, spectral gaps, and rigidity notions are disqualified at the door — contraction destroys linear structure. Each certificate already proves μ(G) ≥ χ(G) − 1 on its instance.
- **Reporting discipline.** Nothing counts as *found* until the independent verifier passes; nothing counts as *absent* until an exact method proves it. Heuristic resistance is never a result. The phrase "we leanproofed it" is banned; the permitted phrase is "this file compiles, and its statement says exactly X."
- **Reproducibility.** Deterministic in (n, seed); every instance seeded and rebuildable; nothing rests on memory — everything rests on seeds and code.
- **The gate.** G1–G6 run in increasing order of cost; kill on first failure; log the reason and seed.

## Key Decisions

<!-- Decisions that constrain future work. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Redo the *attempt*, not the lost proof | The original argument can't be audited; the procedure is identical whether HC is true or false | — Pending |
| Broad v1 — phase all of P0–P7 + kill battery + escalation | The whole document is the backlog; maximize certified terrain | — Pending |
| Stack: networkx + pulp/CBC (reference) + nauty + OR-Tools CP-SAT (now) | Reproduce the 296 verbatim AND get stronger exhaustive generation + exact search | — Pending |
| Lean formalization deferred to milestone 2 | Prove the toolkit first; formalize certificates once the hunt is solid | — Pending |
| Aim at certifiable rungs first (CDM, SHC) | Certifiability runs opposite to fame; a single instance + exact ILP is the proof | — Pending |
| Impossibility only via minor-monotone invariants (μ-family) | Contraction destroys rank/spectral structure; μ is the only known road | — Pending |
| Every existence claim independently verified; corpus doubles as falsification suite | The Asymmetry Principle — impossibility is radioactive until cross-examined | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-21 after initialization*
