# Phase 3: Corpus Reproduction & CI (First Blood) - Pattern Map

**Mapped:** 2026-07-21
**Files analyzed:** 13 new/modified
**Analogs found:** 11 with in-repo analogs / 13 total (2 have no in-repo analog: `ci.yml`, and the raw `certificates.json` which is store output not hand-authored)

> **Phase-3 stance (from RESEARCH):** this is a *composition + freezing* phase. Every trust/algorithmic primitive already exists and is adversarially proven. New code = 1 verbatim generator port (`cayley.py`), 1 manifest builder, 4 thin repro drivers, 3 R-tests, 1 CI workflow, and a `pyproject.toml` tweak. **Any new verification, hashing, or storage logic is a red flag** — reuse the analogs below verbatim.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/alpha2/generators/cayley.py` | generator | transform (deterministic, RNG-injected) | `src/alpha2/generators/tfp.py` | exact (same role + verbatim-port pattern) |
| `src/alpha2/corpus/manifest.py` | persistence/config | batch (hash-freeze) | `src/alpha2/corpus/schema.py` (`h_edges_sha256`) + `data/manifests/fingerprint.json` | role-match |
| `src/alpha2/repro/baseline.py` (FINALIZE) | orchestration/driver | batch (regen→verify→store) | itself (current) + MVP slice in `schema.py` docstring path | exact |
| `src/alpha2/repro/sweep.py` | orchestration/driver | batch | `src/alpha2/repro/baseline.py` | exact (same role + data flow) |
| `src/alpha2/repro/cayley_run.py` | orchestration/driver | batch | `src/alpha2/repro/baseline.py` + Appendix C.3 `run()` | exact |
| `src/alpha2/repro/seed137.py` | orchestration/driver | batch (literal-carry) | `src/alpha2/repro/baseline.py` | role-match (no search/solver) |
| `data/manifests/corpus-v1.manifest.json` | data/config | batch | `data/manifests/fingerprint.json` | exact |
| `data/corpus/hadwiger_alpha2_certificates.json` | data (store output) | — | (produced by `store.append_certificate`) | n/a — not hand-authored |
| `tests/test_corpus_r1.py` | test | request-response (verify) | `tests/test_fingerprint.py::test_stored_model_reverifies` + RESEARCH R1 example | role-match |
| `tests/test_corpus_r2.py` | test | transform (regen→hash) | `tests/test_fingerprint.py::test_golden_hash` | exact |
| `tests/test_corpus_r3.py` | test | batch (replay) | `tests/test_fingerprint.py::test_heuristic_matches_d2_exact_pinned_env` | role-match |
| `.github/workflows/ci.yml` | config/CI | event-driven (on push/PR) | (none in repo) | **no analog** — use RESEARCH Code Examples |
| `pyproject.toml` (MODIFY) | config | — | itself (current `[tool.ruff]` / `[tool.pytest.ini_options]`) | exact |

---

## Pattern Assignments

### `src/alpha2/generators/cayley.py` (generator, transform)

**Analog:** `src/alpha2/generators/tfp.py` (structure/discipline) + Appendix C.3 lines 363–391 (verbatim bodies).

**What to copy:** the module-header determinism warning and RNG-injected signature style from `tfp.py`; the *bodies* of `can_add` / `random_maximal_symmetric_sumfree` / `cayley_adj` byte-verbatim from C.3. `rng` is a parameter, never a global — same as `triangle_free_process(n, rng)`.

**Determinism-warning header pattern** (`generators/tfp.py` lines 1–11) — reuse verbatim, retargeting to C.3:
```python
"""... Verbatim port of the generation core from Appendix C.3 (cayley_test.py).
Bodies are byte-identical to the reference source; only the module location changed.

Determinism note: byte-reproduction depends on CPython set-iteration order AND
rng.shuffle order. Do NOT reformat, reorder comprehensions, or alter loop layout.
Do NOT run `ruff --fix`/format on this module (it is excluded in pyproject.toml).
"""
```

**RNG-injected signature pattern** (`generators/tfp.py` line 33 — `def triangle_free_process(n, rng)`): the Cayley entry takes `rng` explicitly; `random_maximal_symmetric_sumfree(p, rng)` calls `rng.shuffle(elems)` (C.3 line 379). Never seed inside the generator.

**Verbatim bodies to port** (Appendix C.3 lines 363–391):
```python
def can_add(S, p, a):
    b = (-a) % p
    T = S | {a, b}
    for u in (a, b):
        for x in T:
            if (u + x) % p in T:      # u + x = z violation
                return False
            if (u - x) % p in T:      # x + (u-x) = u violation
                return False
    return True

