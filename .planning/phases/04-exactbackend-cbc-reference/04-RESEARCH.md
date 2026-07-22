# Phase 4: ExactBackend & CBC Reference - Research

**Researched:** 2026-07-21
**Domain:** Exact ILP solving (PuLP 3.3.2 / bundled CBC 2.10.3) behind a status-honest interface; had₂ obstruction encoding; corpus regression integration
**Confidence:** HIGH — every load-bearing claim below was verified by executing code in THIS repo's pinned `.venv` (pulp 3.3.2, bundled CBC 2.10.3, the project's own `triangle_free_process`), or read directly from the installed pulp 3.3.2 source. Empirical results are tagged `[VERIFIED: live run in pinned .venv]`.

## Summary

Phase 4 closes the program's central soundness hole: the legacy `ilp_had2` reads `pulp.value(prob.objective)` without gating on solver status, so a timed-out CBC incumbent reads as an exact had₂. This research **reproduced the hole live in the pinned environment**: a 20-second-limited CBC run on seed-137 returned `prob.status == 1 (Optimal)` with an *unproven* incumbent of 17 (true bound at stop: 20.879), and a 0.05-second run returned a garbage fractional objective of 23.25 with `status == 0`. The only correct PROVED_OPTIMAL gate in pulp 3.3.2 is `status == LpStatusOptimal AND sol_status == LpSolutionOptimal` — `prob.status` alone is provably insufficient (read directly from `pulp/apis/coin_api.py::get_status`, which maps a "Stopped … objective value" solution file to `LpStatusOptimal` + `LpSolutionIntegerFeasible`).

The rest of the phase is de-risked by direct experiment: the obstruction-based constraint generator (H-edges / cherries / C₄ diagonals) was implemented in scratch and produces **byte-identical constraint sets** to the naive O(|E_G|²) loop on both seed 1 (726/998/131) and seed 137 (3782/1913/177), with all three structural-checksum formulas matching exactly. CBC then proves **had₂(seed-137) = 17 PROVED_OPTIMAL with a 17-set family in ~149 s single-thread** (macOS Rosetta; Linux CI will differ in wall time, not value), while decision mode (`Σ ≥ k`, constant objective) resolves k=16 and k=17 in ~2.5 s each — a 60× spread that dictates the battery architecture: decision mode for kills, optimize mode only for exact-value/radioactive questions, and the seed-137 optimize regression marked `slow`.

The one genuine design decision the planner must front-load is the seed-137 corpus reconciliation. The frozen 296-corpus stores the Appendix D.3 16-set literal (R1 asserts byte-equality to it; `repro/` drivers are declared frozen). The Phase-4 regression must therefore live **in the test suite via an in-memory schema-v1 record routed through the trust root** — not as a corpus mutation. Upgrading the stored corpus record to the 17-set family is possible without breaking R2/R3 (H-hashes unchanged, R3 replays only baseline+cayley) but requires deliberately amending R1's literal and touching a frozen driver — flagged below as an explicit option needing a lockstep, single-commit decision, recommended as a separate final plan or deferral.

**Primary recommendation:** Build `solvers/` as three modules — stdlib-only `result.py` (Status enum + frozen ExactOutcome whose exact-value accessor *raises* unless PROVED_OPTIMAL), backend-neutral `problems/had2.py` (obstruction enumeration + raise-based structural checksum), and `cbc.py` (PULP_CBC_CMD adapter with the two-field status gate, logPath-always, bound parsing, binary-version stamping) — and pin the live-verified numbers in this document as regression constants.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Status contract / result types | `solvers/result.py` (stdlib-only) | — | Must be importable by future battery/verify code without pulling pulp; unrepresentability enforced at the type, not at call sites |
| Variable + conflict enumeration, structural checksum | `solvers/problems/had2.py` (pure, backend-neutral) | tests (naive reference) | One enumeration, unit-tested once, translated by every backend; Phase 5's CP-SAT consumes the same data (ARCHITECTURE.md Pattern 2) |
| pulp/CBC translation, solve, status mapping, extraction, version stamp | `solvers/cbc.py` | — | The only module importing pulp; owns all CBC quirks (sol_status, log parse, Rosetta note) |
| Family verification | existing `corpus/verifier.py` (trust root, untouched) | `verify/model.py` (legacy, byte-frozen) | Solver output is an UNTRUSTED proposal; only the stdlib trust root confers truth |
| Regression anchoring (seed-137, CI panel) | tests/ | corpus (read-only) | Phase 4 must not mutate the frozen 296 corpus or the frozen repro drivers |
| Version/platform stamping in records | `corpus/schema.make_backends` (existing) + `cbc.py` version probe | — | schema.py stays stdlib-only; the actual CBC binary version string is produced by cbc.py and passed in |

## Project Constraints (from CLAUDE.md)

- **`pulp==3.3.2` hard pin** — PuLP 4.0 removes the bundled CBC / reworks the solver API; the pin is what keeps Appendix C byte-compatible. Do not touch the lockfile's pulp entry.
- **Deterministic single-thread CBC**: `PULP_CBC_CMD(msg=0, timeLimit=…)` reference invocation; CBC is single-threaded unless `threads` is passed (verified in `coin_api.py::getOptions` — `-threads` is only emitted when set). Pass `threads=1` explicitly for self-documentation.
- **The Asymmetry Principle**: existence is cheap to certify (verifier arbitrates); impossibility is radioactive. Every `had₂ < χ`-flavored outcome in this phase is single-backend and must be recorded as such — SHC-CANDIDATE assignment is Phase 5 (dual-backend), out of scope here.
- **Reporting discipline**: nothing counts as found until the independent verifier passes; nothing counts as absent until an exact method proves it — and in this phase "proves" means PROVED_OPTIMAL, never an incumbent.
- **GSD workflow enforcement**: file changes go through `/gsd-execute-phase` etc.
- **Blueprint 3 (CLAUDE.md stack section)** is the authoritative sketch for the obstruction enumeration and the CBC/CP-SAT division of labor; this phase implements the CBC half only.
- **macOS caveat**: the bundled CBC osx wheel is x86_64-only → runs under Rosetta 2 on Apple Silicon (verified: `.venv/.../solverdir/cbc/osx/i64/cbc` executed successfully here). Linux x86_64 is the canonical reference-regeneration platform (ENV-05); `schema._cbc_under_rosetta()` already stamps this.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXACT-01 | `ExactBackend` interface computes had₂(G) and extracts a model, with a status contract separating `PROVED_OPTIMAL` from `INCUMBENT_ONLY` (never reading an objective under a timeout as exact) | Status-mapping table below (empirically verified against pinned pulp 3.3.2 + CBC 2.10.3, including the treacherous `status=Optimal` on timeout-with-incumbent); `ExactOutcome` design with raising accessor; deterministic unit tests of the mapping + one live timeout integration test |
| EXACT-02 | pulp/CBC backend implements `ExactBackend` as reference solver (reproduces the 296) using obstruction-based constraint generation replacing the O(\|E_G\|²) loop, guarded by the structural-checksum assertion | Obstruction enumeration implemented and proven set-equal to the naive loop on seeds 1 & 137; checksum formulas validated live (177/1913/3782 on seed-137); had₂(seed-137)=17 PROVED_OPTIMAL reproduced with 17-set family; CI-panel + reconciliation design below |
</phase_requirements>

