# Pitfalls Research

**Domain:** Computational attack + certification harness on Hadwiger's Conjecture (α = 2) — exact solvers, minor theory, certificate corpus, Lean formalization
**Researched:** 2026-07-21
**Confidence:** HIGH (encoding claims checked line-by-line against Appendix C source; monotonicity counterexamples verified by direct computation; solver/library behavior verified against primary docs and issue trackers; items flagged MEDIUM/LOW inline)

**Organizing principle.** The Asymmetry Principle is not just a philosophical constraint — it recurs *inside the tooling* at every level. In every pitfall below, the same shape appears: **a bug that over-counts existence gets caught by the verifier (the extracted model fails); a bug that under-counts existence produces a false impossibility signal with no certificate to catch it.** All engineering effort should be biased accordingly: the "found" path is self-checking; the "not found / less than χ" path is where every safeguard must live.

Phase names used below: **Foundation** (toolkit port, verifier, corpus regeneration, CI), **Phase 1** (candidate pools P0–P7), **Phase 2** (kill battery runbook, gates G1–G6), **Phase 3** (escalation: Falsification-Rule harness, Monotonicity Audit, survivor protocol), **Milestone 2** (Lean).

---

## Critical Pitfalls

### Pitfall 1: A missing or inverted conflict class in the had₂ encoding

**What goes wrong:**
The had₂ ILP (Appendix C.3 `ilp_had2`, C.4 inline) has exactly four constraint classes, and each maps to a specific substructure of the triangle-free graph H:

| Constraint class | Code | Substructure of H | Exact count |
|---|---|---|---|
| Vertex-disjointness | `Σ mv[e ∋ v] + sv[v] ≤ 1` per vertex | — | n constraints |
| Pair–pair conflict | `mv_i + mv_j ≤ 1` when all 4 cross pairs are H-edges | **4-cycles of H** (the two selected pairs are the diagonals) | npp = #C₄(H) = ½ Σ_{u<v} C(codeg_H(u,v), 2) |
| Single–pair conflict | `sv[v] + mv[(a,b)] ≤ 1` when v H-adjacent to both a,b | **cherries (paths P₃) of H** | nsp = Σ_v C(deg_H(v), 2) |
| Single–single conflict | `sv[u] + sv[v] ≤ 1` per H-edge | **edges of H** | nss = \|E(H)\| |

(The bijections use triangle-freeness: if v is H-adjacent to both a and b then ab ∉ E(H) automatically, so *every* cherry conflicts with a legal pair variable; every 4-cycle of H is chordless, so both diagonals are legal pair variables. Derived from the C.3/C.4 code; the counts give an independent checksum — `investigate_137.py` already prints npp/nsp/nss.)

What breaks per omission:

- **Missing any conflict class or disjointness** → the "family" is not pairwise-adjacent (or reuses vertices) → had₂ **over-counted**. If had₂ ≥ χ, the extracted model **fails the independent verifier** — caught, *provided extraction + verification always run*. If anyone ever reports the objective value without extracting and verifying a model, this bug ships silently.
- **Inverted conflict predicate** (requiring SOME cross pair in H instead of ALL — an `or` for an `and`) → massive over-constraint → had₂ **under-counted** → a false "had₂ < χ" → **a fabricated SHC-counterexample claim, and there is no certificate that can catch it.** This is the radioactive direction.
- **H/G adjacency mixup**: the entire codebase stores H's adjacency (`adj` is the triangle-free graph); G-edges are the *non-edges* (`Gedges = [(u,v) ... if v not in adj[u]]`). One flipped membership test anywhere inverts the whole semantics while remaining perfectly runnable.

**Why it happens:**
Four separate constraint classes, two graphs (G and H) sharing one adjacency structure, and an objective that still produces plausible-looking numbers when a class is missing. Nothing crashes; the only symptom is a wrong integer.

**How to avoid:**
1. **Structural checksums (cheap, decisive):** after building the model, assert `nss == |E(H)|`, `nsp == Σ_v C(deg_H(v),2)`, `npp == ½ Σ_{u<v} C(codeg_H(u,v),2)` — three one-line combinatorial counts computed by independent code. A missing class shows up as a count of 0 or a mismatch instantly.
2. **Brute-force differential on tiny graphs:** exhaustive had₂ by enumeration for n ≤ 10 (all families of disjoint ≤2-sets, pairwise adjacency checked directly) vs the ILP, over random triangle-free H and hand-picked cases with known values (H = C₅ ⇒ G = C₅, had₂ = 3 = χ; complete bipartite H; stars; perfect matchings). Run as unit tests.
3. **Cross-solver differential:** CBC vs CP-SAT must agree on the *value* on every test instance and on a nightly random battery. Same value from two independent encodings is strong evidence; disagreement is an immediate red alert.
4. **Never report the objective without the witness:** the pipeline rule is `value ≥ χ ⇒ extract model ⇒ verifier must pass, else hard failure` (a verifier failure here means the *encoding* is broken, not the instance — treat it as a stop-the-world bug).
5. **Regression-pin seed 137:** `had₂(n=31, seed=137) == 17` becomes a permanent test. It is the one instance where the exact solver has already arbitrated a dispute.

**Warning signs:**
Constraint-class counters at 0 or mismatching the combinatorial formulas; CBC and CP-SAT disagreeing; a verifier failure on an ILP-extracted model; had₂ < ω(G) (impossible — singletons on a max clique are always a valid family, so had₂ ≥ ω(G) = α(H) always); had₂ jumping discontinuously between code versions on the same (n, seed).

**Phase to address:**
Foundation (encoding tests, checksums, differential harness ship with the port); Phase 2 relies on it; Phase 3's CP-SAT scaling re-runs the same differential suite.

---

### Pitfall 2: Treating a timed-out incumbent as the exact optimum ("had₂ < χ" without proven optimality)

**What goes wrong:**
`ilp_had2` calls `prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=300))`, then does `val = pulp.value(prob.objective); had2 = int(round(val))` — **without ever checking `prob.status`**. When CBC hits the time limit it returns the best incumbent found so far, which is only a *lower bound* on had₂. PuLP's status reporting around CBC time limits is known-treacherous: documented issues where PuLP reports "Optimal" for runs that stopped on the time limit with a ~10% gap, populates non-integer-feasible solutions, and where CBC applies the time limit inconsistently ([pulp#517](https://github.com/coin-or/pulp/issues/517), [Cbc#440](https://github.com/coin-or/Cbc/issues/440), [pulp discussion #486](https://github.com/coin-or/pulp/discussions/486)). And `msg=0` suppresses the very CBC log line ("Stopped on time limit") a human would have noticed. `investigate_137.py` prints the status but its `had_2(G) < chi(G)` branch is not *gated* on it.

The asymmetry, precisely:
- Incumbent ≥ χ → extract model → verifier passes → **sound kill** (the certificate is self-justifying; optimality was never needed).
- Incumbent < χ at timeout → means nothing, but the code path prints/records a number that reads like an exact value. One `if had2 < chi` on an incumbent = **a false SHC-counterexample**, the most sensational possible wrong claim this program can make.

**Why it happens:**
Solver APIs make the objective value equally accessible whether or not it was proven optimal; the status check is a separate, skippable step; and on small instances CBC always finishes, so the missing check never fires during development.

