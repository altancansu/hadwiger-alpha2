---
phase: 01-pinned-environment-verbatim-port
plan: 01
subsystem: infra
tags: [uv, cpython-3.12.13, networkx, pulp, ortools, packaging, determinism, triangle-free-process, edmonds-blossom]

# Dependency graph
requires: []
provides:
  - Pinned uv-managed CPython 3.12.13 environment reproducing from a committed uv.lock (networkx 3.6.1 / pulp 3.3.2 / ortools 9.15.6755; pynauty 2.8.8.1 as optional [nauty] extra)
  - src/alpha2 src-layout package holding the Appendix C toolkit ported byte-verbatim (generators/invariants/search/verify) plus a thin repro entry
  - paths.py single-source repo-relative CORPUS path (all /mnt sandbox paths removed)
  - The invariant fingerprint test (n=31 seed=1 -> m=131, nu=15, chi=16) GREEN on the pinned interpreter
  - chi(G) computed ONLY as n - nu via Edmonds blossom; networkx confined to invariants/matching.py
affects: [02-trust-root-corpus-schema, 03-corpus-reproduction-ci, golden-fingerprint, chi-no-estimate-guard, exact-backend]

# Tech tracking
tech-stack:
  added: [uv 0.11.30, CPython 3.12.13, networkx==3.6.1, pulp==3.3.2, ortools==9.15.6755, pynauty==2.8.8.1 (extra), pytest, ruff, hatchling]
  patterns:
    - "Library / thin-entry cut: side-effect-free algorithm modules + a single repro/baseline driver owning I/O and the instance list"
    - "Single source of paths (paths.py); no absolute path may live anywhere else"
    - "Verifier trust-root import boundary: verify/model.py carries its own byte-identical is_conflict and imports nothing from search"
    - "Single-RNG contract v1: one random.Random(seed) feeds triangle_free_process THEN solve, in that order"
    - "Determinism-sensitive modules (generators/tfp.py, search/heuristic.py) excluded from ruff auto-fix"

key-files:
  created:
    - pyproject.toml
    - .python-version
    - uv.lock
    - .gitignore
    - src/alpha2/paths.py
    - src/alpha2/generators/tfp.py
    - src/alpha2/invariants/matching.py
    - src/alpha2/search/heuristic.py
    - src/alpha2/verify/model.py
    - src/alpha2/repro/baseline.py
    - tests/test_fingerprint.py
  modified: []

key-decisions:
  - "requires-python pinned as >=3.12,<3.13 in pyproject with exact patch (3.12.13) anchored via .python-version (research Assumption A3 granularity)"
  - "pynauty kept as an optional [nauty] extra so a compiler-less clean `uv sync` succeeds; nauty binary documented in CLAUDE.md, not in uv.lock (research A1/A2)"
  - "dev tooling (pytest, ruff) declared under [project.optional-dependencies] and installed with `uv sync --extra dev` (NOT --group dev)"
  - "hatchling chosen as the src-layout build backend (packages = [src/alpha2])"

patterns-established:
  - "Byte-verbatim port: algorithm bodies copied character-for-character; only module location, cross-module imports, and the /mnt->paths.CORPUS output path changed"
  - "Fingerprint invariants sourced from Appendix D (the doc), asserted independently so a porting bug cannot self-certify"

requirements-completed: [ENV-01, ENV-02, CHI-01]

# Metrics
duration: 5min
completed: 2026-07-22
---

# Phase 01 Plan 01: Pinned Environment & Verbatim Port Summary

**uv-pinned CPython 3.12.13 stack (networkx 3.6.1 / pulp 3.3.2 / ortools 9.15.6755 from a committed uv.lock) plus the Appendix C toolkit ported byte-verbatim into src/alpha2 — n=31 seed=1 regenerates |E(H)|=131, ν=15, χ=16 and the invariant fingerprint is GREEN.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-22T01:02:20Z
- **Completed:** 2026-07-22T01:06:48Z
- **Tasks:** 3
- **Files modified:** 20 (tracked, across 3 commits)

## Accomplishments
- Pinned uv project: `.python-version = 3.12.13`, `requires-python = ">=3.12,<3.13"`, committed `uv.lock` pinning networkx 3.6.1 / pulp 3.3.2 / ortools 9.15.6755 (+ pynauty 2.8.8.1 under the optional `nauty` extra). Clean `uv sync` resolves 3.12.13, never system 3.9.6.
- Appendix C toolkit relocated byte-verbatim into a src-layout package: `generators/tfp.py` (RandomSet + triangle-free process + tf/maxTF checks), `invariants/matching.py` (ν→χ), `search/heuristic.py` (profile heuristic), `verify/model.py` (assert-based verifier with its own is_conflict), `repro/baseline.py` (thin driver).
- χ(G) computed ONLY as n − ν via `nx.max_weight_matching(maxcardinality=True)`; networkx confined to `invariants/matching.py`; no coloring/estimate path anywhere in `src/`.
- `tests/test_fingerprint.py::test_invariants` GREEN on the pinned interpreter (131/15/16/tf/maxTF). Bonus: the self-generated `H_edges` SHA-256 matches the research-frozen golden `3c953d90…41e2` (byte-exact reproduction; golden freeze itself is Plan 02).
- Full baseline driver runs end-to-end: all 12 instances "K_chi MODEL FOUND + VERIFIED", writing `data/corpus/hadwiger_alpha2_certificates.json` (repo-relative). n=31 seed=1 record has verified=True, chi_G=16, matching_number_H=15, len(H_edges)=131.

## Task Commits

Each task was committed atomically:

1. **Task 1: uv scaffold + src package skeleton + failing invariant fingerprint** - `7cb4707` (chore)
2. **Task 2: Verbatim port — generation + matching core** - `21d1eb9` (feat)
3. **Task 3: Verbatim port — search + verify + thin entry; fingerprint GREEN** - `ac226e1` (feat)

**Plan metadata:** (final docs commit — see below)

## Files Created/Modified
- `pyproject.toml` - uv project: name=alpha2, core deps + [nauty]/[dev] extras, hatchling src-layout, pytest config, ruff excludes for determinism-sensitive modules
- `.python-version` - `3.12.13` exact-patch interpreter anchor
- `uv.lock` - committed lockfile pinning networkx/pulp/ortools (+ pynauty extra)
- `.gitignore` - `.venv/`, `__pycache__/`, `data/corpus/*.json`, `*.pyc`
- `src/alpha2/paths.py` - single source of the repo-relative CORPUS path (+ ensure_parent)
- `src/alpha2/generators/tfp.py` - RandomSet, triangle_free_process, is_triangle_free, is_edge_maximal_tf (verbatim)
- `src/alpha2/invariants/matching.py` - matching_number → ν; the sole χ = n − ν path (verbatim)
- `src/alpha2/search/heuristic.py` - is_conflict, full/update_conflicts, initial_state, assignments, valid_groups, cand_energy, solve (verbatim)
- `src/alpha2/verify/model.py` - verify_model (assert-based) + own private is_conflict copy (verbatim)
- `src/alpha2/repro/baseline.py` - run_instance + main() driver; single-RNG contract v1; output → paths.CORPUS
- `tests/test_fingerprint.py` - ENV-03 invariant fingerprint (131/15/16/tf/maxTF), doc-derived
- `data/corpus/.gitkeep`, `data/manifests/.gitkeep` - empty data dirs
- package `__init__.py` files (alpha2 + 5 subpackages + tests)

## Decisions Made
- Interpreter pin granularity: `>=3.12,<3.13` in pyproject + exact `3.12.13` in `.python-version` (research A3; both reproduce, this keeps patch flexibility in pyproject while `.python-version` anchors the exact fetch).
- pynauty stays an optional `nauty` extra (research A1/A2); default `uv sync` installs core only so a compiler-less checkout still passes the fingerprint. nauty 2.9.3 binary is documented in CLAUDE.md, not lockable.
- dev tools installed via `uv sync --extra dev` because `dev` is an `[project.optional-dependencies]` extra, not a PEP 735 `[dependency-groups]` table.
- hatchling as the build backend with `packages = ["src/alpha2"]`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Docstring wording hardened so CHI-01 / import-boundary static guards stay clean**
- **Found during:** Task 3 (search + verify + entry)
- **Issue:** My added docstrings in `invariants/matching.py` and `verify/model.py` contained the bare words "coloring"/"greedy" and the phrase "import from alpha2.search". The plan's own acceptance grep (`import ...search`) and the research-planned CHI-01 static guard (grep `coloring|greedy_color` in `src/`) would flag these descriptive lines as false positives, undermining the guards.
- **Fix:** Reworded the two docstrings to describe the invariants positively ("chi is computed exactly and is never estimated or approximated"; "must never pull anything out of alpha2.search") without the trigger tokens. No code changed; the verbatim source comment `# ---------- exact chromatic number ... ----------` was preserved as-is (it does not match a `coloring|greedy_color` guard).
- **Files modified:** src/alpha2/invariants/matching.py, src/alpha2/verify/model.py
- **Verification:** `grep -RnE 'coloring|greedy_color' src/` → no hits; `grep -Eq 'from alpha2.search|import .*search' src/alpha2/verify/model.py` → no hits; fingerprint still GREEN.
- **Committed in:** `ac226e1` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 missing-critical / guard-hygiene).
**Impact on plan:** Doc-only wording; zero effect on algorithm bodies or determinism. No scope creep. The two apparent grep "failures" during verification were confirmed to be docstring-prose false positives (verify/model.py has zero actual import statements; the "chromatic" hits are all comments describing what is NOT done) and were resolved by the reword.

## Issues Encountered
- `uv` was not on PATH (installed to the session scratchpad during research). Resolved by symlinking `~/.local/bin/uv` and prefixing `PATH` per command. The `uv python install 3.12.13` step emitted a harmless warning about an unmanaged `python3.12` shim already existing; the 3.12.13 toolchain itself installed correctly and `uv sync` selected it.
- `data/corpus/hadwiger_alpha2_certificates.json` is produced by the baseline run but is `.gitignore`d (regenerated artifact; the golden manifest/freeze is Plan 02 scope), so it is intentionally NOT committed.

## User Setup Required
None - no external service configuration required. (nauty `geng` is not a Phase-1 gate; `brew install nauty` is documented for later phases only.)

## Next Phase Readiness
- Walking Skeleton spine complete: pinned env + verbatim toolkit + GREEN fingerprint.
- Ready for Plan 01-02 (golden byte-exact fingerprint freeze, stored-model re-verify, CHI-01 no-estimate guard test). The golden `H_edges` SHA-256 is already pre-validated (`3c953d90…41e2`).
- No blockers introduced. pulp/ortools/pynauty are locked-but-unexercised as intended (only networkx runs in the fingerprint path).

---
*Phase: 01-pinned-environment-verbatim-port*
*Completed: 2026-07-22*

## Self-Check: PASSED
All 11 created files present on disk; all 3 task commits (7cb4707, 21d1eb9, ac226e1) exist in git history.
