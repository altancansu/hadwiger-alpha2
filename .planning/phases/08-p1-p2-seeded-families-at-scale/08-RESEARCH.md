# Phase 8: P1 & P2 — Seeded Families at Scale — Research

**Researched:** 2026-07-23
**Domain:** Additive combinatorics (sum-free sets in finite abelian groups) × extremal graph minor theory (Hadwiger, α=2) × exact ILP/CP-SAT solving at scale
**Confidence:** HIGH on codebase integration and the gate/screen mechanics; HIGH on the literature anchors (Green–Ruzsa, Chudnovsky–Seymour, Seymour ε-question, the Dec-2025 n/6 connected-matching result); MEDIUM on the exact Green–Ruzsa density labels (I/II/III numbering varies by source) and on the precise ILP-feasibility crossover point (n where CP-SAT optimality proofs stop closing).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

1. **Focus — break-hunt spine (P2 first).** Primary deliverable is the sum-free Cayley
   hunt: compute the **screened gap `g(G) = (χ(G) − had₃(G)) / χ(G)`** on each instance and
   track it **vs group order** across the structured-vs-random grid. `χ = n − ν(H)` (exact
   blossom); `had₃` = exact size-≤3-branch-set minor lower bound (existing backends).
   Interpretation: `g ≤ 0` ⇒ the K_χ minor already packs (Hadwiger holds on that instance);
   `g > 0` ⇒ a **candidate** (necessary, not sufficient — small branch sets can't reach χ; may
   just need larger branch sets). Sweep is **cheap to falsify, loud if real**: plot `g` vs |Γ|,
   look for a knee/upward trend/crossing.
   - **P2 grid:** generalized sum-free Cayley over arbitrary finite **abelian Γ**, structured
     (Andrásfai-interval, Green–Ruzsa-type) **vs** random-greedy maximal sum-free sets, odd
     **|Γ| = 31 – ~500**. Track structured vs random separately.
   - **P1 (secondary, in-phase):** TFP critical-size sweep extended (n=31–32, new seeds),
     showpieces pushed toward n≈1001–2001 via heuristic + verifier engine. Kept, not the spine.

2. **Prediction (LOCKED pre-data — falsifiable hypothesis, NOT an assumption): the STRUCTURED
   family (Andrásfai-interval / Green–Ruzsa) breaks first** — algebraic rigidity obstructs
   minor-packing, whereas random-greedy sets are expected to pack. The adversarial counter to
   hold in mind: vertex-transitivity can instead make minors *easier* to pack (automorphic
   branch-set copies), in which case structured stays clean — the sweep decides which force wins.
   A flat/negative `g` curve **falsifies** the hypothesis and is itself a (small) publishable
   result.

