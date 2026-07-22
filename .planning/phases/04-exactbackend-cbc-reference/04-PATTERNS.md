# Phase 4: ExactBackend & CBC Reference - Pattern Map

**Mapped:** 2026-07-21
**Files analyzed:** 12 new (6 source, 5 test, 1 possibly-modified config)
**Analogs found:** 10 / 12 (2 files have no in-repo analog — patterns come from 04-RESEARCH.md verified code + `.planning/reference/alpha2-program-source.md` Appendix C)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/alpha2/solvers/__init__.py`, `src/alpha2/solvers/problems/__init__.py` | package init | — | `src/alpha2/corpus/__init__.py` (empty file) | exact |
| `src/alpha2/solvers/result.py` | model (Status enum + frozen ExactOutcome, stdlib-only) | immutable value objects | `src/alpha2/corpus/schema.py` (stdlib-only builder + raise-on-invalid) | role-match |
| `src/alpha2/solvers/backend.py` | interface (ExactBackend Protocol + registry, stdlib-only) | — | **none** — first Protocol in repo | no analog (use RESEARCH §Architecture) |
| `src/alpha2/solvers/problems/had2.py` | utility (pure combinatorial transform + checksum gate) | transform: (adj, n) → variable/conflict sets | `src/alpha2/generators/tfp.py` (module shape) + Appendix C.4 naive loops (semantics source) | role-match + reference |
| `src/alpha2/solvers/cbc.py` | service/adapter (the ONLY pulp importer) | request-response: problem → solve → status map → extraction | Appendix C.3 `ilp_had2` (byte-compat model source) + `src/alpha2/invariants/matching.py` (third-party confinement) | reference + role-match |
| `tests/test_solver_result.py` | test (pure unit, no solver) | — | `tests/test_schema_roundtrip.py` | role-match |
| `tests/test_had2_problem.py` | test (unit + naive-loop differential) | — | `tests/test_corpus_r2.py` (regenerate-from-seed gate) + Appendix C.4 naive loops (test-local reference) | role-match |
| `tests/test_cbc_backend.py` | test (fast integration: tiny solves, decision kills, `-O` canary) | — | `tests/test_schema_roundtrip.py` (synthetic instances) + `tests/test_verifier_dash_O.py` (subprocess `-O` canary) | role-match |
| `tests/test_cbc_status_honesty.py` | test (live timeout integration) | — | `tests/test_corpus_r3.py` (structure only) | partial |
| `tests/test_seed137_regression.py` | test (slow integration via trust root) | — | `tests/test_corpus_r3.py` (`slow` marker) + `src/alpha2/repro/seed137.py` (regen) + `tests/test_schema_roundtrip.py::_seed_record` (in-memory record) | exact (composite) |
| `.github/workflows/ci.yml` (possibly modified: extend `-O` step over one solver test) | config | — | itself (Phase 3, `03-04-SUMMARY.md`) | exact |

**Frozen files that must NOT be modified** (unless the planner explicitly fences the corpus-upgrade option per RESEARCH Open Question 1): `src/alpha2/corpus/{verifier,schema,store,manifest}.py`, `src/alpha2/verify/model.py`, `src/alpha2/repro/*.py`, `src/alpha2/generators/{tfp,cayley}.py`, `data/corpus/*`, `data/manifests/*`, `tests/test_corpus_r{1,2,3}.py`.

## Pattern Assignments

### `src/alpha2/solvers/result.py` (model, immutable value objects)

**Analog:** `src/alpha2/corpus/schema.py` — the repo's exemplar of a stdlib-only module that raises (never asserts) on invalid input.

**Core code:** RESEARCH already provides the full verified skeleton (04-RESEARCH.md lines 151–186: `Status` enum, `NotProvedOptimal`, frozen `ExactOutcome` with `__post_init__` invariants and the raising `exact_value()` accessor). Copy it verbatim; it is the design.

**Raise-not-assert discipline** — copy the refuse-invalid style from `src/alpha2/corpus/schema.py` lines 275–280:
```python
    had_2 = len(model_branch_sets)
    if had_2 < chi_G:
        raise ValueError(
            f"family size {had_2} < chi {chi_G}: the FULL had_2 family (len >= chi) "
            "must be stored; a truncated family is a rejected input, never a shortcut"
        )
```
`result.py`'s `__post_init__` guards use the same shape (`if cond: raise ValueError(...)`). Zero `assert` statements anywhere in the module (Pitfall 6).

**Module-docstring convention** — follow `src/alpha2/corpus/verifier.py` lines 1–24: state the trust-boundary contract in the docstring (stdlib-only; importable without pulp; why the accessor raises), and avoid grep-trigger tokens (the word "assert" in prose tripped Phase-2 grep guards — see 02-01-SUMMARY.md deviation 2).

---

### `src/alpha2/solvers/backend.py` (interface, no analog)

**No in-repo analog** — the repo has no Protocol/registry yet. Use `typing.Protocol` + a plain dict registry per 04-RESEARCH.md's structure and `.planning/research/ARCHITECTURE.md` Pattern 2. Keep it stdlib-only (`typing`, nothing else) so future battery code imports it without pulp. Docstring style: `corpus/verifier.py` lines 1–24.

---

### `src/alpha2/solvers/problems/had2.py` (utility, transform)

**Analog for module shape:** `src/alpha2/generators/tfp.py` — pure functions over `(adj: list[set[int]], n)`, no classes needed, section-comment headers.

**Module structure pattern** (`src/alpha2/generators/tfp.py` lines 1–11, 33–47): top docstring stating the contract, then plain functions taking `(adj, n)`:
```python
def triangle_free_process(n, rng):
    adj = [set() for _ in range(n)]
    ...
    return adj, m
```
`had2.py` follows the same convention: `enumerate_had2(adj, n)` and a `build_problem(adj, n)`-style entry returning plain data (the `Had2Problem`).

**Core enumeration:** copy the verified implementation from 04-RESEARCH.md lines 205–224 (`enumerate_had2`: G-edges, H-edge ss set, cherry sp set, C₄-diagonal pp set with `frozenset` dedup). Two load-bearing subtleties are documented at RESEARCH lines 227–231 (frozenset dedups the double C₄ discovery; triangle-freeness makes the enumeration total — re-assert it raise-based at build time).

**Structural checksum gate:** copy from 04-RESEARCH.md lines 370–379 verbatim (raise-based `ChecksumError`, degrees from `adj`, codegrees via `len(adj[u] & adj[v])`):
```python
deg = [len(adj[v]) for v in range(n)]
nss_expect = sum(deg) // 2
nsp_expect = sum(d * (d - 1) // 2 for d in deg)
npp_expect = sum(
    (c := len(adj[u] & adj[v])) * (c - 1) // 2
    for u in range(n) for v in range(u + 1, n)) // 2
if (len(ss), len(sp), len(pp)) != (nss_expect, nsp_expect, npp_expect):
    raise ChecksumError(...)
```
Regression constants (live-verified): seed-1 → (131, 998, 726); seed-137 → (177, 1913, 3782).

**Semantic byte-compat source (what the enumeration must be set-equal to):** the naive loops in `.planning/reference/alpha2-program-source.md` Appendix C.4 lines 516–534:
```python
npp = 0
for i in range(len(Gedges)):
    a, b = Gedges[i]
    for j in range(i + 1, len(Gedges)):
        c, d = Gedges[j]
        if len({a, b, c, d}) < 4: continue
        if c in adj[a] and d in adj[a] and c in adj[b] and d in adj[b]:
            prob += mvar[Gedges[i]] + mvar[Gedges[j]] <= 1; npp += 1
nsp = 0
for v in range(n):
    for (a, b) in Gedges:
        if v == a or v == b: continue
        if a in adj[v] and b in adj[v]:
            prob += svar[v] + mvar[(a, b)] <= 1; nsp += 1
nss = 0
for u in range(n):
    for v in adj[u]:
        if v > u:
            prob += svar[u] + svar[v] <= 1; nss += 1
```
These loops live ONLY as test-local reference code in `tests/test_had2_problem.py` (never a production path).

**Pitfall to document in the docstring** (RESEARCH Pitfall 5): pair variables exist only for G-edges — that IS the size-2 connectivity constraint; widening the variable index set silently admits disconnected branch sets.

---

### `src/alpha2/solvers/cbc.py` (service/adapter, request-response)

**Byte-compatibility source:** Appendix C.3 `ilp_had2`, `.planning/reference/alpha2-program-source.md` lines 394–402 — the variable naming, objective, and disjointness constraints the CBC model must reproduce:
```python
def ilp_had2(adj, n, chi, time_limit=300):
    import pulp
    Gedges = [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]
    prob = pulp.LpProblem("had2", pulp.LpMaximize)
    mv = {e: pulp.LpVariable(f"m_{e[0]}_{e[1]}", cat="Binary") for e in Gedges}
    sv = {v: pulp.LpVariable(f"s_{v}", cat="Binary") for v in range(n)}
    prob += pulp.lpSum(mv.values()) + pulp.lpSum(sv.values())
    for v in range(n):
        prob += pulp.lpSum(mv[e] for e in Gedges if v in e) + sv[v] <= 1
```
Keep the `m_{u}_{v}` / `s_{v}` names, `LpProblem("had2", LpMaximize)`, and the per-vertex disjointness row. The conflict rows come from `problems/had2.py`'s enumeration (proven set-equal to C.3/C.4's loops). What must NOT be copied from C.3: `pulp.value(prob.objective)` without a status gate (line 420), `int(round(val))` (line 422), and the `fam[:chi]` truncation in its caller (line 443) — these are exactly the soundness holes Phase 4 closes.

**Extraction shape** (keep, then guard): Appendix C.3 lines 423–424:
```python
    fam = [tuple(e) for e in Gedges if mv[e].value() and mv[e].value() > 0.5] + \
          [(v,) for v in range(n) if sv[v].value() and sv[v].value() > 0.5]
```
Wrap with: status gate first, integrality guard (each binary within 1e-6 of 0/1 else ERROR), objective recomputation (count of extracted == reported value else ERROR). Never truncate; the FULL family goes in `ExactOutcome.family`.

**Status mapping, invocation, bound parse, version probe:** copy verbatim from 04-RESEARCH.md Code Examples — CBC invocation + two-field gate (lines 341–355: `PULP_CBC_CMD(msg=0, threads=1, timeLimit=..., logPath=...)`; `proved_optimal = prob.status == pulp.LpStatusOptimal and prob.sol_status == pulp.LpSolutionOptimal`), `parse_bound` (lines 359–366), `cbc_binary_version` (lines 384–393).

**Third-party import confinement pattern** — copy from `src/alpha2/invariants/matching.py` lines 11–16 (the repo's precedent for confining a third-party library to one module, with the import inside the module that owns it):
```python
def matching_number(adj, n):
    import networkx as nx
    Hg = nx.Graph(); Hg.add_nodes_from(range(n))
    ...
```
`cbc.py` is the analogous sole owner of `import pulp`. Consider an AST guard test pinning this (see Shared Patterns → AST import-boundary guard).

**Decision mode** (RESEARCH Pattern 3): constant objective `prob += 0`, add `Σ mv + Σ sv >= target_k`; feasible → MODEL_FOUND, Infeasible → PROVED_INFEASIBLE, stopped → UNKNOWN. Optimize-mode Infeasible/Unbounded → ERROR (encoding bug), never PROVED_INFEASIBLE.

---

### `tests/test_solver_result.py` (unit test, no solver)

**Analog:** `tests/test_schema_roundtrip.py` — the repo's pure-unit style over a builder module.

**Refusal-test pattern** (`tests/test_schema_roundtrip.py` lines 212–224):
```python
def test_short_family_refused_never_truncated():
    # A family shorter than chi must RAISE (no fam[:chi], no silent truncation).
    with pytest.raises((ValueError, VerificationError)):
        build_record(
            provenance=provenance_seed("f", 5, 1, "p"),
            ...
        )
```
Same shape for: `exact_value()` raises `NotProvedOptimal` on every non-PROVED_OPTIMAL status; `__post_init__` rejects value≠None for UNKNOWN/ERROR and value≠bound for PROVED_OPTIMAL. Plus the exhaustive `(status, sol_status)` → `Status` mapping table test (all pairs from RESEARCH Pattern 1's table, lines 133–141) — feed the pure mapping function, no solver run.

---

### `tests/test_had2_problem.py` (unit + differential test)

**Analogs:** `tests/test_corpus_r2.py` (regenerate-H-from-seed then compare, gated on a structural invariant) + Appendix C.4 naive loops embedded test-local.

**Regenerate-from-seed pattern** (`tests/test_schema_roundtrip.py` lines 57–65 — the compact form):
```python
def _seed_record(seed, model, method, omega_G=None):
    n = 31
    adj, _ = triangle_free_process(n, random.Random(seed))
    H_edges = _h_edges(adj, n)
    ...
```
Use `triangle_free_process(31, random.Random(seed))` for seeds 1 and 137, then assert obstruction enumeration is SET-equal (not count-equal) to the test-local naive loops (Appendix C.4 lines 516–534, adapted to collect sets instead of adding constraints), and assert the checksum triples (131, 998, 726) / (177, 1913, 3782). Also: mutated-class test proving the checksum RAISES `ChecksumError` (not assert), and exhaustive brute-force had₂ for n ≤ 8 random triangle-free H.

**Literal-embedding discipline** (`tests/test_corpus_r1.py` lines 27–38): expected constants embedded as literals in the test file, no cross-test imports.

---

### `tests/test_cbc_backend.py` (fast integration test)

**Analogs:** `tests/test_schema_roundtrip.py::_synthetic_empty_h` (tiny closed-form instances) + `tests/test_verifier_dash_O.py` (the `-O` canary the solver path must join).

**Tiny synthetic instance pattern** (`tests/test_schema_roundtrip.py` lines 82–97):
```python
def _synthetic_empty_h(provenance):
    """A tiny fully verifiable record: H has no edges => G is complete K5. ..."""
    n = 5
    return build_record(provenance=provenance, H_edges=[], nu_H=0, chi_G=5,
        model_branch_sets=[[0], [1], [2], [3], [4]], matching_M=[], tutte_berge_U=[], ...)
```
Same closed-form spirit for the CBC panel: H=C₅ (had₂=3), H=empty (had₂=n), H=perfect matching; plus decision-mode kills at k=χ=16 on seed-1/seed-137 (~2.5 s each, live-verified) with families routed through `verify_certificate`.

**`-O` subprocess canary pattern** (`tests/test_verifier_dash_O.py` lines 25–55) — the extension over one solver-path test copies this exactly: a `textwrap.dedent` script that (a) exits 3 if `__debug__` is True (real branch, not an assert), (b) exercises a raise-based solver guard (e.g. `ChecksumError` on a mutated conflict set, or `NotProvedOptimal`), (c) exits 0 iff it raised; parent runs `[sys.executable, "-O", "-c", SCRIPT]` with `PYTHONPATH=src`:
```python
def test_verifier_fails_closed_under_dash_O():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run([sys.executable, "-O", "-c", SCRIPT],
                       env=env, cwd=str(REPO), capture_output=True)
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())
```
Also add the bound-parse fixture test here using the captured log grammar (`Result - Stopped on time limit` / `Objective value: 17.00000000` / `Upper bound: 20.879` — RESEARCH Pattern 3).

---

### `tests/test_cbc_status_honesty.py` (live timeout integration)

**Partial analog:** no existing test runs a solver. Structure follows plain pytest with `pytest.raises`. The one live test (RESEARCH line 188): solve seed-137 optimize with a short `timeLimit`, assert `outcome.status in {Status.INCUMBENT_ONLY, Status.UNKNOWN}` (accept EITHER — which one depends on whether CBC found the incumbent in time), and `pytest.raises(NotProvedOptimal)` on `outcome.exact_value()`. Regenerate H via the `_seed_record`-style pattern above (`triangle_free_process(31, random.Random(137))`).

---

### `tests/test_seed137_regression.py` (slow integration via trust root)

**Composite of three exact analogs:**

**1. `slow` marker + never-touch-repo-corpus** (`tests/test_corpus_r3.py` lines 84–91):
```python
@pytest.mark.slow
def test_r3_replay_tfp_pinned(tmp_path):
    """Replay the baseline (31,1) instance into tmp_path; byte-identical to committed."""
    target = _find_seed(_committed_records(), 31, 1)
    corpus = tmp_path / "tfp_replay.json"
    baseline.run_instance(31, 1, str(corpus))
    assert str(corpus) != str(paths.CORPUS), "R3 must never touch the repo corpus"
```
The `slow` marker is already registered (`pyproject.toml` line 26: `markers = ["slow: release/nightly replay gate"]`) — register nothing new. The Phase-4 regression needs no corpus file at all: the record stays in memory.

**2. Regeneration + invariants** (`src/alpha2/repro/seed137.py` lines 44–48 — read-only analog; do NOT modify this frozen driver):
```python
    rng = random.Random(137)
    adj, m = triangle_free_process(31, rng)        # regenerate H only; do NOT call solve
    nu = matching_number(adj, 31)
    chi = 31 - nu
    M, U, nu2 = extract_witness(adj, 31)           # emission-time witness (verifier re-checks)
```

**3. In-memory record through the trust root** (`src/alpha2/repro/seed137.py` lines 49–59, minus the store call; identical shape in `tests/test_schema_roundtrip.py::_seed_record` lines 61–79):
```python
    H_edges = sorted([min(u, v), max(u, v)] for u in range(31) for v in adj[u] if u < v)
    rec = schema.build_record(
        provenance=schema.provenance_seed(
            "triangle_free_process_complement", 31, 137,
            "Bohman uniform triangle-free process"),
        H_edges=H_edges, nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in family],   # the CBC 17-set family
        matching_M=M, tutte_berge_U=U,
        method="exact ILP (CBC): had_2(G)=17", omega_G=14, verified=True,
    )
    k = verify_certificate(rec)                        # trust root arbitrates; k == 17
```
(`schema.build_record` derives `had_2 = len(model_branch_sets)` and supports k ≥ χ with no changes — `schema.py` lines 275–280, 294.)

**Assertions:** `status == PROVED_OPTIMAL`, `exact_value() == 17`, `bound == 17`, `len(family) == 17`, `verify_certificate(rec) == 17`; metamorphic check `17 > 16 == len(stored D.3 family)` against the committed corpus record (find it with the `_find_seed_record` helper pattern, `tests/test_corpus_r1.py` lines 55–64). Assert on value/status/verifiability, never on model bytes (RESEARCH Assumption A1).

---

### `.github/workflows/ci.yml` (possibly modified)

Existing workflow already gains the seed-137 slow test automatically via the release-gate's `-m slow` selector (03-04-SUMMARY.md) — no change needed for that. The only candidate edit is extending the every-commit `python -O` canary step to include one solver-path test (RESEARCH line 188 / Pitfall 6), mirroring the existing step:
`uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q` → append the solver `-O` test. Keep both action SHA pins untouched.

## Shared Patterns

### Raise-based guards, never assert (all new solver modules)
**Source:** `src/alpha2/corpus/verifier.py` lines 57–67 (representative):
```python
        if len(e) != 2:
            raise VerificationError(f"malformed H_edge {e!r} (len != 2)")
        ...
        if (u, v) in seen:
            raise VerificationError(f"duplicate H_edge {e!r}")
```
**Apply to:** `result.py` (`NotProvedOptimal`, `ValueError`), `had2.py` (`ChecksumError`, triangle-free re-assert), `cbc.py` (integrality/recompute/encoding → ERROR paths). Impossibility-adjacent checks must survive `python -O`; zero `ast.Assert` in these modules.

### Trust-root routing (solver output is an UNTRUSTED proposal)
**Source:** `src/alpha2/repro/baseline.py` lines 43–58 (the driver emission tail) and `src/alpha2/corpus/verifier.py` lines 213–231 (`verify_certificate` = the single combined entry point, returns k, raises on any defect).
**Apply to:** `test_cbc_backend.py` (decision-mode families), `test_seed137_regression.py`. No solver-side "verified" flag ever confers truth; only `verify_certificate` does. All frozen trust primitives are consumed, never edited.

### stdlib-only trust boundary + third-party confinement
**Source:** `src/alpha2/corpus/schema.py` lines 175–184 (`importlib.metadata.version` — read a version without importing the package) and `src/alpha2/invariants/matching.py` lines 11–16 (third-party import confined to the owning module).
**Apply to:** `result.py`, `backend.py`, `problems/had2.py` (stdlib-only — importable without pulp); `cbc.py` (sole pulp importer). Backend version string: `cbc_binary_version()` subprocess probe (RESEARCH lines 384–393) → `"pulp==3.3.2 / CBC 2.10.3"` in `ExactOutcome.backend_version`; `schema.make_backends`/`_cbc_under_rosetta` (schema.py lines 187–223) stay untouched and already stamp platform honestly.

### AST import-boundary guard (optional but on-pattern)
**Source:** `tests/test_verifier_isolation.py` lines 17–49 — parse the module with `ast`, allow-list imports, count `ast.Assert` == 0, count raises ≥ N.
**Apply to:** a guard pinning `import pulp` to `solvers/cbc.py` only and zero asserts in `solvers/{result,problems/had2}.py` — the same mechanism that pins networkx to `matching.py` (CHI-01) and stdlib-only to `verifier.py`. Caution from 02-01/03-02 summaries: keep grep-trigger tokens ("assert", "networkx", "ilp_had2", "pulp") out of docstring prose in guarded modules.

### `slow` marker / CI tiering
**Source:** `tests/test_corpus_r3.py` line 84 (`@pytest.mark.slow`), `pyproject.toml` line 26 (marker registered).
**Apply to:** `test_seed137_regression.py` only (~149 s optimize). Everything else (decision kills ~2.5 s, tiny closed-form, brute force n≤8, mapping units) stays in the every-commit tier.

### Embedded literals, no cross-test imports
**Source:** `tests/test_corpus_r1.py` lines 26–38 (`D2_MODEL`, `D3_MODEL` as in-file literals).
**Apply to:** checksum constants (131/998/726, 177/1913/3782), the captured CBC log fixture text, seed-137 expected value 17, D.3 16-set literal for the metamorphic comparison.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/alpha2/solvers/backend.py` | interface | — | No Protocol/registry exists in the repo; use RESEARCH §Recommended Project Structure + ARCHITECTURE.md Pattern 2 |
| `tests/test_cbc_status_honesty.py` (live-timeout leg) | test | — | No existing test invokes a solver or a timeout; RESEARCH line 188 specifies the test design (accept INCUMBENT_ONLY or UNKNOWN; `exact_value()` raises) |

## Metadata

**Analog search scope:** `src/alpha2/**` (all 23 modules), `tests/**` (all 13 test files), `.planning/reference/alpha2-program-source.md` (Appendix C.3 lines 394–425, C.4 lines 508–563), `pyproject.toml`, Phase 2/3 SUMMARYs.
**Files scanned:** 15 read in full (all ≤ 310 lines; single-pass reads).
**Byte-compatibility anchor:** Appendix C.3 `ilp_had2` (reference md lines 394–425) is THE source for the CBC model shape (variable names, objective, disjointness rows); Appendix C.4 loops (lines 516–534) are THE test-local naive reference for constraint set-equality. C.3/C.4's status-free objective read and `fam[:chi]` truncation are the anti-patterns this phase makes unrepresentable.
**Pattern extraction date:** 2026-07-21
