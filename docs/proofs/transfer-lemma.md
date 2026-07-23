# The Transfer Lemma (in-repo re-derivation)

**Requirement:** POOL-0 · **ROADMAP:** SC3 · **Phase:** 07 P0 CDM frontier
**Executable backing:** `tests/pool/cdm/test_transfer_lemma.py`
**Status of this document:** states *exactly* what it proves. The two ingredients
(monotonicity, edge-minimal correspondence) are proven here; CLWY Lemma 2.5 is
*cited*; the completeness of the connected-frontier claim rests on **Assumption A3**,
which is flagged below as an author-read residual and is **not** claimed as certified.

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

The lemma is carried by two ingredients (§2, §3) and one carve-out (§4). §5 states the
residual (**A3**) precisely and exhibits the concrete witness (`P4`) that makes A3
non-trivial — the single point on which the *connected-frontier* completeness turns.

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

## 5. Residual: Assumption A3 (author-read pending — NOT certified here)

The clean target of §1 — *"CDM on the MTF-complements ⟹ CDM for **every** connected
`α=2` graph"* — needs one more step beyond §2–§4:

> **A3 (`07-RESEARCH.md` Assumptions Log).** The disconnected-complement carve-out
> `K_a ⊔ K_b` is the **only** obstruction; equivalently, every *connected* `α=2` graph `G`
> admits a **connected** edge-minimal reduction `G₀ ⊆ G` (so that §3 monotonicity lifts
> `CDM(G₀)` — known to hold for connected MTF-complements — up to `G`).

**This document does not prove A3, and does not assert it is externally certified.**
It is proven here only that:

- (§3) monotonicity is valid, and
- (§4) the disconnected edge-minimal graphs are precisely `K_a ⊔ K_b`.

**Why A3 is non-trivial — a concrete witness.** Consider `G = P4` (the path `0–1–2–3`).
`P4` is connected with `α(P4)=2`, and it **holds CDM** (`has_cdm` returns the perfect
matching `{01, 23}`, whose two edges are joined by the edge `1–2`). Yet the *only*
edge-minimal `α=2` graph below `P4` is `2K₂ = K₂ ⊔ K₂` (its complement `P̄4` has diameter 3,
so `P4` is itself **not** an MTF-complement; the unique maximal-triangle-free extension of
`P̄4` is `C₄`, whose complement is `2K₂`). And `2K₂` **fails** CDM (§4). So for `P4`,
monotonicity from the *checked* connected MTF-complements lifts **nothing** — its CDM is
true but is *not* delivered by the §3 argument. Every step of this is machine-checked in
`tests/pool/cdm/test_transfer_lemma.py` reasoning and reproducible via `has_cdm`.

`P4` sits squarely inside A3's scope: it is a connected `α=2` graph whose forced
edge-minimal reduction is disconnected. A3 asserts such graphs are nonetheless covered
(their CDM established by other means, or such reductions never obstruct the frontier
claim). **That assertion is the single residual research statement requiring the author's
eyes** before any *external* connected-frontier claim is published.

**Correctness backstop (independent of the prose).** The hard gate is empirical: the
n≤11 definition gate (`test_cdm_n_le_11.py`) reproduces CLWY's published result — **all
134** MTF-complements at `n ≤ 11` decide as expected (105 connected hold CDM; 29
`K_a ⊔ K_b` fail), matching CLWY's all-connected-`α=2`-hold-CDM verification. What Phase 7
*adjudicates and stores* at `n = 12,13,14` is CDM on the **1,813 MTF-complements**
themselves; the transfer lemma is the *warrant* for why those instances are the right
ones to check, with A3 the flagged residual on the reach of "every connected graph."

---

## 6. What this file establishes (exact statement)

- **Proven:** CDM edge-addition **monotonicity** (§3); every `α=2` graph is a spanning
  supergraph of an edge-minimal `α=2` graph; the disconnected edge-minimal `α=2` graphs
  are exactly `K_a ⊔ K_b` and legitimately fail CDM (§4).
- **Cited (not re-proven):** CLWY **Lemma 2.5** four-way TFAE `[arXiv:2512.17114]`,
  empirically corroborated `(i)⟺(ii)` over all 134 `n ≤ 11` MTF survivors.
- **Consequence:** CDM verified on the connected MTF-complements at `n` lifts, by
  monotonicity, to every connected `α=2` graph **that possesses a connected edge-minimal
  reduction**.
- **Residual (Assumption A3, author-read pending, non-blocking):** that this covers
  *every* connected `α=2` graph. The witness `P4` shows A3 is non-trivial; the empirical
  n≤11 definition gate is the correctness backstop. No external certification is claimed.

*This file states exactly what it proves; the reach of the connected-frontier claim is
bounded by Assumption A3, which remains an author-read item.*