**How to avoid:**
1. **Gate every "<" conclusion on proven optimality:** CBC: `prob.status == LpStatusOptimal` *and* (PuLP ≥ 2.x) `prob.sol_status == LpSolutionOptimal`. CP-SAT: `status == cp_model.OPTIMAL` (not `FEASIBLE`), and record `solver.BestObjectiveBound()` — the claim "had₂ = v" requires `ObjectiveValue == BestObjectiveBound == v`.
2. **Tri-state result type:** `had2_exact(…) → {PROVEN(v), LOWER_BOUND(v), FAILED}` — make it *impossible to express* "had₂ < χ" from a `LOWER_BOUND`. Timeout-with-incumbent-below-χ is classified UNRESOLVED, never RESISTANT.
3. **Two-solver rule for the radioactive direction:** any `had₂ < χ` (a certified SHC counterexample — a *publishable result*) requires CBC and CP-SAT independently proving optimality at the same value, with solver versions, parameters, and logs stored. (Per the survivor protocol, an independent reproduction precedes any claim anyway.)
4. **Record both bounds always:** store `(best_family_value, best_bound)` in every record so a later audit can see how close any timeout got.

**Warning signs:**
`msg=0` with a `timeLimit` set anywhere in the exact path; a record whose method string says "exact" but has no stored solver status; had₂ values that change when the time limit changes; `sol_status`/`status` absent from the JSON schema.

**Phase to address:**
Foundation (the ported `ilp_had2` gets the tri-state interface and status gating — this is a required *fix* to Appendix C, not a port); Phase 3 (survivor protocol enforces the two-solver rule before any impossibility talk).

---

### Pitfall 3: Branch-set connectivity is enforced *structurally* in the reference ILP — every re-encoding must re-add it explicitly

**What goes wrong:**
In `ilp_had2`, "a size-2 branch set induces a connected subgraph of G" is never written as a constraint — it is enforced by *variable indexing*: pair variables exist only for `Gedges` (non-edges of H). Two re-encoding contexts will lose this silently:

1. **CP-SAT port:** a natural CP-SAT model ("assign each vertex a block label, maximize blocks used") or a Boolean grid over *all* vertex pairs quietly admits "branch sets" {a,b} with ab ∉ E(G) — a disconnected pair. Every cross-adjacency can still hold, so the "model" passes the pairwise-adjacency constraints while not being a minor model at all. had₂ inflates; worse, it inflates *plausibly* (bounded by n still).
2. **Lean definitions (Milestone 2):** a hand-rolled `IsKMinorLe2` that requires disjointness and cross-adjacency but forgets `G.Adj a b` for 2-element branch sets defines a *different, larger* parameter. Theorems about it are theorems about nothing relevant. (The same slip in reverse — requiring branch sets to be H-edges — makes the theorem vacuously false and *will* be noticed; the too-weak direction compiles and passes.)

Escalation to branch-set-size-3 multiplies the hazard: a 3-set needs a *spanning connected* induced subgraph in G (path or triangle among the three — at least 2 of the 3 internal pairs as G-edges arranged connectedly), and its conflict predicate is no longer a clean local substructure of H. The size-≤2 elegance (conflicts = edges/cherries/C₄s of H) does not generalize; hand-deriving size-3 conflicts is where a whole new class of encoding bugs enters.

**Why it happens:**
Implicit constraints are invisible in the constraint list, so a porter auditing "did I copy all the constraints?" answers yes while dropping one that was never written down.

**How to avoid:**
1. **Write the model-validity predicate once, on paper, as the spec:** (i) branch sets disjoint, nonempty, size ≤ s; (ii) each branch set induces a *connected* subgraph of G; (iii) every pair of branch sets joined by ≥ 1 G-edge. Every encoding (CBC, CP-SAT, size-3, Lean) is audited against this list item by item, with an explicit note of *which mechanism* enforces each item.
2. **The verifier is the arbiter for every backend:** any model extracted from any encoding goes through the same independent verifier, which checks connectivity explicitly (`verify_model` already checks `b not in adj[a]` for pairs; the size-3 verifier must check connectivity of 3-sets in G — spec it now).
3. **Cross-encoding differential:** CBC (edge-indexed) vs CP-SAT (whatever indexing) on the test battery — a structurally-lost constraint shows up as CP-SAT > CBC on some tiny instance.

**Warning signs:**
A CP-SAT backend that agrees with CBC on most instances but exceeds it on some; extracted models with a pair that the verifier rejects as "pair is not an edge of G"; a size-3 escalation whose value jumps implausibly (had₃ ≫ had₂ + small).

**Phase to address:**
Foundation (CP-SAT backend lands here — spec + differential first); Phase 2/3 (branch-set-3 escalation); Milestone 2 (the same predicate list becomes the Lean definition audit).

---

### Pitfall 4: Symmetry breaking that silently deletes all optimal models

**What goes wrong:**
For vertex-transitive candidates (Cayley complements P2, Higman–Sims P3, SRGs), the temptation is "WLOG vertex 0 is a singleton / is in a pair / is uncovered." These are *not* WLOG. The validity criterion for a symmetry-breaking constraint C is: **for every optimal solution x there must exist σ ∈ Aut(instance) with σ(x) satisfying C.** Vertex-transitivity moves any single vertex anywhere, but it does not guarantee any particular *role* is realized in some optimum:

- Concrete 5-vertex disaster (hand-verified): H = Ḡ = C₅ — the canonical tight α = 2 instance — has had₂ = 3 = χ, and *every* optimal family is spanning (2 pairs + 1 singleton). The innocent constraint "vertex 0 is unused" (superficially justified as "some vertex can be left out, WLOG it's 0") is satisfied by *no* optimal family: the solver returns had₂ = 2 < 3 = χ — **a fabricated SHC counterexample on five vertices.**
- "Vertex 0 is in a pair" fails symmetrically whenever all optima are all-singleton families (possible: had₂ ≥ ω(G) = α(H), which is ≥ 8 at n = 31 by R(3,8) = 28, and 14 on seed 137).
- For TFP complements the trap is worse: a random maximal triangle-free H almost surely has **trivial** automorphism group, so *any* symmetry-style constraint is a pure unsound restriction — there is no symmetry to break.
- Fixing the singleton/pair *profile* is the seed-137 bug re-entering through the solver door (see Pitfall 5).

**Why it happens:**
Symmetry breaking is standard ILP practice, the speedups are real, and on satisfiable instances the wrongness is invisible (a model is still found). The invalid constraint only bites in the branch where it matters most — the impossibility branch.

**How to avoid:**
1. **Derive constraints only from the computed automorphism group** (nauty is already in the stack): orbit/lex-leader constraints w.r.t. verified generators of Aut(H), never from assumed family-level symmetry. If Aut is trivial, no symmetry constraints — full stop.
2. **Prefer solver-internal symmetry handling:** CP-SAT's `symmetry_level` parameter does automatic, objective-preserving symmetry detection inside the solver — sound by construction and usually enough.
3. **The assume-and-verify discipline (asymmetric use):** with SB on — if the result is a model ≥ χ that verifies, the kill is sound regardless of the SB's validity (the certificate is self-justifying). If the result is a value < χ, **rerun without SB before recording anything.** SB is a speedup for the existence direction only; it is never allowed to touch an impossibility conclusion.
4. **Differential test in CI:** on a battery of small vertex-transitive instances (cycles, Cayley graphs, Petersen), assert had₂(with SB) == had₂(without SB).

