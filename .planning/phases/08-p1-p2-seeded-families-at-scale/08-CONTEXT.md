# Phase 8: P1 & P2 — Seeded Families at Scale — Context

**Gathered:** 2026-07-23
**Status:** Ready for planning
**Source:** In-session discussion + author decisions (AskUserQuestion)
**Requirements:** POOL-1, POOL-2

<domain>
## Phase Boundary

Phase 8 runs the signature TFP family (P1) and the generalized sum-free Cayley family (P2)
at scale under the battery with resistance discipline, probing the open linear-connected-matching
asymptotic. **This phase is deliberately reoriented from the roadmap's balanced framing into a
break-hunt: P2 (sum-free Cayley) is the spine; P1 is secondary.** The author's research goal is to
locate a possible Hadwiger α=2 counterexample in the structured sum-free Cayley family at large χ.

Delivers exact-method-backed adjudication of seeded families; every kill certificated; RESISTANT
instances queued for the survivor protocol (Phase 11). No heuristic-only claims.
</domain>

## Locked Decisions

1. **Focus — break-hunt spine (P2 first).** The primary deliverable is the sum-free Cayley hunt:
   compute the **screened gap `g(G) = (χ(G) − had₃(G)) / χ(G)`** on each instance and track it
   **vs group order** across the structured-vs-random grid. `χ = n − ν(H)` (exact blossom);
   `had₃` = exact size-≤3-branch-set minor lower bound (existing backends). Interpretation:
   `g ≤ 0` ⇒ the K_χ minor already packs (Hadwiger holds on that instance, by construction);
   `g > 0` ⇒ a **candidate** (necessary, not sufficient — small branch sets can't reach χ; may just
   need larger branch sets). Sweep is designed to be **cheap to falsify, loud if real**: plot `g`
   vs |Γ|, look for a knee/upward trend/crossing.
   - **P2 grid:** generalized sum-free Cayley over arbitrary finite **abelian Γ**, structured
     (Andrásfai-interval, Green–Ruzsa-type) **vs** random-greedy maximal sum-free sets, odd
     **|Γ| = 31 – ~500**. Track structured vs random separately.
   - **P1 (secondary, in-phase):** TFP critical-size sweep extended (n=31–32, new seeds), showpieces
     pushed toward n≈1001–2001 via heuristic + verifier engine. Kept, but not the spine.

2. **Prediction (LOCKED pre-data — falsifiable hypothesis, NOT an assumption): the STRUCTURED
   family (Andrásfai-interval / Green–Ruzsa) breaks first** — algebraic rigidity obstructs
   minor-packing, whereas random-greedy sets are expected to pack. Recorded before any Phase 8 data
   exists (timestamped for priority). The adversarial counter to hold in mind: vertex-transitivity
   can instead make minors *easier* to pack (automorphic branch-set copies), in which case structured
   stays clean — the sweep decides which force wins. A flat/negative `g` curve **falsifies** the
   hypothesis and is itself a (small) publishable result.

3. **Execution model.** Runs on a rented **64-core (up to ~250-core) x86-64** box. Parallelize at
   the **instance level** (pytest-xdist / job runner over the grid). **Any *reported* impossibility /
   INFEASIBLE / had₃<χ verdict stays deterministic single-worker (`num_workers=1` + pinned seed)** —
   CLAUDE.md CP-SAT regressions (#3590/#3842/#4839). Cores scale breadth of the hunt, never the
   determinism of a single reported verdict. On shared CPU, solver budgets MUST be deterministic
   (`max_deterministic_time`), never wall-clock.

4. **Epistemic discipline carried forward from Phase 7.** Keep **claim-(a)** ("these specific
   instances were checked") separate from **claim-(b)** ("therefore all connected α=2 graphs of this
   type"). `had₃ < χ` is a **screening signal only** → scaled exact search → **E3 survivor protocol
   (Phase 11)** before anything is called a break. RNG contract **v2** (sha256 per-stage subseeds);
   every instance rebuildable exactly from its stored descriptor. **Zero heuristic-only claims** —
   heuristic resistance is never a result; RESISTANT instances queue, they do not conclude.
   **Never announce a "break" before it survives E3 AND a human referee** (public repo raises the
   stakes on this).

## Claude's Discretion

- Exact plumbing of the `g(G)` metric and its per-instance certificate schema (reuse Phase-7 CDM
  schema patterns + the existing exact backends).
- Generator internals for structured vs random maximal sum-free sets over abelian Γ; sharding.
- How P1's large-n showpieces reuse the heuristic+verifier engine.
- Whether had₃ needs a tier bump for the sweep sizes, or had₂ screening suffices first.

## Canonical References

- ROADMAP.md Phase 8 Success Criteria (POOL-1, POOL-2) — the SC still bind; the reorientation
  changes *emphasis and ordering*, not the criteria.
- CLAUDE.md — Blueprint 3/4 (exact had₂/had₃, CP-SAT determinism), Stack "Stack Patterns by Variant",
  and the P2 alternatives (python-igraph, Green–Ruzsa classification note).
- Phase 7 artifacts: `src/alpha2/pool/cdm/*` (schema/store/verifier patterns to mirror),
  `docs/proofs/transfer-lemma.md` (claim-a/claim-b discipline; the two-clique lemma method).
- `src/alpha2/battery/pipeline.py::run_candidate` (the battery entry the sweep drives).

## Open Questions for Research (RESEARCH.md)

1. The precise statement + citations of the **open linear-connected-matching asymptotic** this phase
   probes — what is known, what is conjectured, what would "moving the needle" mean.
2. How to **generate structured (Andrásfai-interval, Green–Ruzsa) vs random-greedy maximal sum-free
   sets over arbitrary finite abelian Γ** — exact constructions, references, and dedup discipline.
3. `had₃` integration + cost at the sweep's group orders; whether a tier bump or connectivity
   handling (seagulls) is needed to make `g(G)` a trustworthy screen.
4. Rigor of the `g(G)` screen: exactly what `had₃ < χ` does and does not establish about the true
   Hadwiger number at these sizes (so the certificate states only what it proves).
