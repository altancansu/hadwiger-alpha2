---
phase: 03-corpus-reproduction-ci-first-blood
plan: 03
subsystem: reproduction
tags: [corpus, manifest, golden-hash, r1, r2, r3, determinism, reproducibility, sha256]

# Dependency graph
requires:
  - phase: 03-corpus-reproduction-ci-first-blood
    plan: 02
    provides: "frozen 296-record schema-v1 corpus (284 TFP + 12 Cayley); generators/cayley.py; repro/{baseline,sweep,cayley_run,seed137,freeze}.py"
  - phase: 02-trust-root-and-schema
    provides: "corpus/schema.h_edges_sha256 (frozen sha256 convention), verify_certificate (raise-based trust root), store.append_certificate"
  - phase: 01-environment-and-toolkit-port
    provides: "generators/tfp, paths.CORPUS, pytest+slow-marker pins, fingerprint.json (ENV-03 exemplar)"
provides:
  - "src/alpha2/corpus/manifest.py — 296-entry golden-hash manifest builder reusing schema.h_edges_sha256 (no hand-rolled sha256); asserts recomputed==stored and exactly 296"
  - "data/manifests/corpus-v1.manifest.json — frozen, committed 296-entry golden manifest (284 tfp + 12 cayley); additive to the untouched fingerprint.json"
  - "tests/test_corpus_r2.py — generator-determinism panel (regenerate H from seed -> hash -> compare manifest), TFP + Cayley legs, gated on doc/structural invariants; slow full-296 panel"
  - "tests/test_corpus_r3.py — pinned-interpreter (3.12.13) byte-replay gate, marked slow, replays into tmp_path"
  - "Tightened tests/test_corpus_r1.py — hard 296 / (284,12) count gate + seed-137 model == Appendix D.3 literal"
