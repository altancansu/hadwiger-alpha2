---
phase: 04-exactbackend-cbc-reference
reviewed: 2026-07-22T00:00:00Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - src/alpha2/solvers/result.py
  - src/alpha2/solvers/backend.py
  - src/alpha2/solvers/cbc.py
  - src/alpha2/solvers/problems/had2.py
  - tests/test_solver_result.py
  - tests/test_cbc_backend.py
  - tests/test_cbc_status_honesty.py
  - tests/test_solver_isolation.py
  - tests/test_had2_problem.py
  - tests/test_seed137_regression.py
  - .github/workflows/ci.yml
findings:
  critical: 0
  warning: 4
  info: 6
  total: 10
status: issues_found
---

# Phase 4: Code Review Report — ExactBackend & CBC Reference

**Reviewed:** 2026-07-22
**Depth:** deep (cross-file trace, reference-source diff vs Appendix C.3/C.4, live adversarial probes in the pinned .venv)
**Files Reviewed:** 11
**Status:** issues_found (no soundness leak found; 4 warnings, 6 info)

## Summary

This review adversarially hunted the one failure that matters: **any path by which a
time-limited/incumbent CBC result could be read as an exact had₂.** I traced every
extraction and status path in `cbc.py`/`result.py`, diffed the enumeration against the
Appendix C.3/C.4 reference loops, verified the checksum algebra independently, ran the
phase's fast test suite live (49 passed, 8.9 s), and executed hand-built adversarial
probes against `ExactOutcome`.

**Soundness verdict: no leak found in the shipped code.** Specifically verified:

- **Two-field gate is the sole PROVED_OPTIMAL path.** `map_status` returns
  `PROVED_OPTIMAL` only on `LpStatusOptimal AND LpSolutionOptimal` in optimize mode
  (cbc.py:59-60); the treacherous `(Optimal, IntegerFeasible)` timeout case maps to
  `INCUMBENT_ONLY`; `NotSolved` → `UNKNOWN`; everything unrecognized falls through to
  `ERROR` (fail-closed default, cbc.py:70). Infeasible/Unbounded in optimize mode →
  `ERROR`, never `PROVED_INFEASIBLE` — correct per the "empty family is always
  feasible" argument.
- **Objective/model extraction is status-gated.** Variable values are touched only for
  statuses in `_EXTRACTABLE` (cbc.py:230); `pulp.value(prob.objective)` is read only
  inside `_guarded_extract` after that gate; extraction carries the integrality guard
  (1e-6 to {0,1}), objective recompute, and internal-disjointness check; any guard trip
  downgrades the whole outcome to `ERROR` with `value=None, family=None` (cbc.py:232-233).
  The garbage classes reproduced in 04-RESEARCH (fractional 23.25 on NotSolved, stale 1.0
  on Infeasible) are unreachable.
- **`exact_value()` is truly non-returning on non-proven status** for every outcome the
  CBC adapter can construct: raises `NotProvedOptimal` for all five non-proven statuses
  (result.py:91-94). (A hand-construction gap exists — see WR-02.)
- **Obstruction enumeration cannot silently under-generate.** The structural checksum is
  enforced on **every** build — `solve_had2` always goes through `build_had2_problem`
  (cbc.py:180), which recomputes nss/nsp/npp independently from degrees/codegrees and
  raises `ChecksumError` on any mismatch (had2.py:90-100). I verified the checksum
  algebra: in triangle-free H, codeg(u,v) ≥ 2 forces uv to be a G-edge, so
  ½·ΣC(codeg,2) counts exactly the deduped diagonal pairs (each C₄ discovered once per
  diagonal, frozenset-deduped); H-edges have codeg 0 and contribute nothing. Dropping any
  single conflict of any class trips the gate (mutation-tested, and re-proved under `-O`
  by the canary). Set-equality (not count-equality) vs test-local copies of the C.4
  loops is asserted on seeds 1 and 137 — I diffed those test-local loops against
  Appendix C.3 lines 403-418 and C.4 lines 516-534 and they are faithful.
