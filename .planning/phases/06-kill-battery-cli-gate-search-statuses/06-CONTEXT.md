# Phase 6: Kill Battery CLI (Gate, Search, Statuses) - Context

**Gathered:** 2026-07-22
**Status:** Ready for planning
**Source:** Author decision (single load-bearing fork surfaced by 06-RESEARCH.md, resolved via AskUserQuestion)

<domain>
## Phase Boundary

Phase 6 wires the already-built, already-tested mathematics (exact χ, dual-backend
had₂/had₃, `differential_verdict`, trust-root verifier, hash-chained append-only
store, `build_record`) into one tested CLI running the 7-step runbook per candidate,
with derived statuses and an append-only results log. Phase 6 owns NO new mathematics.

Explicitly out of scope / deferred: nauty/geng exhaustive generation (Phase 7 — not
installed, must not be required here); the full author "trust" sign-off of the gate
(see deferred checkpoint below) beyond the SC1 slice.
</domain>

<decisions>
## Implementation Decisions

### D-01 — Gate kill-semantics: ROLE B (flag, don't kill) for studied pools [LOCKED]
The G1–G6 gate does NOT kill-on-first-failure for instances from studied pools
(TFP / Cayley / seed-137). Instead:
- The **hard-gate** — the only tests that may KILL — is the minimal set: G1 even-n
  criticality (`ν == n//2`, so the n=32 corpus row passes) plus connectivity. seed-137
  passes the hard-gate.
- G3-deep (κ, δ), G4 (ω / clique ratio), G5, G6 run as **flag-only**: they record
  regime info + reason + witness onto the result, but do NOT terminate the runbook
  for studied pools.
- **Rationale (author-confirmed):** seed-137 provably fails the strict §2 gate
  (κ=11<χ=16 at G3; δ=16<17 at G3; ω/n=0.45≫¼ at G4). A literal kill-on-first-failure
  gate would gate-kill seed-137 at G3 before the had₂=17 step — contradicting SC1
  ("gate pass → had₂=17 kill") and the very existence of the 296-certificate corpus.
- **Consequence for SC1:** `alpha2 battery --family tfp --n 31 --seed 137` must run
  gate PASS (hard-gate) → exact χ=16 → heuristic miss routes onward → both backends
  prove had₂=17 → verified kill appended. The G3/G4 flags travel on the record; they
  do not stop the pipeline.

### G1–G6 definitions source [LOCKED]
The exact G1–G6 definitions are the author's original §2, already pinned in-repo at
`.planning/reference/alpha2-program-source.md` (Appendix E §2). Freeze from there —
do NOT invent or paraphrase gate definitions ("never invent the missing hour").
The G6 proven-safe family list (GATE-03) is the enumerated, cited list in that file.

### Search (SRCH-01) [from research]
The current `heuristic.solve()` hard-codes the spanning profile and MISSES seed-137.
The fix is exact and required: iterate non-spanning `(p′, s′)` profiles with
`p′ + s′ = χ` and `2p′ + s′ ≤ n`, with per-profile local-search repair + restarts.
"Not found" is a RESISTANT queue state, NEVER a result.

### Statuses & log (VRF-03 / CLI-02) [from research]
KILLED / SHC-CANDIDATE / RESISTANT are DERIVED views over the immutable corpus +
append-only JSONL results log. Transitions never edit stored records. RESISTANT is
reachable ONLY via exact-method timeout.

### Claude's Discretion
CLI framing (argparse vs. click — no new deps preferred), module layout under
`gate/` and `battery/`, JSONL schema field names (consistent with existing
`build_record` provenance), per-step budget defaults, and JSON logging structure —
all at implementer discretion, consistent with existing patterns.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Gate definitions (authoritative, frozen)
- `.planning/reference/alpha2-program-source.md` (Appendix E §2, ~lines 635–644) — the
  author's original G1–G6 definitions + the G6 proven-safe family list with citations.

### Existing machinery to wire (do not reimplement)
- `src/alpha2/solvers/` — `backend.get_backend`, cbc/cpsat `solve_had2`/`solve_had3`,
  `differential.differential_verdict`, `symmetry`
- `src/alpha2/corpus/` — `verifier.verify_certificate` (trust root), `schema.build_record`,
  the append-only hash-chained store
- `src/alpha2/invariants/` — matching (ν, hence χ = n − ν), witness extraction
- existing `heuristic.py` (spanning-profile searcher to be generalized)

### Project research
- `.planning/research/ARCHITECTURE.md`, `PITFALLS.md` — 7-step runbook + gate patterns
- `.planning/phases/06-kill-battery-cli-gate-search-statuses/06-RESEARCH.md`
</canonical_refs>

<specifics>
## Specific Ideas

- SC1 anchor: `alpha2 battery --family tfp --n 31 --seed 137` end-to-end, deterministic
  in (n, seed), per-step budgets, structured JSON logging.
- Stale-API gotcha (from research): networkx 3.6.1 removed `graph_clique_number`; use
  `nx.max_weight_clique(G, weight=None)` for G4's ω.
- Zero new dependencies. No nauty/geng.
</specifics>

<deferred>
## Deferred Ideas

### Author sign-off checkpoint — "gate trusted" (NON-BLOCKING for SC1)
Before the gate is declared *trusted* for production (beyond the SC1 slice), the author
must sign off on:
1. **B₇ meaning** — appears only in a `FEATURES.md` G6 safe-family screen, absent from
   §2, irrelevant to SC1; confirm what it denotes.
2. **§2 ↔ FEATURES.md label reconciliation** — reconcile the reconstructed vs. original
   G1–G6 labels.
These are a `checkpoint:human-verify` on the gate-trust task; they do NOT block building
or running the seed-137 SC1 slice under D-01.

### Later phases
- Full G5/G6 settled/open map growth (GATE-03) as pools/literature settle classes.
- P7 fitness instrumentation consumers (SRCH-02 exposes restarts-to-solution +
  initial-conflict counts now; consumers come later).
- nauty/geng provisioning → Phase 7 (separate, user-controlled, environment-specific).
</deferred>

---

*Phase: 06-kill-battery-cli-gate-search-statuses*
*Context captured: 2026-07-22 — author decision on gate kill-semantics (Role B)*
