# Phase 6: Kill Battery CLI (Gate, Search, Statuses) - Pattern Map

**Mapped:** 2026-07-22
**Files analyzed:** 11 source/config (+ Wave-0 test files, covered as a class)
**Analogs found:** 11 / 11 (every new file has an in-repo analog — Phase 6 is wiring, not invention)

> **Read-first for the planner:** Phase 6 owns NO new mathematics. Every excerpt below is copied from an
> already-tested in-repo module. The dominant instruction across all files is **"raises-only, never
> `assert`"** (survives `python -O`) and **"the trust root / differential gate is the sole authority."**
> Do not re-implement math — wire the existing functions in the order the analogs show.

## File Classification

| New / Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------|------|-----------|----------------|---------------|
| `src/alpha2/gate/checks.py` (new) | service (pure predicates) | transform | `corpus/verifier.py` private checks + `generators/tfp.py:49-62` | role-match |
| `src/alpha2/gate/runner.py` (new) | middleware (ordered chain + outcome type) | request-response | `solvers/differential.py` + `solvers/result.py` (outcome dataclass) | role-match |
| `src/alpha2/gate/safe_families.py` (new) | config/data (family→citation map + screen) | transform/lookup | `corpus/manifest.py:36-47` (`_FAMILY_KEY` map) | partial |
| `src/alpha2/invariants/cliques.py` (new) | utility (networkx-confined invariant) | transform | `invariants/matching.py:11-32` | **exact** |
| `src/alpha2/search/heuristic.py` (**modify** `solve`) | service (searcher) | batch/transform | itself — `search/heuristic.py:99-157` | **exact (self)** |
| `src/alpha2/battery/pipeline.py` (new) | controller/orchestrator (7-step runbook) | event-driven / request-response | `repro/baseline.py:34-68` + `repro/cayley_run.py:39-73` + `tests/test_seed137_regression.py:76-119` | **exact** |
| `src/alpha2/battery/log.py` (new) | store (append-only JSONL) | file-I/O / append | `corpus/store.py:86-144` | role-match |
| `src/alpha2/status/views.py` (new) | view (derived read over immutable facts) | transform/read | `corpus/manifest.py:50-99` | role-match |
| `src/alpha2/cli.py` (new) | controller (argparse subcommands) | request-response | `corpus/manifest.py:102-112` + `repro/*.main()` (dispatch/`__main__`); argparse itself = no-analog | partial |
| `src/alpha2/paths.py` (**modify** — add `RESULTS_LOG`) | config | — | itself — `paths.py:12-18` | **exact (self)** |
| `pyproject.toml` (**modify** — add `[project.scripts]`) | config | — | itself — `pyproject.toml:1-14` | **exact (self)** |
| `tests/test_gate_*.py`, `test_profile_general.py`, `test_battery_*.py`, `test_results_log.py`, `test_status_views.py` (new) | test | — | `tests/test_seed137_regression.py`, `tests/test_differential.py` | role-match |

---

## Pattern Assignments

### `src/alpha2/invariants/cliques.py` (utility, transform) — EXACT ANALOG

**Analog:** `src/alpha2/invariants/matching.py` — the frozen "networkx is confined to this one module,
imported *inside* the function" invariant pattern. Copy it verbatim in shape.

**Module-confinement + import-inside-function pattern** (`matching.py:11-16`):
```python
# ---------- exact chromatic number of G = complement(H) ----------
def matching_number(adj, n):
    import networkx as nx
    Hg = nx.Graph(); Hg.add_nodes_from(range(n))
    Hg.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
    M = nx.max_weight_matching(Hg, maxcardinality=True)
    return len(M)
```

**New code (ω via G4, κ via G3) — networkx 3.6.1 API from RESEARCH (`graph_clique_number` is REMOVED):**
```python
def omega_G(adj, n):
    """omega(G) = max clique of G = complement(H). networkx confined to this module."""
    import networkx as nx
    G = nx.complement(_H_graph(adj, n))
    clique, _ = nx.max_weight_clique(G, weight=None)   # NOT graph_clique_number (removed 3.x)
    return len(clique)                                  # seed-137 => 14

def kappa_G(adj, n):
    import networkx as nx
    return nx.node_connectivity(nx.complement(_H_graph(adj, n)))   # seed-137 => 11
```
Build `nx.Graph` from `adj` exactly as `matching.py` does (`add_nodes_from(range(n))`; edges `u<v`).
Confine networkx here — the CHI-01 discipline that pins `max_weight_matching` to `matching.py` applies
identically to `max_weight_clique`/`node_connectivity`.

