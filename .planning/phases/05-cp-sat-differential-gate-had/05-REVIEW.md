---
phase: 05-cp-sat-differential-gate-had
reviewed: 2026-07-22T10:15:37Z
depth: deep
files_reviewed: 7
files_reviewed_list:
  - src/alpha2/corpus/verifier.py
  - src/alpha2/solvers/cpsat.py
  - src/alpha2/solvers/differential.py
  - src/alpha2/solvers/problems/had3.py
  - src/alpha2/solvers/symmetry.py
  - src/alpha2/solvers/cbc.py
  - src/alpha2/solvers/problems/had2.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-07-22T10:15:37Z
**Depth:** deep (cross-file soundness trace)
**Files Reviewed:** 7 source modules + 10 test files (fast tier executed)
**Status:** issues_found (0 blockers, 3 warnings, 2 info)

## Summary

I reviewed the Phase 5 diff (`6bbdab7..HEAD`) with the epistemic-discipline lens
from `CLAUDE.md` as the primary axis: false `PROVED_OPTIMAL`, impossibility-branch
contamination, trust-root weakening, recorded-mode nondeterminism, and
solver-library leakage. The fast test suite (82 tests, `not slow`) passes; the
`@pytest.mark.slow` seed-137 test was not run per instructions.

**The headline result is positive on every soundness-critical axis I could
prove.** In particular:

- **Trust-root widening (verifier.py {1,2}→{1,2,3}) is SOUND and COMPLETE.** For a
  3-vertex branch set, "connected in G" is exactly "≥2 internal G-edges", and the
  added check `g_edges = (b∉adj[a]) + (c∉adj[a]) + (c∉adj[b]); if g_edges < 2: raise`
  counts precisely the three unordered internal pairs, order-independently. Intra-set
  vertex aliasing is caught by the pre-existing `used`-set loop (which runs before the
  size-3 block), range/type checks are unchanged, and the pairwise-adjacency
  `_is_conflict` check is size-agnostic and still applied across all C(k,2) pairs. The
  size-≤2 legs are byte-unchanged. No trust-root weakening.
- **had3.py combinatorics are sound and the checksum is a genuine independent
  recomputation.** Triangle-freeness makes every enumerated conflict genuine (no
  *spurious* conflict — the dangerous direction for a false impossibility), the triple
  index `≤1 internal H-edge` is exactly the connected-in-G set, and I verified the
  bijections behind `n_triples = C(n,3) − ΣC(deg,2)`, `n_triple_single = ΣC(deg,3)`,
  and `n_triple_pair = Σ_{u<w} C(codeg,3)` hold on triangle-free H.
- **Status honesty holds.** `PROVED_OPTIMAL` requires `OPTIMAL AND round(obj)==round(bound)`;
  optimize-mode `INFEASIBLE`→`ERROR` (never `PROVED_INFEASIBLE`); extraction is gated,
  disjointness- and recompute-guarded, and every guard raises or maps to `ERROR` (correct
  under `python -O`, canary-tested).
- **Determinism** in recorded/impossibility mode is `num_workers=1` + pinned
  `random_seed=137`; `interleave_search` is deliberately avoided.
- **Library confinement holds:** `cpsat.py` is the only `ortools` importer, `cbc.py` the
  only `pulp` importer, and `differential.py`/`symmetry.py`/`verifier.py` import no solver
  library (test-enforced).

The findings below are quality/robustness concerns and one soundness-adjacent
*labeling* issue. None is a blocker: the invariant that no false certificate and no
false impossibility can pass the frozen trust root is preserved.

## Warnings

### WR-01: `solve_had3` returns `PROVED_OPTIMAL` for a Tier-1 *relaxation* — the value is an upper bound on had₃, not the exact size-3 Hadwiger number