- **Raise-based, `-O`-proof.** Zero `ast.Assert` in all four solver modules
  (AST-enforced); the `-O` subprocess canary proves `NotProvedOptimal` and
  `ChecksumError` fire with asserts stripped, with a real `__debug__` branch proving
  `-O` is live. I additionally verified empirically that pytest's assertion rewriting
  keeps test asserts live under `python -O -m pytest` (a deliberately failing assert
  still fails), so the CI `-O` canary step is not vacuous.
- **Determinism.** `threads != 1` raises (cbc.py:173-177); `threads=1` passed explicitly;
  all conflict rows emitted in `sorted(...)` order, variables created in deterministic
  `Gedges`/`range(n)` order — the model file is byte-deterministic per instance; no
  recorded value depends on solver nondeterminism (tests assert value/status/bound/
  verifiability, never model bytes).
- **pulp confinement + version stamping.** AST guard confines `pulp` imports to
  `cbc.py` across all of `src/alpha2/` (with a non-vacuity leg); `backend_version`
  stamps `pulp==<ver> / CBC <probed banner>`; tests pin "pulp==3.3.2" and "2.10.3".
- **No security issues.** Fixed-argument subprocess (the probed CBC path from pulp,
  `-exit`), per-run `TemporaryDirectory` log files, read-only corpus loads in tests, no
  secrets, no injection surface.

What survives adversarial scrutiny does so because the design is fail-closed at every
branch. The warnings below are real defects, but none of them opens the
incumbent-as-exact hole: WR-01 is a CI verification gap, WR-02/WR-04 are contract gaps
reachable only by future backends/callers, WR-03 fails in the safe direction.

## Warnings

### WR-01: Phase-4 functional solver tests never run in CI — the "every-commit kill panel" exists only locally

**Status:** FIXED — commit e2e2c4b (`ci(04): run solver soundness tests on every commit`): the five solver test files added to the every-commit `test` job under `-m "not slow"`; release-gate/-O canary/3.13 canary/SHA pins unchanged.

**File:** `.github/workflows/ci.yml:37,43,61`
**Issue:** The every-commit `test` job runs a fixed file list
(`test_corpus_r1.py test_corpus_r2.py test_fingerprint.py`) plus the `-O` canary
(`test_verifier_dash_O.py test_corpus_r1.py test_solver_isolation.py`). The
release-gate job runs `pytest -q -m slow` (slow-marked tests only) plus the full-296
R2 panel. Consequently **none of the phase's functional solver tests execute in CI at
all**: `test_cbc_backend.py` (including the seed-1/seed-137 decision-kill panel that
commit ce06acd labels "every-commit 296-lineage decision-kill panel" and that
04-RESEARCH Pattern 6 designates the every-commit SC2 leg), `test_cbc_status_honesty.py`
(the SC1 live incumbent-never-reads-as-exact proof), `test_had2_problem.py`
(set-equality vs Appendix C.4 + checksum mutation + brute-force differential), and
`test_solver_result.py` (status contract). Only the import-boundary/AST/`-O` guards in
`test_solver_isolation.py` run. A future regression to `map_status`, the extraction
guards, or the enumeration would sail through CI green; only the nightly/tag release
gate would catch the two slow tests' subset. The entire fast solver suite costs ~9 s
locally — there is no budget reason for the omission.
**Fix:** Add the solver tests to the every-commit job, e.g. change ci.yml:37 to:
```yaml
run: uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py tests/test_solver_result.py tests/test_had2_problem.py tests/test_cbc_backend.py tests/test_cbc_status_honesty.py tests/test_solver_isolation.py -m "not slow" -q
```
(or simply `uv run --frozen pytest -q -m "not slow"` now that the whole fast suite is
seconds-scale).

### WR-02: `ExactOutcome` under-enforces its own invariants — PROVED_OPTIMAL with `value=None` constructs, and `exact_value()` silently returns `None`

**Status:** FIXED — commit aad5741 (`fix(04): enforce ExactOutcome status-honesty invariants`): valued statuses require a genuine int (bool/float/None raise); PROVED_INFEASIBLE joins UNKNOWN/ERROR on value=None; PROVED_OPTIMAL requires a non-None family; non-valued statuses require family=None; bound_source restricted to the four documented provenances. Raise-based; regression tests cover all three live-probed inconsistencies.

