# Phase 5: CP-SAT, Differential Gate & had₃ - Pattern Map

**Mapped:** 2026-07-22
**Files analyzed:** 5 source files (4 new, 1 extended) + 8 test files
**Analogs found:** 5 / 5 source (4 exact/role, 1 self-extension); 8 / 8 tests have strong analogs

All analogs are frozen Phase-4 code in this same repo. Phase 5 is composition + discipline: every source file copies a proven analog almost verbatim, changing only the solver library / size gate. The only genuinely new combinatorics is size-3 triple enumeration (`had3.py`) — which is exactly where the research flags bugs live, so it gets the same checksum + verifier + differential guards `had2.py` already has.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/alpha2/solvers/cpsat.py` (NEW) | backend adapter (service) | request-response (solve→outcome) | `src/alpha2/solvers/cbc.py` | exact (role + flow) |
| `src/alpha2/solvers/problems/had3.py` (NEW) | model / problem-data | transform (H → var+conflict sets) | `src/alpha2/solvers/problems/had2.py` | exact (role + flow) |
| `src/alpha2/solvers/differential.py` (NEW) | service / gate (stdlib-only) | transform (2 outcomes → verdict) | `src/alpha2/solvers/result.py` (stdlib-only trust discipline) + `backend.py` | role-match (no exact analog for the gate itself) |
| `src/alpha2/solvers/symmetry.py` (NEW, or a flag in `cpsat.py`) | utility / wrapper | request-response (wrap a solve) | `src/alpha2/solvers/cbc.py` `solve_had2` mode-dispatch (lines 179-205) | partial (role-match) |
| `src/alpha2/corpus/verifier.py` (EXTEND `verify_model_record`) | verifier (trust root) | validation | `src/alpha2/corpus/verifier.py` itself (lines 71-122) | self-extension |

Test files (all NEW except the -O canary extension) map to existing test analogs — see **Test Patterns** below.

## Pattern Assignments

### `src/alpha2/solvers/cpsat.py` (backend adapter, request-response) — EXACT-03

**Analog:** `src/alpha2/solvers/cbc.py` (the frozen reference adapter — copy its *structure* wholesale, swap pulp→cp_model).

This is a near-line-for-line mirror. Copy the module docstring discipline (cbc.py lines 1-26), the `_EXTRACTABLE` frozenset gate, `map_status`, `_guarded_extract`, the `<Backend>` class with `name`/`backend_version`/`solve_had2`, and the `register_backend` call. Change only: the library, the status vocabulary, and the model-build calls.

**Imports pattern** — mirror `cbc.py` lines 27-38, swapping the solver import. ortools must be the ONLY library this module imports (the confinement rule, backend.py lines 1-11):
```python
import importlib.metadata
import time

from ortools.sat.python import cp_model

from alpha2.solvers.backend import register_backend
from alpha2.solvers.problems.had2 import build_had2_problem
from alpha2.solvers.result import ExactOutcome, SolveParams, Status
```

**Registration** (copy `cbc.py` line 293 — the module-bottom lazy-registry hook that `get_backend("cpsat")` triggers via `importlib.import_module("alpha2.solvers.cpsat")`, backend.py lines 51-67):
```python
register_backend("cpsat", CPSATBackend)
```

**`solve_had2` signature + argument guards** — copy `cbc.py` lines 179-205 verbatim (mode validation, the explicit `bool` rejection of `target_k`, the `target_k is only meaningful in decision mode` guard). The one CBC-specific check to REPLACE is the `p.threads != 1` guard (cbc.py lines 201-205) — for CP-SAT the determinism contract is `num_workers=1` + pinned `random_seed`, not `threads`:
```python
if mode not in ("optimize", "decision"):
    raise ValueError(f"mode must be 'optimize' or 'decision', got {mode!r}")
if mode == "decision":
    if not isinstance(target_k, int) or isinstance(target_k, bool) or target_k < 1:
        raise ValueError("decision mode requires a positive int target_k ...")
elif target_k is not None:
    raise ValueError("target_k is only meaningful in decision mode")
```

**Model translation** — reuse the SAME `build_had2_problem(adj, n)` (cbc.py line 208); translate its `Gedges/ss/sp/pp` into CP-SAT Bools. The shared `Had2Problem` object is what makes CBC-vs-CP-SAT agreement meaningful (independent encodings, one instance). Model shape from RESEARCH Code Examples (verified live):
```python
problem = build_had2_problem(adj, n)          # checksum-gated on EVERY build
m = cp_model.CpModel()
mv = {e: m.new_bool_var(f"m_{e[0]}_{e[1]}") for e in problem.Gedges}
sv = {v: m.new_bool_var(f"s_{v}") for v in range(n)}
for v in range(n):                            # per-vertex disjointness
    m.add_at_most_one([mv[e] for e in problem.Gedges if v in e] + [sv[v]])