**File:** `src/alpha2/solvers/problems/had3.py:86-95`, `src/alpha2/solvers/cpsat.py:320-325`, `src/alpha2/solvers/cbc.py:410-415`
**Issue:** The size-3 model enumerates only **triple-single** and **triple-pair**
conflicts (from `W(T)`). It omits **triple-triple** conflicts entirely. Two connected
triples `T1={a,b,c}`, `T2={d,e,f}` are non-adjacent in G exactly when H contains the
bipartite `K_{3,3}` between them — which is triangle-free and therefore *possible* in a
valid instance (e.g. `H ⊇ K_{3,3}`). The model has no constraint forbidding both from
being selected, so the feasible region is a **superset** of the true size-3 model:
`solve_had3(mode="optimize")` returns `Status.PROVED_OPTIMAL` on a relaxation whose
optimum can *exceed* the true had₃.

This is **sound in the impossibility direction** — a relaxation optimum `< chi` implies
the true had₃ `< chi`, so an SHC-flavored conclusion is not fabricated — and Blueprint 4
explicitly scopes Phase 5 to "Tier 1 (seagull triples only)". But the value is labeled
`PROVED_OPTIMAL` and `differential_verdict` treats an equal-value pair as "a FACT for
this instance" (differential.py:69). The **existence/AGREED_KILL** branch is where this
bites: `_guarded_extract3` checks only disjointness and `round(obj)==count`, **not**
pairwise adjacency, so on a `K_{3,3}`-bearing instance the "optimal" family can contain
two mutually non-adjacent triples. If a caller records an `AGREED_KILL` (value ≥ chi)
without running that family through `verify_certificate`, a **false kill** results. The
CBC-vs-CP-SAT differential cannot catch this because both backends translate the *same*
`Had3Problem` (the shared-model gap the had3_backends test comment slightly overstates as
catchable).

**Fix:** No soundness patch is required for Tier 1, but (a) state explicitly in the
`solve_had3` docstrings and in `Had3Problem` that the optimum is an **upper bound** on
had₃ (triple-triple conflicts omitted), and (b) make the AGREED_KILL contract enforce
trust-root verification of the winning family before any kill is recorded — the family is
untrusted and may be pairwise-non-adjacent. When Tier 2 lands, add the triple-triple
conflict class and extend the checksum with its `Σ C(codeg₃,·)` count.

### WR-02: `differential_verdict` does not guard that the two outcomes are the SAME problem/mode

**File:** `src/alpha2/solvers/differential.py:45-70`
**Issue:** The function reads only `.status` and `.exact_value()`; it never asserts
`a.problem == b.problem`, nor `a.mode == b.mode == "optimize"`. A caller error that pairs
a had₂ outcome with a had₃ outcome (or an optimize with a decision outcome) is silently
accepted: `exact_value()` on two *incomparable* quantities is compared as if for one
instance, yielding a spurious `AGREED_KILL`/`SHC_CANDIDATE` or a false
`CriticalDisagreement` (which would halt a batch on a non-bug). Every other module in this
phase applies defense-in-depth consistency guards (`result.__post_init__`, the
`bool`-rejection in both backends, the type checks in `verifier.py`); this raises-only
gate is the one place that trusts its inputs' shape.
**Fix:**
```python
if a.problem != b.problem or a.mode != b.mode:
    raise CriticalDisagreement(
        f"mismatched outcomes: a=({a.problem},{a.mode}) b=({b.problem},{b.mode}) "
        "— the differential gate compares two solves of ONE instance/mode"
    )
if a.mode != "optimize":
    raise ValueError("differential_verdict is an optimize-mode gate")
```

### WR-03: CP-SAT search log is claimed "archived" but is silently discarded

**File:** `src/alpha2/solvers/cpsat.py:32`, `cpsat.py:217-218`, `cpsat.py:337-338`
**Issue:** The module docstring states "The search log is archived (not printed)" and the
inline comment calls `log_search_progress=True` the "analog of CBC's logPath". But with
`log_to_stdout=False` and **no** `solver.log_callback` (and no log field on
`ExactOutcome`), the generated log goes nowhere — it is neither printed nor captured. The
CBC path genuinely archives (writes `logPath` to a temp file and reads it back into
`log_text` for `parse_bound`); the CP-SAT path derives its bound from
`solver.best_objective_bound` directly and needs no log. In an evidence-discipline
codebase ("evidence + dual bound", "nothing rests on memory") a docstring asserting
archival that the code does not perform is a real defect, and `log_search_progress=True`
adds solver overhead for output that is dropped.
**Fix:** Either capture the log (`solver.log_callback = lines.append` and thread it into
the outcome / a temp file, mirroring CBC) to make the "archived" claim true, or drop
`log_search_progress=True` and correct the docstring to say the CP-SAT bound comes from
`best_objective_bound`, not an archived log.

