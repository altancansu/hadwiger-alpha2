# The Transfer Lemma (in-repo re-derivation)

**Requirement:** POOL-0 · **ROADMAP:** SC3 · **Phase:** 07 P0 CDM frontier
**Executable backing:** `tests/pool/cdm/test_transfer_lemma.py`,
`tests/pool/cdm/test_a3_coverage.py`
**Status of this document:** states *exactly* what it proves. The two ingredients
(monotonicity, edge-minimal correspondence) are proven here; CLWY Lemma 2.5 is
*cited*. The former residual **A3** (the *reach* of the connected-frontier claim) is
now **discharged** two ways: a **proven-for-all-n lemma** (§5, the two-clique / single
cross-edge argument) covers exactly the graphs monotonicity misses, and an
**exhaustive superset enumeration** (`test_a3_coverage`) verifies the *exact* A3
statement — every connected `α=2` graph holds CDM — for **all `n ≤ 12`**. What
remains is *not* A3 but the pre-existing frontier target: that the connected
MTF-complements themselves hold CDM (CLWY, verified `n ≤ 11`; Phase-7-adjudicated at
`n = 12,13,14`).

---

## 0. Notation and the CDM property

Fix `n ≥ 3`. For a graph `G` on vertex set `[n]` let `H := Ḡ` be its complement.
By the α=2 dictionary of this program, `α(G) = 2 ⟺ H is triangle-free (with ≥1 edge)`,
and `χ(G) = n − ν(H)`.

A **matching** `M` of `G` is a set of pairwise vertex-disjoint edges; `V(M)` is the set
of covered vertices. Following Costa–Luu–Wood–Yip (CLWY) `[arXiv:2512.17114 §1]`:

- `M` is **connected** iff for every two edges `e, f ∈ M`, the vertex-sets `V(e)` and
  `V(f)` are *adjacent in G* — i.e. at least one of the four cross pairs is an edge of `G`.
  For pairwise-disjoint edges this is exactly the statement that the size-2 branch sets
  `e` and `f` are adjacent in a `K_{|M|}`-minor model.
- `M` is **dominating** iff every vertex `w ∈ V(G) ∖ V(M)` is *adjacent to each edge*
  `e = {a,b} ∈ M`, where "adjacent to an edge" means adjacent to **≥1 endpoint**
  (`w ∈ adj(a) ∪ adj(b)`). This is Assumption **A1** of `07-RESEARCH.md`, empirically
  locked by the n≤11 definition gate `test_cdm_n_le_11.py`.

**CDM(G)** (CLWY Conjecture 10, restricted to `α(G)=2`) is the decidable predicate:
*"`G` has a non-empty connected dominating matching."* The executable arbiter is
`has_cdm(adj, n)` (`src/alpha2/pool/cdm/reference.py`), cross-checked by `cdm_cpsat`.

The program cares about CDM because `CDM ⟹ SHC_{α=2} ⟹ Hadwiger_{α=2}` (CLWY Thm 2.10).
A CDM *failure* is **not** a Hadwiger counterexample — CDM is sufficient, not necessary.

---

## 1. Statement of the transfer lemma

> **Transfer (target).** To establish CDM for every **connected** `α=2` graph on `n`
> vertices, it suffices to verify CDM on the complements of the maximal-triangle-free
> (MTF) graphs on `n` vertices — equivalently, on the **edge-minimal** `α=2` graphs,
> equivalently on the complements of the connected triangle-free diameter-2 graphs —
> **provided each such connected complement holds CDM**. These complements are exactly
> the outputs of `geng -ctq n | pickg -Z2`.

The lemma is carried by two ingredients (§2, §3) and one carve-out (§4). §5 **closes**
the former residual (**A3** — the *reach* of the connected-frontier claim): it proves
the direct lemma that covers exactly the graphs monotonicity misses (the `P4`-class),
and records the exhaustive-superset gate that verifies the exact A3 statement in range.

---

## 2. Ingredient A — CLWY Lemma 2.5 (cited)

**Lemma 2.5 `[CITED: arXiv:2512.17114, Lemma 2.5]`.** For a triangle-free graph `H` on
`≥3` vertices the following are equivalent (TFAE):

1. `H` is **edge-maximal triangle-free** (adding any non-edge creates a triangle);
2. `H` has **diameter 2**;
3. the complement `Ḡ := H̄ = G` has `α(G)=2` and is **edge-minimal**;
4. the complement `G` has **no dominating edge**.

**Consequence used here.** `pickg -Z2` (diameter exactly 2) applied to a `geng -ctq`
stream (connected, triangle-free, quiet) emits **exactly** the connected MTF graphs `H`;
their complements `G = H̄` are **exactly** the edge-minimal `α=2` graphs. Hence
adjudicating CDM on the `pickg -Z2` outputs = adjudicating CDM on every edge-minimal
`α=2` graph at `n`.

