---
phase: 07-p0-cdm-frontier
plan: 05
subsystem: pool/cdm
tags: [cdm, transfer-lemma, proof, monotonicity, alpha2, hadwiger, mtf, lemma-2.5]

# Dependency graph
requires:
  - phase: 07-01
    provides: test_transfer_lemma RED scaffold + embedded n≤11 MTF oracle (134 graph6 literals) + is_edge_maximal_tf Lemma-2.5 leg
  - phase: 07-02
    provides: has_cdm(adj,n) DFS reference — the CDM decider the monotonicity predicate reasons over
provides:
  - docs/proofs/transfer-lemma.md — in-repo transfer-lemma proof (ROADMAP SC3) with proven CDM monotonicity + K_a⊔K_b carve-out + honest A3 residual
  - test_transfer_lemma GREEN — executable Lemma-2.5 equivalence + CDM edge-addition monotonicity predicates
affects: [07-06, 11-escalation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "In-repo proof discipline: prove-what-is-provable (monotonicity, edge-minimal classification), CITE Lemma 2.5, and delimit the claim by an explicitly-flagged assumption (A3) — no overclaiming"
    - "Proof↔predicate link: prose claims backed by executable predicates (is_edge_maximal_tf, has_cdm) run in test_transfer_lemma"

key-files:
  created:
    - docs/proofs/transfer-lemma.md
  modified: []

key-decisions:
  - "Monotonicity proven adjacency-positive: CDM(G)⟹CDM(G+e) because 'connected' + 'dominating' only gain from added edges; M and V(M) unchanged"
  - "Disconnected edge-minimal α=2 graphs classified EXACTLY as K_a⊔K_b (two-clique argument from α=2), legitimate CDM-fails, out of scope, never a Hadwiger event"
  - "A3 (disconnected-complement is the ONLY obstruction) is NOT proven; concrete P4 witness exhibits a connected α=2 graph whose only edge-minimal reduction (2K₂) fails CDM — recorded as non-blocking author-read"

patterns-established:
  - "Reporting discipline honored: proof states exactly what it proves; connected-frontier reach bounded by A3; empirical n≤11 gate is the correctness backstop"

requirements-completed: [POOL-0]

# Metrics
duration: 12min
completed: 2026-07-23
---

# Phase 07 Plan 05: Transfer-Lemma Proof Summary

**In-repo transfer-lemma proof (ROADMAP SC3): a full proof of CDM edge-addition monotonicity plus an exact classification of the disconnected edge-minimal α=2 graphs as K_a⊔K_b, cited to CLWY Lemma 2.5, honestly bounded by the flagged A3 residual (concrete P4 witness) with the empirical n≤11 gate as backstop — and its executable Lemma-2.5 + monotonicity predicates GREEN.**

## Performance
- **Duration:** ~12 min
- **Completed:** 2026-07-23
- **Tasks:** 2
- **Files modified:** 1 (1 created; the predicate test was already finalized-green from 07-01/07-02)

## Accomplishments
- **`docs/proofs/transfer-lemma.md`** (new `docs/proofs/` dir, 208 lines): the transfer lemma re-derived in-repo. (§2) CLWY **Lemma 2.5** cited `[arXiv:2512.17114]` with the four-way TFAE and the empirical `(i)⟺(ii)` corroboration over all 134 n≤11 MTF survivors; (§3) a **full proof of CDM edge-addition monotonicity** `CDM(G)⟹CDM(G+e)` via the adjacency-positive argument; (§4) a **proof** that disconnected edge-minimal α=2 graphs are exactly **K_a⊔K_b** (two-clique argument), legitimate CDM-fails excluded from the connected frontier, never a Hadwiger event; (§5) the honest **A3** residual with a concrete `P4` witness; (§6) an exact statement of what the file does and does not establish.
- **`test_transfer_lemma` GREEN** — Lemma-2.5 equivalence (`is_edge_maximal_tf ⟺ diameter==2` over all 134 n≤11 survivors) + CDM edge-addition monotonicity (every α-preserving non-edge added to C₅ preserves `has_cdm`). `2 passed`.
- **Self-review performed and recorded** (below); the A3 residual is flagged as a **non-blocking author-read**, not a blocking pause (Q1 author-delegated 2026-07-22).

## Task Commits

1. **Task 1: Write the transfer-lemma proof + finalize its predicate test** — `33123f3` (docs). The predicate test was already GREEN (RED scaffold from 07-01, greened when 07-02 delivered `has_cdm`); this task delivered the proof document.
2. **Task 2: Self-review the proof + flag deferred author read (A3)** — no separate code artifact; the self-review and A3 flag are recorded in this SUMMARY and committed with the plan metadata.

**Plan metadata:** (final docs commit)

## Files Created/Modified
- `docs/proofs/transfer-lemma.md` — in-repo transfer-lemma proof (SC3): monotonicity proof + K_a⊔K_b carve-out + Lemma 2.5 citation + A3 residual.

## Decisions Made
- **Monotonicity is the load-bearing proven ingredient.** `CDM(G)⟹CDM(G+e)` holds because M and V(M) are unchanged and both "connected" and "dominating" are adjacency-positive (only gain from added edges). Proven line-by-line; iterated to spanning-supergraph chains.
- **Disconnected edge-minimal α=2 ⟺ K_a⊔K_b, proven exactly.** α=2 + disconnected forces exactly two components, each a clique (else an independent triple). Their complements are the complete-bipartite MTF graphs; they fail CDM legitimately and are carved out.
- **A3 is stated, not asserted.** The clean "MTF-complements ⟹ every connected α=2 graph" needs the extra claim that every connected α=2 graph reduces to a *connected* edge-minimal graph. This is Assumption A3 and is left as an author-read; `P4` is the concrete witness showing it is non-trivial.

## Proof self-review

Rigorous self-review of `docs/proofs/transfer-lemma.md` (Task 2), against the plan's five checkpoints:

1. **Lemma 2.5 usage — correct.** The proof invokes CLWY Lemma 2.5 as a **citation** `[arXiv:2512.17114]`, not a re-derivation, and uses only the `edge-maximal-tf ⟺ diameter-2 ⟺ edge-minimal-complement` edges it needs. The `(i)⟺(ii)` edge is empirically corroborated over all 134 n≤11 survivors via the repo's independent `is_edge_maximal_tf` vs `nx.diameter` (`test_lemma_2_5_edge_maximal_iff_diameter_2`, GREEN). No overclaim: Lemma 2.5 is cited, corroboration is scoped to the frontier actually adjudicated.

2. **Monotonicity argument — logically valid, line-by-line.** With `E(G) ⊆ E(G')`: (a) `M ⊆ E(G) ⊆ E(G')` and disjointness/non-emptiness are properties of the unchanged edge set ⟹ still a matching; (b) any connectedness-witnessing cross edge persists under edge addition, none destroyed ⟹ still connected; (c) `V(M)` unchanged so the dominated set `V(G)∖V(M)` is unchanged, each `w`'s ≥1-endpoint adjacency persists ⟹ still dominating. Both non-trivial conditions are adjacency-positive; the induction to supergraph chains is immediate. **Sound.** Executable analog (`test_cdm_monotone_under_edge_addition` over C₅) GREEN.

3. **Connected carve-out — correct and proven.** The classification "disconnected edge-minimal α=2 ⟹ exactly two cliques ⟹ K_a⊔K_b" is a clean two-line argument from α=2 (three components or an intra-component non-edge each force an independent triple). Their complements are complete-bipartite MTF graphs; `K_a⊔K_b` (a,b≥2) fails CDM (an intra-clique edge cannot dominate the other clique; a cross matching is not connected). Matches `test_cdm_n_le_11.py` (105 connected hold, 29 K_a⊔K_b fail). Catalogued out-of-scope, never a Hadwiger event.

4. **Assumption A3 — assessed; the proof-as-written does NOT justify it.** The monotonicity+Lemma-2.5 machinery certifies CDM only for connected α=2 graphs that lie above a **connected** edge-minimal graph. A3 (disconnected-complement is the *only* obstruction) additionally claims this covers *every* connected α=2 graph. **The proof does not establish A3.** Concrete witness found during review: `G = P4` is connected with α=2 and **holds CDM** (`has_cdm` returns `{01,23}`), yet its only edge-minimal α=2 reduction is `2K₂ = K₂⊔K₂` (P̄4 has diameter 3 ⟹ P4 is not itself an MTF-complement; the unique maximal-tf extension of P̄4 is C₄, complement `2K₂`), which **fails** CDM. So monotonicity from the checked connected MTF-complements lifts *nothing* to P4 — P4's CDM is true but not delivered by this argument. This is squarely A3's research-level content, **not** an out-of-scope logical gap in monotonicity or the carve-out, so per the Task-2 instruction I did **not** halt: I recorded it as the flagged residual. The empirical n≤11 definition gate (all 134 MTF-complements decide as CLWY published) is the hard correctness backstop.

5. **Test status — GREEN.** `uv run pytest tests/pool/cdm/test_transfer_lemma.py -x -q -m "not slow"` → **2 passed**.

**Verdict:** monotonicity (§3) and the K_a⊔K_b classification (§4) are sound and proven; Lemma 2.5 is correctly cited and corroborated; the connected-frontier *completeness* rests on A3, which the proof honestly flags rather than asserts. No genuine logical gap outside A3 was found — proceeding, not halting, per the author-delegated Q1 resolution.

### ⏳ AUTHOR READ PENDING (non-blocking): transfer-lemma A3

The Assumption A3 claim — *"the disconnected-complement carve-out (K_a⊔K_b) is the ONLY obstruction; every connected α=2 graph reduces to a connected edge-minimal graph"* — is a first-new-science assertion that still wants the **author's final read** before any external connected-frontier claim is published. Concrete review anchor: the `P4` witness in `docs/proofs/transfer-lemma.md` §5. Correctness backstop that stands regardless of the prose: the empirical n≤11 definition gate (`test_cdm_n_le_11.py`, all 134 connected MTF-complements vs CLWY's published all-CDM result). This surfaces the existing STATE.md pending todo with a now-concrete witness.

