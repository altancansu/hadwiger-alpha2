# Feature Research

**Domain:** Exact, certificate-emitting computational search harness for Hadwiger's Conjecture restricted to α(G) = 2 (H = Ḡ triangle-free) — the "kill battery" + candidate pools P0–P7
**Researched:** 2026-07-21
**Confidence:** HIGH for the core pipeline (fully specified by the preserved Appendix C toolkit); MEDIUM-HIGH for pools (all load-bearing citations verified against Oct–Dec 2025 arXiv literature); exceptions flagged inline

## Strategic Context (why this feature set, verified)

The feature catalog is organized around the certifiability ladder **CDM ⟹ SHC ⟹ HC** (Costa–Luu–Wood–Yip, arXiv 2512.17114, Dec 2025 — verified: Theorem 2.10 establishes the implication chain; CDM computationally verified only to **n ≤ 11**; the authors note "we do not know if CDM is equivalent to SHC"). Per instance:

- A **CDM failure** is a single graph, finitely checkable (exhaustive/ILP search for a nonempty connected dominating matching).
- An **SHC failure** is certified the moment an exact solver proves had₂(G) < χ(G) — our ILP computes exactly this.
- An **HC failure** has no known certificate (impossibility over all models) — hence the Asymmetry Principle and the anti-features below.

Two December 2025 events sharpen the strategy (both verified):
1. **The Odd Hadwiger Conjecture was disproven** (Kühn–Sauermann–Steiner–Wigderson, arXiv 2512.20392: graphs with no K_t odd minor and χ ≥ (3/2 − o(1))t). A famous strengthening of HC fell. This makes hunting the *strengthened* rungs (CDM, SHC) a live, non-quixotic strategy — strengthenings can and do fail.
2. **CLWY published the exact map of settled vs. open α = 2 classes** (arXiv 2512.17114). Pools P3, P4, P5 are aimed precisely at the gaps that paper leaves open by name; P0 extends its computational frontier; P1, P2, P6, P7 cover families the paper does not touch at all (verified: the paper mentions neither the triangle-free process nor sum-free Cayley graphs).

Key structural facts the whole catalog relies on (verified against CLWY):
- χ(G) = n − ν(H), exact in polynomial time (Edmonds blossom). The chromatic half of any claim is mechanical.
- HC_{α=2} vs HC_{n/2}: any minimal counterexample to HC_{α=2} is a counterexample to HC_{n/2} (conjectures equivalent, not instance-wise). Same for SHC_{α=2} ⟺ SHC_{n/2}.
- Duchet–Meyniel: had(G) ≥ n/3 for α = 2; whether any constant above 1/3 is achievable is open, equivalent to linear-size connected matchings (best known improvement additive/sublinear — attributed to Fox in the program doc as Ω(n^{4/5} log^{1/5} n); CLWY cite Fox and Balogh–Kostochka as "incremental" improvements; the Füredi–Gyárfás–Simonovits connected-matching conjecture is still being ground out value-by-value, t ≤ 22 as of Chen–Deng arXiv 2409.05920 — confirming the linear question is genuinely open). Confidence on the exact form of Fox's bound: MEDIUM — pin the citation during P1 phase research.
- Inflations preserve α = 2 and complement-diameter (CLWY Observation 1.3), but **safety is NOT known to be inflation-closed** (CLWY Conjecture 11, open: "the behaviour of minors under inflations is not well understood"). This single open conjecture is why the inflation pools (P3, P6) are legitimate hunting grounds even over "settled" bases.

---

## Feature Landscape

### Table Stakes (the harness does not run without these)

These are Question-1 features: the core pipeline. All are specified by the preserved Appendix C toolkit and PROJECT.md; complexity is implementation effort, not research risk.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| TS-1 Gate G1–G6 (necessary-conditions filter) | Every candidate must die cheaply if trivially safe/reducible; kill-on-first-failure with reason + seed logged | MEDIUM | Cheap→expensive ordering below. **Flag:** the original G1–G6 table was not preserved byte-exact (only the toolkit + certificates survived); the table below is reconstructed from PROJECT.md constraints + the verified 2025 literature. A "freeze gate definitions" task belongs in the first phase; confirm labels with the author. |
| TS-2 Exact χ via matching | χ(G) = n − ν(H) (Gallai/PST identity); the chromatic half must be mechanical and exact | LOW | Already in `hadwiger_tfp.py` (`matching_number` via networkx `max_weight_matching`, maxcardinality). Poly-time; works to n = 501+ today. |
| TS-3 Profile-general heuristic model search | Fast first-line existence search for K_χ models with size-≤2 branch sets; most kills come from here | MEDIUM | The seed-137 lesson, concretely: current `solve()` hard-codes a **spanning** profile p = n − χ pairs + s = 2χ − n singletons (all n vertices used). Seed 137 needed a **non-spanning** profile (9 pairs + 7 singletons = 25 of 31 vertices). Fix: iterate profiles (p′, s′) with p′ + s′ = χ, 2p′ + s′ ≤ n, p′ from high to low; per-profile local search as today (3-set reassignment repair with restarts). "Not found" remains a statement about the searcher — never a result. |
| TS-4 Exact had₂ ILP (SHC decider) | The certifiable rung: had₂(G) ≥ χ(G) verified = instance killed; had₂(G) < χ(G) proven = **certified SHC counterexample** (the headline outcome) | MEDIUM | Model exists in `cayley_test.py::ilp_had2` / `investigate_137.py`: binary var per G-edge (pair branch set) + per vertex (singleton); packing constraints; conflict constraints for non-adjacent branch-set pairs. Reference backend pulp/CBC (reproduces the 296); add OR-Tools CP-SAT behind the same interface for scale. Var count ≈ \|E(G)\| ≈ n²/2 − \|E(H)\| — practical to n ≈ 100–150 with CBC, further with CP-SAT. |
| TS-5 Branch-set-3 escalation (had₃) | If had₂ < χ, SHC fails on the instance but HC is undecided; must escalate to size-≤3 branch sets before any claim about HC on the instance | HIGH | Fires only on had₂ < χ (has never fired: 296/296 killed at ≤2). Variables per connected ≤3-subset of G (O(n³) triples); connectivity + pairwise-adjacency constraints; CP-SAT territory. Design now, implement behind a flag; test on synthetic instances where size-3 is forced. |
| TS-6 Independent verifier | Nothing counts as found until an independent check passes: disjointness, pairs/triples induce connected G-subgraphs, all C(χ,2) cross-adjacencies | LOW | Exists (`verify_model`) for sizes 1–2; extend to size 3 (connectivity check). Must stay a separate code path from every searcher (no shared model-building logic). Runs in CI on the stored corpus. |
| TS-7 Seeded certificate corpus + reproduction | The corpus is both the results archive and the falsification suite for future impossibility claims; must be regenerable from (n, seed) exactly | MEDIUM | JSON schema exists (family, n/p, seed, H_edges or generator params, invariants ν/χ/ω, model_branch_sets, verified, method, had2_exact). Port to repo-relative path. Milestone gate: regenerate + re-verify all 296 (284 TFP n = 31–501, 12 Cayley p ≤ 151), reproduce the 27 stored certificates byte-equivalently, seed 137 included. |
| TS-8 Results log + classification | Every instance ends in exactly one state: KILLED (with method + certificate) / SHC-candidate (had₂ < χ proven) / RESISTANT (heuristic exhausted, exact pending) — with reason + seed | LOW | Append-only log; RESISTANT is an internal work-queue state, never a reported result (see anti-features). |
| TS-9 One tested CLI (7-step runbook) | Single entry point per candidate: gate → exact χ → heuristic search → exact had₂ ILP → branch-3 escalation → verifier → corpus append | MEDIUM | Deterministic in (n, seed); per-step cost budgets; `--family` selects the pool constructor; every step logs structured JSON. The four existing scripts (`hadwiger_tfp.py`, `sweep.py`, `cayley_test.py`, `investigate_137.py`) become library + thin CLI. |
| TS-10 Backend abstraction (CBC reference + CP-SAT) and nauty integration | Reproducing the 296 verbatim requires CBC; scaling P0/P3/P5 and had₃ requires CP-SAT; P0/P7 require exhaustive generation + canonical dedup | MEDIUM | One `ExactBackend` interface, CBC as the reference solver (never removed), CP-SAT as the scale solver; disagreement between backends on any instance = release-blocking bug (free cross-validation). nauty: `geng -t` for triangle-free generation, canonical labels for isomorph rejection. |

