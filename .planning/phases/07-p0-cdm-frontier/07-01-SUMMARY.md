---
phase: 07-p0-cdm-frontier
plan: 01
subsystem: testing
tags: [cdm, pytest, red-scaffold, nauty, geng, graph6, hadwiger, alpha2]

# Dependency graph
requires:
  - phase: 02-corpus
    provides: corpus/verifier.py + corpus/store.py + corpus/schema.py discipline analogs
  - phase: 05-solvers
    provides: solvers/cpsat.py determinism + differential.py agreement-gate analogs
provides:
  - src/alpha2/pool/ + src/alpha2/pool/cdm/ package skeleton
  - paths.CDM_CORPUS (data/corpus/cdm_certificates.json) additive constant
  - tests/pool/cdm/ Wave-0 RED scaffold — 9 test modules + conftest (29 tests)
  - the A1 definition-regression gate (full connected n≤11 MTF oracle, 134 graphs)
  - executable contract for has_cdm / cdm_cpsat / verify_cdm_witness / stream_mtf /
    append_certificate / classify_cdm_fail (implemented in Waves 2–3, plans 02–05)
affects: [07-02, 07-03, 07-04, 07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wave-0 RED scaffold: function-local imports of not-yet-existing modules keep --collect-only clean while bodies stay RED"
    - "Self-contained definition oracle: full n≤11 MTF set embedded as graph6 literals (never skips for want of geng)"
    - "adj = list[set[int]] for G (complement of graph6-decoded MTF H) — LOCKED convention"

key-files:
  created:
    - src/alpha2/pool/__init__.py
    - src/alpha2/pool/cdm/__init__.py
    - tests/pool/__init__.py
    - tests/pool/cdm/__init__.py
    - tests/pool/cdm/conftest.py
    - tests/pool/cdm/test_cdm_n_le_11.py
    - tests/pool/cdm/test_cdm_verifier.py
    - tests/pool/cdm/test_cdm_verifier_dash_O.py
    - tests/pool/cdm/test_generation_counts.py
    - tests/pool/cdm/test_generation_crosscheck.py
    - tests/pool/cdm/test_dfs_cpsat_agree.py
    - tests/pool/cdm/test_transfer_lemma.py
    - tests/pool/cdm/test_disconnected_complement.py
    - tests/pool/cdm/test_cdm_store.py
  modified:
    - src/alpha2/paths.py

key-decisions:
  - "n≤11 MTF oracle embedded as 134 graph6 literals (self-contained), not geng-at-fixture-build, so the A1 definition gate can never silently skip"
  - "Lemma 2.5 equivalence leg made GREEN now (uses embedded oracle + tfp.is_edge_maximal_tf + nx.diameter) — an immediate executable transfer-lemma regression, needing no CDM module"
  - "CDM record convention: store H_edges (MTF triangle-free H) + matching_M of G-edges (complement); verifier rebuilds H-adjacency and re-checks against complement — mirrors corpus/verifier _build_adj"
  - "Adjudicator disconnected carve-out contract pinned as classify_cdm_fail(adj,n)=='disconnected_complement' (07-05 implements)"

patterns-established:
  - "Function-local / import-under-test discipline for RED scaffolds (collection clean, runtime RED)"
  - "Embedded-literal fixtures, zero cross-test imports (mirrors test_cpsat_backend)"
  - "Two distinct brute-verified valid CDM records for store-invariant tests, tmp_path-only"

requirements-completed: [POOL-0]

# Metrics
duration: 22min
completed: 2026-07-23
---

# Phase 07 Plan 01: CDM Frontier Wave-0 RED Scaffold Summary

**The full executable POOL-0 contract landed RED — 9 CDM test modules + conftest (29 tests, clean collection), the A1 definition-regression gate over the complete 134-graph n≤11 MTF oracle, the trust-root mutant/`-O` canary, and an additive `paths.CDM_CORPUS` — with the frozen 296-corpus and its trust root byte-untouched.**

## Performance

- **Duration:** ~22 min
- **Completed:** 2026-07-23
- **Tasks:** 3
- **Files modified:** 15 (14 created, 1 modified)

## Accomplishments
- `src/alpha2/pool/` + `pool/cdm/` package skeleton and additive `paths.CDM_CORPUS` (`data/corpus/cdm_certificates.json`); frozen `paths.CORPUS` literal byte-unchanged.
- The highest-priority **A1 definition-regression gate** (`test_cdm_n_le_11`): iterates the FULL connected n≤11 MTF-complement set — 134 graph6 literals embedded in `conftest.py` (61 at n=11 + all smaller n, generated once via `geng -ctq n | pickg -Z2`, nauty 2.9.3) — asserting `has_cdm` returns a witness for EVERY connected instance (~130) and `None` on disconnected `K_a⊔K_b`. Self-contained: the gate can never silently skip.
- Trust-root discipline scaffolds: 6-mutant `verify_cdm_witness` suite (+ good-record sanity) and the subprocess `python -O` fail-closed canary (3/0/2 exit-code contract).
- Generation (147/392/1274 + Lemma-2.5 second-route + sharding-sum), DFS≡CP-SAT differential (release-blocking), transfer-lemma (Lemma 2.5 GREEN + monotonicity RED), disconnected-complement carve-out, and append-only store (five invariants, tmp_path-only) modules.

## Task Commits

Each task was committed atomically:

1. **Task 1: Package skeleton, paths.CDM_CORPUS, CDM fixtures** - `809600d` (feat)
2. **Task 2: Definition-regression gate + trust-root verifier tests (RED)** - `031c64c` (test)
3. **Task 3: Generation, differential, transfer, disconnected, store tests (RED)** - `61978eb` (test)

## Files Created/Modified
- `src/alpha2/paths.py` - Added additive `CDM_CORPUS` constant beside `CORPUS` (frozen literal untouched).
- `src/alpha2/pool/__init__.py`, `src/alpha2/pool/cdm/__init__.py` - Empty package markers.
- `tests/pool/__init__.py`, `tests/pool/cdm/__init__.py` - Test package markers.
- `tests/pool/cdm/conftest.py` - C5 (has CDM) + `K_3⊔K_3` (disconnected, CDM-fail) adjacencies, hand-built valid CDM record (G=C5), and the 134-graph n≤11 MTF oracle; no cross-test/generator imports.
- `tests/pool/cdm/test_cdm_n_le_11.py` - A1 definition gate (full connected n≤11 set).
- `tests/pool/cdm/test_cdm_verifier.py` - Good record + 6 single-perturbation mutants.
- `tests/pool/cdm/test_cdm_verifier_dash_O.py` - `python -O` raises-only canary.
- `tests/pool/cdm/test_generation_counts.py` - 147/392/1274 (n=14 slow, geng-gated).
- `tests/pool/cdm/test_generation_crosscheck.py` - Lemma-2.5 second route + sharding-sum.
- `tests/pool/cdm/test_dfs_cpsat_agree.py` - DFS≡CP-SAT differential (small + slow full batch).
- `tests/pool/cdm/test_transfer_lemma.py` - Lemma 2.5 (GREEN) + CDM monotonicity (RED).
- `tests/pool/cdm/test_disconnected_complement.py` - `K_a⊔K_b` classified, not escalated.
- `tests/pool/cdm/test_cdm_store.py` - Five append-only store invariants, tmp_path-only.

## Decisions Made
- **Embedded MTF literals over geng-at-fixture-build.** The definition gate is the sole independent check that our A1 reading == CLWY's CDM; embedding the 134 graph6 strings guarantees it runs even without a `geng` binary. Verified the counts live (1/2/3/4/6/10/16/31/61 for n=3..11).
- **Lemma 2.5 leg made GREEN immediately.** It needs only the embedded oracle + `generators.tfp.is_edge_maximal_tf` + `networkx.diameter` — no CDM module — so it is a live transfer-lemma regression now rather than a deferred RED body. Confirmed passing (134/134).
- **CDM record shape.** Records store `H_edges` (the MTF triangle-free H) + `matching_M` as G-edges of the complement + `invariants{n, complement_connected, cdm}`, mirroring the `corpus/verifier._build_adj` rebuild-from-stored-data discipline. Two distinct brute-verified valid records (G=C5, G=complement('ECxo')) back the store tests.

## Deviations from Plan

None - plan executed exactly as written. All RED-scaffold imports are function-local (or subprocess-side) per the plan; `--collect-only` is clean and bodies are RED. No architectural changes, no auth gates, no package installs.

## Issues Encountered
- The project venv is invoked directly (`.venv/bin/python`) because `uv` is not on this shell's PATH; the plan's `uv run pytest ...` verify commands were run as `.venv/bin/python -m pytest ...` (equivalent interpreter + deps). No functional impact.

## Verification Results
- `pytest tests/pool/cdm --collect-only -q` → **29 tests collected, zero collection errors.**
- `pytest tests/pool/cdm -q -m "not slow"` → **24 failed, 1 passed (Lemma 2.5), 4 slow deselected** — the intended Wave-0 RED baseline.
- `pytest -q --ignore=tests/pool -m "not slow"` → **239 passed** (no regression in the existing suite).
- `git status data/corpus/ src/alpha2/corpus/` → **clean**: frozen 296-corpus, `corpus/store.py`, `corpus/verifier.py`, `corpus/schema.py` byte-untouched.
- `paths.CDM_CORPUS` ends `data/corpus/cdm_certificates.json`; `paths.CORPUS` still ends `hadwiger_alpha2_certificates.json`.

## Known Stubs
None. This is an intentional RED test scaffold: every module under test (`alpha2.pool.cdm.reference/cpsat/verifier/schema/store/generate/adjudicate`) is implemented in plans 07-02…07-05, and the failing bodies are the executable contract those plans must satisfy — not stubs masking incomplete work.

## Next Phase Readiness
- Wave 2/3 (plans 07-02…07-05) can implement `pool/cdm/*` against a complete, collectable RED contract; each module goes GREEN as it lands.
- The A1 gate must pass BEFORE any n=12–14 new-science claim (Nyquist discipline).
- Interface names the later plans must honor are pinned by the tests: `has_cdm(adj,n)`, `cdm_cpsat(adj,n)`, `verify_cdm_witness(record)` + `VerificationError`, `stream_mtf(n,res,mod)`, `append_certificate(rec,path)`, `classify_cdm_fail(adj,n)`.

---
*Phase: 07-p0-cdm-frontier*
*Completed: 2026-07-23*

## Self-Check: PASSED

All 15 created/modified files present on disk; all 3 task commits (`809600d`, `031c64c`, `61978eb`) present in git history.