**File:** `src/alpha2/solvers/result.py:73-95`
**Issue:** `__post_init__` rejects a value only for UNKNOWN/ERROR and checks
`value == bound` only for PROVED_OPTIMAL. Live probes confirm three constructible
inconsistencies: (a) `ExactOutcome(status=PROVED_OPTIMAL, value=None, bound=None, ...)`
constructs and `exact_value()` **returns `None`** — a declared-`int` accessor silently
yielding a non-value on the one status callers trust; (b) `value=3.0` (float) with
`bound=3` constructs and `exact_value()` returns `3.0`; (c)
`status=PROVED_INFEASIBLE, value=99` constructs, carrying a garbage value on an
impossibility-flavored (radioactive) status. The CBC adapter cannot produce any of
these today (`value = len(fam)` is always an int, guard trips force ERROR), but
`result.py` is the shared, stdlib-only contract that Phase 5's CP-SAT backend will
construct against — the module docstring's claim that weaker outcomes are
"unrepresentable at the type level" is currently overstated exactly where the next
backend author will rely on it.
**Fix:** Tighten `__post_init__`:
```python
_VALUED = (Status.PROVED_OPTIMAL, Status.INCUMBENT_ONLY, Status.MODEL_FOUND)
if self.status in _VALUED:
    if not isinstance(self.value, int) or isinstance(self.value, bool):
        raise ValueError(f"status={self.status.name} requires an int value, got {self.value!r}")
elif self.value is not None:   # PROVED_INFEASIBLE joins UNKNOWN/ERROR here
    raise ValueError(f"status={self.status.name} must carry value=None")
if self.bound_source not in ("definition", "cbc_log", "trivial_n", "none"):
    raise ValueError(f"unknown bound_source {self.bound_source!r}")
```

### WR-03: Recompute-guard tolerance mis-scaled — accumulated per-variable drift can spuriously downgrade a genuine optimum to ERROR at larger n

**Status:** FIXED — commit 328c352 (`fix(04): scale-robust integrality recompute guard`): count compared via `round(reported) == len(fam)` (exact) plus a sub-integer drift budget of `#vars * _INTEGRALITY_TOL`. Fail-closed preserved (unit-level mismatch and excess sub-unit drift still ERROR); solve-free regression tests drive `_guarded_extract` with hand-set varValues.

**File:** `src/alpha2/solvers/cbc.py:140`
**Issue:** `_guarded_extract` accepts each binary within `1e-6` of {0,1}
(cbc.py:133), then requires `abs(len(fam) - reported) <= 1e-6` where `reported =
pulp.value(prob.objective)` is the *sum* over all binaries. With per-variable drift up
to 1e-6, the sum can legitimately differ from the count by up to `#vars * 1e-6` —
~3.7e-4 at n=31 (365 vars) and ~1.25e-1 at n=501 (~125k pair vars), both far above the
1e-6 gate. A solution passing the integrality guard can therefore fail the recompute
guard purely on accumulated float noise, mapping a genuinely PROVED_OPTIMAL solve to
ERROR. This is fail-closed (never unsound), but it is a robustness landmine sitting
directly on the Blueprint-3 scaled-search path (n = 301/501), where it would present as
a mystifying intermittent ERROR on correct solves.
**Fix:** The recompute guard is detecting a *count* mismatch between rounded extraction
and the reported objective; compare at count resolution:
```python
if reported is None or abs(len(fam) - reported) > 0.5:
    return None
```
(or `round(reported) != len(fam)` combined with a scaled tolerance
`len(mv) * _INTEGRALITY_TOL` if sub-unit drift itself should stay fatal).

### WR-04: `target_k` accepts `bool` — `solve_had2(..., mode="decision", target_k=True)` silently means k=1

**Status:** FIXED — committed with this review update (`fix(04): reject bool target_k in CBC decision mode`): explicit `isinstance(target_k, bool)` rejection alongside the int/positivity check; regression test asserts True/False/0/-1/None/3.0/"3" all raise.

**File:** `src/alpha2/solvers/cbc.py:166`
**Issue:** `isinstance(target_k, int)` is `True` for `bool` (`isinstance(True, int)`
confirmed live), and `True >= 1` passes the positivity check, so a caller bug that
passes a boolean (e.g. the result of a comparison) runs a k=1 decision solve and
returns an honest-looking MODEL_FOUND — a wrong-question-right-answer failure the
status discipline cannot catch.
**Fix:**
```python
if not isinstance(target_k, int) or isinstance(target_k, bool) or target_k < 1:
    raise ValueError(...)
```

