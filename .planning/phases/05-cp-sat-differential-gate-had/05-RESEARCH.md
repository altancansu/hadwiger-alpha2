# Phase 5: CP-SAT, Differential Gate & had₃ - Research

**Researched:** 2026-07-22
**Domain:** OR-Tools CP-SAT as a second independent exact backend; dual-backend differential agreement gate; size-3 branch-set (had₃) escalation; assume-and-verify symmetry breaking — all layered on the frozen Phase-4 `ExactBackend`/CBC/trust-root stack.
**Confidence:** HIGH — the CP-SAT API surface, determinism knobs, and status/extraction behavior were verified by executing code against the repo's pinned `.venv` (ortools 9.15.6755, CPython 3.12.13) on 2026-07-22; the differential-gate and had₃/symmetry designs are drawn verbatim from the repo's own `.planning/research/ARCHITECTURE.md` and `PITFALLS.md` (which already specify this phase in detail) and the frozen Phase-4 code that Phase 5 extends. Live-probe results are tagged `[VERIFIED: live run in pinned .venv]`.

> **No CONTEXT.md exists for this phase** (the phase directory was empty at research time). There are therefore no locked user decisions to copy verbatim; every design choice below is Claude's-discretion-with-visibility and is flagged in the Assumptions Log / Open Questions where a real decision is pending. The planner (or a `/gsd:discuss-phase` pass) should resolve the flagged items before locking plans.

## Summary

Phase 4 delivered the status-honest `ExactBackend` contract (`solvers/result.py`), a backend-neutral obstruction model (`solvers/problems/had2.py`), the CBC reference adapter (`solvers/cbc.py`), and a stdlib trust root (`corpus/verifier.py`) that is the sole conferrer of truth. Phase 5 adds the *second opinion* and the *escalation machinery* without touching any of those trust boundaries: a CP-SAT adapter (`solvers/cpsat.py`) that translates the **same `Had2Problem`** object into a CP-SAT model, a pure differential harness (`solvers/differential.py`) that makes backend disagreement release-blocking and is the *only* component allowed to license an SHC-CANDIDATE, a size-3 escalation model (`solvers/problems/had3.py` + a `verify_model_record` extension to size-3 branch sets with explicit connectivity), and an assume-and-verify symmetry-breaking discipline whose regression test is the H=C₅ "WLOG vertex unused" disaster.

The CP-SAT integration is genuinely low-risk on the mechanics and genuinely high-risk on the *epistemics*. Mechanically: ortools 9.15.6755 is installed and its snake_case API (`new_bool_var`, `add`, `add_at_most_one`, `maximize`, `CpSolver().solve`, `status_name`, `objective_value`, `best_objective_bound`, `boolean_value`) all work as expected; a C₅ had₂ solve returns `OPTIMAL`, `objective_value == best_objective_bound == 3`, and a correct 3-set family `[VERIFIED: live run]`. Epistemically: CP-SAT's whole reason for existence here is to disagree with CBC when one of them has a bug, and the same soundness traps Phase 4 closed for CBC reappear in CP-SAT form — a `FEASIBLE` (not `OPTIMAL`) status read as exact, connectivity lost by re-encoding (Pitfall 3), nondeterminism from `num_workers>1` (and documented regressions even at `num_workers=1`), and symmetry breaking that fabricates a sub-χ optimum (Pitfall 4). Every one of these is caught by the same discipline: gate `PROVED_OPTIMAL` on `status==OPTIMAL AND round(objective)==round(bound)`, route every extracted family through the frozen trust root, and never let a single backend — or a symmetry-broken run — assign an impossibility-flavored status.

The had₃ tier and the verifier extension are the one place Phase 5 must modify the trust root, and that is the delicate work: size-3 connectivity is **not** a clean local substructure of H (unlike the had₂ edge/cherry/C₄ conflicts), so the model-validity predicate must be respecified for size 3 and the verifier's size gate widened from `{1,2}` to `{1,2,3}` with an explicit "≥2 of the 3 internal pairs are G-edges" connectivity check — with the full Phase-2 mutant suite plus new size-3 mutants re-run to prove the widened verifier still fails closed.

**Primary recommendation:** Build Phase 5 as a thin vertical slice first — `solvers/cpsat.py` solving C₅ had₂ to `PROVED_OPTIMAL=3` and `solvers/differential.py` proving CBC and CP-SAT agree on C₅ end-to-end through the trust root — then harden outward to the seed-137=17 dual-backend panel, decision mode, the had₃ escalation on synthetic size-3-forced instances (with the verifier extension), and the assume-and-verify symmetry discipline (H=C₅ regression). Add **no** new hard dependencies: ortools is already pinned and installed; `pynauty` (optional `[nauty]` extra) is **not installed** and is not required for EXACT-06 if CP-SAT's internal `symmetry_level` is used for the sound path — defer hand-rolled orbit symmetry breaking to when vertex-transitive pools (P2/P3) actually run.

## Architectural Responsibility Map

Tiers here are the project's module layers (this is a solver/verification harness, not a multi-tier app). "Primary tier" is the module that owns the capability; "secondary" is the collaborator.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CP-SAT model translation, solve, status mapping, extraction, version stamp | `solvers/cpsat.py` (the ONLY ortools importer) | `solvers/problems/had2.py` (reused model data) | Mirrors the Phase-4 `cbc.py` confinement: one module owns all CP-SAT quirks; imports ortools lazily via the existing registry |
| had₂ variable/conflict enumeration (shared by both backends) | `solvers/problems/had2.py` (frozen, reused) | — | Already checksum-gated; both backends translate the *same* `Had2Problem` — that shared source is what makes agreement meaningful (independent *encodings*, identical *instance*) |
| had₃ variable/conflict enumeration (size-3) | `solvers/problems/had3.py` (new, backend-neutral) | `problems/had2.py` (tier-0 base) | Same backend-neutral pattern; size-3 conflicts are NOT local substructures of H → must be enumerated and checksummed independently |
| Dual-backend agreement / disagreement / SHC-CANDIDATE licensing | `solvers/differential.py` (new, stdlib-only) | `corpus/verifier.py` (trust root) | The sole component that may compare two backends and the sole gate for any impossibility-flavored (`had₂ < χ`) status; halts the batch on disagreement |
| Size-3 model verification (connectivity + cross-adjacency) | `corpus/verifier.py` (trust-root EXTENSION) | new size-3 mutant tests | Trust root is the only truth-conferrer; widening it from size-{1,2} to {1,2,3} is a deliberate, mutant-guarded change |
| Determinism for recorded claims | `solvers/cpsat.py` params (`num_workers=1` + `random_seed`, or `interleave_search`) | `result.SolveParams` (recorded verbatim) | Any outcome that touches a status decision or the corpus must come from recorded (deterministic) mode with full params + ortools version |
| Assume-and-verify symmetry breaking | `solvers/symmetry.py` or a `solve_*` flag + a differential wrapper | `solvers/cpsat.py` `symmetry_level`; (optional) pynauty `autgrp` | SB may only accelerate the existence branch; a `< χ` result MUST rerun without SB before anything is recorded |
| Family verification (existence side) | `corpus/verifier.py` (frozen for size-≤2; extended for size-3) | `corpus/schema.build_record` (reused) | Unchanged discipline: solver output is an UNTRUSTED proposal |

