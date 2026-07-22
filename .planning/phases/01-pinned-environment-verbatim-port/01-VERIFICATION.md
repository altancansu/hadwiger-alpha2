---
phase: 01-pinned-environment-verbatim-port
verified: 2026-07-22T01:20:11Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 1: Pinned Environment & Verbatim Port Verification Report

**Phase Goal:** The Appendix C toolkit runs from the repo on a pinned, reproducible interpreter, byte-identical to the historical corpus lineage — the only code changes are paths and imports.
**Verified:** 2026-07-22T01:20:11Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `uv sync` on a clean checkout reproduces the locked environment (CPython 3.12.x exact patch, networkx 3.6.1, `pulp==3.3.2` hard-pin, ortools 9.15.6755, nauty 2.9.3, pynauty 2.8.8.1) from a committed lockfile; system Python 3.9.6 never touched | VERIFIED | Ran `uv sync` fresh: resolved CPython 3.12.13, `networkx.__version__ == 3.6.1`. `uv.lock` (committed) pins `networkx==3.6.1`, `ortools==9.15.6755`, `pulp==3.3.2`, `pynauty==2.8.8.1` (marker `extra == 'nauty'`). `pyproject.toml` hard-pins `pulp==3.3.2` in core deps; pynauty is correctly an optional `[nauty]` extra (not core), matching research Assumption A2. `/usr/bin/python3 --version` still reports `3.9.6` (untouched). nauty 2.9.3 (the `geng` binary) is documented in CLAUDE.md as a brew install, correctly NOT lockable via uv — no Phase-1 test exercises `geng`, consistent with the plan's explicit scope carve-out. |
| 2 | The corpus-fingerprint test passes: regenerating n=31 seed=1 from the repo yields `\|E(H)\|=131`, ν=15, χ=16 with stored `H_edges` byte-exact against the Appendix D exemplar | VERIFIED | `uv run pytest -q` → `8 passed in 0.07s` (full suite, includes `test_invariants`, `test_golden_hash`, `test_stored_model_reverifies`, `test_heuristic_reproduces`, `test_heuristic_matches_d2_exact_pinned_env`, `test_seed137_h_only`, `test_env_smoke`, `test_chi_no_estimate`). Independently re-derived (outside pytest) via a fresh Python one-liner: `triangle_free_process(31, random.Random(1))` → m=131, matching_number=15, chi=16, tf=True, maxTF=True; canonical `H_edges` sha256 = `3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2`, which equals the frozen golden in `data/manifests/fingerprint.json` and equals the manifest's `tfp:n31:s1.h_edges_sha256` field. The manifest's `m/nu/chi` (131/15/16) match Appendix D.2 exactly, and per the SUMMARYs and `tests/test_fingerprint.py` source, the freeze was gated: the doc-derived invariants (131/15/16/tf/maxTF) are asserted (`test_invariants`) as a precondition before the hash is trusted in `test_golden_hash`, and the manifest is loaded (not duplicated) — the golden freeze cannot self-certify a porting bug. |
| 3 | The toolkit lives in a repo-relative src-layout package (no `/mnt` paths), split library + thin entry, reference algorithms unchanged — the n=31 seed=1 K₁₆ model matches Appendix D | VERIFIED | `src/alpha2/` is a src-layout package (`generators/`, `invariants/`, `search/`, `verify/`, `repro/`, `paths.py`), confirmed by `pyproject.toml`'s `packages = ["src/alpha2"]` (hatchling). `grep -RnE "/mnt" src/ tests/ data/` finds zero path literals — the only two hits repo-wide are docstring prose in `paths.py` and `baseline.py` describing the *historical* sandbox path being replaced, not an actual path value. A function-by-function AST-derived byte comparison of every ported function/class (`RandomSet`, `triangle_free_process`, `is_triangle_free`, `is_edge_maximal_tf`, `matching_number`, `is_conflict`×2, `full_conflicts`, `update_conflicts`, `initial_state`, `assignments`, `valid_groups`, `cand_energy`, `solve`, `verify_model`, `run_instance`) against Appendix C.1 in `.planning/reference/alpha2-program-source.md` shows byte-identical bodies. Only `main()` differs, and only in the one sanctioned line: `path = "/mnt/user-data/outputs/..."` → `path = paths.ensure_parent(paths.CORPUS)` — exactly the paths-and-imports-only change the plan mandated. Independently re-verified: the stored Appendix D.2 K16 model (`[[16,20],[14,3],...]`) passes `verify_model(D2_MODEL, adj, 31, 16)` against a freshly regenerated H (not from cached/stored output). |
| 4 | χ(G) is computed only as n − ν(H) via Edmonds blossom (values asserted by the fingerprint test); no estimate exists anywhere in control flow | VERIFIED | `tests/test_chi_no_estimate.py::test_chi_no_estimate` is a genuine AST mechanism guard (Call/Import node inspection, not text grep) that (a) forbids any Call target containing "color"/"chromatic"/"estimate", (b) forbids importing any coloring/approximation/chromatic module, (c) confines all `nx.*` calls in `src/` to an allow-list `{Graph, add_nodes_from, add_edges_from, max_weight_matching}`, and (d) positively asserts `max_weight_matching(..., maxcardinality=True)` exists only in `invariants/matching.py`. I independently proved this guard is non-vacuous: injected a fake `nx.greedy_color(...)` call into `matching.py`, re-ran the guard — it FAILED with `forbidden chromatic-estimate call \`greedy_color\``; reverted the file (`git diff` confirmed clean) and re-ran — GREEN again. `matching.py` itself imports networkx locally and is the sole module that does so (`grep -RniE "import networkx" src/alpha2/generators/tfp.py` → no hits). |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | uv project, hard pins, src-layout | VERIFIED | `requires-python = ">=3.12,<3.13"`; `pulp==3.3.2` hard pin; `nauty`/`dev` optional groups; hatchling `packages = ["src/alpha2"]`; `pythonpath=["src"]`. |
| `.python-version` | `3.12.13` | VERIFIED | File contains exactly `3.12.13`. |
| `uv.lock` | committed lockfile pinning exact versions | VERIFIED | Present, committed, greps confirm `networkx 3.6.1`, `ortools 9.15.6755`, `pulp 3.3.2`, `pynauty 2.8.8.1`. |
| `src/alpha2/generators/tfp.py` | RandomSet + tfp + tf checks, verbatim | VERIFIED | Byte-identical to Appendix C.1 (programmatic diff, exact match). |
| `src/alpha2/invariants/matching.py` | matching_number, sole chi path | VERIFIED | Byte-identical; sole `max_weight_matching` call site (AST-enforced). |
| `src/alpha2/search/heuristic.py` | full heuristic cluster, verbatim | VERIFIED | Byte-identical to Appendix C.1 (all 8 functions). |
| `src/alpha2/verify/model.py` | verify_model + private is_conflict, no search import | VERIFIED | Byte-identical; zero import statements in the file (confirmed via grep — no `from`/`import` lines at all). |
| `src/alpha2/repro/baseline.py` | run_instance + main, repo-relative output | VERIFIED | `run_instance` byte-identical; `main()` differs only in the sanctioned `/mnt/...` → `paths.CORPUS` substitution. End-to-end run produces `data/corpus/hadwiger_alpha2_certificates.json` with n=31 s=1 record: `verified=True, chi_G=16, matching_number_H=15, len(H_edges)=131`. |
| `src/alpha2/paths.py` | single source of repo-relative CORPUS path | VERIFIED | `CORPUS = REPO_ROOT/"data"/"corpus"/"hadwiger_alpha2_certificates.json"`; `ensure_parent` helper. |
| `data/manifests/fingerprint.json` | frozen golden fixture (gated) | VERIFIED | `tfp:n31:s1` (m/nu/chi/sha256) + `tfp:n31:s137` (m/sha256) present; sha256 for s1 matches independently-recomputed value. |
| `tests/test_fingerprint.py` | two-tier fingerprint suite | VERIFIED | 7 test functions present and passing (invariants, golden hash, stored-model reverify, heuristic-reproduces, heuristic-exact-match, seed137, env-smoke). |
| `tests/test_chi_no_estimate.py` | CHI-01 AST mechanism guard | VERIFIED | Present, passing, and independently proven non-vacuous (see Truth 4 evidence). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `invariants/matching.py` | `networkx.max_weight_matching` | `nx.max_weight_matching(Hg, maxcardinality=True)` | WIRED | AST-confirmed unique call site with `maxcardinality=True` literal. |
| `repro/baseline.py` | `paths.py` | `paths.ensure_parent(paths.CORPUS)` | WIRED | Confirmed in source; end-to-end run wrote to `data/corpus/...` (repo-relative), not `/mnt`. |
| `tests/test_fingerprint.py` | `generators/tfp.py` | regenerate + assert invariants | WIRED | `test_invariants`, `test_golden_hash` import and call `triangle_free_process`; both pass. |
| `tests/test_fingerprint.py` | `data/manifests/fingerprint.json` | load frozen hash, no duplicate literal | WIRED | `_load_manifest()` reads the file; `test_golden_hash` compares against the loaded value, not a hardcoded second copy. |
| `verify/model.py` | (no import from `search`) | trust-root boundary | WIRED (negatively confirmed) | Zero import statements in the file; the module is fully self-contained with its own private `is_conflict`. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green | `uv run pytest -q` | `8 passed in 0.07s` | PASS |
| Clean `uv sync` selects pinned interpreter | `uv sync && uv run python -c "..."` | `3.12.13` / `3.6.1` | PASS |
| System Python untouched | `/usr/bin/python3 --version` | `Python 3.9.6` | PASS |
| Baseline driver runs end-to-end (12 instances) | `uv run python -m alpha2.repro.baseline` | `ALL INSTANCES VERIFIED`; n=31 s=1 record verified=True, chi_G=16 | PASS |
| Golden hash reproduces independently (outside pytest) | ad hoc Python one-liner recomputing sha256 | matches `3c953d90…41e2` | PASS |
| D.2 model reverifies against fresh H (outside pytest) | ad hoc `verify_model(D2_MODEL, adj, 31, 16)` | `True` | PASS |
| CHI-01 guard is non-vacuous | inject `nx.greedy_color`, rerun guard, revert | guard FAILED as expected, then PASSED after clean revert | PASS |
| No `/mnt` path literals anywhere in code | `grep -RnE "/mnt" src/ tests/ data/` | 2 hits, both docstring prose describing the historical path, not literal path values | PASS |
| No debt markers / stubs in phase-modified files | `grep -RnE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` etc. across `src/`, `tests/` | zero hits | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ENV-01 | 01-01, 01-02 | Pinned uv-managed CPython 3.12.x, all deps version-locked, committed lockfile reproduces env | SATISFIED | `uv sync` reproduces 3.12.13/networkx 3.6.1 from committed `uv.lock`; `test_env_smoke` passes; system 3.9.6 untouched. |
| ENV-02 | 01-01, 01-02 | Appendix C ported into repo-relative package (no `/mnt`), deterministic, library+CLI split, algorithms unchanged | SATISFIED | Programmatic byte-diff confirms verbatim bodies; `/mnt` grep clean; single-RNG contract preserved in `run_instance`. |
| ENV-03 | 01-01, 01-02 | Corpus-fingerprint test asserts canonical generator invariants (n=31 s=1 → 131/15/16) | SATISFIED | `test_invariants`, `test_golden_hash`, `test_stored_model_reverifies` all green and independently re-derived. |
| CHI-01 | 01-01, 01-02 | χ(G) = n − ν(H) exact via Edmonds blossom, no estimates anywhere | SATISFIED | AST mechanism guard (`test_chi_no_estimate`) passes and was proven non-vacuous by fault injection. |