**TS-1 gate detail — reconstructed G1–G6 in cheap→expensive order** (each check either kills with a logged reason or passes; confirm exact labels against the author's original table):

| # | Check | Kill reason | Cost | Basis (verified) |
|---|-------|-------------|------|------------------|
| G1 | H triangle-free AND has ≥ 1 edge | "out of α = 2 regime" | O(n·m) bitset | Definition of the restriction |
| G2 | G connected; H connected | "G disconnected → two cliques, trivially safe" / "H disconnected → G is a join, reducible by induction" | O(n + m) | Standard reductions; minimal counterexamples are joins of nothing |
| G3 | H edge-maximal triangle-free (⟺ diameter 2, n ≥ 3) | "not edge-maximal — dominated by a harder candidate" (or normalize: complete H to a maximal extension, log both) | O(n²·Δ) bitset | CLWY Lemma 2.5 equivalences; TFP outputs are automatically maximal |
| G4 | G has a dominating edge (N(x) ∪ N(y) = V) | "dominating edge — CDM of size 1 exists; instance reducible" | O(m_G·n) bitset | A dominating edge is exactly a nonempty CDM of size 1 (CLWY definitions); contraction of a dominating edge yields a universal vertex — PST-style induction |
| G5 | Known-safe family screens: girth(H) ≥ 5; base-graph iso match or inflation-of-settled-base detection (modular decomposition + nauty canon vs. list: Clebsch, Mesner, Gewirtz complements and their inflations; triangle-free Kneser inflations in the settled window; Eberhard graphs p ≡ 11 (mod 12); B₇-free per PST) | "in proven-safe class (cite)" | O(n·m) girth; O(n + m) modular decomposition; iso vs. small list cheap | CLWY §3.1–3.4 (verified); PST B₇-free theorem as cited by CLWY [53] — **flag: confirm what B₇ denotes at phase time** |
| G6 | Cheap-invariant trivial wins: compute ν(H) → χ; if χ ≤ 6 kill (Robertson–Seymour–Thomas); compute ω(G) = α(H) (exact, small n); if ω ≥ χ kill ("K_χ is a subgraph") | "χ ≤ 6 (RST)" / "ω ≥ χ trivial" | Blossom O(n³-ish); exact ω exponential but trivial at n ≤ a few hundred | RST 1993 for t ≤ 6; ν computed here is reused by runbook step 2 for free |

### Differentiators (the features that generate the program's value)

Two groups: the candidate pools P0–P7 (Question 2 — each gets a deep-dive section below) and the Phase-3 escalation machinery.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| P0 CDM frontier extension | Extends the literature's exhaustively-verified CDM frontier past n ≤ 11 (CLWY's own stated computational limit) — publishable terrain for ~1,800 ILP/DFS runs | LOW-MEDIUM | Only 147 + 392 + 1,274 = 1,813 maximal triangle-free graphs at n = 12–14 (OEIS A216783, verified); stretch to n ≤ 17 adds ~195k graphs, still cheap |
| P1 TFP complements at scale | The one family known to have killed the original "impossibility" 296/296; scaling probes the open linear-connected-matching asymptotic empirically | MEDIUM | Generator + 296-corpus exist; scale is heuristic+verifier-bound (ILP infeasible past n ≈ 150–200) |
| P2 Sum-free Cayley complements, generalized | Algebraic/pseudorandom counterpoint to P1; structured vs random maximal sum-free sets across general abelian groups is untouched by the literature | MEDIUM | Z_p code exists; generalize group ops + structured catalogs (Green–Ruzsa types, Andrásfai-type intervals) |
| P3 Higman–Sims complement inflations | The named strongly-regular gap: CLWY settled Clebsch/Mesner/Gewirtz for ALL inflations but Higman–Sims only for the base graph (SHC_{n/2}, Thm 3.18); its inflations are open, and inflation-closure (Conj 11) is open | MEDIUM-HIGH | n = 100 base; odd-order uneven inflations from n = 101 up; CP-SAT required for exact work |
| P4 Generalized Kneser K(n, k, ≥ t), small clique ratio | CLWY's fractional-cover technique proves CDM only inside a parameter window (≈ 2k − t ≤ n < (5/2)(k − t)); outside it, with H still triangle-free, nothing is known | MEDIUM | Constructor trivial; the work is parameter search + exact runs at C(n,k) ≤ ~500 |
| P5 Crooked-graph complements (ETT 𝒲₃, 𝒲₅) | ETT (arXiv 2508.19646) proved 𝒲₃, 𝒲₅ infinite via crooked graphs (de Caen–Mathon–Moorhouse); CLWY settled only the 𝒲₇ Cayley "Eberhard graphs" (p ≡ 11 mod 12); crooked complements are open and are the extreme locally-sparse regime for size-≤2 models | HIGH | Requires implementing crooked-function graph constructions over F_{2^m}; instance sizes likely push past exact-ILP range |
| P6 Ramsey-extremal witness inflations | The 477,142 Ramsey(3,8,27) graphs (Brinkmann–Goedgebeur 2012, downloadable) are the minimum-clique-material α = 2 graphs (ω = 7, χ ≥ 14 at n = 27); odd-order inflations ≥ 31 are structured counterpoints to TFP at identical sizes where the battery is already proven fast | LOW-MEDIUM | Data exists; inflation operator + sampling policy is the only new code |
| P7 Adversarial local search | Turns the kill battery from a checker into an optimizer: search edge-maximal triangle-free H-space for battery-resistant graphs; the only pool that can *find* what the structured pools miss | MEDIUM-HIGH | Needs battery-as-library, fitness caching, canonical dedup, and hard Goodhart discipline (exact adjudication before any claim) |
| E1 Falsification-Rule harness | Any proposed impossibility argument runs mechanically against the corpus and must decline to prove impossibility on every instance holding a verified model; the corpus strengthens with every kill | MEDIUM | Phase 3; requires corpus + a pluggable "argument" interface |
| E2 Monotonicity Audit | Gatekeeper for invariant-based impossibility claims: only genuinely minor-monotone invariants (Colin de Verdière μ family) admitted; each certificate already witnesses μ(G) ≥ χ(G) − 1 on its instance | LOW-MEDIUM | Phase 3; a checklist + a small μ-relatives allowlist encoded in the harness |
| E3 Survivor protocol | RESISTANT instances get: independent reproduction → scaled exact search (CP-SAT, symmetry breaking, parallel restarts, long budgets) → second family-membership audit — before any impossibility argument is entertained | MEDIUM | Phase 3; consumes TS-10 backends; seed-137 institutionalized |

