---
phase: 03-corpus-reproduction-ci-first-blood
plan: 01
subsystem: testing
tags: [pytest, corpus, verifier, schema-v1, tutte-berge, reproducibility, tdd]

# Dependency graph
requires:
  - phase: 01-environment-and-toolkit-port
    provides: "generators/tfp (deterministic RNG-injected generator), invariants/matching + witness, paths.CORPUS, fingerprint test + manifest"
  - phase: 02-trust-root-and-schema
    provides: "corpus/schema.build_record (schema-v1 + frozen sha256), corpus/store.append_certificate (verify-at-append + hash-chain + atomic write), corpus/verifier.verify_certificate (raise-based trust root)"
provides:
  - "Finalized repro/baseline.py emitting schema-v1 certificates through the store's verify-at-append trust root (no ad-hoc dict, no asserts in the verified path)"
  - "tests/test_corpus_r1.py — R1 corpus-validity test that re-verifies every stored record from JSON alone via raise-based verify_certificate"
  - "Regenerated 14-record TFP baseline+showpiece corpus slice (data/corpus/hadwiger_alpha2_certificates.json), git-committed as the immutability anchor"
  - "pytest pinned to 8.3.4 + `slow` marker registered (test-infra pins for the CI freeze)"
affects: [03-02 cayley/sweep drivers, 03-03 full-296 freeze + strict family counts, 03-04 CI workflow + python -O job]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Driver emission tail = extract_witness -> schema.build_record -> store.append_certificate (compose the trust root; never hand-roll verify/hash/store)"
    - "Single-RNG contract v1: one random.Random(seed) feeds triangle_free_process THEN solve, in that order (byte-reproduction anchor)"
    - "Trust decision routes only through raise-based verify_certificate; asserts wrap only -O-independent post-conditions"

key-files:
  created:
    - "tests/test_corpus_r1.py"
    - "data/corpus/hadwiger_alpha2_certificates.json"
  modified:
    - "src/alpha2/repro/baseline.py"
    - "pyproject.toml"
    - "uv.lock"
    - ".gitignore"

key-decisions:
  - "Removed data/corpus/*.json blanket ignore for the canonical corpus via a negation so the regenerated corpus is the git-committed immutability anchor (ENV-04)"
  - "Pinned pytest to ==8.3.4 (matches CLAUDE.md 8.x stack; stops the newer-Python canary drifting the runner) — downgraded from the 9.1.1 the env resolved; full suite stays green"
  - "Corpus rebuilt from EMPTY on every driver run (the append-only store refuses a reorder, so re-runs must not double-append)"

patterns-established:
  - "Pattern: schema-v1 driver emission via the trust root (generator -> witness -> build_record -> append_certificate) — the template every later Phase-3 driver copies"
  - "Pattern: R1-style corpus-validity test — verify_certificate over every stored record from JSON alone, assert-free trust decision (python -O safe)"

requirements-completed: [ENV-04]

# Metrics
duration: ~20min
completed: 2026-07-21
---

# Phase 3 Plan 01: Corpus Pipeline First Blood Summary