## Project Constraints (from CLAUDE.md)

- **`ortools == 9.15.6755` pin** — installed and locked in Phase 1 (ENV-01); do not move it. The snake_case CP-SAT API quoted in CLAUDE.md's Blueprint 3 is the correct surface `[VERIFIED: live probe]`.
- **The Asymmetry Principle** — existence is cheap and self-certifying (verifier arbitrates); impossibility is radioactive. Phase 5 is precisely the phase that makes impossibility-flavored claims *possible at all* (dual-backend), so every such path must be gated hardest.
- **Deterministic mode for any recorded/impossibility claim** — CP-SAT `num_workers=1` + pinned `random_seed`, or `interleave_search=true` for deterministic parallel. Default multi-worker CP-SAT is nondeterministic and has documented wrong-INFEASIBLE / nondeterminism regressions (#3590, #3842, #4839, and even single-worker #3943/#3948) — never use it for a reported impossibility.
- **The verifier is the trust root** — solver-found models are UNTRUSTED proposals; only `corpus/verifier.verify_certificate` confers truth. This holds for CP-SAT families exactly as for CBC.
- **`prob.status == OPTIMAL`-analog is not enough by itself** — mirror the Phase-4 two-field discipline: PROVED_OPTIMAL ⇔ `status == cp_model.OPTIMAL AND round(objective_value) == round(best_objective_bound)` (the `had₂ = v requires ObjectiveValue == BestObjectiveBound == v` rule, PITFALLS Pitfall 2).
- **Reporting discipline** — nothing is *found* until the verifier passes; nothing is *absent* until an exact method proves it (and in Phase 5 "proves absence-flavored" means BOTH backends PROVED_OPTIMAL at equal value < χ, in deterministic mode).
- **No `assert` in solver/verifier paths** — `python -O` strips them; every guard raises. Extend the existing `-O` CI canary over at least one CP-SAT-path test.
- **Symmetry breaking is standard but treacherous** — prefer solver-internal `symmetry_level`; hand constraints only from a computed `Aut(H)` with the assume-and-verify rule (CLAUDE.md/PITFALLS Pitfall 4).
- **GSD workflow enforcement** — file changes go through `/gsd-execute-phase`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXACT-03 | OR-Tools CP-SAT backend implements `ExactBackend` for scale, using deterministic single-worker / `interleave_search` for any recorded impossibility claim | CP-SAT adapter design mirroring `cbc.py`; verified API surface + status/extraction/determinism knobs (`num_workers`, `random_seed`, `interleave_search`, `stop_after_first_solution`) live-probed; status-mapping table (Pattern 1); reuses the frozen `Had2Problem` so the two backends are independent encodings of one instance |
| EXACT-04 | Differential harness cross-checks CBC and CP-SAT on shared instances (disagreement is release-blocking); SHC-CANDIDATE only when BOTH prove optimality with equal had₂ < χ | Differential-gate protocol (Pattern 2) lifted from ARCHITECTURE.md §Differential testing + Data-flow step [4]; equal-proven-optima definition, quarantine/halt-on-disagreement, metamorphic verifier-trumps-solver rule; CI agreement panel incl. seed-137=17 |
| EXACT-05 | Branch-set-3 (had₃) escalation behind a flag — triple variables ⟺ ≤1 H-edge (seagull tier first), pruned by empty common H-neighborhood; fires only on had₂ < χ; tested on synthetic size-3-forced instances | had₃ model design (Pattern 3): triple index = connectivity-in-G ⟺ ≥2 of 3 internal pairs are G-edges (≤1 H-edge); conflict pruning by common-H-neighborhood; verifier extension to size-3 with explicit connectivity (Pattern 4); synthetic-instance test strategy (no real SHC candidate exists — 296/296 killed at had₂) |
| EXACT-06 | Symmetry-breaking is assume-and-verify: accelerates the existence branch, but the impossibility branch always reruns without it (H=C₅ "WLOG vertex unused" disaster is a regression test) | Assume-and-verify discipline (Pattern 5) from PITFALLS Pitfall 4; the hand-verified C₅ disaster (had₂=3=χ, "vertex 0 unused" fabricates had₂=2<3); CP-SAT `symmetry_level` sound path; on/off differential; pynauty deferral analysis |
</phase_requirements>

## Standard Stack

### Core (all already pinned and locked — NO new hard packages this phase)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ortools (CP-SAT) | **9.15.6755** (installed, locked) | Second independent exact backend: had₂/had₃ optimality proofs, deterministic recorded mode, model export | State-of-the-art exact CP solver; integer-exact bounds; `status==OPTIMAL` is a genuine optimality proof; snake_case API verified `[VERIFIED: live run + metadata]` |
| pulp / bundled CBC | 3.3.2 / CBC 2.10.3 (frozen Phase 4) | Reference backend in the differential pair | Already the reference lineage; unchanged this phase |
| networkx | 3.6.1 (installed) | ν(H) via existing `invariants/matching.py`; (optional) `is_connected` cross-check for size-3 | Already the χ oracle; no new usage required |
| pytest | 8.3.4 (pinned) | Differential/had₃/symmetry tests as the suite | Existing suite green; add slow-tier dual-backend seed-137 panel |

### Supporting (optional / deferrable)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pynauty | 2.8.8.1 (optional `[nauty]` extra — **NOT installed**) | `autgrp()` → vertex orbits for hand-derived symmetry-breaking constraints | Only if hand SB from `Aut(H)` is chosen over CP-SAT's internal `symmetry_level`. **Not required for EXACT-06's MVP** (the C₅ regression uses a deliberately-invalid hand constraint; the sound path can use `symmetry_level`). Defer install to vertex-transitive pools (P2/P3, Phases 8–9) unless the planner decides otherwise — see Open Questions |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CP-SAT as second backend | PySCIPOpt (SCIP) | A *third* independent opinion for radioactive claims; only needed if lazy separation/constraint handlers become necessary (CDM at larger n). Out of scope now (CLAUDE.md Alternatives) |
| CP-SAT `symmetry_level` (solver-internal SB) | Hand orbit/lex-leader constraints from pynauty `autgrp` | Solver-internal is objective-preserving and sound by construction (no new dep); hand constraints need pynauty + the assume-and-verify guard and only pay off on highly symmetric instances (P2/P3) |
| Deterministic `num_workers=1` + `random_seed` | `interleave_search=true` (deterministic multi-worker) | Single-worker is simplest and clearly deterministic for recorded claims; `interleave_search` is faster but marked Experimental — reserve for exploration/survivor-protocol scaling |

**Installation:** none required for the MVP. `uv sync --frozen --extra dev` reproduces the environment (ortools already present). If the planner elects hand-SB via pynauty: `uv sync --extra dev --extra nauty` (needs a C compiler; pynauty builds its own bundled nauty 2.8.8) — treat as a fenced, optional task.

**Version verification:** `importlib.metadata.version("ortools") == "9.15.6755"` confirmed live; the CP-SAT snake_case API (`new_bool_var`, `add`, `add_at_most_one`, `maximize`, `solve`, `status_name`, `objective_value`, `best_objective_bound`, `boolean_value`, `add_hint`) confirmed present on the installed wheel `[VERIFIED: live run 2026-07-22]`.

## Package Legitimacy Audit

No **new** external packages are installed for the Phase-5 MVP. ortools 9.15.6755 was installed, locked, and audited in Phase 1 (ENV-01). `pynauty` (optional `[nauty]` extra) is a pre-declared, Phase-1-audited dependency that remains un-installed; installing it is an optional, fenced decision, not a new discovery.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| ortools | PyPI | ~9 yrs (Google) | very high (M/mo) | github.com/google/or-tools | not re-run (pinned+installed since Phase 1) | Approved (already locked) |
| pynauty | PyPI | since 2015 | modest | github.com/pdobsan/pynauty | not re-run (Phase-1 declared) | Optional / deferred (not installed) |

**Packages removed due to slopcheck [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

*No slopcheck run was needed this phase — no new package names were introduced. Both entries are pre-existing Phase-1 dependencies from authoritative sources (Google OR-Tools; the canonical pynauty).*

## Architecture Patterns

### System Architecture Diagram

```
                       (H adjacency: list[set[int]], n)
                                   │
                                   ▼
          ┌────────────────────────────────────────────────────────┐
          │ solvers/problems/had2.py   (FROZEN, reused)             │
          │   Had2Problem: Gedges, ss, sp, pp  (checksum-gated)     │
          │ solvers/problems/had3.py   (NEW, backend-neutral)       │
          │   Had3Problem: triples (≤1 H-edge) + size-3 conflicts   │
          └───────────────┬───────────────────────┬────────────────┘
                          │ same model data        │
          ┌───────────────▼─────────┐   ┌──────────▼──────────────┐
          │ solvers/cbc.py (FROZEN) │   │ solvers/cpsat.py (NEW)  │
          │  pulp → PULP_CBC_CMD    │   │  cp_model → CpSolver    │
          │  two-field status gate  │   │  OPTIMAL + obj==bound   │
          │  → ExactOutcome         │   │  num_workers=1/seed     │
          └───────────┬─────────────┘   │  → ExactOutcome         │
                      │                 └──────────┬──────────────┘
                      │  ExactOutcome A            │ ExactOutcome B
                      └──────────────┬─────────────┘
                                     ▼
                  ┌─────────────────────────────────────────────┐
                  │ solvers/differential.py  (NEW, stdlib-only)  │
                  │  both PROVED_OPTIMAL & equal value?          │
                  │   ├ yes & value<χ ─▶ license SHC-CANDIDATE   │
                  │   ├ yes & value≥χ ─▶ agreement (kill path)   │
                  │   ├ unequal proven ─▶ CRITICAL: quarantine,  │
                  │   │                    halt batch (release-  │
                  │   │                    blocking)             │
                  │   └ one non-proven ─▶ insufficient (no claim)│
                  └──────────────────┬──────────────────────────┘
                                     │ family (UNTRUSTED proposal)
                                     ▼
                  ┌─────────────────────────────────────────────┐
                  │ corpus/verifier.py  (trust root)             │
                  │  size ∈ {1,2}  (frozen)                      │
                  │  size 3: ≥2 of 3 internal pairs are G-edges  │
                  │          (connectivity) + all C(k,2) cross   │
                  │  ── ONLY truth-conferring step ──            │
                  └─────────────────────────────────────────────┘

  Assume-and-verify SB wraps a solve: SB on → if result verifies ≥χ, sound
  kill; if result < χ, RERUN WITHOUT SB before differential/record. (EXACT-06)
```

### Recommended Project Structure (additive; nothing existing moves)

```
src/alpha2/solvers/
├── cpsat.py                  # NEW: ortools adapter; ONLY ortools importer; registers "cpsat"
├── differential.py           # NEW: stdlib-only dual-backend agreement gate
├── symmetry.py               # NEW (or a flag in cpsat.py): assume-and-verify SB helpers
└── problems/
    └── had3.py               # NEW: size-3 triple enumeration + size-3 conflict checksum
src/alpha2/corpus/
└── verifier.py               # EXTENDED: size gate {1,2}→{1,2,3} + size-3 connectivity check
tests/
├── test_cpsat_backend.py         # EXACT-03: C5/empty/decision/optimize; -O canary
├── test_cpsat_status_honesty.py  # EXACT-03: FEASIBLE≠OPTIMAL; obj==bound gate; timeout
├── test_differential.py          # EXACT-04: agree; disagreement→CRITICAL/halt; SHC licensing
├── test_differential_panel.py    # EXACT-04: seed-137=17 both PROVED_OPTIMAL (slow)
├── test_had3_problem.py          # EXACT-05: triple enumeration + checksum; synthetic instances
├── test_had3_backends.py         # EXACT-05: had₃ on both backends; verifier size-3 accept/reject
├── test_verifier_size3_mutants.py# EXACT-05: extended trust root fails closed on bad triples
└── test_symmetry_assume_verify.py# EXACT-06: C5 "vertex unused" disaster + on/off differential
```

### Pattern 1: CP-SAT adapter mirroring the CBC status contract (EXACT-03)

The adapter is the CP-SAT analog of `cbc.py`. It must (a) import ortools lazily and register under `"cpsat"` via the existing `register_backend`, (b) translate the shared `Had2Problem` into a CP-SAT model, (c) map `CpSolverStatus` to the LOCKED `Status` vocabulary with a two-condition PROVED_OPTIMAL gate, (d) extract only inside the gate, and (e) return a frozen `ExactOutcome` with `backend="cpsat"` and an ortools version stamp.

**Verified CP-SAT status vocabulary** `[VERIFIED: live run]`: `cp_model.OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, `MODEL_INVALID` (a `CpSolverStatus` enum; use `solver.status_name(st)` for logs).

**Status-mapping table (the CP-SAT analog of the Phase-4 empirical table):**

| CP-SAT `status` | mode | Guard | → `Status` |
|---|---|---|---|
| `OPTIMAL` | optimize | `round(objective_value)==round(best_objective_bound)` | **PROVED_OPTIMAL** |
| `OPTIMAL` | optimize | obj≠bound (should never happen) | **ERROR** |
| `FEASIBLE` | optimize | stopped with incumbent, bound not met | **INCUMBENT_ONLY** |
| `OPTIMAL`/`FEASIBLE` | decision | feasible witness (constant obj / `≥ target_k`) | **MODEL_FOUND** |
| `INFEASIBLE` | decision | target proven unreachable | **PROVED_INFEASIBLE** (radioactive; single-backend) |
| `INFEASIBLE` | optimize | empty family is always feasible → encoding bug | **ERROR** |
| `UNKNOWN` | either | nothing usable | **UNKNOWN** |
| `MODEL_INVALID` | either | build error | **ERROR** |

**Two non-negotiable CP-SAT subtleties** (mirroring Phase-4 Pitfalls 1–2):

1. **`FEASIBLE` is NOT `OPTIMAL`.** CP-SAT returns `FEASIBLE` when it stopped (time/det-time limit) with an incumbent it could not prove optimal — the exact CP-SAT form of the incumbent-as-optimum hole. `exact_value()` must be reachable only from `PROVED_OPTIMAL`; a `FEASIBLE` optimize result is `INCUMBENT_ONLY`. Additionally gate PROVED_OPTIMAL on `round(objective_value)==round(best_objective_bound)` (defense-in-depth per PITFALLS Pitfall 2: `ObjectiveValue == BestObjectiveBound == v`).
2. **`objective_value` is a float** (observed `3.0`) — round it and reuse the Phase-4 recompute discipline: extracted-family count must equal `round(objective_value)`. CP-SAT booleans are exact (no fractional LP junk), so `boolean_value(var)` is clean — but keep the count==objective recompute as the same fail-closed guard the CBC path uses.

**Determinism knobs (all set successfully live** `[VERIFIED]`**):** `solver.parameters.num_workers = 1`, `solver.parameters.random_seed = <pinned>` for recorded/impossibility claims; `interleave_search = True` for deterministic multi-worker (exploration/survivor scaling); `stop_after_first_solution = True` for decision-mode kills; `max_time_in_seconds = <budget>`; `log_search_progress = True` to archive the search log (analog of CBC's `logPath`). `search_branching` is an **enum**, not an int — do not set it with a bare integer (raises `TypeError` `[VERIFIED: live]`); it is not needed for the MVP.

**Version stamp:** `ExactOutcome.backend_version = f"ortools=={importlib.metadata.version('ortools')}"` (e.g. `"ortools==9.15.6755"`) — stdlib metadata read, consistent with the CBC pattern. Feed this into `schema.make_backends` for exact CP-SAT records (`make_backends` already routes `"cp-sat"/"cp_sat"/"cpsat"` in the method string to the `ortools` stamp — verified in `schema.py`).

### Pattern 2: The differential agreement gate (EXACT-04)

A pure, stdlib-only module (`solvers/differential.py`) — no solver import. It consumes two `ExactOutcome`s (CBC + CP-SAT) for the same instance/mode and returns a verdict; it is the **sole** component that may license an SHC-CANDIDATE and the **sole** place a disagreement halts the batch.

**"Equal proven optima" — the exact comparison the gate must make (optimize mode):**
- Both outcomes `status is PROVED_OPTIMAL` **AND** `a.value == b.value`. Only then is the value a *fact*.
- If that fact holds and `value < χ` → **license SHC-CANDIDATE** (a certified refutation of Seymour's strengthening on this instance) — record the value-fact with dual-backend metadata (`agreement={"cbc":v,"cpsat":v}`, both params + versions).
- If that fact holds and `value ≥ χ` → agreement on the kill path; the family goes to the trust root as usual.

**Disagreement handling (release-blocking):**
- Both `PROVED_OPTIMAL` but `a.value != b.value` → **CRITICAL**. This is a solver bug or an encoding-translation bug *by construction* (two exact solvers cannot both be right). Persist both raw outcomes to the results-log, **quarantine the instance, halt the batch** — never skip.
- Exactly one `PROVED_OPTIMAL` (the other `INCUMBENT_ONLY`/`UNKNOWN`/timeout) → **insufficient evidence**, not a disagreement: no impossibility claim, no SHC-CANDIDATE. (Only genuine two-proof conflict is CRITICAL.)

**Metamorphic cross-check (verifier trumps solver):** any verified model of size k proves had₂ ≥ k; if either backend returns `PROVED_OPTIMAL` with `value < k` while a verified size-k family exists (e.g. a stored corpus family, or the other backend's just-verified family), that is a **CRITICAL** error → quarantine, no corpus write. This is the same check the Phase-4 seed-137 test already encodes (`out.exact_value()==17 > 16==len(stored family)`); Phase 5 generalizes it across the pair.

**CI agreement panel:** both backends run `optimize` on a pinned set — C₅ (had₂=3), empty-H (had₂=n), 2–3 tiny TFP instances, and **seed-137 (had₂=17)** — assert both `PROVED_OPTIMAL` with equal value and both extracted families independently pass `verify_certificate`. Fast tier: tiny closed-form instances (ms). Slow tier (`@pytest.mark.slow`, joins the release gate): seed-137 dual-backend optimize (CBC ~149 s + CP-SAT time; see Assumption A2).

### Pattern 3: had₃ (branch-set-3) escalation model (EXACT-05)

**Trigger:** fires *only* on a certified `had₂ < χ` (dual-backend PROVED_OPTIMAL, equal value). No real instance reaches this yet (296/296 are killed at had₂), so the tier is proven against **synthetic size-3-forced instances** — small H where the size-≤2 optimum is < χ but a size-3 family reaches χ.

**Triple variables (the size-3 connectivity constraint, enforced by indexing — the had₂ analog of "pair vars only for G-edges"):** a triple `{a,b,c}` is a legal branch set iff it induces a **connected** subgraph of G, i.e. **at least 2 of the 3 internal pairs are G-edges** ⟺ **at most 1 of the 3 pairs is an H-edge**. (3 vertices are connected iff ≥2 edges present: 2 edges = path, 3 = triangle.) This is exactly the EXACT-05 "triple variables ⟺ ≤1 H-edge" condition. Build the triple index by enumerating vertex triples with ≤1 internal H-edge.
- **Tier 1 (seagull, first):** the ≤1-H-edge triples — Blueprint 4's "seagull tier" covering the Chudnovsky–Seymour mechanism. Objective unchanged (maximize family size); model grows by conflict-sparse Bools.
- **Tier 2 (full had₃, later):** add any remaining G-triangle triples with W(T)-pruned conflicts. Keep behind the same flag; not required for the MVP proof.

**Conflict pruning by empty common H-neighborhood:** a triple T conflicts (is non-adjacent in G) with another set S iff *every* cross pair is an H-edge — i.e. every vertex of S lies in the common H-neighborhood `⋂_{x∈T} N_H(x)`. In a sparse triangle-free H this intersection is *almost always empty* for a connected triple, so triple-conflict constraints are few (Blueprint 4 / reference §5 step 5). Enumerate conflicts from the common-H-neighborhood, not from all pairs. **Warning (Pitfall 3):** unlike had₂, size-3 conflicts are **not** a clean local substructure of H — hand-deriving them is a fresh class of encoding bugs. Mitigations: (a) a size-3 structural checksum independent of the enumeration; (b) the trust-root verifier as arbiter (Pattern 4); (c) the CBC-vs-CP-SAT differential on had₃ (a lost size-3 constraint shows as one backend > the other).

**Both backends:** `solve_had3` on CBC (pulp) and CP-SAT (cp_model), same `Had3Problem` data — the differential harness applies unchanged. (The ARCHITECTURE `ExactBackend` protocol already anticipates `solve_had3`.)

### Pattern 4: Verifier extension to size-3 (trust-root change — the delicate part)

`corpus/verifier.verify_model_record` currently hard-codes `if len(S) not in (1, 2): raise` (line 104-105) and checks "pair is a G-edge" for size-2. Extend it minimally and adversarially:
- **Size gate:** widen to `{1,2,3}`.
- **Connectivity, size 2 (unchanged):** the single pair must be a G-edge (`b not in adj[a]`).
- **Connectivity, size 3 (NEW):** among the 3 internal pairs, **count G-edges (non-H-edges); require ≥ 2** — this is the explicit connectivity check the reference (§4.6 / Pitfall 3) demands. (Optionally cross-check with `networkx.is_connected` on the induced G-subgraph in a test, but the verifier stays stdlib-only.)
- **Cross-adjacency (unchanged):** `_is_conflict(A,B,adj)` is already size-agnostic — it checks every cross pair for all `i<j`; it needs no change and already rejects a triple that is non-adjacent in G to another set.

**Discipline:** the verifier is the trust root and is adversarially frozen. Widening it is a deliberate change that MUST: (1) keep every existing size-≤2 record verifying byte-unchanged (re-run R1/full corpus); (2) pass new size-3 mutants — a disconnected triple (0 or 1 G-edges), a triple with a missing cross-adjacency, a size-4 set (still rejected), a triple aliasing a vertex (disjointness) — each raising `VerificationError`; (3) stay `assert`-free and `-O`-correct. Note `schema.build_record` derives `had_2 = len(model_branch_sets)`; for had₃ the stored invariant is a size-3 family so the field name/semantics need a decision (store as `had_2` when the model is size-≤2, and a distinct `had_3`/`had_le3` fact for the escalation) — flag for the planner (see Open Questions).

### Pattern 5: Assume-and-verify symmetry breaking (EXACT-06)

**The disaster (hand-verified, the regression):** H = Ḡ = C₅ has had₂ = 3 = χ and *every* optimal family is spanning (2 pairs + 1 singleton). The "WLOG vertex 0 is unused" constraint is satisfied by **no** optimal family → the solver returns had₂ = 2 < 3 = χ, a **fabricated SHC counterexample on five vertices**. For TFP complements it is worse: a random maximal-triangle-free H almost surely has *trivial* `Aut`, so any symmetry-style constraint is a pure unsound restriction.

**The discipline (asymmetric use):**
1. **Existence branch:** SB on. If the result is a model ≥ χ that *verifies*, the kill is sound regardless of SB validity (the certificate is self-justifying).
2. **Impossibility branch:** if the SB-on result is `< χ` (any impossibility-flavored value), **rerun WITHOUT SB before recording or entering the differential gate.** SB may never touch an impossibility conclusion. Encode this as a code-path assertion: the SB wrapper cannot emit a `< χ`-flavored outcome to the differential harness without a no-SB rerun.
3. **Sound SB source:** prefer CP-SAT's internal `symmetry_level` (objective-preserving, sound by construction, no new dep). Hand constraints only from a *computed* `Aut(H)` (pynauty `autgrp`), never from assumed family symmetry; if `Aut` is trivial, no SB — full stop.
4. **Differential test:** on small vertex-transitive instances (C₅, other cycles, small Cayley, Petersen) assert `had₂(SB) == had₂(no-SB)`.

**MVP scope for EXACT-06:** the regression (C₅ "vertex unused" → had₂=2, then assume-and-verify rerun → had₂=3) needs **no** pynauty — it deliberately applies an *invalid* hand constraint to prove the discipline catches it. The sound path can rely on `symmetry_level`. Hand orbit-derived SB (pynauty) is only worthwhile when vertex-transitive pools run (P2/P3, Phases 8–9) — recommend deferring the pynauty install unless the planner wants the full orbit machinery now (Open Questions).

### Anti-Patterns to Avoid
- **A lowest-common-denominator solver IR.** Two backends × {had₂, had₃} is a small matrix, not a framework. Each backend translates the shared `Had2Problem`/`Had3Problem` directly; do not build an abstract modeling layer (ARCHITECTURE Anti-Patterns).
- **Reading `objective_value` before the status gate**, or treating `FEASIBLE` as exact.
- **A single backend (or an SB-on run) assigning SHC-CANDIDATE / any `< χ` status.**
- **Widening the had₂ variable index to all vertex pairs / all triples** — that silently admits disconnected branch sets (Pitfall 3, Pitfall 5). Connectivity is enforced by the index, backed by the verifier.
- **Default multi-worker CP-SAT for any recorded/impossibility claim.**

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CP model solving | any custom CP/SAT search | ortools `cp_model` + `CpSolver` | State-of-the-art; `OPTIMAL` is a real optimality proof; already pinned |
| Optimality detection | comparing your own bounds | `status == OPTIMAL` + `objective_value`/`best_objective_bound` | Solver-proven; the two-condition gate is the whole point |
| Determinism | custom RNG plumbing | `num_workers=1` + `random_seed`, or `interleave_search` | Verified parameters; documented pitfalls if hand-rolled |
| Symmetry breaking on symmetric instances | hand "WLOG" constraints | CP-SAT `symmetry_level` (sound), or pynauty `autgrp`-derived + assume-verify | Hand WLOG fabricates sub-χ optima (Pitfall 4) |
| Automorphism group / orbits | any custom graph-iso code | pynauty `autgrp` (if hand SB chosen) | Canonical, correct; the only sound source of SB generators |
| Family verification (incl. size-3) | any solver-side "verified" flag or new checker | extend `corpus/verifier.verify_certificate` | The trust root is the sole truth-conferrer (VRF-01) |
| had₂ model data | re-enumerating per backend | reuse the frozen `Had2Problem` | Shared instance is what makes agreement meaningful; checksum-gated |
| Record assembly / version stamps | ad-hoc dicts | `corpus/schema.build_record` / `make_backends` (already routes `ortools`) | Truncation-impossible; ENV-05 stamps auto-attached |

**Key insight:** Phase 5 is almost entirely *composition + discipline*. The only genuinely new combinatorics is the size-3 triple/conflict enumeration (which is exactly where Pitfall 3 says bugs live, so it gets a checksum + the verifier + the differential). Everything else — status honesty, extraction guards, trust-root routing, record assembly — already exists and is adversarially proven; Phase 5 re-applies it to a second backend.

## Common Pitfalls

### Pitfall 1: CP-SAT `FEASIBLE` read as `OPTIMAL`
**What goes wrong:** a stopped CP-SAT solve returns `FEASIBLE` with an incumbent; read as exact, it fabricates a had₂ value (the CP-SAT twin of the CBC incumbent hole).
**Why it happens:** `objective_value` is equally accessible whether or not optimality was proven.
**How to avoid:** PROVED_OPTIMAL ⇔ `status == cp_model.OPTIMAL AND round(objective_value)==round(best_objective_bound)`; `FEASIBLE`(optimize) → INCUMBENT_ONLY; `exact_value()` reachable only from PROVED_OPTIMAL.
**Warning signs:** any `objective_value` read before a status gate; a "had₂" that changes with the time limit.

### Pitfall 2: Connectivity lost in the CP-SAT re-encoding (and multiplied at size 3)
**What goes wrong:** a natural CP-SAT model ("label each vertex a block, maximize blocks") or a Boolean grid over *all* vertex pairs admits disconnected "branch sets" {a,b} with ab∉E(G); had₂ inflates *plausibly*. Size-3 multiplies it (a triple needs ≥2 internal G-edges).
**Why it happens:** the size-2 connectivity is enforced by variable indexing, never written as a constraint — invisible to a "did I copy all constraints?" audit.
**How to avoid:** index pair vars over G-edges only and triple vars over ≤1-H-edge triples; the verifier checks connectivity explicitly (size-2 G-edge; size-3 ≥2 G-edges); the CBC-vs-CP-SAT differential catches a lost constraint as one backend > the other on a tiny instance.
**Warning signs:** CP-SAT agrees with CBC on most instances but exceeds it on some; a verifier "pair is not a G-edge" rejection; had₃ ≫ had₂ + small.

### Pitfall 3: Nondeterminism / wrong-INFEASIBLE from multi-worker CP-SAT
**What goes wrong:** default `num_workers>1` is wall-clock-dependent and nondeterministic; documented wrong-INFEASIBLE / nondeterminism regressions exist even at `num_workers=1` (#3943/#3948, #3590/#3842/#4839).
**How to avoid:** recorded/impossibility claims use `num_workers=1` + pinned `random_seed` (or `interleave_search=true`), full params + ortools version stored; treat *model bits* as non-reproducible (store them, never assert bit-equality — Assumption A1); the differential gate + verifier — not trust in one solver — is the real safeguard.
**Warning signs:** a recorded claim from exploration mode; a test asserting a specific returned family.

### Pitfall 4: Symmetry breaking that deletes all optimal models
**What goes wrong:** "WLOG vertex 0 unused/singleton/paired" on a vertex-transitive (or trivial-Aut) instance can be satisfied by no optimum → a fabricated had₂ < χ. C₅ is the 5-vertex disaster.
**How to avoid:** assume-and-verify (Pattern 5): SB accelerates existence only; any `< χ` result reruns without SB before recording; sound SB from `symmetry_level` or computed `Aut` only; on/off differential in CI.
**Warning signs:** solve times drop but no had₂(SB)==had₂(no-SB) check; an impossibility branch that consumed an SB-on run.

### Pitfall 5: Disagreement silently skipped instead of halting
**What goes wrong:** two backends return unequal proven optima and the batch continues, burying a solver/encoding bug.
**How to avoid:** the differential gate makes unequal PROVED_OPTIMAL a CRITICAL that quarantines the instance and halts the batch (release-blocking); both raw outcomes persisted.
**Warning signs:** a differential harness that returns a "best of the two" value; any code that picks a winner between backends.

### Pitfall 6: Widening the trust root without re-proving fail-closed
**What goes wrong:** extending `verify_model_record` to size 3 introduces a path that accepts a bad triple, or regresses size-≤2.
**How to avoid:** size-3 mutant suite (disconnected triple, missing cross-adj, size-4, aliased vertex) + re-run the full Phase-2 mutant suite + R1/full corpus (all size-≤2 records verify unchanged) + `-O` canary over the new path.

### Pitfall 7: `assert`-based guards in the new CP-SAT / differential / had₃ paths
**What goes wrong:** `python -O` strips asserts; these are impossibility-adjacent guards.
**How to avoid:** raises only (`NotProvedOptimal`, `ValueError`, `ChecksumError`, a differential `CriticalDisagreement`); extend the `-O` CI canary over at least one CP-SAT-path and one differential test.

## Code Examples

All executed against the pinned `.venv` (ortools 9.15.6755, CPython 3.12.13) on 2026-07-22.

### CP-SAT had₂ optimize on C₅ → PROVED_OPTIMAL = 3
```python
# Source: live run in pinned .venv [VERIFIED]
from ortools.sat.python import cp_model

adj = [{1,4},{0,2},{1,3},{2,4},{3,0}]; n = 5           # H = C5
Gedges = [(u,v) for u in range(n) for v in range(u+1,n) if v not in adj[u]]
m = cp_model.CpModel()
mv = {e: m.new_bool_var(f"m_{e[0]}_{e[1]}") for e in Gedges}
sv = {v: m.new_bool_var(f"s_{v}") for v in range(n)}
for v in range(n):                                       # disjointness as AtMostOne
    m.add_at_most_one([mv[e] for e in Gedges if v in e] + [sv[v]])
for u in range(n):                                       # single-single (H-edges)
    for w in adj[u]:
        if w > u:
            m.add_at_most_one([sv[u], sv[w]])
# (single-pair and pair-pair conflicts added the same way from Had2Problem.sp / .pp)
m.maximize(sum(mv.values()) + sum(sv.values()))

s = cp_model.CpSolver()
s.parameters.num_workers = 1          # deterministic recorded mode
s.parameters.random_seed = 137        # pinned
st = s.solve(m)
# st == cp_model.OPTIMAL; s.objective_value == 3.0; s.best_objective_bound == 3.0
proved_optimal = (st == cp_model.OPTIMAL
                  and round(s.objective_value) == round(s.best_objective_bound))
fam = [e for e in Gedges if s.boolean_value(mv[e])] + [(v,) for v in range(n) if s.boolean_value(sv[v])]
# len(fam) == 3  → route through corpus.verifier.verify_certificate (UNTRUSTED until then)
```

### Decision mode (kill path) + INFEASIBLE detection
```python
# Source: live run [VERIFIED]  — target k=3 feasible → SAT; k=4 infeasible (had2=3)
m.add(sum(mv.values()) + sum(sv.values()) >= target_k)   # no objective (feasibility)
s.parameters.stop_after_first_solution = True            # decision: first feasible
st = s.solve(m)
# st in (OPTIMAL, FEASIBLE) → MODEL_FOUND ; st == INFEASIBLE → PROVED_INFEASIBLE (decision)
```

### Determinism parameters (all set successfully)
```python
# Source: live run [VERIFIED] — every attribute below assigned without error
p = cp_model.CpSolver().parameters
p.num_workers = 1            # recorded/impossibility mode
p.random_seed = 137
p.interleave_search = True   # deterministic multi-worker (exploration; Experimental)
p.stop_after_first_solution = True
p.max_time_in_seconds = 5.0
p.log_search_progress = True # archive search log (CBC logPath analog)
# NOTE: p.search_branching expects an ENUM, not an int — bare int raises TypeError [VERIFIED]
```

### Differential gate (shape)
```python
# Source: ARCHITECTURE.md §Differential testing (stdlib-only; no solver import)
from alpha2.solvers.result import Status

class CriticalDisagreement(Exception): ...   # halts the batch; release-blocking

def differential_verdict(a, b, chi):          # a: CBC outcome, b: CP-SAT outcome (optimize)
    both_proved = a.status is Status.PROVED_OPTIMAL and b.status is Status.PROVED_OPTIMAL
    if both_proved and a.value != b.value:
        raise CriticalDisagreement(f"cbc={a.value} cpsat={b.value}")  # quarantine + halt
    if not both_proved:
        return "INSUFFICIENT"                 # timeout/incumbent → no impossibility claim
    return "SHC_CANDIDATE" if a.value < chi else "AGREED_KILL"   # equal proven value
```

## State of the Art

| Old Approach (Phase 4) | Current Approach (Phase 5) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single engine (CBC); impossibility-flavored values recorded honestly but never battery-conclusive | Two independent engines; a `had₂ < χ` fact requires BOTH PROVED_OPTIMAL at equal value | this phase | SHC-CANDIDATE becomes assignable — the precondition for any impossibility claim |
| had₂ only (size ≤ 2) | had₃ tier (size ≤ 3) behind a flag; verifier widened to {1,2,3} | this phase | The runbook step-5 escalation is real and proven on synthetics before it is ever needed |
| Verifier size gate `{1,2}` | `{1,2,3}` with explicit size-3 connectivity (≥2 G-edges) | this phase | Trust root can arbitrate escalation models |
| No symmetry handling | Assume-and-verify SB; C₅ disaster is a passing regression | this phase | Speedups on symmetric pools without ever contaminating an impossibility branch |

**Deprecated/outdated:** default multi-worker CP-SAT for reported impossibility (documented regressions) — permanently avoided under the deterministic-recorded-mode rule.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CP-SAT `num_workers=1` + fixed `random_seed` is run-to-run deterministic for a fixed ortools version/platform/model — but the returned *optimal family* is not asserted bit-stable (regressions #3943/#3948 acknowledged) | Pattern 1 / Pitfall 3 | Test flakiness only if a test over-asserts model bytes; mitigated by asserting value/status/verifiability, never the family bits |
| A2 | CP-SAT solves seed-137 had₂ optimize to PROVED_OPTIMAL=17 in a CI-tolerable time (order of, or faster than, CBC's ~149 s) | Pattern 2 (panel) | If far slower, the slow-tier budget needs raising; value unaffected. **Not yet measured** — the planner should have Wave-0 measure CP-SAT seed-137 timing |
| A3 | The size-3 "≥2 of 3 internal pairs are G-edges" connectivity rule is the correct and complete size-3 branch-set validity condition (3 vertices connected ⟺ ≥2 edges) | Pattern 4 | A wrong rule corrupts the trust root; mitigated by size-3 mutants + CBC/CP-SAT had₃ differential; graph-theoretically the ⟺ is exact for 3 vertices |
| A4 | The had₃ seagull tier (≤1 H-edge triples) + common-H-neighborhood conflict pruning is sufficient to reach χ on the intended synthetic size-3-forced instances | Pattern 3 | If Tier-1 is insufficient, Tier-2 (G-triangle triples, full had₃) is needed sooner; both are behind the same flag |
| A5 | EXACT-06's MVP does not need pynauty (C₅ regression uses an invalid hand constraint; sound path uses `symmetry_level`) | Pattern 5 | If the planner wants orbit-derived SB now, add the `[nauty]` extra (C compiler needed) — a fenced optional task |
| A6 | A distinct record field/semantics for a size-3 (had₃) model vs the size-≤2 `had_2` is acceptable to add via `schema.build_record` usage without a schema-version bump | Pattern 4 | May require a schema decision; flagged in Open Questions |

## Open Questions

1. **had₃ record schema.** `schema.build_record` derives `had_2 = len(model_branch_sets)` and the verifier's `k` is family size. How is a size-3 escalation model stored — as a `had_2`-typed record (misnamed), a new `had_3`/`had_le3` invariant field, or a schema-version bump?
   - What we know: `model_branch_sets` already supports arbitrary sizes structurally; the verifier just needs the size-3 gate.
   - What's unclear: the invariant field naming and whether the corpus needs a `had_3` fact distinct from `had_2`.
   - Recommendation: add a `had_3`/`had_le3` invariant alongside `had_2` without a version bump if the schema tolerates extra invariant keys (verify `schema.build_record`'s invariant dict is not closed); otherwise a v1→v2 bump. Surface at plan-check.

2. **Symmetry breaking scope for Phase 5.** Ship only the assume-and-verify discipline + `symmetry_level` sound path + C₅ regression (no pynauty), or also install pynauty and build orbit/lex-leader SB now?
   - Recommendation: **defer pynauty** — EXACT-06's testable content (the C₅ disaster regression + on/off differential + the rerun-without-SB code path) is fully satisfiable without it; orbit SB pays off only when P2/P3 vertex-transitive pools run (Phases 8–9). Flag as a decision.

3. **Does the seed-137 corpus record get upgraded to the 17-set family now?** Inherited from Phase 4 (deferred there). Phase 5's dual-backend seed-137=17 panel is the first place *two* engines prove it — arguably the natural moment, but it still touches frozen `repro/`/R1. Recommendation: keep as a fenced, explicit decision (Phase-4 Open-Q carried forward); not required by any EXACT-03..06 success criterion.

4. **`interleave_search` vs `num_workers=1` as the recorded-mode default.** Both are deterministic; single-worker is simplest, `interleave_search` is faster but Experimental. Recommendation: `num_workers=1`+`random_seed` for recorded/impossibility claims; reserve `interleave_search` for exploration.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| ortools (CP-SAT) | `cpsat.py` | ✓ (in `.venv`) | 9.15.6755 | — (pinned) |
| pulp + bundled CBC | differential pair | ✓ | 3.3.2 / CBC 2.10.3 | — |
| networkx | ν(H); optional size-3 connectivity cross-check in tests | ✓ | 3.6.1 | — |
| pytest | test suite | ✓ | 8.3.4 | — |
| pynauty | hand orbit SB (optional) | ✗ (optional `[nauty]` extra, needs C compiler) | — | CP-SAT `symmetry_level` (sound, no dep); assume-and-verify covers EXACT-06 without it |
| Linux x86_64 CI | canonical exact-record platform | ✓ (ubuntu-latest) | — | local runs stamped honestly |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** pynauty — fallback is CP-SAT `symmetry_level` + assume-and-verify (fully covers the EXACT-06 MVP).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 (pinned), via uv |
| Config file | `pyproject.toml` (`markers = ["slow: release/nightly replay gate"]`) |
| Quick run command | `uv run --frozen --extra dev pytest tests/test_cpsat_backend.py tests/test_cpsat_status_honesty.py tests/test_differential.py tests/test_had3_problem.py tests/test_verifier_size3_mutants.py tests/test_symmetry_assume_verify.py -q` |
| Full suite command | `uv run --frozen --extra dev pytest -q` (includes slow: R3 + seed-137 dual-backend optimize) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXACT-03 | CP-SAT status mapping: OPTIMAL+obj==bound→PROVED_OPTIMAL; FEASIBLE→INCUMBENT_ONLY(optimize)/MODEL_FOUND(decision); INFEASIBLE→PROVED_INFEASIBLE(decision)/ERROR(optimize) | unit/integration | `pytest tests/test_cpsat_status_honesty.py -x` | ❌ Wave 0 |
| EXACT-03 | C₅ optimize→3, empty-H→n, decision both legs; family through trust root; ortools version stamped; `-O` canary | integration (fast) | `pytest tests/test_cpsat_backend.py -x` | ❌ Wave 0 |
| EXACT-04 | agreement on C₅/empty/tiny TFP; unequal proven optima→CriticalDisagreement (quarantine/halt); SHC-CANDIDATE only when both PROVED_OPTIMAL & equal value<χ; metamorphic verifier-trumps-solver | unit/integration | `pytest tests/test_differential.py -x` | ❌ Wave 0 |
| EXACT-04 / SC1 | seed-137 dual-backend optimize: both PROVED_OPTIMAL=17, both families verified | integration, `slow` | `pytest tests/test_differential_panel.py -m slow -x` | ❌ Wave 0 |
| EXACT-05 | triple enumeration (≤1 H-edge) + size-3 checksum; conflict pruning by common-H-neighborhood; synthetic size-3-forced instance reaches χ on both backends; fires only on had₂<χ | unit/integration | `pytest tests/test_had3_problem.py tests/test_had3_backends.py -x` | ❌ Wave 0 |
| EXACT-05 | verifier size-3: accepts a connected triple (≥2 G-edges); rejects disconnected triple / missing cross-adj / size-4 / aliased vertex; all size-≤2 records still verify | unit | `pytest tests/test_verifier_size3_mutants.py -x` + full corpus R1 | ❌ Wave 0 |
| EXACT-06 | C₅ "vertex 0 unused" SB fabricates had₂=2<3; assume-and-verify rerun without SB restores had₂=3; had₂(SB)==had₂(no-SB) on small vertex-transitive battery | integration | `pytest tests/test_symmetry_assume_verify.py -x` | ❌ Wave 0 |
| regression | existing R1/R2/R3 + fingerprint + `-O` canary green; `-O` canary extended over one CP-SAT-path + one differential test | regression | `uv run --frozen --extra dev python -O -m pytest tests/test_verifier_dash_O.py -q` + full suite | ✅ existing (+ extension) |

### Sampling Rate
- **Per task commit:** quick run command above (new-module tests only; seconds — tiny instances).
- **Per wave merge:** `uv run --frozen --extra dev pytest -q -m "not slow"` + the `-O` canary.
- **Phase gate:** full suite including `-m slow` (seed-137 dual-backend optimize + R3) green before `/gsd:verify-work`; the differential agreement panel joins the release-gate job automatically via `-m slow`.

### Wave 0 Gaps
- [ ] `tests/test_cpsat_backend.py` — EXACT-03 backend panel (RED-first against `solvers/cpsat.py`)
- [ ] `tests/test_cpsat_status_honesty.py` — EXACT-03 FEASIBLE≠OPTIMAL + obj==bound gate + timeout
- [ ] `tests/test_differential.py` + `tests/test_differential_panel.py` — EXACT-04 gate + slow seed-137 pair
- [ ] `tests/test_had3_problem.py` + `tests/test_had3_backends.py` — EXACT-05 model + both backends + synthetic instances
- [ ] `tests/test_verifier_size3_mutants.py` — EXACT-05 trust-root extension fails closed
- [ ] `tests/test_symmetry_assume_verify.py` — EXACT-06 C₅ disaster + on/off differential
- [ ] **Wave-0 measurement:** CP-SAT seed-137 optimize wall time (feeds Assumption A2 slow-tier budget)
- Framework install: none (pytest pinned and green).

## Security Domain

`security_enforcement` is not set in `.planning/config.json`; there is **no network, auth, user-input, or external-attack surface** in this phase — it is a self-contained mathematical solver/verification harness run in CI and locally. The project's security analog is **epistemic integrity**, already enforced structurally: the trust root confers truth (never a solver), impossibility claims require dual-backend agreement, guards raise (survive `python -O`), and no unverified package is introduced (Package Legitimacy Audit above). The one relevant "supply-chain" note: do **not** auto-download solver packages via `npx`/`pip` outside the frozen lock — the ortools pin is the audited artifact. Standard input-validation (ASVS V5) maps here to the verifier's structural checks on stored records, which already raise on malformed/aliased/out-of-range input (`_build_adj`, range checks) and are extended, mutant-guarded, to size-3 this phase.

## Sources

### Primary (HIGH confidence)
- **Live execution in the pinned `.venv` (2026-07-22)** — ortools 9.15.6755 metadata; CP-SAT snake_case API surface; C₅ had₂ optimize → OPTIMAL, objective_value=best_objective_bound=3.0, 3-set family; decision-mode INFEASIBLE(k=4)/SAT(k=3); all determinism params (`num_workers`, `random_seed`, `interleave_search`, `stop_after_first_solution`, `max_time_in_seconds`, `log_search_progress`) set successfully; `search_branching` int → TypeError
- **Frozen Phase-4 repo code** — `src/alpha2/solvers/{backend,cbc,result}.py`, `solvers/problems/had2.py`, `corpus/{verifier,schema}.py`, `tests/{test_cbc_backend,test_seed137_regression}.py` (the exact contracts, extraction guards, and trust-root size gate Phase 5 extends)
- `.planning/research/ARCHITECTURE.md` — ExactBackend protocol (`solve_had2/had3`), the differential testing protocol (agreement panel, negative-claim rule, metamorphic, disagreement→CRITICAL/halt), the per-candidate data flow (steps [4]/[5]), CP-SAT determinism modes, certificate anatomy with `agreement`
- `.planning/reference/alpha2-program-source.md` — §4 runbook step 4 (symmetry breaking for vertex-transitive) + step 5 (branch-set-3 escalation, seagull conditions, triple variables pruned by common-neighborhood emptiness), G4 seagull threshold
- CLAUDE.md — Blueprint 3 (CBC/CP-SAT division of labor, obstruction enumeration), Blueprint 4 (had₃ tiers 0/1/2), the "What NOT to Use" CP-SAT determinism rows, ortools pin

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` — Pitfall 2 (incumbent-as-optimum, CP-SAT `status==OPTIMAL` + `BestObjectiveBound` rule), Pitfall 3 (connectivity lost in re-encoding; size-3 hazard multiplied), Pitfall 4 (symmetry breaking disaster — the hand-verified C₅ had₂=3 → "vertex 0 unused" → had₂=2, assume-and-verify discipline), CP-SAT determinism/regression references (#3943/#3948; interleave_search)
- OR-Tools issue lineage cited across repo docs (#3590/#3842/#4839 wrong-INFEASIBLE/nondeterminism) — behavior avoided by construction, not re-reproduced here

### Tertiary (LOW confidence)
- Chudnovsky–Seymour *Packing seagulls* capacity/seagull specifics — the exact seagull conditions for Tier-2 should be lifted from the paper when Tier-2 is implemented (Blueprint 4 marks the capacity transcription MEDIUM); the Tier-1 ≤1-H-edge triple condition is derived directly and is HIGH

## Metadata

**Confidence breakdown:**
- CP-SAT backend (EXACT-03): HIGH — API, status, extraction, determinism all live-verified against the installed wheel; mirrors a proven Phase-4 adapter
- Differential gate (EXACT-04): HIGH — protocol taken verbatim from the repo's own ARCHITECTURE.md and reuses the frozen `Status`/`ExactOutcome` contract
- had₃ model + verifier extension (EXACT-05): MEDIUM-HIGH — the size-3 connectivity rule and seagull-tier index are derived and graph-theoretically exact for 3 vertices; Tier-2 conflict specifics and the record-schema naming are flagged (A3/A4/A6)
- Symmetry breaking (EXACT-06): HIGH on the discipline and the C₅ regression (hand-verified in PITFALLS); MEDIUM on whether pynauty is wanted now (flagged, deferrable)

**Research date:** 2026-07-22
**Valid until:** stable under the pins (ortools==9.15.6755 / pulp==3.3.2 / CBC 2.10.3 / CPython 3.12.13); re-verify only if a pin moves.