affects: [03-04 CI workflow (runs R1+R2 every commit, R3+full-296 nightly)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Golden manifest hashes via schema.h_edges_sha256 ONLY — the exact frozen convention the verifier recomputes (single hashing routine; no common-mode gap)"
    - "R2 gates every hash comparison behind a doc-derived (TFP |E(H)|==131) or structural (Cay(Z_p,S) |S|-regular, 2|E|==p|S|) invariant so a porting bug cannot self-certify"
    - "R3 is version-gated: strict byte-equality only on CPython 3.12.13; other interpreters downgrade to 'a verifying model is produced' so the CI canary fails on a genuine hash reason, not R3 fragility"

key-files:
  created:
    - "src/alpha2/corpus/manifest.py"
    - "data/manifests/corpus-v1.manifest.json"
    - "tests/test_corpus_r2.py"
    - "tests/test_corpus_r3.py"
  modified:
    - "tests/test_corpus_r1.py"

key-decisions:
  - "Manifest key scheme (A5) keys off invariants.n for BOTH families: tfp:n{n}:s{seed} / cayley:p{n}:s{seed} (n==p for Cayley Z_p) — extends the existing fingerprint.json style"
  - "corpus-v1.manifest.json written with sort_keys + indent=2 (mirrors fingerprint.json) for a diff-friendly, byte-stable committed artifact; fingerprint.json left byte-unchanged (additive, not overwritten)"
  - "R2 Cayley leg gated on the Cay(Z_p,S) structural identity (|S|-regular + symmetric + 2|E|==p|S|) as the porting-bug tripwire, since no hardcoded doc |E(H)| golden was available for the Cayley instances"
  - "R3 replays via the real repro drivers' run_instance (baseline + cayley_run) into tmp_path; compares only load-bearing fields (excludes environment-stamped reproduction/backends and position-dependent chain_sha256)"

patterns-established:
  - "Pattern: freeze-once golden-hash manifest via the frozen verifier convention (schema.h_edges_sha256), asserting recomputed==stored per record — the R2 anchor"
  - "Pattern: doc/structural invariant gate BEFORE trusting any regenerated hash (a porting bug must not self-certify)"

requirements-completed: [ENV-04, ENV-06]

# Metrics
duration: ~15min
completed: 2026-07-21
---

# Phase 3 Plan 03: Golden Manifest Freeze + R1/R2/R3 Reproduction Contract Summary

**Froze the 296-entry golden-hash manifest (`corpus-v1.manifest.json`, hashed via the frozen `schema.h_edges_sha256` convention the verifier recomputes) and locked in the three-level reproduction contract as the permanent regression harness: R1 hard-gates 296 / (284, 12) + seed-137 == Appendix D.3, R2 proves TFP + Cayley generator determinism against the manifest behind doc/structural invariant gates, and R3 proves pinned-interpreter (3.12.13) byte-identical replay — with `fingerprint.json` and every trust primitive left byte-unchanged.**

## Performance

- **Duration:** ~15 min (execution wave 3)
- **Started / Completed:** 2026-07-21
- **Tasks:** 3 (all `type=auto`)
- **Files:** 5 (4 created, 1 modified)

## Accomplishments

- **Task 1 — `corpus/manifest.py` + freeze:** Built the A5-keyed golden-hash manifest (`tfp:n{n}:s{seed}` / `cayley:p{n}:s{seed}`) reusing `schema.h_edges_sha256` (no local `hashlib.sha256`). `build_manifest` asserts the recomputed hash AGREES with each record's own `H_edges_sha256` (same frozen convention) and refuses duplicate keys; `freeze` asserts exactly 296 entries. Froze `data/manifests/corpus-v1.manifest.json` → `284 tfp + 12 cayley`; `tfp:n31:s1.h_edges_sha256 == 3c953d90…41e2` (frozen golden); `cayley:p31:s5310` present. `fingerprint.json` byte-unchanged.
- **Task 2 — R2 panel + tighten R1:** `test_corpus_r2.py` regenerates H from the seed, hashes via `schema.h_edges_sha256`, and compares to `corpus-v1.manifest.json` — a TFP leg (gated on the Appendix-D.2 `|E(H)|==131`) and a Cayley leg (gated on the `Cay(Z_p,S)` structural identity: `|S|`-regular, symmetric, `2|E|==p|S|`), plus a `slow` full-296 panel that regenerates every stored instance and cross-checks manifest + record self-hash. Tightened `test_corpus_r1.py` to the hard `len==296` / `(284, 12)` count gate and added the seed-137 `model_branch_sets == D3_MODEL` byte-equality; the trust decision stays routed through raise-based `verify_certificate`.
- **Task 3 — R3 replay gate:** `test_corpus_r3.py` (marked `slow`) replays the baseline (31,1) and Cayley (31,5310) drivers into a `tmp_path` corpus under the single-RNG contract v1, then asserts the load-bearing fields (`H_edges`, `model_branch_sets`, `matching_M`, `tutte_berge_U`, `invariants`) are byte-identical to the committed records — gated to CPython 3.12.13, downgrading to "a verifying model is produced" on any other interpreter (Pitfall 4). Never touches the repo corpus.
- **Composition-only, integrity preserved:** No new verification/hashing/storage/generator logic. `git diff --quiet` confirms `verifier.py`, `schema.py`, `store.py`, `tfp.py`, `cayley.py`, and `fingerprint.json` are byte-unchanged.

## Task Commits

Each task committed atomically:

1. **Task 1: freeze 296-entry golden manifest via schema.h_edges_sha256** — `5448c9b` (feat)
2. **Task 2: R2 determinism panel (TFP+Cayley) + tighten R1 to hard 296/(284,12) gate** — `ee02e5c` (test)
3. **Task 3: R3 pinned-interpreter replay gate (marked slow)** — `1ea4b59` (test)

## Files Created/Modified

- `src/alpha2/corpus/manifest.py` (created) — 296-entry golden-hash manifest builder; A5 key scheme; reuses `schema.h_edges_sha256`; asserts recomputed==stored + exactly 296; `main()` freezes the file.
- `data/manifests/corpus-v1.manifest.json` (created) — frozen 296-entry golden manifest (284 tfp + 12 cayley), committed; `sort_keys`+`indent=2` for a stable diff-friendly artifact.
- `tests/test_corpus_r2.py` (created) — R2 determinism panel: TFP + Cayley slices behind doc/structural gates + `slow` full-296 panel; hashes via `schema.h_edges_sha256`, compares to `corpus-v1.manifest.json`.
- `tests/test_corpus_r3.py` (created) — R3 pinned-interpreter byte-replay gate; `@pytest.mark.slow`; replays into `tmp_path`; 3.12.13 guard.
- `tests/test_corpus_r1.py` (modified) — hard `==296` / `(284,12)` count gate + seed-137 `== D.3` literal; added `D3_MODEL` literal and `_find_seed_record` helper; trust stays raise-based.

## Verification Evidence

- `python -m alpha2.corpus.manifest` → `FROZEN: 296 golden-hash entries` (by prefix `{'tfp': 284, 'cayley': 12}`).
- Plan Task-1 one-liner: `manifest 296 ok` (len==296; `tfp:n31:s1` == frozen golden; a `cayley:` key exists).
- `pytest tests/test_corpus_r2.py tests/test_corpus_r1.py -q` → `4 passed`.
- `pytest tests/test_corpus_r3.py -q -m slow` → `2 passed` (pinned interpreter 3.12.13).
- Full suite `pytest -q` → `54 passed` (Plan-01/02 49 + R2 3 + R3 2), no regression.
- `python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q` → `2 passed` (assert-stripping canary; R1 trust routes through raise-based `verify_certificate`).
- `git diff --quiet` over `verifier.py`, `schema.py`, `store.py`, `tfp.py`, `cayley.py`, `fingerprint.json` → all UNCHANGED.

## Deviations from Plan

None — plan executed exactly as written. All acceptance criteria were met without needing any auto-fix (Rules 1-3) or architectural decision (Rule 4).

## Non-deviation Notes (normal flow)

- **pytest lives in the `dev` extra.** As in Plans 01/02, `uv run --frozen pytest` was invoked with `--extra dev` (the default frozen sync installs only runtime packages). Invocation only; no lock drift, no code change.
- **uv PATH bootstrap.** `uv` is not on the shell PATH in this worktree; prepended `$HOME/.local/bin` (working `uv 0.11.30`) and `uv sync --frozen --extra dev` to materialize the worktree `.venv` from the lockfile. No lock drift; interpreter confirmed `3.12.13`.
- **R2 slow full-296 panel runs by default.** No `-m "not slow"` addopts is configured, so the full suite (`pytest -q`) exercises the slow R2/R3 legs too; they pass in ~1.1s total (generation-only + hash; no solver, no verify-at-append), so no deselection was needed.

## Threat Flags

None — no new security-relevant surface. The plan's threat register is mitigated as designed:
- **T-3-01 (manifest tamper):** the manifest hashes via `schema.h_edges_sha256` only (no hand-rolled sha256), asserts `recomputed == stored H_edges_sha256` per record, and is committed; R2 re-derives and compares every commit.
- **T-3-02 (generator drift):** R2 determinism panel with a doc/structural invariant gate before trusting any hash; the manifest is the R2 anchor.
- **T-3-03 (`-O` elevation):** R1's trust decision routes only through raise-based `verify_certificate`; the `python -O` canary over R1 stays green (2 passed).

## Known Stubs

None — no placeholder data or unwired components. The manifest is fully derived from the frozen 296-record corpus; all three R-tests exercise real regeneration/replay against real committed data. The CI workflow that runs R1/R2 every commit and R3/full-296 nightly is intentionally scoped to Plan 04 (per the phase wave decomposition), not a stub in this plan.

## Next Phase Readiness

- The golden manifest is frozen + committed and the R1/R2/R3 contract is green — Plan 04 wires `.github/workflows/ci.yml`: R1 + R2 + fingerprint + `python -O` every commit; R3 + full-296 R2 panel + newer-Python canary on schedule/release.
- The `slow` marker gates R3 (and the R2 full panel) for the nightly/release CI leg.
- No blockers. STATE.md / ROADMAP.md were intentionally NOT modified (worktree mode; the orchestrator owns those writes after the wave merges).

## Self-Check: PASSED

- Files verified present: `src/alpha2/corpus/manifest.py`, `data/manifests/corpus-v1.manifest.json`, `tests/test_corpus_r2.py`, `tests/test_corpus_r3.py`, `tests/test_corpus_r1.py`.
- Commits verified in git log: `5448c9b` (Task 1), `ee02e5c` (Task 2), `1ea4b59` (Task 3).
- Manifest verified: 296 entries, `tfp:n31:s1` == frozen golden, `cayley:p31:s5310` present; R1+R2 (4 passed), R3 slow (2 passed), full suite (54 passed), `-O` canary (2 passed); trust primitives + fingerprint.json byte-unchanged.

---
*Phase: 03-corpus-reproduction-ci-first-blood*
*Completed: 2026-07-21*