for (u, v) in sorted(problem.ss):             # single-single (H-edges)
    m.add_at_most_one([sv[u], sv[v]])
for (v, (a, b)) in sorted(problem.sp):        # single-pair (cherries)
    m.add_at_most_one([sv[v], mv[(a, b)]])
for e1, e2 in sorted(tuple(sorted(pair)) for pair in problem.pp):
    m.add_at_most_one([mv[e1], mv[e2]])       # pair-pair (C4 diagonals)
size = sum(mv.values()) + sum(sv.values())
if mode == "optimize":
    m.maximize(size)
else:
    m.add(size >= target_k)                   # constant objective; pure feasibility
```
Note the sorted() iteration on conflict sets (cbc.py lines 226-231) — copy it for determinism.

**Status mapping** — the CP-SAT analog of `cbc.py`'s `map_status` (lines 48-70). Two-condition PROVED_OPTIMAL gate (RESEARCH Pattern 1 table, mirroring cbc.py's two-field `LpStatusOptimal AND LpSolutionOptimal`):
```python
def map_status(status, solver, mode):
    if status == cp_model.OPTIMAL:
        if round(solver.objective_value) != round(solver.best_objective_bound):
            return Status.ERROR              # obj != bound: should never happen
        return Status.MODEL_FOUND if mode == "decision" else Status.PROVED_OPTIMAL
    if status == cp_model.FEASIBLE:
        return Status.MODEL_FOUND if mode == "decision" else Status.INCUMBENT_ONLY
    if status == cp_model.INFEASIBLE:
        return Status.PROVED_INFEASIBLE if mode == "decision" else Status.ERROR
    if status == cp_model.UNKNOWN:
        return Status.UNKNOWN
    return Status.ERROR                       # MODEL_INVALID or unrecognized
```
CRITICAL, from cbc.py's map_status contract (lines 60-70) and RESEARCH: `INFEASIBLE` in **optimize** mode → `Status.ERROR` (empty family is always feasible → encoding bug), NEVER `PROVED_INFEASIBLE`.

**Determinism knobs** (RESEARCH Pattern 1, all live-verified) — the CP-SAT analog of cbc.py's single-thread `PULP_CBC_CMD(threads=1, logPath=…)` (lines 237-242):
```python
solver = cp_model.CpSolver()
solver.parameters.num_workers = 1            # deterministic recorded/impossibility mode
solver.parameters.random_seed = <pinned>     # pinned seed
if p.time_limit_s is not None:
    solver.parameters.max_time_in_seconds = p.time_limit_s
if mode == "decision":
    solver.parameters.stop_after_first_solution = True
solver.parameters.log_search_progress = True # archive log (CBC logPath analog)
# DO NOT set search_branching with a bare int — it is an enum, raises TypeError.
status = solver.solve(m)
```

**Guarded extraction** — mirror `cbc.py`'s `_guarded_extract` (lines 119-168): extract ONLY inside the status gate, recompute `round(objective_value) == len(fam)`, and check internal disjointness. CP-SAT booleans are exact (no fractional LP junk) so the integrality-tolerance loop can be dropped, but KEEP the count==objective recompute and the disjointness `used`-set guard (cbc.py lines 162-168) as the fail-closed check:
```python
fam = [tuple(e) for e in problem.Gedges if solver.boolean_value(mv[e])] \
    + [(v,) for v in range(n) if solver.boolean_value(sv[v])]
if mode == "optimize" and round(solver.objective_value) != len(fam):
    return None                              # recompute guard: fail closed
```

**Version stamp** — the ortools analog of cbc.py's `backend_version` (lines 176-177):
```python
def backend_version(self):
    return f"ortools=={importlib.metadata.version('ortools')}"
