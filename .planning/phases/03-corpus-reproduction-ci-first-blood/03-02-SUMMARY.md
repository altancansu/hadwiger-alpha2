---
phase: 03-corpus-reproduction-ci-first-blood
plan: 02
subsystem: reproduction
tags: [corpus, cayley, sweep, seed137, freeze, schema-v1, reproducibility, solver-free]

# Dependency graph
requires:
  - phase: 03-corpus-reproduction-ci-first-blood
    plan: 01
    provides: "finalized repro/baseline.py schema-v1 emission template (generator -> witness -> build_record -> append_certificate), R1 test, 14-record slice, pytest+slow-marker pins"
  - phase: 01-environment-and-toolkit-port
    provides: "generators/tfp, invariants/matching+witness, search/heuristic.solve, paths.CORPUS"
  - phase: 02-trust-root-and-schema
    provides: "schema.build_record/provenance_*, store.append_certificate (verify-at-append), verifier.verify_certificate"
provides:
  - "generators/cayley.py — verbatim Appendix C.3 port (can_add / random_maximal_symmetric_sumfree / cayley_adj), rng-injected, solver-free, ruff-excluded"
  - "repro/sweep.py — 269-instance TFP sweep driver (seed-137 excluded), schema-v1 via the trust root"
  - "repro/seed137.py — solver-free seed-137 exact-study driver carrying the Appendix D.3 K16 literal"
  - "repro/cayley_run.py — 12-instance Cayley driver storing inline canonical H_edges (self-contained certs)"
  - "repro/freeze.py — single ordered-freeze entry point: empty corpus -> exactly 296 records (284 TFP + 12 Cayley)"
  - "Frozen 296-record schema-v1 corpus (data/corpus/hadwiger_alpha2_certificates.json), all re-verifying from JSON alone"
