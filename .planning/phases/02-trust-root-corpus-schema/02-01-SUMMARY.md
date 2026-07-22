---
phase: 02-trust-root-corpus-schema
plan: 01
subsystem: corpus-verifier
tags: [trust-root, verifier, stdlib-only, python-O, tutte-berge, witness, mutant-suite, ast-guard, chi-02, vrf-01]

# Dependency graph
requires:
  - Pinned CPython 3.12.13 env + src/alpha2 package (Phase 1)
  - Frozen canonical H_edges sha256 convention + golden 3c953d90…41e2 (Phase 1)
  - triangle_free_process(n, Random(seed)) deterministic generator (Phase 1)
  - matching_number(adj, n) nu oracle (Phase 1)
provides:
  - src/alpha2/corpus/verifier.py — stdlib-only TRUST ROOT (own _is_conflict, VerificationError, verify_model_record, verify_chi_witness); raise-based, zero asserts, correct under python -O
  - src/alpha2/invariants/witness.py — emission-time (UNTRUSTED) extract_witness(adj,n) -> (M,U,nu) Tutte-Berge extractor
  - src/alpha2/invariants/matching.py::matching_edges — canonical [min,max] max-matching edges (keeps the sole blossom call in matching.py)
  - Adversarial proof: 5-mutant suite + python -O fail-closed canary + AST import-boundary/zero-assert guard + M+U hand-check (seed 1 & 137 + synthetic U!=[] star + wrong-chi mutant)
affects: [02-02-schema-store, 03-corpus-reproduction-ci]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Trust root reimplemented from the CONTRACT (Appendix C.1 + E §4.6), never by porting the assert-based verify/model.py — which stays byte-verbatim"
    - "Every check is `if not cond: raise VerificationError(...)` — zero asserts, AST-enforced, correct under python -O"
    - "Verifier rebuilds H-adjacency from stored H_edges and re-derives conflict/odd-components; trusts no emission artifact"
    - "Blossom max_weight_matching stays confined to invariants/matching.py (CHI-01 AST guard); witness.py delegates to it rather than calling networkx directly"
    - "Docstring prose avoids grep-trigger tokens (networkx/assert); the AST guard is the real mechanism check (Phase-1 precedent)"

key-files:
  created:
    - src/alpha2/corpus/__init__.py
    - src/alpha2/corpus/verifier.py
    - src/alpha2/invariants/witness.py
    - tests/test_verifier_mutants.py
    - tests/test_verifier_dash_O.py
    - tests/test_verifier_isolation.py
    - tests/test_tutte_berge.py
  modified:
    - src/alpha2/invariants/matching.py

key-decisions:
  - "verify_chi_witness landed in the Task-2 verifier.py commit (one commit earlier than the plan's Task-3 split): it is the same stdlib-only trust-root module and a cohesive single-file trust boundary is cleaner than an artificial split"
  - "Added matching_edges() to invariants/matching.py so witness.py can obtain the matching M without calling max_weight_matching outside matching.py (the CHI-01 AST guard pins the blossom call there)"
  - "Mutant (e) uses chi_G=17 at the family-size boundary; the lowered-chi (chi_G=15) case is proven at the witness boundary in verify_chi_witness — the two wrong-chi failure modes are distinct"

requirements-completed: [VRF-01, CHI-02]

# Metrics
duration: ~12min
completed: 2026-07-22
---

# Phase 02 Plan 01: Trust Root — Independent stdlib-only Verifier + Tutte-Berge Witness Summary

**The program's trust root now exists: `corpus/verifier.py` is a stdlib-only, zero-assert, raise-based verifier that refuses every adversarial mutant, fails closed under `python -O`, carries its own `_is_conflict`, rebuilds H from stored `H_edges`, and pins χ = n − ν both directions from a stored Tutte-Berge witness — sharing no logic with any searcher and importing nothing from the toolkit.**

## Performance
- **Duration:** ~12 min
- **Tasks:** 3 (all committed atomically)
- **Files:** 7 created, 1 modified; full suite 23 tests green

