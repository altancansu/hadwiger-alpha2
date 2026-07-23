# Phase 7: P0 — CDM Frontier - Research

**Researched:** 2026-07-22
**Domain:** Exact combinatorial adjudication of the CDM property over exhaustively-generated maximal-triangle-free graphs (α=2 frontier), with dual-checker (DFS + CP-SAT) agreement and per-instance certificates
**Confidence:** HIGH (CDM/SHC definitions quoted from the source paper; generation counts reproduced live; existing interfaces read from source)

> **No CONTEXT.md exists for this phase** — Phase 7 has not yet been through `/gsd:discuss-phase` (STATE.md: "ready to discuss Phase 7"). This research therefore has no locked user decisions to honor; it treats the ROADMAP success criteria + POOL-0 as the scope and flags the decisions the planner/discuss step must confirm (see Assumptions Log + Open Questions). If a CONTEXT.md is later produced, its `## Decisions` override anything here.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| POOL-0 | P0 CDM frontier — exhaustively generate the 1,813 maximal-triangle-free graphs at n=12–14 (`geng -ctq \| pickg -Z2`, cross-checked vs OEIS A216783 and a second generator), run an exact CDM checker (DFS reference + CP-SAT cross-check), prove the transfer lemma in-repo, extend the verified CDM frontier past n≤11 (stretch ≤17). | CDM/SHC definitions pinned from arXiv:2512.17114 (§ "The CDM Property" below); generation pipeline + counts reproduced live (61/147/392 confirmed, 1,274 authoritative from OEIS); transfer lemma re-derived from Lemma 2.5 + edge-addition monotonicity; certificate integration mapped against `corpus/verifier.py` + `corpus/schema.py`; DFS + CP-SAT specs given; escalation wired to the existing battery. |
</phase_requirements>

## Summary

Phase 7 is the program's first new science: exactly adjudicate the **CDM property** (Costa–Luu–Wood–Yip, arXiv:2512.17114) on every connected α=2 graph at n=12,13,14, pushing the literature's computer-verified frontier past n≤11. The work has four load-bearing parts, and the research resolves all four to an implementable spec.

