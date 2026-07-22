---
phase: 05-cp-sat-differential-gate-had
plan: 05
subsystem: solvers
tags: [had3, size-3, escalation, cbc, cpsat, ortools, pulp, differential, EXACT-05, EXACT-03]

# Dependency graph
requires:
  - phase: 05-cp-sat-differential-gate-had
    provides: had3.py Had3Problem (seagull Tier-1 triple/conflict model, checksum-gated) — Plan 02
  - phase: 05-cp-sat-differential-gate-had
    provides: widened verify_certificate size-{1,2,3} trust root (>=2-G-edges size-3 connectivity) — Plan 03
  - phase: 05-cp-sat-differential-gate-had
    provides: CPSATBackend + CBCBackend solve_had2 (two-field/two-condition PROVED_OPTIMAL gate, guarded extraction) — Plan 01
provides:
  - solve_had3 on BOTH exact backends behind its own method (a flag), translating the SAME frozen Had3Problem
  - A synthetic size-3-forced dual-backend proof — had_2=4 < had_3=5 on CBC and CP-SAT, the size-3 family arbitrated by the widened trust root
  - The third of three independent size-3 guards: the CBC-vs-CP-SAT had_3 differential
affects: [05-differential-gate, 06-battery, had3-escalation-certificates, runbook-step-5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Escalation-tier additivity: solve_had3 mirrors solve_had2 (same status gate, same bound provenance) but is a SEPARATE method — never on the had_2 path; solve_had2 + _guarded_extract left byte-unchanged (frozen reference lineage)"
    - "Shared-instance differential across sizes: both backends translate the SAME checksum-gated Had3Problem, so a CBC-vs-CP-SAT had_3 agreement is meaningful (identical instance, independent encoding)"
    - "Honest synthetic instance: escalation proven on had_2<had_3 (not had_2<chi, which is unknown for triangle-free H) — the machinery is real even though no real had_2<chi corpus event exists"

key-files:
  created:
    - tests/test_had3_backends.py
  modified:
    - src/alpha2/solvers/cbc.py
    - src/alpha2/solvers/cpsat.py

key-decisions:
  - "Escalation instance is the honest had_2<had_3 size-3-forced H (n=7, had_2=4=chi < had_3=5), NOT the plan's literal had_2<chi: no triangle-free H with had_2<chi is known (296/296 killed at had_2; a fresh ~55k-trial small-graph search over n=6..11 finds none), and CORE value forbids inventing one. Matches the Plan 02 recorded decision."
  - "solve_had3 is the seagull/Tier-1 model: had_2 vars + triple vars (<=1 internal H-edge) + triple-single/triple-pair conflicts; NO triple-triple (Tier-2) conflicts — the trust root is the arbiter of any Tier-1 model gap, and on this instance the optimum (5) is confirmed sound by the verifier and CBC==CP-SAT."
  - "New _guarded_extract3 in each backend extends the had_2 guards over triple vars (integrality incl. triples for CBC; scale-robust round(obj)==count recompute; internal disjointness) rather than mutating _guarded_extract (kept byte-stable for the WR-03 direct-drive tests)."

patterns-established:
  - "The three size-3 guards are now all landed and independent: enumeration checksum (Plan 02 had3.py), trust-root verifier (Plan 03), CBC-vs-CP-SAT had_3 differential (this plan) — a lost size-3 row inflates one backend's had_3 above the other's."
  - "Trigger discipline in tests: assert the had_2 baseline (both backends agree) FIRST, confirm it falls short (had_2<had_3), THEN escalate to solve_had3 — never speculatively."

requirements-completed: [EXACT-05, EXACT-03]

# Metrics
duration: 14min
completed: 2026-07-22
---

# Phase 05 Plan 05: Dual-Backend had₃ Escalation Summary

**`solve_had3` added to BOTH exact backends behind its own method — each translating the SAME frozen seagull-tier `Had3Problem` — proven on a synthetic size-3-forced instance where CBC and CP-SAT agree on had₂=4 < had₃=5, the size-3 family passing the widened trust root, closing the third of three independent size-3 guards.**

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-07-22
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- `CBCBackend.solve_had3` and `CPSATBackend.solve_had3`: the size-3 escalation tier, each mirroring its own `solve_had2` (had₂ vars + G-edge pairs + singletons) and adding checksum-gated triple vars (≤1 internal H-edge) plus per-vertex disjointness over triples and triple-single/triple-pair conflict rows — all from the SAME `Had3Problem` the twin backend translates.
- Same two-field (CBC) / two-condition (CP-SAT) `PROVED_OPTIMAL` gate and guarded extraction (new `_guarded_extract3`, extended over triple vars), same determinism (single-thread CBC; `num_workers=1` + pinned seed CP-SAT), same bound provenance. `solve_had2` and its `_guarded_extract` left byte-unchanged.
- On the synthetic size-3-forced H (n=7): both backends return `PROVED_OPTIMAL` had₃ = 5 > had₂ = 4, the extracted size-3 family (`{0,5,6}` plus four singletons) passes the widened `verify_certificate` (k=5), and CBC == CP-SAT on had₃ (the differential guard).
- Confinement preserved (ortools only in `cpsat.py`, pulp only in `cbc.py`); full fast suite 186/186 green; the `-O` solver-path canary still fails closed.

## Task Commits

1. **Task 1: RED — synthetic size-3-forced dual-backend had₃ test** - `0b426ca` (test)
2. **Task 2: GREEN — add solve_had3 to cbc.py and cpsat.py** - `354b1ab` (feat)

_No REFACTOR commit: solve_had3 is an additive method mirroring the proven solve_had2 shape; nothing to clean up._

## Files Created/Modified
- `src/alpha2/solvers/cbc.py` — Added `solve_had3` (LpProblem "had3": G-edge pair vars + singletons + triple vars; disjointness incl. triples; had₂ + triple-single/triple-pair conflict rows; two-field gate; `ExactOutcome(problem="had3")`) and `_guarded_extract3` (integrality incl. triples + scale-robust recompute + disjointness). Import of `build_had3_problem` added. `solve_had2` / `_guarded_extract` untouched.
- `src/alpha2/solvers/cpsat.py` — Added `solve_had3` (cp_model "had3": bool pairs/singletons/triples; `add_at_most_one` disjointness incl. triples; had₂ + triple conflict rows; OPTIMAL+obj==bound gate; `num_workers=1`+seed) and `_guarded_extract3`. Import of `build_had3_problem` added. `solve_had2` / `_guarded_extract` untouched.
- `tests/test_had3_backends.py` (new) — Embeds the size-3-forced H + pinned invariants; asserts the had₂ baseline agreement (escalation trigger) FIRST, then had₃=5 on both backends through `verify_certificate`, the CBC==CP-SAT had₃ differential, and that a size-3 branch set is load-bearing.

## Decisions Made
- **Honest escalation instance (deviation — see below).** The plan's must-haves specify a `had_2 < chi` size-3-forced instance with `had_3 == chi`. No triangle-free H with `had_2 < chi` is known (296/296 corpus instances are killed at had₂; a fresh ~55k-trial exhaustive-style random search over n=6..11 found none), and the CORE value forbids inventing one. As Plan 02 already established for the had₃ *model* test, the honest escalation signal is `had_2 < had_3`: on the pinned n=7 instance had₂ = 4 = χ < had₃ = 5, so the size-3 branch set is genuinely load-bearing. The escalation *machinery* the plan asks for — flagged `solve_had3` on both backends, the shared `Had3Problem`, the widened trust root, and the CBC-vs-CP-SAT differential — is fully proven; only the (impossible-to-honestly-realize) `had_2 < chi` numeric literal is replaced by `had_2 < had_3`.
- **Seagull/Tier-1 only.** `solve_had3` carries triple-single and triple-pair conflicts (the checksum-gated `Had3Problem.conflicts`), not Tier-2 triple-triple conflicts. The trust root arbitrates any Tier-1 model gap; on this instance the optimum (5, single triple) is confirmed sound by both the verifier and CBC==CP-SAT.
- **`_guarded_extract3` rather than mutating `_guarded_extract`.** The had₂ extractor is directly driven by the WR-03 regression tests (fixed signature), so the triple-aware guards live in a new function; `solve_had2` stays the frozen reference lineage.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Correctness/epistemic-honesty] Escalation instance uses had₂ < had₃, not had₂ < χ**
- **Found during:** Task 1 (RED test construction)
- **Issue:** The plan's must-haves (truths 2 & 3) and success criteria require a synthetic instance with `had_2 < chi` and `had_3 == chi`. Such a triangle-free H is not known to exist — 296/296 corpus instances are killed at had₂, the Plan 02 recorded decision states the same, and a fresh ~55k-trial small-graph search (n=6..11, validated against networkx ν) found zero `had_2 < chi` instances. Pinning a fabricated `had_2 < chi` literal would violate the project's CORE value ("never invent the missing hour") and the trust-root discipline.
- **Fix:** Used the honest, brute-force-established size-3-forced instance (n=7, had₂=4=χ < had₃=5 — the same instance Plan 02's `test_size3_forced_instance_shape` uses). The test asserts the had₂ baseline agreement first (both backends, the escalation trigger), documents `had_2 == chi` explicitly, then proves had₃=5 on both engines with the size-3 family routed through the widened trust root. All of the plan's *machinery* requirements (dual-backend solve_had3, shared Had3Problem, widened verifier, CBC==CP-SAT differential, size-3 family load-bearing) are met.
- **Files modified:** tests/test_had3_backends.py (module docstring + in-file EPISTEMIC NOTE document the substitution and its justification)
- **Verification:** `verify_certificate` returns k=5 on the extracted family; CBC value == CP-SAT value == 5; max branch-set size == 3.
- **Committed in:** `0b426ca` (Task 1) / proven green in `354b1ab` (Task 2)

---

**Total deviations:** 1 auto-fixed (1 correctness/epistemic-honesty)
**Impact on plan:** The escalation tier is fully built and proven; only the unrealizable `had_2 < chi` numeric premise was replaced by the honest `had_2 < had_3` signal (consistent with Plan 02). No scope creep; no machinery omitted.

## Issues Encountered
- Confirmed empirically (before writing any test) that the Tier-1 model — had₂ conflicts + triple-single/triple-pair conflicts, no triple-triple — yields exactly the true optimum (5) on the forced instance, so the omitted Tier-2 conflicts do not over-count here. Guarded regardless by `verify_certificate` and the differential.
- `gsd-sdk query state.record-metric` / `state.add-decision` take named flags (`--phase/--plan/--duration/--tasks/--files`, `--summary`), not positional args — corrected after the first invocation.

## Threat Model Verification
- **T-05-14 (inflated had₃ from a lost size-3 constraint):** mitigated — all three independent guards now landed: the had3 checksum (`build_had3_problem`, Plan 02), the widened `verify_certificate` (Plan 03), and the CBC-vs-CP-SAT had₃ differential (`test_had3_differential_agreement`, this plan). A lost row would show as one backend > the other on the tiny instance.
- **T-05-15 (speculative escalation):** mitigated — `solve_had3` is a separate flagged method, never on the had₂ path; the test asserts the had₂ baseline (escalation trigger) before escalating.
- **T-05-16 (false had₃ optimum):** mitigated — same two-field (CBC) / two-condition (CP-SAT) `PROVED_OPTIMAL` gate + guarded extraction (`_guarded_extract3`), extended over triple vars; `-O` solver-path canary still green.
- **T-05-SC (supply chain):** N/A — no package installed; ortools stays confined to `cpsat.py`, pulp to `cbc.py`.

## User Setup Required
None - no external service configuration required. ortools + pulp/CBC already pinned; nauty/geng not exercised.

## Next Phase Readiness
- The had₃ escalation tier is real, dual-backend, and cross-checked — ready for the Phase-6 battery to wire it into runbook step 5 (escalate on a certified had₂ < χ). Whenever a real had₂ < χ event first appears, `solve_had3` can be fired same-day.
- The differential gate (`solvers/differential.py`, Plan 04) applies unchanged to had₃ outcomes (both carry `problem="had3"` and the same `Status` vocabulary).
- Deferred (carried forward, unchanged): the distinct `had_3`/`had_le3` corpus-field naming, to be resolved by the first real escalation-certificate consumer (Phase 6/11); Tier-2 (G-triangle triple-triple) conflicts behind the same flag if a future instance needs them.

## Self-Check: PASSED

All created/modified files present on disk; both task commits (`0b426ca` test, `354b1ab` feat) exist in history.

---
*Phase: 05-cp-sat-differential-gate-had*
*Completed: 2026-07-22*
