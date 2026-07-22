---
phase: 3
slug: corpus-reproduction-ci-first-blood
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-21
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Mirrors 03-RESEARCH.md § Validation Architecture (Phase-Requirements → Test-Map)
> and the actual `<automated>` commands in the four PLAN.md files.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest **8.3.4** (pinned in Plan 01 Task 1; the environment resolves 9.x but the pin matches CLAUDE.md's stated `pytest 8.x` stack so the newer-Python canary cannot silently drift the runner — A6) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths=["tests"]`, `pythonpath=["src"]`, `markers=["slow: release/nightly replay gate"]` (marker registered in Plan 01 Task 1) |
| **Quick run command** | `uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q` |
| **Full suite command** | `uv run --frozen pytest -q` (adds the existing 42 Phase-1/2 tests + the `-O` canary; `slow`/R3 deselected by default) |
| **Estimated runtime** | quick panel ~5–15 s; full suite (slow deselected) ~30–60 s; R3 `-m slow` and one-shot corpus freeze can run into low **minutes** (n=501 witness extraction + O(N²) verify-at-append — see Slow-Freeze Escape Hatch below) |

**Slow-Freeze Escape Hatch (W5 / RESEARCH Pitfall 5 / A3):** the corpus-freeze / baseline-regeneration *driver* steps (`python -m alpha2.repro.baseline`, `python -m alpha2.repro.freeze`) are code-execution, not test latency, and can exceed the 30 s Nyquist window (worst case minutes). Accepted MVP tradeoff — run the driver in the background or raise the tool timeout, and/or reduce the heuristic `time_budget` for the bulk pass. Never weaken verify-at-append. R1/R2/R3 check the **stored** corpus, so test feedback latency stays fast once the corpus is frozen.

---

## Sampling Rate

- **After every task commit:** Run `uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q` (verifier over the stored corpus + determinism slice).
- **After every plan wave:** Run `uv run --frozen pytest -q` (full suite incl. the Phase-1/2 tests and the `-O` canary).
- **Before `/gsd:verify-work`:** Full suite green **+** R3 green (`pytest tests/test_corpus_r3.py -q -m slow`) **+** `len(corpus)==296` **+** `corpus-v1.manifest.json` committed.
- **Max feedback latency:** 30 s for test panels (driver freeze steps exempted per the Slow-Freeze Escape Hatch).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | ENV-04 | T-3-03 | R1 routes the trust decision only through raise-based `verify_certificate` (no `assert` governs verification); pytest pinned + `slow` marker registered | integration (RED) | `uv run --frozen pytest tests/test_corpus_r1.py -q ; test $? -ne 0` | ✅ created test-first in this task | ⬜ pending |
| 3-01-02 | 01 | 1 | ENV-04 | T-3-01 / T-3-02 / T-3-03 | baseline.py emits schema-v1 via `store.append_certificate` (verify-at-append), assert-free verified path, (31,1) byte-equal to Appendix D.2 | integration (GREEN) | `uv run --frozen python -m alpha2.repro.baseline && uv run --frozen pytest tests/test_corpus_r1.py -q` | ✅ (baseline.py finalized) | ⬜ pending |
| 3-02-01 | 02 | 2 | ENV-04 | T-3-02 | `generators/cayley.py` verbatim C.3, rng injected (never global), ruff-excluded, no solver | unit (smoke) | `uv run --frozen python -c "import random; from alpha2.generators.cayley import random_maximal_symmetric_sumfree, cayley_adj; S=random_maximal_symmetric_sumfree(31, random.Random(5310)); a=cayley_adj(31,S); print(len(S), sum(len(x) for x in a))"` | ✅ Wave 0 (new module) | ⬜ pending |
| 3-02-02 | 02 | 2 | ENV-04 | T-3-01 | sweep.py excludes seed-137; seed137.py carries the D.3 literal with NO `solve(` (solver-free); no assert governs verification | unit (structural) | `uv run --frozen python -c "import pathlib; s=pathlib.Path('src/alpha2/repro/sweep.py').read_text(); assert 'append_certificate' in s and 'if s != 137' in s; z=pathlib.Path('src/alpha2/repro/seed137.py').read_text(); assert 'SEED137_MODEL' in z and 'solve(' not in z; print('ok')"` | ✅ Wave 0 (new drivers) | ⬜ pending |
| 3-02-03 | 02 | 2 | ENV-04 | T-3-01 / T-3-01b | freeze.py rebuilds from empty to exactly 296 records with family counts (284 TFP, 12 Cayley); Cayley records carry inline H_edges | integration | `uv run --frozen python -m alpha2.repro.freeze && uv run --frozen python -c "import json,collections,alpha2.paths as p; r=json.load(open(p.CORPUS)); c=collections.Counter(x['provenance']['family'] for x in r); assert len(r)==296; assert c['triangle_free_process_complement']==284 and c['cayley_maximal_sumfree_Zp']==12; print('296 ok')"` | ✅ Wave 0 (new freeze.py) | ⬜ pending |
| 3-03-01 | 03 | 3 | ENV-04 | T-3-01 | 296-entry manifest hashes via `schema.h_edges_sha256` (frozen convention, no hand-rolled sha256); fingerprint.json untouched | integration | `uv run --frozen python -m alpha2.corpus.manifest && uv run --frozen python -c "import json; m=json.load(open('data/manifests/corpus-v1.manifest.json')); assert len(m)==296; assert m['tfp:n31:s1']['h_edges_sha256']=='3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2'; print('manifest 296 ok')"` | ✅ Wave 0 (new manifest.py) | ⬜ pending |
| 3-03-02 | 03 | 3 | ENV-04, ENV-06 | T-3-02 / T-3-03 | R2 regenerate→hash→compare-to-manifest behind a doc-invariant gate (TFP + Cayley legs); R1 hard-gates 296/(284,12) + seed-137==D.3 | integration (determinism) | `uv run --frozen pytest tests/test_corpus_r2.py tests/test_corpus_r1.py -q` | ✅ Wave 0 (test_corpus_r2.py) | ⬜ pending |
| 3-03-03 | 03 | 3 | ENV-06 | T-3-03 | R3 replays a driver slice into `tmp_path` and asserts byte-identical stored fields under the pinned-interpreter (3.12.13) guard; marked `slow` | slow (release gate) | `uv run --frozen pytest tests/test_corpus_r3.py -q -m slow` | ✅ Wave 0 (test_corpus_r3.py) | ⬜ pending |
| 3-04-01 | 04 | 4 | ENV-06 | T-3-04 / T-3-03 | Every-commit `test` job: R1+R2+fingerprint + `python -O` canary; all actions SHA-pinned; `uv sync --locked` / `uv run --frozen`; no macOS leg | CI (config) | `uv run --frozen python -c "d=__import__('yaml').safe_load(open('.github/workflows/ci.yml')); j=d['jobs']['test']; steps=' '.join(str(s) for s in j['steps']); assert 'astral-sh/setup-uv' in steps and 'uv sync --locked' in steps and 'python -O' in steps and 'test_corpus_r1.py' in steps and 'test_fingerprint.py' in steps; print('ok')"` | ✅ Wave 0 (new ci.yml) | ⬜ pending |
| 3-04-02 | 04 | 4 | ENV-06 | T-3-02 / T-3-04 | Scheduled release-gate (R3 + full-296 R2 on 3.12.13); non-blocking 3.13 canary in an isolated `--no-project` env (requires-python bypassed) that genuinely runs and fails on drift | CI (config) | `uv run --frozen python -c "s=open('.github/workflows/ci.yml').read(); assert 'continue-on-error: true' in s and '3.13' in s and '--no-project' in s and '-m slow' in s and 'schedule' in s; print('ok')" && uv run --frozen pytest -q -m slow` | ✅ Wave 0 (ci.yml jobs) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing test infrastructure (pytest in the `dev` extra + `[tool.pytest.ini_options]` config with `testpaths`/`pythonpath`) already exists from Phases 1–2. The only Wave 0 setup is folded into **Plan 01 Task 1** (executed test-first / RED-first), not a separate scaffolding pass:

- [x] Pin pytest to `8.3.4` in the `dev` extra + `uv lock` — Plan 01 Task 1.
- [x] Register the `slow` pytest marker in `[tool.pytest.ini_options]` — Plan 01 Task 1.
- [x] `tests/test_corpus_r1.py` created RED-first (fails on the empty corpus) before baseline.py is finalized — Plan 01 Task 1 → GREEN in Task 2.
- New test files `tests/test_corpus_r2.py` and `tests/test_corpus_r3.py` are created inside Plan 03 (Wave 3) against the already-frozen corpus; the CI harness (`ci.yml`) is created in Plan 04 (Wave 4).

*No separate Wave 0 scaffolding is required beyond the above — existing pytest infrastructure covers the phase, and all new tests are authored test-first within their plans.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| (none) | — | — | — |

*All phase behaviors have automated verification. The 3.13 drift canary is intentionally informational (`continue-on-error: true`) but still fully automated — a human reads its yellow annotation, they do not run it.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task above carries an automated command)
- [x] Wave 0 covers all MISSING references (pytest pin + `slow` marker + R1 RED scaffold, all in Plan 01 Task 1; no `MISSING` automated commands remain)
- [x] No watch-mode flags
- [x] Feedback latency < 30s (driver freeze steps exempted via the documented Slow-Freeze Escape Hatch)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-21
