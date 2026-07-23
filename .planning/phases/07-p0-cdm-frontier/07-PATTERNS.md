# Phase 7: P0 — CDM Frontier - Pattern Map

**Mapped:** 2026-07-22
**Files analyzed:** 22 (11 source + 11 tests) new/modified
**Analogs found:** 20 / 22 (2 have no code analog: the Markdown proof + the JSON data file)

> No CONTEXT.md exists for this phase. File list extracted from `07-RESEARCH.md`
> §"Recommended Project Structure" + §"Validation Architecture → Wave 0 Gaps".
> The whole phase is *wiring a new predicate (CDM) into the existing had₂
> apparatus* — nearly every new file has a strong in-repo analog to copy.

## CLAUDE.md constraints that bind these files

| Constraint | Applies to | Rule |
|-----------|-----------|------|
| **stdlib-only trust leg** (VRF-01) | `pool/cdm/reference.py`, `pool/cdm/verifier.py`, `pool/cdm/schema.py`, `pool/cdm/store.py` | Import ONLY json/hashlib/collections/subprocess/os/tempfile. NEVER import networkx, ortools, or any proposer module. Raises-only (`if not cond: raise`), no `assert` — correct under `python -O`. |
| **ortools confinement** | `pool/cdm/cpsat.py` ONLY | The single new module allowed to `from ortools.sat.python import cp_model`. Mirrors `solvers/cpsat.py` being "the ONLY module that imports the ortools library." |
| **networkx confinement** | `pool/cdm/generate.py` (+ `adjudicate.py` at decode) | `from_graph6_bytes` / `complement` live here only. Decode feeds a plain `adj = list[set[int]]`; the reference/verifier never touch a graph library. |
| **Determinism-sensitive / ruff-excluded** | `pool/cdm/generate.py` (candidate) | Generation touches subprocess + graph6; if any CPython-set-iteration order is load-bearing, add it to `pyproject.toml` `[tool.ruff] extend-exclude` exactly like `tfp.py`/`cayley.py`. NOT auto-formatted. |
| **CP-SAT determinism on UNSAT** (#3590/#3842/#4839) | `pool/cdm/cpsat.py` | Any CDM-FAIL (UNSAT/INFEASIBLE) uses `num_workers=1` + pinned `random_seed` — the exact idiom in `solvers/cpsat.py:208-210`. |
| **Frozen 296-corpus untouched** | `pool/cdm/store.py`, `pool/cdm/schema.py`, `paths.py` | New `data/corpus/cdm_certificates.json` via a NEW `paths.CDM_CORPUS`. Do NOT extend `corpus/store.py` / `corpus/verifier.py` / the frozen corpus. |
| **No WL-hash dedup** | `pool/cdm/generate.py` | `geng` output is already isomorph-free; a 2nd stream is deduped via `shortg`, never WL-hash. |
| **GSD workflow** | all | These are edits behind a GSD command; no direct repo edits outside the workflow. |

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/alpha2/pool/__init__.py` | package | — | `src/alpha2/generators/__init__.py` | exact |
| `src/alpha2/pool/cdm/__init__.py` | package | — | `src/alpha2/corpus/__init__.py` | exact |
| `src/alpha2/pool/cdm/generate.py` | generator | streaming (subprocess→graph6) | `src/alpha2/generators/tfp.py` + `cayley.py` | role-match (determinism discipline); pattern for geng is RESEARCH Pattern 1 |
| `src/alpha2/pool/cdm/reference.py` | solver (reference) | transform (decide) | `src/alpha2/corpus/verifier.py` (stdlib/raises/-O), DFS spec in RESEARCH §DFS | role-match |
| `src/alpha2/pool/cdm/cpsat.py` | solver (cross-check) | request-response (solve) | `src/alpha2/solvers/cpsat.py` | exact |
| `src/alpha2/pool/cdm/verifier.py` | verifier (trust leg) | transform (verify record) | `src/alpha2/corpus/verifier.py` + `invariants/witness.py` | exact (discipline), role-adapted (CDM ≠ K_χ model) |
| `src/alpha2/pool/cdm/schema.py` | schema | transform (build record) | `src/alpha2/corpus/schema.py` | exact |
| `src/alpha2/pool/cdm/store.py` | store | file-I/O (append-only) | `src/alpha2/corpus/store.py` | exact |
| `src/alpha2/pool/cdm/adjudicate.py` | pipeline/controller | event-driven (per-instance runbook) | `src/alpha2/battery/pipeline.py` + `solvers/differential.py` | role-match |
| `src/alpha2/paths.py` (MODIFY) | config | — | `src/alpha2/paths.py` (self; add `CDM_CORPUS`) | exact |
| `docs/proofs/transfer-lemma.md` | doc/proof | — | (none — human artifact) | no analog |
| `data/corpus/cdm_certificates.json` | data | — | `data/corpus/hadwiger_alpha2_certificates.json` (produced by store, not hand-written) | no analog |
| `tests/pool/cdm/conftest.py` | test fixtures | — | inline fixtures in `tests/test_cpsat_backend.py:39-51` | role-match |
| `tests/pool/cdm/test_generation_counts.py` | test | integration | `tests/test_reproduction_contract.py` (count assertions) | partial |
| `tests/pool/cdm/test_generation_crosscheck.py` | test | integration | RESEARCH §"Reproduce…counts" bash + `tfp.is_edge_maximal_tf` | partial |
| `tests/pool/cdm/test_cdm_n_le_11.py` | test | integration | `tests/test_cpsat_backend.py` brute-differential panel | role-match |
| `tests/pool/cdm/test_dfs_cpsat_agree.py` | test | integration (slow) | `tests/test_cpsat_backend.py::test_brute_force_differential_n_le_8` | exact |
| `tests/pool/cdm/test_cdm_verifier.py` | test | unit | `tests/test_verifier_mutants.py` | exact |
| `tests/pool/cdm/test_cdm_verifier_dash_O.py` | test | unit (subprocess -O) | `tests/test_solver_paths_dash_O.py` | exact |
| `tests/pool/cdm/test_transfer_lemma.py` | test | property | `tests/test_cpsat_backend.py` panel (parametrize) | partial |
| `tests/pool/cdm/test_disconnected_complement.py` | test | unit | `tests/test_verifier_mutants.py` (single-perturbation style) | partial |
| `tests/pool/cdm/test_cdm_store.py` | test | integration | `tests/test_store_append_only.py` | exact |

---

## Pattern Assignments

### `src/alpha2/pool/cdm/generate.py` (generator, streaming)

**Analogs:** `src/alpha2/generators/tfp.py` (determinism/ruff discipline), `src/alpha2/generators/cayley.py` (injected-rng, port-shape); the geng subprocess shape is RESEARCH Pattern 1.

**Determinism header to copy** (`tfp.py:1-11`) — verbatim-style docstring warning + the ruff-exclude note:
```python
"""... Determinism note: byte-reproduction depends on CPython set-iteration order,
which depends on the exact code here. Do NOT reformat, reorder comprehensions,
merge/split loops... Do NOT run `ruff --fix`/format on this module (it is excluded
in pyproject.toml)."""
```

**Provenance capture** must feed `schema.provenance_graph6` (see `corpus/schema.py:120-122`): `provenance_graph6(family="mtf_complement", n, graph6)` + a `params` sidecar `{geng_version, flags:"-ctq | pickg -Z2", shard:"res/mod"|null, index}`.

**Subprocess idiom** (RESEARCH §Architecture Patterns Pattern 1 — copy exactly; V5 security control: `Popen([...])` arg lists, NEVER `shell=True`, int-validate `n`/`res`/`mod`):
```python
p1 = subprocess.Popen(["geng", "-ctq", str(n)] + ([shard] if shard else []), stdout=subprocess.PIPE)
p2 = subprocess.Popen(["pickg", "-Z2"], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
p1.stdout.close()
for i, line in enumerate(p2.stdout):
    g6 = line.strip()
    if g6:
        yield i, g6, shard
p2.wait()
```
Decode (in `adjudicate.py`, networkx-confined) — RESEARCH §"Complement + α=2 sanity":
```python
H = nx.from_graph6_bytes(g6.encode()); G = nx.complement(H)
adj = [set(G.neighbors(u)) for u in range(G.number_of_nodes())]  # feed reference/cpsat
```

**Anti-pattern (CLAUDE.md):** never filter the full triangle-free stream in Python (`tfp.is_edge_maximal_tf` timed out at n=13) — keep `pickg` in the C pipe.

---

### `src/alpha2/pool/cdm/reference.py` (solver reference, transform) — `has_cdm(adj, n)`

**Analog:** `src/alpha2/corpus/verifier.py` for the *discipline* (stdlib-only, raises-or-returns, `-O`-safe, rebuild adjacency from primitive data); the *algorithm* is the DFS in RESEARCH §"The DFS reference decision procedure" (copy that body; it is the trusted reference the CP-SAT model is checked against).

**Discipline to mirror** (`corpus/verifier.py:1-27`): module docstring stating "stdlib ONLY … imports NOTHING from generators/search/solver," and the `_is_conflict`-style *private* adjacency helper (a private copy of the definition logic, imported from nowhere). The two definition helpers `vsets_adjacent(e,f)` and `dominates(M)` are the CDM analog of `verifier._is_conflict` (`verifier.py:34-46`) — inline, private, no import.

**Interface contract:** return a witness `M` (list of `(a,b)`, `a<b`) if a non-empty connected dominating matching exists, else `None`. Pin the A1 adjacency reading ("w adjacent to edge e ⟺ w adjacent to ≥1 endpoint"). Belt-and-suspenders second reference (enumerate all pairwise-adjacent matchings, test `dominates`) is acceptable for small n.

**No `assert`** — this is a reference decision procedure that gates radioactive UNSAT; every check is a plain branch (mirror the `verifier.py` raises-only rule so it survives `python -O`).

---

### `src/alpha2/pool/cdm/cpsat.py` (solver cross-check, request-response) — `cdm_cpsat(adj, n)`

**Analog:** `src/alpha2/solvers/cpsat.py` — the ONLY ortools importer; copy its structure directly. The CDM boolean encoding is RESEARCH §"The CP-SAT cross-check encoding."

**Import + confinement header** (`cpsat.py:1-6, 44-48`):
```python
"""OR-Tools CP-SAT adapter — the ONLY module that imports the ortools library. ..."""
import importlib.metadata, math, time
from ortools.sat.python import cp_model
```

**Pinned deterministic seed + single-worker idiom** (`cpsat.py:57, 207-214` — copy VERBATIM for any CDM-FAIL/UNSAT; this is the LOCKED impossibility discipline):
```python
_RANDOM_SEED = 137
...
solver = cp_model.CpSolver()
solver.parameters.num_workers = 1
solver.parameters.random_seed = _RANDOM_SEED
if p.time_limit_s is not None:
    solver.parameters.max_time_in_seconds = p.time_limit_s
if mode == "decision":
    solver.parameters.stop_after_first_solution = True
```

**Sorted-iteration determinism** for conflict rows (`cpsat.py:200-205`): iterate constraint sources in `sorted(...)` order. The CDM model's three constraint families (matching `AddAtMostOne` per vertex, connected pairwise `x[e]+x[f]<=1`, dominating `x[e] <= sum(inc_w)`) each build in sorted order.

**Status honesty** (`cpsat.py:67-93` `map_status`): INFEASIBLE (CDM-FAILS) is the radioactive direction — map it to a PROVED-INFEASIBLE-style verdict ONLY under `num_workers=1`+seed, and require the DFS's exhaustive UNSAT to agree before it is trusted. A SAT witness is UNTRUSTED — route through `verify_cdm_witness`. Reuse the `Status` enum / `ExactOutcome`-style honesty from `solvers/result.py:33-141` (a stopped solve is never read as exact).

---

### `src/alpha2/pool/cdm/verifier.py` (trust leg, transform) — `verify_cdm_witness(record)`

**Analogs:** `src/alpha2/corpus/verifier.py` (the discipline + `_build_adj` + sha256 integrity + raises) and `src/alpha2/invariants/witness.py` (emission-side extractor is UNTRUSTED; the verifier re-checks from stored data).

**CRITICAL — do NOT reuse `verify_model_record`** (RESEARCH Anti-Pattern): a connected dominating matching is NOT a K_χ branch-set family (unmatched vertices need not be pairwise adjacent). Write a *new* leg with its own checks.

**Discipline to copy** (`corpus/verifier.py:1-27`): the full trust-boundary docstring — "stdlib ONLY (json, hashlib, collections)… imports NOTHING from proposers… rebuilds adjacency from the STORED edges… every check is `if not cond: raise` … correct under `python -O`."

**`_build_adj` pattern to copy verbatim** (`verifier.py:49-68`) — rebuild `list[set]` from stored edges, raising on malformed/non-canonical/duplicate:
```python
def _build_adj(H_edges, n):
    adj = [set() for _ in range(n)]; seen = set()
    for e in H_edges:
        if len(e) != 2: raise VerificationError(...)
        u, v = e
        if not (isinstance(u, int) and isinstance(v, int) and 0 <= u < v < n): raise VerificationError(...)
        if (u, v) in seen: raise VerificationError(...)
        seen.add((u, v)); adj[u].add(v); adj[v].add(u)
    return adj
```

**sha256 integrity gate to copy** (`verifier.py:92-96`): recompute canonical edge sha256 and compare to the stored value before trusting anything.

**Range-check-before-index guard to copy** (`verify_chi_witness` `CR-01`, `verifier.py:176-179`): `adj` is a plain list, so a negative vertex silently wraps (`adj[-1]==adj[n-1]`) and could alias two labels — range-check `0 <= v < n` on every witness vertex BEFORE indexing.

**CDM verifier legs** (each `if not cond: raise VerificationError(...)`):
1. non-empty `M`; each `(a,b)` is an edge of G (i.e. NOT an H-edge in the complement encoding — decide the storage convention and gate it like `verifier.py:117`);
2. `M` is a matching (no repeated vertex — copy the `covered`-set logic `verifier.py:169-185`);
3. `M` is **connected**: every pair of edges `V(e),V(f)` adjacent in G (the `vsets_adjacent` predicate, re-checked);
4. `M` is **dominating**: every `w ∉ V(M)` adjacent to ≥1 endpoint of each `M`-edge (A1 reading).

Returns `True` (or `|M|`); raises on any violation.

---

### `src/alpha2/pool/cdm/schema.py` (schema, transform)

**Analog:** `src/alpha2/corpus/schema.py` — copy the canonical-edges + sha256 + hash-chain + record-builder machinery.

**Reuse directly (do not re-implement):** `provenance_graph6(family, n, graph6)` (`schema.py:120-122`), `canonical_edges` (`schema.py:48-62`), `h_edges_sha256` (`schema.py:91-98`), `canonical_record_json`/`chain_hash`/`CHAIN_FIELD` (`schema.py:65-88`). A CDM `build_cdm_record` mirrors `build_record` (`schema.py:246-310`) but stores `{provenance(graph6), H_edges, H_edges_sha256, matching_M (the witness), invariants:{n, complement_connected: bool, cdm: true}}`.

**ENV-05 carve-out (RESEARCH Pitfall 5 / A4):** CDM certificates are **solver-independent** — do NOT stamp `CANONICAL_PLATFORM`/`cbc_under_rosetta` (`schema.py:42, 187-193`) on a CDM-HOLDS cert. Record only nauty/geng version + Python version. `make_reproduction`/`make_backends` (`schema.py:166-223`) are had₂/CBC-shaped — write a CDM-specific reproduction block that is `byte_exact` and platform-agnostic.

**JSON-native coercion to copy** (`schema.py:229-243` `_as_int_pairs`): coerce every stored int with `int(...)` so no tuple/np-int leaks and the record round-trips through `json.dumps/loads` with field-equality.

---

### `src/alpha2/pool/cdm/store.py` (store, file-I/O)

**Analog:** `src/alpha2/corpus/store.py` — clone the append-only mechanics; do NOT reinvent (RESEARCH "Don't Hand-Roll").

**Three guarantees to copy exactly** (`store.py:1-40` docstring + `append_certificate` body `store.py:86-144`):
1. **Verify-at-append** — every append calls `verify_cdm_witness(rec)` (the new leg) and requires `verified is True`;
2. **Append-only prefix-immutability** — re-verify every prior record + recompute the per-record hash chain from record 0 (`_verify_chain` `store.py:53-75`, `chain_hash` from schema);
3. **Atomic write** — `tempfile.mkstemp(dir=…)` → `fh.flush()` → `os.fsync(fh.fileno())` → `os.replace(tmp, path)`, temp unlinked on failure (`store.py:132-143`):
```python
fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
try:
    with os.fdopen(fd, "w") as fh:
        json.dump(new, fh); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
finally:
    if os.path.exists(tmp):
        os.unlink(tmp)
```
Swap the import `from alpha2.corpus.verifier import verify_certificate` for the CDM leg, and default `path` to `paths.CDM_CORPUS` (new).

---

### `src/alpha2/pool/cdm/adjudicate.py` (pipeline, event-driven)

**Analogs:** `src/alpha2/battery/pipeline.py` (the per-instance runbook + emit/result shape) and `src/alpha2/solvers/differential.py` (the DFS≡CP-SAT agreement gate — CDM's dual-decision must mirror `differential_verdict`/`CriticalDisagreement`).

**Runbook control-flow to mirror** (`pipeline.py:93-252` `run_candidate`): per instance — decode → `has_cdm` (reference) + `cdm_cpsat` (cross-check) → agreement gate → CDM-HOLDS: `verify_cdm_witness` + `store.append_certificate`; CDM-FAILS: classify complement-connectivity, escalate or catalog. Copy the `emit(...)`/`result(...)` closure pattern (`pipeline.py:123-163`) and the append-event logging (`battery/log.py`).

**Agreement gate to mirror** (`differential.py:38-42, 57-108`): a CDM `CriticalDisagreement`-style class; DFS-says-CDM vs CP-SAT-says-UNSAT (or vice-versa) is release-blocking → quarantine + HALT the batch, never "best of two." Copy the docstring stance (`differential.py:29-33`).

**Disconnected-complement carve-out (RESEARCH Pitfall 1 / Open Q1):** before escalating any CDM-FAIL, classify `nx.is_connected(complement)` — `K_a ⊔ K_b` (complete-bipartite H) CDM-fails are catalogued as expected/out-of-scope, NEVER routed to E3 as a Hadwiger event.

**Escalation hook (RESEARCH Open Q4):** a *connected*-complement CDM-fail routes to the existing battery (`battery/pipeline.run_candidate` had₂ dual-backend) + records + quarantines; full E3 is deferred to Phase 11.

---

### `src/alpha2/paths.py` (config, MODIFY)

**Analog:** the file itself. Add a `CDM_CORPUS` constant beside `CORPUS` (`paths.py:12`), same `REPO_ROOT / "data" / "corpus" / ...` shape; `ensure_parent` (`paths.py:22-25`) already generalizes:
```python
CDM_CORPUS = REPO_ROOT / "data" / "corpus" / "cdm_certificates.json"
```
Sole path authority — no other module embeds the literal (`paths.py:2-6`).

---

## Test Pattern Assignments

### `tests/pool/cdm/test_cdm_verifier.py` — mirror `tests/test_verifier_mutants.py`

Copy the **single-perturbation mutant** structure (`test_verifier_mutants.py:79-158`): one known-good CDM record + witness `M`; each test mutates ONE thing and asserts `verify_cdm_witness` raises `VerificationError`. CDM mutants: (a) empty `M`; (b) `M` not a matching (shared vertex); (c) `M` not connected (a pair of `V`-non-adjacent edges); (d) `M` not dominating (an uncovered vertex non-adjacent to some `M`-edge); (e) a size-2 set that is an H-edge not a G-edge; plus a `sha256`-mismatch integrity mutant (`test_verifier_mutants.py:20, 69-71`). Keep the "good record genuinely passes" sanity tests.

### `tests/pool/cdm/test_cdm_verifier_dash_O.py` — mirror `tests/test_solver_paths_dash_O.py`

Copy the subprocess `-O` canary harness verbatim (`test_solver_paths_dash_O.py:24-102`): the `if __debug__: sys.exit(3)` real-branch guard, the exit-code contract (3=not-optimized→fail, 0=raised-correctly, 2=rubber-stamped), and `_run_dash_O` with `PYTHONPATH=src`. Canary: a mutant CDM witness (e.g. non-dominating) must STILL raise under `python -O` (proves the verifier is raises-only, not assert-based).

### `tests/pool/cdm/test_cdm_store.py` — mirror `tests/test_store_append_only.py`

Copy exactly (`test_store_append_only.py`): every test writes to `tmp_path` (real corpus NEVER touched); prove valid-append-creates-file, second-append-preserves-prefix (`data[0] == first`), unverified/mutant refused with file byte-unchanged, prefix-immutability on tamper, CR-02 coherent-substitution refused via the hash chain, and atomic-write-survives-`monkeypatch`-crash (`test_store_append_only.py:147-167`).

### `tests/pool/cdm/test_dfs_cpsat_agree.py` — mirror `tests/test_cpsat_backend.py::test_brute_force_differential_n_le_8`

Copy the parametrized differential panel (`test_cpsat_backend.py:225-251`): `has_cdm` (reference) ≡ `cdm_cpsat` on every instance; mark the n=14 full batch `@pytest.mark.slow` (marker already registered, `pyproject.toml:29`) and shardable via res/mod. Any disagreement is release-blocking.

### `tests/pool/cdm/test_cdm_n_le_11.py` — the A1 definition regression (highest-priority gate)

No exact analog; use the panel/parametrize style of `test_cpsat_backend.py:225-251`. Reproduce CLWY's result: every connected α=2 graph at n≤11 has CDM. Any n≤11 CDM-less connected graph indicates a definition bug (A1), NOT new science — validate BEFORE trusting n=12–14.

### `tests/pool/cdm/test_generation_counts.py` + `test_generation_crosscheck.py`

Assert exact per-n counts 147/392/1,274 (RESEARCH §"Reproduce…counts"); cross-check `pickg -Z2` vs `tfp.is_edge_maximal_tf` (`generators/tfp.py:56-62`) on n≤12 survivors + OEIS A216783 + `shortg` canonical-set equality. Guard sharding: Σ over `res` in `0..mod-1` == total (Pitfall 3).

### `tests/pool/cdm/test_transfer_lemma.py` + `test_disconnected_complement.py`

Property/unit tests: Lemma 2.5 (diam-2 ⟺ edge-maximal via `tfp.is_edge_maximal_tf`) and CDM edge-addition monotonicity; and the `K_a ⊔ K_b` classifier (disconnected complement CDM-fails are catalogued, not escalated).

### `tests/pool/cdm/conftest.py`

Fixtures: small α=2 graphs as in-file literals (copy `test_cpsat_backend.py:39-47` `_c5_adj`/`_empty_adj` shape), `K_a ⊔ K_b`, hand CDM witnesses, and a cached n≤11 MTF sample. Embedded-literal discipline: no cross-test imports (`test_cpsat_backend.py:19-23`).

---

## Shared Patterns

### Trust-leg discipline (stdlib-only, raises-only, `-O`-safe)
**Source:** `src/alpha2/corpus/verifier.py:1-46`
**Apply to:** `pool/cdm/reference.py`, `pool/cdm/verifier.py`, `pool/cdm/schema.py`, `pool/cdm/store.py`
Every check is `if not cond: raise VerificationError(...)` — no `assert`. Rebuild adjacency from stored primitive data (`_build_adj`, `verifier.py:49-68`); never trust a live object. Range-check `0 <= v < n` before indexing a list (`verifier.py:176-179`). Integrity via recomputed sha256 (`verifier.py:92-96`).

### CP-SAT determinism on the impossibility direction
**Source:** `src/alpha2/solvers/cpsat.py:57, 207-214`
**Apply to:** `pool/cdm/cpsat.py`
`_RANDOM_SEED = 137`; `solver.parameters.num_workers = 1`; `solver.parameters.random_seed = _RANDOM_SEED`. Iterate all constraint sources in `sorted(...)`. Never report CDM-FAIL on CP-SAT alone — the DFS reference is the arbiter.

### Dual-engine agreement → release-blocking on disagreement
**Source:** `src/alpha2/solvers/differential.py:38-42, 57-108`
**Apply to:** `pool/cdm/adjudicate.py`
Two independent engines cannot both be right about a decision; unequal verdicts = `CriticalDisagreement` → quarantine + HALT, never pick a winner, never skip.

### Append-only, verify-at-append, atomic, hash-chained persistence
**Source:** `src/alpha2/corpus/store.py:86-144` + `schema.py:65-88`
**Apply to:** `pool/cdm/store.py`, `pool/cdm/schema.py`
tempfile→fsync→os.replace; per-record `chain_sha256`; verify (the CDM leg) before write; new `paths.CDM_CORPUS`, frozen 296-corpus untouched.

### Determinism-sensitive generator (ruff-excluded, verbatim port)
**Source:** `src/alpha2/generators/tfp.py:1-11` + `pyproject.toml:31-39`
**Apply to:** `pool/cdm/generate.py` (if any set-iteration order is load-bearing)
Docstring determinism warning; add the module to `[tool.ruff] extend-exclude`; never `ruff --fix`/format.

### Subprocess input-validation (V5)
**Source:** RESEARCH §Security Domain + Pattern 1
**Apply to:** `pool/cdm/generate.py`
`subprocess.Popen([...])` arg lists, NEVER `shell=True`; int-validate `n`/`res`/`mod`; assert decoded n == requested n.

### Tagged-union provenance reuse
**Source:** `src/alpha2/corpus/schema.py:120-149`
**Apply to:** `pool/cdm/schema.py`, `pool/cdm/generate.py`
`provenance_graph6(family="mtf_complement", n, graph6)` already exists for geng-sourced instances — reuse, do not re-invent.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `docs/proofs/transfer-lemma.md` | doc/proof | — | Human prose artifact (Lemma 2.5 + monotonicity + disconnected-complement carve-out). No `docs/proofs/` precedent exists in-repo; structure from RESEARCH §"The Transfer Lemma." |
| `data/corpus/cdm_certificates.json` | data | — | Produced by `pool/cdm/store.append_certificate`, never hand-written; shape follows `data/corpus/hadwiger_alpha2_certificates.json` but is a runtime output, not a template to copy. |

Two files have a strong-*discipline* analog but a role-*adapted* body (flagged inline above):
- `pool/cdm/verifier.py` — copies `corpus/verifier.py` discipline but MUST NOT reuse `verify_model_record` (a CDM matching ≠ a K_χ branch-set family).
- `pool/cdm/reference.py` — copies the stdlib/raises/`-O` discipline of `corpus/verifier.py`, but the algorithm body is the RESEARCH DFS spec (no in-repo DFS-decision analog exists yet).

## Metadata

**Analog search scope:** `src/alpha2/{generators,corpus,solvers,battery,invariants}/`, `tests/`, `pyproject.toml`, `data/corpus/`.
**Files scanned (read in full):** `generators/tfp.py`, `generators/cayley.py`, `corpus/verifier.py`, `corpus/schema.py`, `corpus/store.py`, `solvers/cpsat.py`, `solvers/differential.py`, `solvers/result.py`, `invariants/witness.py`, `battery/pipeline.py`, `paths.py`, `pyproject.toml`, `tests/test_verifier_mutants.py`, `tests/test_store_append_only.py`, `tests/test_cpsat_backend.py`, `tests/test_solver_paths_dash_O.py`, `tests/test_differential.py` (partial).
**Pattern extraction date:** 2026-07-22