def random_maximal_symmetric_sumfree(p, rng):
    S = set(); elems = list(range(1, p))
    changed = True
    while changed:
        changed = False
        rng.shuffle(elems)
        for a in elems:
            if a in S: continue
            if can_add(S, p, a):
                S.add(a); S.add((-a) % p); changed = True
    return S

def cayley_adj(p, S):
    adj = [set() for _ in range(p)]
    for u in range(p):
        for s in S:
            adj[u].add((u + s) % p)
    return adj
```

**Do NOT port** `ilp_had2` (C.3 lines 393–425) — Phase 3 is solver-free; all 12 Cayley resolve by heuristic (D.1 rows 16–27 all `method=heuristic`).

**Also required (see `pyproject.toml` below):** add `src/alpha2/generators/cayley.py` to `[tool.ruff] extend-exclude` — it is determinism-sensitive (`rng.shuffle`).

---

### `src/alpha2/corpus/manifest.py` (persistence/config, batch)

**Analog:** `src/alpha2/corpus/schema.py` (`h_edges_sha256`, lines 91–98) — reuse it, never re-hash. Shape mirror: `data/manifests/fingerprint.json`.

**Critical:** the manifest MUST hash via `schema.h_edges_sha256` so its bytes match what `verifier.verify_model_record` recomputes (verifier lines 89–92 do the SAME `json.dumps(sorted [min,max] pairs, separators=(",",":"))` then sha256). Do NOT hand-roll sha256 (RESEARCH "Don't Hand-Roll").

**Reuse the frozen convention** (`corpus/schema.py` lines 91–98):
```python
def h_edges_sha256(H_edges):
    canon = json.dumps(canonical_edges(H_edges), separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()
```

**Manifest entry shape** — mirror `data/manifests/fingerprint.json` (add `nu`/`chi`, keep the `h_edges_sha256` key name the verifier convention produces):
```json
{
  "tfp:n31:s1": { "m": 131, "nu": 15, "chi": 16,
                  "h_edges_sha256": "3c953d90...41e2" }
}
```
**Key scheme** (RESEARCH Assumption A5, extends fingerprint.json): `tfp:n{N}:s{S}` and `cayley:p{P}:s{S}` (e.g. `cayley:p31:s5310`). Build from the stored corpus after all 296 land; freeze once, commit forever.

**Do NOT overwrite `fingerprint.json`** — it stays as the ENV-03 exemplar; `corpus-v1.manifest.json` is additive (RESEARCH Pattern 4 note).

---

### `src/alpha2/repro/baseline.py` (orchestration/driver, batch) — FINALIZE

**Analog:** itself (current file) for the RNG-contract core; the MVP vertical slice in RESEARCH Pattern 1 for the schema-v1 upgrade.

**Preserve VERBATIM (RNG contract v1 — Pitfall 3):** the `run_instance` RNG order — one `random.Random(seed)`, then `triangle_free_process` THEN `solve`, in that order (current `baseline.py` lines 28–36). Do NOT introduce per-stage subseeds.

**Current RNG core to keep** (`repro/baseline.py` lines 27–36):
```python
def run_instance(n, seed, records):
    rng = random.Random(seed)
    adj, m = triangle_free_process(n, rng)      # generator consumes rng FIRST
    ...
    nu = matching_number(adj, n)
    chi = n - nu
    sets, init_conf, moves, restarts, tsolve = solve(adj, n, chi, rng)  # SAME rng, next
```
(`solve` signature: `solve(adj, n, k, rng, time_budget=90.0)` → `sets, init_conf, moves, restarts, tsolve` — `heuristic.py` line 99.)

**REPLACE the emission tail:** the current ad-hoc `rec = {...}` dict + `json.dump(records)` (lines 44–67) must become the witness→build_record→append path from RESEARCH Pattern 1:
```python
from alpha2.invariants.witness import extract_witness
from alpha2.corpus import schema, store

M, U, nu2 = extract_witness(adj, n)            # emission-time witness (verifier re-checks)
H_edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
rec = schema.build_record(
    provenance=schema.provenance_seed(
        "triangle_free_process_complement", n, seed,
        "Bohman uniform triangle-free process"),
    H_edges=H_edges, nu_H=nu, chi_G=chi,
    model_branch_sets=[list(s) for s in sets],
    matching_M=M, tutte_berge_U=U, method="heuristic",
    omega_G=None, verified=True,
)
store.append_certificate(rec, path=path)        # verify-at-append trust root + atomic write
```

**Canonical H_edges expression** is already present verbatim in current `baseline.py` line 46 — reuse exactly (it matches `schema.canonical_edges`).

**Remove `assert`** in the verified path (current line 33 `assert tf`) — Pitfall 6 / `-O` job. Route correctness through `verify_certificate` (raise-based), not asserts.

**Path override:** `store.append_certificate(rec, path=...)` — mirror `paths.CORPUS` usage (current `baseline.py` lines 65–67 use `paths.ensure_parent(paths.CORPUS)`).

---

### `src/alpha2/repro/sweep.py` (orchestration/driver, batch) — NEW

**Analog:** `src/alpha2/repro/baseline.py` (finalized) — identical `run_instance` body; only the instance list differs.

**Copy the finalized `run_instance` verbatim** (same generator→solve→witness→build_record→append path above). The ONLY difference is the driver `main()` instance list (Pitfall 1 exact decomposition — encode as data):
```python
# 269 sweep instances (seed-137 EXCLUDED — it is stored once as the exact study):
#   n=31  seeds 100..299  (200) minus seed 137 -> 199
#   n=51  seeds 100..149  (50)
#   n=101 seeds 100..119  (20)
instances = ([(31, s) for s in range(100, 300) if s != 137]
             + [(51, s) for s in range(100, 150)]
             + [(101, s) for s in range(100, 120)])
assert len(instances) == 269
```
Showpieces `(301,13),(501,14)` may live here or in baseline — 15 (baseline 12 + showpieces 2 + seed137 1) + 269 = 284 TFP total. Assert `len(corpus)==296` after the full freeze.

**Note (Pitfall 5):** sequential `append_certificate` is O(N²). Accept for MVP; only add a *tested* batch path if measured too slow — never weaken verify-at-append.

---

### `src/alpha2/repro/cayley_run.py` (orchestration/driver, batch) — NEW

**Analog:** `src/alpha2/repro/baseline.py` (finalized driver shape) + Appendix C.3 `run()` (lines 427–455) for the Cayley-specific generation + accounting.

**RNG contract:** same single-stream order as baseline — `rng = random.Random(seed)`, then `random_maximal_symmetric_sumfree(p, rng)` (consumes rng via `rng.shuffle`) THEN `solve(adj, p, chi, rng, time_budget=60)` (C.3 lines 428–435).

**Reconstruct + store inline H_edges (Pattern 3 / Pitfall 2 — the reference stored only `S`):**
```python
from alpha2.generators.cayley import random_maximal_symmetric_sumfree, cayley_adj

rng = random.Random(seed)
S = random_maximal_symmetric_sumfree(p, rng)
adj = cayley_adj(p, S)                          # reconstruct adjacency
nu = matching_number(adj, p); chi = p - nu
sets, *_ = solve(adj, p, chi, rng, time_budget=60)
M, U, _ = extract_witness(adj, p)
H_edges = sorted([min(u, v), max(u, v)] for u in range(p) for v in adj[u] if u < v)
rec = schema.build_record(
    provenance=schema.provenance_params(
        "cayley_maximal_sumfree_Zp", p, {"S": sorted(S)}, seed=seed),
    H_edges=H_edges, nu_H=nu, chi_G=chi,
    model_branch_sets=[list(s) for s in sets],
    matching_M=M, tutte_berge_U=U, method="heuristic",
    omega_G=None, verified=True,
)
store.append_certificate(rec, path=path)
```
Use `schema.provenance_params` (schema.py lines 109–117) — `params={"S": sorted(S)}` + `seed` for R2 regeneration. (Baseline uses `provenance_seed`; Cayley uses `provenance_params`.)

**Instance list (Pitfall 1 — 12 Cayley):** `for p in (31, 53, 101, 151): for k in range(3): seed = 5000 + 10*p + k` (C.3 lines 463–465). All 12 resolve heuristically — no `ilp_had2` fallback (drop C.3 lines 438–444).

---

### `src/alpha2/repro/seed137.py` (orchestration/driver, batch) — NEW, NO SOLVER

**Analog:** `src/alpha2/repro/baseline.py` for generation + store; RESEARCH Pattern 2 for the carried literal.

**Regenerate H from seed, carry the D.3 model literal (no `solve`, no CBC):**
```python
# Source: Appendix D.3 — K16 model (9 pairs + 7 singletons); verifier re-checks vs regenerated H
SEED137_MODEL = [[2,20],[4,7],[8,18],[9,13],[12,27],[16,22],[17,24],[19,29],[26,28],
                 [0],[1],[3],[10],[11],[21],[23]]

rng = random.Random(137)
adj, m = triangle_free_process(31, rng)          # regenerate H only; do NOT call solve
nu = matching_number(adj, 31); chi = 31 - nu
M, U, _ = extract_witness(adj, 31)
H_edges = sorted([min(u, v), max(u, v)] for u in range(31) for v in adj[u] if u < v)
rec = schema.build_record(
    provenance=schema.provenance_seed(
        "triangle_free_process_complement", 31, 137,
        "Bohman uniform triangle-free process"),
    H_edges=H_edges, nu_H=nu, chi_G=chi,
    model_branch_sets=SEED137_MODEL,             # literal; had_2 = len = 16 (interim)
    matching_M=M, tutte_berge_U=U,
    method="exact ILP (CBC): had_2(G)=17",       # documents true had_2; family arrives Phase 4
    omega_G=14, verified=True,
)
store.append_certificate(rec, path=path)
```
This matches the Phase-2 interim record exactly (02-02-SUMMARY.md: had_2=16 derived, method string documents 17, omega_G=14). `method` containing "ILP" makes `reproduction.kind` = `semantic` (schema.py `reproduction_kind_for_method`). Seed-137 is stored ONCE (excluded from the sweep loop — Pitfall 1).

---

### `data/manifests/corpus-v1.manifest.json` (data/config, batch) — NEW

**Analog:** `data/manifests/fingerprint.json` (exact shape). Generated by `corpus/manifest.py` from the frozen 296-record corpus; committed. Keep `fingerprint.json` untouched alongside it.

---

### `tests/test_corpus_r1.py` (test, verify) — NEW

**Analog:** `tests/test_fingerprint.py::test_stored_model_reverifies` (lines 85–94) for the "re-verify stored witness, never replay search" discipline; RESEARCH R1 Code Example for the full-corpus loop.

**Pattern — verify all 296 from JSON alone + per-family counts (Pitfall 1):**
```python
import json
from alpha2 import paths
from alpha2.corpus.verifier import verify_certificate, VerificationError

def test_r1_all_296_reverify():
    records = json.load(open(paths.CORPUS))
    assert len(records) == 296
    tfp = sum(1 for r in records if r["provenance"]["family"] == "triangle_free_process_complement")
    cay = sum(1 for r in records if r["provenance"]["family"] == "cayley_maximal_sumfree_Zp")
    assert (tfp, cay) == (284, 12)
    for rec in records:
        k = verify_certificate(rec)                # raises on any violation
        assert k >= rec["invariants"]["chi_G"]
```
Route the trust check through `verify_certificate` (raise-based) so the `-O` job stays meaningful — keep any `assert` out of the verification decision itself (Pitfall 6). This test is also run under `python -O` in CI.

---

### `tests/test_corpus_r2.py` (test, transform) — NEW

**Analog:** `tests/test_fingerprint.py::test_golden_hash` (lines 73–82) — regenerate → hash → compare to manifest, with a doc-invariant gate before trusting the hash.

**Pattern — regenerate from seed, sha256 == manifest (use `schema.h_edges_sha256`, not a 2nd hash impl):**
```python
import json, random
from alpha2.generators.tfp import triangle_free_process
from alpha2.corpus.schema import h_edges_sha256

def regen_tfp_hash(n, seed):
    adj, _ = triangle_free_process(n, random.Random(seed))
    H_edges = [[min(u,v),max(u,v)] for u in range(n) for v in adj[u] if u < v]
    return h_edges_sha256(H_edges)

def test_r2_manifest_determinism():
    manifest = json.load(open("data/manifests/corpus-v1.manifest.json"))
    assert regen_tfp_hash(31, 1) == manifest["tfp:n31:s1"]["h_edges_sha256"]
```
Add a Cayley R2 leg using `generators.cayley.random_maximal_symmetric_sumfree` + `cayley_adj` (same regen→hash pattern). Per-commit = a slice; nightly = all 296.

---

### `tests/test_corpus_r3.py` (test, batch replay) — NEW, marked `slow`

**Analog:** `tests/test_fingerprint.py::test_heuristic_matches_d2_exact_pinned_env` (lines 111–126) — the pinned-interpreter byte-exact replay pattern (single-RNG contract).

**Pattern — replay a driver slice, assert identical stored JSON on 3.12.13:** reuse the single-`random.Random(seed)`→generate→solve order (fingerprint.py lines 118–126), then compare the produced record bytes to the committed corpus record. Register `slow` in `pyproject.toml` markers; release/nightly gate only (RESEARCH Validation Architecture). Never make R3 the *only* reproduction notion (Pitfall 4).

---

### `.github/workflows/ci.yml` (config/CI, event-driven) — NEW, **no in-repo analog**

**No analog exists** (no `.github/` in repo). Use RESEARCH Code Examples verbatim (lines 349–376): `astral-sh/setup-uv` **pinned to a commit SHA**, `uv sync --locked --extra dev`, `uv run --frozen pytest`. Jobs: R1+R2+fingerprint+`-O` every commit; R3+full-296+3.13 canary (`continue-on-error: true`) on schedule/release. The `-O` job template is `tests/test_verifier_dash_O.py` (subprocess `python -O`) extended to `test_corpus_r1.py` (Pitfall 6). Canonical runner: `ubuntu-latest` (Linux x86_64).

---

### `pyproject.toml` (config) — MODIFY

**Analog:** itself (current `[tool.ruff]` and `[tool.pytest.ini_options]` blocks).

**Three edits (RESEARCH Wave 0 Gaps):**
1. Add `"src/alpha2/generators/cayley.py"` to `[tool.ruff] extend-exclude` (currently lists `tfp.py` + `heuristic.py`) — determinism-sensitive `rng.shuffle` (Pitfall 3).
2. Register a `slow` marker under `[tool.pytest.ini_options]` (for R3): `markers = ["slow: release/nightly replay gate"]`.
3. Pin pytest in the `dev` extra (currently bare `pytest`) → `pytest==8.x` before freezing CI (Assumption A6), so the newer-Python canary can't drift the runner silently.

---

## Shared Patterns

### Single-RNG contract v1 (byte-reproduction anchor)
**Source:** `src/alpha2/repro/baseline.py` lines 28–36 (docstring lines 8–11).
**Apply to:** ALL repro drivers (`baseline`, `sweep`, `cayley_run`; `seed137` uses the generator half only).
```python
rng = random.Random(seed)          # ONE stream
adj, _ = <generator>(size, rng)    # generator consumes rng FIRST
...
sets, *_ = solve(adj, size, chi, rng)   # SAME rng, next — never a subseed
```

### Canonical H_edges construction
**Source:** `src/alpha2/repro/baseline.py` line 46; matches `schema.canonical_edges` (schema.py lines 48–62).
**Apply to:** every driver, before `build_record`.
```python
H_edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
```

### Verify-at-append via the trust root (never hand-roll storage)
**Source:** `src/alpha2/corpus/store.py::append_certificate` (lines 86–144).
**Apply to:** every driver's emission tail — `store.append_certificate(rec, path=path)` gates on `verify_certificate` (BOTH legs) + `verified is True`, re-verifies the whole prefix, hash-chains, and `os.replace`-writes atomically. Pass `path` in tests so the repo corpus is untouched.

### Frozen sha256 convention (never re-hash)
**Source:** `src/alpha2/corpus/schema.py::h_edges_sha256` (lines 91–98); verifier recomputes identically (verifier.py lines 89–92).
**Apply to:** `corpus/manifest.py` and `tests/test_corpus_r2.py`. Any ad-hoc sha256 is a common-mode risk (RESEARCH "Don't Hand-Roll").

### Emission-time witness (untrusted; verifier re-checks)
**Source:** `src/alpha2/invariants/witness.py::extract_witness` (lines 35–42) → returns `(M, U, nu)`.
**Apply to:** every driver that produces a heuristic model (`baseline`, `sweep`, `cayley_run`, `seed137`). Feed `M`/`U` straight into `build_record`; the verifier's `verify_chi_witness` re-derives correctness.

### `python -O` fail-closed discipline (assert-free verified path)
**Source:** `tests/test_verifier_dash_O.py` (subprocess `python -O` canary, lines 25–55).
**Apply to:** all new drivers and R-tests — keep `assert` out of any path the `-O` CI job runs; the R1 decision routes only through raise-based `verify_certificate` (Pitfall 6, Anti-Patterns).

### Doc-invariant gate before trusting a hash
**Source:** `tests/test_fingerprint.py` lines 78–82, 137–143 (`assert m == EXPECTED_M` before comparing sha256).
**Apply to:** R2 tests — gate on the doc-derived invariant (e.g. `m`, `nu`, `chi`) before the hash comparison, so a porting bug cannot self-certify.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.github/workflows/ci.yml` | config/CI | event-driven | No `.github/` directory exists; use RESEARCH Code Examples (setup-uv + `uv sync --locked` + `uv run --frozen`). Pin action to a commit SHA. |
| `data/corpus/hadwiger_alpha2_certificates.json` | data | — | Not hand-authored — it is the atomic output of `store.append_certificate`; "pattern" is simply running the drivers, then git-committing the result as the immutability anchor. |

---

## Metadata

**Analog search scope:** `src/alpha2/{generators,corpus,invariants,repro,search,verify}/`, `tests/`, `data/manifests/`, `pyproject.toml`, Appendix C.3/D of `.planning/reference/alpha2-program-source.md`.
**Files scanned:** 13 source/test/config files read in full + C.3 (lines 353–472) of the reference.
**Pattern extraction date:** 2026-07-21
</content>
</invoke>