No orphaned requirements: REQUIREMENTS.md traceability table maps exactly ENV-01, ENV-02, ENV-03, CHI-01 to Phase 1, all four appear in both plans' `requirements:` frontmatter, and REQUIREMENTS.md itself has been updated to `[x]` for ENV-01/ENV-02/CHI-01 (ENV-03 checkbox in REQUIREMENTS.md is still `[ ]` — a stale checkbox, not a functional gap; the roadmap traceability table correctly shows ENV-03 status "Pending" too, which is a documentation lag, not a code gap — see note below).

### Anti-Patterns Found

None. Scanned all `src/alpha2/**/*.py` and `tests/*.py` for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER`, placeholder/coming-soon prose, and empty-body stub patterns (`return null`, `return {}`, `return []`, `=> {}`) — zero hits. Working tree is clean (`git status --short` empty) after all verification probes (including the fault-injection test) were reverted.

### Deviations Reported by Executors — Sanity-Checked

1. **Docstring rewording (Wave 1, `invariants/matching.py` / `verify/model.py`)** — Confirmed via full-body byte comparison against Appendix C.1 that the function/class bodies are unaffected; only newly-added module-level docstrings (which did not exist in the original single-file script) were reworded to avoid tripping the CHI-01 static guard on their own prose. The original inline comment `# ---------- exact chromatic number of G = complement(H) ----------` is preserved byte-for-byte in `matching.py`. No behavioral change.
2. **Single-RNG contract for the exact-match test** — Verified against Appendix C.1's own `run_instance`: the reference source itself does `rng = random.Random(seed)` once, then feeds that same `rng` into `triangle_free_process(n, rng)` and later `solve(adj, n, chi, rng)` — i.e., the "single-RNG contract" is not an invented shortcut but a faithful reproduction of the reference driver's own behavior. `01-RESEARCH.md` documents this as "Contract v1, frozen" and confirms it reproduces Appendix D.2 exactly on both CPython 3.9.6 and 3.12.13. This is not a hack to force a pass; it is the verbatim-preserved reference contract.

### Human Verification Required

None. All four success criteria and their supporting artifacts/links were verifiable programmatically (env resolution, test execution, AST static analysis, byte-diff comparison, and fault-injection non-vacuity check). No visual, UX, or external-service-dependent behavior exists in this phase.

### Gaps Summary

No gaps. One minor documentation inconsistency was observed (not a code/functional gap): `.planning/REQUIREMENTS.md`'s ENV-03 checkbox and the roadmap traceability table both still show ENV-03 as unchecked/"Pending" even though ROADMAP.md's own Progress table marks Phase 1 "Complete" with both plans checked off, and the SUMMARYs list `ENV-03` under `requirements-completed`. This is a stale-checkbox bookkeeping item in planning docs, not a functional deficiency in the codebase — the ENV-03 fingerprint test itself is implemented, green, and independently re-verified above. Recommend a documentation touch-up in a future planning pass; it does not block Phase 2.

---

*Verified: 2026-07-22T01:20:11Z*
*Verifier: Claude (gsd-verifier)*
