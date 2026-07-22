---
phase: 01-pinned-environment-verbatim-port
plan: 02
subsystem: testing
tags: [golden-fingerprint, sha256, byte-exact-reproduction, chi-no-estimate, ast-static-guard, edmonds-blossom, seed-137, determinism]

# Dependency graph
requires:
  - phase: 01-01
    provides: "pinned uv CPython 3.12.13 env; src/alpha2 verbatim Appendix C toolkit (generators/invariants/search/verify); single-RNG contract v1; test_invariants GREEN"
provides:
  - Frozen golden manifest data/manifests/fingerprint.json (tfp:n31:s1 -> m=131,nu=15,chi=16,h_edges_sha256=3c953d90…41e2; tfp:n31:s137 -> m=177,h_edges_sha256=c3e7540f…cb13), each gated on doc-derived Appendix D invariants before freeze
  - Two-tier reproduction fingerprint suite: test_golden_hash + test_stored_model_reverifies (hard/version-proof) and test_heuristic_reproduces + test_heuristic_matches_d2_exact_pinned_env (soft/pinned-interpreter)
  - CHI-01 mechanism-based static guard (AST, not prose grep) proving n − matching_number is the sole chi path and networkx is confined to max_weight_matching(maxcardinality=True)
  - seed-137 H-only fingerprint pre-locked for the Phase-4 regression (|E(H)|=177, no model/ILP)
  - ENV-01 interpreter/networkx pin tripwire (test_env_smoke)
affects: [02-trust-root-corpus-schema, 03-corpus-reproduction-ci, golden-fingerprint, chi-no-estimate-guard, exact-backend, seed-137-regression]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gated golden freeze: doc-derived invariants (131/15/16/tf/maxTF; 177) asserted FIRST, only then is the self-generated sha256 trusted and frozen — a porting bug can never self-certify"
    - "Two-tier fingerprint: version-proof witness re-verification (stored D.2 model vs freshly regenerated H) separated from pinned-interpreter exact reproduction (single-RNG contract v1)"
    - "Mechanism-based static guard via AST Call/Import inspection (not source-text grep) so comment/docstring prose can neither trip nor mask the CHI-01 gate"

key-files:
  created:
    - data/manifests/fingerprint.json
    - tests/test_chi_no_estimate.py
  modified:
    - tests/test_fingerprint.py

key-decisions:
  - "Golden manifest is the single source of the frozen hash; tests load h_edges_sha256 FROM the manifest (never a duplicated literal) so the manifest is the authority under test"
  - "test_heuristic_matches_d2_exact_pinned_env uses the single-RNG contract v1 (one random.Random(1) feeds triangle_free_process THEN solve) — the plan's literal fresh-Random(1) snippet does NOT reproduce D.2 exactly; the plan's own 'under the single-RNG contract' instruction and Plan 01's established pattern govern"
  - "CHI-01 guard implemented as an AST scan over actual Call/Import nodes (mechanism), verified non-vacuous by an injected greedy_color that trips it"

patterns-established:
  - "Gated golden freeze (invariant gate before hash trust) — reused per instance in Phase 3's full-corpus manifest"
  - "Two-tier fingerprint (hard witness re-verify vs soft pinned-env replay) — the reproduction-contract shape Phase 2/3 encode corpus-wide"
  - "AST mechanism guards over prose grep — the template for future control-flow invariants (e.g. verifier import-boundary, python -O canary)"

requirements-completed: [ENV-03, ENV-02, CHI-01, ENV-01]

# Metrics
duration: 13min
completed: 2026-07-22
---

# Phase 01 Plan 02: Golden Fingerprint Freeze, Stored-Model Re-verify & CHI-01 Guard Summary

**Byte-exact golden manifest (n=31 s=1 H_edges sha256 = 3c953d90…41e2, plus seed-137 |E(H)|=177) frozen only after the Appendix-D invariants passed, the stored D.2 K16 model re-verified against a freshly regenerated H, the heuristic replayed to D.2 exactly under the single-RNG contract, and an AST mechanism guard proving χ is only ever n − ν — full `uv run pytest -q` GREEN (8 tests).**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-07-22T01:02:00Z (approx)
- **Completed:** 2026-07-22T01:15:08Z
- **Tasks:** 2
- **Files modified:** 3 (across 2 task commits + 1 docs commit)

## Accomplishments
- Froze `data/manifests/fingerprint.json` gated on the doc: regenerated H_edges, asserted Appendix-D invariants (m=131/ν=15/χ=16/tf/maxTF for s1; m=177 for s137) FIRST, and only then trusted + froze the canonical sha256. The n=31 s=1 hash equals the pre-validated golden `3c953d90…41e2`; seed-137's H-only hash is `c3e7540f…cb13`.
- Two-tier fingerprint suite: `test_golden_hash` (regenerated sha256 == manifest, byte-exact tripwire, ENV-03), `test_stored_model_reverifies` (Appendix D.2 K16 model re-verifies against fresh H with no search replay — the version-proof witness, ENV-02), `test_heuristic_reproduces` (CI-safe "any verifying model"), and the distinct `test_heuristic_matches_d2_exact_pinned_env` (reproduces D.2 byte-exactly on CPython 3.12.13).
- CHI-01 static guard `tests/test_chi_no_estimate.py` implemented as an **AST mechanism** guard (not a prose grep): no chromatic-estimate Call/Import anywhere in `src/alpha2`, networkx surface confined to a matching allow-list, and a positive assertion that `invariants/matching.py` is the sole chi path via `max_weight_matching(maxcardinality=True)`. Verified non-vacuous — an injected `greedy_color` trips it.
- seed-137 H-only fingerprint pre-locked for the Phase-4 regression (`|E(H)|=177`, no model/ILP — CBC is Phase 4). ENV-01 pin tripwire (`test_env_smoke`) asserts CPython 3.12.13 / networkx 3.6.1.
- Full suite `uv run pytest -q` GREEN (8 passed).