**Finalized `repro/baseline.py` to emit witness-complete schema-v1 certificates through the append-only store's verify-at-append trust root, regenerated a 14-record TFP baseline+showpiece corpus, and landed the R1 test that re-verifies every stored record from JSON alone — with the (31, seed=1) model byte-equal to Appendix D.2.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-07-21 (execution wave 1)
- **Completed:** 2026-07-21
- **Tasks:** 2 (both TDD)
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments
- Wired the thinnest real vertical slice of Phase 3 end-to-end: `triangle_free_process` -> `matching_number`/`extract_witness` -> `schema.build_record` -> `store.append_certificate`, replacing the old ad-hoc pre-schema dict + `json.dump` tail.
- Landed `tests/test_corpus_r1.py` (RED against the empty corpus, GREEN after regeneration): every stored record re-verifies from JSON via raise-based `verify_certificate`; slice ≥ 14; ≥ 1 TFP family; (31,1) stored model == Appendix D.2 literal.
- Regenerated the 14-record TFP slice (12 baseline + showpieces n=301, n=501), all `schema_version==1`, and committed it as the git immutability anchor.
- Pinned pytest to 8.3.4 and registered the `slow` marker; the full suite (49 tests, incl. Phase-1/2's 48) stays green and the `python -O` assert-stripping canary passes over R1.
- Trust primitives (`verifier.py`, `schema.py`, `store.py`) byte-unchanged — this was a composition-only plan, no reimplementation of verification/hashing/storage.

## Task Commits

Each task was committed atomically (both TDD):

1. **Task 1: R1 corpus-validity test (RED) + pytest test-infra pins** - `d2b3449` (test)
2. **Task 2: Finalize baseline.py to schema-v1 store path; regenerate 14-record slice (GREEN)** - `38d7081` (feat)

_TDD RED/GREEN gate: `test(...)` d2b3449 precedes `feat(...)` 38d7081 in git log; no REFACTOR commit was needed._

## Files Created/Modified
- `tests/test_corpus_r1.py` (created) - R1 corpus-validity: re-verifies every stored record from JSON alone via `verify_certificate`; asserts slice ≥ 14, ≥ 1 TFP, and (31,1) model == D.2. Embeds `D2_MODEL` as a literal (no cross-test import).
- `data/corpus/hadwiger_alpha2_certificates.json` (created) - Regenerated 14-record schema-v1 TFP baseline+showpiece slice; the git-committed immutability anchor.
- `src/alpha2/repro/baseline.py` (modified) - Finalized `run_instance` to emit schema-v1 via `store.append_certificate`; removed `assert tf`, dead `verify_model` import/usage, and unused `json`/`is_*_tf` imports; added showpieces (301,13),(501,14); rebuilds corpus from empty.
- `pyproject.toml` (modified) - Pinned dev `pytest==8.3.4`; registered `markers = ["slow: release/nightly replay gate"]`.
- `uv.lock` (modified) - Re-locked to the pytest 8.3.4 pin.
- `.gitignore` (modified) - Negation for the canonical corpus file so ENV-04's regenerated corpus is tracked; other generated corpus JSON stays ignored.

## Decisions Made
- **Corpus is a committed artifact, not generated-and-ignored.** The `data/corpus/*.json` blanket ignore (a Phase-1/2 default, when tests wrote to `tmp_path` and the real corpus was empty) directly conflicted with ENV-04's requirement that the regenerated corpus be re-verifiable "from stored JSON alone" and serve as the git immutability anchor (`store.py` docstring). Added a `!` negation for the one canonical file.
- **pytest 8.3.4 pin over the resolved 9.1.1.** Matches CLAUDE.md's stated 8.x stack and prevents the newer-Python canary silently drifting the runner (Assumption A6). Confirmed the downgrade leaves the existing suite green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `.gitignore` blocked the required ENV-04 corpus artifact**
- **Found during:** Task 2 (regenerate + commit the 14-record slice)
- **Issue:** `git add` of `data/corpus/hadwiger_alpha2_certificates.json` was refused — line 4 `data/corpus/*.json` ignored it. The plan's artifact spec and ENV-04 require the regenerated corpus committed as the immutability anchor; without it the plan's core deliverable could not be persisted.
- **Fix:** Added `!data/corpus/hadwiger_alpha2_certificates.json` (with an explanatory comment) after the blanket rule, keeping other generated/tmp corpus JSON ignored.
- **Files modified:** `.gitignore`
- **Verification:** `git ls-files data/corpus/hadwiger_alpha2_certificates.json` now lists the file; it is committed in `38d7081`.
- **Committed in:** `38d7081` (part of the Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix was required to deliver the plan's central artifact (the committed corpus). No scope creep — a single narrowly-scoped `.gitignore` negation.

## Issues Encountered
- **`uv` not on PATH; worktree had no `.venv`.** Resolved by prepending `$HOME/.local/bin` (a working `uv 0.11.30` symlink) and running `uv sync --frozen --extra dev` to materialize the worktree venv from the lockfile. No lock drift.
- **Showpiece n=501 latency (slow-freeze escape hatch, W5/Pitfall 5).** The 14-instance regeneration (incl. n=301/501 witness extraction + O(N²) verify-at-append) was run as a background job to avoid tool-call truncation; it completed in well under a minute (n=501 ≈ 6s). No pipeline weakening; verify-at-append left intact.

## Threat Flags
None — no new security-relevant surface. The plan's threat register (T-3-01 tamper, T-3-02 RNG drift, T-3-03 -O elevation) is mitigated as designed: every write goes through `store.append_certificate`; the (31,1)==D.2 byte-equality tripwire guards RNG drift; `baseline.py` is assert-free (`grep -c 'assert ' == 0`) and R1 routes trust through raise-based `verify_certificate`, both confirmed green under `python -O`.

## Known Stubs
None — no placeholder data or unwired components. The 14 records are fully verified schema-v1 certificates. The strict (284, 12)/296 family-count assertion is intentionally deferred to Plan 03 (documented in the R1 test's scope note and the plan's task behavior), after the full freeze; a `family_counts` helper is already wired for it.

## Next Phase Readiness
- The schema-v1 driver emission path is proven on 14 real instances — Plan 02 (sweep, cayley_run, seed137) copies this exact `run_instance` template; Plan 03 scales to the full 296 and adds the strict family-count + manifest assertions.
- pytest is pinned and the `slow` marker exists for Plan 03's R3 replay gate.
- No blockers. Note for the orchestrator: STATE.md/ROADMAP.md were intentionally NOT modified (worktree mode); this SUMMARY is committed on the worktree branch.

## TDD Gate Compliance
Plan tasks are `tdd="true"`. Gate sequence satisfied in git log: `test(03-01)` (d2b3449, RED — R1 failed on the empty corpus) precedes `feat(03-01)` (38d7081, GREEN — R1 passes over the 14-record corpus). No unexpected RED-phase pass occurred (the empty-corpus `FileNotFoundError` was the expected RED). REFACTOR not required.

## Self-Check: PASSED
- Files verified present: `tests/test_corpus_r1.py`, `src/alpha2/repro/baseline.py`, `data/corpus/hadwiger_alpha2_certificates.json`, `pyproject.toml`.
- Commits verified in git log: `d2b3449` (Task 1), `38d7081` (Task 2).
- Corpus verified tracked by git (`git ls-files`).

---
*Phase: 03-corpus-reproduction-ci-first-blood*
*Completed: 2026-07-21*
