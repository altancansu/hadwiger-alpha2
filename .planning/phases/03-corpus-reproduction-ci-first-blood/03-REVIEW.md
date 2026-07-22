---
phase: 03-corpus-reproduction-ci-first-blood
reviewed: 2026-07-22T04:33:25Z
depth: deep
files_reviewed: 12
files_reviewed_list:
  - src/alpha2/repro/baseline.py
  - src/alpha2/repro/sweep.py
  - src/alpha2/repro/cayley_run.py
  - src/alpha2/repro/seed137.py
  - src/alpha2/repro/freeze.py
  - src/alpha2/generators/cayley.py
  - src/alpha2/corpus/manifest.py
  - tests/test_corpus_r1.py
  - tests/test_corpus_r2.py
  - tests/test_corpus_r3.py
  - .github/workflows/ci.yml
  - pyproject.toml
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-07-22T04:33:25Z
**Depth:** deep
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed the diff `8649deb..HEAD` for `src/`, `tests/`, `.github/`, `pyproject.toml`. This is a strong, disciplined implementation: the trust root (`corpus/verifier.py`), schema (`corpus/schema.py`) and store (`corpus/store.py`) are byte-unchanged in this phase (confirmed by diff), so every certificate's correctness continues to route through the raise-based `verify_certificate` — I could not find any `assert` governing a verification/trust decision anywhere in the new code (all asserts in `sweep.py`/`freeze.py` guard only the 269/296 instance-count accounting, matching the project's own stated discipline). The solver-free property holds: no `pulp`/`cbc`/`ortools`/`cp_model` import or call appears anywhere in the Phase-3 path; seed-137 is carried as a literal (`SEED137_MODEL`) and only `triangle_free_process` (never `solve`) is invoked in `seed137.py`. The manifest reuses `schema.h_edges_sha256` exclusively — no hand-rolled hashing. The committed corpus (296 records, 284/12 split) and manifest (296 entries) were spot-checked and match the documented accounting.

The one material defect is a genuine data-loss landmine in the freeze orchestration: `repro/freeze.py`'s `freeze(path=...)` parameter is not honored by `repro/baseline.py`, whose `main()` unconditionally targets and deletes the real `paths.CORPUS` regardless of what path the caller intended. This is dormant today (nothing currently calls `freeze(path=<non-default>)`), but it directly contradicts the store's own "impossible to corrupt" design goal at the orchestration layer, and is exactly the kind of API footgun a future test or script would trigger by accident. I also found a CI test-selection bug (the "every commit" job unintentionally executes the release/nightly `@pytest.mark.slow` full-296 R2 panel because the invoking command lacks `-m "not slow"`), and a missing failure-mode guard where `search.heuristic.solve()` can return `sets=None` on a wall-clock timeout with no handling in any of the three heuristic-driving repro drivers.

## Critical Issues

### CR-01: `freeze(path=...)` is not honored by `baseline.main()` — data-loss risk on the committed corpus

**Status:** FIXED (2026-07-22, commit 979d818) — `baseline.main()` now takes `path=None` (default resolves to `paths.CORPUS`, byte-identical behavior) and honors a caller path end-to-end; `freeze()` threads `path` into `baseline.main(path=path)`. Regression test added: `tests/test_freeze_path_threading.py` (stub drivers; proves `paths.CORPUS` stays byte-untouched).

**File:** `src/alpha2/repro/freeze.py:36-63` (and `src/alpha2/repro/baseline.py:65-78`)
**Issue:** `freeze(path=None)` accepts an arbitrary `path` and, when it is not `paths.CORPUS`, creates an empty JSON array there and then calls the four drivers. Three of the four drivers (`sweep.main(path=path)`, `cayley_run.main(path=path)`, `seed137.main(path=path)`) correctly append onto the caller-supplied `path`. `baseline.main()`, however, takes **no** `path` argument — it hardcodes `path = paths.ensure_parent(paths.CORPUS)` and, per its own docstring ("the corpus is rebuilt from EMPTY on every run"), does `if os.path.exists(path): os.remove(path)` on **`paths.CORPUS`** before writing 14 records there, ignoring whatever `path` was passed into `freeze()`. The `# baseline.main empties+writes to paths.CORPUS` comment on `freeze.py:50` acknowledges this behavior but does not fix it.