## Standard Stack

### Core (all already pinned and locked — NO new packages this phase)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PuLP | 3.3.2 (hard pin, installed) | ILP modeling + `PULP_CBC_CMD` driver | Appendix C byte-compatibility; bundles CBC binaries `[VERIFIED: installed wheel inspected]` |
| CBC (bundled) | **2.10.3**, build 2019-12-15 | Reference MILP engine | `[VERIFIED: live run — banner "Version: 2.10.3" from `.venv/.../solverdir/cbc/osx/i64/cbc`]` |
| networkx | 3.6.1 (installed) | ν(H) via existing `invariants/matching.py` only | Already the χ oracle; Phase 4 adds no new networkx usage |
| pytest | 8.3.4 (pinned Phase 3) | Test harness | Existing suite: 54 tests green |

**Installation:** none. `uv sync --frozen --extra dev` reproduces the environment. Any plan task that would add a dependency is out of scope.

**Version verification:** `pulp.__version__ == "3.3.2"` and CBC banner `Version: 2.10.3` were both confirmed by execution in the project `.venv` on 2026-07-21. The CBC binary version probe for record stamping: run `[PULP_CBC_CMD().path, "-exit"]` via subprocess and parse the `Version:` line `[VERIFIED: live run]`.

## Package Legitimacy Audit