3. **Execution model.** Runs on a rented **64-core (up to ~250-core) x86-64** box. Parallelize
   at the **instance level** (pytest-xdist / job runner over the grid). **Any *reported*
   impossibility / INFEASIBLE / had₃<χ verdict stays deterministic single-worker
   (`num_workers=1` + pinned seed)** — CLAUDE.md CP-SAT regressions (#3590/#3842/#4839). Cores
   scale breadth of the hunt, never the determinism of a single reported verdict. On shared CPU,
   solver budgets MUST be deterministic (`max_deterministic_time`), never wall-clock.

4. **Epistemic discipline carried forward from Phase 7.** Keep **claim-(a)** ("these specific
   instances were checked") separate from **claim-(b)** ("therefore all connected α=2 graphs of
   this type"). `had₃ < χ` is a **screening signal only** → scaled exact search → **E3 survivor
   protocol (Phase 11)** before anything is called a break. RNG contract **v2** (sha256 per-stage
   subseeds); every instance rebuildable exactly from its stored descriptor. **Zero
   heuristic-only claims** — heuristic resistance is never a result; RESISTANT instances queue,
   they do not conclude. **Never announce a "break" before it survives E3 AND a human referee.**

### Claude's Discretion

- Exact plumbing of the `g(G)` metric and its per-instance certificate schema (reuse Phase-7 CDM
  schema patterns + the existing exact backends).
- Generator internals for structured vs random maximal sum-free sets over abelian Γ; sharding.
- How P1's large-n showpieces reuse the heuristic+verifier engine.
- Whether had₃ needs a tier bump for the sweep sizes, or had₂ screening suffices first.

### Deferred Ideas (OUT OF SCOPE)

- Announcing any "break" (deferred to E3 / Phase 11 + human referee).
- Full ETT/crooked and Kneser structured catalogs (Phase 10).
- Any impossibility claim about the *true* Hadwiger number (no certificate exists — Asymmetry
  Principle; the sweep only screens).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **POOL-1** | P1 TFP complements at scale — reproduce the 296, extend the critical-size sweep (n=31–32, many seeds), push showpieces toward n≈1001–2001 (heuristic + verifier past ILP range), resistance tracking. | §"P1 (secondary)" — existing `generators.tfp.triangle_free_process` + `search.heuristic.solve` + trust-root verifier already scale to n≈501 in the corpus; the n≈1001–2001 showpieces are existence-only (heuristic HIT → verify), never exact (§"g(G) rigor & cost"). RNG contract v2 recipe in §"Pattern 4". |
| **POOL-2** | P2 sum-free Cayley — generalize to any finite abelian Γ, add structured generators (Andrásfai intervals, Green–Ruzsa types) alongside random-greedy; structured-vs-random grid, |Γ| odd 31–~500. | §"Sum-free constructions" (exact recipes + citations), §"Pattern 1–3" (generator modules mirroring `pool/cdm`), §"g(G) screen" (had₂→had₃ tiering), §"Dedup discipline" (canonical labeling, no WL-hash). |
</phase_requirements>

## Summary

This phase turns the sum-free Cayley family into a **break-hunt instrument**. The mathematics is
clean and the constructions are exact and citable: a symmetric (`S = −S`) sum-free set `S ⊂ Γ`
makes the Cayley graph `H = Cay(Γ, S)` triangle-free, so its complement `G = H̄` is an α=2 graph;
`S` **maximal** sum-free makes `H` edge-maximal-triangle-free (the gate's G2 target). The
research question P2 probes is **Seymour's ε-question**: is there ε>0 with `had(G) ≥ (1/3+ε)n`
for every α≤2 graph? The best unconditional lower bounds are linear-connected-matching bounds —
`n/7` (Nguyen 2022) improved to **`n/6` (Dec 2025)** — all still short of the Hadwiger target
`χ ≈ (n+1)/2` for these near-`(n/3)`-regular graphs. The `g(G) = (χ − had₃)/χ` screen measures,
per instance, how far the size-≤3 branch-set minor falls below χ.

**The honest cost/rigor split is the single most important planning fact.** The `g ≤ 0` (packing)
branch is **cheap and scales to n≈2000**: the profile heuristic finds a size-≤2 K_χ minor and the
trust root verifies it (an existence certificate). The `g > 0` (candidate) branch is
**impossibility-flavored and ILP-bound**: proving `had₂ < χ` or `had₃ < χ` requires CP-SAT/CBC
*proven optimality*, and for these graphs χ ≈ n/2 with tens of thousands of pair variables — this
closes only at the **small-to-mid end (n≈31 up to ~150–200, the existing corpus ILP frontier)**.
Beyond that, a non-packing instance is **RESISTANT** (heuristic miss), **not** `g>0`, and queues
for E3 — it is never a reported candidate. So the `g`-vs-|Γ| plot is dense with verified `g≤0`
points everywhere and sparse with exact `g>0` points only where optimality proofs close.
Crucially, `had₃ < χ` establishes **only** "no K_χ minor with branch sets of size ≤3" — it does
**not** prove `had(G) < χ` (branch sets of size ≥4 are not excluded; it is *not* known that
`had = had₃` for α=2), so `g>0` is necessary-not-sufficient and certificates must say exactly that.

**Primary recommendation:** Build a new `src/alpha2/pool/sumfree/` package mirroring `pool/cdm/`
exactly (schema/store/verifier/generate/adjudicate), add three generator modules over a stdlib
finite-abelian-group representation (no new dependency), route each gate-surviving instance
through the existing `battery.run_candidate` had₂→had₃ path, and record a per-instance `g(G)`
certificate that states only what it proves. Structured vs random are separate provenance tags;
canonical-graph6 dedup (`shortg`/`pynauty.certificate`, never WL-hash) collapses isomorphic
(Γ,S) descriptors within each |Γ|.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Finite abelian group Γ arithmetic (element add/negate, enumerate) | New `pool/sumfree/group.py` (stdlib) | — | Pure integer tuple arithmetic mod invariant factors; no library needed |
| Sum-free set construction (structured + random) | New `pool/sumfree/generate.py` | `generators.cayley` (frozen Z_p reference, byte-locked) | New abelian generalization must NOT edit the frozen corpus generator |
| Triangle-free H → α=2 G adjacency | New `pool/sumfree/generate.py` (`cayley_adj` analog) | — | `list[set[int]]` adjacency, the repo's universal graph shape |
| Exact χ = n − ν(H) | `invariants.matching` (Edmonds blossom, existing) | — | Frozen CHI-01 path, already exact to n≈501 |
| Gate G1–G6 (criticality, connectivity, diameter-2) | `gate.runner` / `gate.checks` (existing) | — | Hard G1/G2 pre-filter runs before any exact solve |
| had₂ / had₃ exact minor bound | `solvers.cbc` + `solvers.cpsat` + `solvers.differential` (existing) | `solvers.problems.had2/had3` (frozen models) | Dual-backend, deterministic single-worker for reported verdicts |
| K_χ minor existence (packing / showpieces) | `search.heuristic.solve` + `corpus.verifier` (existing) | — | Existence-only, scales to n≈2000; verifier is sole truth |
| `g(G)` metric + certificate | New `pool/sumfree/screen.py` + `schema.py` | `corpus.schema` helpers (stdlib boundary) | New metric plumbing is Claude's discretion; reuse CDM schema shape |
| Isomorph dedup across generator streams | `shortg` (subprocess) / `pynauty.certificate` | — | Merged streams need canonical dedup; WL-hash forbidden |
| Instance-level parallelism | `pytest-xdist` / job runner | — | Breadth only; per-verdict determinism stays single-worker |

## Standard Stack

**No new external packages are introduced by this phase.** Every capability is served by the
already-pinned Phase-1 stack. This is a deliberate finding: the abelian-group arithmetic and the
sum-free constructions are elementary integer operations, and every solver/verifier/gate leg
already exists.

### Core (all already pinned — see CLAUDE.md Technology Stack)
| Library | Version | Purpose in Phase 8 | Provenance |
|---------|---------|--------------------|-----------|
| CPython | 3.12.x (uv-pinned) | Runtime; set-iteration determinism anchor | [VERIFIED: CLAUDE.md / uv.lock] |
| networkx | 3.6.1 | ν(H) blossom → χ; graph6 encode for dedup; complement | [VERIFIED: CLAUDE.md] |
| ortools (CP-SAT) | 9.15.6755 | had₂/had₃ optimality proofs; `max_deterministic_time` budget | [VERIFIED: CLAUDE.md] |
| PuLP + CBC | 3.3.2 (hard pin) | Reference had₂ backend for the differential gate | [VERIFIED: CLAUDE.md] |
| nauty | 2.9.3 (brew) | `shortg`/`labelg` canonical dedup of merged (Γ,S) streams | [VERIFIED: CLAUDE.md] |
| pynauty | 2.8.8.1 | in-process `certificate()` dedup + `autgrp()` orbits (vertex-transitive SB) | [VERIFIED: CLAUDE.md] |
| pytest-xdist | latest (pinned) | instance-level fan-out across 64–250 cores | [VERIFIED: CLAUDE.md] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `math`, `itertools`, `hashlib` | — | group arithmetic, factorization (trial division, n≤500), sha256 subseeds | Always; `factorint`-class work is trivial at n≤500 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib group arithmetic | `sympy` (`factorint`, `AbelianGroup`) | Rejected — adds a heavy dependency for n≤500 factorization that trial division does in microseconds; would need slopcheck + a pin. Not worth it. `[ASSUMED]` sympy would work but is unnecessary. |
| `shortg` for cross-stream dedup | `pynauty.certificate` in-process | Both are canonical (nauty). Prefer `shortg` for batch merge, `pynauty.certificate` for in-loop dedup. Do **not** mix the two canonical conventions within one dedup key set (CLAUDE.md: 2.8.8 vs 2.9.3 forms never mixed). |
| CP-SAT `max_deterministic_time` | wall-clock `timeLimit` | On the shared 64–250-core box wall-clock is nondeterministic under contention — a RESISTANT/KILLED verdict could flip run-to-run. Deterministic budget is mandatory for any recorded verdict (Locked Decision 3). |

**Installation:** none — `uv sync` already provides the full stack.

**Version verification:** No new package to verify. All versions were confirmed against PyPI /
brew during Phase-1 stack research (CLAUDE.md "Sources") and are frozen in `uv.lock`.

## Package Legitimacy Audit

> This phase installs **zero** new external packages. The audit is therefore trivially clean.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| *(none — no new installs)* | — | — | — | — | — | — |

**Packages removed due to slopcheck [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

All libraries used are the Phase-1 pinned set (networkx, ortools, pulp, nauty, pynauty,
pytest-xdist), each already legitimacy-audited during Phase-1 stack research and locked in
`uv.lock`. If the planner nonetheless adds any package (e.g. sympy), gate it behind a
`checkpoint:human-verify` and run the Package Legitimacy Gate before install.

## Sum-Free Constructions over Finite Abelian Γ (POOL-2 core)

### The bridge (why sum-free ⟺ our graphs)

`S ⊂ Γ \ {0}` is **sum-free** iff `S ∩ (S+S) = ∅` (no `a,b,c ∈ S` with `a+b=c`). If additionally
`S = −S` (**symmetric**), the Cayley graph `H = Cay(Γ, S)` (edges `{x, x+s}` for `s ∈ S`) is a
well-defined **undirected, triangle-free** `|S|`-regular graph — a triangle `x, x+s, x+s+s'`
would force `s + s' ∈ S`, i.e. a sum relation. `G = H̄` is then an **α=2** graph (α(G)=2 ⟺
H triangle-free). `[CITED: arXiv:2506.17401 §sum-free/Cayley; CLAUDE.md PROJECT (α=2 ⟺ H
triangle-free)]` The existing `generators/cayley.py` is exactly this for `Γ = Z_p`
`[VERIFIED: codebase src/alpha2/generators/cayley.py]`.

**Maximality → edge-maximal-triangle-free (gate G2).** `S` is a **maximal** sum-free set if no
element can be added keeping sum-freeness. Then adding any edge-orbit to `H` closes a triangle,
i.e. `H` is edge-maximal-triangle-free *within Cayley graphs*. Note this is **necessary but not
identical** to G2's global diameter-2 condition: `H` has diameter 2 ⟺ `Γ = {0} ∪ S ∪ (S+S)` (every
non-neighbor difference lies in `S+S`). Some maximal sum-free `S` still leave `H` of diameter >2 →
those instances are **hard-killed by G2** (cheap, expected). The existing Z_p random maximal
symmetric sets all passed (12 corpus instances), so this is a per-instance filter, not a blocker.
`[VERIFIED: codebase gate/checks.py g2 + generators/cayley.can_add]`

### The Green–Ruzsa maximum-density classification (structured target)

Green & Ruzsa (2005) determined the maximum sum-free density `μ(Γ) = λ(Γ)/|Γ|` for **every**
finite abelian Γ, `2/7 ≤ μ ≤ 1/2`, by the arithmetic of the prime divisors of `|Γ| = n`:

| Case (by prime divisors of n) | Max density μ(Γ) | Extremal construction |
|-------------------------------|------------------|-----------------------|
| **Some prime `p ∣ n` with `p ≡ 2 (mod 3)`** (take smallest such p) | `1/3 + 1/(3p)` | Pull back the **middle interval** of `Z_p`: `S = { g : φ(g) ∈ ((p+1)/3, …, (2p−1)/3) }` via a surjection `φ: Γ ↠ Z_p` |
| **No such prime, but `3 ∣ n`** | `1/3` | Union of the two non-zero cosets of an index-3 subgroup, or the middle-interval analog |
| **Every prime divisor `≡ 1 (mod 3)`** | `1/3 − 1/(3m)`, `m` = exponent (largest element order) | Coset-based; for `Z_p`, `p≡1 mod 3`, size `(p−1)/3` |

`[CITED: Green–Ruzsa, "Sum-free sets in abelian groups", Israel J. Math. 147 (2005); arXiv:math/0307142; restated arXiv:2506.17401 and Hassler–Treglown notes]`

> **`[ASSUMED]` label caveat (A1):** the I/II/III *numbering* of these three cases differs across
> sources (some call `3∣n` "Type III", some "Type II"). The **arithmetic conditions and density
> formulas above are the reliable form** — use them, not a numeral. Verify the exact extremal-set
> membership formula against the primary paper before locking a generator (MEDIUM confidence on
> the coset-membership details for the non-cyclic type-II case).

**Worked sizes for the odd grid (checks the formulas):**
- `Z_31`: 31 prime, `31 ≡ 1 mod 3` → third case, `μ = 1/3 − 1/93`, max sum-free size `(31−1)/3 = 10`.
- `Z_53`: `53 ≡ 2 mod 3` → first case, `μ = 1/3 + 1/159`, middle interval `[18,35]`, size 18.
- `Z_31`, `H = Cay(Z_31, S)` with `|S|=10` symmetric → 10-regular, χ = 31 − ν. This is the corpus
  `p=31` family (χ=16 in the TFP corpus; the Cayley χ depends on ν(H)). `[VERIFIED: arithmetic]`

### Structured generator recipes (Claude's discretion — concrete recipes)

**(a) Andrásfai-interval / arithmetic-interval (the "vertex-transitive rigid" family).**
Two canonical structured sum-free sets in `Z_n`:
- **Middle-third interval:** `S = { k : ⌈n/3⌉ ≤ k ≤ ⌊2n/3⌋ } ∪ (negatives)`, symmetrized. Sum-free
  because the smallest sum of two middle elements exceeds `⌊2n/3⌋` (mod-n wrap avoided by the
  symmetric interval around n/2). This is the classic **Andrásfai** vertex-transitive triangle-free
  Cayley graph. `[CITED: Green–Ruzsa extremal construction; standard Andrásfai family]`
- **Residue-class (coset) set:** for `n ≡ 2 (mod 3)`, `S = { x : x ≡ 1 (mod 3) }` is sum-free
  (`1+1 = 2 ≢ 1 mod 3`) and symmetric iff closed under negation (`−1 ≡ 2 mod 3` — so use
  `S = {x ≡ 1} ∪ {x ≡ 2}` = non-multiples of 3, which is **not** sum-free; the correct symmetric
  Andrásfai set is the middle interval). **`[ASSUMED]` A2:** the exact symmetric Andrásfai
  connection set — pin against the Andrásfai-graph definition `And(k) = Cay(Z_{3k−1}, {±1,±4,…})`
  (elements `≡ 1 mod 3` and their negatives) before locking; MEDIUM confidence on the symmetry
  bookkeeping.

**(b) Green–Ruzsa-type (the extremal maximal sets from the classification table above).**
Build the extremal `S` per the max-density case, then verify sum-freeness + maximality
programmatically (raise-based, mirroring `can_add`). These are the "algebraically rigid"
structured instances the LOCKED prediction expects to break first.

**(c) Random-greedy maximal (the pseudorandom counterpoint — generalize the existing code).**
Generalize `generators.cayley.random_maximal_symmetric_sumfree(p, rng)` from `Z_p` to arbitrary Γ:
same greedy loop, but `can_add`/negation use the Γ group operation (component-wise mod invariant
factors). Expected to pack (the adversarial-counter side of the prediction). Counting theory
(Balogh–Liu–Sharifzadeh–Treglown; Hassler–Treglown 2021) confirms these exist in abundance and are
well-understood structurally. `[CITED: arXiv:2108.04615; arXiv:2506.17401]`

### Group representation (no new dependency)

`Γ = Z_{d₁} × … × Z_{d_k}` given by its **invariant factors** `(d₁,…,d_k)`. Elements are integer
tuples; `add` is component-wise mod `dᵢ`; `neg` is component-wise. Enumerate with
`itertools.product`. Factor `n` by trial division to pick the Green–Ruzsa case. Store the
descriptor as `{"invariant_factors": [...], "S": [sorted element tuples]}` — the instance rebuilds
**from the descriptor**, never from an RNG replay (avoids the set-iteration cross-platform hazard;
mirrors `repro/cayley_run.py` storing `sorted(S)`). `[VERIFIED: codebase repro/cayley_run.py,
corpus/schema.provenance_params]`

### Dedup discipline (merged streams — canonical only)

Structured + random generators over many Γ **will** produce isomorphic `G` from distinct `(Γ,S)`.
Because these are **merged streams** (unlike Phase-7's single already-isomorph-free geng stream),
dedup **is** required. Use canonical labeling **only**:
- **Batch:** encode each `H` to graph6 (`networkx.to_graph6_bytes` / write), pipe through
  **`shortg`** (canonical-label + sort + unique) — the dedicated nauty tool. n≤500 is trivial for
  nauty. `[VERIFIED: CLAUDE.md Blueprint 1 canonical-form dedup]`
- **In-process:** `pynauty.certificate(g)` as a dict key. `[VERIFIED: CLAUDE.md]`
- **NEVER** `networkx` Weisfeiler–Lehman hash — not canonical, silent collisions violate exactness
  (CLAUDE.md "What NOT to Use"). `[VERIFIED: CLAUDE.md]`
- Keep the **first** `(Γ,S)` descriptor per canonical class as provenance; log the collapsed
  duplicates. Keep structured/random tags separate — a structured `S` and a random `S` that yield
  the *same* graph is itself an interesting data point, so record the collision rather than
  silently dropping the structured one.

## The `g(G) = (χ − had₃)/χ` Screen — Rigor and Cost (Open Q3 + Q4)

### What each quantity is

- `χ(G) = n − ν(H)`, exact via Edmonds blossom (existing, CHI-01). For near-`(n/3)`-regular `H`
  with a near-perfect matching, `ν = ⌊n/2⌋` so `χ = ⌈n/2⌉` — i.e. **χ ≈ n/2**, a large target.
- `had_k(G)` = max `t` with a `K_t` minor whose branch sets all have size ≤ k. Monotone:
  `had₂ ≤ had₃ ≤ had(G)` (true Hadwiger number). Hadwiger's conjecture: `had(G) ≥ χ`.
- `g(G) = (χ − had₃)/χ`.

### Exactly what `had₃ < χ` establishes — and what it does NOT (the certificate honesty rule)

- `had₃ < χ` (proven) establishes **only**: *there is no `K_χ` minor of `G` whose branch sets all
  have size ≤ 3.* `[VERIFIED: def of had₃; codebase solvers/problems/had3.py]`
- It does **NOT** establish `had(G) < χ`. Branch sets of size ≥ 4 are not excluded, and it is
  **not known that `had = had₃` for α=2 graphs** — seagulls (size-3 paths) are provably needed
  (Chudnovsky–Seymour), and no theorem caps optimal α=2 branch sets at 3. So `g > 0` is a
  **necessary-not-sufficient screen** for a counterexample. `[CITED: Chudnovsky–Seymour, Packing
  seagulls, Combinatorica 32 (2012); ASSUMED A3 that no size-≤3 sufficiency theorem exists — this
  is a negative claim; verified absence in the α=2 literature surveyed, but flag for the author]`
- Conversely `g ≤ 0` (i.e. `had₃ ≥ χ`) with a **verified extracted family** of size ≥ χ **does**
  prove Hadwiger holds on that instance — a genuine, hand-checkable existence result. This is the
  cheap, sound, publishable-per-instance direction.

**Certificate must state literally:** "No `K_χ` minor with branch sets of size ≤ 3 (had₃ = V < χ,
both backends PROVED_OPTIMAL); this does not prove `had(G) < χ`; queued for E3." Never
"counterexample", never "had(G) < χ". This mirrors the CDM pool's radioactive-impossibility
handling. `[VERIFIED: codebase pool/cdm/adjudicate radioactive-connected-complement pattern]`

### Tiering (Open Q — had₂ pre-screen suffices; no new tier needed)

The existing Phase-5 escalation is exactly right for the screen; **no tier bump is needed for
correctness** (the bump that matters is computational, see below):

1. **had₂ exact** (`solve_had2`, dual-backend, `differential_verdict`). If `had₂ ≥ χ` → verify
   family → **g ≤ 0, packs** (done, cheap). If `had₂ < χ` proven → escalate.
2. **had₃ seagull Tier-1** (`solve_had3`, fires only on `had₂ < χ`). The seagull optimum is an
   **upper bound** `U` on true had₃ (`value_is_upper_bound=True`, omits triple–triple conflicts).
   - `U < χ` proven ⇒ true `had₃ ≤ U < χ` ⇒ **`g > 0` candidate** (the impossibility direction is
     sound from the upper bound — see `differential.differential_verdict`). `[VERIFIED: codebase
     solvers/differential.py lines 94–108]`
   - `U ≥ χ` ⇒ inconclusive from the number; escalate to Tier-2 full had₃, **extract + verify** the
     family (a value ≥ χ never licenses a kill by itself — `UnverifiedKill` guard). Verified family
     ≥ χ ⇒ packs; else exact Tier-2 optimum < χ ⇒ candidate.
3. **Connectivity / seagull handling is already correct:** the had₃ triple index enforces
   connectivity by construction (≤1 internal H-edge), and the size-3 verifier checks it. No new
   seagull code is required. `[VERIFIED: codebase solvers/problems/had3.py + Phase-5 verifier
   widening]`

### Cost / feasibility at |Γ| = 31–500 (the honest flag)

**This is the critical planning constraint.** For χ ≈ n/2:
- had₂ ILP variable count ≈ `|E(G)| = C(n,2) − |E(H)|`. `H` is ~`(n/3)`-regular ⇒
  `|E(H)| ≈ n²/6`, so `|E(G)| ≈ n²/2 − n²/6 ≈ n²/3`. At **n=500 that is ≈ 84,000 pair variables**
  plus n singletons, objective ≥ 250.
- **Proving OPTIMALITY** (required for a `had₂ < χ` or `had₃ < χ` verdict — the `g>0` branch) at
  this scale is very likely **infeasible** in any reasonable deterministic budget. This matches the
  existing corpus's ILP frontier (the 12 Cayley exact instances stop at `p ≤ 151`; TFP exact was
  feasible to n≈150–200). `[VERIFIED: codebase repro/cayley_run p∈{31,53,101,151}; FEATURES.md "ILP
  infeasible past n≈150–200"]`
- **Existence (`g≤0`, packing)** via `search.heuristic.solve` + verifier is **cheap and scales to
  n≈2000** (the P1 showpiece target) — it finds a size-≤2 model and the trust root verifies it.

**Consequence for the sweep design (state this in every plan):**
- The `g`-vs-|Γ| curve is **densely populated with verified `g ≤ 0` (packing) points across the
  whole 31–500 range** (cheap heuristic+verify), and **sparsely with exact `g > 0` points only in
  the ~31–150/200 ILP-feasible window.**
- A structured instance that the heuristic **cannot** pack at n where random packs is **RESISTANT**
  (a heuristic miss → exact escalation), **NOT** a reported `g>0` point, until exact `had_k < χ` is
  *proven*. Above the ILP frontier, a resistant structured instance simply **queues for E3** — it is
  the signal to escalate, never a conclusion.
- Therefore "STRUCTURED breaks first" will first manifest empirically as **structured RESISTANT-rate
  climbing above random RESISTANT-rate as |Γ| grows**, with confirmed `g>0` only where optimality
  proofs close. The plot should track *both* verified-g and resistant-rate, structured vs random.

## Architecture Patterns

### System Architecture Diagram

```
  (Γ invariant factors, generator kind, seed)
                │
                ▼
   ┌───────────────────────────────┐
   │ pool/sumfree/generate.py       │   structured (Andrásfai / Green–Ruzsa)
   │  group.py: Γ arithmetic        │─── or random-greedy maximal sum-free S
   │  → S (symmetric sum-free)      │        (RNG contract v2 subseed "gen")
   │  → H = Cay(Γ,S) adjacency      │
   └───────────────┬───────────────┘
                   │ H (list[set[int]]), descriptor {invariant_factors, S}
                   ▼
        canonical dedup (shortg / pynauty.certificate)  ── collapse isomorphic (Γ,S)
                   │
                   ▼
   ┌───────────────────────────────┐
   │ battery/pipeline.run_candidate │
   │  [1] gate G1–G6  ── HARD G1 (ν=⌊n/2⌋, n≥31) / G2 (connected, diam-2)
   │      hard-fail → KILLED-BY-GATE (cheap, no cert)
   │  [2] χ = n − ν(H)  (blossom, exact)
   │  [3] heuristic K_χ  ── HIT → verify → KILLED(packs, g≤0)   ◄── scales to n≈2000
   │      MISS → exact
   │  [4] had₂ dual-backend  ── differential_verdict
   │        AGREED_KILL(≥χ) → verify → g≤0
   │        SHC_CANDIDATE(had₂<χ) → had₃
   │        INSUFFICIENT(timeout) → RESISTANT ──► E3 queue (Phase 11)
   │  [5] had₃ seagull→Tier-2  ── U<χ proven → g>0 CANDIDATE (screen only)
   └───────────────┬───────────────┘
                   ▼
   ┌───────────────────────────────┐
   │ pool/sumfree/screen.py+schema  │   g(G)=(χ−had₃)/χ per-instance certificate
   │  → store.append (verify-at-append)  │  states ONLY "no K_χ minor, branch≤3"
   │  → results log (structured vs random, |Γ|, g, terminal_state)
   └───────────────────────────────┘
                   ▼
        aggregate: g vs |Γ|, structured/random, resistant-rate  (the plot)
```

### Recommended Project Structure (mirror `pool/cdm/`)
```
src/alpha2/pool/sumfree/
├── group.py         # finite abelian Γ: invariant factors, add/neg/enumerate (stdlib)
├── generate.py      # structured (Andrásfai, Green–Ruzsa) + random-greedy maximal S; H=Cay(Γ,S)
├── screen.py        # g(G) computation orchestration over run_candidate outcomes
├── schema.py        # g(G) certificate record (reuse corpus/schema stdlib helpers)
├── store.py         # append-only, verify-at-append (mirror pool/cdm/store.py)
├── verifier.py      # stdlib-only re-check of the g(G) certificate claim
└── adjudicate.py    # per-instance + batch runbook driver (mirror pool/cdm/adjudicate.py)
```

### Pattern 1: Generator mirrors `generators/cayley` but is a NEW module
**What:** New abelian-Γ generator; the frozen `generators/cayley.py` (Z_p, corpus-locked, excluded
from ruff) is **not edited**. **When:** always — corpus byte-reproduction depends on the frozen
module. **Example (structure, not verbatim port):**
```python
# Source: generalizes codebase generators/cayley.py can_add/random_maximal_symmetric_sumfree
def can_add(S, group, a):            # group: the Γ arithmetic object
    b = group.neg(a); T = S | {a, b}
    for u in (a, b):
        for x in T:
            if group.add(u, x) in T: return False   # sum relation
            if group.add(u, group.neg(x)) in T: return False
    return True
```

### Pattern 2: RNG contract v2 — sha256 per-stage subseeds (ROADMAP SC3)
**What:** Derive independent subseeds per stage so changing one stage never shifts another.
**When:** all new P1/P2 instances. **Example:**
```python
import hashlib, random
def subseed(master: int, stage: str) -> int:
    h = hashlib.sha256(f"{master}:{stage}".encode()).digest()
    return int.from_bytes(h[:8], "big")
gen_rng   = random.Random(subseed(seed, "sumfree-generate"))   # feeds random-greedy S
search_rng= random.Random(subseed(seed, "heuristic-search"))   # feeds solve()
```
Store the **descriptor** (`invariant_factors`, `S`) so rebuild is descriptor-driven, not
RNG-replay-driven (cross-platform set-iteration safety; mirrors `repro/cayley_run.py`).

### Pattern 3: Route through `run_candidate`, add `g(G)` around it
**What:** Reuse the battery runbook unchanged; compute `g = (chi − had_k)/chi` from its returned
`chi` and `had_2`/`had_3` fields; the terminal_state (KILLED/SHC-CANDIDATE/RESISTANT) already
encodes the screen outcome. **When:** every gate-surviving instance. `run_candidate` returns
`chi`, `had_2`, `terminal_state`, `verified` — the screen reads these; it never re-solves.
`[VERIFIED: codebase battery/pipeline.run_candidate return dict]`

### Pattern 4: Deterministic solver budget on shared CPU
**What:** Set CP-SAT `max_deterministic_time` (a work-count budget), never wall-clock `timeLimit`,
for any verdict that gets recorded. **Why:** under 64–250-core contention wall-clock is
nondeterministic → RESISTANT/KILLED could flip. `num_workers=1` + pinned `random_seed` for any
reported impossibility (`had_k < χ`). `[CITED: CLAUDE.md sat_parameters.proto; regressions
#3590/#3842/#4839]`

### Anti-Patterns to Avoid
- **Editing `generators/cayley.py`** to add abelian support — breaks corpus byte-reproduction. Make
  a new module.
- **Reporting a heuristic miss as `g>0`** — a miss is RESISTANT (queue state), never a candidate.
- **WL-hash dedup** — not canonical; use `shortg`/`pynauty.certificate`.
- **Wall-clock budgets** on the shared box for recorded verdicts.
- **Calling `had₃ < χ` a counterexample** — it is a screen; certificate states only "no K_χ minor,
  branch sets ≤3".
- **Symmetry breaking on the impossibility branch** — vertex-transitive SB may accelerate existence
  but every reported `had_k < χ` re-runs SB-free (EXACT-06).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ν(H) / χ(G) | matching code | `invariants.matching` (blossom) | Exact, frozen, CHI-01 |
| had₂/had₃ minor | new ILP model | `solvers.cbc/cpsat` + `solvers.problems.had2/had3` | Checksum-gated, dual-backend, frozen |
| Minor verification | trust logic | `corpus.verifier.verify_certificate` | The sole trust root |
| Isomorph dedup | hash | `shortg` / `pynauty.certificate` | Canonical; WL-hash collides |
| Group element factorization | prime sieve libs | stdlib trial division (n≤500) | Trivial at this scale |
| Gate criticality/connectivity | reimplement G1/G2 | `gate.runner` / `gate.checks` | Frozen §2 definitions |
| Vertex-orbit symmetry breaking | custom autgroup | `pynauty.autgrp()` | Assume-and-verify (EXACT-06) |

**Key insight:** Every mathematical leg already exists and is trust-gated. Phase 8's genuinely new
code is **only** the abelian-group arithmetic, the three sum-free generators, the dedup wiring, and
the `g(G)` certificate schema. Everything else is orchestration over frozen machinery — the same
shape as Phase 7's `pool/cdm/adjudicate.py`.

## Common Pitfalls

### Pitfall 1: Confusing the screen with a proof (the radioactive one)
**What goes wrong:** Recording `had₃ < χ` as "found a counterexample" / "had(G) < χ".
**Why:** `had₃ < χ` only excludes size-≤3 branch sets; size-≥4 minors may still reach χ, and no
theorem caps α=2 branch sets at 3. **Avoid:** certificate says literally "no K_χ minor with branch
sets ≤3; does not prove had(G)<χ; E3-queued". **Warning sign:** any certificate string containing
"counterexample" or "had(G) <" outside an E3-survived context.

### Pitfall 2: Wall-clock budgets flipping verdicts on the shared box
**What goes wrong:** Same instance reads RESISTANT under load, KILLED when idle.
**Why:** wall-clock `timeLimit` on a contended 64–250-core box is nondeterministic.
**Avoid:** `max_deterministic_time` + `num_workers=1` for every recorded verdict. **Warning sign:**
a determinism-panel instance whose terminal_state changes between two identical runs.

### Pitfall 3: G1/G2 hard-kill surprising the sweep
**What goes wrong:** Many structured `(Γ,S)` never reach the `g(G)` screen — G1 requires
`ν(H) = ⌊n/2⌋` (near-perfect matching) and G2 requires connected + diameter-2. A structured `S`
whose `H` lacks a near-perfect matching or has diameter >2 is **KILLED-BY-GATE** (cheap, no cert).
**Why:** the gate is a critical-graph filter; not every sum-free Cayley graph is n=2χ−1 critical.
**Avoid:** expect and log gate-kills as a first-class outcome; the `g` plot is over **gate
survivors only**. Report the structured/random gate-survival rate too. **Warning sign:** a plan
that assumes every generated instance yields a `g` value. `[VERIFIED: codebase gate/checks.g1
`nu == n // 2`; g2 connectivity+diameter]`

### Pitfall 4: Editing the frozen Z_p generator
**What goes wrong:** Adding abelian support inside `generators/cayley.py` shifts set-iteration order
→ 296-corpus byte-reproduction CI fails. **Avoid:** new `pool/sumfree/` module; leave the frozen
module and its ruff-exclusion untouched. **Warning sign:** a diff touching `generators/cayley.py`.

### Pitfall 5: Mixing canonical-form conventions in dedup
**What goes wrong:** `shortg` (nauty 2.9.3) and `pynauty` (nauty 2.8.8) canonical forms are not
interchangeable; mixing them in one key set silently fails to dedup. **Avoid:** pick one convention
per dedup key set. **Warning sign:** a dedup dict keyed by both a `shortg` line and a
`pynauty.certificate` from the same batch. `[VERIFIED: CLAUDE.md Version Compatibility note]`

### Pitfall 6: Extremal-set formula drift (Green–Ruzsa case labels)
**What goes wrong:** Using an "I/II/III" numeral from one source with a construction from another.
**Avoid:** key generators off the **arithmetic condition** (smallest prime ≡2 mod3 / 3∣n / all ≡1
mod3), never a numeral; verify each extremal `S` is sum-free + maximal programmatically before
trusting it. **Warning sign:** a generator that trusts a density formula without a `can_add`-style
re-check. `[ASSUMED A1]`

## Code Examples

### Group arithmetic (stdlib, new module)
```python
# Source: standard invariant-factor representation; no library needed
from itertools import product
class Abelian:
    def __init__(self, factors):      # e.g. (31,) or (3, 15) for Z_3 x Z_15
        self.factors = tuple(factors)
        self.n = 1
        for d in factors: self.n *= d
    def elements(self):               # deterministic enumeration
        return list(product(*(range(d) for d in self.factors)))
    def add(self, a, b):  return tuple((x+y) % d for x, y, d in zip(a, b, self.factors))
    def neg(self, a):     return tuple((-x) % d for x, d in zip(a, self.factors))
```

### Middle-third structured sum-free set in Z_n
```python
# Source: Green–Ruzsa extremal / Andrásfai; verify sum-freeness before use
def middle_interval_Zn(n):
    lo, hi = (n + 2) // 3, (2 * n) // 3           # symmetric-ish middle band
    S = {k for k in range(lo, hi + 1)}
    S |= {(-k) % n for k in list(S)}              # symmetrize S = -S
    S.discard(0)
    return S                                       # re-check: S & (S+S) == empty
```

### g(G) from a run_candidate outcome
```python
# Source: codebase battery/pipeline.run_candidate return dict
res = run_candidate("sumfree", n, seed, params={"invariant_factors": factors, "S": sortedS})
chi = res["chi"]
had_k = res["had_2"]                              # or had_3 field when escalated
g = None if had_k is None else (chi - had_k) / chi   # None when RESISTANT (no exact value)
# terminal_state already: KILLED (g<=0), SHC_CANDIDATE (g>0 screen), RESISTANT (E3 queue)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sum-free Cayley only over `Z_p` (12 corpus instances) | Arbitrary finite abelian Γ, structured vs random grid | This phase (P2) | New science — abelian generalization is untouched by the literature (FEATURES.md) |
| α=2 Hadwiger lower bound `had(G) ≥ n/7` (Nguyen 2022, connected matchings) | **`had(G) ≥ n/6`** via a connected matching of size n/6 | **Dec 2025** (arXiv:2512.01401) | The current frontier of "moving the needle"; still far below χ≈n/2 and below Seymour's conjectured (1/3+ε)n |
| Sum-free max density folklore | Green–Ruzsa exact `μ(Γ)` for all abelian Γ, `2/7 ≤ μ ≤ 1/2` | 2005 (Israel J. Math) | Gives the exact structured extremal targets |

**Deprecated/outdated:** none relevant. The Chudnovsky–Seymour seagull min-max (Combinatorica 2012)
remains the exact-branch-set-3 mechanism the `had₃` tier implements.

## The Open Asymptotic This Phase Probes (Open Q1 — precise)

**Seymour's ε-question (the target):** *Does there exist `ε > 0` such that every graph `G` with
`α(G) ≤ 2` has `had(G) ≥ (1/3 + ε)·|V(G)|`?* — **OPEN.** Seymour states that if Hadwiger's
conjecture holds for α=2 it is probably true in general. `[CITED: Seymour, "Hadwiger's conjecture"
survey, web.math.princeton.edu/~pds/papers/hadwiger/paper.pdf; restated in arXiv:2512.01401]`

**What is known (the connected-matching lower bounds):** For `α(G)=2`, a **connected matching** of
size `t` (a matching whose edges are pairwise joined by an edge — i.e. size-≤2 branch sets forming
`K_t`) gives `had(G) ≥ t`. Unconditional linear bounds:
- `had(G) ≥ n/7` — Nguyen (2022). `[CITED: arXiv:2512.01401 background]`
- **`had(G) ≥ n/6`** — Dec 2025 (arXiv:2512.01401, "Dense Matchings of Linear Size in Graphs with
  Independence Number 2"). `[CITED: arXiv:2512.01401]`
- The trivial upper target is `χ = n − ν(H) ≈ n/2`; Hadwiger wants `had ≥ χ`.

**What is conjectured:** the `(1/3+ε)n` bound (Seymour). Even `n/3` is not yet unconditionally
reached in general; the seagull min-max (Chudnovsky–Seymour 2012) and the CLWY/CDM line
(arXiv:2512.17114, verified to n≤11) attack it structurally. `[CITED: Chudnovsky–Seymour,
Combinatorica 32 (2012) 251–282; Costa–Luu–Wood–Yip arXiv:2512.17114]`

**What "moving the needle" would concretely mean for this phase's publishable outcomes:**
1. **Realistic outcome A (packing / clean structured family):** verified `g ≤ 0` across the whole
   structured grid = empirical evidence that structured (algebraically rigid) sum-free Cayley
   graphs *do* pack `K_χ` — supports the "vertex-transitivity makes minors easier" side, a clean
   negative result that **falsifies the LOCKED prediction** and is itself publishable (a new family
   verified for Hadwiger-α=2 at scale, extending the corpus).
2. **Realistic outcome B (a resistant structured tail):** structured RESISTANT-rate climbing above
   random as |Γ| grows, with exact `g>0` confirmed in the ILP-feasible window — an **empirical
   knee** in `g` vs |Γ|. This is a *screening* result (a candidate family for E3), not a
   counterexample; "moving the needle" here = a new **construction** whose size-≤3 minor provably
   lags χ, sharpening where the `n/6→n/2` gap is hardest. Only E3 + a referee can promote it.
3. **Not realistically in-scope:** a *proof* that `had(G) < χ` for some instance — no certificate
   exists for the true Hadwiger number (Asymmetry Principle); the sweep can never conclude it.

## P1 (secondary) — scope notes for the planner

- **Critical-size sweep n=31–32, new seeds:** reuse `generators.tfp.triangle_free_process` +
  `run_candidate("tfp", n, seed)`. n=32 is the even-n critical row (G1 uses `ν = n//2 = 16`, already
  handled). Exact had₂ dual-backend is feasible at n=31–32 (corpus lineage). `[VERIFIED: codebase
  gate/checks.g1 even-n fix; corpus n=31 seed=137]`
- **Showpieces n≈1001–2001:** **existence-only** — `search.heuristic.solve` finds a size-≤2 K_χ
  model, `corpus.verifier` verifies it, store the certificate. **No exact solve** at these sizes
  (ILP far out of range; blossom ν is still exact and fast to n≈2001). A heuristic **miss** is
  RESISTANT, never a result (SRCH-02). `[VERIFIED: codebase; FEATURES.md]`
- **RNG contract v2** (Pattern 2) applies to all new P1 instances; store the descriptor for
  descriptor-driven rebuild.
- P1 is deliberately **secondary** (Locked Decision 1): scope it as a thin driver + the showpiece
  existence loop, not the phase spine.

## Runtime State Inventory

> Not a rename/refactor/migration phase — this is greenfield pool construction. Section omitted per
> template guidance. (The one adjacency-to-frozen-code caution — do not edit `generators/cayley.py`
> — is captured as Pitfall 4, not a runtime-state item.)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Green–Ruzsa I/II/III case *numbering* varies by source; the arithmetic-condition + density formulas are the reliable form | Sum-free constructions | Low — generators key off arithmetic conditions, not numerals; formulas cross-checked on Z_31/Z_53 |
| A2 | Exact symmetric Andrásfai connection set (`≡1 mod 3` + negatives vs middle interval) needs pinning against `And(k)` definition | Structured recipes (a) | Medium — a wrong symmetric set could be non-sum-free; mitigated by mandatory `can_add` re-check |
| A3 | No theorem caps optimal α=2 clique-minor branch sets at size ≤3 (so had₃<χ ≠ had<χ) — a negative claim | g(G) rigor | Medium — if such a theorem existed, had₃<χ would be stronger; author should confirm. Certificate honesty holds either way |
| A4 | ILP optimality-proof frontier for these graphs sits at n≈150–200 | g(G) cost | Medium — the exact crossover is budget/hardware-dependent; the plan should measure it, not assume it |
| A5 | sympy is unnecessary (stdlib trial division suffices at n≤500) | Standard Stack | Low — trivially true at this scale |

**Every `[ASSUMED]` above needs author/data confirmation before it becomes a locked decision.** A1,
A2, A6 are pinnable from the primary papers; A3 is an author question; A4 is answered by the sweep
itself (measure the frontier).

## Open Questions

1. **Exact Green–Ruzsa extremal-set membership for non-cyclic type-II Γ.**
   - Known: the max density formulas and the cyclic middle-interval construction.
   - Unclear: the precise coset-membership formula for the "all primes ≡1 mod 3" case on non-cyclic Γ.
   - Recommendation: pin from Green–Ruzsa (2005) / Hassler–Treglown before locking the structured
     generator; until then, generate candidate extremal sets and verify sum-free+maximal
     programmatically (raise-based).
2. **Which odd non-cyclic Γ to include in the grid** (Z_3×Z_15, Z_3^k, Z_5^k, Z_7×Z_7, …).
   - Known: many exist in 31–500; Z_3^k caps and Z_5^k are literature-interesting (arXiv 2025 Z_5^k).
   - Recommendation: Claude's discretion — start with all cyclic odd n plus a curated non-cyclic
     set (Z_3^4=81, Z_3×Z_27=81, Z_5^3=125, Z_7^2=49→out, Z_3^2×Z_5=45, Z_9×Z_9=81…).
3. **The exact ILP feasibility frontier** (A4) — measure it in an early plan (time had₂ optimality
   at n = 31, 61, 101, 151, 201, …) so the sweep's exact-window boundary is empirical, not assumed.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| CPython 3.12.x | everything | ✓ (uv-pinned) | 3.12.x | — |
| networkx | ν/χ, dedup graph6 | ✓ | 3.6.1 | — |
| ortools CP-SAT | had₂/had₃ optimality | ✓ | 9.15.6755 | — |
| PuLP/CBC | reference had₂ | ✓ | 3.3.2 | — |
| nauty `shortg`/`labelg` | canonical dedup | ✓ (brew) | 2.9.3 | `pynauty.certificate` in-process |
| pynauty | in-proc dedup, autgrp | ✓ | 2.8.8.1 | `shortg` subprocess |
| pytest-xdist | instance parallelism | ✓ | pinned | serial (slower, still correct) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** dedup has two interchangeable canonical routes (do not mix
in one key set). No new install required.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (existing) |
| Config file | `pyproject.toml` `[tool.pytest]` / `pytest.ini` (existing) |
| Quick run command | `uv run pytest tests/pool/sumfree/ -x -q` |
| Full suite command | `uv run pytest` (includes the frozen 296-corpus reproduction + `python -O` canary) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| POOL-2 | sum-free S is sum-free + symmetric + maximal | unit | `pytest tests/pool/sumfree/test_generate.py -x` | ❌ Wave 0 |
| POOL-2 | H=Cay(Γ,S) triangle-free; G=H̄ is α=2 | unit | `pytest tests/pool/sumfree/test_generate.py::test_triangle_free -x` | ❌ Wave 0 |
| POOL-2 | Green–Ruzsa sizes match on Z_31=10, Z_53=18 | unit | `pytest tests/pool/sumfree/test_structured.py -x` | ❌ Wave 0 |
| POOL-2 | canonical dedup collapses isomorphic (Γ,S); WL-hash never used | unit | `pytest tests/pool/sumfree/test_dedup.py -x` | ❌ Wave 0 |
| POOL-2 | g(G) certificate states only "no K_χ minor branch≤3" (no "counterexample") | unit | `pytest tests/pool/sumfree/test_screen.py::test_certificate_honesty -x` | ❌ Wave 0 |
| POOL-2 | RNG v2 subseeds; descriptor rebuild is byte-exact | unit | `pytest tests/pool/sumfree/test_rng_v2.py -x` | ❌ Wave 0 |
| POOL-2/1 | verdict is deterministic (max_deterministic_time, num_workers=1) across two runs | integration | `pytest tests/pool/sumfree/test_determinism.py -x` | ❌ Wave 0 |
| POOL-1 | n=31/32 critical sweep exact had₂ matches corpus lineage | integration | `pytest tests/pool/sumfree/test_p1_sweep.py -x` | ❌ Wave 0 |
| POOL-1 | n≈1001 showpiece heuristic HIT verified by trust root | integration (slow) | `pytest tests/pool/sumfree/test_showpiece.py -x -m slow` | ❌ Wave 0 |
| POOL-2 | frozen `generators/cayley.py` untouched; 296-corpus reproduction still green | regression | `uv run pytest tests/repro -x` | ✅ (existing CI) |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/pool/sumfree/ -x -q`
- **Per wave merge:** `uv run pytest` (full suite incl. 296-corpus + `python -O` canary)
- **Phase gate:** full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/pool/sumfree/test_generate.py` — sum-free/symmetric/maximal + triangle-free (POOL-2)
- [ ] `tests/pool/sumfree/test_structured.py` — Green–Ruzsa/Andrásfai sizes (POOL-2)
- [ ] `tests/pool/sumfree/test_dedup.py` — canonical dedup, WL-hash-forbidden guard (POOL-2)
- [ ] `tests/pool/sumfree/test_screen.py` — g(G) + certificate-honesty (POOL-2)
- [ ] `tests/pool/sumfree/test_rng_v2.py` — sha256 subseeds + descriptor rebuild (POOL-1/2)
- [ ] `tests/pool/sumfree/test_determinism.py` — deterministic-budget verdict stability (POOL-1/2)
- [ ] `tests/pool/sumfree/conftest.py` — shared Γ / small-instance fixtures
- [ ] `tests/pool/sumfree/test_p1_sweep.py`, `test_showpiece.py` — P1 secondary

## Security Domain

> `security_enforcement` is not set in config.json (treat as enabled). This is an offline
> research harness — no auth, network, sessions, or PII. The only real surface is subprocess
> invocation of nauty tools, already handled by the Phase-7 pattern.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no users) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | int-validate + bound Γ invariant factors and n **before** any subprocess/string interpolation; reject non-int/`bool`; cap n (mirror `pool/cdm/generate._validate`, T-7-08) |
| V6 Cryptography | no | sha256 is used only as a deterministic RNG subseed (not a security control) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell injection via nauty args (`shortg`/`labelg`) | Tampering | `subprocess.Popen` with **arg lists only**, never a shell string; validate numeric args first (existing `pool/cdm/generate` pattern) |
| Unbounded generation DoS (huge Γ) | DoS | bound `n ≤ ~500` and validate before spawning; `itertools.product` over bounded factors |
| Untrusted graph6 on dedup roundtrip | Tampering | assert decoded n == requested n (mirror `pool/cdm/adjudicate._decode` V5 boundary) |