```
`schema.make_backends` already routes `"cp-sat"/"cp_sat"/"cpsat"` in the method string to the ortools stamp (schema.py lines 208-209, 217) — no schema change needed for the version stamp.

**Outcome assembly** — copy `cbc.py`'s final `return ExactOutcome(...)` (lines 278-290) exactly, with `backend=self.name` (`"cpsat"`) and the ortools `backend_version`. `ExactOutcome.__post_init__` (result.py lines 86-120) enforces the value/bound/family invariants for free.

---

### `src/alpha2/solvers/problems/had3.py` (model, transform) — EXACT-05

**Analog:** `src/alpha2/solvers/problems/had2.py` (copy the whole pattern: frozen dataclass + `enumerate_*` + `build_*` with an independent structural checksum).

**Dataclass + docstring discipline** — mirror `had2.py` lines 29-53. Backend-neutral, stdlib-only (never import a solver). Triangle-free re-check up front (had2.py lines 83-87):
```python
@dataclass(frozen=True)
class Had3Problem:
    n: int
    triples: list          # triple index: {a,b,c} with <=1 internal H-edge (>=2 G-edges)
    # ... plus size-3 conflict sets, checksum-gated
```

**Triple index = the size-3 connectivity constraint by indexing** — the direct analog of had2.py's "pair vars exist ONLY for G-edges" comment (had2.py lines 5-12, and the `Gedges` comprehension line 57). A triple is legal iff it induces a connected subgraph of G ⟺ **≥2 of its 3 internal pairs are G-edges** ⟺ **≤1 pair is an H-edge** (RESEARCH Pattern 3):
```python
triples = [
    (a, b, c)
    for a in range(n) for b in range(a + 1, n) for c in range(b + 1, n)
    if ((b in adj[a]) + (c in adj[a]) + (c in adj[b])) <= 1   # <=1 internal H-edge
]
```

**Conflict pruning by common H-neighborhood** — mirror had2.py's C4-diagonal enumeration from `W = adj[a] & adj[b]` (had2.py lines 66-72). A triple T conflicts with a set S iff every vertex of S lies in `⋂_{x∈T} N_H(x)`; enumerate from that intersection, not all pairs (RESEARCH Pattern 3).

**Independent structural checksum** — copy had2.py's `build_had2_problem` checksum gate exactly (lines 88-101): recompute the conflict-class counts independently from H's structure and `raise ChecksumError` on mismatch. Reuse the existing `ChecksumError` (had2.py line 34) or define a size-3 analog:
```python
if (len(triples), len(conflicts)) != (ntriples_expect, nconf_expect):
    raise ChecksumError(f"size-3 counts {(...)} != H-structure {(...)}")
return Had3Problem(...)
```
RESEARCH Pitfall 3 warning: unlike had₂, size-3 conflicts are NOT a clean local substructure of H — the checksum + verifier + differential are the three independent guards (copy all three).

---

### `src/alpha2/solvers/differential.py` (gate service, transform) — EXACT-04

**Analog:** `src/alpha2/solvers/result.py` (stdlib-only trust-boundary discipline) + `backend.py` (stdlib-only, raises-only). No exact analog exists for the gate itself → this is the one genuinely-new module; it borrows the *discipline*, not the shape.

**Stdlib-only + raises-only header** — copy result.py's trust-boundary docstring stance (result.py lines 1-28) and its custom-exception pattern (result.py lines 45-46, `NotProvedOptimal`). NO solver import (RESEARCH Pattern 2 — it consumes two `ExactOutcome`s, never a solver):
```python
from alpha2.solvers.result import Status

class CriticalDisagreement(Exception):
    """Two backends returned unequal PROVED_OPTIMAL values — halts the batch."""
```

**The verdict function** — RESEARCH Code Examples "Differential gate (shape)", using the frozen `Status` enum and `ExactOutcome.exact_value()` (result.py lines 122-132) rather than raw `.value`:
```python
def differential_verdict(a, b, chi):          # a: CBC outcome, b: CP-SAT outcome (optimize)
    both_proved = (a.status is Status.PROVED_OPTIMAL
                   and b.status is Status.PROVED_OPTIMAL)
    if both_proved and a.exact_value() != b.exact_value():
        raise CriticalDisagreement(f"cbc={a.value} cpsat={b.value}")  # quarantine + halt
    if not both_proved:
        return "INSUFFICIENT"                 # timeout/incumbent → no impossibility claim
    return "SHC_CANDIDATE" if a.exact_value() < chi else "AGREED_KILL"