Concretely, calling `freeze(path=<some other file>)` (e.g. from a test that wants to avoid touching the real corpus, or a future script) will:
1. Unconditionally **delete the real, committed 296-record `paths.CORPUS`** (`os.remove` inside `baseline.main()`), then overwrite it with only 14 baseline+showpiece records — a silent, irreversible destruction of the trust-critical corpus artifact this whole phase exists to protect.
2. Leave the caller's intended `path` with only 269+12+1 = 282 records (sweep+cayley+seed137, since baseline's 14 never land there), which trips the `assert len(corpus) == 296` at the end of `freeze()` — but only *after* step 1 has already happened.

No test or call site in this diff currently passes a non-default `path` to `freeze()` (verified by grep), so this is dormant, not actively triggered. But the function signature actively invites exactly this usage, the failure mode is destructive to the repo's git-committed immutability anchor (`store.py`'s own docstring calls git history "the actual immutability anchor for a wholesale rewrite" — this bug bypasses that anchor by rewriting the file directly on disk before any commit), and there is no confirmation/safety check anywhere in the path. This meets the BLOCKER bar for data-loss risk.

**Fix:** Give `baseline.main()` the same `path=None` contract as its siblings, and thread it through:
```python
# src/alpha2/repro/baseline.py
def main(path=None):
    instances = [(31, 1), (31, 2), (31, 3), (32, 4), (51, 5), (51, 6),
                 (76, 7), (101, 8), (101, 9), (151, 10), (200, 11), (201, 12),
                 (301, 13), (501, 14)]
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    if os.path.exists(path):
        os.remove(path)
    ...
    for n, seed in instances:
        run_instance(n, seed, path)
```
```python
# src/alpha2/repro/freeze.py
baseline.main(path=path)        # 14 TFP (now honors the caller's path)
```
Additionally, consider guarding the `os.remove(path)` in `baseline.main()` (and the `os.remove` in `freeze()`) so a destructive rebuild only ever targets a path the caller explicitly opted into, e.g. by requiring the caller to pass a fresh/non-existent path rather than silently truncating whatever already exists there.

## Warnings

### WR-01: CI "every commit" job runs the release/nightly full-296 R2 panel

**Status:** FIXED (2026-07-22, committed with this review update) — added `-m "not slow"` to the every-commit R1/R2/fingerprint step; verified `test_r2_full_panel_all_296` is deselected per-commit. The `release-gate` job (including its second `test_corpus_r2.py` step), the `-O` canary step, the 3.13 canary job, and all action SHA pins are unchanged (release-gate cleanup deliberately deferred — out of scope for this fix pass).

**File:** `.github/workflows/ci.yml:34-35`
**Issue:** The `test` job's step runs:
```
uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q
```
with no `-m "not slow"` filter. `tests/test_corpus_r2.py::test_r2_full_panel_all_296` is decorated `@pytest.mark.slow` and its own module docstring states "Per-commit: a small slice... The full 296-instance panel is the `slow` (release/nightly) leg below" — but because the CI command doesn't deselect the `slow` marker, pytest collects and **runs** `test_r2_full_panel_all_296` on every push and PR anyway (verified locally: `pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q --collect-only` collects `test_r2_full_panel_all_296`; it only gets excluded when `-m "not slow"` is explicitly passed). This directly contradicts the documented per-commit/release-gate split in both the test file and `03-RESEARCH.md`'s Validation Architecture section ("Per task commit: ... fast determinism slice" vs. "Phase gate: full suite green"). The `release-gate` job then reruns the same panel twice more (`pytest -q -m slow`, then a redundant `pytest tests/test_corpus_r2.py -q`), so on a scheduled/tag run the full-296 regeneration executes three times in one workflow.

Locally the full panel only takes ~0.4s (it regenerates adjacency but never invokes the heuristic solver), so the immediate performance blast radius is small today — but the *design intent* documented in the code is not what actually executes, and that gap will silently widen if the panel grows more expensive.

**Fix:**
```yaml
- name: R1 + R2 (fast slice) + fingerprint (verifier over stored corpus)
  run: uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -m "not slow" -q
```
and drop the redundant second `pytest tests/test_corpus_r2.py -q` step in `release-gate` (the `-m slow` run already covers it, or explicitly separate "slow panel" vs "fast slice" if both are wanted for the release gate).

### WR-02: No guard for `solve()` returning `sets=None` on a search timeout

**Status:** FIXED (2026-07-22, commit 4ca3177) — all three drivers (`baseline.py`, `sweep.py`, `cayley_run.py`) now raise a `RuntimeError` naming the instance (n/p, seed, restarts, elapsed) when `solve()` returns `sets=None`; success path unchanged.

