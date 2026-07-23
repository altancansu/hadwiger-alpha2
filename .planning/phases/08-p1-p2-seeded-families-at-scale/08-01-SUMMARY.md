---
phase: 08-p1-p2-seeded-families-at-scale
plan: 01
subsystem: testing
tags: [pytest, tdd, red-contract, sumfree, cayley, abelian-group, g-screen, certificate-honesty, pynauty, cp-sat]

# Dependency graph
requires:
  - phase: 07-p0-cdm-frontier
    provides: "pool/cdm schema/store/verifier/adjudicate patterns (append-only hash-chain, verify-at-append, stdlib trust root) mirrored by the sumfree contract"
provides:
  - "Full executable RED contract for src/alpha2/pool/sumfree/ (12 test modules + conftest) pinning the POOL-1/POOL-2 interface surface for Waves 2-5"
  - "Certificate-HONESTY gate as a first-class executable regression (radioactive 'counterexample'/'had(G) <' strings forbidden; honest g>0 literal required)"
  - "Additive paths SUMFREE_CORPUS, P1_SHOWPIECE_CORPUS, SUMFREE_SWEEP beside the byte-frozen CORPUS"
  - "Small-Γ fixtures (Z_31, Z_53, Z_3×Z_3) + a hand-verified g<=0 KILLED record + an honesty CANARY record"
affects: [08-02 det-budget, 08-03 group/generate/dedup/rng, 08-04 screen/adjudicate/schema/store/verifier, 08-05 frontier, 08-06 slow sweep, 08-07 p1 showpieces]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RED contract via function-local imports of not-yet-existing modules (--collect-only stays clean; bodies fail on import)"
    - "Embedded-literal fixtures: zero cross-test imports so a fixture bug can never share a code path with the code under test"
    - "Descriptor-driven rebuild {invariant_factors, S} as the reproducibility unit (never RNG replay)"
    - "Honesty gate: forbidden radioactive substrings enforced in the stdlib trust root, not just at emission"

key-files:
  created:
    - tests/pool/sumfree/test_group.py
    - tests/pool/sumfree/test_generate.py
    - tests/pool/sumfree/test_structured.py
    - tests/pool/sumfree/test_dedup.py
    - tests/pool/sumfree/test_rng_v2.py
    - tests/pool/sumfree/test_schema.py
    - tests/pool/sumfree/test_store.py
    - tests/pool/sumfree/test_screen.py
    - tests/pool/sumfree/test_determinism.py
    - tests/pool/sumfree/test_frontier.py
    - tests/pool/sumfree/test_p1_sweep.py
    - tests/pool/sumfree/test_showpiece.py
  modified: []

key-decisions:
  - "Did NOT mark POOL-1/POOL-2 requirements complete: this plan lands only the RED contract; the shared phase requirements are satisfied by the implementation waves (08-03..08-07)"
  - "Two honesty tests are green-by-design (they assert the committed CANARY fixture is radioactive-clean); the fail-closed verifier honesty guards remain RED until the Wave-3/4 verifier exists"

patterns-established:
  - "Green-Ruzsa/Andrasfai structured SIZES keyed off the |Γ| mod 3 arithmetic condition (never an I/II/III numeral) — RESEARCH Pitfall 6"
  - "Every generator (structured AND random) held to the SAME brute symmetric+sum-free+maximal re-check — A1/A2, never trust a density formula"
  - "nauty-canonical dedup only; WL-hash explicitly forbidden as a dedup key (source-inspection guard)"

requirements-completed: []

# Metrics
duration: ~25min (resume session; Task 1 pre-committed)
completed: 2026-07-23
---

# Phase 8 Plan 01: POOL-1 + POOL-2 RED Contract Summary

**The complete executable sum-free g(G)-screen falsification suite (12 RED test modules + conftest) landed RED against the not-yet-built `pool/sumfree/` package, with the radioactive certificate-honesty rule pinned as a first-class regression and the frozen 296-corpus byte-untouched.**

## Performance

- **Duration:** ~25 min (resume session; Task 1 `a13a0ad` was pre-committed)
- **Completed:** 2026-07-23
- **Tasks:** 3 (Task 1 verified pre-existing; Tasks 2–3 executed here)
- **Files created:** 12 test modules (5 in Task 2, 7 in Task 3)