**(1) What CDM is.** `[CITED: arxiv.org/abs/2512.17114]` A graph G with α(G)=2 has the CDM property iff it has a **non-empty connected dominating matching**: a set M of vertex-disjoint edges that is *connected* (every two edges of M have adjacent vertex-sets in G — i.e. M's edges are pairwise linked, which is exactly a K_{|M|} minor of size-2 branch sets) and *dominating* (every vertex outside V(M) is adjacent to each edge of M). CDM ⟹ SHC_{α=2} ⟹ Hadwiger_{α=2}, where SHC_{α=2} (Conjecture 8) is "G has a K_{χ(G)}-model with all branch sets of size ≤ 2" — which is *exactly* the had₂ = χ property the repo's dual-backend already decides. So CDM is a stronger, purely combinatorial sufficient condition, and its "positive" witness is a tiny, hand-checkable object.

**(2) The transfer lemma.** `[CITED: arxiv.org/abs/2512.17114 Lemma 2.5]` For a triangle-free graph on ≥3 vertices, edge-maximal-triangle-free ⟺ diameter 2 ⟺ its complement has α=2 and is **edge-minimal** ⟺ its complement has no dominating edge. Combined with the fact that **CDM is monotone under adding edges to G** (a connected dominating matching survives every edge addition), verifying CDM on the edge-minimal α=2 graphs — i.e. the complements of the maximal-triangle-free (MTF) graphs — establishes CDM for *all* α=2 graphs at that n. `geng -ctq | pickg -Z2` generates exactly those MTF graphs. **One genuine subtlety** (Open Q1) the in-repo proof must dispatch: some edge-minimal graphs are disconnected (two cliques, complement = complete bipartite) and can *fail* CDM without being counterexamples, because the conjecture hypothesizes connected G.

**(3) Generation is verified.** Live runs reproduced the MTF counts exactly: **n=11→61, n=12→147, n=13→392** via `geng -ctq n | pickg -Z2`; n=14→**1,274** is authoritative (OEIS A216783; a partial-shard run is consistent). Total 147+392+1,274 = **1,813**. An independent Python edge-maximal filter over the raw `geng -ctq` stream agreed exactly (61/147) — but is too slow past n≈12 in networkx (n=13 timed out on 20.8M graphs), confirming CLAUDE.md's "keep the C filter in the pipe" rule.

**(4) Certificate integration honors the Asymmetry Principle.** CDM-HOLDS = existence → store the witness matching M (graph6 provenance already exists in the schema) + verify it with a new stdlib-only `verify_cdm_witness` leg mirroring the frozen trust root's discipline. CDM-FAILS = impossibility → RADIOACTIVE: requires exhaustive-DFS proof **and** deterministic CP-SAT UNSAT agreement, and immediate escalation to the full battery + independent reproduction. The existing frozen 296-corpus and its verifier stay byte-untouched.

**Primary recommendation:** Build a small `pool/cdm/` subsystem: (a) a `geng`-subprocess generator emitting graph6 MTF H's with full provenance; (b) a `has_cdm(G)` DFS reference + a `cdm_cpsat(G)` CP-SAT cross-check that must agree on all 1,813; (c) a new stdlib CDM-witness verifier + a dedicated append-only CDM corpus (leave the had₂ trust root/corpus frozen); (d) an in-repo transfer-lemma proof document with the monotonicity + Lemma-2.5 argument and the disconnected-complement carve-out. Reuse the *existing* CP-SAT determinism discipline (num_workers=1, pinned seed) for every CDM-FAIL. No new third-party packages are required.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Exhaustive MTF generation | External C tool (nauty `geng`/`pickg`) via subprocess | Python provenance capture | McKay canonical-augmentation is isomorph-free at C speed; Python must never enumerate the 10⁶–10⁸ triangle-free pre-images (CLAUDE.md Blueprint 1). |
| graph6 → adjacency decode | Python (`networkx.from_graph6_bytes`) | ~15-line bitset decoder (only if a full-stream Python filter is ever needed) | Only the ~1,813 survivors reach Python; networkx is more than adequate for that volume. |
| CDM decision (reference) | Python DFS (`pool/cdm/reference.py`) | — | Correctness-obvious, solver-free, trusted; n≤14 makes exhaustive search trivial. |
| CDM decision (cross-check) | OR-Tools CP-SAT (`pool/cdm/cpsat.py`) | — | Independent second engine; deterministic single-worker for any UNSAT (impossibility). |
| CDM-HOLDS witness verification | Python stdlib-only verifier (new `verify_cdm_witness`) | — | Trust root discipline: independent, no import of any proposer, correct under `python -O`. |
| Certificate persistence | Append-only CDM corpus (new store, same atomic-write discipline) | Existing `corpus/store` pattern reused | Keeps the frozen 296-corpus + its verifier byte-untouched while reusing the proven append-only mechanics. |
| CDM-FAIL escalation | Existing battery (`battery/pipeline.run_candidate`) + dual-backend had₂ + E3 | Independent reproduction | Radioactive-impossibility protocol already exists; POOL-0 wires CDM-fail into it. |
| Transfer-lemma proof | In-repo prose/Markdown proof + executable count/monotonicity checks | pytest property tests | The lemma is a human artifact; its empirical predicates (Lemma 2.5 equivalences, monotonicity) are testable. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| nauty `geng`/`pickg`/`shortg`/`countg` | 2.9.3 (brew; on PATH — verified) | Exhaustive MTF generation + C-speed diameter/count filters + canonical dedup | Canonical exhaustive generator; `geng -ctq n \| pickg -Z2` reproduced 61/147/392 live `[VERIFIED: live run]`. |
| networkx | 3.6.1 (pinned) | graph6 decode (`from_graph6_bytes`), complement (`nx.complement`), α/ω sanity | Already the repo's graph library; `from_graph6_bytes` verified working on geng output `[VERIFIED: live run]`. |
| OR-Tools CP-SAT | 9.15.6755 (pinned) | Independent CDM decision (SAT feasibility model) | Second engine for the mandated cross-check; existing `solvers/cpsat.py` determinism discipline reused. |
| Python stdlib | 3.12.13 (pinned) | DFS reference, CDM-witness verifier, subprocess driver, append-only store | Trust-root + reference algorithms are stdlib-only by program rule. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest / pytest-xdist | latest (dev extra) | 1,813-instance batch as tests; DFS≡CP-SAT differential; transfer-lemma predicates | Always — POOL-0 adjudication runs as the suite; xdist fans the n=14 batch out. |
| pynauty | 2.8.8.1 (optional `[nauty]` extra) | In-process canonical `certificate()` for dedup of a *second* generation route | Only if merging an independent generator's stream (Blueprint 1 dedup); not needed for the single `geng` stream (already isomorph-free). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `geng -ctq \| pickg -Z2` | triangleramsey / Goedgebeur or Brandt–Brinkmann–Harmuth direct MTF generators | Direct MTF generators are the *recommended independent second route* for the cross-check (esp. n=14); needed for real only past n≈16. Cross-check counts + `shortg` canonical forms. |
| CP-SAT feasibility cross-check | PySCIPOpt (SCIP) as a third opinion | Only if a CDM-FAIL ever appears (radioactive) and a third independent UNSAT is wanted; not needed for the expected all-HOLD result. |
| networkx `from_graph6_bytes` | ~15-line graph6→int-bitset decoder | Only if a Python-side filter over the *full* triangle-free stream is required — which the research shows is too slow (avoid; keep the filter in the C pipe). |

**Installation:** No new packages. All four core tools are already installed and pinned (ENV-01, verified on this machine: nauty 2.9.3 on PATH, networkx 3.6.1, ortools 9.15, Python 3.12.13). An optional independent generator (triangleramsey) would be the only possible addition — see Package Legitimacy Audit.

## Package Legitimacy Audit

**No new external Python packages are introduced by this phase.** All dependencies (nauty, networkx, ortools, pynauty) are already pinned and audited in ENV-01 / the STACK research. slopcheck is therefore not applicable to a new-install list.

| Package | Registry | Status | Disposition |
|---------|----------|--------|-------------|
| nauty | brew (2.9.3) | Pre-installed, on PATH, version verified | Already approved (ENV-01) |
| networkx | PyPI 3.6.1 | Pinned in lockfile | Already approved (ENV-01) |
| ortools | PyPI 9.15.6755 | Pinned in lockfile | Already approved (ENV-01) |
| pynauty | PyPI 2.8.8.1 | Optional `[nauty]` extra, pinned | Already approved (ENV-01) |
| triangleramsey / plantri-family MTF generator (OPTIONAL) | ANU/nauty ecosystem (C source) | **Not evaluated** — only needed if the "second independent generator" route is chosen over the reuse-of-`geng` cross-checks | If adopted: `checkpoint:human-verify` before build/install; prefer building from the ANU source tarball (same trust path as nauty), not an unverified PyPI mirror. |

**Packages removed due to slopcheck [SLOP]:** none.
**Packages flagged [SUS]:** none (no new installs).

## The CDM Property (the heart of the phase)

### Exact definitions (quoted from arXiv:2512.17114)

`[CITED: arxiv.org/html/2512.17114 §1, Conjectures 8 & 10, Lemma 2.5]`

- **Matching** M: a set of pairwise vertex-disjoint edges of G. V(M) = vertices covered by M.
- **Connected matching:** "M is connected if for every two edges e,f ∈ M, V(e) and V(f) are adjacent." (I.e. for every pair of M-edges, at least one of the four cross vertex-pairs is an edge of G. For pairwise-*disjoint* edges this is exactly the condition that {e as a size-2 branch set} and {f as a size-2 branch set} are adjacent in G — a size-2 K-minor model.)
- **Dominating matching:** "M is dominating if each vertex of V(G)∖V(M) is adjacent to each edge e ∈ M." (A vertex w is *adjacent to an edge* e={a,b} iff w is adjacent to a or b — i.e. w has a neighbour in V(e). See Assumptions Log A1 — this "≥1 endpoint" reading is the standard vertex-edge adjacency and is what makes {w} a valid size-1 branch set adjacent to branch set {a,b}.)
- **CDM (Conjecture 10):** "Every connected graph G with α(G)=2 has a non-empty connected dominating matching." The *property* CDM(G) is the decidable predicate "G has a non-empty connected dominating matching."
- **SHC_{α=2} (Conjecture 8):** "Every graph G with α(G)=2 has a K_{χ(G)}-model in which each branch set has size at most 2." **This is exactly the repo's had₂(G) ≥ χ(G) property** (the size-≤2 branch-set model the trust root already verifies).
- **Implication chain (Theorem 2.10 / Figure 1):** **CDM ⟹ SHC_{α=2} ⟹ Hadwiger_{α=2}.** `[CITED]` Verified computationally "for all graphs up to 11 vertices." CDM is *sufficient*, not necessary — a CDM failure does **not** disprove Hadwiger.

### The DFS reference decision procedure (trusted, solver-free)

Decide `has_cdm(G)` exhaustively; n≤14 makes this trivial. Correctness is obvious by construction — this is the reference the CP-SAT model is checked against.

Structure (recommended — the "grow to cover an undominated vertex" formulation, which self-prunes and terminates cleanly):

```python
# Source: derived from arXiv:2512.17114 §1 definitions. adj = list[set[int]] for G.
def has_cdm(adj, n):
    """Return a witness matching M (list of (a,b)) if G has a non-empty connected
    dominating matching, else None. Exhaustive; trusted reference."""
    G_edges = [(a, b) for a in range(n) for b in adj[a] if a < b]

    def vsets_adjacent(e, f):                 # e,f disjoint edges: V(e),V(f) adjacent in G
        a, b = e; c, d = f
        return (c in adj[a] or d in adj[a] or c in adj[b] or d in adj[b])

    def dominates(M):                          # every vertex outside V(M) adjacent to each edge
        cover = {v for e in M for v in e}
        for w in range(n):
            if w in cover:
                continue
            for (a, b) in M:
                if w not in adj[a] and w not in adj[b]:
                    return False
            # additionally: w must be adjacent to *some* other vertex? No — only to each edge.
        return True

    def dfs(M, cover):
        if M and dominates(M):
            return list(M)
        # find an undominated vertex (or, if none but M empty, seed with any edge)
        target = None
        for w in range(n):
            if w in cover:
                continue
            if any(w not in adj[a] and w not in adj[b] for (a, b) in M):
                target = w; break
        candidates = G_edges if not M else [
            (a, b) for (a, b) in G_edges
            if (a == target or b == target)               # must cover the undominated target
            and a not in cover and b not in cover          # keep it a matching
            and all(vsets_adjacent((a, b), e) for e in M)  # keep it connected (pairwise)
        ]
        if not M:  # seed: any edge, pairwise-adjacency vacuous
            candidates = [e for e in G_edges]
        for (a, b) in candidates:
            r = dfs(M + [(a, b)], cover | {a, b})
            if r is not None:
                return r
        return None

    return dfs([], set())
```

Notes for the planner: (a) the seed step branches over *all* edges (a non-empty M can start anywhere); (b) after the first edge, every added edge must be pairwise-V-adjacent to all current M-edges (maintains "connected" = clique-of-edges) and must cover a currently-undominated vertex (this both prunes hard and guarantees termination — an undominated vertex can only be fixed by matching it, since existing M-edges never gain neighbours); (c) a fully-exhaustive-but-simpler variant (enumerate all pairwise-adjacent matchings, test `dominates` on each) is an acceptable *belt-and-suspenders* second reference for small n if the executor wants maximal obviousness.

### The CP-SAT cross-check encoding (independent second engine)

Boolean model whose feasibility ⟺ CDM(G). Must AGREE with the DFS on every instance.

```python
# Source: standard CP-SAT feasibility encoding of the §1 definitions.
# x[e] = edge e chosen for M ; y[v] = 1 iff v in V(M) (derived).
from ortools.sat.python import cp_model
m = cp_model.CpModel()
E = [(a, b) for a in range(n) for b in adj[a] if a < b]
x = {e: m.NewBoolVar(f"x_{e}") for e in E}
# matching: each vertex in <=1 chosen edge
for v in range(n):
    inc = [x[e] for e in E if v in e]
    if inc:
        m.Add(sum(inc) <= 1)
# non-empty
m.Add(sum(x.values()) >= 1)
# connected (pairwise): forbid two disjoint, non-V-adjacent edges together
for i, e in enumerate(E):
    for f in E[i+1:]:
        if set(e) & set(f):
            continue  # share a vertex -> matching constraint already excludes
        a, b = e; c, d = f
        if not (c in adj[a] or d in adj[a] or c in adj[b] or d in adj[b]):
            m.Add(x[e] + x[f] <= 1)
# dominating: for vertex w non-adjacent to BOTH endpoints of edge e, choosing e forces w matched
for e in E:
    a, b = e
    for w in range(n):
        if w == a or w == b:
            continue
        if w not in adj[a] and w not in adj[b]:   # w not adjacent to edge e
            inc_w = [x[g] for g in E if w in g]
            m.Add(x[e] <= sum(inc_w))             # x[e]=1 => w is covered by some edge
```

Determinism discipline (LOCKED, reuse existing pattern): for any **UNSAT** (CDM-FAILS) verdict — which is impossibility-flavored and therefore radioactive — solve with `num_workers=1` + pinned `random_seed` (the exact idiom already established in `solvers/cpsat.py`, STATE.md Phase 05 P01). A SAT witness is routed to the independent CDM verifier and its solver-nondeterminism is irrelevant (certificates are checked, not trusted). The DFS↔CP-SAT differential is release-blocking: any disagreement quarantines the instance and halts the batch (mirror `differential_verdict` / `CriticalDisagreement`).

## The Transfer Lemma (re-derived in-repo — ROADMAP SC3)

**Statement (to prove in-repo):** To establish CDM for every connected α=2 graph on n vertices, it suffices to verify CDM on the complements of the maximal-triangle-free graphs on n vertices (equivalently: the edge-minimal α=2 graphs, equivalently the connected triangle-free diameter-2 graphs' complements) — precisely the outputs of `geng -ctq n | pickg -Z2`.

**Two ingredients:**

1. **Lemma 2.5 (CLWY) `[CITED]`** — for a triangle-free graph on ≥3 vertices, TFAE: (i) edge-maximal triangle-free; (ii) diameter = 2; (iii) complement has α=2 and is edge-minimal; (iv) complement has no dominating edge. This is what makes `pickg -Z2` (diameter exactly 2) on a `geng -ctq` (connected triangle-free) stream generate exactly the MTF graphs — **empirically confirmed**: the repo's `is_edge_maximal_tf` (add-any-edge-makes-a-triangle) filter over the raw stream produced 61 (n=11) and 147 (n=12), identical to `pickg -Z2` `[VERIFIED: live run]`.

2. **CDM edge-addition monotonicity (prove in-repo):** if G has a non-empty connected dominating matching M and G' = G + one edge (same vertices, still α≤2), then M is still a non-empty connected dominating matching in G'. Proof: M's edges are unchanged (still a matching); "connected" and "dominating" are *adjacency-positive* conditions and adjacency only increases. Hence **CDM(G) ⟹ CDM(G')**. Contrapositive: the edge-minimal α=2 graphs are the only ones that need checking; every α=2 graph is a spanning supergraph of some edge-minimal one, so its CDM is inherited.

**The proof obligation the in-repo write-up MUST address (Open Q1 — do not gloss):** monotonicity flows *upward* (minimal ⟹ all supergraphs), so if an edge-minimal graph *fails* CDM, its supergraphs are not certified by it. Some edge-minimal α=2 graphs are **disconnected** — exactly when the MTF complement is complete bipartite K_{a,b} (triangle-free, diameter 2, in the `pickg -Z2` output), giving G = K_a ⊔ K_b, which has no connected dominating matching (an edge in one clique cannot dominate the other clique). These are **not** counterexamples because Conjecture 10 hypothesizes *connected* G. The transfer must therefore be stated as: "every **connected** α=2 graph G inherits CDM from an edge-minimal α=2 graph reachable by edge-deletions that preserve connectivity" — or, more cleanly, prove the target statement directly over connected G by extending H=Ḡ to a maximal-triangle-free H* whose complement is connected (such an extension exists whenever G is connected), and note the disconnected MTF-complements are catalogued and excluded from the "connected-frontier" claim. **Recommendation:** the CDM checker should classify each of the 1,813 instances as connected-complement (in scope for the connected frontier) vs disconnected-complement (K_a⊔K_b, expected CDM-fail, out of scope), and the transfer proof should carry this carve-out explicitly. A disconnected-complement CDM-fail must be recognized and **not** mis-escalated as a Hadwiger event.

## Architecture Patterns

### System Architecture Diagram

```
                          Phase 7 P0 — CDM Frontier
   ┌────────────────────────────────────────────────────────────────────────┐
   │  GENERATION (C speed, in the pipe)                                       │
   │   geng -ctq n [res/mod] ──▶ pickg -Z2 ──▶ graph6 lines (MTF H's)         │
   │        (connected, triangle-free, quiet)   (diameter exactly 2)          │
   └───────────────────────────────┬────────────────────────────────────────┘
                                    │  ~1,813 survivors only (147+392+1,274)
                                    ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │  DECODE + PROVENANCE (Python)                                            │
   │   from_graph6_bytes(H) ──▶ G = complement(H)  (α(G)=2)                   │
   │   provenance = {geng_version, flags, n, shard res/mod, index, graph6}    │
   └───────────────────────────────┬────────────────────────────────────────┘
                                    ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │  DUAL CDM DECISION  (must agree — release-blocking differential)         │
   │   has_cdm(G)  [DFS reference, trusted] ══╗                               │
   │   cdm_cpsat(G)[CP-SAT, indep, det UNSAT] ══╬══▶ agree?                    │
   └───────────────────────────────┬───────────╨───────────┬────────────────┘
              CDM-HOLDS (SAT)       │                       │ CDM-FAILS (UNSAT)
              existence (cheap)     ▼                       ▼ impossibility (RADIOACTIVE)
   ┌─────────────────────────────────────┐   ┌──────────────────────────────┐
   │ verify_cdm_witness(M)  (stdlib,     │   │ connected-complement?         │
   │  independent trust leg)             │   │   yes ─▶ ESCALATE: battery     │
   │   ▶ append to CDM corpus            │   │          had₂ + E3 + indep     │
   │     (graph6 provenance + M)         │   │          reproduction          │
   └─────────────────────────────────────┘   │   no (K_a⊔K_b) ─▶ catalog,     │
                                              │        NOT a Hadwiger event    │
                                              └──────────────────────────────┘

   TRANSFER LEMMA (Lemma 2.5 + edge-addition monotonicity) proven in-repo:
     MTF-complements adjudicated  ⟹  all connected α=2 graphs at n adjudicated
```

### Recommended Project Structure
```
src/alpha2/pool/                 # new: candidate-pool subsystems (P0..P7 land here)
├── __init__.py
└── cdm/
    ├── __init__.py
    ├── generate.py      # geng/pickg subprocess driver + provenance + res/mod sharding
    ├── reference.py     # has_cdm(adj, n) DFS reference (stdlib only, trusted)
    ├── cpsat.py         # cdm_cpsat(adj, n) CP-SAT feasibility cross-check (ortools-confined)
    ├── verifier.py      # verify_cdm_witness(record) — stdlib-only NEW trust leg
    ├── schema.py        # CDM certificate record builder (reuses provenance_graph6)
    ├── store.py         # append-only CDM corpus (reuse corpus/store atomic-write pattern)
    └── adjudicate.py    # per-instance: decode -> dual-decide -> verify/escalate -> append
docs/proofs/
└── transfer-lemma.md    # in-repo write-up (ROADMAP SC3)
data/corpus/
└── cdm_certificates.json  # NEW dedicated append-only CDM corpus (frozen 296 untouched)
```

### Pattern 1: geng subprocess driver with provenance + sharding
**What:** shell out to `geng`/`pickg`, stream graph6 lines, attach a full provenance record per instance.
**When to use:** the generation step; the ONLY correct way (pynauty has no geng binding — CLAUDE.md verified).
**Example:**
```python
# Source: nauty 2.9.3 usage (verified live); CLAUDE.md Blueprint 1.
import subprocess, shutil
def geng_version():
    # nauty prints usage/version to stderr; capture for provenance
    out = subprocess.run(["geng", "--help"], capture_output=True, text=True)
    return (out.stderr or out.stdout).splitlines()[0].strip()

def stream_mtf(n, res=None, mod=None):
    """Yield (index, graph6, shard) for MTF graphs on n vertices."""
    shard = f"{res}/{mod}" if mod else None
    geng_args = ["geng", "-ctq", str(n)] + ([shard] if shard else [])
    p1 = subprocess.Popen(geng_args, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["pickg", "-Z2"], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
    p1.stdout.close()
    for i, line in enumerate(p2.stdout):
        g6 = line.strip()
        if g6:
            yield i, g6, shard
    p2.wait()
```
Provenance record per instance (POOL-0 SC1): `{geng_version, flags:"-ctq | pickg -Z2", n, shard:"res/mod"|null, index, graph6}` → maps onto the existing `schema.provenance_graph6(family="mtf_complement", n, graph6)` plus a `params` sidecar for `{geng_version, flags, shard, index}`.

### Pattern 2: dual-decision differential (reuse the had₂ discipline)
**What:** run DFS + CP-SAT, require agreement, treat UNSAT as radioactive.
**When to use:** every instance.
**Example:** structurally identical to `battery/pipeline` step [4]: compute both verdicts, raise a `CriticalDisagreement`-style halt on mismatch; for SAT route the witness through `verify_cdm_witness`; for UNSAT re-run CP-SAT deterministically and require the DFS's exhaustive UNSAT to match before escalating.

### Anti-Patterns to Avoid
- **Filtering the full triangle-free stream in Python/networkx** — n=13 (20.8M graphs) timed out live; keep `pickg` in the C pipe.
- **Using WL-hash / any non-canonical hash for isomorph dedup** — CLAUDE.md forbidden; `geng` output is already isomorph-free, and a second stream is deduped via `shortg`/`pynauty.certificate` only.
- **Reusing `corpus/verifier.verify_model_record` for a CDM witness** — a connected dominating matching is NOT a K_χ branch-set family (unmatched vertices need not be pairwise adjacent); it needs its own verifier leg. Do not force-fit it.
- **Trusting a CP-SAT SAT/UNSAT verdict without the DFS** — the DFS is the reference; CP-SAT is the cross-check, never the sole authority (esp. for UNSAT).
- **Mutating the frozen 296-corpus or its verifier** — add a parallel CDM store/verifier instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Isomorph-free triangle-free generation | A Python triangle-free enumerator | `geng -ctq` | McKay canonical augmentation; 467M graphs at n=14 — C only. |
| Maximal-triangle-free / diameter-2 filter | Python loop over the full stream | `pickg -Z2` in the pipe | Verified 61/147/392 at C speed; Python is orders slower (n=13 timed out). |
| graph6 parsing | A hand decoder (unless a full-stream Python filter is needed) | `networkx.from_graph6_bytes` | Only ~1,813 survivors reach Python; verified working on geng output. |
| Canonical dedup of a *second* generation stream | WL-hash / custom canonical form | `shortg` (or `pynauty.certificate`) | The one canonical convention; WL is non-canonical (forbidden). |
| CP-SAT determinism on UNSAT | Ad-hoc worker/seed settings | The existing `solvers/cpsat.py` `num_workers=1` + pinned-seed idiom | Documented CP-SAT wrong-INFEASIBLE / nondeterminism regressions (CLAUDE.md #3590/#3842/#4839). |
| Append-only, crash-safe, verify-at-append persistence | A fresh JSON writer | The `corpus/store` pattern (tempfile→fsync→os.replace + hash-chain) | Already proven; the CDM store should clone it, not reinvent it. |

**Key insight:** the entire *impossibility-handling* apparatus (dual-backend agreement, deterministic CP-SAT, radioactive-UNSAT protocol, append-only immutability, independent stdlib verification) already exists in the repo for had₂. Phase 7 is mostly *wiring a new predicate (CDM) into that proven apparatus*, not building new machinery.

## Common Pitfalls

### Pitfall 1: The disconnected-complement CDM-fail (false Hadwiger alarm)
**What goes wrong:** an MTF complete-bipartite H yields G = K_a ⊔ K_b, which legitimately has no connected dominating matching; a naive checker escalates it as a Hadwiger-threatening CDM-less graph.
**Why it happens:** Conjecture 10 is about *connected* G; the generation includes disconnected complements.
**How to avoid:** classify each instance by complement-connectivity up front; a disconnected-complement CDM-fail is catalogued as expected/out-of-scope, never routed to E3 as an anomaly.
**Warning signs:** CDM-fail whose G has ≥2 components / whose H is complete bipartite (`-b` bipartite + one non-edge class).

### Pitfall 2: CP-SAT nondeterminism on UNSAT (impossibility)
**What goes wrong:** a parallel-portfolio CP-SAT run returns INFEASIBLE nondeterministically or (per documented regressions) wrongly.
**Why it happens:** default multi-worker search is nondeterministic; INFEASIBLE is exactly the radioactive direction.
**How to avoid:** for any CDM-FAIL cross-check use `num_workers=1` + pinned seed (existing idiom), and require the trusted DFS's exhaustive UNSAT to agree; never report CDM-FAIL on CP-SAT alone.
**Warning signs:** DFS≡CP-SAT differential mismatch → quarantine + halt (release-blocking).

### Pitfall 3: Silently miscounting the frontier (generation drift)
**What goes wrong:** wrong `geng`/`pickg` flags, a dropped shard, or a mis-set res/mod silently yields ≠1,813.
**Why it happens:** sharded generation (`res/mod`) is easy to sum incorrectly; a `-q` in the wrong place hides the count.
**How to avoid:** assert exact per-n counts (147/392/1,274) against OEIS A216783 AND a second route; when sharding, assert Σ over all `res` in `0..mod-1` equals the total; keep a canonical-form set (via `shortg`) to detect duplicates/omissions across shards.
**Warning signs:** total ≠ 1,813; duplicate canonical graph6 across shards.

### Pitfall 4: vertex-edge adjacency ambiguity in "dominating"
**What goes wrong:** implementing "w adjacent to edge e" as "adjacent to *both* endpoints" (or as "adjacent to the branch set as a whole") instead of "adjacent to ≥1 endpoint" changes the property and breaks agreement with the paper's n≤11 result.
**Why it happens:** "adjacent to an edge" is stated tersely.
**How to avoid:** pin the "≥1 endpoint" reading (Assumptions Log A1) and validate by **reproducing the paper's n≤11 CDM result** (all connected α=2 graphs at n≤11 have CDM) as a regression before trusting the n=12–14 output.
**Warning signs:** any connected α=2 graph at n≤11 reported CDM-less — that contradicts the paper and indicates a definition bug, not new science.

### Pitfall 5: Rosetta/Linux platform concerns leaking into CDM certificates
**What goes wrong:** treating a CDM certificate as platform-sensitive like a CBC ILP certificate.
**Why it happens:** the ENV-05 contract makes Linux x86_64 canonical for *ILP-derived* certificates (CBC-under-Rosetta).
**How to avoid:** CDM certificates are **solver-independent** — the witness is a matching verified by pure stdlib integer logic (no floating point, no CBC), and CP-SAT is only a cross-check whose SAT witness is re-verified. So CDM-HOLDS certificates are byte-reproducible cross-platform. Record the `geng`/`pickg`/nauty version and Python version in provenance; do **not** mark CDM certificates as requiring the Linux canonical platform. (Only a CDM-FAIL that escalates into a CBC-backed had₂ certificate inherits the ENV-05 Linux rule.)
**Warning signs:** a CDM certificate stamped with a CBC/Rosetta platform dependency.

## Code Examples

### Reproduce and assert the exact MTF frontier counts
```bash
# Source: nauty 2.9.3, verified live 2026-07-22 (61/147/392 exact).
for n in 12 13 14; do
  echo -n "n=$n MTF: "
  geng -ctq $n | pickg -Z2 | wc -l      # expect 147, 392, 1274
done
# Sharded n=14 (parallelizable; sum over res=0..mod-1 must equal 1274):
geng -ctq 14 0/64 | pickg -Z2 | wc -l   # one of 64 shards
```

### Complement + α=2 sanity per survivor
```python
# Source: networkx 3.6.1, verified from_graph6_bytes works on geng output.
import networkx as nx
H = nx.from_graph6_bytes(g6.encode())          # MTF (triangle-free, diam 2)
G = nx.complement(H)                            # alpha(G) = 2
n = G.number_of_nodes()
adj = [set(G.neighbors(u)) for u in range(n)]   # feed has_cdm / cdm_cpsat
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hadwiger_{α=2} verified ad hoc per family | CDM ⟹ SHC ⟹ Hadwiger; CDM computer-verified to n≤11 | CLWY, arXiv:2512.17114 (Dec 2025) | Gives a single clean predicate to push exhaustively; Phase 7 extends the frontier to n=14 (stretch 17). |
| had₂ = χ checked via ILP per instance | CDM (connected dominating matching) as a stronger, tiny-certificate sufficient condition | This phase adopts CDM as primary; had₂ becomes the escalation cross-check | Existence certificates shrink to a matching; impossibility stays radioactive. |

**Deprecated/outdated:** none — this is a new-science extension, not a migration.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | "w adjacent to edge e={a,b}" in the *dominating* condition means w adjacent to ≥1 endpoint (standard vertex-edge adjacency), not both. | The CDM Property | Load-bearing: the wrong reading changes the property and the n≤11 reproduction fails. **Mitigation:** validate by reproducing CLWY's n≤11 all-CDM result before trusting n=12–14. Confirm against the paper's Definition text during planning. |
| A2 | n=14 MTF count is 1,274 (not reproduced end-to-end here — only partial shards run; taken from OEIS A216783 + CLAUDE.md). | Summary / Generation | A miscount would mean the frontier claim is off. **Mitigation:** the plan asserts the full count against OEIS + a second generator. |
| A3 | The transfer proof's disconnected-complement carve-out (K_a⊔K_b) is the *only* obstruction to "check MTF-complements ⟹ done for connected G." | Transfer Lemma | If other obstructions exist, the transfer proof is incomplete. **Mitigation:** the in-repo proof is reviewed; the executable classifier surfaces every disconnected-complement instance for inspection. |
| A4 | CDM certificates are solver-independent and thus exempt from the ENV-05 Linux-canonical-platform rule. | Pitfall 5 | If wrong, cross-platform reproduction of CDM certs could drift. **Mitigation:** the witness verifier is pure-integer stdlib (no float, no CBC) — low risk. |
| A5 | A dedicated CDM corpus + new verifier leg (rather than extending the frozen had₂ trust root/schema) is the preferred integration. | Architecture | If the project prefers a single unified corpus, the schema must instead be extended additively. **This is a design decision for discuss-phase** (Open Q2). |

## Open Questions (RESOLVED)

**Resolution (2026-07-22, plan-check):** Q1 → dedicated carve-out — disconnected `K_a⊔K_b` catalogued out-of-scope, connected frontier proven directly (07-05 proof + 07-06 classifier). Q2 → dedicated CDM corpus + new stdlib `verify_cdm_witness` leg (`paths.CDM_CORPUS`; frozen 296-corpus untouched; 07-03). Q3 → v1 second-FILTER route (OEIS A216783 + `is_edge_maximal_tf` + `shortg` canonical-set) ratified at the 07-04 blocking author checkpoint; a fully independent MTF generator is deferred. Q4 → escalation HOOK wired now (07-06: connected-complement CDM-fail → battery had₂ + quarantine); full E1/E2/E3 deferred to Phase 11.

1. **The connected-vs-disconnected carve-out in the transfer proof.**
   - What we know: monotonicity + Lemma 2.5 give the backbone; disconnected edge-minimal graphs (K_a⊔K_b, complete-bipartite complements) can fail CDM without being counterexamples.
   - What's unclear: the cleanest *in-repo* phrasing — (a) prove directly over connected G via a connectivity-preserving maximal-triangle-free extension, vs (b) catalog + exclude disconnected complements.
   - Recommendation: do (a) as the theorem and (b) as the executable audit; both in `docs/proofs/transfer-lemma.md`. Flag for author review (this is "first new science").

2. **Certificate home: dedicated CDM corpus vs extended unified schema.**
   - What we know: the frozen 296-corpus + its trust root must stay byte-untouched; the schema already has `graph6` provenance anticipating geng-sourced instances.
   - What's unclear: whether CDM certs live in a new `data/corpus/cdm_certificates.json` with a parallel verifier, or the had₂ schema/verifier gains an additive CDM leg.
   - Recommendation: dedicated CDM store + new stdlib `verify_cdm_witness` (safest for immutability); confirm in discuss-phase (A5).

3. **The second independent generation route for n=14.**
   - What we know: `pickg -Z2` is the primary; the Python edge-maximal filter agrees but is too slow past n≈12; `pickg -j1` is NOT equivalent (it matches *exactly* 1 common neighbour — measured 56/139/382, not 61/147/392).
   - What's unclear: whether to (a) use an external MTF generator (triangleramsey/Goedgebeur — a package decision) or (b) use a fast bitset-based edge-maximal filter over the C stream as the independent route.
   - Recommendation: for v1, cross-check counts vs OEIS + `shortg`-canonical-set equality between two *filter* predicates (`-Z2` vs a bitset edge-maximal check on survivors); adopt an external generator only if the author wants a fully independent *generator* (Package Legitimacy checkpoint).

4. **Escalation depth for an (unexpected) connected-complement CDM-fail.**
   - What we know: it routes to the battery (had₂ dual-backend) + E3 + independent reproduction.
   - What's unclear: E1/E2/E3 (Phase 11) are not yet built; Phase 7 precedes Phase 11.
   - Recommendation: Phase 7 wires the escalation *hook* (record CDM-fail, run existing battery had₂ to test whether SHC still holds, quarantine) and defers full E3 to Phase 11; a connected-complement CDM-fail at n≤14 is not expected given the conjecture, so this path is a safety net, not a mainline.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| nauty `geng` | MTF generation | ✓ | 2.9.3 (`/opt/homebrew/bin/geng`) | none needed |
| nauty `pickg` | diameter-2 filter | ✓ | 2.9.3 | Python bitset edge-maximal filter (slower) |
| nauty `shortg`/`countg` | canonical dedup / counts | ✓ | 2.9.3 | — |
| networkx | graph6 decode + complement | ✓ | 3.6.1 | ~15-line bitset decoder |
| OR-Tools CP-SAT | CDM cross-check | ✓ | 9.15.6755 | DFS is the trusted reference; CP-SAT is only the cross-check |
| Python | everything | ✓ | 3.12.13 | — |
| triangleramsey (optional 2nd generator) | independent generation route | ✗ | — | reuse `geng` with a second filter predicate + OEIS + `shortg` |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** an external independent MTF *generator* is absent; the count/canonical cross-checks against OEIS + `shortg` + a second filter predicate substitute for v1.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (+ pytest-xdist for fan-out) — already the repo's suite |
| Config file | `pyproject.toml` (existing pytest config) |
| Quick run command | `uv run pytest tests/pool/cdm -x -q` |
| Full suite command | `uv run pytest -q` (includes the 296-corpus regression + CDM batch) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| POOL-0 | `geng -ctq \| pickg -Z2` yields exactly 147/392/1,274 at n=12/13/14 | integration | `uv run pytest tests/pool/cdm/test_generation_counts.py -x` | ❌ Wave 0 |
| POOL-0 | Generation counts cross-check vs OEIS A216783 + a second route | integration | `uv run pytest tests/pool/cdm/test_generation_crosscheck.py -x` | ❌ Wave 0 |
| POOL-0 | DFS `has_cdm` reproduces CLWY's n≤11 all-CDM result (definition regression, A1) | unit | `uv run pytest tests/pool/cdm/test_cdm_n_le_11.py -x` | ❌ Wave 0 |
| POOL-0 | DFS ≡ CP-SAT on every instance (all 1,813; disagreement release-blocking) | integration (slow) | `uv run pytest tests/pool/cdm/test_dfs_cpsat_agree.py -x` | ❌ Wave 0 |
| POOL-0 | `verify_cdm_witness` accepts valid M, rejects mutants (non-matching, non-connected, non-dominating, empty) | unit | `uv run pytest tests/pool/cdm/test_cdm_verifier.py -x` | ❌ Wave 0 |
| POOL-0 | `verify_cdm_witness` fails closed under `python -O` (no asserts) | unit | `uv run pytest tests/pool/cdm/test_cdm_verifier_dash_O.py -x` (run under `-O` in CI) | ❌ Wave 0 |
| POOL-0 | Transfer-lemma predicates: Lemma 2.5 equivalence (diam-2 ⟺ edge-maximal) + CDM edge-addition monotonicity | property (hypothesis) | `uv run pytest tests/pool/cdm/test_transfer_lemma.py -x` | ❌ Wave 0 |
| POOL-0 | Disconnected-complement (K_a⊔K_b) classified + not mis-escalated | unit | `uv run pytest tests/pool/cdm/test_disconnected_complement.py -x` | ❌ Wave 0 |
| POOL-0 | CDM corpus append-only + witness verified-at-append (mirrors store discipline) | integration | `uv run pytest tests/pool/cdm/test_cdm_store.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/pool/cdm -x -q` (fast: counts at n≤13, verifier mutants, n≤11 definition regression, transfer predicates).
- **Per wave merge:** full n=12–14 adjudication batch under xdist (`-n auto`), asserting all 1,813 HOLD and DFS≡CP-SAT everywhere.
- **Phase gate:** full suite green (incl. the frozen 296-corpus regression untouched) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/pool/cdm/conftest.py` — fixtures: small α=2 graphs (C₅, K_a⊔K_b, hand CDM witnesses), a cached n≤11 MTF sample.
- [ ] `tests/pool/cdm/test_cdm_n_le_11.py` — the A1 definition regression (reproduce CLWY n≤11). **Highest-priority gate** — validates the CDM definition before any new-science claim.
- [ ] `tests/pool/cdm/test_generation_counts.py` + `test_generation_crosscheck.py` — 147/392/1,274 + OEIS + second route.
- [ ] `tests/pool/cdm/test_cdm_verifier*.py` — mutant suite + `-O` canary (trust-root discipline).
- [ ] The n=14 full-batch test should be markable `@pytest.mark.slow` and shardable (res/mod) so CI can fan it out.

## Security Domain

`security_enforcement` is not set in `.planning/config.json` (treated as enabled), but Phase 7 is a local, offline mathematics CLI with **no** authentication, sessions, network services, PII, or secrets. The only genuine surface is **subprocess input handling** for the nauty pipe.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth surface) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (subprocess args + graph6 parsing) | Never pass shell strings — use `subprocess.Popen([...])` arg lists (no `shell=True`); validate n is a small positive int and res/mod are ints before interpolation; treat graph6 lines from `geng` as trusted-but-bounded (assert decoded n matches requested n). |
| V6 Cryptography | no | sha256 is used only as a content identity hash (existing schema), not for security. |

### Known Threat Patterns for {local nauty-subprocess CLI}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command/arg injection via n or res/mod interpolated into a shell | Tampering | `Popen` arg lists, no `shell=True`, int-validate all numeric args. |
| Resource exhaustion (unbounded `geng` at large n) | Denial of Service | Cap n at the phase's 14 (stretch 17) with an explicit budget; shard via res/mod; the batch is offline/CI, not user-facing. |
| Silent generation drift misread as science | Tampering (integrity) | Exact-count assertions vs OEIS + second route + `shortg` canonical-set (see Pitfall 3). |

## Sources

### Primary (HIGH confidence)
- `[CITED]` **arXiv:2512.17114** — Costa, Luu, Wood, Yip, "Verifying Hadwiger's Conjecture for Examples of Graphs with α(G)=2." Definitions of CDM (Conjecture 10), SHC_{α=2} (Conjecture 8), the CDM⟹SHC⟹Hadwiger chain (Thm 2.10 / Fig 1), the n≤11 verification claim, and Lemma 2.5 (edge-maximal ⟺ diameter-2 ⟺ edge-minimal-complement ⟺ no-dominating-edge). https://arxiv.org/abs/2512.17114 , https://arxiv.org/html/2512.17114
- `[VERIFIED: live run]` **nauty 2.9.3** on PATH — `geng -ctq n | pickg -Z2` reproduced MTF counts **61 (n=11), 147 (n=12), 392 (n=13)**; `pickg` flag semantics (`-Z#` diameter, `-z#` radius, `-T#` triangles, `-h#` max independent set, `-k#` max clique, `-N#` chromatic number) read from `pickg --help`; n=14 partial shards consistent with 1,274.
- `[VERIFIED: live run]` **Independent Python edge-maximal-tf filter** (`is_edge_maximal_tf` in `src/alpha2/generators/tfp.py`) over the raw `geng -ctq` stream agreed exactly with `pickg -Z2` (61, 147) — empirically confirms Lemma 2.5's diameter-2 ⟺ edge-maximal equivalence; too slow past n≈12 in networkx (n=13 timed out on 20.8M graphs).
- `[VERIFIED: source read]` Repo interfaces: `corpus/schema.py` (graph6 provenance, build_record, ENV-05 contract), `corpus/store.py` (append-only atomic + hash-chain), `corpus/verifier.py` (stdlib trust root, `_is_conflict`, `-O`-safe raises), `solvers/backend.py`/`result.py` (ExactBackend, status honesty), `battery/pipeline.py` (7-step runbook, differential escalation), `generators/tfp.py`.

### Secondary (MEDIUM confidence)
- OEIS A216783 (maximal triangle-free counts 61/147/392/1,274) and A006785 (triangle-free counts incl. 467,871,369 at n=14) — cross-referenced via CLAUDE.md STACK sources; the 1,274 value is authoritative there and consistent with live partial runs.
- CLAUDE.md Blueprint 1 (geng flags, MTF-via-diameter, graph6-into-bitset, dedup rules) and STACK/PITFALLS research (CP-SAT determinism regressions #3590/#3842/#4839).

### Tertiary (LOW confidence)
- The precise "≥1 endpoint" reading of vertex-edge adjacency in the *dominating* condition (A1) — standard but not verbatim-confirmed from the PDF; **flagged for definition-regression validation against CLWY n≤11.**

## Metadata

**Confidence breakdown:**
- CDM/SHC definitions + implication chain: HIGH — quoted from the source paper (Conjectures 8/10, Thm 2.10, Lemma 2.5).
- Generation pipeline + counts: HIGH — 61/147/392 reproduced live; 1,274 authoritative (OEIS) + partial-shard-consistent.
- Transfer lemma: HIGH on the backbone (Lemma 2.5 + monotonicity, both re-derived and one empirically confirmed); MEDIUM on the disconnected-complement carve-out phrasing (Open Q1, author review).
- Certificate integration: HIGH on the existing interfaces (source-read); MEDIUM on the store-home decision (A5/Open Q2 — a discuss-phase choice).
- DFS + CP-SAT specs: HIGH — direct encodings of the definitions; the A1 adjacency reading is the one flagged assumption.
- Pitfalls: HIGH — grounded in live measurements (Python-filter timeout, `-j1` non-equivalence) and existing repo discipline.

**Research date:** 2026-07-22
**Valid until:** ~2026-08-21 (stable: pinned toolchain, a published paper, exhaustive counts that cannot drift). Re-verify only if the CLWY paper is revised (v2→v3) or nauty is upgraded.