**File:** `src/alpha2/repro/baseline.py:46`, `src/alpha2/repro/sweep.py:50`, `src/alpha2/repro/cayley_run.py:49`
**Issue:** `search.heuristic.solve(adj, n, k, rng, time_budget=...)` uses `time.time()`-gated loops and returns `(None, best_init, None, restarts, elapsed)` if it fails to drive the conflict set to empty before `time_budget` expires (`heuristic.py:157`). None of the three repro drivers that call `solve()` check for this:
```python
sets, init_conf, moves, restarts, tsolve = solve(adj, n, chi, rng)  # SAME rng, next
...
model_branch_sets=[list(s) for s in sets],   # TypeError if sets is None
```
A timeout produces an unhandled `TypeError: 'NoneType' object is not iterable` mid-driver rather than a clear, actionable error — this is especially relevant for the 269-instance sweep and the 12 Cayley instances (the largest, n≤501/p≤151, run in a single `freeze()` invocation, per Pitfall 5's own "could run for minutes" note) on a slower or loaded CI runner. Because the number of `rng` draws consumed before the time-based cutoff is itself wall-clock dependent, a timeout is also a genuine (if narrow) violation of the "deterministic in (n, seed)" contract this whole phase is built to protect: the exact same seed could produce a successful model on a fast machine and a bare crash on a slow one.

**Fix:** Fail closed with a clear diagnostic instead of an opaque `TypeError`:
```python
sets, init_conf, moves, restarts, tsolve = solve(adj, n, chi, rng)
if sets is None:
    raise RuntimeError(
        f"heuristic search timed out for n={n} seed={seed} "
        f"(restarts={restarts}, elapsed={tsolve:.1f}s) — no model found"
    )
```

### WR-03: `baseline.main()` signature is inconsistent with its sibling drivers

**Status:** FIXED (2026-07-22, commit 979d818) — resolved by the CR-01 fix (same root cause): `baseline.main(path=None)` now matches its sibling drivers.

**File:** `src/alpha2/repro/baseline.py:65`
**Issue:** `sweep.main(path=None)`, `cayley_run.main(path=None, time_budget=60.0)` and `seed137.main(path=None)` all accept an optional `path`; `baseline.main()` does not. This is the root API inconsistency behind CR-01, and independent of that bug it is also a straightforward maintainability/consistency defect: a reader of `freeze.py` who sees `sweep.main(path=path)`, `cayley_run.main(path=path)`, `seed137.main(path=path)` would reasonably expect `baseline.main(path=path)` to exist too.
**Fix:** See CR-01's fix — give `baseline.main()` the same `path=None` contract as the other three drivers.

## Info

### IN-01: `nu2` from `extract_witness` is computed and discarded in every driver

**File:** `src/alpha2/repro/baseline.py:47`, `src/alpha2/repro/sweep.py:51`, `src/alpha2/repro/cayley_run.py:50`, `src/alpha2/repro/seed137.py:48`
**Issue:** Each driver computes `nu = matching_number(adj, n)` and later calls `M, U, nu2 = extract_witness(adj, n)`, which internally calls `matching_number(adj, n)` again (`invariants/witness.py:37`) and returns it as `nu2`. `nu2` is never read or cross-checked against `nu` anywhere in the driver. Since both calls are the same deterministic pure function on the same input, `nu2` is not an independent cross-check (it can't diverge from `nu`) — it's simply a discarded return value from a redundant blossom-matching computation.
**Fix:** Either drop the unused binding (`M, U, _ = extract_witness(adj, n)`) or, if an explicit local sanity check is desired, assert `nu2 == nu` at the driver level to make the redundancy purposeful rather than silent.

### IN-02: Undocumented magic-number divergence in Cayley's search time budget

**File:** `src/alpha2/repro/cayley_run.py:36`
**Issue:** `cayley_run.run_instance` defaults `time_budget=60.0`, while `baseline.py`/`sweep.py` call `solve()` with no override (the `heuristic.solve` default of `90.0`). Nothing in the driver or its docstring explains why Cayley instances get a shorter budget than TFP instances; given that `time_budget` is load-bearing for RNG consumption (see WR-02), an unexplained divergent constant is worth a one-line justification so a future editor doesn't "helpfully" unify the two budgets and inadvertently reproduce a different corpus.
**Fix:** Add a one-line comment on the `time_budget=60.0` default explaining the reasoning (e.g., empirically sufficient for p≤151) or reference the freeze runtime measurement that justified it.

---

_Reviewed: 2026-07-22T04:33:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