### Anti-Features (deliberately NOT built — Question 3)

| Feature | Why Requested (surface appeal) | Why Problematic (actual) | Alternative |
|---------|-------------------------------|--------------------------|-------------|
| Non-minor-monotone "impossibility" checks: rank arguments, Frankl–Wilson, slice rank, Haemers minrank, spectral gaps, rigidity | These tools kill existence questions in extremal combinatorics and feel like power; a "no K_χ minor because rank" module would seem to complete the battery | Contraction destroys linear structure: none of these invariants is minor-monotone, so a "proof" built on them says nothing about minors. This is exactly the class of airtight-feeling wrong argument the original lost session most plausibly was. The corpus already holds 296 verified models any such argument must survive — and would not | Monotonicity Audit (E2): impossibility only via the Colin de Verdière μ family; every proposed argument first runs through the Falsification-Rule harness (E1) against the corpus |
| Reporting heuristic "resistance" as a result | After a large sweep, "n graphs resisted the searcher" reads like a finding and is publishable-shaped | Resistance is a statement about the searcher, not the graph. Seed 137 is the canonical case: 300s of restarts "resistant," dissolved by one exact ILP run (had₂ = 17 > 16 = χ) — the searcher's spanning-profile assumption was the bug | RESISTANT is an internal queue state (TS-8) feeding the survivor protocol (E3); only exact-method outcomes are ever reported |
| Any Lean impossibility claim ("we leanproofed that no minor exists") | Formal verification feels like the ultimate rigor; a compiling file is emotionally conclusive | The easy-to-formalize direction (existence certificates) was never in doubt; the hard direction (impossibility over all models) has no known certificate to formalize. A compiling Lean file certifies its statement, not the meta-claim. Lean itself is deferred to milestone 2 for certificate checking only | Permitted phrase: "this file compiles, and its statement says exactly X." Milestone 2 formalizes *existence* certificates (verifier semantics), never impossibility |
| Assuming HC's truth (or falsity) anywhere in control flow | A prior ("Seymour thinks it holds") could prune "hopeless" searches and save compute | The program is outcome-symmetric by design; both truths make the outputs valuable (kills → verified corpus + falsification suite; a survivor → a certified SHC/CDM counterexample). Any asymmetric shortcut poisons both | The battery's procedure is identical under both truths; priors may order the work queue, never gate it |
| Reconstructing the original lost argument | Narrative closure; "find the missing hour" | The argument cannot be audited and its one identified candidate family is now 296/296 dead; reconstruction would be motivated reasoning at scale | Reconstruct the disciplined *attempt* (this program); let the corpus adjudicate any future impossibility idea mechanically |

---

## Candidate Pool Deep-Dives (Question 2)

Each pool: what it is, concrete construction, why it is open/interesting, complexity, and dependencies. All pools consume the full kill battery (TS-1..TS-10) and emit into the same corpus/log.

### P0 — CDM frontier (exhaustive maximal triangle-free, n = 12–14, stretch ≤ 17)