```
Key discipline (RESEARCH Pattern 2 / Pitfall 5): unequal PROVED_OPTIMAL is a CRITICAL that **halts the batch** — never "best of two", never skip. Exactly-one-proved is `INSUFFICIENT`, not a disagreement.

**Metamorphic cross-check (verifier trumps solver)** — generalize the seed-137 regression check (`test_seed137_regression.py` lines 124-129: `out.exact_value() == 17 > stored_size == 16`). Any `PROVED_OPTIMAL` value below a verified size-k family is CRITICAL → quarantine, no corpus write.

---

### `src/alpha2/solvers/symmetry.py` (wrapper utility, request-response) — EXACT-06

**Analog:** `cbc.py` `solve_had2` mode-dispatch + guard structure (lines 179-205); the assume-and-verify rule has no code analog (new discipline).

Wrap a solve with SB enabled; if the SB-on result is `< χ` (impossibility-flavored), the wrapper MUST rerun WITHOUT SB before the outcome may reach `differential.py` (RESEARCH Pattern 5). Encode as a raise-guarded code path (never `assert` — cbc.py raises-only discipline, result.py lines 22-24):
```python
class SBContaminationError(Exception):
    """An SB-on run produced a < chi outcome and was not re-verified without SB."""
```
Sound SB source for the MVP: CP-SAT's internal `symmetry_level` (objective-preserving, no new dep). The C₅ "vertex 0 unused" regression deliberately applies an *invalid* hand constraint to prove the discipline catches it — no pynauty needed. Consider a `symmetry_level`/SB flag on `cpsat.py.solve_had2` instead of a separate module (RESEARCH structure note, line 155).

---

### `src/alpha2/corpus/verifier.py` — EXTEND `verify_model_record` (trust root) — EXACT-05

**Analog:** the function itself (verifier.py lines 71-122) — a minimal, adversarial widening. This is the delicate change; keep every existing size-≤2 path byte-identical.

**Size gate** — widen line 104 from `(1, 2)` to `(1, 2, 3)`:
```python
if len(S) not in (1, 2, 3):
    raise VerificationError(f"branch set size {len(S)} not in (1,2,3): {S!r}")
```

**Size-2 connectivity (UNCHANGED)** — keep lines 112-115 exactly (`b in adj[a]` → H-edge rejection).

**Size-3 connectivity (NEW)** — the explicit ≥2-G-edges check (RESEARCH Pattern 4 / Assumption A3: 3 vertices connected ⟺ ≥2 edges). Insert alongside the size-2 branch:
```python
if len(S) == 3:
    a, b, c = S
    g_edges = (b not in adj[a]) + (c not in adj[a]) + (c not in adj[b])
    if g_edges < 2:
        raise VerificationError(f"triple {S!r} disconnected in G ({g_edges} G-edges < 2)")