## Accomplishments
- **VRF-01 trust root** (`src/alpha2/corpus/verifier.py`): `VerificationError`, private `_is_conflict` (byte-identical logic to Appendix C.1, never imported), `_build_adj` (rebuilds adjacency from stored `H_edges`, raises on malformed/non-canonical/duplicate), `verify_model_record` (returns k; recomputes canonical sha256, checks k≥χ, sizes∈{1,2}, in-range, globally disjoint, size-2 sets are G-edges, all C(k,2) cross-adjacencies). 19 `raise VerificationError`; **zero asserts** (AST-enforced); stdlib-only (`json`, `hashlib`, `collections`).
- **CHI-02 witness re-check** (`verify_chi_witness`, same module): validates M is a matching in H with |M|==ν (ν≥|M|), counts odd-order components of H−U by stdlib BFS, requires (n−c_odd+|U|)//2 == ν (ν≤ that) — pinning χ = n − ν in both directions. **General** path: U is read and removed, never assumed empty.
- **Emission extractor** (`src/alpha2/invariants/witness.py`): `extract_witness(adj,n) -> (M,U,nu)` via Gallai-Edmonds probing (D = exposable vertices, U = A(G)); UNTRUSTED, never imported by the verifier.
- **Adversarial proof (4 test files):** 5-mutant suite (overlap / H-edge pair / missing cross-adj / truncated `fam[:-1]` / wrong χ=17) each raises, good_record() passes returning k=16 with golden sha `3c953d90…41e2`; `python -O` subprocess canary (real `if __debug__` branch, overlapping known-bad record → returncode 0); AST isolation guard (stdlib allow-list imports, zero `ast.Assert`, ≥6 `raise VerificationError`); Tutte-Berge hand-check for seed 1 & 137 (U=[], ν=15, χ=16 both directions) + synthetic K_{1,3} star (U=[0] non-empty → exercises the general odd-component path) + wrong-chi witness mutant (χ_G=15 → raises at the n−ν≠χ boundary).
- **Anchor preserved:** `src/alpha2/verify/model.py` byte-unchanged (`git diff --quiet` holds); `grep -c "networkx\|import nx" corpus/verifier.py` == 0; CHI-01 AST guard still green (now also scanning `witness.py`).

## Task Commits
1. **Task 1: RED adversarial trust-root suite** — `e307691` (test) — mutants, `-O` canary, AST isolation; all fail at import (verifier absent)
2. **Task 2: stdlib-only trust-root verifier (VRF-01 + witness)** — `65bb28c` (feat) — `verify_model_record` + `verify_chi_witness`; mutants/isolation/`-O` GREEN
3. **Task 3: Tutte-Berge extractor + hand-check tests (CHI-02)** — `6fae758` (feat) — `witness.py`, `matching_edges`, `test_tutte_berge.py`; full suite green

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `matching_edges()` to `invariants/matching.py`**
- **Found during:** Task 3.
- **Issue:** `extract_witness` needs the actual maximum-matching EDGES M, but the Phase-1 CHI-01 AST guard (`tests/test_chi_no_estimate.py`) pins every `max_weight_matching` call to `invariants/matching.py`. Calling it from `witness.py` (per RESEARCH Code Examples §4) would trip that guard and break the full suite.
- **Fix:** Added an additive `matching_edges(adj, n)` helper to `matching.py` (returns canonical `[min,max]` pairs; `matching_number` untouched). `witness.py` reuses it plus `matching_number`, so the sole blossom call stays in `matching.py` and `witness.py` imports no graph library directly.
- **Files modified:** `src/alpha2/invariants/matching.py`, `src/alpha2/invariants/witness.py`.
- **Verification:** `test_chi_no_estimate.py`, `test_verifier_isolation.py`, and full suite (23) all green; `matching_number` bytes/behavior unchanged (golden fingerprint unaffected).
- **Committed in:** `6fae758`.

**2. [Rule 2 - Guard hygiene] Reworded verifier docstring to drop grep-trigger tokens**
- **Found during:** Task 2.
- **Issue:** The plan's Task-3 acceptance uses a literal `grep -c "networkx\|import nx" ... == 0`; my docstring prose contained the words "networkx" and "assert", producing false-positive matches (the same false-positive class Phase 1 resolved for CHI-01).
- **Fix:** Reworded the module docstring ("no third-party graph library", "no optimization-stripped statements") so both the literal grep guards and the authoritative AST guard read clean. No code changed.
- **Files modified:** `src/alpha2/corpus/verifier.py` (docstring only).
- **Committed in:** `65bb28c`.

### Structural note (not a deviation in behavior)
`verify_chi_witness` was written into `verifier.py` in the Task-2 commit rather than added in a separate Task-3 verifier edit. It is the same stdlib-only trust-root surface; a single cohesive module is cleaner than splitting the two verify functions across commits. All Task-3 acceptance criteria for `verify_chi_witness` are met.

**Total deviations:** 2 auto-fixed (1 blocking, 1 guard-hygiene). No architectural changes, no scope creep, no authentication gates.

## Known Stubs
None. Schema.py / store.py are Plan 02 scope (the verifier consumes plain dicts by design); the verifier and witness are fully wired and adversarially proven.

## Verification Evidence
- `uv run pytest -q` → **23 passed**.
- `uv run pytest tests/test_verifier_mutants.py tests/test_verifier_dash_O.py tests/test_verifier_isolation.py tests/test_tutte_berge.py -x` → all green.
- `git diff --quiet src/alpha2/verify/model.py` → clean (byte-unchanged).
- `grep -c "raise VerificationError" src/alpha2/corpus/verifier.py` → 19 (≥6).
- `grep -c "networkx\|import nx" src/alpha2/corpus/verifier.py` → 0.
- `PYTHONPATH=src uv run python -O -m pytest tests/test_verifier_dash_O.py` → passed.

## Next Plan Readiness
Plan 02-02 (schema v1 + append-only atomic store) can now gate every append on `verify_model_record` + `verify_chi_witness`. The trust root is proven; nothing enters the corpus unverified.

## Self-Check: PASSED
All 8 created files present on disk; all 3 task commits (e307691, 65bb28c, 6fae758) exist in git history.