- **What:** Exhaustively test the CDM conjecture ("every connected α = 2 graph has a nonempty connected dominating matching," CLWY Conjecture 10) beyond the literature's computational frontier. CLWY state verification for **all graphs up to 11 vertices** (verified quote). P0 extends to 12–14 via the maximal-triangle-free reduction.
- **Construction:**
  1. Generate all maximal triangle-free (MTF) graphs H on n = 12, 13, 14: counts are **147, 392, 1,274** (OEIS A216783, verified by direct fetch). Two independent generation routes for cross-validation: (a) nauty `geng -t` (all triangle-free) piped through an edge-maximality filter; (b) the Brandt–Brinkmann–Harmuth MTF generator / House of Graphs "maximal triangle-free" collection as an external cross-check of counts.
  2. Discard complete bipartite H (complement disconnected — conjecture scoped to connected G; these correspond to the trivially-safe two-cliques case).
  3. For each G = H̄: exact search for a nonempty connected dominating matching. At n ≤ 14 an exhaustive DFS over matchings with domination + connectivity pruning is simpler and likely faster than ILP; implement both (DFS as reference, CP-SAT/ILP as cross-check — connectivity needs lazy cuts or flow encoding in the ILP).
  4. **Prove the transfer lemma in-repo** (small but load-bearing): a CDM is preserved under adding G-edges (matching stays a matching; domination and connectivity are monotone), so CDM verified on complements of all non-complete-bipartite MTF graphs on n vertices, plus the trivial two-cliques-with-a-cross-edge case, covers all connected α = 2 graphs on n vertices. This is why 1,813 graphs suffice instead of all ~470M triangle-free graphs at n = 14.
  5. Any CDM-less graph found = a **CDM counterexample candidate**: immediately escalate to the full battery (it may still satisfy SHC/HC — had₂ ILP decides the next rung) and to independent reproduction.
- **Why open/interesting:** The first rung of the ladder, verified only to n ≤ 11; a counterexample here is a single finite graph and would be the cheapest certified result the program can produce. Even all-kills extend the certified frontier past the named literature bound — immediate, publishable, and every instance strengthens the falsification suite.
- **Complexity:** LOW-MEDIUM. 1,813 graphs, sub-second exact checks each. Stretch: n = 15 (5,036), 16 (25,617), 17 (164,796) remain trivial totals; n = 18 (1,337,848) is an overnight batch. Promise 12–14, stretch 15–17.
- **Depends on:** nauty integration (TS-10), CDM exact checker (new — distinct objective from the had₂ ILP), transfer lemma writeup, corpus schema extension (family = `mtf_exhaustive`, store canonical labels instead of seeds).

### P1 — Triangle-free-process complements at scale

- **What:** The seeded Bohman triangle-free-process family — the pool that produced the original 296/296 kills — regenerated, re-verified, and pushed to larger n with resistance tracking.
- **Construction:** Exists verbatim (`triangle_free_process(n, rng)`: uniform random open-pair insertion until no open pairs; output is automatically edge-maximal triangle-free). Deterministic in (n, seed). Scale plan: reproduce the 296 (n = 31–501); extend the sweep grid at the critical sizes (n = 31–32, many seeds) and push showpieces to n ≈ 1001–2001. Memory for the open-pair set is O(n²) (~2M pairs at n = 2001 — fine); blossom matching at n = 2001 is minutes; the heuristic (profile-general, TS-3) plus verifier is the only realistic existence engine past n ≈ 150–200 (the had₂ ILP has ~n²/2 binaries — reserve exact runs for small-to-mid n and for any resistant instance at a size CP-SAT can still reach).
- **Why open/interesting:** TFP complements are the hardest known generic regime: ω(G) = α(H) = Θ(√(n log n)) (Bohman–Keevash / Fiz Pontiveros–Griffiths–Morris analyses of the process — the R(3,k) machinery) while χ(G) ≈ n/2, so the clique-to-chromatic ratio → 0. The open asymptotic the pool probes: do linear-size connected matchings (equivalently size-≤2 models hitting χ) persist as n → ∞? Verified models at n = 501 say yes empirically; theory guarantees only n/3 + lower-order (see Strategic Context). CLWY's paper does not touch random families at all (verified) — this pool is the program's own turf, plus it is the falsification suite's backbone.
- **Complexity:** MEDIUM. Generator and corpus exist; the work is scale-out (budget scheduling, parallel seeds, resistance queue) and the TS-3 profile generalization, which becomes mandatory at sizes where no ILP can adjudicate.
- **Depends on:** TS-3 (profile-general search — blocking for large n), TS-7 corpus reproduction (milestone gate), TS-10 CP-SAT (mid-size resistant instances), E3 survivor protocol (resistance handling).

### P2 — Sum-free Cayley complements (general abelian groups)

- **What:** H = Cay(Γ, S) for S a maximal symmetric sum-free set in a finite abelian group Γ (sum-free ⟹ triangle-free; symmetric ⟹ undirected; maximal sum-free ⟹ edge-maximal triangle-free among Cayley graphs — re-verify per instance with the G3 check). Existing corpus: Z_p, p ∈ {31, 53, 101, 151}, random maximal S, 12/12 killed.
- **Construction:**
  1. Generalize the existing `random_maximal_symmetric_sumfree` from Z_p to any abelian Γ given as a direct-product of cyclic groups (replace mod-p arithmetic with componentwise group ops; `can_add` logic is identical: reject a if (S ∪ {a, −a}) violates sum-freeness).
  2. Add **structured** generators alongside random-greedy: middle-third intervals in Z_n (S = {⌈n/3⌉..⌊2n/3⌋-ish} — the Andrásfai-type vertex-transitive triangle-free graphs); largest sum-free sets per the Green–Ruzsa classification of abelian groups (type I/II/III by which prime divisors ≡ 1 or 2 mod 3 divide |Γ|); Z_2^k cosets and the classified maximal sum-free sets there; Z_3^k caps. (Structured catalogs from training knowledge — MEDIUM confidence on classification details; pin Green–Ruzsa specifics during phase research.)
  3. Grid: group type × structured/random × |Γ| odd, 31 ≤ |Γ| ≤ ~500; several seeds per random cell. Everything deterministic in (Γ spec, seed).
- **Why open/interesting:** Algebraic, vertex-transitive, blow-up-adjacent structure — maximum contrast with P1's randomness at identical sizes. Vertex-transitivity means ν(H) is near-perfect (χ = ⌈n/2⌉ typically) and symmetry both helps (CP-SAT symmetry breaking) and hurts (structured obstructions could exist that random graphs never show). Untouched by CLWY (verified). Structured-vs-random within one family isolates whether algebraic structure ever *creates* resistance.
- **Complexity:** MEDIUM. Small generalization of existing code; the exact ILP works to |Γ| ≈ 150 with CBC (already demonstrated at p = 151), further with CP-SAT.
- **Depends on:** TS-4/TS-10 backends; group-spec plumbing in the CLI and corpus schema (store Γ spec + S explicitly).