## Sources

### Primary (HIGH confidence)
- **Codebase (VERIFIED by direct read):** `generators/cayley.py`, `generators/tfp.py`,
  `battery/pipeline.py` (`run_candidate` return contract), `pool/cdm/{schema,generate,adjudicate,
  store}.py` (the mirror target), `solvers/problems/{had2,had3}.py`, `solvers/differential.py`
  (upper-bound/impossibility soundness), `gate/{runner,checks}.py` (G1 `nu==n//2`, hard/flag tiers),
  `search/heuristic.py` (`solve` signature), `paths.py`, `corpus/schema.py`.
- **CLAUDE.md** — full pinned stack, Blueprints 1/3/4, dedup discipline (WL-hash forbidden),
  CP-SAT determinism regressions, P2 alternatives + Green–Ruzsa classification note.
- Green–Ruzsa, "Sum-free sets in abelian groups," Israel J. Math. 147 (2005); arXiv:math/0307142 —
  max density classification.
- Chudnovsky–Seymour, "Packing seagulls," Combinatorica 32 (2012) 251–282 — the had₃/seagull
  mechanism.

### Secondary (MEDIUM confidence — verified against primary/official)
- arXiv:2512.01401 (Dec 2025), "Dense Matchings of Linear Size in Graphs with Independence Number
  2" — `had ≥ n/6`; Seymour's `(1/3+ε)n` ε-question; n/7 (Nguyen 2022) background.
