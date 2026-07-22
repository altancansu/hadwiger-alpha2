---
phase: 01-pinned-environment-verbatim-port
reviewed: 2026-07-22T01:27:05Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - src/alpha2/paths.py
  - src/alpha2/__init__.py
  - src/alpha2/generators/__init__.py
  - src/alpha2/invariants/__init__.py
  - src/alpha2/search/__init__.py
  - src/alpha2/verify/__init__.py
  - src/alpha2/repro/__init__.py
  - src/alpha2/generators/tfp.py
  - src/alpha2/invariants/matching.py
  - src/alpha2/search/heuristic.py
  - src/alpha2/verify/model.py
  - src/alpha2/repro/baseline.py
  - tests/test_fingerprint.py
  - tests/test_chi_no_estimate.py
  - pyproject.toml
  - data/manifests/fingerprint.json
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: clean
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-22T01:27:05Z
**Depth:** standard
**Files Reviewed:** 13 source files (+ pyproject.toml, fingerprint.json)
**Status:** clean (no Critical findings; 2 Warnings, 2 Info)

## Summary

This phase claims a byte-verbatim port of the Appendix C toolkit into `src/alpha2`, plus glue (`paths.py`, `pyproject.toml`, package wiring) and a two-tier fingerprint/guard test suite. I independently re-derived and checked this claim rather than trusting the SUMMARY:

- **AST-diffed every ported function** (`RandomSet`, `triangle_free_process`, `is_triangle_free`, `is_edge_maximal_tf`, `matching_number`, `is_conflict` (both copies), `full_conflicts`, `update_conflicts`, `initial_state`, `assignments`, `valid_groups`, `cand_energy`, `solve`, `verify_model`, `run_instance`, `main`) against the Appendix C source extracted from `.planning/reference/alpha2-program-source.md`. All match exactly at the AST level — **no algorithmic deviation found**.
- **Regenerated n=31/seed=1 and n=31/seed=137 on the actual pinned `.venv` (CPython 3.12.13)** and independently: matched `m=131/nu=15/chi=16/tf=True/maxTF=True` and the frozen `h_edges_sha256` in `data/manifests/fingerprint.json` for both instances, byte-for-byte. Also confirmed the heuristic reproduces the Appendix D.2 K16 model exactly under the single-RNG contract, and that `verify_model` accepts it.
- **Ran the full pinned suite** (`.venv/bin/python -m pytest -q`) — 8/8 pass.
- **Mutation-tested `test_chi_no_estimate.py`'s AST guard**: injected a `nx.greedy_color(...)` call into a scratch copy of `matching.py` — the guard correctly failed. Confirmed **not vacuously green**.
- **Verified `paths.py`'s `parents[2]` arithmetic** resolves to the true repo root at runtime, and that `uv.lock` pins agree with `pyproject.toml`'s exact version pins (networkx 3.6.1 / pulp 3.3.2 / ortools 9.15.6755).

Given the algorithm bodies are proven byte-identical to Appendix C by direct AST comparison (not just SUMMARY assertion), no findings are raised against the ported bodies themselves per the review scope. Findings below are limited to the glue code and test-suite robustness, as instructed.

## Warnings

### WR-01: Trust-root verifier is entirely `assert`-based and silently no-ops under `python -O`

**File:** `src/alpha2/verify/model.py:23-38`
**Issue:** `verify_model` — the project's stated "trust root" ("nothing counts as found until the independent verifier passes") — implements every check (disjointness, size validity, in-range indices, G-edge membership, full pairwise adjacency) as a bare `assert`. CPython strips all `assert` statements when run with `-O`/`-OO` or `PYTHONOPTIMIZE` set. Under those conditions `verify_model` degrades to `return True` unconditionally for *any* input, including a garbage/adversarial model — i.e. the trust root becomes a rubber stamp with zero indication anything changed. This is a real, currently-unmitigated risk to the epistemic-integrity core value of the project, not a hypothetical: nothing in the current test suite or driver guards against accidental `-O` invocation (no `assert __debug__`-style canary, no `sys.flags.optimize` check, no test that runs the verifier under `-O` and expects a failure/guard). The module's own docstring acknowledges this ("hardening to explicit exceptions / a `python -O` canary is Phase 2, not now") — so it is tracked, but it is real and currently open, not merely hypothetical.
**Fix:** Not required to close in Phase 1 (explicitly deferred), but flagging as it directly threatens the "verifier is the trust root" invariant. When addressed, prefer either explicit `if not (...): raise VerificationError(...)` checks (survives `-O`) or a startup guard that refuses to import/run the verifier module when `sys.flags.optimize > 0` / `not __debug__`:
```python
if not __debug__:
    raise RuntimeError("verify_model requires assertions enabled; refusing to run under python -O")
```