### P3 — Higman–Sims complement inflations

- **What:** G = inflations of the complement of the Higman–Sims graph (HS: srg(100, 22, 0, 6), λ = 0 ⟹ triangle-free; the complement has α = 2, n = 100, ν = 50, χ = 50).
- **Construction:**
  1. Build HS from a standard construction (Steiner system S(3, 6, 22) / M₂₂-based, or a vetted edge list, e.g., from a published dataset); verify srg parameters, triangle-freeness, and vertex-transitivity programmatically before use.
  2. Inflation operator (new, shared with P6): replace vertex v of G by a clique of size k_v, join cliques completely iff originals adjacent. Complement-side view: H-side becomes the blow-up HS[k] (independent sets per vertex) — automatically triangle-free, and (since HS has λ = 0, μ = 6 and every vertex has neighbors) the blow-up stays edge-maximal triangle-free, so instances pass G3. Target odd orders: uneven inflation vectors (e.g., one vertex ×2 → n = 101; sampled uneven vectors → 101–301).
  3. Battery per instance. Exact χ is cheap at any size. had₂ ILP at n = 101: ~3,900 pair-vars (G-edges ≈ 5,050 − 4,400-ish blow-up count depending on vector) — CBC-hard, CP-SAT-feasible; n = 200 (uniform ×2): ~15,500 pair-vars — CP-SAT with tuned conflict encoding, long budgets, symmetry breaking on the HS automorphism group (order 88,704,000 in the base — huge symmetry to exploit).
- **Why open/interesting:** The named gap: CLWY settled Clebsch, Mesner, Gewirtz complements **for all inflations** (Lemmas 3.14–3.17) but Higman–Sims only for the base graph, and only at the SHC_{n/2} level (Theorem 3.18); nothing is known for its inflations, and inflation-closure of any of these conjectures is itself open (Conjecture 11 — verified quotes). HS is the largest and most rigid triangle-free strongly regular graph; if algebraic rigidity ever obstructs size-≤2 models, this is the flagship place.
- **Complexity:** MEDIUM-HIGH. Construction + verification LOW; exact search at n ≥ 100 is the first real CP-SAT stress test; symmetry-breaking work is genuinely new engineering.
- **Depends on:** TS-10 CP-SAT (blocking for exact runs), inflation operator (shared with P6), TS-3 profile-general heuristic (first line at n = 200+), G5 screen updated so the *base* HS complement (settled, SHC_{n/2}) is not re-hunted while its inflations are.

### P4 — Generalized Kneser graphs K(n, k, ≥ t) with small clique ratio

- **What:** G with vertices = k-subsets of [n], adjacent iff |A ∩ B| ≥ t (so H is the "small-intersection" graph); α(G) = 2 ⟺ no three k-sets pairwise intersect in < t points. Classical triangle-free Kneser complements (t = 1 side) are settled by CLWY for the window 2k ≤ n ≤ 3k − 1 (Lemmas 3.6–3.7, all inflations); generalized K(n, k, ≥ t) settled (CDM, hence everything) only for ≈ 2k − t ≤ n < (5/2)(k − t) (Theorem 3.12).
- **Construction:**
  1. Constructor is trivial (itertools over C(n,k) subsets + intersection sizes); exactness of the α = 2 condition is re-checked by gate G1 rather than trusted from parameters.
  2. Parameter sweep: enumerate (n, k, t) with C(n,k) ≤ ~500 (exact-ILP range) and C(n,k) ≤ ~2,000 (heuristic range); keep instances that pass G1 (H triangle-free) and fall **outside** the CLWY-settled window; prioritize small clique ratio ω(G)/χ(G) (compute both exactly — ω via exact clique on these sizes) since small-clique-material instances are where the fractional-cover technique has no purchase.
  3. **Flag (MEDIUM confidence):** two reads of the paper produced slightly different window forms ("2k − t ≤ n" vs "2k ≤ n" < (5/2)(k − t)); pin the exact Theorem 3.12 statement and the paper's intersection convention at phase start before declaring any parameter cell "open."
- **Why open/interesting:** CLWY explicitly lists the out-of-window generalized Kneser range among their open cases (verified). These are the natural "designed" small-clique-ratio family — the structured analogue of what TFP achieves randomly — and each settled cell is a clean, citable increment.
- **Complexity:** MEDIUM. No new algorithmic machinery; the work is parameter cartography + exact runs + a careful settled/open map maintained against the paper.
- **Depends on:** TS-4/TS-10; exact ω computation in G6; the G5 screen encoding the settled window (so settled cells are killed at the gate with the citation, not re-proven).

### P5 — Crooked-graph families (ETT 𝒲₃, 𝒲₅ complements)

- **What:** Complements of the Eberhard–Taranchuk–Timmons families in 𝒲_t = {non-star graphs of diameter 2, triangle-free, K_{2,t}-free}. Verified from arXiv 2508.19646: Hoffman–Singleton ⟹ 𝒲₂ finite; Wood conjectured all 𝒲_t finite; ETT disproved this — 𝒲₃ is infinite and 𝒲₅ contains infinitely many regular graphs, **both via crooked graphs** (first constructed by de Caen–Mathon–Moorhouse); 𝒲₇ contains infinitely many Cayley graphs on F_p², p ≡ 11 (mod 12). CLWY settled exactly those 𝒲₇ Cayley "Eberhard graphs" (Theorem 3.21, SHC_{α=2}) and list other primes as open; the crooked 𝒲₃/𝒲₅ complements appear in no settled list.
- **Construction:**
  1. Implement crooked-function graphs over F_{2^m}: crooked functions (e.g., Gold-type x^{2^k+1} with gcd(k, m) = 1, m odd) and the de Caen–Mathon–Moorhouse graph construction from them; then the ETT modifications giving the 𝒲₃ and 𝒲₅ members. **This requires reading the ETT paper's construction sections at phase time** — exact vertex counts per member were not verified in this research pass (expect powers of 2, plausibly ≥ 2^{2m}-scale, i.e., the smallest members may already exceed comfortable exact-ILP size). LOW-MEDIUM confidence on instance sizes; the construction's existence and status is HIGH.
  2. Programmatic validation per instance: triangle-free, diameter 2 (⟹ passes G3), K_{2,t}-freeness as a family sanity check.
  3. Battery; expect heuristic + CP-SAT-with-budgets as the workhorses if sizes are large; secondary target from CLWY's own open list: Eberhard 𝒲₇ Cayley graphs at primes p ≢ 11 (mod 12) (constructor is elementary — F_p² Cayley — and sizes p² may be large but the construction cost is trivial).