**In-repo corroboration (empirical, not a re-proof of Lemma 2.5).** The repo's
independent predicate `is_edge_maximal_tf(adj, n)` (`src/alpha2/generators/tfp.py`)
implements (1) directly ("every non-edge closes a triangle"), and
`test_lemma_2_5_edge_maximal_iff_diameter_2` checks `(1) ⟺ (2)` over the **full** set of
134 connected MTF survivors at `n ≤ 11` (embedded oracle, no `geng` at fixture-build).
Live generation reproduced the counts `61 (n=11) / 147 (n=12) / 392 (n=13)`, matching
`pickg -Z2` and OEIS A216783. This corroborates the `(i)⟺(ii)` edge of Lemma 2.5 on the
frontier we actually adjudicate; it does not replace the citation.

---

## 3. Ingredient B — CDM edge-addition monotonicity (proven in-repo)

> **Theorem (monotonicity of CDM under edge addition).** Let `G` be a graph and let
> `G' = G + e'` be `G` with one extra edge `e'` on the same vertex set. If `M` is a
> non-empty connected dominating matching of `G`, then the *same* set `M` is a non-empty
> connected dominating matching of `G'`. Hence **CDM(G) ⟹ CDM(G')**.

**Proof.** Write `E(G) ⊆ E(G')` (the vertex set is unchanged and only edges are added).

*`M` is still a non-empty matching.* `M ⊆ E(G) ⊆ E(G')`, and pairwise vertex-disjointness
is a property of the edge *set* `M`, which is unchanged. Non-emptiness is unchanged.

*`M` is still connected.* Connectedness requires, for each pair `e, f ∈ M`, that at least
one cross pair between `V(e)` and `V(f)` be an edge. Any such witnessing edge lived in
`E(G) ⊆ E(G')`, so it survives. Adding `e'` can only create additional cross adjacencies;
it can destroy none. Connectedness is an **adjacency-positive** condition.

*`M` is still dominating.* `V(M)` is unchanged (same `M`), so the set of vertices to
dominate, `V(G) ∖ V(M)`, is unchanged. Each such `w` was adjacent (≥1 endpoint) to each
`e ∈ M` in `G`; that adjacency lies in `E(G) ⊆ E(G')` and persists. `e'` can only add
adjacencies. Domination is likewise **adjacency-positive**. ∎

**Corollary (finite iteration).** By induction on the number of added edges, if `G₀ ⊆ G`
on the same vertex set and `CDM(G₀)` holds, then `CDM(G)` holds. Thus CDM is **monotone**
along spanning-supergraph chains: `G₀ ⊆ G₁ ⊆ … ⊆ G`.

**Contrapositive / why only edge-minimal graphs need checking.** Every `α=2` graph `G` is
a spanning supergraph of some **edge-minimal** `α=2` graph `G₀` (delete `G`-edges while
`α` stays `2`, i.e. add edges to `H = Ḡ` while it stays triangle-free, until `H` is
maximal-triangle-free; by Lemma 2.5(3) the result `G₀ = H̄*` is edge-minimal `α=2`). If
**that** `G₀` holds CDM, monotonicity lifts it to `G`. So the only graphs that must be
adjudicated directly are the edge-minimal ones — the MTF-complements of §2.

The executable analog is `test_cdm_monotone_under_edge_addition`: starting from `C₅`
(which holds CDM), adding *every* `α`-preserving non-edge individually preserves
`has_cdm(...) is not None`.

---

## 4. The connected-vs-disconnected carve-out (Open Q1 — resolved as a carve-out)

Monotonicity flows **upward** (minimal ⟹ supergraphs). So if an edge-minimal `α=2` graph
`G₀` *fails* CDM, it certifies nothing about its supergraphs. Some edge-minimal `α=2`
graphs do fail CDM — and they do so **legitimately**, not as Hadwiger events.

**Classification of the disconnected edge-minimal graphs (proven).**
Let `G₀` be `α=2` and **disconnected**.

- `G₀` has exactly **two** components: three components would let us pick one vertex from
  each, giving an independent set of size 3, contradicting `α = 2`.
- Each component is a **clique**: a non-edge inside one component together with any vertex
  of the other component is an independent triple, again contradicting `α = 2`.

Hence `G₀ = K_a ⊔ K_b` for some `a, b ≥ 1` with `a + b = n`. Its complement is the complete
bipartite graph `K_{a,b}`, which is triangle-free and edge-maximal (diameter 2) — so
`K_a ⊔ K_b` is indeed edge-minimal `α=2`, and appears in the `pickg -Z2` stream via the
complete-bipartite MTF complements. **Conversely** every `K_a ⊔ K_b` (with `a,b ≥ 2`)
fails CDM: an edge inside `K_a` cannot dominate any vertex of `K_b` (no cross adjacency),
and a two-edge matching with one edge in each clique is *not connected* (the two vertex
sets have no cross edge). `has_cdm(K_a ⊔ K_b) = None` — verified in `test_cdm_n_le_11.py`
(the `105` connected instances hold; the `29` disconnected `K_a ⊔ K_b` complements fail).

**Carve-out statement.** The disconnected edge-minimal `α=2` graphs are **exactly**
`K_a ⊔ K_b`. CLWY Conjecture 10 hypothesizes **connected** `G`, so these are *out of scope*
for the connected frontier: a `K_a ⊔ K_b` CDM-failure is **catalogued as expected and
excluded**, and must **never** be escalated as a Hadwiger event (`07-RESEARCH.md`
Pitfall 1). The operational enforcement is the `07-06` complement-connectivity classifier.

---

## 5. Closing the reach residual A3 (proven lemma + exhaustive in-range gate)

The clean target of §1 — *"CDM on the MTF-complements ⟹ CDM for **every** connected
`α=2` graph"* — needs one step beyond §2–§4, historically flagged as **A3**:

> **A3 (as originally phrased, `07-RESEARCH.md` Assumptions Log).** Every *connected*
> `α=2` graph `G` admits a **connected** edge-minimal reduction `G₀ ⊆ G`, so that §3
> monotonicity lifts `CDM(G₀)` — known for connected MTF-complements — up to `G`.

**That phrasing is literally FALSE, and `P4` disproves it.** Consider `G = P4` (the path
`0–1–2–3`): connected, `α(P4)=2`, and it **holds CDM**. Yet the *only* edge-minimal `α=2`
graph below `P4` is `2K₂ = K₂ ⊔ K₂` (its complement `P̄4` has diameter 3, so `P4` is **not**
an MTF-complement; the unique maximal-triangle-free extension of `P̄4` is `C₄`, whose
complement is `2K₂`), and `2K₂` **fails** CDM (§4). So monotonicity from the checked
connected MTF-complements lifts **nothing** to `P4`. Its CDM is true but must come from a
*different* argument. The real content of A3 is therefore not "a connected reduction
always exists" (it need not) but **"the graphs with only disconnected reductions hold CDM
anyway."** That is what we now prove.

### 5.1 The direct lemma (PROVEN for all `n`)

> **Lemma A3 (two-clique closure).** Let `G` be a **connected** graph with `α(G)=2` that
> admits **at least one disconnected** edge-minimal `α=2` reduction. Then `G` holds CDM;
> concretely, **any single edge of `G` between the two cliques is, by itself, a connected
> dominating matching.**

**Proof.** By §4, a disconnected edge-minimal reduction of `G` is `G₀ = K_a ⊔ K_b`, whose
complement is the *complete* bipartite `K_{a,b}`. Since reduction adds edges to `H := Ḡ`
until maximal-triangle-free, `H ⊆ K_{a,b}`; hence **`H` is bipartite** with parts
`A` (`|A|=a`), `B` (`|B|=b`). Complementing, `A` and `B` are each **cliques of `G`**, and
they partition `V(G)`. (Equivalently: `G` is two cliques joined by the cross edges that are
the *non*-edges of `H` between `A` and `B`. Note `α(G)=2` is automatic — any independent
set meets each clique in `≤1` vertex.)

`G` is connected, so there is at least one **cross edge** `e = {u, v}` with `u ∈ A`,
`v ∈ B` (a single cross edge already connects everything, since `u` reaches all of `A` and
`v` reaches all of `B` inside their cliques; with no cross edge `G` would be `K_a ⊔ K_b`,
disconnected). Take `M := {e}`.

- **Non-empty:** `M` has one edge. ✔
- **Connected:** connectedness constrains *pairs* of edges; `|M| = 1`, so it holds
  vacuously. ✔
- **Dominating:** let `w ∉ {u, v}`. Then `w ∈ A` or `w ∈ B`. If `w ∈ A`, then `w ∼ u`
  (both in the clique `A`); if `w ∈ B`, then `w ∼ v` (both in the clique `B`). Either way
  `w` is adjacent to `≥1` endpoint of `e`, i.e. dominated by the edge `e`. ✔

Hence `M = {e}` is a non-empty connected dominating matching, so `CDM(G)` holds. ∎

This is exactly the `P4` mechanism the old §5 pointed at, made rigorous and *general*:
`P4 = K₂(01) ∪ K₂(23)` with the single cross edge `1–2`, and indeed `M = {1–2}` alone
dominates `0` (via `1`) and `3` (via `2`). The lemma **covers precisely the class
monotonicity misses**: every connected `α=2` graph either has a *connected* edge-minimal
reduction (→ §3 lifts CDM from the connected MTF-complement frontier) **or** has *only*
disconnected reductions (→ it is two-clique, and Lemma A3 gives CDM directly). No connected
`α=2` graph falls outside both cases. The **danger case** flagged in review — two large
cliques joined by a single sparse cross edge — is exactly where the lemma is *strongest*:
that lone cross edge dominates both cliques wholesale, so a *one-edge* matching already
certifies CDM (no need for a simultaneously connected-and-dominating larger matching).

**Machine corroboration (not the proof, a check of it).** Over the full `geng -tq n`
triangle-free stream for all `n ≤ 11`, every one of the **39,311** connected two-clique
`α=2` graphs has the property that *every* cross edge is, as a singleton, a dominating
matching (`has_cdm`-consistent; 0 exceptions).

### 5.2 The exact A3 statement, verified exhaustively in range

Independently of the prose, `tests/pool/cdm/test_a3_coverage.py` checks A3's *exact*
statement head-on. For each `n` it enumerates the **full triangle-free superset**
`geng -tq n` (NOT the `pickg -Z2` maximal subset — this is the whole `α=2` universe, the
edge-minimal graphs *and* every `P4`-like graph above a disconnected floor), complements
each `H` with `≥1` edge to `G`, and asserts every **connected** `G` satisfies
`has_cdm(G) is not None`. Result — **every connected `α=2` graph holds CDM**:

| `n` | connected `α=2` graphs | held CDM |
|----:|-----------------------:|---------:|
| 4–10 | 14,615 | all |
| 11 | 105,065 | all |
| 12 | 1,262,173 | all |

`n ≤ 11` runs as the default gate (matching CLWY's verified range); `n = 12` is behind the
`slow` marker. **Total: 1,381,853 connected `α=2` graphs at `n ≤ 12`, every one holds
CDM.** A single connected failure would raise loudly with its graph6 — none occurred.

### 5.3 What is now true (and the honest remaining item — not A3)

A3's *reach* question is **discharged**: §5.1 proves for **all `n`** that the graphs
monotonicity cannot reach (only-disconnected-reduction, i.e. two-clique) hold CDM; §5.2
verifies the whole connected `α=2` frontier exhaustively for `n ≤ 12`. The connected-frontier
claim therefore reduces cleanly to a *single* target: **that the connected MTF-complements
themselves hold CDM.** That is the pre-existing CLWY frontier (verified `n ≤ 11`, all 105
connected MTF-complements holding; `test_cdm_n_le_11.py`), and it is exactly what Phase 7
adjudicates and stores at `n = 12,13,14` (the **1,813 MTF-complements**). It is **not** A3
and was never in A3's scope; A3 was only ever about whether monotonicity's reach is
complete, and §5.1–§5.2 settle that.

**Author-check (non-blocking).** Whether CLWY `[arXiv:2512.17114]` states this coverage
reduction in an equivalent form is not resolvable from the in-repo citation text (Lemma 2.5
and Conjecture 10 are what the doc cites); the two-clique lemma above is proven **in-repo
and stands on its own**, so no external certification is needed to discharge A3.

---

## 6. What this file establishes (exact statement)

- **Proven:** CDM edge-addition **monotonicity** (§3); every `α=2` graph is a spanning
  supergraph of an edge-minimal `α=2` graph; the disconnected edge-minimal `α=2` graphs
  are exactly `K_a ⊔ K_b` and legitimately fail CDM (§4); **Lemma A3 (§5.1) — for all `n`,
  every connected `α=2` graph whose only edge-minimal reductions are disconnected is a
  two-clique graph and holds CDM via a single cross edge.**
- **Cited (not re-proven):** CLWY **Lemma 2.5** four-way TFAE `[arXiv:2512.17114]`,
  empirically corroborated `(i)⟺(ii)` over all 134 `n ≤ 11` MTF survivors.
- **Consequence:** every connected `α=2` graph holds CDM **iff** the connected
  MTF-complements do — graphs with a connected edge-minimal reduction by §3 monotonicity,
  graphs with only disconnected reductions by §5.1 Lemma A3. The reach is now **complete**,
  not conditional on an uncertified coverage step.
- **A3 (the reach residual) — DISCHARGED.** Proven for all `n` (§5.1) and, as its exact
  statement, verified exhaustively for **all `n ≤ 12`** by superset enumeration
  (`test_a3_coverage`: 1,381,853 connected `α=2` graphs, every one holds CDM; §5.2).
- **Remaining item (pre-existing, *not* A3):** that the connected MTF-complements hold CDM
  for all `n` — CLWY's result verified `n ≤ 11`, Phase-7-adjudicated at `n = 12,13,14`.

*This file states exactly what it proves. The connected-frontier reach is now fully
established (proven lemma + exhaustive-in-range gate); the only open target is the CLWY
MTF-complement frontier itself, which Phase 7 adjudicates.*