- Seymour, "Hadwiger's conjecture" survey (web.math.princeton.edu/~pds/papers/hadwiger/paper.pdf) —
  the ε-question and the "α=2 is the crux" framing.
- Hassler–Treglown notes + arXiv:2506.17401 "Notes on sum-free sets in abelian groups" — sum-free
  definitions, symmetric sets, classification restatement, Cayley bridge.
- arXiv:2108.04615 "On maximal sum-free sets in abelian groups"; arXiv:2512.17114 (Costa–Luu–
  Wood–Yip, CDM/CLWY line, verified to n≤11).

### Tertiary (LOW confidence — flagged for validation)
- Exact Green–Ruzsa case *numbering* and non-cyclic type-II coset-membership formula (A1, A2) —
  pin from the primary paper before locking generators.
- Absence of a "size-≤3 branch sets suffice for α=2" theorem (A3) — negative claim; author to
  confirm.

## Metadata

**Confidence breakdown:**
- Codebase integration (mirror pool/cdm, run_candidate wiring, gate interaction): **HIGH** — read
  directly.
- Sum-free constructions + citations: **HIGH** on the bridge and density classification; **MEDIUM**
  on exact structured-set membership formulas (A1/A2).
- g(G) rigor (what had₃<χ proves): **HIGH** — follows from definitions + the solver's own
  upper-bound/impossibility soundness comments.
- ILP cost/feasibility crossover: **MEDIUM** — reasoned from variable counts + corpus frontier;
  measure it (Open Q3).
- Literature asymptotic (Seymour ε-question, n/6, n/7): **HIGH** on statements, **MEDIUM** on the
  exact n/6 proof internals (abstract-level read).

**Research date:** 2026-07-23
**Valid until:** ~2026-08-22 (30 days; stable — the frozen stack and the 2005/2012 anchors do not
move; the Dec-2025 n/6 result is the current frontier and could be improved — re-check arXiv for a
newer α=2 connected-matching bound before publishing).
</content>
</invoke>