**Warning signs:**
Any hand-written constraint mentioning a specific vertex index; SB code paths shared between the existence and impossibility branches; a "resistant" instance that first appeared after SB was enabled; Aut(H) never actually computed.

**Phase to address:**
Phase 3 (scaled exact search is where SB gets added — the asymmetric-use rule goes in the survivor protocol); Foundation (the SB differential test rides the standard battery).

---

### Pitfall 5: The under-powered-heuristic trap — a fixed search-space *shape* masquerading as instance hardness (seed 137)

**What goes wrong:**
The Appendix C heuristic hard-codes the model *shape*: `solve()` sets `p = n − k; s = 2k − n` and `initial_state` builds exactly p pairs + s singletons **partitioning all n vertices**. But a K_k model need not span: it may leave vertices unused, with any singleton count s′ from max(0, 2k−n) up to k. At n = 31, k = 16 the code can represent *only* s′ = 1 (15 pairs + 1 singleton, spanning); the actual seed-137 optimum is 9 pairs + 7 singletons covering 25 vertices with 6 unused — **a shape the searcher could not even express.** The instance was never resistant; the search space was truncated. Compounding traps in the same code: `sweep.py` silently uses a *different* time budget (60 s) than the baseline driver (90 s); and `assert p >= 0 and s >= 0` means the heuristic *crashes* on any pool instance with χ < n/2 (possible in P4/P6), which a sloppy runner would log as a failure or worse.

**Why it happens:**
The spanning profile is correct for the *generic* TFP instance (near-perfect matchings make near-spanning models natural), so it passes hundreds of instances before the outlier arrives. Profile assumptions feel like optimizations, not semantics.

**How to avoid:**
1. **The classification rule is structural, not procedural:** RESISTANT is a label only an *exact* method (proven-optimal, Pitfall 2) can assign. Heuristic failure auto-escalates to the ILP; the runbook encodes "heuristic NOT FOUND → exact solver" as an unconditional edge, never a judgment call.
2. **Fix the searcher anyway:** let s′ range (iterate profiles, or drop the spanning requirement and allow an "unused" pool). Cheap and removes a whole class of false signals.
3. **Budget/restart policy is data, not code:** time budgets, restart counts, and RNG policies are declared per-run in config and recorded in every log line, so "resistance" is always attributable to a specific searcher configuration.
4. **Escalation ladder before the R-word:** fresh independent RNG streams (seed the retry as `random.Random(f"{n}:{seed}:retry:{i}")` — string seeding is SHA-512-based and hash-randomization-immune), 5–10× budget, *then* exact. This is exactly the `investigate_137.py` sequence; make it the codified path, not an ad-hoc script.
5. **Language discipline in logs:** the status string is "NOT FOUND BY <searcher-id, budget, seed>" — never "no model."

**Warning signs:**
Any assert on profile counts in a searcher; a heuristic that cannot represent the stored seed-137 model (test: replay it as an initial state — does the data structure even hold it?); failure rates that jump when n changes parity; "resistant" counts that vary with the time budget.

**Phase to address:**
Foundation (port fixes the profile restriction; seed-137 becomes a named regression test); Phase 2 (the runbook hard-codes heuristic→exact escalation and the classification vocabulary).

---

### Pitfall 6: Reproducibility rot — shared RNG streams, iteration-order coupling, and silent library-semantics drift

**What goes wrong:**
Several independent mechanisms, all present or latent in the Appendix C code:

1. **One RNG stream across pipeline stages:** `run_instance` passes the *same* `rng` from `triangle_free_process` into `solve`. The searcher's randomness therefore depends on exactly how many `randrange` calls the *generator* consumed — any refactor of the process (even a pure optimization of `RandomSet`) shifts the search stream, and heuristic outcomes flip on unrelated code changes. The graph stays identical; the *searcher behavior* doesn't.
2. **Set-iteration-order coupling:** `solve` picks conflicts via `tuple(conf)[rng.randrange(len(conf))]` — iteration order of a Python set of int-tuples. Verified here: stable across `PYTHONHASHSEED` for int tuples (unlike str keys, which reorder run-to-run — demonstrated locally), but it is an *implementation detail* of CPython's hashing, not a language guarantee; a CPython upgrade can legally change it.
3. **Library semantics drift, the worst kind:** networkx `max_weight_matching` returned a **dict** (mate map, len = 2ν) in 2.0 and a **set of edges** (len = ν) by 2.2 — verified against both versions' official docs. `nu = len(M)` is silently wrong by a factor of 2 across that boundary, making χ = n − 2ν without any error. Modern (3.x) behavior is the set. Version drift in either direction reintroduces it.
4. **Solver-model nondeterminism:** the optimal *value* is canonical; the optimal *model* is not. CBC version bumps change which optimum is returned; CP-SAT with default parallelism is explicitly nondeterministic, and even `num_workers=1` determinism has had regressions ([or-tools#3943](https://github.com/google/or-tools/issues/3943), [#3948](https://github.com/google/or-tools/issues/3948)); deterministic multi-worker needs `interleave_search:true` + `share_binary_clause:false`. A workflow that promises "rerun reproduces the stored model bit-for-bit" will break.
5. **Certificates that aren't self-contained:** Cayley records store the sum-free set S but *not* `H_edges`; verification requires re-running `cayley_adj` — fine only if that reconstruction is itself part of the audited verifier. The original absolute output path (`/mnt/user-data/outputs/...`) is already flagged for the port.

**How to avoid:**
1. **Independent child streams per stage:** `random.Random(f"{family}:{n}:{seed}:{stage}")`. Generator streams never feed searchers.
2. **Sort before choosing:** any RNG choice over a set goes through `sorted(...)` first (cost is negligible at these sizes).
3. **Pin and guard:** pin exact versions (requirements lockfile) *and* add semantic runtime guards that survive repinning: assert `M` is a set of 2-tuples each an H-edge, `2*len(M) ≤ n`, and `chi ≥ ceil(n/2)` (always true since ν ≤ ⌊n/2⌋ — the dict-semantics bug instantly violates it). Environment note: Python 3.9.6 (present) is past EOL (Oct 2025); current networkx (≥3.3) and recent OR-Tools wheels require newer Pythons — resolve the interpreter/library matrix *first*, at Foundation, before pinning (MEDIUM confidence on exact wheel cutoffs; verify at port time).
4. **Two-tier reproducibility, stated explicitly:** Tier 1 (*replay*): every stored certificate is self-contained (store `H_edges` for **all** families, plus solver name/version/params/status) and re-verifies from the JSON alone — this must never break. Tier 2 (*regeneration*): (n, seed) → identical graph → identical invariants → *some* verified model — the model bits are allowed to differ. Never promise Tier 2 model-bit stability; store a SHA-256 of the canonical sorted edge list in each record so graph identity is checkable at a glance.
5. **Corpus reproduction runs in CI** (already an Active requirement): Tier 1 over all 27 stored certificates + Tier 2 spot checks per family.

**Warning signs:**
A kill flipping to not-found after a refactor that "didn't touch the searcher"; χ values ≈ n/2 becoming ≈ 0 or negative after an environment change (the factor-2 matching bug); stored model differing on rerun and someone "fixing" the corpus by overwriting it; certificates that can only be checked by importing the generator.

**Phase to address:**
Foundation (all of it: seeding scheme, guards, pinning, self-contained schema, CI); Phase 1 (every new pool inherits the schema).

---

### Pitfall 7: The verifier is the trust root — and the current one is strippable, non-independent, and trusts χ

**What goes wrong:**
Everything in this program reduces to "the independent verifier passed." Three concrete failure modes against the Appendix C `verify_model`:

1. **It is 100% `assert`-based.** Demonstrated locally: under `python -O`, every assert is stripped and `verify_model` **returns True on a blatantly invalid model** (overlapping branch sets, wrong count). One `-O` in a Makefile, container, or downstream import and the trust root is a no-op that still prints VERIFIED.
2. **It is not independent.** It calls the same `is_conflict` the searcher uses, on the same in-memory `adj` the generator built. A bug in `is_conflict` (or a corrupted `adj`) fools searcher and verifier *identically* — a common-mode failure. The 296/296 record is only as strong as this one shared function.
3. **It verifies the model, not the claim.** The claim is "had(G) ≥ χ(G)"; `verify_model` checks "these k sets form a K_k model" with k passed in by the caller. If ν were ever overstated by a matching bug, χ would be *understated*, and a genuinely-verified K_k model for k < χ_true would be recorded as a full kill. The chromatic half currently rests on trusting networkx's blossom — the one exact step with no stored witness.

**Why it happens:**
Verifiers get written last, by the same author, importing the handiest helpers; asserts feel like checks; and χ "is exact anyway" so nobody certifies it.

**How to avoid:**
1. **Rewrite with explicit exceptions/result types — zero asserts** — and add a CI job that runs the entire verification suite under `python -O` (guards against assert-based logic anywhere in the trust path, forever).
2. **True independence:** the verifier is a separate module (eventually a separate ~150-line single-file program; Milestone 2's Lean checker becomes the third leg) that (a) imports nothing from generator/searcher code, (b) reconstructs adjacency *only* from the certificate's stored `H_edges`, (c) re-implements adjacency/conflict logic with different data structures (e.g., frozenset edge set vs adjacency lists).
3. **Verify the full claim chain from the JSON alone:** (i) H from stored edges; (ii) H is triangle-free (needed for α(G) ≤ 2 *and* for the χ formula's validity); (iii) χ certified both ways: stored matching M (validity + size ⇒ ν ≥ |M|) **plus a stored Tutte–Berge witness** U ⊆ V with n − 2|M| = odd_components(H − U) − |U| (⇒ ν ≤ |M|) — this makes χ = n − ν fully hand-checkable and removes blossom from the trust base; (iv) the model verifies as a K_χ model. Foundation adds M and U to the certificate schema.
4. **Adversarial verifier suite (mutation testing):** for every stored certificate, generate known-bad mutants — drop a branch set; duplicate a vertex across sets; replace a pair with an H-edge; delete one cross-adjacency by editing `H_edges`; permute labels inconsistently; k off by one; truncated edge list — and assert the verifier **rejects every mutant with the right reason**. A verifier is tested by what it refuses.
5. **The recovery asymmetry (worth designing around):** if a *searcher/solver* bug is found later, all verified-existence certificates survive (they are self-justifying given a correct verifier); only absence/resistance labels are contaminated. If a *verifier* bug is found, everything must be re-verified. This is the argument for maximal verifier simplicity and for spending Milestone 2's first energy on the Lean re-verification of the corpus.

**Warning signs:**
`assert` anywhere in the verify path; the verifier importing from `hadwiger_tfp`; certificates that can't be verified without regenerating the graph; no test that feeds the verifier a bad model (if you've never seen it reject, you don't know it can).

**Phase to address:**
Foundation (this is *the* foundation deliverable — hardened verifier + adversarial suite + extended schema before corpus regeneration); Milestone 2 (Lean checker re-verifies the corpus as its first, non-vacuous task).

---

### Pitfall 8: A Falsification-Rule runner that passes arguments vacuously — or tests them at the wrong k

**What goes wrong:**
The Falsification Rule (any impossibility argument must decline on every corpus instance with a verified model) has teeth only if the runner actually exercises the argument:

1. **Vacuous compliance:** the argument's implemented hypothesis never engages (a predicate typo, a stricter-than-claimed precondition, an exception swallowed as "declined") → "declined on all 296" gets reported as PASS while testing nothing.
2. **The k-level blind spot (concrete gap in the current corpus):** certificates are stored at k = χ, but seed 137 has **had₂ = 17 > 16 = χ**, and the code stores only `fam[:chi]` — **the 17-set optimal family is computed and then discarded** (both `ilp_had2`'s caller and `investigate_137.py` truncate). An impossibility argument claiming "no K₁₇ minor" on seed 137 is *demonstrably false*, yet it would sail through a runner that only checks stored χ-level certificates. The corpus is currently blind above χ.
3. **Instance identity drift:** a runner that regenerates instances from (n, seed) with a drifted generator tests the argument against a different graph than the certificate's.
4. **Semantics of survival:** passing the rule is *necessary, never sufficient* — the corpus spans (so far) two families. Survival must not be reported as evidence the argument is sound, only that it wasn't instantly refuted.
5. **Soft-fail wiring:** a runner that logs the contradiction and continues lets a refuted argument reach the survivor protocol anyway.

**How to avoid:**
1. **Verdict protocol per (argument, instance):** {PROVES_IMPOSSIBLE(k), DECLINES(reason), ERROR, TIMEOUT} — ERROR/TIMEOUT are never counted as DECLINES.
2. **Engagement telemetry with a positive-control requirement:** the runner reports on how many instances the argument's hypotheses actually held; zero engagement = the run is INVALID, not a pass. Add synthetic positive controls: a deliberately-wrong toy argument ("graphs with an odd vertex count have no K_χ minor") must be *caught* by the runner — test the falsifier itself.
3. **Fix the corpus first:** store the **full optimal family** (all had₂ sets) alongside the truncated χ-model in every exact-method record, and have the runner test PROVES_IMPOSSIBLE(k) against every k with a verified witness (χ-level and had₂-level).
4. **Run against stored `H_edges` only** (Tier-1 artifacts), never regenerated instances.
5. **Hard-fail semantics:** any PROVES_IMPOSSIBLE on an instance with a verified model at that k auto-REJECTS the argument — a terminal state that blocks the survivor protocol, recorded in the results log.

**Warning signs:**
A falsification report with no engagement counts; "296/296 declined" on the argument's *first-ever* run (suspicious — most real arguments engage somewhere); certificate records whose `had2_exact` exceeds the stored model size (the blind spot's fingerprint — seed 137 is exactly this today); the runner importing generators.

**Phase to address:**
Phase 3 (the harness itself + verdict protocol); Foundation (schema change: store full optimal families — do it before regenerating the corpus so nothing needs re-solving later).

---

### Pitfall 9: A non-minor-monotone invariant sneaking into an impossibility argument

**What goes wrong:**
The impossibility schema — "f is minor-monotone, f(G) < f(K_k), therefore no K_k minor" — is sound *only* for genuinely minor-monotone f (monotone under deletions **and contractions**). The disqualified families fail specifically at contraction, and the failures are small and checkable (all verified by direct computation for this research):

- **Adjacency rank:** rank A(C₄) = 2, but contracting one edge gives K₃ with rank 3. Contraction *increased* rank on a 4-vertex graph. Any rank-based "certificate" (Haemers/minrank-style bounds included) can be destroyed by a single contraction; deletion-monotonicity (interlacing) does not extend, because identifying two rows/columns and OR-ing adjacencies is not a linear operation.
- **Spectral radius / eigenvalue bounds:** once-subdivided K₄ has λ_max ≈ 2.8558 while its minor K₄ has λ_max = 3 — the minor's spectral quantity *exceeds* the host's (computed here; the general mechanism is the Hoffman–Smith subdivision effect). Cauchy interlacing covers induced subgraphs only; there is no contraction analogue.
- **Chromatic number itself:** χ(K₃,₃) = 2, contract a perfect matching → K₃ with χ = 3. (A reminder that even "obviously graph-theoretic" invariants fail; the Hadwiger *conjecture* is precisely the claim that χ is dominated by a minor-monotone quantity.)
- **Rigidity-type invariants:** defined by sparsity counts/generic embeddings that contraction does not respect — same disqualification class.

The safe family is the one *designed* for minor-monotonicity: Colin de Verdière's μ, whose Strong Arnold (transversality) condition exists precisely to make minor-monotonicity provable (Colin de Verdière 1990; [van der Holst–Lovász–Schrijver survey](https://ir.cwi.nl/pub/1257/1257D.pdf); [Schrijver, "Minor-monotone graph invariants"](https://ir.cwi.nl/pub/2157/2157D.pdf) for the μ-type relatives), plus structural parameters (treewidth, genus, the Hadwiger number itself). Each corpus certificate already yields μ(G) ≥ χ(G) − 1 on its instance via μ(K_χ) = χ − 1 and monotonicity — the sound direction. A subtler trap on the safe invariant: *numerically estimated* μ upper bounds (floating-point eigensolvers, no Strong Arnold verification) used for impossibility are not certificates; μ enters impossibility arguments only with an exact/verified computation.

**Why it happens:**
Deletion-monotonicity is abundant and feels like minor-monotonicity; rank and spectral methods are the strongest tools in extremal combinatorics (Frankl–Wilson, slice rank), so they're what a strong practitioner reflexively reaches for — plausibly what the lost original argument did.

**How to avoid:**
1. **Allowlist, not blocklist:** an invariant enters an impossibility argument only with (a) a literature citation establishing minor-monotonicity, or (b) a machine-checked monotonicity proof. Default is disqualified.
2. **Automated monotonicity falsifier (cheap, decisive):** given a proposed invariant as code `f(graph) → number`, search random small graphs and single contractions for f(G/e) > f(G). Every counterexample above lives on ≤ 5 vertices — this catches rank, spectral, and χ in seconds. Run it *before* the (more expensive) Falsification-Rule corpus pass; a monotonicity violation is an instant, mechanical disqualification with a stored counterexample.
3. **Order the gates:** Monotonicity Audit → Falsification-Rule run → survivor protocol. Cheapest refutation first.

**Warning signs:**
An argument whose engine is a matrix over a field, an eigenvalue, or a tensor rank; monotonicity asserted with a citation that proves it only for subgraphs/induced subgraphs; the word "interlacing" doing load-bearing work in a *minor* claim; μ values produced by floating-point code without exactness discussion.

**Phase to address:**
Phase 3 (the audit gate + falsifier are part of the escalation harness); Foundation ships the falsifier utility in the test toolkit (it doubles as a teaching tool and gets unit-tested against the verified counterexamples above).

---

### Pitfall 10: Gate battery (G1–G6) — killing for the wrong reason, and gates that secretly depend on each other

**What goes wrong:**
Gate bugs are quiet because a wrongly-gated candidate just disappears from the pipeline:

1. **Criticality off-by-one:** the hard regime is χ(G) = ⌈n/2⌉ (equivalently ν(H) = ⌊n/2⌋). Encoding it as `n == 2*chi - 1` is correct **only for odd n** — it silently excludes even-n critical instances. The corpus itself contains the counterexample: row 4 is n = 32, χ = 16 = n/2 (n = 2χ, not 2χ − 1). A gate with the odd-only predicate drops a class of instances the program explicitly hunts.
2. **Hidden prerequisite chains:** χ = n − ν(H) is *only valid because* α(G) ≤ 2 (every color class is a vertex or an H-edge — Gallai/PST). If gates are reordered for cost and the χ stage runs on a candidate that never passed triangle-freeness, the "exact χ" is garbage — and everything downstream (target k, kill classification) inherits it. Similarly `is_edge_maximal_tf`'s equivalence to diameter-2 rides on maximality forcing connectivity; a gate computing diameter directly on a disconnected candidate raises (networkx) or returns ∞ — and a sloppy runner logs the crash as a kill.
3. **Crash ≠ fail:** `solve()`'s `assert p >= 0 and s >= 0` crashes outright on pool instances with χ < n/2 (live possibility in P4 generalized Kneser and P6 Ramsey-inflation pools). Exceptions mis-logged as gate failures poison the kill statistics and hide real bugs.
4. **Gate-kill ≠ Hadwiger-kill:** a gate failure means "not in the hard regime / malformed candidate" — it is *not* a verified instance of Hadwiger. If the results log counts gate-kills and model-kills in one number, the headline claim ("X/X killed") silently changes meaning.
5. **Cost-order changes behavior:** "kill on first failure" + reordering means a candidate failing G2 *and* G5 gets logged under whichever ran first; longitudinal statistics ("what kills candidates") become artifacts of ordering unless the reason taxonomy is stable.

**How to avoid:**
1. **Every gate kill stores a machine-checkable witness:** the triangle found (G1), the unclosable non-edge (G2), the computed ν and matching (criticality), the ω-clique, etc. Gate kills become mini-certificates; a wrong-reason kill is then detectable by replaying witnesses — and the replay is a cheap CI job.
2. **Explicit gate DAG + defensive re-assertion:** encode prerequisites (χ-stage requires G1) in code, and have expensive stages *re-assert* the cheap facts they depend on (`is_triangle_free` is O(Σ deg²) — trivial at these sizes; run it again inside the χ stage).
3. **Correct criticality predicate:** `nu(H) == n // 2` (equivalently `chi == (n + 1) // 2`) — with a unit test on n = 31 (χ = 16) *and* n = 32 (χ = 16), the corpus's own rows.
4. **Three-way outcome type per gate:** PASS / FAIL(witness) / ERROR(traceback) — ERRORs quarantine the candidate and page the operator; they never count as kills.
5. **Separate ledgers:** KILLED-BY-GATE (not-a-hard-candidate) vs KILLED-BY-MODEL (verified Hadwiger instance) vs SHC-CANDIDATE vs RESISTANT vs UNRESOLVED — the reporting discipline's vocabulary, enforced by the runbook's schema, so no future summary can blur them.

**Warning signs:**
A gate predicate mentioning `2*chi - 1`; kill counts that shift when gates are reordered (they shouldn't, for the same candidate set); zero ERROR entries ever (means errors are being swallowed); gate statistics with no stored witnesses; even-n candidates vanishing at the criticality gate.

**Phase to address:**
Phase 2 (the runbook *is* this: gate definitions pinned, witnesses, taxonomy, DAG); Foundation (the witness-logging convention and outcome types are part of the CLI contract).

---

### Pitfall 11: Lean statement vacuity — the theorem compiles, is sorry-free, and says nothing (Milestone 2)

**What goes wrong:**
The Asymmetry Principle's formal-methods corollary: the easy-to-formalize direction was never in doubt, and a wrong *statement* certifies nothing while feeling conclusive. Specific vacuity channels for this project, checked against current mathlib:

1. **No minor theory to lean on:** mathlib has no graph-minor module (`Mathlib/Combinatorics/SimpleGraph/Minor` does not exist — 404 at research time; searches surface no `IsMinor`/Hadwiger-number development; re-verify at milestone start). Every load-bearing definition — minor model, branch-set connectivity, had₂ — will be **hand-rolled**, which is exactly where Pitfall 3's dropped-connectivity slip re-enters, now with no runtime verifier to catch it. A definition of "K_k model" missing `G.Adj a b` for 2-element branch sets defines a larger parameter; `had₂ ≥ χ` for it is a weaker theorem that reads identically.
2. **Junk-value conventions:** `SimpleGraph.chromaticNumber : ℕ∞` is **noncomputable**, defined as an infimum, with χ = ⊤ iff no finite coloring and χ = 0 iff the vertex type is empty (verified against mathlib source). Consequences: (a) you cannot `#eval`/`decide` it directly — instance-level facts must go through explicit `Colorable` witnesses and lower-bound lemmas; (b) a mis-encoded instance graph (typo'd edge predicate, wrong `Fintype`/`DecidableEq` instances, empty vertex type) makes χ = 0 and many inequalities *trivially true*; (c) `ℕ∞` coercions invite statements true for the wrong reason (⊤-absorption, `0 ≤ x`).
3. **Quantifier/binding slips:** `∃` where `∀` over corpus instances; a hypothesis no instance satisfies (vacuous ∀); the Lean graph not being *byte-identical* to the certificate's graph (theorem about a cousin of the instance).
4. **`native_decide` trust inflation:** kernel `decide` on n = 301/501 instances may be infeasible, and the tempting escape adds the compiler to the trust base — `Lean.ofReduceBool`/`Lean.trustCompiler` axioms, with a documented soundness-bug history (the Lean community's own assessment during the leakage incident: with `implemented_by` in dependencies, `native_decide` was "almost certainly capable of proving False"; see the [soundness-bug thread](https://leanprover-community.github.io/archive/stream/270676-lean4/topic/soundness.20bug.3A.20native_decide.20leakage.html) and [RFC #12216](https://github.com/leanprover/lean4/issues/12216); Lean ≥ 4.29 now surfaces one axiom per native computation in `#print axioms`).

**How to avoid:**
1. **Statement/proof separation with hostile review:** all theorem *statements* live in a `Statements.lean` with zero proofs, reviewed independently of any proof work — the statement is audited as adversarially as an impossibility claim. The permitted phrase (already in PROJECT.md) is "this file compiles, and its statement says exactly X" — the audit's job is to make X true.
2. **Polarity tests for every definition** (the falsification suite, transplanted to Lean): each hand-rolled predicate ships with a provable positive control and a provable *negative* control — e.g., `hasKMinor (completeGraph 5) 5` provable AND `¬ hasKMinor (pathGraph 3) 3` provable; a `Coloring` witness giving χ ≤ 16 AND a lower-bound proof giving χ ≥ 16 on the instance. A definition with no provable negation is presumed vacuous.
3. **Golden binding:** the Lean instance graph is defined from the literal edge list, and a checked equality (edge count = 131 for n31/s1; SHA-256 of the canonical edge list matching the JSON, via a small verified encoding) ties the formal object to the corpus artifact.
4. **Axiom budget in CI:** `#print axioms` per theorem, diffed against an expected set; any appearance of `Lean.ofReduceBool`/`trustCompiler`/per-computation native axioms is a *reported, deliberate* trust expansion, never an accident. Kernel-only (`decide` with efficient `Nat`-packed adjacency encodings) is the default target; `native_decide` is an explicit, documented fallback.
5. **First task = re-verify, not re-prove:** Milestone 2 begins by making Lean the corpus's *third independent verifier* (re-check stored certificates) — a task that is non-vacuous by construction and shakes out every definition against 27 concrete instances before any general theorem is attempted. General Lean footgun catalogue: [nielsvoss/lean-pitfalls](https://github.com/nielsvoss/lean-pitfalls).

**Warning signs:**
A proof that closes suspiciously fast (`simp`/`decide` one-liners on supposedly deep statements); theorems whose hypotheses no test instance satisfies; `native_decide` appearing without a paired reporting note; statements using `ℕ∞` comparisons nobody sanity-tested on the empty graph; no negative-control lemmas anywhere in the file.

**Phase to address:**
Milestone 2 (all of it); Foundation prepares the binding surface now (canonical edge-list hashing in the certificate schema).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Truncating the ILP's optimal family to `fam[:chi]` before storing | Smaller records | Falsification Rule blind above χ (seed 137's 17-set family already discarded once); re-solving needed later | Never — store the full family + the truncation |
| Cayley records storing S but not `H_edges` | Tiny records | Certificates not self-contained; verifier must trust a reconstruction routine | Only if the verifier owns an audited `cayley_adj` AND records carry an edge-list hash; prefer storing edges |
| Assert-based checking anywhere in the trust path | Fast to write | Entire trust chain becomes a no-op under `python -O` (demonstrated) | Never in verifier/gates; fine in scratch scripts |
| Single-solver "exact" results | Half the compute | One solver's bug = unfalsifiable wrong claim in the radioactive direction | Fine for kills (verifier arbitrates); never for had₂ < χ claims |
| In-run-only verification for sweep instances (269 of 296) | Sweep speed | Nothing re-checkable without rerunning; silent dependence on generator stability | Acceptable only because Tier-2 regeneration is tested in CI; store per-instance invariant digests (ν, χ, edge-hash) to make drift detectable |
| Sharing one RNG across generate/search | One seed to record | Search outcomes coupled to generator internals; refactors flip results | Never going forward (Foundation fixes it); document that historical seeds used the coupled scheme |
| Hard-coded time budgets in code (90 s vs 60 s already inconsistent) | Simplicity | "Resistance" becomes budget-dependent and unattributable | Never — budgets are config, logged per run |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| networkx | Trusting `len(max_weight_matching(...))` semantics across versions (2.0: dict, len = 2ν; ≥2.2: set of edges, len = ν — verified against both docs) | Pin version; wrap in `matching_number()` with runtime guards: elements are H-edges, disjoint, `2*len(M) ≤ n`, `chi ≥ ceil(n/2)` |
| networkx | `maxcardinality=True` omitted (weight-optimal ≠ cardinality-optimal) | Keep `maxcardinality=True` (present in C.1) and unit-test on a graph where they differ |
| PuLP/CBC | Believing `prob.status`/objective after `timeLimit` (documented misleading-Optimal + non-integer-solution issues: [pulp#517](https://github.com/coin-or/pulp/issues/517), [Cbc#440](https://github.com/coin-or/Cbc/issues/440)) | Tri-state result; check `sol_status`; `msg=1` in exact runs so "Stopped on time" is in captured logs; recompute objective from extracted binaries and assert it equals the reported value |
| OR-Tools CP-SAT | Assuming determinism/OPTIMAL by default | Gate on `status == OPTIMAL`; record `BestObjectiveBound`; for reproducibility: fixed `random_seed`, `num_workers=1` (and version-pin — even that has had regressions: [#3943](https://github.com/google/or-tools/issues/3943)), or `interleave_search:true` for deterministic parallelism; treat model bits as non-reproducible, store them |
| OR-Tools CP-SAT | Hand-writing symmetry constraints when the solver has `symmetry_level` | Prefer solver-internal symmetry; hand constraints only from nauty-computed Aut with the assume-and-verify rule (Pitfall 4) |
| nauty `geng -t` | Assuming output labeling/order matches internal vertex conventions; assuming "triangle-free" implies "maximal triangle-free" | Parse graph6 with a tested decoder; maximality is a separate filter (`is_edge_maximal_tf`); canonical labels from nauty ≠ your generation labels — never join records across tools by vertex index |
| Python runtime | Python 3.9.6 is EOL (Oct 2025); recent networkx/OR-Tools wheels require newer interpreters (MEDIUM confidence on exact cutoffs) | Decide the interpreter version at Foundation *before* pinning the stack; CI matrix on the chosen version only |
| JSON corpus | Tuples→lists round-trip; verifying against regenerated rather than stored graphs | Verifier consumes stored `H_edges` only; canonical sorted edge lists + SHA-256 digest per record |
| Lean/mathlib | Assuming mathlib has minors/Hadwiger; `#eval`-ing `chromaticNumber` (noncomputable, ℕ∞) | Budget for hand-rolled minor theory with polarity tests; instance facts via `Colorable` witnesses and bound lemmas (Pitfall 11) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| O(\|E(G)\|²) pair–pair constraint generation (C.3 scans all pairs of G-edges) | Model *build* time exceeds solve time; memory blowup | Generate pair–pair conflicts by enumerating **4-cycles of H** (sparse: \|E(H)\| ~ n^{3/2}) instead of scanning G-edge pairs; counts must match the checksum (Pitfall 1) | G is dense (\|E(G)\| ≈ C(n,2) − n^{3/2}): fine at n ≤ 60, painful ~n = 150, infeasible to even build at n = 301/501 as coded |
| CBC on 10⁵+ binaries with quadratic constraints | Timeouts → incumbents → Pitfall 2 territory | CP-SAT backend with structural constraint generation; decompose by ω-clique seeding; accept UNRESOLVED honestly | Large-n exact escalation (Phase 3) |
| Exhaustive P0 generation at n = 12–14 | `geng -t` output volume explodes (triangle-free counts grow ~10× per vertex; maximal-TF are far fewer but you must filter to find them) | Filter maximality during generation (canonical-augmentation hooks) or use/port a dedicated maximal-triangle-free generator; verify counts against published MTF enumeration before trusting exhaustiveness (LOW confidence on exact feasibility ceiling — needs phase research) | Somewhere n = 13–15 for generate-then-filter |
| Heuristic budget as constant while n scales | Large-n instances "fail" heuristically and flood the exact queue | Budget scaling policy in config (e.g., per-restart accounting), logged | n ≥ 200 with 60–90 s budgets |
| Verifier pairwise check O(k²·4) per model — trivial — but corpus-wide re-verification in CI grows linearly with corpus | CI time creep → temptation to skip re-verification | Keep full re-verification; it's seconds per thousand certificates — never sample it | Only if corpus reaches ~10⁶ instances (not projected) |

## Epistemic Integrity Mistakes

(Domain analogue of the security section: what can corrupt the trust chain.)

| Mistake | Risk | Prevention |
|---------|------|------------|
| Mutating stored certificates in place ("fixing" a record by hand) | Corpus stops being evidence; Tier-1 replay breaks silently | Append-only corpus + content hashes; edits only via regeneration + re-verification; corpus diffs reviewed like code |
| Falsification harness executing submitted impossibility-argument *code* with corpus write access | A buggy/malicious argument mutates the falsification suite that judges it | Run arguments in a sandbox with read-only corpus mount; harness re-hashes corpus before/after every run |
| Status-vocabulary drift ("not found" → "resistant" → "hard instance" in prose) | Heuristic gaps read as mathematical signals; the exact sin the program exists to prevent | Fixed enum in schema (Pitfall 10.5); release notes generated from the ledger, not written free-form |
| Counting gate-kills and model-kills in one headline number | "X/X killed" silently changes meaning between reports | Separate ledgers; the headline format is pinned in the reporting template |
| Verifier version not recorded with verification events | "Verified" claims not attributable after verifier evolves | Record verifier version+hash in each verification event; re-verify corpus on verifier changes (cheap) |

## "Looks Done But Isn't" Checklist

- [ ] **`ilp_had2` port:** looks done when it returns numbers — verify it *gates on proven-optimal status*, returns the tri-state, stores both bounds, and stores the **untruncated** optimal family
- [ ] **Verifier:** looks done when 27/27 pass — verify it passes the *adversarial mutant suite* (rejects every known-bad model with the right reason), runs green under `python -O`, imports nothing from generator/searcher, and consumes only stored JSON
- [ ] **χ exactness:** looks done because blossom is exact — verify certificates carry the matching **and a Tutte–Berge witness U**, and the verifier checks both directions from the JSON
- [ ] **Corpus regeneration:** looks done when files appear — verify Tier-1 (all stored certificates re-verify byte-for-byte semantics) *and* Tier-2 (per-family (n, seed) spot regeneration matches stored edge-hashes) in CI
- [ ] **CP-SAT backend:** looks done when it agrees with CBC on a few instances — verify the *connectivity-of-branch-sets* mechanism explicitly (Pitfall 3) and the nightly random differential battery is wired
- [ ] **Criticality gate:** looks done on the n = 31 sweep — verify n = 32/χ = 16 (corpus row 4) passes the predicate
- [ ] **Falsification runner:** looks done when it reports 296 declines — verify engagement telemetry > 0, the synthetic wrong-argument positive control gets caught, and k-levels above χ are exercised (seed-137's k = 17)
- [ ] **Symmetry breaking:** looks done when solve times drop — verify had₂(SB) == had₂(no-SB) on the battery and the impossibility branch *reruns without SB*
- [ ] **Seeding:** looks done when runs repeat on one machine — verify stage-independent streams (edit the generator internals in a scratch branch: heuristic outcomes must not change) and str-seed derivation (PYTHONHASHSEED-immune)
- [ ] **Lean statements (M2):** look done when sorry-free — verify polarity tests exist per definition, `#print axioms` matches the expected set, and the instance binding hash-checks against the JSON

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Encoding bug found after corpus built | LOW for kills / HIGH for any "<" claims | Verified-existence certificates are self-justifying — re-run the verifier suite and they stand. Anything derived from solver *values* without witnesses (had₂-exact numbers, UNRESOLVED/RESISTANT labels) is re-solved with the fixed encoding. This asymmetry is why witnesses are stored for everything. |
| Verifier bug found | HIGH (bounded) | Fix + extend the adversarial suite with the escaped case; re-verify the entire corpus (minutes); publish an errata entry in the results log; bump verifier version in all records |
| False RESISTANT discovered (seed-137 pattern) | LOW | Named protocol already exists: fresh independent RNG streams → 5–10× budget → exact ILP with status gating → if killed, corpus append + a searcher-bug postmortem documenting *which assumption* hid the model |
| Unsound symmetry breaking discovered | MEDIUM | All SB-on *kills* stand (verified models). All SB-on values < χ and UNRESOLVED labels re-run without SB; audit which survivor-protocol entries consumed them |
| Statement vacuity found in Lean after "completion" | MEDIUM | The corpus and Python verifier are unaffected (Lean is the third leg, not the root); fix the statement, re-run polarity tests, re-audit `Statements.lean`, note in the writeup that prior compile-success certified nothing — which the reporting discipline already assumed |
| Library-drift breakage (networkx/solver semantics) | LOW if guards exist | Runtime guards fail loudly at first import/run; repin, rerun CI corpus reproduction; guards are the difference between a loud LOW and a silent HIGH |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. Missing/inverted conflict class | Foundation | Structural-checksum asserts on; brute-force differential green on tiny graphs; seed-137 regression (had₂ = 17) pinned |
| 2. Incumbent-as-optimum | Foundation (interface), Phase 3 (two-solver rule) | Tri-state type makes "< χ from LOWER_BOUND" unrepresentable; grep CI for `timeLimit` without status gating |
| 3. Implicit connectivity lost in re-encoding | Foundation (CP-SAT), Phase 2/3 (size-3), Milestone 2 (defs) | Cross-encoding differential; verifier rejects disconnected pairs; Lean polarity tests |
| 4. Unsound symmetry breaking | Phase 3 | SB on/off differential in battery; impossibility branch reruns without SB (code-path assertion) |
| 5. Fixed-profile false resistance | Foundation (searcher fix), Phase 2 (escalation runbook) | Searcher can represent the stored seed-137 model; RESISTANT label only writable by exact-method code path |
| 6. Reproducibility rot | Foundation | CI corpus reproduction (Tier 1 + Tier 2); stage-stream independence test; version guards |
| 7. Verifier trust root | Foundation, Milestone 2 (third leg) | Adversarial mutant suite; `python -O` CI job; import-independence lint; Tutte–Berge witnesses in schema |
| 8. Falsification runner vacuity | Phase 3 (runner), Foundation (full-family storage) | Engagement telemetry; synthetic wrong-argument control caught; k = 17 seed-137 case exercised |
| 9. Non-monotone invariant | Phase 3 (audit), Foundation (falsifier tool) | Falsifier catches rank/spectral/χ on ≤ 5-vertex counterexamples in CI; allowlist enforced in survivor protocol |
| 10. Gate wrong-reason kills | Phase 2, Foundation (conventions) | Gate witnesses replayable; n = 32 criticality unit test; ERROR/FAIL separation visible in ledger |
| 11. Lean statement vacuity | Milestone 2, Foundation (binding hashes) | Statements file independently reviewed; polarity tests; axiom budget in CI; corpus re-verified in Lean first |

## Sources

**Primary (project):**
- `.planning/PROJECT.md` — governing constraints (Asymmetry Principle, Falsification Rule, Monotonicity Audit, reporting discipline)
- `.planning/reference/alpha2-program-source.md` — Appendix C toolkit (all encoding claims checked against `ilp_had2`, `verify_model`, `solve`, `initial_state`, `investigate_137.py`); Appendix D (seed-137 facts: χ = 16, ω = 14, had₂ = 17, 9-pair/7-singleton model; stored-certificate table incl. n = 32 row)

**Verified by direct computation for this research (HIGH):**
- rank A(C₄) = 2 → contract → rank A(K₃) = 3 (adjacency rank not minor-monotone)
- λ_max(subdivided K₄) ≈ 2.8558 < 3 = λ_max(K₄) with K₄ a minor (spectral radius not minor-monotone)
- χ(K₃,₃) = 2 → contract matching → χ(K₃) = 3 (χ not minor-monotone)
- `python -O` strips an assert-based verifier to a no-op that accepts invalid models
- PYTHONHASHSEED reorders str-set iteration across runs; int-tuple sets stable (implementation detail, not guaranteed)
- had₂(C₅) = 3 with all optima spanning → "vertex 0 unused" SB fabricates had₂ = 2 < χ

**Library/solver documentation and issue trackers (HIGH–MEDIUM):**
- [networkx 2.0 `max_weight_matching` docs](https://networkx.org/documentation/networkx-2.0/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) (returns dict) vs [networkx 2.2 docs](https://networkx.org/documentation/networkx-2.2/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) (returns set) and [current stable docs](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html)
- PuLP/CBC status and time-limit issues: [pulp#517](https://github.com/coin-or/pulp/issues/517), [Cbc#440](https://github.com/coin-or/Cbc/issues/440), [pulp discussion #486](https://github.com/coin-or/pulp/discussions/486), [pulp#668](https://github.com/coin-or/pulp/issues/668)
- CP-SAT determinism: [or-tools#3943](https://github.com/google/or-tools/issues/3943), [or-tools#3948](https://github.com/google/or-tools/issues/3948), [or-tools#3590](https://github.com/google/or-tools/issues/3590), [OR-Tools CP solver docs](https://developers.google.com/optimization/cp/cp_solver)
- mathlib: [`SimpleGraph.chromaticNumber` source](https://github.com/leanprover-community/mathlib4/blob/master/Mathlib/Combinatorics/SimpleGraph/Coloring/Vertex.lean) (noncomputable, ℕ∞, ⊤/0 conventions verified); no minor module found ([Minor page 404](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Minor.html)) — re-verify at Milestone 2 start
- Lean native_decide trust base: [soundness-bug thread](https://leanprover-community.github.io/archive/stream/270676-lean4/topic/soundness.20bug.3A.20native_decide.20leakage.html), [RFC #12216 (one axiom per native computation)](https://github.com/leanprover/lean4/issues/12216), [Lean validating-proofs reference](https://lean-lang.org/doc/reference/latest/ValidatingProofs/), [nielsvoss/lean-pitfalls](https://github.com/nielsvoss/lean-pitfalls)

**Minor-monotonicity literature (HIGH):**
- [van der Holst, Lovász, Schrijver — "The Colin de Verdière graph parameter" (survey)](https://ir.cwi.nl/pub/1257/1257D.pdf) — μ minor-monotone; Strong Arnold Property
- [Schrijver — "Minor-monotone graph invariants" (survey)](https://ir.cwi.nl/pub/2157/2157D.pdf) — the μ-type minor-monotone family
- [Springer: On the Relation Between Two Minor-Monotone Graph Parameters](https://link.springer.com/article/10.1007/PL00009821)

---
*Pitfalls research for: Hadwiger α = 2 hunt-and-certify harness (exact solvers + minor theory + Lean)*
*Researched: 2026-07-21*
