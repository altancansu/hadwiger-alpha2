---
phase: 05-cp-sat-differential-gate-had
verified: 2026-07-22T10:07:43Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 5: CP-SAT, Differential Gate & had₃ Verification Report

**Phase Goal:** The complete exact-arbitration stack: a second independent engine (OR-Tools CP-SAT backend implementing `ExactBackend`), the cross-examination differential harness that gates every SHC-CANDIDATE, the had₃ (branch-set-3) escalation tier ready to fire same-day, and symmetry-breaking that can never contaminate an impossibility branch.
**Verified:** 2026-07-22T10:07:43Z
**Status:** passed
**Re-verification:** No — initial verification

**Note on mode:** ROADMAP marks this phase `mode: mvp`, but the phase goal is a technical-deliverable statement, not an "As a … I want … so that …" User Story. The MVP User-Flow-Coverage narrowing therefore does not apply; verification proceeds against the four ROADMAP Success Criteria (the roadmap contract), as directed. This is noted, not treated as a gap.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth (Success Criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | CP-SAT agrees with CBC on every shared CI-panel instance (both PROVED_OPTIMAL, equal had₂, both families verified, seed-137=17 included); recorded claims deterministic (num_workers=1 + pinned seed) | ✓ VERIFIED | Live: C5 → cbc PROVED_OPTIMAL 3, cpsat PROVED_OPTIMAL 3, backend_version `ortools==9.15.6755`. `cpsat.py` sets `num_workers=1` + `random_seed=137` unconditionally (lines 207–208). Fast panel `test_differential_panel.py::test_agreement_panel_fast` green. seed-137 slow leg present + `@pytest.mark.slow`, regenerates (m==177, nu==15, chi==16) before solving, asserts both PROVED_OPTIMAL==17, bound==17, routes through `differential_verdict` + `verify_certificate`; executor ran it green (201 s, recorded in 05-07-SUMMARY, CP-SAT ~0.25 s). |
| 2 | Differential harness makes disagreement release-blocking (CRITICAL, quarantine, halt); SHC-CANDIDATE assignable only when BOTH prove optimality with equal had₂ < χ | ✓ VERIFIED | Live: `differential_verdict` returns AGREED_KILL (C5, equal 3 ≥ χ=3), SHC_CANDIDATE (equal 2 < χ=3), INSUFFICIENT (one INCUMBENT_ONLY), and raises `CriticalDisagreement` on unequal proven optima (2 vs 3). `differential.py` stdlib-only (imports only `Status`), raises-only (0 asserts). Metamorphic `assert_not_below_verified` present. `-O` canary `test_solver_paths_dash_O.py` green under `python -O`. |
| 3 | had₃ behind a flag on BOTH backends — seagull-tier (≤1 H-edge), common-H-neighborhood pruning, fires only on had₂<χ; proven on synthetic size-3-forced instances; verifier extended to size-3 with connectivity checks | ✓ VERIFIED (principled deviation, goal-preserving) | Live on forced n=7 instance: had₂ = 4 on both backends; `solve_had3` → PROVED_OPTIMAL 5 on both (CBC==CP-SAT), max branch-set size 3 (a triple is load-bearing), family verifies k=5 through the widened trust root. `had3.py` triple index `(…)<=1` H-edge, conflicts from `W(T)=adj[a]&adj[b]&adj[c]`, independent degree/codegree ChecksumError gate (checksum passed live: 19 triples, 6 conflicts). `verify_model_record` size gate `not in (1,2,3)` + explicit `g_edges < 2` size-3 connectivity check (verifier.py 107–124); `test_verifier_size3_mutants` rejects disconnected/size-4/aliased. `solve_had3` is a separate flagged method, never on the had₂ path (trigger discipline). See deviation note below. |
| 4 | Symmetry-breaking is assume-and-verify: the H=C₅ "WLOG vertex unused" disaster is a passing regression; impossibility-direction runs re-execute without SB | ✓ VERIFIED | Live: fabricated C5 SB-on had₂=2 (< χ=3) → `assume_and_verify` reruns without SB and returns 3; unguarded (`rerun_no_sb=None`) raises `SBContaminationError`; on/off differential `had₂(symmetry_level=2)==had₂(no SB)==3`. `symmetry.py` stdlib-only (imports only `Status`, no pulp/ortools/pynauty), raises-only. `test_symmetry_assume_verify.py` green (7 cases). |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/alpha2/solvers/cpsat.py` | CP-SAT `ExactBackend`, only ortools importer, map_status two-condition gate, determinism, register_backend | ✓ VERIFIED | 381 lines; `register_backend("cpsat", …)`; reuses `build_had2_problem`; two-condition PROVED_OPTIMAL gate; `solve_had3` present. |
| `src/alpha2/solvers/problems/had3.py` | Backend-neutral seagull triple model + checksum | ✓ VERIFIED | 126 lines; `build_had3_problem` with independent degree/codegree checksum; no solver import. |
| `src/alpha2/corpus/verifier.py` | Size gate widened to {1,2,3} + size-3 connectivity | ✓ VERIFIED | `not in (1,2,3)` + `g_edges < 2` check; 0 asserts; size-≤2 paths unchanged. |
| `src/alpha2/solvers/differential.py` | CriticalDisagreement + differential_verdict + metamorphic guard | ✓ VERIFIED | stdlib-only, imports only `Status`; SOLE SHC-CANDIDATE licenser. |
| `src/alpha2/solvers/cbc.py` (solve_had3) | had₃ on CBC backend | ✓ VERIFIED | `solve_had3` + `_guarded_extract3` added; `problem="had3"`; solve_had2 untouched. |
| `src/alpha2/solvers/symmetry.py` | assume_and_verify + SBContaminationError | ✓ VERIFIED | stdlib-only; no pynauty/ortools/pulp; sound path via `symmetry_level`. |
| `tests/test_differential_panel.py` | Dual-backend agreement panel + seed-137 slow leg | ✓ VERIFIED | Fast panel + `@pytest.mark.slow` seed-137 leg through `differential_verdict`. |

### Key Link Verification

| From | To | Via | Status |
| --- | --- | --- | --- |
| cpsat.py | problems.had2.build_had2_problem | shared checksum-gated translation | ✓ WIRED |
| cpsat.py | backend.register_backend("cpsat") | module-bottom registry hook | ✓ WIRED |
| cpsat.py / cbc.py | problems.had3.build_had3_problem | shared Had3Problem translation | ✓ WIRED |
| differential.py | result.Status.PROVED_OPTIMAL | two-outcome comparison | ✓ WIRED |
| test_differential_panel.py | get_backend('cbc')+get_backend('cpsat') → differential_verdict | agreement licensed only through gate | ✓ WIRED |
| symmetry.py | get_backend('cpsat').solve_had2(…, symmetry_level=…) | sound SB path | ✓ WIRED |

### Behavioral Spot-Checks

| Behavior | Result | Status |
| --- | --- | --- |
| C5 had₂ dual-backend agreement | cbc=3, cpsat=3, both PROVED_OPTIMAL | ✓ PASS |
| differential verdicts (AGREED_KILL/SHC/INSUFFICIENT/CRITICAL) | all four paths behave per contract | ✓ PASS |
| had₃ escalation on forced n=7 (had₂=4 → had₃=5, CBC==CP-SAT, triple used, verified k=5) | as expected | ✓ PASS |
| C5 SB disaster restored (2→3) + SBContaminationError + on/off equal | as expected | ✓ PASS |
| had₃ checksum gate live (19 triples, 6 conflicts) | gate passed | ✓ PASS |

### Probe / Suite Execution

| Command | Result | Status |
| --- | --- | --- |
| `pytest -q -m "not slow"` | 195 passed, 6 deselected (31.7 s) | ✓ PASS |
| `pytest` (7 phase-5 test files) | 76 passed | ✓ PASS |
| `python -O -m pytest test_verifier_dash_O.py test_solver_paths_dash_O.py` | 4 passed (fail-closed under -O) | ✓ PASS |
| seed-137 slow leg (`pytest -m slow`) | executor-run green, 201 s (recorded 05-07-SUMMARY) — not re-run per instructions | ✓ PASS (recorded) |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| EXACT-03 | 05-01, 05-05, 05-07 | CP-SAT backend implements ExactBackend, deterministic recorded mode | ✓ SATISFIED | cpsat.py registered, deterministic, seed-137 proved |
| EXACT-04 | 05-04, 05-07 | Differential harness (disagreement release-blocking); SHC-CANDIDATE gate | ✓ SATISFIED | differential.py + panel through the gate |
| EXACT-05 | 05-02, 05-03, 05-05 | had₃ seagull tier behind flag, verifier extended to size-3 | ✓ SATISFIED | had3.py + widened verifier + dual-backend had₃ |
| EXACT-06 | 05-06 | Assume-and-verify symmetry breaking; C5 disaster regression | ✓ SATISFIED | symmetry.py + passing regression |

No orphaned requirements: all four IDs mapped to Phase 5 in REQUIREMENTS.md (marked Complete) and declared in plan frontmatter.

### Anti-Patterns Found

None. No `TBD`/`FIXME`/`XXX` debt markers, no `TODO`/`HACK`/`PLACEHOLDER`/"not implemented" in any phase-modified source file. Confinement intact: ortools imported only in cpsat.py; pulp only in cbc.py. Raises-only preserved (0 asserts) in differential.py, symmetry.py, verifier.py.

### Principled Deviation (goal-preserving, not a gap)

Plans 05-02 and 05-05 literally specified a size-3-forced instance with `had₂ < χ`. No such triangle-free H is known — one would itself be a Hadwiger counterexample (all 296 corpus instances are killed at had₂). Per the project CORE value ("never invent the missing hour") and CLAUDE.md's radioactive-impossibility discipline, the executors honestly substituted the `had₂ < had₃` size-3-forced escalation signal (real n=7 instance: had₂=4 < had₃=5), documented in-test and in the SUMMARYs. The had₃ machinery the goal requires — flagged `solve_had3` on both backends, shared checksum-gated `Had3Problem`, common-H-neighborhood conflict pruning, widened trust root, CBC-vs-CP-SAT differential — is fully built and proven. Only the unrealizable numeric premise changed; the escalation tier is genuinely "ready to fire same-day" on the first real had₂ < χ event. SC3's "proven on synthetic size-3-forced instances" is satisfied; the "fires only on had₂ < χ" clause is honored as a workflow/trigger discipline (solve_had3 is a separate flagged method never run on the had₂ path). Treated as goal-preserving.

### Human Verification Required

None. All four success criteria are programmatically verifiable and were verified live in this session (plus the recorded executor-run seed-137 slow leg). No visual/UX/external-service items.

### Gaps Summary

None. The complete exact-arbitration stack is present, substantive, wired, and behaviorally confirmed: a second independent CP-SAT engine agreeing with CBC (including seed-137=17 in deterministic mode), a release-blocking differential gate that solely licenses SHC-CANDIDATE, a dual-backend had₃ seagull tier proven on a synthetic size-3-forced instance with the trust root widened to size-3, and assume-and-verify symmetry breaking with the C₅ disaster as a passing regression. The one deviation (had₂<had₃ substituted for the unrealizable had₂<χ premise) is an epistemically-correct, goal-preserving choice mandated by the project's CORE value.

---

_Verified: 2026-07-22T10:07:43Z_
_Verifier: Claude (gsd-verifier)_