## Info

### IN-01: `solve_had2_sound_sb` silently assumes a CP-SAT backend and optimize mode

**File:** `src/alpha2/solvers/symmetry.py:80-96`
**Issue:** It calls `backend.solve_had2(..., symmetry_level=symmetry_level)`, but only
`CPSATBackend.solve_had2` accepts `symmetry_level` — passing a `CBCBackend` raises a bare
`TypeError`. It also forwards `mode` but no `target_k`, so `mode="decision"` fails inside
the backend (and `assume_and_verify`'s impossibility check only fires on `PROVED_OPTIMAL`,
an optimize-only status). The helper is effectively CP-SAT-optimize-only while its
signature suggests generality. Behavior is fail-safe (a `TypeError`, not a wrong answer).
**Fix:** Document the CP-SAT/optimize precondition in the docstring, or guard it:
`if mode != "optimize": raise ValueError(...)` and assert the backend exposes
`symmetry_level`.

### IN-02: `chi` is an untrusted caller-supplied parameter in `differential_verdict` and `assume_and_verify`

**File:** `src/alpha2/solvers/differential.py:45`, `src/alpha2/solvers/symmetry.py:53`
**Issue:** The SHC/KILL boundary and the impossibility-flavored test both hinge on `chi`,
which is passed in with no in-module pinning — unlike `verify_certificate`, where `chi_G`
is pinned in both directions by the Tutte-Berge witness. A wrong `chi` flips
`SHC_CANDIDATE`↔`AGREED_KILL`. This mirrors the documented caveat on
`verify_model_record`'s `k >= chi` gate and is a caller responsibility, but is worth an
explicit docstring note that `chi` MUST originate from `verify_chi_witness` /
`verify_certificate`, never from a solver flag.
**Fix:** Add a one-line provenance requirement to both docstrings ("`chi` MUST come from
the trust root's pinned `chi_G`").

---

## Verification notes (what was checked and cleared)

- **verifier.py size-3 branch:** connectivity check is exact and complete; aliasing,
  range, disjointness, and the C(k,2) cross-adjacency `_is_conflict` sweep all still fire
  for size-3 sets. Size-≤2 behavior byte-unchanged (regression test re-runs the frozen
  Phase-2 mutant suite; `good_record()` still returns k=16).
- **had3 checksum bijections** verified by hand on triangle-free H; no spurious conflict
  is ever enumerated (the direction that could fabricate a false impossibility), and every
  `(u,w)` in a `W(T)` pair is provably a G-edge, so `mv[S]` always exists.
- **Status mapping / `-O` correctness:** all guards are `if not cond: raise`/`→ERROR`;
  no `assert` on any soundness path; `-O` canaries pass for both the CP-SAT and
  differential paths.
- **Determinism:** `num_workers=1` + pinned seed on both `solve_had2`/`solve_had3`;
  conflict rows emitted in `sorted()` order.
- **Library confinement:** `ortools` only in `cpsat.py`, `pulp` only in `cbc.py`;
  `differential.py` no-solver-import test passes.
- **Fast suite:** 82 passed, 1 deselected (slow), 0 failures.

---

_Reviewed: 2026-07-22T10:15:37Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

**STATUS: issues_found — 0 BLOCKER, 3 WARNING, 2 INFO. No soundness hole found: the trust-root widening is sound and complete, had₃ conflicts are spurious-free (no false-impossibility path), status honesty and determinism hold, and solver libraries stay confined. The warnings are a Tier-1 relaxation labeling gap (WR-01), a missing problem/mode consistency guard in the differential gate (WR-02), and a false "log archived" claim in the CP-SAT adapter (WR-03).**