affects: [03-03 manifest + strict count/hash gates, 03-04 CI workflow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "generators/cayley.py mirrors generators/tfp.py: verbatim reference bodies, rng injected (never global), ruff extend-exclude for determinism"
    - "Cayley certs store INLINE canonical H_edges (not just S/p) so the trust root re-derives adjacency from stored bytes (Pitfall 2 / T-3-01)"
    - "seed-137 carried as the Appendix D.3 literal with NO solver (Phase 3 is solver-free); method string documents the true had_2(G)=17"
    - "freeze.py is the single ordered-freeze command: empty -> baseline(14) -> sweep(269) -> cayley_run(12) -> seed137(1) = 296, with count/family-count asserts"

key-files:
  created:
    - "src/alpha2/generators/cayley.py"
    - "src/alpha2/repro/sweep.py"
    - "src/alpha2/repro/seed137.py"
    - "src/alpha2/repro/cayley_run.py"
    - "src/alpha2/repro/freeze.py"
  modified:
    - "pyproject.toml"
    - "data/corpus/hadwiger_alpha2_certificates.json"

key-decisions:
  - "cayley.py ported byte-verbatim from C.3 and added to [tool.ruff] extend-exclude; the ilp fallback was intentionally NOT ported (solver-free phase)"
  - "seed-137 stored ONCE (excluded from the 269 sweep) as the D.3 16-set literal; method 'exact ILP (CBC): had_2(G)=17' documents the true had_2 and routes reproduction.kind=semantic without running any solver"
  - "freeze.py drives all four generators in fixed order onto an emptied corpus; family-count/len asserts govern accounting only — correctness stays with raise-based verify-at-append (python -O safe)"

requirements-completed: [ENV-04]

# Metrics
duration: ~15min
completed: 2026-07-21
---

# Phase 3 Plan 02: Full-296 Corpus Reproduction Summary

**Scaled the proven Plan-01 baseline emission path to the full corpus: ported the one missing generator (`generators/cayley.py`, verbatim Appendix C.3), wrote the three remaining drivers (`sweep.py`, `seed137.py`, `cayley_run.py`) plus a single ordered `freeze.py`, and froze exactly 296 self-contained schema-v1 certificates (284 TFP + 12 Cayley) — every one re-verifying from stored JSON alone, with no solver invoked.**

## Performance

- **Duration:** ~15 min (execution wave 2)
- **Started / Completed:** 2026-07-21
- **Tasks:** 3 (all `type=auto`)
- **Files:** 7 (5 created, 2 modified)

## Accomplishments
- **Task 1 — `generators/cayley.py`:** Byte-verbatim C.3 port of `can_add` / `random_maximal_symmetric_sumfree` / `cayley_adj`, `rng` injected (consumes the stream via `rng.shuffle`), no global seed, no solver. Added to `[tool.ruff] extend-exclude` (determinism-sensitive). Smoke test: `random_maximal_symmetric_sumfree(31, Random(5310))` -> |S|=10, 310 directed adjacencies.
- **Task 2 — `sweep.py` + `seed137.py`:** `sweep.py` copies the finalized baseline `run_instance` verbatim; the only difference is the 269-instance data list (`n=31 s100..299 excl 137` = 199, `n=51 s100..149` = 50, `n=101 s100..119` = 20) with a runtime `assert len == 269`. `seed137.py` regenerates H from `random.Random(137)` and carries the Appendix D.3 K16 literal — no `solve`, no CBC — with `method="exact ILP (CBC): had_2(G)=17"` (routes `reproduction.kind=semantic`), `omega_G=14`, had_2(model)=16.
- **Task 3 — `cayley_run.py` + `freeze.py`:** `cayley_run.py` runs the 12 Cayley instances (p in {31,53,101,151}, seed=5000+10p+k), reconstructs and stores **inline canonical H_edges** so each record is self-contained (Pitfall 2), via `provenance_params("cayley_maximal_sumfree_Zp", p, {"S": sorted(S)}, seed=seed)`; all 12 resolve heuristically. `freeze.py` empties the corpus and drives baseline(14) -> sweep(269) -> cayley_run(12) -> seed137(1), then asserts `len == 296` and family counts (284, 12).
- **Freeze result:** `FROZEN: 296 records ({'triangle_free_process_complement': 284, 'cayley_maximal_sumfree_Zp': 12})`, exit 0.
- **Trust primitives byte-unchanged:** `git diff --quiet` over `verifier.py`, `schema.py`, `store.py`, `tfp.py` — no verification/hashing/storage/generator primitive mutated (composition-only, as mandated).

## Task Commits

Each task committed atomically:

1. **Task 1: Port generators/cayley.py verbatim from C.3 + ruff exclude** — `ac61a8a` (feat)
2. **Task 2: sweep.py (269) + seed137.py (D.3 literal, solver-free)** — `03b2256` (feat)
3. **Task 3: cayley_run.py (12, inline H_edges) + freeze.py ordered freeze to 296** — `bbfbc16` (feat)

## Files Created/Modified
- `src/alpha2/generators/cayley.py` (created) — verbatim C.3 sum-free/Cayley generator; rng-injected; ruff-excluded; solver-free.
- `src/alpha2/repro/sweep.py` (created) — 269-instance TFP sweep; baseline `run_instance` verbatim; data-encoded instance list + `assert len == 269`.
- `src/alpha2/repro/seed137.py` (created) — solver-free seed-137 exact study; carries `SEED137_MODEL` (D.3 K16 literal); `triangle_free_process(31, rng)` regen only.
- `src/alpha2/repro/cayley_run.py` (created) — 12 Cayley instances; inline canonical H_edges; `provenance_params` with S+seed.
- `src/alpha2/repro/freeze.py` (created) — single ordered-freeze entry point; empties corpus, runs the four drivers, asserts 296 + (284, 12).
- `pyproject.toml` (modified) — added `src/alpha2/generators/cayley.py` to `[tool.ruff] extend-exclude`.
- `data/corpus/hadwiger_alpha2_certificates.json` (modified) — regenerated from empty to the full 296-record schema-v1 corpus (was the 14-record Plan-01 slice).

## Verification Evidence
- `python -m alpha2.repro.freeze` -> exit 0, 296 records, family counts (284, 12).
- Plan verify one-liner: `296 ok {'triangle_free_process_complement': 284, 'cayley_maximal_sumfree_Zp': 12}`.
- `pytest tests/test_corpus_r1.py` -> `1 passed` (re-verifies every stored record from JSON alone via raise-based `verify_certificate`).
- `pytest tests/test_fingerprint.py -m "not slow"` -> `7 passed`.
- `git diff --quiet` over verifier/schema/store/tfp -> UNCHANGED.
- Corpus tracked by git (`git ls-files` lists it).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Docstring token `ilp_had2` tripped the "no solver" acceptance grep**
- **Found during:** Task 1 verification.
- **Issue:** The acceptance criterion greps that `cayley.py` does NOT contain `ilp_had2`. My explanatory docstring mentioned the ported-out function by name (`(`ilp_had2`) is intentionally NOT ported`), producing a false-positive "SOLVER PRESENT" on the literal grep even though no solver code exists.
- **Fix:** Reworded the docstring to "The exact ILP fallback from C.3 is intentionally NOT ported" — same meaning, no `ilp_had2` token.
- **Files modified:** `src/alpha2/generators/cayley.py`
- **Verification:** `grep -q 'ilp_had2\|import pulp'` now returns no match; the file still carries the three verbatim functions + `rng.shuffle`.
- **Committed in:** `ac61a8a` (Task 1 commit).

---

**Total deviations:** 1 auto-fixed (1 blocking, cosmetic). No architectural changes, no scope creep.

## Non-deviation Notes (normal flow)
- **pytest lives in the `dev` extra.** The plan's bare `uv run --frozen pytest` fails to spawn pytest because the default frozen sync installs only the 12 runtime packages. Ran with `uv run --frozen --extra dev pytest` (matching Plan 01's `--extra dev` convention). No lock drift; this is invocation, not a code change.
- **Slow-freeze escape hatch used as designed (W5 / Pitfall 5 / A3).** The full 296 freeze re-verifies the whole prefix on every append (O(N^2)) plus n=501 witness extraction; it was run as a background job to avoid tool-call truncation and completed cleanly in well under the tool timeout. Verify-at-append was NOT weakened and no batch path was added. Heuristic `time_budget` was left at the reproduction defaults (never reduced) so the frozen corpus is the standard-budget artifact.