## Accomplishments
- Verified Task 1 (`a13a0ad`) present and did not redo it (package skeleton + additive paths + Γ/record fixtures).
- Task 2: the POOL-2 generator/dedup/RNG contract — Abelian(factors) arithmetic + V5 validation, symmetric/sum-free/zero-free + triangle-free brute re-checks, Green–Ruzsa sizes (Z_31→10, Z_53→18), nauty-canonical dedup (WL-hash forbidden), sha256 stage-independent subseeds + byte-identical descriptor rebuild.
- Task 3: the POOL-1/POOL-2 schema/store/screen/determinism/frontier/P1 contract — g-screen record schema, five append-only store invariants, THE certificate-honesty gate, deterministic-verdict driver (forces the 08-02 det-budget field), ILP-frontier measurement, P1 TFP sweep + large-n existence-only showpieces.
- Full contract collects clean (57 tests) and is RED (48 fail on missing modules under `-m "not slow"`, exit 1); existing suite unchanged (273 passed, no regressions); frozen corpus + trust root + `generators/cayley.py` byte-untouched.

## Task Commits

1. **Task 1: Package skeleton + additive paths + Γ/record fixtures** - `a13a0ad` (feat) — pre-existing, verified present
2. **Task 2: RED contract — group/generate/structured/dedup/rng_v2** - `09d2a55` (test)
3. **Task 3: RED contract — schema/store/screen(honesty)/determinism/frontier/p1** - `f1b4f93` (test)

## Files Created/Modified
- `tests/pool/sumfree/test_group.py` - Abelian(factors) order/elements/add/neg + V5 input validation (bool/oversized n≤500 cap)
- `tests/pool/sumfree/test_generate.py` - symmetric+sum-free+zero-free brute re-check, triangle-free Cayley adjacency, hand-built C_5
- `tests/pool/sumfree/test_structured.py` - Green–Ruzsa sizes keyed on |Γ| mod 3, maximality re-check
- `tests/pool/sumfree/test_dedup.py` - nauty-canonical isomorph collapse; WL-hash/graph_hash forbidden
- `tests/pool/sumfree/test_rng_v2.py` - sha256 stage-independent subseed + byte-identical descriptor rebuild
- `tests/pool/sumfree/test_schema.py` - build_gscreen_record json round-trip, provenance/sha256/computed-g, RESISTANT→null had/g
- `tests/pool/sumfree/test_store.py` - five append-only invariants vs SUMFREE_CORPUS (tmp_path only), two distinct hand-verified g≤0 records
- `tests/pool/sumfree/test_screen.py` - compute_g, verifier fails closed on 'counterexample'/'had(G) <', honest literal, MISS→RESISTANT g=None
- `tests/pool/sumfree/test_determinism.py` (slow) - identical verdict across two num_workers=1 deterministic-budget runs
- `tests/pool/sumfree/test_frontier.py` - measure_ilp_frontier per-n had_2-optimality-proved flag, monotone downward
- `tests/pool/sumfree/test_p1_sweep.py` (slow) - n=31/32 TFP exact had_2 verdicts, seed-deterministic
- `tests/pool/sumfree/test_showpiece.py` (slow) - large-n existence-only: HIT trust-root-verified, MISS RESISTANT never a result

## Decisions Made
- **POOL-1/POOL-2 NOT marked complete.** These requirements are shared across the whole phase (plans 08-01..08-07). This plan delivers only the RED falsification contract; the requirements are satisfied when the implementation waves make the contract GREEN. Marking them complete on the scaffold would violate the program's own reporting discipline ("nothing counts as found until the verifier passes"). `requirements-completed: []`.
- **Two honesty tests are intentionally green.** `test_honest_positive_g_statement_has_required_literals` and `test_honest_canary_scans_clean_of_radioactive_strings` validate the committed CANARY fixture is radioactive-clean — an always-green regression on a stored artifact. The fail-closed verifier honesty guards (`test_verifier_fails_closed_on_*`) import the not-yet-existent verifier and remain RED. This is faithful to the plan's "certificate-honesty gate is executable" requirement while keeping 48/50 non-slow tests RED.

## Deviations from Plan
None - plan executed exactly as written. Task 2's five test files were found already authored (untracked, from the interrupted session); each was read and verified against the Task 2 contract before committing — they matched precisely, so no rework was needed. All Task 3 files were authored here.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. (Heavy `-m slow` sweeps run later on the remote box per docs/COMPUTE.md; this plan is authoring-only on the Mac.)

## Next Phase Readiness
- The full POOL-1/POOL-2 interface surface is now pinned RED and collectable — Waves 2–5 (plans 08-02..08-07) have a concrete falsification target.
- `test_determinism.py` explicitly drives the 08-02 deterministic-budget field (`det_budget` / `max_deterministic_time`).
- Module names the implementation must honor: `alpha2.pool.sumfree.{group,generate,dedup,rng,schema,store,verifier,screen,adjudicate,frontier,p1}`.
- No blockers.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Completed: 2026-07-23*