### WR-02: `verify_model`'s disjointness check can mask the specific defect it's diagnosing

**File:** `src/alpha2/verify/model.py:28-30` (also present verbatim in `search/heuristic.py`'s proposer path — inherited, not introduced)
**Issue:** Empirically confirmed during review: a corrupted/adversarial branch-set model that reuses a vertex already assigned elsewhere raises `"branch sets not disjoint"` even when the more specific/interesting defect (e.g., a genuinely non-adjacent pair) would also have applied to a *different* mutation. This isn't a logic bug — the assertion order (disjointness before adjacency) is correct and matches Appendix C exactly — but it means the AssertionError message alone cannot be trusted to characterize *which* invariant a given malformed model actually violates without inspecting all of them; a caller catching `AssertionError` generically and logging only the message risks under-diagnosing corpus corruption. This is a minor diagnostic-quality issue in the (deferred) hardening path, not a phase-1 blocker; it is verbatim from Appendix C so no fix is warranted in this phase, but worth carrying into the Phase 2 exception-hardening design (multiple violated invariants should ideally all be reported, not just the first).
**Fix:** Defer to Phase 2 hardening (per WR-01) — when converting to explicit exceptions, consider collecting all violated invariants rather than raising on the first.

## Info

### IN-01: `test_chi_no_estimate.py`'s AST guard uses a fixed substring ban-list, leaving a residual gap for differently-named estimate paths

**File:** `tests/test_chi_no_estimate.py:26-29, 83-112`
**Issue:** The guard's negative checks (`BANNED_CALL_SUBSTRINGS = ("color", "chromatic", "estimate")`, `BANNED_IMPORT_SUBSTRINGS = ("color", "chromatic", "approximation")`) are name-based. I confirmed by mutation test that the guard *is* effective against the concrete threat model documented (a `greedy_color`/coloring-module estimate), and that any direct `nx.<attr>(...)` call not on the `ALLOWED_NX_ATTRS` allow-list is independently caught regardless of its name (this second check is name-agnostic and closes most of the gap). The residual gap is narrow: a hand-rolled, purely local function (no networkx call, e.g. a private helper named something outside the ban-list that computes an upper bound heuristically) would not trip either check. Given this is deliberately scoped as a mechanism guard (not a full taint-tracking system) and the positive assertion (`matching_has_blossom`) guarantees the real exact path exists and is used, this is acceptable for Phase 1 but worth noting for anyone relying on this guard as an airtight barrier in later phases when more code lands in `src/alpha2`.
**Fix:** No action required now; consider tightening later (e.g., a positive allow-list of every function defined in `src/alpha2/invariants/matching.py` combined with an assertion that `chi` is computed nowhere else, rather than a negative name ban) if `src/` grows.

### IN-02: `ruff` `extend-exclude` omits `verify/model.py` and `invariants/matching.py` despite both carrying byte-identical-preservation intent

**File:** `pyproject.toml:27-34`
**Issue:** `extend-exclude` only lists `generators/tfp.py` and `search/heuristic.py` — the two modules whose docstrings explicitly warn "Do NOT reformat... do NOT run `ruff --fix`/format." `verify/model.py` carries a private byte-identical copy of `is_conflict` that the docstring says "must be preserved," and `invariants/matching.py` is the sole CHI-01 path, but neither is in the ruff exclusion list. In practice this is likely low-risk (neither module's correctness depends on line-level formatting the way `tfp.py`'s `RandomSet` layout or `heuristic.py`'s `tuple(conf)[rng.randrange(...)]` idiom do — I verified `is_conflict`'s logic is order-independent, only membership tests, not set-iteration order), but it is an inconsistency between the stated "byte-identical" intent in the docstrings and the tooling that's supposed to enforce it. A future `ruff format .` (not just `--fix`) run would be free to reformat these two files without any lint signal.
**Fix:** For consistency with the stated intent, consider adding both files to `extend-exclude`, or explicitly documenting in the docstrings that these two modules are content-verbatim (not formatting-verbatim) so the narrower ruff scope is intentional.

---

_Reviewed: 2026-07-22T01:27:05Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