```

**Cross-adjacency (UNCHANGED)** — `_is_conflict` (verifier.py lines 34-46) is already size-agnostic (loops all cross pairs) and needs NO change; the `for i<j` loop (lines 117-120) already rejects a triple non-adjacent in G to another set.

**Discipline (RESEARCH Pattern 4 / Pitfall 6):** stays stdlib-only, raises-only (`-O`-correct). MUST (1) keep all size-≤2 records verifying byte-unchanged (re-run R1/full corpus + `test_verifier_mutants.py`); (2) pass new size-3 mutants; (3) extend the `-O` canary. The `had_3` record field naming is an OPEN QUESTION (RESEARCH Open Q1 / A6) — flag for planner before writing to `schema.build_record` (schema.py line 275 derives `had_2 = len(model_branch_sets)`).

## Shared Patterns

### Two-field / two-condition PROVED_OPTIMAL gate
**Source:** `src/alpha2/solvers/cbc.py` `map_status` lines 59-60 (`LpStatusOptimal AND LpSolutionOptimal`).
**Apply to:** `cpsat.py` (`status == OPTIMAL AND round(objective_value) == round(best_objective_bound)`), `differential.py` (only two PROVED_OPTIMAL license a value-fact).

### Extraction only inside the status gate + recompute guard
**Source:** `src/alpha2/solvers/cbc.py` `_EXTRACTABLE` (lines 43-45) + `_guarded_extract` recompute (lines 143-158, 162-168).
**Apply to:** `cpsat.py` extraction. `objective_value` is read ONLY after PROVED_OPTIMAL; `round(objective_value) == len(fam)`; disjointness `used`-set.

### Independent structural checksum on every model build
**Source:** `src/alpha2/solvers/problems/had2.py` `build_had2_problem` lines 88-101 (`ChecksumError`).
**Apply to:** `had3.py` (size-3 counts recomputed independently from H's structure).

### Raises-only, `-O`-correct guards (never `assert`)
**Source:** `src/alpha2/corpus/verifier.py` (docstring lines 15-17, `if not cond: raise` throughout) + `result.py` lines 22-24.
**Apply to:** `cpsat.py`, `differential.py`, `symmetry.py`, `had3.py`, verifier extension. Extend the `-O` canary (`test_verifier_dash_O.py`) over ≥1 CP-SAT-path and ≥1 differential test.

### Family is an UNTRUSTED proposal → route through the trust root
**Source:** `src/alpha2/solvers/result.py` lines 26-28; `corpus/verifier.verify_certificate` (verifier.py lines 213-231).
**Apply to:** every extracted CP-SAT/had₃ family — verify via `verify_certificate`, never trust a solver flag.

### Lazy backend registration + confinement (one library per module)
**Source:** `src/alpha2/solvers/backend.py` lines 44-67; `cbc.py` line 293 (`register_backend("cbc", ...)`).
**Apply to:** `cpsat.py` — `register_backend("cpsat", CPSATBackend)` at module bottom; ortools imported nowhere else.

## Test Patterns

| New test (Wave 0) | Req | Copy structure from | Key excerpt to reuse |
|-------------------|-----|---------------------|----------------------|
| `test_cpsat_backend.py` | EXACT-03 | `tests/test_cbc_backend.py` | `_c5_adj`/`_empty_adj`/`_h_edges` literals (lines 49-61); C5 optimize→3 through `verify_certificate` (lines 119-144); decision both-legs (lines 180-198); bool-`target_k` rejection (lines 207-215). Swap `_assert_stamp` to check `"ortools==9.15.6755"`. |
| `test_cpsat_status_honesty.py` | EXACT-03 | `tests/test_cbc_status_honesty.py` | timed-out solve → status in {INCUMBENT_ONLY, UNKNOWN}; `exact_value()` raises `NotProvedOptimal`; obj==bound gate. FEASIBLE≠OPTIMAL is the CP-SAT twin of the incumbent hole. |
| `test_differential.py` | EXACT-04 | `test_cbc_backend.py` (E2E shape) + new `CriticalDisagreement` assertions | build two `ExactOutcome`s, assert `differential_verdict` → SHC_CANDIDATE / AGREED_KILL / INSUFFICIENT; unequal PROVED_OPTIMAL raises `CriticalDisagreement`. |
| `test_differential_panel.py` (`@pytest.mark.slow`) | EXACT-04/SC1 | `tests/test_seed137_regression.py` | `@pytest.mark.slow` (line 61); regen seed-137 (m==177); both backends `PROVED_OPTIMAL == 17`; both families `verify_certificate`. |
| `test_had3_problem.py` | EXACT-05 | `tests/test_had2_problem.py` | triple enumeration + checksum on synthetic size-3-forced instances. |
| `test_had3_backends.py` | EXACT-05 | `test_cbc_backend.py` | had₃ on both backends; verifier size-3 accept/reject through trust root. |
| `test_verifier_size3_mutants.py` | EXACT-05 | `tests/test_verifier_mutants.py` | `good_record()`/mutant pattern (lines 42-56, 81-157). New size-3 mutants: disconnected triple (0/1 G-edges), missing cross-adj, size-4 (still rejected), aliased vertex — each `pytest.raises(VerificationError)`. |
| `test_symmetry_assume_verify.py` | EXACT-06 | `test_cbc_backend.py` C5 literal | C₅ "vertex 0 unused" SB → had₂=2; assume-and-verify rerun → had₂=3; on/off differential `had₂(SB)==had₂(no-SB)`. |
| `test_verifier_dash_O.py` (EXTEND) | regression | `tests/test_verifier_dash_O.py` (existing) | subprocess `-O` canary (lines 25-55); extend over a CP-SAT-path + a differential test. |

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/alpha2/solvers/differential.py` | gate service | transform | No existing dual-backend comparator. Borrows stdlib-only + raises-only discipline from `result.py`/`backend.py`; the metamorphic check generalizes `test_seed137_regression.py` lines 124-129. The gate SHAPE is new (RESEARCH Pattern 2). |
| `src/alpha2/solvers/symmetry.py` | wrapper utility | request-response | No existing symmetry-breaking code. Assume-and-verify rerun-without-SB is a new discipline (RESEARCH Pattern 5); wrapper/guard structure borrows from `cbc.py.solve_had2`. |

## Metadata

**Analog search scope:** `src/alpha2/solvers/{cbc,result,backend}.py`, `src/alpha2/solvers/problems/had2.py`, `src/alpha2/corpus/{verifier,schema}.py`, `tests/{test_cbc_backend,test_cbc_status_honesty,test_verifier_mutants,test_verifier_dash_O,test_seed137_regression}.py`.
**Files scanned:** ~11 read in full/targeted; 29 source files enumerated.
**Pattern extraction date:** 2026-07-22