## Info

### IN-01: Dead guard in the pair–pair loop

**File:** `src/alpha2/solvers/problems/had2.py:71`
**Issue:** `if len({a, b, c, d}) == 4` is provably always true for well-formed H:
`c, d ∈ N_H(a) ∩ N_H(b)` forces `c, d ∉ {a, b}` (no self-loops), and `i < j` forces
`c != d`. Harmless (it mirrors C.4's guard and defends malformed adjacency), but it is
an always-true branch.
**Fix:** Keep it, but add a comment stating it is defensive-only/always-true for valid
input, so a future reader doesn't infer a real degenerate case exists.

### IN-02: `build_had2_problem` accepts malformed adjacency; checksum gate cannot catch it

**File:** `src/alpha2/solvers/problems/had2.py:76-101`
**Issue:** No validation of symmetry, irreflexivity, or vertex range. Because the
checksum expectations are recomputed from the *same* `adj`, a malformed adjacency
(asymmetric entries, self-loops) passes the gate self-consistently and produces a model
about a graph nobody intended; out-of-range vertices fail loudly later (KeyError on
`mv[(a, b)]` in cbc.py). All current callers use the frozen generators, and the trust
root independently verifies families against `H_edges` derived from the same `adj`, so
end-to-end results stay internally consistent — but a cheap raise-based well-formedness
check (`v != u`, `0 <= v < n`, `u in adj[v]`) would close the gap at the module that
owns the model.
**Fix:** Add an O(Σdeg) symmetry/irreflexivity/range raise before `is_triangle_free`.

### IN-03: `register_backend` silently overwrites an existing registration

**File:** `src/alpha2/solvers/backend.py:44-48`
**Issue:** A second `register_backend("cbc", other_factory)` silently shadows the
reference backend — every subsequent `get_backend("cbc")` returns the impostor with no
signal. Given the registry is the battery's route to the reference engine, collisions
should be loud.
**Fix:** `if name in _REGISTRY and _REGISTRY[name] is not factory: raise ValueError(f"backend {name!r} already registered")`.

### IN-04: `cbc_binary_version` caches a transient probe failure as "unknown" for the process lifetime

**File:** `src/alpha2/solvers/cbc.py:100-116`
**Issue:** A one-off subprocess hiccup pins `backend_version` to `"... / CBC unknown"`
in every outcome for the rest of the process. The stamp stays *honest* (never wrong,
just uninformative), and `_assert_stamp`/the seed-137 regression pin "2.10.3" so CI
would fail loudly — but not retrying is gratuitous.
**Fix:** Cache only successful probes (`if ver != "unknown": _CBC_VERSION_CACHE = ver`).

### IN-05: No `bound >= value` consistency check on INCUMBENT_ONLY outcomes

**File:** `src/alpha2/solvers/cbc.py:243-246`
**Issue:** For a maximize problem the dual bound must be ≥ the incumbent. A corrupted
or mis-parsed `Upper bound:` line below the incumbent would be recorded silently as
evidence (`bound_source="cbc_log"`). Status labels remain honest either way, but an
inconsistent-evidence detector is one line.
**Fix:** After parsing, `if parsed < value: bound, bound_source = n, "trivial_n"` (or
map to ERROR — inconsistent solver evidence is a defect worth surfacing).

### IN-06: 1374 PULP_CBC_CMD DeprecationWarnings per fast-suite run

**File:** `src/alpha2/solvers/cbc.py:209` (emission site: pulp 3.3.2 `coin_api.py:70`)
**Issue:** Every `PULP_CBC_CMD(...)` construction under the (deliberate, load-bearing)
3.3.2 pin emits "PULP_CBC_CMD is deprecated and will be removed in PuLP 4.0". The
warning is expected and must never drive an upgrade (the pin is the point), so the
flood is pure noise burying real warnings.
**Fix:** Add a targeted `filterwarnings` entry in `pyproject.toml`
(`"ignore:PULP_CBC_CMD is deprecated:DeprecationWarning"`), with a comment citing the
hard pin.

---

_Reviewed: 2026-07-22_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
