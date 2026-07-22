---
phase: 05-cp-sat-differential-gate-had
plan: 03
subsystem: testing
tags: [verifier, trust-root, had3, size-3, python-O, mutants, EXACT-05]

# Dependency graph
requires:
  - phase: 02-corpus-schema-store-verifier
    provides: verify_model_record trust root (size-{1,2} gate, _is_conflict, mutant + -O canary suites)
  - phase: 05-cp-sat-differential-gate-had
    provides: had3.py size-3 triple/conflict model (same >=2-G-edges connectivity rule)
provides:
  - Trust root widened to accept size-3 branch sets iff connected in G (>=2 internal G-edges)
  - Size-3 adversarial mutant suite (disconnected/zero-G-edge/missing-cross-adj/size-4/aliased)
  - Extended -O canary proving the size-3 path fails closed under python -O
affects: [05-differential-gate, 06-battery, had3-escalation-certificates]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Trust-root widening discipline: change ONLY the new size branch; keep size-<=2 + _is_conflict byte-identical; re-prove with new mutants + full prior suites + extended -O canary"
    - "Size-3 connectivity by explicit >=2-G-edges count, matching had3.py's index rule (single source of the graph fact)"

key-files:
  created:
    - tests/test_verifier_size3_mutants.py
  modified:
    - src/alpha2/corpus/verifier.py
    - tests/test_verifier_dash_O.py

key-decisions:
  - "Widened verify_model_record size gate {1,2}->{1,2,3} with an explicit size-3 >=2-G-edges connectivity check; size-<=2 legs and _is_conflict/C(k,2) cross-adjacency loop kept byte-identical"
  - "No schema.py change and no new had_3 invariant field this phase (RESEARCH Open-Q1/A6): size-3 escalation is proven at the trust-root level; a distinct had_3 corpus fact is deferred to the first real escalation-certificate consumer (Phase 6/11)"
  - "Size-3 mutant records are small hand-built H's with in-file canonical sha256 (mirroring the -O canary's embedded [[0,1]]), not schema.py-built records"

patterns-established:
  - "The three size-3 guards are independent: enumeration checksum (Plan 02 had3.py), trust-root verifier (this plan), differential (Plan 05); this plan lands guard 2"
  - "Raises-only widening stays -O-correct: the -O canary is extended over the new branch with a disconnected triple that must still raise (exit 0), never rubber-stamp (exit 2)"

requirements-completed: [EXACT-05]

# Metrics
duration: 10min
completed: 2026-07-22
---

# Phase 05 Plan 03: Trust-Root Size-3 Widening Summary

**Widened the frozen verifier's `verify_model_record` size gate from {1,2} to {1,2,3} with an explicit >=2-G-edges size-3 connectivity check, adversarially guarded by a size-3 mutant suite, a full-corpus re-verify, and an extended `python -O` canary — size-<=2 logic and `_is_conflict` byte-unchanged.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-22
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- Trust root now accepts a size-3 branch set **iff** it is connected in G (>=2 of its 3 internal pairs are G-edges / <=1 internal H-edge); every disconnected/malformed triple raises `VerificationError`.
- The size gate is exactly {1,2,3}: a size-4 set still raises; size-1 and size-2 paths (including the size-2 pair-is-G-edge check and the size-agnostic C(k,2) cross-adjacency loop) are byte-unchanged.
- The widened path is raises-only and fails closed under `python -O` — a disconnected size-3 record is still rejected with asserts stripped.
- Full regression proven: the Phase-2 mutant suite, the full R1 corpus, and the verifier isolation guard all stay green (172/172 in the whole suite).

## Task Commits

1. **Task 1: RED — size-3 mutant suite + connected-triple accept + -O size-3 canary** - `6deade1` (test)
2. **Task 2: GREEN — widen verify_model_record to {1,2,3} with size-3 connectivity check** - `0a199cd` (feat)

_No REFACTOR commit: the widening is a two-line size branch alongside the unchanged size-2 branch; nothing to clean up._

## Files Created/Modified
- `src/alpha2/corpus/verifier.py` - Size gate `(1,2)`->`(1,2,3)`; new size-3 branch `g_edges = (b not in adj[a])+(c not in adj[a])+(c not in adj[b]); if g_edges < 2: raise`; docstring rules 4/5 updated. `_is_conflict`, `_build_adj`, size-<=2 logic, and the C(k,2) loop untouched.
- `tests/test_verifier_size3_mutants.py` (new) - Accepts a connected triple (returns k=2); rejects disconnected triple (1 G-edge), zero-G-edge H-triangle, missing cross-adjacency (via `_is_conflict`), size-4 set, and aliased vertex; re-runs the frozen Phase-2 mutant assertions + good_record()==16 to prove size-<=2 is unchanged.
- `tests/test_verifier_dash_O.py` (extended) - Second subprocess `-O` canary embedding a disconnected size-3 record whose `model_branch_sets` triple must still raise under -O (same exit-code contract 0=raised / 2=rubber-stamped / 3=not-under-O).

## Decisions Made
- **No schema/invariant change this phase (RESEARCH Open-Q1 / A6):** the size-3 escalation is proven at the trust-root level only; `schema.build_record`'s closed invariants dict (deriving `had_2 = len(model_branch_sets)`) is untouched, and a distinct `had_3`/`had_le3` corpus fact is deferred to the first real escalation-certificate consumer. This defers only an unused storage-field naming, not any EXACT-05 behavior.
- **Hand-built size-3 mutant records** (each with its own tiny H + in-file canonical sha256) rather than schema-built records — mirroring the existing `-O` canary's embedded `[[0,1]]` and the mutant suite's "verifier consumes JSON dicts, never schema.py" discipline.
- **Connectivity expressed as an explicit `>=2 G-edges` count**, matching `had3.py`'s triple-index rule so the graph fact (3 vertices connected in G <=> >=2 internal G-edges) has one consistent statement across the enumerator and the verifier.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None. RED landed as expected (only `test_accepts_connected_triple` failed, on the size-gate rejection of size 3); GREEN turned it green with all rejection/regression tests still passing.

## Threat Model Verification
- **T-05-07 (trust-root bypass):** mitigated — explicit >=2-G-edges check; gate exactly {1,2,3}; disconnected/size-4/aliased/missing-cross-adjacency mutants each raise `VerificationError`.
- **T-05-08 (size-<=2 regression):** mitigated — size-<=2 + `_is_conflict` byte-identical; Phase-2 mutant suite + full R1 corpus green.
- **T-05-09 (assert-stripped rubber stamp):** mitigated — raises-only; -O canary extended with a bad size-3 record; `grep -c "assert " verifier.py` == 0.

## User Setup Required
None - no external service configuration required. nauty/geng not exercised; stdlib + pytest only.

## Next Phase Readiness
- The trust root can now arbitrate had_3 escalation models (guard 2 of 3). Ready for Plan 05's CBC-vs-CP-SAT had_3 differential (guard 3) and the battery wiring in Phase 6.
- No blockers introduced. The deferred `had_3` corpus-field naming remains an open item for the first real escalation-certificate consumer (Phase 6/11).

## Self-Check: PASSED

All created/modified files present on disk; all three commits (6deade1 test, 0a199cd feat, 9b01936 docs) exist in history.

---
*Phase: 05-cp-sat-differential-gate-had*
*Completed: 2026-07-22*