## Threat Flags
None — no new security-relevant surface. The plan's threat register is mitigated as designed:
- **T-3-01 (Cayley tamper):** Cayley records carry inline canonical `H_edges` (verified: `num_H_edges` present, e.g. 155 for p=31), so the verifier re-derives adjacency from stored bytes.
- **T-3-02 (RNG drift):** `cayley.py` bodies are byte-verbatim + ruff-excluded; single-RNG contract v1 preserved.
- **T-3-01b (miscount):** seed-137 stored once (excluded from the sweep); `freeze.py` asserts `len == 296` and family counts (284, 12).
- **T-3-SC (supply chain):** no new PyPI installs — runtime stack unchanged from the Phase-1 lockfile.

## Known Stubs
None — no placeholder data or unwired components. All 296 records are fully verified schema-v1 certificates re-verifying from JSON alone. The manifest builder and the strict R1/R2/R3 count+hash gates are intentionally scoped to Plan 03 (per the plan's wave decomposition), not stubs in this plan's output.

## Next Phase Readiness
- The full 296-record corpus is frozen and committed as the immutability anchor — Plan 03 hashes it into `corpus-v1.manifest.json` and tightens R1 to a hard count gate + adds R2/R3.
- All four drivers + `freeze.py` are the deterministic rebuild path a single command reproduces.
- No blockers. STATE.md / ROADMAP.md were intentionally NOT modified (worktree mode; orchestrator owns those writes).

## Self-Check: PASSED
- Files verified present: `src/alpha2/generators/cayley.py`, `src/alpha2/repro/sweep.py`, `src/alpha2/repro/seed137.py`, `src/alpha2/repro/cayley_run.py`, `src/alpha2/repro/freeze.py`, `data/corpus/hadwiger_alpha2_certificates.json`.
- Commits verified in git log: `ac61a8a` (Task 1), `03b2256` (Task 2), `bbfbc16` (Task 3).
- Corpus verified: 296 records, family counts (284, 12); R1 + fingerprint tests green; trust primitives byte-unchanged.

---
*Phase: 03-corpus-reproduction-ci-first-blood*
*Completed: 2026-07-21*