---

### `src/alpha2/gate/checks.py` (service, pure predicates)

**Analogs:** `corpus/verifier.py` (stdlib-only, raises-only, rebuilds adjacency from data) and
`generators/tfp.py:49-62` (the already-existing G2 primitives — do NOT re-derive them).

**Reuse existing G2 primitives directly (do not reimplement):** `generators/tfp.py`
```python
def is_triangle_free(adj, n):   # tfp.py:49
    ...
def is_edge_maximal_tf(adj, n): # tfp.py:56 — "every non-edge closes a triangle <=> H diameter 2"
    ...
```

**Predicate shape — pure over `(adj, n, inv)`, raises-only guards (mirror `verifier._is_conflict`,
`verifier._build_adj:49-70`).** The mandated even-n criticality fix (CLAUDE.md + RESEARCH Pattern 1) —
encode as `nu == n//2`, **never** `n == 2*chi - 1`:
```python
def g1_criticality(adj, n, inv):
    nu = inv["nu_H"]                      # from invariants/matching (already exact)
    if nu != n // 2:                      # accepts n=31 (nu=15) AND n=32 (nu=16)
        return Fail("not critical: nu(H)=%d != n//2=%d" % (nu, n // 2))
    if n < 31:
        return Fail("below Carter bound n>=31")
    return Pass(witness={"nu_H": nu, "chi_G": n - nu})
```
χ and ω are gate **inputs** — compute them (via `invariants/matching`, `invariants/cliques`) before the
checks that consume them (RESEARCH Pitfall 4). No `assert` anywhere (RESEARCH: gate path must survive
`python -O` — mirror `verifier.py`'s `if not cond: raise` discipline).

---

### `src/alpha2/gate/runner.py` (middleware, ordered chain + outcome type)

**Analogs:** `solvers/result.py` (the frozen outcome-dataclass + `__post_init__` raising discipline) and
`solvers/differential.py` (a stdlib-only verdict function whose every guard raises).

**Outcome type — copy the `Status` enum + validated-dataclass shape** (`result.py:33-43, 95-129`):
```python
class Status(Enum):
    MODEL_FOUND = auto()
    PROVED_OPTIMAL = auto()
    ...
    def __post_init__(self):
        if ...: raise ValueError(...)   # every guard RAISES, never assert (python -O safe)
```
Model the gate outcome as `PASS | FAIL(witness) | ERROR(trace)` in the same raises-only spirit.

**Chain + verdict discipline — copy `differential_verdict`'s "compose, guard, raise" shape**
(`differential.py:57-108`): the runner walks `[(name, tier, check_fn), ...]` in cost order; a **hard**
FAIL raises/returns `GateKill(reason=name, witness=...)`; a **flag_only** FAIL is recorded and execution
continues; ERROR quarantines (never a kill). **D-01 (LOCKED): hard set = {G1 `nu==n//2` crit, G2
tf/diam2, connectivity}; G3-deep/G4/G5/G6 = flag_only** — seed-137 passes the hard set and its G3/G4
flags travel on the record without stopping the pipeline.

---

### `src/alpha2/battery/pipeline.py` (controller, 7-step runbook) — EXACT ANALOG

**Analog:** `repro/baseline.py:34-68` (`run_instance`) is the driver skeleton; `repro/cayley_run.py:39-73`
adds the **per-step budget as config, not code** (`time_budget=`) and params-provenance; and
`tests/test_seed137_regression.py:76-119` is the SC1 **in-memory dual-backend kill** template.

**Driver skeleton — the generate → nu → chi → search → witness → build_record path** (`baseline.py:41-64`):
```python
rng = random.Random(seed)
adj, m = triangle_free_process(n, rng)                      # consumes rng FIRST (single-RNG contract v1)
nu = matching_number(adj, n)
chi = n - nu
sets, init_conf, moves, restarts, tsolve = solve(adj, n, chi, rng)  # SAME rng, next
if sets is None:
    raise RuntimeError(f"heuristic search timed out ... — no model found")  # never silent fall-through
M, U, nu2 = extract_witness(adj, n)
H_edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
rec = schema.build_record(provenance=schema.provenance_seed(...), H_edges=H_edges,
    nu_H=nu, chi_G=chi, model_branch_sets=[list(s) for s in sets], matching_M=M,
    tutte_berge_U=U, method="heuristic", omega_G=None, verified=True)
```
**Config-not-code budget** (`cayley_run.py:39` signature): `def run_instance(..., time_budget=60.0)` and
`solve(adj, p, chi, rng, time_budget=time_budget)` — per-step budgets are parameters echoed into every
log line (RESEARCH Pitfall 5), never literals.

**Step [4] dual-backend had₂ → licensed verdict** (RESEARCH Code Examples; `tests/test_differential.py:118-121`):
```python
from alpha2.solvers.backend import get_backend
from alpha2.solvers.differential import differential_verdict, CriticalDisagreement
from alpha2.solvers.result import SolveParams
a = get_backend("cbc").solve_had2(adj, n, mode="optimize", params=SolveParams(time_limit_s=budget))
b = get_backend("cpsat").solve_had2(adj, n, mode="optimize", params=SolveParams(time_limit_s=budget))
try:
    verdict = differential_verdict(a, b, chi)   # "AGREED_KILL" | "SHC_CANDIDATE" | "INSUFFICIENT"
except CriticalDisagreement:
    quarantine_and_halt()                       # release-blocking; never pick a winner
# INSUFFICIENT (a timeout on either side) => RESISTANT queue; NEVER from a heuristic miss.
```

**SC1 in-memory kill (corpus byte-untouched) — copy `test_seed137_regression.py:100-119`** almost
verbatim: build the record from the FULL `out.family` (`len == had_2 == 17`), stamp
`backends["cbc"] = f"CBC {cbc_binary_version()}"`, then `k = verify_certificate(rec)` OUTSIDE any truth
expression (call, bind `k`, compare). **Do NOT `store.append_certificate` seed-137** — RESEARCH Runtime
State + Anti-Pattern: route SC1 through the in-memory record, leaving the frozen corpus untouched.

**Status honesty (LOCKED):** heuristic "not found" is an unconditional edge to the exact solver, NEVER
RESISTANT; RESISTANT is reachable ONLY via an exact-method timeout (`INSUFFICIENT`). SHC-CANDIDATE is
licensed ONLY by `differential_verdict` on two equal `PROVED_OPTIMAL`.

---

### `src/alpha2/battery/log.py` (store, append-only JSONL)

**Analog:** `corpus/store.py:86-144` — the append-only, atomic, verify-context write. The results log is a
**simpler, separate contract** (JSONL, every event; no hash-chain/verifier gate — that is the corpus's
job, RESEARCH Pattern 4), but copy the **atomic-write + path-from-`paths.py`** discipline:

**Atomic append idiom** (`store.py:94-96, 132-143`):
```python
if path is None:
    path = paths.ensure_parent(paths.RESULTS_LOG)   # NEW paths entry — never embed a literal path
path = os.fspath(path)
...
# atomic: tempfile in SAME dir -> flush -> os.fsync -> os.replace (crash sees old or new, never torn)
```
For JSONL, append one `json.dumps(event) + "\n"` line per terminal state (CLI-02 required fields:
terminal state + method + certificate ref + reason + seed/provenance). Path MUST come from a new
`paths.RESULTS_LOG` (see below), never a hard-coded string (`paths.py` is the sole path authority).

---

### `src/alpha2/status/views.py` (view, derived read over immutable facts)

**Analog:** `corpus/manifest.py:50-99` — the "load immutable records, derive a keyed view, pure read,
never edit" pattern. This is exactly VRF-03's derived-status shape.

**Load-and-derive pattern** (`manifest.py:50-77, 90-92`):
```python
def build_manifest(records):        # -> build_status_view(corpus_records, log_events)
    view = {}
    for rec in records:
        key = manifest_key(rec)                     # -> status key per instance
        ...                                          # DERIVE only; raise on duplicate/drift
        view[key] = {...}
    return view

with open(corpus_path) as fh:       # READ-ONLY load; transitions never edit a stored record
    records = json.load(fh)
```
Status is a **pure function of (immutable corpus records + append-only log events)** computed on read
(KILLED / SHC-CANDIDATE / RESISTANT). The store is append-only by construction (`store.py`), so the view
must ONLY read. RESISTANT only via exact-method timeout.

---

### `src/alpha2/cli.py` (controller, argparse subcommands)

**Analog:** `corpus/manifest.py:102-112` and every `repro/*.main()` — the thin-`main()` + `__main__`-guard
dispatch shape. **argparse itself has no in-repo analog** (no module currently imports it — verified);
use RESEARCH Standard Stack guidance (stdlib argparse, zero new deps).

**Thin main + guard** (`manifest.py:102-112`):
```python
def main():
    ...            # no logic; parse args, dispatch to battery.pipeline / status.views
if __name__ == "__main__":
    main()
```
Keep the CLI thin (no math, no orchestration logic — delegate to `battery.pipeline` / `status.views`).
Input validation (V5): `--family` ∈ known pools, `n` positive int, `seed` int, via argparse `type=`. The
entry point registered in `pyproject.toml` calls `alpha2.cli:main` (see below).

---

### `src/alpha2/search/heuristic.py` (**modify** `solve` — the seed-137 fix, SRCH-01) — SELF ANALOG

**Analog:** the current `solve()` itself (`heuristic.py:99-157`). Rewrite ONLY the profile-selection head;
preserve the local-search body and instrumentation return tuple.

**The spanning-only head to REPLACE** (`heuristic.py:99-101`):
```python
def solve(adj, n, k, rng, time_budget=90.0):
    p = n - k; s = 2 * k - n
    assert p >= 0 and s >= 0 and 2 * p + s == n     # <-- single spanning profile; MISSES seed-137
```
Replace with a **profile enumeration** `(p', s')` where `p' + s' = χ` and `2p' + s' ≤ n` (i.e. `s'` from
`max(0, 2χ − n)` up to `χ`), each with its own restart budget, allowing unused vertices — **never an
`assert`** (it crashes on pool instances with χ < n/2; RESEARCH Pitfall 2 / Pattern 2).

**Preserve byte-for-byte** (`heuristic.py:115`, module is ruff-excluded in `pyproject.toml:32-36`):
```python
pr = tuple(conf)[rng.randrange(len(conf))]   # determinism-sensitive; do NOT reformat / ruff --fix
```
**Keep the instrumentation return contract** (`heuristic.py:156-157`): `return sets, best_init, moves,
restarts, elapsed` (SRCH-02 exposes restarts-to-solution + initial-conflicts). A miss returns
`sets=None` — the pipeline treats that as an unconditional edge to exact, NEVER RESISTANT.

**Regression seed** (SRCH-01 test): the D.3 model is 9 pairs + 7 singletons = 25 vertices, 6 unused — add
a unit test that the rewritten data structure can even *hold* that non-spanning state.

---

### `src/alpha2/paths.py` (**modify** — add `RESULTS_LOG`) — SELF ANALOG

**Analog:** `paths.py:12-18` itself. Add one constant beside `CORPUS`, same `REPO_ROOT / "data" / ...`
shape; `ensure_parent` already generalizes over any path:
```python
CORPUS = REPO_ROOT / "data" / "corpus" / "hadwiger_alpha2_certificates.json"
RESULTS_LOG = REPO_ROOT / "data" / "results" / "battery_results.jsonl"   # NEW — sole path authority
```

---

### `pyproject.toml` (**modify** — add `[project.scripts]`) — SELF ANALOG

**Analog:** `pyproject.toml:1-14` itself. No `[project.scripts]` exists (verified). Add the entry point
(Runtime State: `alpha2` console command); dependencies stay unchanged (zero new deps):
```toml
[project.scripts]
alpha2 = "alpha2.cli:main"
```

---

## Shared Patterns

### Raises-only guards (NO `assert` in gate/verify/status/battery paths)
**Source:** `solvers/result.py:95-129`, `solvers/differential.py`, `corpus/verifier.py:34-70`,
`corpus/store.py`.
**Apply to:** `gate/checks.py`, `gate/runner.py`, `battery/pipeline.py`, `status/views.py`, `cli.py`.
Every guard is `if not cond: raise ...` — `assert` is a no-op under `python -O` (the project's standing CI
canary). The lone permitted `assert` precedent is accounting-only, never a verification decision
(`sweep.py:82` `assert len(instances) == 269`).

### The trust root / differential gate is the SOLE authority
**Source:** `corpus/verifier.py:223-243` (`verify_certificate` returns `k`), `solvers/differential.py:57-108`.
**Apply to:** `battery/pipeline.py` (kill/SHC decisions), `status/views.py` (never re-derive truth).
A solver family is an UNTRUSTED proposal until `verify_certificate` arbitrates; SHC-CANDIDATE is licensed
ONLY by `differential_verdict`. Call the trust root OUTSIDE any truth-expression (call → bind `k` →
compare), per `test_seed137_regression.py:118`.

### Record assembly — always `schema.build_record` + tagged-union provenance
**Source:** `corpus/schema.py:104-122` (`provenance_seed`/`provenance_params`/`provenance_graph6`),
`schema.py:246-310` (`build_record`).
**Apply to:** `battery/pipeline.py`. Never hand-assemble a dict; `build_record` refuses `fam[:chi]`
truncation, derives `had_2 = len(model)`, and stamps reproduction/backends. Use
`provenance_seed(...)` for TFP, `provenance_params("cayley_maximal_sumfree_Zp", ...)` for Cayley
(`cayley_run.py:60`).

### Paths only from `paths.py`; append-only + atomic writes
**Source:** `paths.py`, `corpus/store.py:132-143`.
**Apply to:** `battery/log.py`, `status/views.py`. No module embeds a filesystem path;
tempfile→fsync→`os.replace` for any file the reader/crash must never see torn.

### Single-RNG determinism contract v1
**Source:** `repro/baseline.py:11-13, 41-46`, `repro/cayley_run.py:10-12`.
**Apply to:** `battery/pipeline.py`. One `random.Random(seed)` feeds the generator FIRST, then `solve`,
in that order — never a per-stage subseed. Deterministic in (n, seed); budgets logged per run.

---

## No Analog Found

| Concern | Role | Data Flow | Reason / Mitigation |
|---------|------|-----------|---------------------|
| `cli.py` argparse subcommand parsing | controller | request-response | No module imports `argparse` today (verified). Dispatch/`__main__` shape exists (`manifest.py:102-112`), but the argparse subparser wiring itself follows RESEARCH Standard Stack (stdlib argparse), not an in-repo analog. |
| `gate/safe_families.py` GATE-03 map completeness | config/data | lookup | Only a *shape* analog exists (`manifest.py:36-47` family→key map). The settled/open family map with citations is new data; MVP may stub with "screen not yet active" logging (RESEARCH GATE-03). |
| JSONL line format (vs the corpus's JSON-array store) | store | append | `store.py` is a JSON-array with hash-chain + verifier gate; the results log is deliberately a *different, simpler* contract (append-only JSONL, no chain). Copy only the atomic-write + path discipline, not the chain/verify machinery. |

---

## Metadata

**Analog search scope:** `src/alpha2/{invariants,search,solvers,corpus,generators,repro}/`, `src/alpha2/paths.py`,
`pyproject.toml`, `tests/`.
**Files scanned (read in full or targeted):** `repro/{baseline,sweep,seed137,cayley_run}.py`,
`search/heuristic.py`, `invariants/matching.py`, `corpus/{schema,store,verifier,manifest}.py`,
`solvers/{backend,differential,result}.py`, `generators/{tfp,cayley}.py`, `paths.py`, `pyproject.toml`,
`tests/test_seed137_regression.py`, `tests/test_differential.py`.
**Pattern extraction date:** 2026-07-22