- **Why open/interesting:** K_{2,t}-free + diameter 2 is the **thin-witness regime**: every non-adjacent pair has ≥ 1 but ≤ t − 1 common neighbors, so pair branch sets have minimal attachment options — the structurally hardest environment for size-≤2 models, and the newest named family (Aug 2025) with genuinely infinite supply. A kill here is evidence SHC survives even at the sparsest witness structure; resistance here would be the most interesting signal the program could produce.
- **Complexity:** HIGH. Finite-field constructions from a fresh paper, likely large instances, and the heaviest reliance on CP-SAT tuning and the profile-general heuristic.
- **Depends on:** TS-3, TS-10 (both blocking); ETT paper study task (phase research); G5 screen encoding the settled 𝒲₇/p ≡ 11 case.

### P6 — Ramsey-extremal witnesses (inflate (3,8,27) graphs to odd order ≥ 31)

- **What:** The 477,142 Ramsey(3, 8, 27) graphs — triangle-free H on 27 vertices with α(H) ≤ 7 (McKay–Zhang 1992: R(3,8) = 28; full enumeration Brinkmann–Goedgebeur 2012; downloadable from McKay's Ramsey data page — all counts verified). Since R(3,7) = 23 ≤ 27, every such H has α(H) = 7 exactly, so G = H̄ has n = 27, α = 2, **ω(G) = 7**, χ(G) = 27 − ν(H) ≥ 14. Inflate G to odd orders ≥ 31.
- **Construction:**
  1. Download + checksum the (3,8,27) archive; parse graph6; verify per graph: triangle-free, α = 7 (spot-check exhaustively on samples, fully if cheap).
  2. Reuse the P3 inflation operator with uneven vectors to hit odd n ∈ {31, 33, ...} (e.g., inflate 4 of 27 vertices ×2 → 31). Instances pass G3 iff the base H is edge-maximal — filter or note (not all 477k are MTF; the gate decides, and non-maximal bases can be completed to maximal with the normalization logged).
  3. Sampling policy over the 477k × inflation-vector product space: stratify by ν(H), |E(H)|, automorphism group size; exhaustive over the un-inflated 27-vertex bases first (cheap: battery at n = 27 is faster than the proven n = 31 runs), then sampled inflations at 31–55.
- **Why open/interesting:** These are the extremal minimum-clique-material α = 2 graphs — ω/χ ≤ 1/2 at the base, the worst ratio finite structures achieve, exactly the regime where clique-seeded intuitions fail and where the fractional/counting techniques have nothing to grip. They are structured (Ramsey-extremal, often high-symmetry) counterpoints to TFP at the very sizes (31+) where the battery is proven fast, and inflation-openness (Conjecture 11) applies here too. No overlap with any settled CLWY class (verified — their strongly-regular list is Clebsch/Mesner/Gewirtz/HS).
- **Complexity:** LOW-MEDIUM. All data exists; new code is the sampling policy + graph6 ingestion; battery cost per instance is the already-demonstrated n = 31-class cost (seconds heuristic, minutes ILP).
- **Depends on:** Inflation operator (shared with P3), dataset ingestion, TS-4; corpus schema field for base-graph provenance (graph6 string + inflation vector replaces the seed).

### P7 — Adversarial local search over edge-maximal triangle-free H

- **What:** The battery inverted: a local search over MTF-graph space using kill-battery outputs as a fitness function, hunting for graphs that resist. Heuristic signals **steer only**; exact methods alone are reported (hard rule inherited from PROJECT.md).
- **Construction:**
  1. State space: edge-maximal triangle-free H on fixed odd n (start n = 31, where exact adjudication is proven cheap). Moves ("triangle-preserving flips"): delete one H-edge, then greedily re-maximalize with a seeded random completion order — output is again MTF; optionally larger perturbations (delete k edges / vertex neighborhood rewires) for basin escape.
  2. Fitness (cheap → expensive tiers): gate-passage depth; heuristic restarts-to-solution and initial-conflict counts under a fixed budget (TS-3 instrumented to expose these); ω(G)/χ(G) and ν-profile as shaping terms; exact had₂ − χ margin computed only at checkpoints/elites (ILP in the inner loop is unaffordable and, worse, would tempt margin-hacking).
  3. Infrastructure: battery-as-library with per-call budgets; fitness cache keyed by nauty canonical label (isomorph dedup — mandatory, else the search re-pays for the same graph); provenance lineage (parent canon label, move, seed) so every elite is exactly rebuildable; population/restart schedule seeded and logged.
  4. Discipline: any "resistant" elite goes straight to the survivor protocol (E3) — independent reproduction, scaled exact search, family-membership audit — before it is even *called* interesting internally. The seed-137 failure mode (searcher artifact masquerading as resistance) is the expected dominant outcome and the fitness function's known Goodhart risk.
- **Why open/interesting:** Every structured pool samples where theory already shines light; P7 is the only feature that searches *against the battery itself*, and it converts every improvement in the battery into sharper search. If a size-≤2-model obstruction exists anywhere near these sizes, adversarial pressure is the likeliest finder — and any find is instantly certifiable (had₂ ILP) because the sizes are chosen inside exact range.
- **Complexity:** MEDIUM-HIGH. No deep new math; the cost is engineering (caching, budgets, lineage) plus the epistemic guardrails.
- **Depends on:** Everything: TS-1..TS-10 as an importable library (not scripts), nauty canonical labels, instrumented TS-3, E3. Should be the last pool to start; runs forever after.

---

## Feature Dependencies

```
Foundation port (repo-relative, deterministic, library-ized)
    └──requires──> nothing (first)

TS-2 exact χ ──feeds──> TS-1 G6, runbook step 2
TS-3 profile-general heuristic ──requires──> Foundation
TS-4 had₂ ILP ──requires──> Foundation; TS-10 backends
TS-5 had₃ escalation ──requires──> TS-4 (only fires on had₂ < χ); TS-10 CP-SAT
TS-6 verifier ──independent of──> all searchers (separate code path); extended by TS-5 (size-3)
TS-7 corpus ──requires──> TS-6 (nothing stored unverified); gates the milestone (296 reproduction)
TS-8 results log ──requires──> TS-1 (kill reasons), TS-4 (exact outcomes)
TS-9 CLI ──requires──> TS-1..TS-8
TS-10 backends/nauty ──requires──> Foundation

P0 ──requires──> TS-10 (geng -t + canon), new CDM exact checker, transfer lemma, TS-7
P1 ──requires──> TS-3 (blocking at large n), TS-7 (296 reproduction first), E3
P2 ──requires──> TS-4; group-spec plumbing
P3 ──requires──> TS-10 CP-SAT (blocking), inflation operator, TS-3
P4 ──requires──> TS-4; exact ω (G6); settled-window map in G5
P5 ──requires──> ETT construction study, TS-3 + TS-10 (both blocking)
P6 ──requires──> inflation operator (shared with P3), dataset ingestion, TS-4
P7 ──requires──> battery-as-library (all TS), nauty canon cache, instrumented TS-3, E3

E1 falsification harness ──requires──> TS-7 (a corpus to cross-examine)
E2 monotonicity audit ──requires──> nothing technical (policy + allowlist); referenced by E1
E3 survivor protocol ──requires──> TS-10 (scaled exact search), TS-8 (RESISTANT queue)

P7 ──enhances──> P1..P6 (feeds found-hard instances back as new family seeds)
E1 ──strengthened by──> every pool kill (corpus growth)
G5 screen ──must track──> P3/P4/P5 results (settled cells move from "pool" to "gate kill")
```

### Dependency Notes

- **TS-3 blocks P1-at-scale and P5:** beyond n ≈ 150–200 no exact backend can adjudicate, so the heuristic + verifier is the only existence engine; the spanning-profile bug class (seed 137) must be fixed before any large-n claim is logged.
- **TS-10 CP-SAT blocks P3 and TS-5:** CBC demonstrably handles n ≈ 31–151 ILPs; the HS inflation instances (~4k–15k binaries with quadratic conflict families) and any had₃ model need CP-SAT.
- **Inflation operator is shared (P3, P6):** build once with an inflation-vector spec in the corpus schema; both pools' provenance is (base graph id, vector) instead of (n, seed).
- **The gate and the pools co-evolve:** every class the program or the literature settles gets added to G5 with a citation, so the battery never re-spends on proven terrain — the settled/open map (esp. for P4 cells) is a maintained artifact, not a one-time table.
- **CDM checker (P0) ≠ had₂ ILP (TS-4):** different objective (nonempty connected dominating matching — feasibility with connectivity), different failure semantics (a CDM-less graph is a rung-1 candidate, not yet an SHC event). Do not conflate in the CLI.
- **E1 conflicts with nothing but depends on discipline:** it is only meaningful if TS-7 stores full, independently re-verifiable models — another reason nothing unverified ever enters the corpus.

## MVP Definition

### Launch With (v1 — the milestone's Foundation + first blood)

- [ ] Foundation port: repo-relative paths, deterministic (n, seed), library + CLI split — everything else stands on this
- [ ] TS-1 gate (G1–G4 minimally; G5/G6 screens can start as stubs logging "screen not yet active") with frozen definitions signed off by the author
- [ ] TS-2 exact χ, TS-3 profile-general heuristic (seed-137 class fixed), TS-4 had₂ ILP (CBC reference), TS-6 verifier, TS-7 corpus, TS-8 log, TS-9 CLI
- [ ] 296-instance corpus regenerated and independently re-verified; 27 stored certificates reproduced — the reproducibility gate that proves the port
- [ ] P0 executed (n = 12–14, 1,813 graphs): cheapest new certified terrain, extends the literature's stated n ≤ 11 frontier, validates the whole harness on a second problem shape (CDM) beyond had₂

### Add After Validation (v1.x)

- [ ] TS-10 CP-SAT backend + backend cross-validation — trigger: first instance CBC cannot close, or P3 start
- [ ] P1 at scale + P6 (both cheap: existing generator / existing dataset) — trigger: corpus reproduction green
- [ ] P2 generalized groups — trigger: P1/P6 pipelines stable
- [ ] TS-5 had₃ escalation implemented (not just designed) — trigger: any had₂ < χ event, or before P3/P5 exact pushes (so an SHC event can be escalated same-day)
- [ ] P3, P4 — trigger: CP-SAT validated
- [ ] E3 survivor protocol — trigger: first RESISTANT instance at a size exact methods cannot reach

### Future Consideration (v2+)

- [ ] P5 crooked families — after the ETT construction study; heaviest research dependency
- [ ] P7 adversarial search — deliberately last: it needs the whole battery as a stable library and inherits every guardrail
- [ ] E1 falsification harness + E2 monotonicity audit as executable policy — Phase 3 of the milestone
- [ ] Lean 4 certificate formalization — milestone 2 by decision (Out of Scope here)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Foundation port + TS-7 corpus reproduction | HIGH (nothing is real until the 296 reproduce) | MEDIUM | P1 |
| TS-1 gate + TS-2 + TS-3 + TS-4 + TS-6 + TS-8 + TS-9 | HIGH | MEDIUM | P1 |
| P0 CDM frontier | HIGH (named frontier extension, cheapest certified result) | LOW | P1 |
| TS-10 CP-SAT + nauty | HIGH (unlocks P0 gen, P3, TS-5) | MEDIUM | P1/P2 boundary |
| P1 at scale | HIGH (the program's signature family + open asymptotic) | MEDIUM | P2 |
| P6 Ramsey inflations | MEDIUM-HIGH (structured contrast at proven-cheap sizes) | LOW | P2 |
| P2 general Cayley | MEDIUM | MEDIUM | P2 |
| TS-5 had₃ | HIGH when it fires, idle otherwise | HIGH | P2 (design), fires on demand |
| P3 Higman–Sims inflations | HIGH (the named SRG gap) | HIGH | P2/P3 |
| P4 generalized Kneser | MEDIUM-HIGH (named open window) | MEDIUM | P3 |
| E1/E2/E3 escalation machinery | HIGH (the program's epistemic moat) | MEDIUM | P3 |
| P5 crooked families | HIGH (newest, hardest regime) | HIGH | P3/v2 |
| P7 adversarial search | HIGH (only generative pool) | HIGH | v2 |

## Literature Frontier Analysis (competitor-analysis analogue)

| Capability | CLWY 2025 (arXiv 2512.17114) | Other literature | Our Approach |
|-----------|------------------------------|------------------|--------------|
| CDM exhaustive verification | All graphs, n ≤ 11 | — | P0: all connected α = 2 graphs at n = 12–14 via the 1,813 MTF complements + transfer lemma; stretch ≤ 17 |
| Per-instance SHC decision | Theorem-per-family (fractional covers, structural lemmas) | — | Exact had₂ ILP decides SHC on ANY individual graph, certificate emitted either way |
| Random families (TFP) | Absent | Bohman / Fiz Pontiveros–Griffiths–Morris analyze the process, not Hadwiger on its complements | P1: 296 verified instances, scaling, resistance discipline |
| Sum-free Cayley complements | Absent | Sum-free set theory exists (Green–Ruzsa); no Hadwiger testing found | P2 structured-vs-random grid |
| SRG inflations | Clebsch/Mesner/Gewirtz all inflations; HS base only (SHC_{n/2}) | — | P3: the open HS-inflation cells, CP-SAT + symmetry |
| Generalized Kneser | CDM inside ≈ 2k − t ≤ n < (5/2)(k − t) | — | P4: out-of-window cells, settled/open map maintained |
| 𝒲_t families | 𝒲₇ Cayley (p ≡ 11 mod 12) settled; other primes open | ETT construct 𝒲₃/𝒲₅ (crooked), pose nothing about their complements' minors | P5: crooked complements + remaining Eberhard primes |
| Ramsey-extremal witnesses | Absent | Brinkmann–Goedgebeur enumerate (3,8,27); nobody runs minors on their complements | P6: battery + inflations at odd n ≥ 31 |
| Adversarial instance search | Absent | — | P7: battery-as-fitness with exact adjudication |
| Impossibility hygiene | n/a (existence-side paper) | Odd Hadwiger just fell to a clever construction (KSSW Dec 2025) | E1/E2/E3 + anti-features: impossibility is radioactive, corpus is the falsification suite |

## Sources

**Verified primary (HIGH confidence):**
- Costa, Luu, Wood, Yip — "Verifying Hadwiger's Conjecture for Examples of Graphs with α(G) = 2", [arXiv:2512.17114](https://arxiv.org/abs/2512.17114) (CDM conjecture + n ≤ 11 verification; Theorem 2.10 ladder; Lemmas 2.5, 3.6–3.7, 3.12, 3.14–3.17; Theorems 3.18, 3.21; Conjecture 11; open-case list) — fetched abstract + HTML twice
- Eberhard, Taranchuk, Timmons — "Examples of diameter-2 graphs with no triangle or K_{2,t}", [arXiv:2508.19646](https://arxiv.org/abs/2508.19646) (𝒲₃ infinite, 𝒲₅ regular, 𝒲₇ Cayley p ≡ 11 mod 12; crooked graphs from de Caen–Mathon–Moorhouse)
- Kühn, Sauermann, Steiner, Wigderson — "Disproof of the Odd Hadwiger Conjecture", [arXiv:2512.20392](https://arxiv.org/abs/2512.20392)
- Norin, Seymour — "Dense minors of graphs with independence number two", [arXiv:2206.00186](https://arxiv.org/abs/2206.00186) / [JCTB](https://www.sciencedirect.com/science/article/abs/pii/S0095895625000619) (⌈n/2⌉-vertex minor, ~0.98688 density — the "sliver" calibration)
- OEIS [A216783](https://oeis.org/A216783) — maximal triangle-free graph counts (n = 12: 147; 13: 392; 14: 1,274; … 18: 1,337,848); Brandt–Brinkmann–Harmuth generator + House of Graphs links — fetched b-file directly
- [McKay's Ramsey graph data](https://users.cecs.anu.edu.au/~bdm/data/ramsey.html) — R(3,8) = 28 (McKay–Zhang 1992); 477,142 Ramsey(3,8,27) graphs (Brinkmann–Goedgebeur 2012), downloadable
- Chen, Deng — "Connected matching in graphs with independence number two", [arXiv:2409.05920](https://arxiv.org/abs/2409.05920) (FGS conjecture through t ≤ 22 — linear connected matching genuinely open)
- Project-internal: `.planning/reference/alpha2-program-source.md` (Appendix C toolkit verbatim; Appendix D certificate facts incl. seed-137 exact resolution had₂ = 17 > 16 = χ), `.planning/PROJECT.md`

**Adjacent literature noted (MEDIUM confidence, cited-not-fetched):**
- "Dominating Hadwiger's Conjecture for graphs G with α(G) = 2", [arXiv:2510.12564](https://arxiv.org/abs/2510.12564); "…holds for all 2K₂-free graphs", [arXiv:2510.12567](https://arxiv.org/abs/2510.12567) — the DHC strengthening thread; track for G5 screen additions
- Plummer–Stiebitz–Toft 2003 (as surveyed by CLWY [53]: B₇-free ⟹ had ≥ n/2) — **flag: confirm B₇ definition at phase time**
- Balogh–Kostochka, Fox — constant-factor/additive improvements over Duchet–Meyniel (exact form of Fox's bound: pin during P1 phase research)
- Green–Ruzsa sum-free classification; Bohman–Keevash / Fiz Pontiveros–Griffiths–Morris TFP analyses — training-data recall, standard results

**Known gaps (LOW confidence — flagged for phase research):**
- Exact original G1–G6 labels/definitions (reconstruction provided; confirm with author)
- Exact CLWY Theorem 3.12 parameter window + intersection convention for K(n, k, ≥ t)
- ETT crooked-construction details and instance vertex counts (P5 phase must read the paper's construction sections)
- Triangle-free graph totals per n (~1.3M at n = 12) quoted from memory (A006785) — only used as a non-load-bearing comparison

---
*Feature research for: the α = 2 Program — Hadwiger hunt-and-certify toolkit*
*Researched: 2026-07-21*