No external packages are installed in this phase. All solver dependencies (pulp 3.3.2 + bundled CBC) were installed, locked, and audited in Phase 1 (ENV-01). **Packages removed due to slopcheck [SLOP] verdict:** none. **Packages flagged [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
                              (H adjacency: list[set[int]], n)
                                          │
                                          ▼
            ┌─────────────────────────────────────────────────────┐
            │ solvers/problems/had2.py  (pure, backend-neutral)    │
            │  enumerate: G-edges (pair vars), vertices (single    │
            │  vars), conflicts from H-obstructions:               │
            │    single–single = H-edges                           │
            │    single–pair   = cherries (2-subsets of N_H(v))    │
            │    pair–pair     = C₄ diagonals (2-subsets of        │
            │                    N_H(a)∩N_H(b) per G-edge {a,b})   │
            │  → raise-based STRUCTURAL CHECKSUM gate:             │
            │    nss=|E(H)|, nsp=ΣC(deg,2), npp=½ΣC(codeg,2)       │
            └───────────────┬─────────────────────────────────────┘
                            │ Had2Problem (vars + conflict sets, plain data)
                            ▼
   mode="decision"(target_k) ─┐  ┌─ mode="optimize"
            ┌─────────────────┴──┴──────────────────────────────┐
            │ solvers/cbc.py  (the ONLY pulp importer)           │
            │  build LpProblem → PULP_CBC_CMD(msg=0, threads=1,  │
            │  timeLimit, logPath=tmp) → solve                   │
            │  read (prob.status, prob.sol_status) → Status      │
            │  extract family iff status permits (0.5 threshold  │
            │  + integrality guard + recompute objective)        │
            │  parse log for bound ("Upper bound:") on stops     │
            │  stamp backend_version = pulp 3.3.2 + CBC 2.10.3   │
            └───────────────┬────────────────────────────────────┘
                            │ ExactOutcome (frozen; family = UNTRUSTED proposal)
                            ▼
            ┌───────────────────────────────────────────────────┐
            │ battery-facing consumption (tests now, CLI Phase 6)│
            │  outcome.exact_value() raises unless PROVED_OPTIMAL│
            │  family → schema.build_record → corpus/verifier    │
            │  (trust root) — ONLY the verifier confers truth    │
            └───────────────────────────────────────────────────┘
```

### Recommended Project Structure (additive; nothing existing moves)

```
src/alpha2/solvers/
├── __init__.py
├── result.py            # Status enum, SolveParams, ExactOutcome (stdlib-only)
├── backend.py           # ExactBackend Protocol + get_backend registry (stdlib-only)
├── cbc.py               # pulp/CBC adapter; status mapping; extraction; version probe
└── problems/
    ├── __init__.py
    └── had2.py          # obstruction enumeration + structural checksum (stdlib-only)
tests/
├── test_solver_result.py        # status-contract unit tests (no solver runs)
├── test_had2_problem.py         # obstruction==naive set-equality @ n=31; checksums; brute force n≤8
├── test_cbc_backend.py          # tiny-instance solves; decision+optimize; -O canary
├── test_cbc_status_honesty.py   # timeout test: incumbent can NEVER read as exact
└── test_seed137_regression.py   # had₂=17 PROVED_OPTIMAL + 17-set family via trust root (slow)
```

This matches ARCHITECTURE.md's refactor milestone 5 layout (`solvers/result.py, backend.py, problems/had2.py, cbc.py`) `[CITED: .planning/research/ARCHITECTURE.md §Refactor table]`.

### Pattern 1: The status contract — pulp → Status mapping (the heart of EXACT-01)

**Ground truth, verified by execution against pinned pulp 3.3.2 + CBC 2.10.3:**

| Live experiment | `prob.status` | `prob.sol_status` | `pulp.value(objective)` | Correct Status |
|---|---|---|---|---|
| seed-137 optimize, 300 s limit, finished in 149 s | 1 `Optimal` | 1 `LpSolutionOptimal` | 17.0 | **PROVED_OPTIMAL** |
| seed-137 optimize, **20 s limit** (stopped with incumbent) | **1 `Optimal`** ⚠️ | **2 `LpSolutionIntegerFeasible`** | 17.0 (bound was 20.879!) | **INCUMBENT_ONLY** |
| seed-137 optimize, 0.05 s limit (stopped, nothing) | 0 `Not Solved` | 0 `NoSolutionFound` | **23.25 — fractional garbage** ⚠️ | **UNKNOWN** |
| trivially infeasible probe | −1 `Infeasible` | −1 `LpSolutionInfeasible` | **1.0 — garbage** ⚠️ | **PROVED_INFEASIBLE** (decision) / **ERROR** (optimize) |
| decision mode k=16 / k=17, feasible | 1 `Optimal` | 1 `LpSolutionOptimal` | 0 (constant obj) | **MODEL_FOUND** |

`[VERIFIED: live runs in pinned .venv, 2026-07-21]`

Three non-negotiable consequences:

1. **`prob.status == LpStatusOptimal` is NOT a proof of optimality.** The installed `coin_api.py::get_status` maps a solution file starting `"Stopped … objective value …"` to `(LpStatusOptimal, LpSolutionIntegerFeasible)` — the timeout-with-incumbent case *deliberately reports status Optimal*. The PROVED_OPTIMAL gate is the conjunction: `prob.status == pulp.LpStatusOptimal and prob.sol_status == pulp.LpSolutionOptimal` (both constants are top-level pulp exports; `prob.sol_status` exists — verified). `[VERIFIED: pulp 3.3.2 source `apis/coin_api.py` lines 338–367 + live run]`
2. **Never read `pulp.value(prob.objective)` or `var.value()` before the status gate.** On `Not Solved` the variable values are the LP relaxation (fractional, 23.25 observed); on `Infeasible` they are stale garbage (1.0 observed). Extraction happens only for `{PROVED_OPTIMAL, MODEL_FOUND, INCUMBENT_ONLY}`, and always with an integrality guard (each binary within 1e-6 of 0/1 → else ERROR) and an objective recomputation (`sum of extracted binaries == reported value` → else ERROR). This also defends against the documented pulp#517 non-integer-solution failure class `[CITED: github.com/coin-or/pulp/issues/517]`.
3. **`optimize` mode can never be legitimately infeasible** (the empty family is always feasible) — an Infeasible result in optimize mode is an encoding bug and maps to **ERROR**, not PROVED_INFEASIBLE. Similarly Unbounded (objective ≤ n structurally) maps to ERROR.

**Making "had₂ < χ from an incumbent" unrepresentable** (success criterion 1): use a frozen dataclass with invariant enforcement plus a raising accessor —

```python
# solvers/result.py — stdlib only
from dataclasses import dataclass
from enum import Enum, auto

class Status(Enum):
    MODEL_FOUND       = auto()  # decision: feasible witness produced (→ verifier)
    PROVED_OPTIMAL    = auto()  # optimize: value exact; bound == value
    PROVED_INFEASIBLE = auto()  # decision: target k proven unreachable (RADIOACTIVE; single-backend in Phase 4)
    INCUMBENT_ONLY    = auto()  # stopped; value = best found, NOT exact
    UNKNOWN           = auto()  # stopped; nothing usable — values are garbage, never surfaced
    ERROR             = auto()  # integrality/recompute/encoding failure

class NotProvedOptimal(Exception): ...

@dataclass(frozen=True)
class ExactOutcome:
    problem: str; mode: str; status: Status
    value: int | None          # populated ONLY for PROVED_OPTIMAL / INCUMBENT_ONLY / MODEL_FOUND
    bound: int | None          # dual bound; == value iff PROVED_OPTIMAL
    family: tuple[tuple[int, ...], ...] | None   # UNTRUSTED proposal
    backend: str; backend_version: str
    params: "SolveParams"; wall_time_s: float

    def __post_init__(self):
        if self.status in (Status.UNKNOWN, Status.ERROR) and self.value is not None:
            raise ValueError("value must be None for UNKNOWN/ERROR")
        if self.status is Status.PROVED_OPTIMAL and self.value != self.bound:
            raise ValueError("PROVED_OPTIMAL requires value == bound")

    def exact_value(self) -> int:
        """The ONLY battery-facing exact accessor. Raises unless proven."""
        if self.status is not Status.PROVED_OPTIMAL:
            raise NotProvedOptimal(f"status={self.status.name}: no exact value exists")
        return self.value
```

The status-honesty test then has two legs: (a) **deterministic unit tests** feeding every `(status, sol_status)` pair through the mapping function (no solver invocation — fast, exhaustive); (b) **one live integration test**: solve seed-137 optimize with a short `timeLimit` and assert the outcome status is in `{INCUMBENT_ONLY, UNKNOWN}` (which of the two depends on whether CBC found the incumbent in time — observed: 0.05 s → UNKNOWN, 20 s → INCUMBENT_ONLY; a robust test accepts either) and that `exact_value()` raises `NotProvedOptimal`. Because these are impossibility-adjacent guards, checks in `result.py`/`cbc.py` are **raise-based, never `assert`** (the `python -O` canary must cover the new modules, consistent with Phase 2/3 discipline).

### Pattern 2: Obstruction-based constraint generation + structural checksum (EXACT-02)

The four constraint classes of the had₂ ILP and their H-substructure bijections (all counts live-verified):

| Class | Constraint | H-substructure | Checksum formula | seed-1 | seed-137 |
|---|---|---|---|---|---|
| disjointness | `Σ mv[e∋v] + sv[v] ≤ 1` per v | — | n | 31 | 31 |
| single–single | `sv[u]+sv[v] ≤ 1` | H-edges | `nss = |E(H)|` | 131 | 177 |
| single–pair | `sv[v]+mv[(a,b)] ≤ 1` | cherries (P₃ centered at v) | `nsp = Σ_v C(deg_H(v),2)` | 998 | 1913 |
| pair–pair | `mv[e₁]+mv[e₂] ≤ 1` | C₄s of H (the two diagonals) | `npp = ½ Σ_{u<v} C(codeg_H(u,v),2)` | 726 | 3782 |

`[VERIFIED: live run — obstruction enumeration and the naive O(|E_G|²) loop produce EQUAL SETS (not just counts) on seeds 1 and 137 at n=31; all checksums match]`

The enumeration (validated implementation, from the scratch run):

```python
# solvers/problems/had2.py — pure stdlib; adj is H's adjacency (list of sets)
def enumerate_had2(adj, n):
    Gedges = [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]
    ss = {(u, v) for u in range(n) for v in adj[u] if v > u}          # H-edges
    sp = set()
    for v in range(n):                                                # cherries at v
        nb = sorted(adj[v])
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                sp.add((v, (nb[i], nb[j])))                           # {a,b}⊆N_H(v) ⇒ ab is a G-edge (H triangle-free)
    pp = set()
    for (a, b) in Gedges:                                             # C4 diagonals
        W = sorted(adj[a] & adj[b])                                   # common H-neighborhood of a G-edge
        for i in range(len(W)):
            for j in range(i + 1, len(W)):
                c, d = W[i], W[j]                                     # cd is a G-edge (H triangle-free ⇒ C4 chordless)
                if len({a, b, c, d}) == 4:
                    pp.add(frozenset(((a, b), (c, d))))               # frozenset DEDUPS the double discovery
    return Gedges, ss, sp, pp
```

**Two correctness subtleties the planner must encode as explicit task guidance:**

1. **Each C₄ is discovered twice** — once from diagonal {a,b}, once from diagonal {c,d}. The `frozenset` set-membership dedups it. Without dedup, `npp` doubles and the equal-count assert vs the naive loop fails. (The naive loops in C.3/C.4 iterate ordered `i<j` pairs and add each once.)
2. **Triangle-freeness is what makes the enumeration total**: every 2-subset of `N_H(v)` is automatically a G-edge (else H has a triangle), and every C₄ of H is chordless so both diagonals are legal pair variables. The enumeration must therefore only ever be run on triangle-free H — cheap to re-assert (raise-based) at problem-build time, consistent with Pitfall 10's defensive re-assertion rule.

**The structural checksum is the build gate** (success criterion 3): after enumeration, compute `nss/nsp/npp` *independently* — degrees straight from `adj`, codegrees via direct `len(adj[u] & adj[v])` over all u<v pairs (O(n²·deg); ~7.5M set-ops at n=501, fine) — and **raise** (never `assert`; `-O` discipline) on any mismatch. A missing conflict class shows up as a zero/mismatch instantly; an inverted predicate (the radioactive under-count direction) shows up as npp exploding or collapsing. The **naive O(|E_G|²) loop is retained as test-only code** (in `tests/test_had2_problem.py`, or a `_naive` helper in the test module) for the equal-set assert at n=31 — it must not remain a production path.

Also pin the cheap domain sanity checks: `had₂ ≥ ω(G) = α(H)` always (singletons on a max clique; seed-137: ω=14), and metamorphically `had₂ ≥ len(stored verified family)` on every corpus instance touched by the CI panel — a PROVED_OPTIMAL value below a stored verified family size is a CRITICAL encoding bug (verifier trumps solver).

### Pattern 3: Decision vs optimize modes (success criterion 4)

- **decision(target_k):** constant objective (`prob += 0`), add `Σ mv + Σ sv ≥ target_k`. Outcomes: feasible → MODEL_FOUND (family extracted, length ≥ k, → verifier); Infeasible → PROVED_INFEASIBLE; Stopped → UNKNOWN. **Live timing: k=16 and k=17 on seed-137 in 2.3–2.6 s** vs 149 s for the optimality proof — decision mode is the kill path, 60× cheaper. `[VERIFIED: live run]`
- **optimize:** maximize `Σ mv + Σ sv`. PROVED_OPTIMAL iff the two-field gate passes; INCUMBENT_ONLY/UNKNOWN otherwise; Infeasible/Unbounded → ERROR.
- **value AND bound always recorded:** for PROVED_OPTIMAL, `bound = value` by definition. For stopped runs, parse the CBC log — pass `logPath=<tmpfile>` on **every** exact solve (this also un-suppresses the "Stopped on time limit" evidence that `msg=0` hides — Pitfall 2). Observed log grammar with the bundled 2.10.3 on `-max` problems: `Result - Optimal solution found` / `Result - Stopped on time limit`, then `Objective value: X`, and on stopped runs **`Upper bound: Y`** (the dual bound; observed `20.879` on the incumbent run and `23.250` on the no-incumbent run) plus `Gap:`. Parse `Upper bound:`; if absent (defensive), fall back to the trivial bound `n` and record the fallback provenance. `[VERIFIED: live logs, 2 stopped runs + 1 optimal run]` Caution: this log grammar is CBC-2.10.3-specific — one more reason the pulp pin is load-bearing; keep the parser tolerant and covered by a fixture test using the captured log text.
- **Params recorded verbatim** in every ExactOutcome: `timeLimit`, `threads=1`, seed n/a for CBC (no seed option passed; single-thread CBC is deterministic for a fixed binary+platform+model file), wall time.

### Pattern 4: Extraction → trust root (never verifier-free)

Extraction stays the Appendix-C shape (`value() > 0.5` over pair vars then singleton vars) but adds: integrality guard, objective recomputation, internal disjointness pre-check — then the family goes to the **existing trust root** as an in-memory schema-v1 record:

```python
# the independently-verified path for a solver family (no corpus write needed)
M, U, nu2 = extract_witness(adj, n)                      # emission-time witness
rec = schema.build_record(
    provenance=schema.provenance_seed("triangle_free_process_complement", 31, 137,
                                      "Bohman uniform triangle-free process"),
    H_edges=H_edges, nu_H=nu, chi_G=chi,
    model_branch_sets=[list(s) for s in family],         # FULL family — 17 sets; had_2 derived = 17
    matching_M=M, tutte_berge_U=U,
    method="exact ILP (CBC): had_2(G)=17", omega_G=14, verified=True)
verifier.verify_certificate(rec)                          # raises on any defect; k=17 ≥ chi=16 supported
```

`schema.build_record` already derives `had_2 = len(model_branch_sets)`, supports k ≥ χ, and refuses k < χ — `fam[:chi]` truncation is structurally impossible (Phase 2 decision). `verify_model_record` checks k ≥ χ, sizes ∈ {1,2}, disjointness, pairs-are-G-edges, and all C(k,2) cross-adjacencies — it verifies a 17-set family at χ=16 with no changes. The legacy `verify/model.py` stays byte-frozen and untouched.

**Backend version stamping** (success criterion 4 + Phase-2 stub closure): `cbc.py` exposes `cbc_binary_version()` — subprocess `[PULP_CBC_CMD().path, "-exit"]`, parse the `Version:` banner line → `"2.10.3"` — recorded in `ExactOutcome.backend_version` as e.g. `"pulp==3.3.2 / CBC 2.10.3"` and available to override `make_backends`' current `"bundled-with-pulp-3.3.2"` provenance string when exact records are built. `[VERIFIED: live banner parse]`

### Pattern 5: Seed-137 reconciliation with the frozen corpus (success criterion 2)

**Current frozen state (all verified by reading the committed artifacts):**
- Corpus record (31, 137): the Appendix D.3 **16-set literal** (9 pairs + 7 singletons), `had_2=16` derived, `method="exact ILP (CBC): had_2(G)=17"` (documents true value; routes `reproduction.kind=semantic`), `omega_G=14`.
- `tests/test_corpus_r1.py` asserts `d3["model_branch_sets"] == D3_MODEL` (byte-equality to that 16-set literal) **and** `len(corpus)==296` with family counts (284, 12).
- Phase 3 declared "the `repro/` drivers are frozen forever after"; `repro/seed137.py`'s own docstring says "the true had_2(G)=17 family arrives in Phase 4 via CBC".
- R2 compares H-edge hashes only (unaffected by any model change); R3 replays baseline + cayley drivers only (seed137.py not replayed); the manifest hashes `H_edges` only.

**Recommended reconciliation — regression-as-test, corpus untouched (do this unconditionally):**
The Phase-4 seed-137 regression is `tests/test_seed137_regression.py` (marked `slow`; ~2.5 min single-thread): regenerate H from `random.Random(137)` via the frozen generator, solve optimize via the new CBC backend, assert `status == PROVED_OPTIMAL`, `exact_value() == 17`, `bound == 17`, family length 17, then route the family through the trust root via an in-memory record (code above). Nothing in `data/corpus/`, `repro/`, or R1/R2/R3 changes — they *cannot* break. This satisfies the roadmap's literal success criterion ("passes the seed-137 regression … full 17-set family extracted and independently verified").

Additionally assert **compatibility with the frozen record**: the stored 16-set D.3 literal still verifies (R1 already does this) and `17 == exact_value() > 16 == len(stored family)` — the metamorphic direction (solver value ≥ any verified family size).

**Corpus upgrade to the 17-set stored family (the Phase-2 "drop in" promise) — OPTION, not default:** it is *possible* without breaking R2/R3 or the manifest (H-hashes unchanged; R3 doesn't replay seed137), but it necessarily (a) edits the frozen `repro/seed137.py` (or adds a driver + edits frozen `freeze.py`'s ordered sequence), (b) rewrites the committed corpus's last record, and (c) amends R1's `D3_MODEL` byte-equality assertion in the same commit — three deliberate exceptions to Phase-3 freeze discipline, plus a solver dependency inside the freeze path (149 s, platform-stamped Rosetta locally vs canonical Linux). The semantic reproduction contract (ENV-05) makes a locally-solved committed family legitimate *evidence* (semantic records promise value + a verifying model, not byte-stable model bits), but the freeze-discipline cost is real. **Recommendation: keep Phase 4 to the regression-as-test; surface the corpus upgrade as an explicit decision** (either a clearly-fenced final plan in this phase or a deferral note to the phase that builds the Falsification-Rule harness, which is the first actual consumer of k=17-level corpus storage — Phase 11). See Open Questions.

### Pattern 6: CI panel (296-lineage exact values, every commit vs slow)

Two tiers, matching the existing CI split:

- **Every-commit (fast) panel:** tiny closed-form instances solved to PROVED_OPTIMAL in milliseconds — H=C₅ (had₂=3=χ, the SB-disaster instance, doubling as a future Phase-5 anchor), H=empty (had₂=n), H=perfect matching, plus a brute-force differential: exhaustive had₂ by enumeration for n ≤ 8 random triangle-free H vs CBC optimize (Pitfall 1's decisive test). Plus **decision-mode kills** on seed-1 and seed-137 at k=χ=16 (~2.5 s each, live-verified) with families verified by the trust root — this is the "reproduces 296-lineage exact values" every-commit leg (χ-level values from the frozen corpus, exact-method confirmed).
- **Slow/release panel (`-m slow`, joins R3 in the release gate):** seed-137 optimize regression (had₂=17, ~149 s), optionally one Cayley p=31 decision kill.

Budget note for the planner: the existing full suite runs in ~seconds; the seed-137 optimize test alone adds ~2.5 min → it must carry `@pytest.mark.slow` and join the nightly/tag release-gate job, not the every-commit job.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MILP solving | any custom branch-and-bound | bundled CBC via `PULP_CBC_CMD` | Reference lineage; byte-compatible with Appendix C |
| Solution-file/status parsing | custom .sol reader | `prob.status` + `prob.sol_status` (pulp's own parse) | pulp 3.3.2's `get_status` is the pinned, inspected behavior; only the *log bound* needs a (tiny, fixture-tested) parser |
| Family verification | any solver-side "verified" flag | existing `corpus/verifier.verify_certificate` | The trust root is the only truth-conferring component (VRF-01) |
| Witness extraction | new Gallai–Edmonds code | existing `invariants/witness.extract_witness` | Already adversarially tested (CHI-02) |
| Record assembly / version stamps | ad-hoc dicts | `corpus/schema.build_record` / `make_backends` | Truncation-impossible, ENV-05 stamps auto-attached |
| ν(H) | anything | `invariants/matching.matching_number` | CHI-01 AST guard pins the blossom call there |

**Key insight:** Phase 4 is a *composition* phase on the trust side — the only genuinely new logic is enumeration (pure combinatorics, checksum-gated), status mapping (5 statuses, exhaustively unit-testable), and extraction guards. Everything downstream of "family produced" already exists and is adversarially proven.

## Common Pitfalls

### Pitfall 1: `prob.status == Optimal` on a timed-out incumbent
**What goes wrong:** pulp 3.3.2 maps "Stopped … objective value X" sol-files to `LpStatusOptimal` + `LpSolutionIntegerFeasible` — reproduced live (20 s limit → status=1, incumbent 17, true bound 20.879).
**How to avoid:** PROVED_OPTIMAL ⇔ `status==LpStatusOptimal AND sol_status==LpSolutionOptimal`. Unit-test the mapping on all pairs; live-test with a short timeLimit.
**Warning signs:** any code reading `prob.status` alone; any `pulp.value(...)` before a status gate.

### Pitfall 2: Garbage objective/variable values outside the gate
**What goes wrong:** `pulp.value(prob.objective)` returned 23.25 (fractional LP junk) on a 0.05 s stop and 1.0 on an Infeasible probe — live-verified. The legacy `int(round(val))` would report had₂=23.
**How to avoid:** extraction only in permitted statuses; integrality guard (values within 1e-6 of {0,1}); recompute objective from extracted binaries and require equality with the reported value; UNKNOWN/ERROR carry `value=None` enforced by `__post_init__`.

### Pitfall 3: C₄ double-count in obstruction enumeration
**What goes wrong:** each 4-cycle is found from both diagonals; without dedup `npp` doubles and the checksum/equal-count assert fails (or worse, duplicate constraints silently mask a *different* count bug).
**How to avoid:** collect pair–pair conflicts as `frozenset({e1,e2})` in a set (validated); assert set-equality (not just count-equality) with the naive loop at n=31 on seeds 1 and 137.

### Pitfall 4: H/G adjacency flip
**What goes wrong:** `adj` is H everywhere; G-edges are `v not in adj[u]`. One flipped membership test inverts the semantics while running fine.
**How to avoid:** the structural checksums catch class-level flips instantly (nss would count G-edges ≈ 334, not 177); the brute-force n≤8 differential catches the rest; re-assert `is_triangle_free`-style invariants (raise-based) at problem build.

### Pitfall 5: Connectivity is enforced by variable indexing, not constraints
**What goes wrong:** pair variables exist only for G-edges — that IS the size-2 connectivity constraint. Any refactor that widens the variable index set (e.g., "all vertex pairs") silently admits disconnected "branch sets".
**How to avoid:** document the mechanism in `problems/had2.py`'s docstring per the model-validity predicate; the trust-root verifier independently rejects non-G-edge pairs (already proven by the Phase-2 mutant suite).

### Pitfall 6: `assert`-based guards in the new solver path
**What goes wrong:** `python -O` strips asserts; the structural checksum and status gates are impossibility-adjacent and must survive `-O`.
**How to avoid:** raises only (`ChecksumError`, `NotProvedOptimal`, `ValueError`); extend the existing `-O` CI canary to at least one solver-path test.

### Pitfall 7: CI wall-time blowup
**What goes wrong:** seed-137 optimize is ~149 s single-thread (Rosetta; Linux similar order). Putting it in the every-commit job doubles CI time.
**How to avoid:** `@pytest.mark.slow` on the optimize regression; every-commit panel = decision-mode kills (~2.5 s) + tiny closed-form/brute-force instances.

### Pitfall 8: Recording PROVED_INFEASIBLE / had₂<χ-flavored outcomes as conclusions
**What goes wrong:** Phase 4 has ONE engine; any impossibility-flavored value is single-backend and must not be battery-conclusive (SHC-CANDIDATE machinery is Phase 5).
**How to avoid:** `ExactOutcome` records the fact honestly (status + backend + version); no code path in Phase 4 assigns instance-level statuses from `PROVED_INFEASIBLE`/`INCUMBENT_ONLY`. The timeout test proves the type-level guarantee.

## Code Examples

Verified patterns (all executed against the pinned environment during this research):

### CBC invocation + status mapping
```python
# Source: pulp 3.3.2 installed source (apis/coin_api.py) + live verification
import pulp

solver = pulp.PULP_CBC_CMD(msg=0, threads=1, timeLimit=params.time_limit_s,
                           logPath=str(log_tmp))     # logPath ALWAYS: evidence + bound
prob.solve(solver)

proved_optimal = (prob.status == pulp.LpStatusOptimal
                  and prob.sol_status == pulp.LpSolutionOptimal)
incumbent_only = (prob.status == pulp.LpStatusOptimal
                  and prob.sol_status == pulp.LpSolutionIntegerFeasible)
infeasible     = (prob.status == pulp.LpStatusInfeasible)
# prob.status == pulp.LpStatusNotSolved → UNKNOWN: touch NO values (fractional garbage)
```

### Bound parsing from the CBC log (stopped runs)
```python
# Source: live CBC 2.10.3 logs captured in this research
# "Result - Stopped on time limit" ... "Objective value: 17.00000000" ... "Upper bound: 20.879"
def parse_bound(log_text: str) -> float | None:
    for line in log_text.splitlines():
        if line.startswith("Upper bound:"):
            return float(line.split(":")[1])
    return None   # caller falls back to trivial bound n, provenance-tagged
```

### Structural checksum (independent recomputation, raise-based)
```python
# Source: formulas from PITFALLS.md Pitfall 1, validated live (seed-1: 131/998/726; seed-137: 177/1913/3782)
deg = [len(adj[v]) for v in range(n)]
nss_expect = sum(deg) // 2
nsp_expect = sum(d * (d - 1) // 2 for d in deg)
npp_expect = sum(
    (c := len(adj[u] & adj[v])) * (c - 1) // 2
    for u in range(n) for v in range(u + 1, n)) // 2
if (len(ss), len(sp), len(pp)) != (nss_expect, nsp_expect, npp_expect):
    raise ChecksumError(f"conflict-class counts {(len(ss), len(sp), len(pp))} "
                        f"!= H-structure {(nss_expect, nsp_expect, npp_expect)}")
```

### CBC binary version probe
```python
# Source: live run — banner "Welcome to the CBC MILP Solver / Version: 2.10.3 / Build Date: Dec 15 2019"
import subprocess, pulp
def cbc_binary_version() -> str:
    path = pulp.PULP_CBC_CMD(msg=0).path
    out = subprocess.run([path, "-exit"], capture_output=True, text=True, timeout=30)
    for line in out.stdout.splitlines():
        if line.strip().startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return "unknown"
```

## State of the Art

| Old Approach (Appendix C) | Current Approach (Phase 4) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `val = pulp.value(prob.objective); had2 = int(round(val))` — no status gate | Two-field gate + `ExactOutcome` with raising accessor | this phase | The incumbent-as-optimum soundness hole becomes unrepresentable |
| O(\|E_G\|²) pair–pair scan (infeasible to even build at n=301/501) | H-obstruction enumeration (set-equal at n=31, ~10× faster there, scales as Σ C(codeg,2)) | this phase | Unlocks exact had₂ beyond toy n; identical semantics proven |
| `fam[:chi]` truncation before storing | FULL family; schema derives had₂ = len (truncation refused since Phase 2) | Phase 2 (schema), consumed now | Falsification-Rule k-level blind spot closes at the interface |
| `msg=0` hides "Stopped on time limit" | `logPath` always; Result/bound lines archived + parsed | this phase | Timeout evidence + dual bound recorded per run |
| `backends.cbc = "bundled-with-pulp-3.3.2"` stub | actual binary version "2.10.3" stamped at solve time | this phase | ENV-05 per-record version stamps complete for exact records |

**Deprecated/outdated:** PuLP 4.0 alphas (remove bundled CBC / rework `PULP_CBC_CMD`) — permanently out of scope under the hard pin `[CITED: CLAUDE.md stack table]`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CBC 2.10.3 single-thread is run-to-run deterministic for a fixed binary + platform + model file (no seed option passed) | Pattern 3 | Regression test flakiness on *which* optimal family is returned (never on the value); mitigation already designed: tests assert value/status/verifiability, never model bytes |
| A2 | Linux-CI CBC solve time for seed-137 optimize is the same order as the 149 s observed under Rosetta | Pattern 6 / CI budget | If dramatically slower, the slow-marker budget needs raising; value unaffected |
| A3 | The `Upper bound:` log line is emitted by bundled CBC 2.10.3 on all stopped `-max` runs (observed on 2 of 2 stopped runs, both node-count 0) | Pattern 3 | Bound falls back to trivial `n` with provenance tag — degraded audit info, no soundness impact |

All other load-bearing claims are `[VERIFIED]` by execution or direct source inspection — no user confirmation needed for them.

## Open Questions (RESOLVED)

1. **Does the frozen corpus's seed-137 record get upgraded to the 17-set family in this phase?** — **RESOLVED:** regression-as-test, corpus byte-untouched (plan 04-04); the stored-family upgrade is DEFERRED to a future deliberate freeze amendment — first real consumer is the Phase-11 Falsification-Rule harness.
   - What we know: the Phase-2 summary promises "Phase 4 drops in seed-137's true 17-set family with no schema change"; but Phase 3 froze the repro drivers "forever", and R1 byte-asserts the 16-set D.3 literal. R2/R3/manifest are provably unaffected by a model-field change; R1 + `seed137.py` (+ `freeze.py` ordering) are the only artifacts a lockstep amendment must touch.
   - What's unclear: whether freeze discipline outweighs the corpus-completeness promise *now* (the first real consumer of k=17-level corpus storage is the Phase-11 Falsification-Rule harness).
   - Recommendation: Phase 4 ships the regression-as-test unconditionally (satisfies the roadmap success criterion verbatim); the corpus upgrade is either a clearly-fenced final plan (single commit: driver + refreeze + R1 literal, flagged as a deliberate freeze amendment) or an explicit deferral recorded in STATE.md. Planner should surface this at plan-check; treat as Claude's-discretion-with-visibility since no CONTEXT.md exists.

2. **Decision-mode "stop at first feasible":** — **RESOLVED:** no `maxSolutions` option needed — with a constant objective CBC already behaves as pure feasibility (2.3 s observed). No `maxSolutions`-style option is needed; do not add unverified CBC CLI options.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pulp | cbc.py | ✓ (in `.venv`) | 3.3.2 | — (hard pin) |
| bundled CBC binary | all solves | ✓ (executed live; Rosetta on this Mac) | 2.10.3 | — |
| networkx | witness/matching (existing) | ✓ | 3.6.1 | — |
| pytest | test suite | ✓ | 8.3.4 (pinned) | — |
| uv | env/reproduction | ✓ (`$HOME/.local/bin`, per Phase-3 notes) | 0.11.30 | — |
| Linux x86_64 CI | canonical exact-record platform | ✓ (ci.yml, ubuntu-latest) | — | local Rosetta runs stamped honestly via `cbc_under_rosetta` |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 (pinned), via uv |
| Config file | `pyproject.toml` (`markers = ["slow: release/nightly replay gate"]`) |
| Quick run command | `uv run --frozen --extra dev pytest tests/test_solver_result.py tests/test_had2_problem.py tests/test_cbc_backend.py tests/test_cbc_status_honesty.py -q` |
| Full suite command | `uv run --frozen --extra dev pytest -q` (includes slow: R3 + seed-137 optimize, ~3 min total) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXACT-01 | Status mapping: every (status, sol_status) pair → correct Status; PROVED_OPTIMAL requires both fields | unit (no solver) | `pytest tests/test_solver_result.py -x` | ❌ Wave 0 |
| EXACT-01 | `exact_value()` raises for INCUMBENT_ONLY/UNKNOWN/ERROR/MODEL_FOUND; `__post_init__` invariants | unit | `pytest tests/test_solver_result.py -x` | ❌ Wave 0 |
| EXACT-01 / SC1 | Live timeout on seed-137 optimize: status ∈ {INCUMBENT_ONLY, UNKNOWN}, `exact_value()` raises, no garbage value surfaced | integration (~5–20 s) | `pytest tests/test_cbc_status_honesty.py -x` | ❌ Wave 0 |
| EXACT-02 / SC3 | Obstruction enumeration set-equal to naive loop at n=31, seeds 1 & 137; checksums 131/998/726 and 177/1913/3782; checksum raises (not assert) on a mutated class | unit | `pytest tests/test_had2_problem.py -x` | ❌ Wave 0 |
| EXACT-02 | Brute-force had₂ (n ≤ 8 exhaustive) == CBC optimize on random triangle-free H + closed-form cases (C₅→3, empty→n) | integration (fast) | `pytest tests/test_cbc_backend.py -x` | ❌ Wave 0 |
| SC2 | seed-137: PROVED_OPTIMAL, value=bound=17, 17-set family through `verify_certificate` via in-memory record; ≥ stored-16-set metamorphic check | integration, `slow` (~2.5 min) | `pytest tests/test_seed137_regression.py -m slow -x` | ❌ Wave 0 |
| SC2 | CI panel: decision-mode kills at k=χ on seed-1/seed-137 (+ 1 Cayley optional), families verified | integration (~5 s) | `pytest tests/test_cbc_backend.py -x` | ❌ Wave 0 |
| SC4 | Decision + optimize both work; value/bound/backend_version present in every outcome (incl. bound parse fixture from captured logs) | unit + integration | `pytest tests/test_cbc_backend.py tests/test_solver_result.py -x` | ❌ Wave 0 |
| trust regression | Existing R1/R2/R3 + fingerprint + `-O` canary stay green; `-O` canary extended over one solver-path test | regression | `uv run --frozen --extra dev python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q` + full suite | ✅ existing (+ extension) |

### Sampling Rate
- **Per task commit:** quick run command above (new-module tests only; seconds).
- **Per wave merge:** `uv run --frozen --extra dev pytest -q -m "not slow"` + the `-O` canary.
- **Phase gate:** full suite including `-m slow` (seed-137 optimize + R3) green before `/gsd:verify-work`; CI `test` job untouched, `release-gate` job gains the seed-137 slow test automatically via the `-m slow` selector.

### Wave 0 Gaps
- [ ] `tests/test_solver_result.py` — EXACT-01 status contract (pure unit; write RED-first against `solvers/result.py`)
- [ ] `tests/test_had2_problem.py` — EXACT-02 enumeration/checksum (embeds the naive reference loop as test-local code)
- [ ] `tests/test_cbc_backend.py` — decision/optimize/brute-force/CI-panel
- [ ] `tests/test_cbc_status_honesty.py` — SC1 live timeout
- [ ] `tests/test_seed137_regression.py` — SC2, `@pytest.mark.slow`
- Framework install: none (pytest pinned and green at 54 tests).

## Sources

### Primary (HIGH confidence)
- **Live execution in the pinned `.venv` (2026-07-21)** — status/sol_status behavior across optimal/incumbent/stopped/infeasible; garbage-value demonstrations (23.25, 1.0); seed-137 had₂=17 PROVED_OPTIMAL in 149 s with 17-set family; decision mode 2.3–2.6 s; obstruction==naive set-equality on seeds 1 & 137; checksum values; CBC 2.10.3 banner; log grammar (`Result -`, `Objective value:`, `Upper bound:`, `Gap:`)
- **Installed pulp 3.3.2 source** — `pulp/apis/coin_api.py` (`get_status` mapping incl. the Stopped→Optimal override, `getOptions` threads emission, `solve_CBC` cmd construction, logPath plumbing); `pulp/constants.py` (LpStatus/LpSolution values)
- Repo artifacts: `src/alpha2/corpus/{verifier,schema,store}.py`, `src/alpha2/repro/seed137.py`, `tests/test_corpus_r1.py`, `.planning/reference/alpha2-program-source.md` (Appendix C.3/C.4 verbatim ILP; D.3 facts), Phase 2/3 SUMMARYs, ROADMAP Phase-4 section

### Secondary (MEDIUM confidence)
- `.planning/research/ARCHITECTURE.md` (Pattern 2 ExactBackend sketch — adopted with refinements), `.planning/research/PITFALLS.md` (Pitfalls 1–3 formulas — now upgraded to VERIFIED by the live runs), CLAUDE.md Blueprint 3
- PuLP/CBC issue lineage for the status treachery: coin-or/pulp#517, coin-or/Cbc#440 (cited in PITFALLS.md; behavior independently reproduced here)

### Tertiary (LOW confidence)
- None load-bearing. (CBC log-grammar stability across future CBC versions is irrelevant under the hard pin; flagged in A3 anyway.)

## Metadata

**Confidence breakdown:**
- Status contract / pulp semantics: HIGH — read from installed source AND reproduced live, including the treacherous case
- Obstruction encoding + checksums: HIGH — set-equality and formula match proven by execution on the actual project generator
- Seed-137 regression values: HIGH — had₂=17 PROVED_OPTIMAL reproduced in this environment; timings MEDIUM (platform-dependent)
- Corpus reconciliation: HIGH on the constraint analysis (artifacts read directly); the upgrade-vs-defer choice is a flagged decision, not a research uncertainty

**Research date:** 2026-07-21
**Valid until:** stable indefinitely under the pins (pulp==3.3.2 / CBC 2.10.3 / CPython 3.12.13); re-verify only if any pin moves
