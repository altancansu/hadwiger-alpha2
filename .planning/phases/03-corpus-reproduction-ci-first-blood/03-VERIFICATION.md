---
phase: 03-corpus-reproduction-ci-first-blood
verified: 2026-07-22T04:28:53Z
status: passed
score: 13/13 must-haves verified
overrides_applied: 0
---

# Phase 3: Corpus Reproduction & CI (First Blood) Verification Report

**Phase Goal:** The full 296-instance corpus regenerates and independently re-verifies, and that
reproduction runs as the permanent test suite — the trust anchor and regression harness for
everything downstream.
**Verified:** 2026-07-22T04:28:53Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Corpus has exactly 296 records = 284 triangle_free_process_complement + 12 cayley_maximal_sumfree_Zp, all re-verifiable from stored JSON alone (R1) | ✓ VERIFIED | `data/corpus/hadwiger_alpha2_certificates.json` loaded directly: `len=296`, `{'triangle_free_process_complement': 284, 'cayley_maximal_sumfree_Zp': 12}`. `uv run --frozen pytest tests/test_corpus_r1.py -q` → `1 passed`. R1 hard-gates the exact count and calls raise-based `verify_certificate` on every record (no `assert` governs the verification decision itself — confirmed by reading `tests/test_corpus_r1.py`). |
| 2 | Determinism panel R2 passes; R3 replay passes under the pinned interpreter | ✓ VERIFIED | `uv run --extra dev --frozen pytest -q -m slow` → `3 passed, 51 deselected` (2 R3 tests + 1 R2 slow full-296 panel). Also ran non-slow R2 legs as part of full suite (3 passed total in `test_corpus_r2.py`). Interpreter confirmed `3.12.13` (pinned) via `python -c "import sys; print(sys.version)"`, so R3's strict byte-equality branch is exercised, not the downgraded branch. |
| 3 | Golden manifest `data/manifests/corpus-v1.manifest.json` frozen with 296 entries via `schema.h_edges_sha256` | ✓ VERIFIED | `json.load` on the manifest: `len=296`; `tfp:n31:s1` == `{"chi": 16, "h_edges_sha256": "3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2", "m": 131, "nu": 15}` (matches the plan's frozen golden verbatim); 12 `cayley:` keys present. `src/alpha2/corpus/manifest.py` imports and calls `schema.h_edges_sha256` — no local `hashlib.sha256` call (grep confirms). |
| 4 | seed-137 present and equal to the Appendix D.3 literal; NO solver (CBC/PuLP/CP-SAT) invoked in the Phase-3 path | ✓ VERIFIED | The unique (family=triangle_free_process_complement, n=31, seed=137) record's `model_branch_sets` is byte-identical to the Appendix D.3 16-set literal `[[2,20],[4,7],[8,18],[9,13],[12,27],[16,22],[17,24],[19,29],[26,28],[0],[1],[3],[10],[11],[21],[23]]` (`omega_G=14`). `grep -n "solve(" src/alpha2/repro/*.py` shows `solve(` only in `baseline.py`, `sweep.py`, `cayley_run.py` (the heuristic Python solver — NOT CBC/PuLP/CP-SAT); `grep -rniE "pulp|ortools|cbc" src/alpha2/repro/` matches only comment/docstring text in `seed137.py` explaining that CBC is *not* run. No `import pulp`/`import ortools` anywhere in `src/alpha2/repro/` or `src/alpha2/generators/cayley.py`. |
| 5 | `python -O` assert-stripping canary passes over R1 + verifier | ✓ VERIFIED | `uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q` → `2 passed`. `grep -c 'assert ' src/alpha2/repro/baseline.py` == 0; `cayley_run.py`/`seed137.py` also 0; `sweep.py`'s 2 asserts are accounting-only (`assert len(instances) == 269`), not verification decisions. |
| 6 | CI (`.github/workflows/ci.yml`): every-commit = R1+R2+fingerprint+`python -O`; scheduled = R3+full-296; non-blocking isolated 3.13 drift canary; SHA-pinned actions; `uv sync --locked` | ✓ VERIFIED | Read `.github/workflows/ci.yml` directly: `test` job runs `pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q` then `python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q`; `release-gate` job (guarded `schedule`/tag) runs `pytest -q -m slow` (R3) + `pytest tests/test_corpus_r2.py -q` (full R2); `canary` job has `continue-on-error: true`, runs `uv run --no-project --isolated --python 3.13 ...` (bypasses `requires-python`). Both `actions/checkout@` and `astral-sh/setup-uv@` pinned to 40-hex-char SHAs (verified via regex — `11bd71901bbe5b1630ceea73d27597364c9af683`, `d0cc045d04ccac9d8b7881df0226f9e82c39688e`). Every step uses `uv sync --locked` / `uv run --frozen`. No macOS leg. |
| 7 | Full suite green: `uv run --extra dev --frozen pytest -q` | ✓ VERIFIED | `54 passed in 1.12s` (includes `test_corpus_r1.py`, `test_corpus_r2.py` ×3, `test_corpus_r3.py` ×2, `test_fingerprint.py` ×7, plus the pre-existing Phase-1/2 suite). |
| 8 | Trust primitives (verifier.py, schema.py, store.py, tfp.py) byte-unchanged from before the phase | ✓ VERIFIED | `git log` on those 4 files shows only Phase-1/2 commits (`21d1eb9`…`8a8b9c5`). Checked every Phase-3 commit hash recorded in the four SUMMARY.md files (`d2b3449, 38d7081, ac61a8a, 03b2256, bbfbc16, 5448c9b, ee02e5c, 1ea4b59, d7c6aab, d451f9d`) via `git show --name-only` — none touch `corpus/verifier.py`, `corpus/schema.py`, `corpus/store.py`, or `generators/tfp.py`. |

**Score:** 8/8 primary truths verified (13/13 counting the itemized must_haves across the four PLAN.md frontmatters — see Required Artifacts / Key Links below).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/alpha2/repro/baseline.py` | TFP baseline+showpiece driver emitting schema-v1 via `store.append_certificate` | ✓ VERIFIED | Contains `append_certificate`; `assert ` count = 0; no `verify_model` import. |
| `tests/test_corpus_r1.py` | R1 corpus-validity test | ✓ VERIFIED | Contains `verify_certificate(`; hard `==296`/`(284,12)` gate; D2/D3 byte-equality checks; passes. |
| `data/corpus/hadwiger_alpha2_certificates.json` | Regenerated corpus | ✓ VERIFIED | 296 records, all `schema_version==1`, tracked by git (`git ls-files`). |
| `src/alpha2/generators/cayley.py` | Verbatim C.3 port | ✓ VERIFIED | Contains `can_add`, `random_maximal_symmetric_sumfree`, `cayley_adj`, `rng.shuffle`; no `ilp_had2`/`import pulp`; ruff-excluded. |
| `src/alpha2/repro/sweep.py` | 269-instance sweep driver | ✓ VERIFIED | Contains `append_certificate`; `if s != 137` exclusion; `assert len(instances) == 269`. |
| `src/alpha2/repro/seed137.py` | seed-137 driver, no solver | ✓ VERIFIED | Contains `SEED137_MODEL`; no `solve(`; method documents `had_2(G)=17`; `omega_G=14`. |
| `src/alpha2/repro/cayley_run.py` | 12-instance Cayley driver, inline H_edges | ✓ VERIFIED | Contains `cayley_adj(`; inline canonical `H_edges` comprehension present; `provenance_params(`. |
| `src/alpha2/repro/freeze.py` | Ordered-freeze entry point | ✓ VERIFIED | Empties corpus, drives baseline→sweep→cayley_run→seed137; asserts 296 + (284,12). |
| `src/alpha2/corpus/manifest.py` | 296-entry golden manifest builder | ✓ VERIFIED | Uses `schema.h_edges_sha256`; no local `hashlib.sha256`. |
| `data/manifests/corpus-v1.manifest.json` | Frozen 296-entry manifest | ✓ VERIFIED | 296 entries; golden hash for `tfp:n31:s1` matches plan's frozen value; `fingerprint.json` untouched (`git diff --quiet` clean). |
| `tests/test_corpus_r2.py` | R2 determinism panel | ✓ VERIFIED | TFP leg (doc-gated `|E(H)|==131`) + Cayley leg (structural gate) + slow full-296 panel; all pass. |
| `tests/test_corpus_r3.py` | R3 pinned-interpreter replay | ✓ VERIFIED | `@pytest.mark.slow`; replays into `tmp_path`; version-gated byte-equality; both legs pass on 3.12.13. |
| `.github/workflows/ci.yml` | GitHub Actions workflow | ✓ VERIFIED | 3 jobs (`test`, `release-gate`, `canary`); every claim in must_haves confirmed by direct file read. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `baseline.py` | `alpha2.corpus.store.append_certificate` | import + emission tail | ✓ WIRED | `grep -c 'store.append_certificate'` ≥ 1; driver runs and produces stored records. |
| `test_corpus_r1.py` | `alpha2.corpus.verifier.verify_certificate` | per-record loop | ✓ WIRED | Imported and called on every record; test passes with real corpus data. |
| `cayley_run.py` | `alpha2.generators.cayley.cayley_adj` | adjacency reconstruction | ✓ WIRED | Import present, inline `H_edges` derived from `cayley_adj` output before `build_record`. |
| `seed137.py` | `alpha2.corpus.store.append_certificate` | literal-carry emission | ✓ WIRED | Import present; record built from `SEED137_MODEL` and appended without calling `solve`. |
| `manifest.py` | `alpha2.corpus.schema.h_edges_sha256` | per-instance hash reuse | ✓ WIRED | Confirmed via grep; manifest hash for `tfp:n31:s1` matches record's own `H_edges_sha256` field. |
| `test_corpus_r2.py` | `data/manifests/corpus-v1.manifest.json` | regenerated-hash equality | ✓ WIRED | `MANIFEST_PATH` loaded, compared against regenerated digests; all 3 tests pass. |
| `ci.yml` | `test_corpus_r1/r2 + test_fingerprint + test_verifier_dash_O` | `uv run --frozen pytest` | ✓ WIRED | Exact pytest invocations present in the `test` job; local equivalents confirmed green. |

### Data-Flow Trace (Level 4)

Not applicable in the standard UI-data-flow sense (this phase has no rendering layer), but the
equivalent trust-chain trace was performed: stored JSON → `verify_certificate` (re-derives
adjacency from `H_edges`, recomputes `nu`, cross-checks `matching_M`/`tutte_berge_U`) → manifest
hash comparison (R2) → pinned-interpreter byte replay (R3). All three legs independently
regenerate from the seed/params rather than trusting cached fields, and all pass against the
same committed corpus.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Corpus loads and has exact family counts | `python3 -c "json.load(...); Counter(...)"` | `296`, `{'triangle_free_process_complement': 284, 'cayley_maximal_sumfree_Zp': 12}` | ✓ PASS |
| R1 test | `uv run --frozen pytest tests/test_corpus_r1.py -q` | `1 passed` | ✓ PASS |
| R2+R3 slow panel | `uv run --extra dev --frozen pytest -q -m slow` | `3 passed, 51 deselected` | ✓ PASS |
| `python -O` canary | `uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q` | `2 passed` | ✓ PASS |
| Full suite | `uv run --extra dev --frozen pytest -q` | `54 passed` | ✓ PASS |
| No solver in repro path | `grep -rniE "pulp|ortools|cbc" src/alpha2/repro/` | only explanatory comments (no imports/calls) | ✓ PASS |
| Manifest golden hash | `python3 -c "json.load(manifest); assert ..."` | `tfp:n31:s1` matches frozen golden `3c953d90…41e2` | ✓ PASS |
| Trust primitives unchanged | `git log`/`git show --name-only` on 10 Phase-3 commit hashes | no matches against `verifier.py`/`schema.py`/`store.py`/`tfp.py` | ✓ PASS |

### Probe Execution

Not applicable — this phase's plans use `<automated>` pytest/shell commands, not `scripts/*/tests/probe-*.sh` style probes. All `<automated>` commands from the four PLAN.md files were independently re-run above with matching results.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| ENV-04 | 01, 02, 03 | Full 296-instance corpus regenerated and independently re-verified; all 27 stored certificates reproduce | ✓ SATISFIED | 296/296 stored, all re-verify via `verify_certificate`; the original 27 (14 baseline+showpieces + 12 Cayley + 1 seed-137) are all present as a subset, confirmed by construction (`freeze.py` order) and directly by seed/family checks above. |
| ENV-06 | 03, 04 | Test suite + CI run the verifier over the stored corpus on every commit, including a `python -O` job and the fingerprint test | ✓ SATISFIED | `ci.yml` `test` job runs exactly this; confirmed both by reading the file and running local equivalents green. |

**Note on REQUIREMENTS.md checkbox state:** `.planning/REQUIREMENTS.md` lines 17/19/112/114 still show ENV-04 and ENV-06 as `- [ ]` / "Pending" in the traceability table, while `.planning/ROADMAP.md` line 15 shows Phase 3 as `[x]` complete (2026-07-22) and all 4 plan checkboxes checked. This is a stale-documentation drift in REQUIREMENTS.md, not a code gap — the codebase evidence above independently confirms both requirements are satisfied. Recommend updating REQUIREMENTS.md's checkboxes/table as a trivial follow-up; not a phase-blocking gap since REQUIREMENTS.md is a tracking artifact, not the implementation.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | none found | — | Scanned all Phase-3-created/modified files (`repro/*.py`, `generators/cayley.py`, `corpus/manifest.py`, `tests/test_corpus_r*.py`, `.github/workflows/ci.yml`) for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER/"not yet implemented" — zero matches. |

### Human Verification Required

None. All must-haves are programmatically verifiable (stored corpus data, pytest results, git history, and a declarative CI YAML file), and all were independently confirmed by direct execution/inspection rather than trusting SUMMARY.md narrative.

### Gaps Summary

No gaps. Every observable truth, artifact, and key link declared across the four PLAN.md
frontmatters (`03-01` through `03-04`) was independently re-verified against the live codebase:
the corpus contains exactly 296 records with the correct family split, every record re-verifies
from stored JSON alone via the raise-based trust root, the golden manifest is frozen with the
correct hashing convention, seed-137 carries the exact Appendix D.3 literal with no solver
invoked anywhere in the Phase-3 driver path, the `python -O` canary and full test suite are both
green, and `.github/workflows/ci.yml` wires R1/R2/fingerprint/`-O` into every commit plus a
scheduled R3/full-296 release gate and a non-blocking, genuinely-executing 3.13 drift canary with
SHA-pinned actions. Trust primitives (`verifier.py`, `schema.py`, `store.py`, `tfp.py`) are
confirmed byte-unchanged across all 10 Phase-3 commits. The only discrepancy found was a stale
checkbox state in `REQUIREMENTS.md` (not yet ticked off), which is a documentation-sync issue,
not a functional gap — flagged above for a trivial follow-up but does not affect the `passed`
status.

---

_Verified: 2026-07-22T04:28:53Z_
_Verifier: Claude (gsd-verifier)_