## Deviations from Plan

None — plan executed as written. Notes: (a) the predicate test `tests/pool/cdm/test_transfer_lemma.py` was already finalized and GREEN from 07-01 (RED scaffold) + 07-02 (`has_cdm`); Task 1's remaining artifact was the proof document, which was delivered. (b) The test checks Lemma-2.5 equivalence over the self-contained embedded **n≤11** oracle (134 survivors) rather than building n≤12 at fixture time — this is the 07-01 "no geng-at-fixture-build" discipline, and satisfies the acceptance criterion (Lemma 2.5 equivalence + monotonicity predicates green).

## Threat Register Compliance
- **T-7-11 (unsound transfer lemma over-claiming frontier coverage):** mitigated — monotonicity + K_a⊔K_b classification proven; Lemma 2.5 cited; the connected-frontier reach is explicitly bounded by the flagged A3 residual (no overclaim), with executable predicates (Lemma 2.5 equivalence + monotonicity) GREEN and the n≤11 definition gate as backstop.
- **T-7-12 (disconnected-complement fail mis-stated as a counterexample):** mitigated — §4 carve-out proves K_a⊔K_b are legitimate CDM-fails excluded from the connected frontier, never a Hadwiger event; operationally enforced by the 07-06 classifier.
- **T-7-SC (package installs):** N/A — docs + (already-green) test only; no new packages.

## Known Stubs
None. The proof document is complete prose; its executable predicates pass. The only open item is the intentional, tracked **A3 author-read** (non-blocking, backstopped by the n≤11 gate) — documented above, not a stub in code.

## Issues Encountered
None requiring problem-solving. The A3 residual (P4 witness) was surfaced by the planned self-review and is the designed outcome of the author-delegated Q1 resolution, not an unplanned obstacle.

## Next Phase Readiness
- **07-06** (complement-connectivity classifier + CDM-fail escalation hook) can rely on §4's proven K_a⊔K_b classification to distinguish out-of-scope disconnected-complement fails from (unexpected) connected-complement fails.
- **Author-read A3** remains the single pending item before any *external* connected-frontier claim; it is non-blocking for continued Phase-7 execution and is surfaced in STATE.md.

---
*Phase: 07-p0-cdm-frontier*
*Completed: 2026-07-23*

## Self-Check: PASSED

Created file `docs/proofs/transfer-lemma.md` present on disk (208 lines; grep confirms `monotonicity`, `connected`, `K_a`/`K_b`, `arXiv:2512.17114`, A3/Q1). SUMMARY present. Task-1 commit `33123f3` present in git history. `test_transfer_lemma` → 2 passed.