## Task Commits

Each task was committed atomically:

1. **Task 1: Freeze golden manifest + byte-exact hash + stored-model re-verify + heuristic replay** - `907da79` (feat)
2. **Task 2: CHI-01 mechanism static guard + seed-137 H-only fingerprint + env smoke** - `4f93e63` (feat)

**Plan metadata:** final docs commit (SUMMARY + STATE + ROADMAP) — see below.

## Files Created/Modified
- `data/manifests/fingerprint.json` - frozen golden fixture: tfp:n31:s1 (m/nu/chi/h_edges_sha256) + tfp:n31:s137 (m/h_edges_sha256), gated on doc invariants
- `tests/test_fingerprint.py` - extended with test_golden_hash, test_stored_model_reverifies, test_heuristic_reproduces, test_heuristic_matches_d2_exact_pinned_env, test_seed137_h_only, test_env_smoke (+ existing test_invariants); shared canonical_h_edges_sha256 helper + manifest loader
- `tests/test_chi_no_estimate.py` - AST mechanism guard for CHI-01 (no estimate call/import; networkx confined; positive matching-path assertion)

## Decisions Made
- **Manifest is the authority under test.** Tests load `h_edges_sha256` from `data/manifests/fingerprint.json`; the golden value is never duplicated as a second literal, so a manifest edit is what the byte-exact tripwire actually guards.
- **Single-RNG contract for the exact-match tier.** `test_heuristic_matches_d2_exact_pinned_env` feeds one `random.Random(1)` into `triangle_free_process` THEN `solve` (contract v1). See Deviations — this is the only path that reproduces D.2 exactly.
- **AST over grep for CHI-01.** The guard inspects real Call/Import nodes, so Wave 1's docstring rewording (and any future prose) can neither create false positives nor mask a real estimate call.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Exact-match heuristic tier requires the single-RNG contract, not a fresh Random(1)**
- **Found during:** Task 1 (heuristic replay)
- **Issue:** The plan's literal action text says `solve(adj, 31, 16, random.Random(1))` for the pinned-env tier, but a fresh `Random(1)` for `solve` does NOT reproduce the Appendix D.2 model exactly (verified: setwise-unequal to D.2). Asserting exact D.2 equality with a fresh RNG would make `test_heuristic_matches_d2_exact_pinned_env` permanently RED.
- **Fix:** Used the single-RNG contract v1 established in Plan 01 (one `random.Random(1)` feeds `triangle_free_process` THEN `solve`, in that order) — which reproduces D.2 byte-exactly (`[list(s) for s in sets] == D2_MODEL`). This matches the plan's own "under the single-RNG contract" instruction; the literal fresh-Random snippet was superseded. `test_heuristic_reproduces` (CI-safe tier) also uses the single-RNG contract but only asserts a verifying model.
- **Files modified:** tests/test_fingerprint.py
- **Verification:** `test_heuristic_matches_d2_exact_pinned_env` GREEN; empirically confirmed single-RNG == D.2 exactly while fresh-RNG != D.2.
- **Committed in:** `907da79` (Task 1 commit)

**2. [Rule 2 - Missing Critical] CHI-01 guard made mechanism-based (AST) rather than prose grep**
- **Found during:** Task 2 (CHI-01 guard)
- **Issue:** The plan action describes a token grep with comment-line stripping. A pure word-grep is weak/circular here because Wave 1 already reworded docstrings to remove trigger tokens, and the verbatim source comment `# ---------- exact chromatic number ... ----------` legitimately contains "chromatic". A grep guard would either false-positive on that comment or be trivially satisfiable.
- **Fix:** Implemented the guard over the AST (Call/Import nodes only, comments and docstrings inherently excluded): forbids any chromatic-estimate Call target or coloring/approximation Import, confines the networkx API surface to a matching allow-list, and positively asserts `max_weight_matching(maxcardinality=True)` is the sole chi path in `invariants/matching.py`. This tests the real invariant, as directed by the plan's critical-reminder.
- **Files modified:** tests/test_chi_no_estimate.py
- **Verification:** Guard GREEN on clean tree; injected `nx.greedy_color(...)` into matching.py trips it (FAILED as expected), then matching.py restored byte-identical (`git diff` empty).
- **Committed in:** `4f93e63` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing-critical). Both are hardening the tests to actually hold the intended invariants; zero changes to any `src/alpha2` algorithm body. No scope creep.
**Impact on plan:** All acceptance criteria met exactly; the deviations make the exact-match tier and the CHI-01 guard real rather than vacuous.

## Issues Encountered
- Pre-existing uncommitted change to `.planning/config.json` (not produced by this plan) was left untouched and excluded from all task commits (scope boundary).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 complete (2/2 plans). The reproduction contract is now a concrete, self-defending assertion: gated golden freeze + version-proof witness re-verification + pinned-env exact replay + AST-enforced single chi path.
- Phase 2 (Trust Root & Corpus Schema) can build the stdlib-only verifier against this fingerprint harness; the seed-137 H-only entry is pre-locked for the Phase-4 CBC regression.
- No blockers introduced. pulp/ortools/pynauty remain locked-but-unexercised (only networkx runs in the fingerprint path).

---
*Phase: 01-pinned-environment-verbatim-port*
*Completed: 2026-07-22*

## Self-Check: PASSED
- Files exist: data/manifests/fingerprint.json, tests/test_chi_no_estimate.py, tests/test_fingerprint.py (all present on disk).
- Commits exist: 907da79 (Task 1), 4f93e63 (Task 2) in git history.
- Full suite `uv run pytest -q` GREEN (8 passed).
