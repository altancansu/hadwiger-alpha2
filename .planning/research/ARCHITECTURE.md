# Architecture Research

**Domain:** Reproducible computational research harness (hunt-and-certify pipeline for the Hadwiger α = 2 program)
**Researched:** 2026-07-21
**Confidence:** HIGH (component design and build order derived directly from the Appendix C source and PROJECT.md constraints; solver-determinism and packaging claims verified against authoritative docs)

---

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                              │
│  ┌──────────────┐   ┌───────────────────────┐   ┌─────────────────────┐   │
│  │  cli/        │──▶│  battery/pipeline     │   │  repro/  (frozen    │   │
│  │  subcommands │   │  (steps 1–7, statuses)│   │  legacy drivers)    │   │
│  └──────────────┘   └───────────┬───────────┘   └──────────┬──────────┘   │
├─────────────────────────────────┼──────────────────────────┼──────────────┤
│                        PROPOSER LAYER (all output UNTRUSTED)              │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────────────┐   │
│  │ generators/│─▶│  gate/   │─▶│ invariants/│─▶│ search/ (heuristic)  │   │
│  │ P0…P7      │  │ G1–G6    │  │ ν, χ, ω    │  │  + solvers/ (exact)  │   │
│  └────────────┘  └──────────┘  └────────────┘  └──────────┬───────────┘   │
│                                                           │ proposed      │
│                                                           │ models        │
├───────────────────────────────────────────────────────────▼───────────────┤
│                        TRUST ROOT (pure, stdlib-only)                     │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  verify/  — independent model verifier + record re-verification     │  │
│  │  (imports NOTHING from generators/search/solvers)                   │  │
│  └───────────────────────────────┬─────────────────────────────────────┘  │
├──────────────────────────────────┼────────────────────────────────────────┤
│                        PERSISTENCE LAYER                                  │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│  │ corpus/ (append-only │  │ manifest (golden │  │ results-log        │   │
│  │ JSON certificates)   │  │ hashes per seed) │  │ (JSONL, every run) │   │
│  └──────────┬───────────┘  └──────────────────┘  └────────────────────┘   │
├─────────────┼─────────────────────────────────────────────────────────────┤
│             ▼          ADVERSARIAL LAYER (read-only consumers)            │
│  ┌─────────────────────────────────┐  ┌───────────────────────────────┐   │
│  │ falsify/ — Falsification-Rule   │  │ falsify/audit — Monotonicity  │   │
│  │ runner (args vs corpus)         │  │ Audit (static metadata gate)  │   │
│  └─────────────────────────────────┘  └───────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

The single most important structural fact: **everything above `verify/` is a proposer; only `verify/` confers truth.** Generators propose candidates, the heuristic proposes models, solvers propose models *and* value claims. Nothing enters the corpus as a fact until the verifier passes it (existence claims) or the dual-backend agreement protocol passes it (impossibility-flavored value claims — see the Asymmetry pattern below).

### Component Responsibilities

| Component | Responsibility | Purity / determinism requirement | Typical implementation |
|-----------|----------------|----------------------------------|------------------------|
| `graphs` | Core adj-set representation (`list[set[int]]` as in Appendix C), canonical edge-list serialization, graph6 decode, SHA-256 hashing of canonical form | **Pure, deterministic.** No I/O, no RNG | Thin module; keep the raw `list[set]` type — do NOT wrap in a class that changes iteration semantics (corpus reproduction depends on the current code paths) |
| `generators/` (P0–P7, one module per pool) | `(params, seed) → H` (adj-set) plus an instance descriptor (family id, params, seed) | **Deterministic in (params, seed).** RNG injected as `random.Random` argument, never global. Exhaustive generator is deterministic per (geng version, flags, res/mod shard) | Ported `triangle_free_process`, `random_maximal_symmetric_sumfree`+`cayley_adj`; new pools follow the same signature; geng behind a subprocess adapter |
| `gate/` | Ordered chain G1–G6, cheapest first, kill on first failure, structured reason | **Pure predicates** over (H, invariants-so-far). Cost tier annotated per check | List of `(name, cost_tier, check_fn)`; configured per pool; exact G1–G6 semantics pinned from the Phase-2 runbook, mechanism built now |
| `invariants/` | Exact ν(H) via Edmonds blossom → χ(G) = n − ν; ω(G) = α(H); triangle-free / edge-maximality (diameter-2) checks | **Pure; VALUES canonical** (ν, χ, ω are well-defined numbers). Witness objects (which matching, which clique) are NOT canonical across networkx versions — store values, verify witnesses | Ported `matching_number`, `is_triangle_free`, `is_edge_maximal_tf`; networkx isolated HERE and only here |
| `search/` | Profile-general heuristic model search (ported `solve`, `initial_state`, conflict machinery) | Deterministic given (H, rng) **within a CPython version** (see set-iteration caveat in Reproducibility). Output is always an untrusted proposal | Verbatim port of Appendix C `solve()` and helpers |
| `solvers/` | ExactBackend interface; CBC (reference) and CP-SAT adapters; problem modules had2 / had3 / cdm; differential harness | **Not deterministic in general.** Pinned modes for recorded claims (CBC single-thread; CP-SAT `num_workers=1` or `interleave_search=true`). Output untrusted: proposals + status claims, versions always recorded | See ExactBackend pattern below |
| `verify/` | The trust root: `verify_model` (ported), record-level re-verification (re-derive invariants, check model against H), later an independent reduction auditor for negative claims | **MUST be pure, deterministic, stdlib-only, and import nothing from generators/search/solvers.** This is non-negotiable | Ported `verify_model` + `is_conflict` (verifier keeps its OWN copy of `is_conflict` — do not share the search module's) |
| `corpus/` | Append-only JSON certificate store, schema + versioning, atomic writes, canonical serialization, golden-hash manifest | Append-only; **deterministic serialization** (sorted keys, canonical separators) so hashes are stable; no record mutation ever | JSON file at `data/corpus/…json` (repo-relative), manifest as separate committed file |
| `battery/` | Per-candidate runbook steps 1–7 in cost order; status assignment KILLED / SHC-CANDIDATE / RESISTANT; logging of reason + seed on every kill | Deterministic given (config, seeds) modulo declared solver modes; every event logged | Orchestrator function calling the layers above; owns NO math |
| `falsify/` | ImpossibilityArgument interface, Monotonicity Audit registry, corpus-driven falsification runner | **Read-only** on corpus; deterministic per argument | Runner + protocol; arguments are plug-ins |
| `repro/` | The four frozen legacy drivers (baseline 12, sweep, cayley, seed-137 study) that DEFINE the 296-instance corpus | **Frozen after Phase 3** — these are the executable definition of the corpus; algorithm-preserving port only | `hadwiger_tfp.main`, `sweep`, `cayley_test.main`, `investigate_137` bodies relocated, paths made repo-relative, nothing else changed |
| `cli/` | Subcommands: `reproduce`, `battery`, `verify`, `diff-backends`, `falsify`, `status` | Thin; no logic | argparse-style subcommands (framework choice is STACK.md's call; keep `verify/` importable without any CLI deps) |

### Trust topology

```
UNTRUSTED PROPOSERS                    TRUST ROOT              FACT STORE
generators ─┐
gate ───────┤  candidates, claims
invariants ─┼────────────────────▶  verify/  ──pass──▶  corpus (append-only)
search ─────┤  proposed models         │
solvers ────┘  value claims            └──fail──▶  results-log only (never corpus)

Special case (impossibility-flavored): "had₂ < χ" has NO witness.
It enters the corpus only via: both backends PROVED_OPTIMAL + equal value
+ independent reduction audit (survivor protocol). See Asymmetry pattern.
```

---

## Recommended Project Structure

PyPA guidance favors the src layout: it forces tests to run against the *installed* package, prevents accidental import of the in-development copy via CWD, and makes editable installs behave like real installs — exactly the discipline a reproducibility-first project wants (verified: packaging.python.org src-layout discussion).

```
hadwiger-alpha2/
├── pyproject.toml              # pinned deps: networkx, pulp, ortools (exact versions)
├── src/alpha2/
│   ├── __init__.py
│   ├── paths.py                # THE single source of repo-relative data paths
│   ├── graphs.py               # adj-set core, canonical JSON edges, graph6, sha256
│   ├── generators/
│   │   ├── base.py             # Generator protocol + InstanceDescriptor
│   │   ├── tfp.py              # P1: Bohman process (ported verbatim, incl. RandomSet)
│   │   ├── cayley.py           # P2: sum-free Cayley (ported verbatim)
│   │   ├── exhaustive.py       # P0: geng -t subprocess stream + maximality filter
│   │   ├── hs_inflation.py     # P3   (parametric, seedless — descriptor carries params)
│   │   ├── kneser.py           # P4   (parametric)
│   │   ├── crooked.py          # P5   (parametric)
│   │   ├── ramsey.py           # P6   (base graphs + inflation params)
│   │   └── adversarial.py      # P7: flip-based local search (battery as fitness)
│   ├── gate/
│   │   ├── checks.py           # G1–G6 predicate implementations
│   │   └── runner.py           # cost-ordered chain, kill-on-first-failure + reason
│   ├── invariants/
│   │   ├── matching.py         # ν via networkx blossom; χ = n − ν
│   │   ├── cliques.py          # ω(G) = α(H)
│   │   ├── structure.py        # triangle-free, edge-maximal (diameter-2)
│   │   └── witnesses.py        # (later) max matching M + Tutte–Berge set U extraction
│   ├── search/
│   │   └── heuristic.py        # ported solve/initial_state/conflict machinery
│   ├── solvers/
│   │   ├── result.py           # ExactOutcome, Status enum, SolveParams
│   │   ├── backend.py          # ExactBackend protocol + get_backend registry
│   │   ├── cbc.py              # pulp/CBC adapter (ports ilp_had2 + status discipline)
│   │   ├── cpsat.py            # OR-Tools CP-SAT adapter (hints, determinism knobs)
│   │   ├── problems/
│   │   │   ├── had2.py         # backend-neutral variable/conflict enumeration
│   │   │   ├── had3.py         # branch-set-≤3 escalation model
│   │   │   └── cdm.py          # connected dominating matching (P0), cut-loop inside
│   │   └── differential.py     # dual-backend agreement harness
│   ├── verify/
│   │   ├── model.py            # trust root: verify_model + OWN is_conflict copy
│   │   ├── record.py           # re-verify a corpus record end-to-end
│   │   └── reduction.py        # (survivor protocol) independent had2-reduction audit
│   ├── corpus/
│   │   ├── schema.py           # record schema v1, versioned
│   │   ├── store.py            # append-only, atomic write (tmp+rename), canonical JSON
│   │   └── manifest.py         # golden sha256 of H_edges per (family, n|p, seed)
│   ├── battery/
│   │   └── pipeline.py         # steps 1–7, status machine, results-log emission
│   ├── falsify/
│   │   ├── interface.py        # ImpossibilityArgument protocol, Verdict enum
│   │   ├── audit.py            # Monotonicity Audit: invariant-tag registry
│   │   └── runner.py           # corpus-driven falsification suite
│   ├── repro/
│   │   ├── baseline.py         # = hadwiger_tfp main() (12 instances)
│   │   ├── sweep.py            # = sweep.py (270 + 2 showpieces)
│   │   ├── cayley_run.py       # = cayley_test main() (12 instances)
│   │   └── seed137.py          # = investigate_137
│   └── cli.py
├── data/
│   ├── corpus/hadwiger_alpha2_certificates.json     # regenerated, then guarded
│   ├── manifests/corpus-v1.manifest.json            # golden hashes, committed
│   └── results-log/                                  # JSONL per run, append-only
├── tests/
│   ├── unit/                   # invariants, conflicts, gate, store
│   ├── certificates/           # R1: every stored cert re-verifies
│   ├── determinism/            # R2: golden hashes for a pinned instance panel
│   ├── differential/           # CBC vs CP-SAT agreement panel
│   └── slow/                   # R3: full pipeline replay slices (release gate)
└── scripts/                    # thin shims: python -m alpha2.repro.baseline etc.
```

### Structure Rationale

- **`verify/` has its own copy of `is_conflict`.** Today `verify_model` calls the same `is_conflict` used by the search — a shared-bug channel. The trust root must be independently implemented (it is 10 lines; duplicate it deliberately and test the two copies against each other).
- **`repro/` is separate from `battery/`.** The four legacy drivers are the *executable definition* of the 296-instance corpus, including their exact RNG-sharing behavior (one `random.Random(seed)` feeds both the process and the heuristic). They get frozen after reproduction succeeds. The battery is the forward-looking pipeline; it may evolve. Never make corpus reproduction depend on battery evolution.
- **`solvers/problems/` is backend-neutral.** The combinatorics of "which branch-set pairs conflict" is defined once (pure, unit-tested) and translated by each backend. Differential testing then isolates solver/encoding-translation bugs; the verifier independently catches enumeration bugs on the existence side; `verify/reduction.py` audits the enumeration on the (rare, radioactive) impossibility side.
- **`paths.py` is the only place a path is constructed.** The sandbox-path problem (`/mnt/user-data/outputs/...` hard-coded inside functions in all four scripts) becomes a one-line fix per driver, and tests can point the store at tmp dirs.

---

## Architectural Patterns

### Pattern 1: Verifier as Trust Root (untrusted proposers, trusted checker)

**What:** Every model-producing component (heuristic, CBC, CP-SAT, future exhaustive search) returns *proposals*. A single pure, stdlib-only verifier checks disjointness, sizes, G-edge-ness of pairs, and all C(χ,2) pairwise adjacencies. Status assignment and corpus writes happen only downstream of the verifier.
**When to use:** Always — it is the codebase's enforcement of "nothing counts as found until the independent verifier passes."
**Trade-offs:** Slight duplication (verifier reimplements adjacency logic). That duplication is the point.

### Pattern 2: ExactBackend interface with a proven-optimality contract

**What:** One protocol, two engines, three problems, two modes. The critical design element is the `Status` enum separating *incumbent values* from *proven optima* — the legacy `ilp_had2` conflates them (it does `val = pulp.value(prob.objective); had2 = int(round(val))` without checking `prob.status`, so a CBC timeout with an incumbent would be silently reported as an exact `had2`). Harmless on the existence side (the verifier rules), but on the impossibility side (`had2 < χ` ⇒ SHC-candidate) it is a soundness hole. The interface closes it.

```python
class Status(Enum):
    MODEL_FOUND      = auto()   # decision mode: feasible witness produced (→ verify/)
    PROVED_OPTIMAL   = auto()   # optimize mode: value is exact (value == bound)
    PROVED_INFEASIBLE= auto()   # decision mode: target k proven unreachable
    INCUMBENT_ONLY   = auto()   # timeout; value = best found, NOT exact
    UNKNOWN          = auto()   # timeout, nothing usable
    ERROR            = auto()

@dataclass(frozen=True)
class SolveParams:
    time_limit_s: float
    seed: int                   # solver seed, recorded verbatim
    workers: int = 1            # 1 = deterministic mode (recorded claims)
    hint: tuple | None = None   # warm start from heuristic near-miss

@dataclass(frozen=True)
class ExactOutcome:
    problem: str                # "had2" | "had3" | "cdm"
    mode: str                   # "decision" | "optimize"
    status: Status
    value: int | None           # optimum iff PROVED_OPTIMAL
    bound: int | None           # best proven dual bound
    family: tuple[tuple[int, ...], ...] | None   # UNTRUSTED proposal
    backend: str                # "cbc" | "cpsat"
    backend_version: str        # recorded: pulp/CBC and ortools versions
    params: SolveParams
    wall_time_s: float

class ExactBackend(Protocol):
    name: str
    def solve_had2(self, H, *, mode, target_k=None, params) -> ExactOutcome: ...
    def solve_had3(self, H, *, mode, target_k=None, params) -> ExactOutcome: ...
    def solve_cdm(self,  H, *, params) -> ExactOutcome: ...

def get_backend(name: Literal["cbc", "cpsat"]) -> ExactBackend: ...
```

- **Decision vs optimize:** `decision` mode asks "does a family of size ≥ χ exist?" (constraint `Σ ≥ k`, no objective) — cheap, stops at first feasible, ideal for kills. `optimize` mode computes exact `had2` — required for any `had2 < χ` claim. This maps the Asymmetry Principle directly onto solver calls: existence needs only feasibility + verification; impossibility needs proven optimality.
- **Backend-neutral problem modules:** `problems/had2.py` enumerates variables (G-edges, vertices) and the three conflict families (pair–pair, single–pair, single–single) as pure data; `cbc.py`/`cpsat.py` translate to pulp constraints / `AddAtMostOne`+`Maximize`. Both backends provably solve the same instance.
- **CDM connectivity:** connectivity is not a packing constraint. `problems/cdm.py` owns a lazy-separation loop (solve → check connectivity of matched subgraph → add cut → re-solve) and drives whichever backend it is given. Backends stay stateless single-shot; problem modules own iteration.
- **Extraction:** the legacy `sets = fam[:chi]` trick (any χ-subset of a pairwise-adjacent family is pairwise-adjacent) stays, but in the adapter, followed by mandatory `verify_model`.

**Differential testing protocol (question 5):**

1. **CI panel (routine):** a pinned set — seed-137 (`had2 = 17`), 2–3 small TFP instances, one small Cayley, plus tiny closed-form graphs with hand-computed values. Both backends run `optimize`; assert both `PROVED_OPTIMAL` with equal `value`; both extracted families independently pass `verify_model`.
2. **Negative-claim rule (mandatory):** no `SHC-CANDIDATE` status is ever assigned from one backend. `had2 < χ` requires `PROVED_OPTIMAL` from **both** CBC and CP-SAT with equal values, in deterministic mode, versions recorded, plus (survivor protocol) an independent re-derivation of the conflict enumeration via `verify/reduction.py`.
3. **Metamorphic cross-checks:** any verified model of size k proves `had2 ≥ k`; if a solver returns `PROVED_OPTIMAL` with `value < k` while a verified size-k model exists, that is a hard CRITICAL error (verifier trumps solver, instance quarantined, no corpus write).
4. **Disagreement handling:** unequal proven optima → CRITICAL log entry, both raw outcomes persisted to results-log, instance quarantined. This is a solver bug or encoding-translation bug by construction, and it must halt the batch, not be skipped.

### Pattern 3: RNG Contract v1 (frozen) vs v2 (derived)

**What:** All randomness flows through explicitly passed `random.Random` objects — the Appendix C code already does this; keep it absolute (no module-level `random.*` calls anywhere).
- **Contract v1 (legacy, frozen):** `run_instance` seeds ONE `random.Random(seed)` and lets the triangle-free process and then the heuristic consume the *same stream*. The stored heuristic certificates depend on this exact consumption order. The `repro/` drivers preserve it byte-for-byte, forever.
- **Contract v2 (new pools):** derive independent integer subseeds per stage so stages can evolve independently: `sub = int.from_bytes(hashlib.sha256(f"{seed}:{channel}".encode()).digest()[:8], "big")` with channels `"gen"`, `"search"`, `"solver"`, `"restart:{i}"`. Never seed `random.Random` with tuples or other hashables (falls back to `hash()`), and never rely on `PYTHONHASHSEED`-dependent values. str/bytes seeding and int seeding are the only safe forms.

**Trade-offs:** carrying two contracts is mild complexity; collapsing to one would either break corpus reproduction (if v1 is dropped) or freeze all new pools into a fragile shared-stream design (if v2 is dropped).

### Pattern 4: Append-only facts, derived statuses

**What:** The corpus stores immutable *facts* (certificates: instance identity, invariants, verified model, method, solver metadata). Instance *status* (KILLED / SHC-CANDIDATE / RESISTANT) is a *derived view* computed from corpus + results-log, never stored as a mutable field.
**Why:** statuses transition (RESISTANT → KILLED after a longer budget; SHC-CANDIDATE → KILLED-with-shc-flag after had3 succeeds). Deriving them means no record is ever edited, the falsification suite always reads a consistent fact base, and history is fully auditable.
**Trade-offs:** `alpha2 status` must scan the log; trivial at this scale.

### Pattern 5: Golden-hash manifest ("store witnesses, not transcripts")

**What:** A committed manifest maps every corpus instance `(family, n|p, seed)` → `sha256(canonical H_edges JSON)`, plus ν, χ. Canonical JSON = sorted keys, `separators=(",", ":")`, edge lists sorted `[min,max]` pairs (the code already sorts).
**Why:** (a) generator determinism becomes a seconds-fast CI check with no solving; (b) it decouples certificate validity from search replay — a certificate is valid iff regenerated H matches the manifest hash AND the stored model verifies against it; (c) it detects any environment drift (Python version, refactor) immediately and loudly.
**Trade-offs:** none meaningful; the manifest is a few hundred lines.

### Pattern 6: Generator protocol with three shapes

**What:** All pools implement one descriptor-producing protocol, but there are three generation shapes the schema must accommodate:
- **Seeded stochastic** (P1 TFP, P2 Cayley, P7 adversarial): identity = `(family, n|p, seed)`.
- **Parametric deterministic** (P3 Higman–Sims inflations, P4 Kneser `K(n,k,≥t)`, P5 crooked, P6 Ramsey inflations): identity = `(family, params_dict)`, no seed. The schema's `seed` field must be optional with `params` required.
- **Exhaustive stream** (P0): identity = `(geng_version, flags, res/mod shard, index-in-stream)` plus the graph6 string itself. Store the graph6 string — it is its own certificate of identity.

### Pattern 7: Gate as a configured predicate chain

**What:** `gate/runner.py` executes `[(name, cost_tier, check_fn), ...]` in cost order, stopping at the first failure with a structured `GateKill(reason=name, detail=...)`; the battery logs reason + seed and moves on. Checks visible in the existing code and program text: H triangle-free (validity assert), H edge-maximal / diameter-2, connectivity, size/parity window; plus a cheap fast-path worth building in: if ω(G) ≥ χ(G), the max clique itself is a verified K_χ model with singleton branch sets — instant certificate, no search.
**Note:** the precise G1–G6 semantics come from the author's Phase-2 runbook; the architecture ships the mechanism (ordered, cost-annotated, pluggable, per-pool configurable) so the runbook drops in as configuration, not code surgery.

### Pattern 8: Falsification suite as corpus-driven adversarial runner

**What:** Any impossibility argument is a plug-in:

```python
class Verdict(Enum):
    PROVES_IMPOSSIBLE = auto()   # the argument claims no K_k minor exists in G
    DECLINES          = auto()   # the argument cannot conclude on this instance
    NOT_APPLICABLE    = auto()   # instance outside the argument's stated scope

@dataclass(frozen=True)
class ArgumentMeta:
    name: str
    invariants_used: tuple[str, ...]   # tags checked against the audit registry
    claimed_scope: str

class ImpossibilityArgument(Protocol):
    meta: ArgumentMeta
    def evaluate(self, G_adj, k: int) -> Verdict: ...
```

The **Monotonicity Audit** is a *static* gate that runs before any evaluation: `invariants_used` tags are checked against a registry (`minor_monotone = {"colin_de_verdiere_mu", ...}`, `disqualified = {"rank", "spectral_gap", "rigidity", "minrank", ...}`). Arguments using disqualified tags are rejected at the door and never executed. The **runner** then loads every corpus record with a verified model, rebuilds G from stored `H_edges` (hash-checked against the manifest), calls `evaluate(G, k=χ)`, and the argument is REFUTED the moment it returns `PROVES_IMPOSSIBLE` on any instance holding a verified model — with the refuting instance cited. Passing = zero `PROVES_IMPOSSIBLE` across the corpus. Every kill added to the corpus automatically strengthens this suite; the runner needs no changes as pools grow.

---

## Data Flow

### Per-candidate pipeline (the kill battery)

```
(family, params, seed)
      │  generators/  → H (adj-set) + descriptor
      ▼
[1] gate/ G1..G6 (cost order) ── fail Gi ──▶ status: KILLED(gate:Gi)   [results-log only]
      ▼ pass
[2] invariants/  ν(H) → χ(G) = n − ν  (exact, canonical); ω optional
      │            └── fast path: ω(G) ≥ χ → clique = verified singleton model → KILLED
      ▼
[3] search/ heuristic model search (budgeted)
      │ model proposal ──▶ verify/ ── pass ──▶ KILLED(model:heuristic) + corpus append
      ▼ not found (fact about the searcher, NOT the graph)
[4] solvers/ had2:
      decision mode "≥ χ?" ── SAT ──▶ family ──▶ verify/ ─ pass ─▶ KILLED(model:exact-had2) + corpus
      optimize mode ── PROVED_OPTIMAL had2 < χ (backend A)
      │                    └─▶ REQUIRED: backend B optimize, PROVED_OPTIMAL, equal value
      │                              agree ──▶ status: SHC-CANDIDATE  (certified SHC
      │                                        counterexample on this instance; corpus append
      │                                        of the value-fact with dual-backend metadata)
      ▼                              disagree ─▶ CRITICAL, quarantine, halt batch
[5] solvers/ had3 escalation (only for SHC-CANDIDATE):
      had3 ≥ χ model ──▶ verify/ (size-≤3 rules) ─ pass ─▶ KILLED(model:exact-had3),
      │                                                    record keeps shc_counterexample=true
      ▼ PROVED_OPTIMAL had3 < χ (dual-backend) ──▶ escalate: survivor protocol
[6] any TIMEOUT / UNKNOWN / INCUMBENT_ONLY at steps 4–5 within budget
      ──▶ status: RESISTANT  → survivor-protocol queue (longer budgets, CP-SAT scaling,
           symmetry breaking, parallel restarts with enumerated recorded seeds,
           second family-membership audit) — never an impossibility claim
[7] corpus append (only verified facts) + results-log append (every event)
```

### Status semantics (derived, not stored)

| Status | Meaning | Assignment condition |
|--------|---------|----------------------|
| `KILLED` | Instance is dead as an HC counterexample | Gate failure (reason `gate:Gi`) or a verified K_χ model (reason `model:heuristic` / `model:exact-had2` / `model:exact-had3`). Model kills append a certificate; gate kills log only |
| `SHC-CANDIDATE` | Certified counterexample to Seymour's strengthening on this instance | Both backends `PROVED_OPTIMAL`, equal value, `had2 < χ`, deterministic mode, versions recorded. This is a *prize*, and it is also radioactive: survivor-protocol handling before any publication-grade claim |
| `RESISTANT` | Exact methods inconclusive within budget | Solver `TIMEOUT`/`UNKNOWN`/`INCUMBENT_ONLY` on the decisive question. Heuristic failure alone NEVER produces RESISTANT (heuristic "not found" is a statement about the searcher — seed 137 is the standing lesson) |

### Corpus vs results-log (two stores, different contracts)

| | Certificate corpus | Results-log |
|---|---|---|
| Content | Verified facts only (existence certificates; dual-backend value facts) | Every event: gate kills + reasons, timeouts, solver stats, disagreements, run metadata |
| Mutability | Append-only, atomic writes, never edited | Append-only JSONL, one file per run |
| Consumers | Falsification suite, verifier tests, Lean (milestone 2) | Status derivation, resistance tracking (P1's open asymptotic question), debugging |

### Falsification-suite consumption

```
corpus.json ──▶ load records with verified model ──▶ manifest hash check on H_edges
     │                                                     │
     ▼                                                     ▼
audit.py: ArgumentMeta.invariants_used ⊆ minor-monotone registry?
     │ no → DISQUALIFIED (never runs)                      │ yes
     ▼                                                     ▼
runner: for each record: verdict = argument.evaluate(G, k=χ)
     any PROVES_IMPOSSIBLE → argument REFUTED (witness instance cited)
     else → report {declined: N, not_applicable: M} → argument SURVIVES the suite
```

---

## Build Order (dependency-ordered; maps to a FINE 8–12-phase roadmap)

The governing constraint ordering: **characterization before refactor** (reproduce the 296 with minimally-moved code, then refactor behind interfaces with the reproduction suite as the regression harness), and **certifiable rungs first** among pools (P0 CDM and SHC-detection early).

```
1 ─▶ 2 ─▶ 3 ─▶ 4 ─▶ 5 ─▶ 6 ─▶ 7 ─▶ 8 ─▶ 9 ─▶ 10 ─▶ 11
                │              └────────────▶ 12 (falsify: needs only 3 + 7 config;
                └── (12 partially parallel from here)         survivor part needs 6, 7)
```

| # | Phase | Delivers | Depends on | Rationale |
|---|-------|----------|------------|-----------|
| 1 | **Package scaffold + verbatim port** | src-layout `alpha2/` package; Appendix C code relocated into `graphs`, `generators/tfp`, `generators/cayley`, `invariants/`, `search/`, `verify/`, `repro/` with algorithms byte-preserved; `paths.py` replaces the sandbox path; pinned `pyproject.toml`. Exit: n=31 seed=1 runs from the repo and `H_edges` + the K₁₆ model match Appendix D exemplar D.2 | — | Everything imports from here. The ONLY code change allowed is the output path and import statements — the corpus definition must not drift before it is reproduced |
| 2 | **Corpus store + schema + verifier hardening** | Schema v1 (with optional `seed`, `params`, `graph6` fields for future pools); append-only atomic store; canonical JSON; `verify/record.py` re-verification; manifest module; verifier gets its own `is_conflict` | 1 | Reproduction (3) needs somewhere trustworthy to write and something independent to check with. Schema must be designed before 296 records exist in it |
| 3 | **Reproduce + verify the 296** | Run `repro/` drivers: baseline 12 + sweep 269 in-run (n=31 s100–299 incl. 137, n=51 s100–149, n=101 s100–119) + showpieces (301, 501) + Cayley 12 + seed-137 exact study; regenerate corpus JSON; all instances verified; seed-1 and seed-137 stored models byte-equal to Appendix D; freeze golden manifest (hashes for all 296). Exit: 296/296, manifest committed, `repro/` frozen | 1, 2 | This is the characterization suite for every later refactor, and the trust anchor for the whole program. Nothing downstream is safe to build until this passes |
| 4 | **Test suite + CI** | pytest layers: unit (conflict machinery, invariants, store atomicity); R1 certificate-validity over stored certs; R2 manifest determinism panel; a small R3 replay slice; CI with pinned Python + pinned deps; a canary job on a newer Python to detect `random`-module drift early | 3 | PROJECT.md: "the verifier and corpus reproduction run as tests." CI must exist before refactoring begins in 5 |
| 5 | **ExactBackend interface + CBC adapter** | `solvers/result.py`, `backend.py`, `problems/had2.py` (backend-neutral enumeration extracted from `ilp_had2`), `cbc.py`; decision + optimize modes; **status discipline fixing the incumbent/optimal conflation**; seed-137 regression: `had2 = 17`, `PROVED_OPTIMAL` | 3, 4 | First refactor under test. CBC is the reference; the interface shape is proven against known ground truth before a second engine exists |
| 6 | **CP-SAT backend + differential harness** | `cpsat.py` (`num_workers=1` deterministic default; `random_seed` recorded; optional exploration mode with workers>1 or `interleave_search=true`; `AddHint` warm starts from heuristic near-misses); `differential.py`; CI agreement panel (both backends, equal proven optima, both families verified) | 5 | The second engine and the cross-examination machinery. From here, dual-backend confirmation of negative claims is possible — the precondition for ever assigning SHC-CANDIDATE |
| 7 | **Battery pipeline + gate + CLI + results-log** | `battery/pipeline.py` (steps 1–7, cost order, status machine, reason+seed logging); `gate/` chain with runbook-configurable G1–G6 + ω ≥ χ fast path; JSONL results-log; `cli.py` (`reproduce`, `battery`, `verify`, `diff-backends`, `status`). Exit: `alpha2 battery --pool tfp --n 31 --seed 137` reproduces the case study end-to-end with correct statuses | 5, 6 | The "one tested CLI" Foundation requirement. Needs both backends so the status machine's dual-backend rule is real, not stubbed |
| 8 | **Branch-set-3 escalation (had3)** | `problems/had3.py` on both backends; `verify/` extension to size-≤3 branch sets; battery wiring of the SHC-CANDIDATE → had3 path; synthetic-target tests (no real SHC-candidate exists yet — 296/296 killed) | 6, 7 | Completes the pipeline contract in the Foundation requirement ("… → branch-set-3 escalation → …"). Built against synthetic instances so the path is proven before it is ever needed in anger |
| 9 | **nauty integration + P0 CDM frontier** | `generators/exhaustive.py`: `geng -t -c` subprocess stream, graph6 decode, res/mod sharding for deterministic work-splitting, own edge-maximality filter; `problems/cdm.py` (connectivity via lazy cut loop) on both backends; exhaustive 12–14-vertex run; CDM certificates into corpus. Exit: verified CDM frontier past n ≤ 11 | 6, 7 | The first NEW science, aimed at the most certifiable rung (a CDM counterexample is a single finitely-checkable graph). Wants CP-SAT (speed over thousands of instances) and the battery (logging/statuses), hence after 6–7 |
| 10 | **Pool expansion: P1/P2 at scale + P3–P6 generators** | P1 larger-n sweeps with resistance tracking (RESISTANT queue feeds the open asymptotic question); P2 general abelian groups + structured sum-free sets (RNG Contract v2); P3–P6 as parametric generator modules + pool configs. P3–P6 are mutually independent — the roadmap may split or parallelize them freely | 7 (and 8 for full escalation coverage) | Homogeneous work: each pool is a generator + config; zero new infrastructure. Ordering within the phase by construction difficulty (P4 Kneser trivial; P3 Higman–Sims needs the base graph; P6 needs Ramsey witness data) |
| 11 | **P7 adversarial search** | `generators/adversarial.py`: triangle-preserving flip local search over edge-maximal TF graphs; battery-as-fitness needs a cheap-mode pipeline call (gate + invariants + short heuristic only); exact-only reporting enforced by the status machine | 7, 10 (pattern maturity) | Last pool: it *consumes* the battery as a subroutine, so the battery API must be stable first |
| 12 | **Escalation harnesses: Falsification Rule + Monotonicity Audit + survivor protocol** | `falsify/` interface, audit registry, corpus runner + `alpha2 falsify`; survivor protocol runner (CP-SAT long budgets, symmetry breaking, parallel restarts with enumerated recorded seeds, `verify/reduction.py` independent reduction audit, second family-membership audit) | Falsify: 3 (corpus) + 7 (CLI). Survivor: 6, 7 | The falsification runner depends only on the corpus and can start any time after Phase 3 — schedule it as slack/parallel work. The survivor protocol needs the scaled CP-SAT machinery. Both must exist BEFORE any impossibility argument is entertained, per the Phase-3 program rules |

**Prerequisite call-outs for the roadmap:**
- Phases 1→2→3→4 are strictly sequential (each is the safety net for the next). Do not begin Phase 5 until 296/296 reproduces — the reproduction suite is what makes the solver refactor safe.
- Phase 6 gates everything that can ever assign `SHC-CANDIDATE` (7, 8, 9, 12-survivor).
- Phase 9 (P0) is deliberately ahead of Phase 10 (P1–P6 expansion): certifiability-first strategy.
- Phase 12's falsification half is the only genuinely order-flexible item (needs only 3 + a CLI hook); if the roadmap wants an early morale/discipline win, it can run right after Phase 7.

---

## Reproducibility Architecture

### Nondeterminism inventory and mitigations

| Source | Behavior | Mitigation |
|--------|----------|------------|
| `random.Random` cross-version | Official guarantee covers ONLY `random()` + seeding compatibility; `shuffle`, `randrange`, `sample` are explicitly "subject to change across Python versions" (docs.python.org, Notes on Reproducibility). In practice stable since 3.2/3.11, but the architecture must not *rest* on that | Pin the Python version in CI for corpus jobs; commit the golden-hash manifest (R2 catches any drift in seconds); keep full `H_edges` inline for the 27 stored certificates (self-contained even if regeneration ever drifts); record `python_version` in every corpus record; run a newer-Python canary job so drift is discovered on purpose, not by accident |
| Heuristic replay | `solve()` picks conflicts via `tuple(conf)[rng.randrange(len(conf))]` — **set iteration order** of int-tuples is deterministic within a CPython build but is an implementation detail across versions. Byte-exact search replay is therefore CPython-version-sensitive even with the same seed | Define certificate validity so it never requires replaying the search (see R1 below). Legacy drivers frozen; replay tested only in the pinned-CI environment (R3) |
| networkx blossom / max clique | The VALUES ν, χ, ω are canonical; the returned *witness* (which matching/clique) may vary across networkx versions | Store values, never trust witnesses without checking; when witnesses are stored (see hand-checkability upgrade), they are verified on read, so version drift is harmless |
| CBC via pulp | Single-threaded by default; deterministic for a fixed binary + fixed model construction order (edge enumeration is already ordered). With `timeLimit`, may return an incumbent that is NOT proven optimal | Pin pulp (which pins the bundled CBC); record solver version per outcome; `Status` discipline: `PROVED_OPTIMAL` only when the solver status says optimal |
| OR-Tools CP-SAT | With `num_workers > 1`, search is wall-clock-dependent and nondeterministic. Verified from `sat_parameters.proto`: `num_workers=1` means no parallelism; `random_seed` (default 1) reinitializes the solver RNG each solve; `interleave_search=true` makes the search "deterministic (independently of num_workers!)" (marked Experimental) | Two declared modes: *exploration* (workers free, results only steer) and *recorded* (`num_workers=1`, fixed `random_seed`, or `interleave_search=true` for deterministic parallel) — any outcome that touches the corpus or a status decision must come from recorded mode, with full params + `ortools` version in the record |
| geng | Output stream is canonical and deterministic for a fixed nauty version + flags + res/mod shard | Record `(geng_version, flags, shard, index)` in P0 descriptors; store the graph6 string itself in the record |

### The reproduction contract (three levels — this is what "reproduce the corpus" means)

- **R1 — Certificate validity (trust root; CI, every commit):** for each stored certificate: regenerate H from `(n|p, seed)` (or read inline `H_edges`), check sha256 against the manifest, re-derive ν/χ (values), run `verify_model` on the STORED `model_branch_sets`. Robust to any search/solver/networkx drift, because nothing is replayed — witnesses are checked, not re-found.
- **R2 — Generator determinism (CI, every commit, seconds):** regenerate a panel (full 296 nightly; a slice per-commit) and compare `H_edges` hashes to the manifest.
- **R3 — Full pipeline replay (release gate, slow):** rerun `repro/` drivers on the pinned environment; assert identical corpus JSON (including the heuristic-found models, which replay exactly under Contract v1 on the pinned CPython).

### Certificate anatomy (per record, self-contained and hand-checkable)

```json
{
  "schema_version": 1,
  "family": "triangle_free_process_complement",
  "n": 31, "seed": 137, "params": null,
  "H_edges": [[0,5], "..."],                  // inline for stored certs; hash always
  "h_edges_sha256": "…",
  "invariants": {"m": 177, "nu": 15, "chi": 16, "omega": 14},
  "model_branch_sets": [[2,20],[4,7],"…"],
  "verified": true, "verifier_version": "…",
  "method": "exact-cbc:optimize",
  "exact": {"problem": "had2", "value": 17, "status": "PROVED_OPTIMAL",
             "agreement": {"cbc": 17, "cpsat": 17},
             "params": {"time_limit_s": 300, "seed": 1, "workers": 1},
             "backend_versions": {"pulp/cbc": "…", "ortools": "…"}},
  "env": {"python": "3.x.y", "networkx": "…"},
  "created": "…"
}
```

Hand-checking a record requires only pencil work: branch sets disjoint with sizes ≤ 2; each pair absent from `H_edges` (a G-edge); every one of the C(χ,2) branch-set pairs has at least one cross pair absent from `H_edges`.

**The one trust gap, and the planned upgrade:** χ = n − ν currently *trusts* networkx's blossom for ν. To make χ hand-checkable (and Lean-checkable in milestone 2 without formalizing Edmonds' algorithm), add `invariants/witnesses.py`: store a maximum matching M (|M| = ν, trivially checkable ⇒ χ ≤ n − ν... i.e. ν ≥ |M|) plus a Tutte–Berge witness set U with `|U| + odd_components(H − U)` achieving `ν = ½(n − odd(H−U) + |U|)` (checkable ⇒ ν ≤ that value). U is computable from the Edmonds–Gallai decomposition, e.g. `D = {v : ν(H − v) = ν}`, `U = N(D) \ D` — n+1 matching calls, a batch job even at n = 501. Schedule this as a late Foundation or pre-Lean task; it converts every certificate into a fully witness-based object where the verifier (and later Lean) checks witnesses instead of trusting algorithms.

---

## Scaling Considerations

The scaling axes here are instance size and pool cardinality, not users.

| Scale | Pressure point | Architectural response |
|-------|----------------|------------------------|
| n ≈ 31–101 (critical sizes) | None — full pipeline in seconds/minutes | Default path; ILP optimize mode routine |
| n ≈ 301–501 (showpieces) | had2 model size: variables = \|E(G)\| = C(n,2) − \|E(H)\| ≈ 10⁵ at n = 501; naive pair–pair conflict enumeration is O(\|E(G)\|²) pair scans | Enumerate conflicts by common-H-neighborhood indexing rather than all-pairs (a pair–pair conflict requires {c,d} ⊆ N_H(a) ∩ N_H(b)); prefer decision mode + heuristic warm-start hints; keep optimize mode for small/critical n where impossibility claims would actually be tested |
| P0 exhaustive n = 12–14 | Triangle-free graph counts grow to ~10⁸ at n = 14 before maximality filtering | Stream from `geng -t -c` (never materialize), filter maximality with our own predicate, shard deterministically via geng's `res/mod` splitting across processes; record shard identity per instance. If throughput still hurts, evaluate a specialized maximal-triangle-free generator in phase research (flagged LOW confidence — verify options during Phase 9) |
| Survivor protocol / long budgets | CP-SAT multi-worker speed vs determinism | Exploration mode may use all cores; any *recorded* claim re-run in deterministic mode (`num_workers=1` or `interleave_search=true`); parallel restarts as enumerated `(attempt, seed)` pairs, every attempt logged |
| Corpus growth (hundreds → thousands of records) | Single JSON file append cost and diff noise | Acceptable through this milestone (append = read+write with atomic rename). If it becomes painful: shard corpus per family (`corpus/p1.json`, …) behind the same store API — do NOT introduce a database; JSON-on-disk is a deliverable ("self-contained JSON") and the Lean milestone consumes it directly |

---

## Anti-Patterns

### Anti-Pattern 1: Trusting solver incumbents as exact values

**What people do:** read the objective after `solve()` and treat it as the optimum — exactly what legacy `ilp_had2` does (`val = pulp.value(prob.objective)` with `timeLimit=300` and no status check).
**Why it's wrong:** with a time limit, CBC can return a feasible incumbent; calling it `had2` would let a timeout masquerade as an exact impossibility fact (`had2 < χ`) — the single most radioactive misstatement this program can make.
**Do this instead:** the `Status` contract — `value` is meaningful as an exact optimum only under `PROVED_OPTIMAL`; SHC-CANDIDATE additionally requires the second backend to agree.

### Anti-Pattern 2: Defining reproduction as byte-exact search replay everywhere

**What people do:** "rerun the script, diff the JSON" as the only notion of reproducibility.
**Why it's wrong:** heuristic replay depends on CPython set-iteration order and `random`-module internals that Python explicitly does not guarantee across versions; the corpus would look "broken" on any interpreter bump even though every certificate remains perfectly valid.
**Do this instead:** the three-level contract — R1 (verify stored witnesses against regenerated H; version-proof), R2 (golden hashes), R3 (full replay, pinned environment only).

### Anti-Pattern 3: Sharing verification code with the searcher

**What people do:** import the search module's `is_conflict` inside the verifier (the current code does).
**Why it's wrong:** a single bug in the adjacency predicate silently corrupts both the proposer and the checker — the exact failure mode an "independent verifier" exists to prevent.
**Do this instead:** `verify/` keeps its own implementations, stdlib-only, no imports from proposer modules; test the duplicate implementations against each other.

### Anti-Pattern 4: Mutable statuses inside corpus records

**What people do:** write `"status": "RESISTANT"` into a record, then edit it when the instance later dies.
**Why it's wrong:** editing certified records destroys auditability and makes the falsification suite's fact base unstable.
**Do this instead:** corpus stores immutable facts; statuses are derived views over corpus + results-log (Pattern 4).

### Anti-Pattern 5: Global RNG and clever seed derivation

**What people do:** `import random; random.shuffle(...)` at module level, or seeding `Random((seed, "search"))` with a tuple.
**Why it's wrong:** global state breaks (n, seed) determinism the moment call order changes; tuple seeding falls back to `hash()` semantics rather than the guaranteed int/str seeding path.
**Do this instead:** inject `random.Random` everywhere (already the codebase's style); derive subseeds only via integer arithmetic or sha256 of explicit strings (Contract v2).

### Anti-Pattern 6: Reporting heuristic outcomes as instance facts

**What people do:** classify an instance RESISTANT because the local search failed.
**Why it's wrong:** "not found" is a fact about the searcher — seed 137 resisted the heuristic solely because of a wrong profile assumption and fell to the exact ILP in one run.
**Do this instead:** the status machine makes RESISTANT reachable only through exact-method timeout; heuristic failure merely routes to step 4.

### Anti-Pattern 7: Premature generic solver abstraction

**What people do:** build a universal MIP-modeling IR so "any backend can solve any problem."
**Why it's wrong:** CDM needs a connectivity cut loop; had2/had3 are pure packing; a lowest-common-denominator IR either can't express the loop or grows into a modeling language. Two backends × three problems is a six-cell matrix, not a framework.
**Do this instead:** backend-neutral *enumeration* shared per problem, explicit per-backend translation, problem modules own any iteration (Pattern 2).

---

## Integration Points

### External tools/services

| Tool | Integration pattern | Notes |
|------|---------------------|-------|
| nauty `geng` | Subprocess adapter streaming graph6 lines (`geng -t -c [res/mod] n`); decode in `graphs.py` | Pin the nauty version; record version + full argv in P0 provenance; `-t` = triangle-free confirmed in the geng manpage; our own maximality filter runs on top (never trust an external filter for the science) |
| OR-Tools CP-SAT | `cpsat.py` adapter; `cp_model` build from backend-neutral enumeration; `AddHint` for warm starts | Pin `ortools` version; recorded-mode params (`num_workers=1`/`interleave_search`, `random_seed`) verified against `sat_parameters.proto`. Check wheel availability for the pinned Python before Phase 6 — if the local 3.9.6 is too old for the chosen OR-Tools release, pin a newer interpreter in the venv (the manifest + R2 make any interpreter change loud and testable) |
| pulp/CBC | `cbc.py` adapter around the ported `ilp_had2` construction | pulp wheels bundle a CBC binary — pinning pulp pins CBC; record versions in every `ExactOutcome`; status mapping is the load-bearing part |
| networkx | Confined to `invariants/` (blossom ν, max clique ω) | Values canonical; never persist unverified witnesses; pinned version recorded per record |
| CI (GitHub Actions or equivalent) | Jobs: unit + R1 + R2 (+ differential panel) per commit; R3 + full 296 nightly/release; newer-Python canary | Pin Python + all deps for corpus jobs; the canary job exists precisely to catch `random`/set-order drift on a schedule the team controls |

### Internal boundaries

| Boundary | Communication | Considerations |
|----------|---------------|----------------|
| generators ↔ battery | `(descriptor, H)` values | Generators never touch the store or solvers |
| battery ↔ solvers | `ExactBackend.solve_*` calls returning `ExactOutcome` | Battery never reads solver internals; only `ExactOutcome` |
| solvers ↔ verify | None direct — battery routes every proposed family through `verify/` | Solvers must not "self-verify" |
| verify ↔ everything | Import direction is one-way INTO verify from stdlib only | Enforce with an import-linter rule or a unit test that inspects `verify/` imports |
| corpus ↔ falsify | Read-only file access + manifest hash check | Falsify never writes corpus; refutations go to results-log/reports |
| repro ↔ everything else | Frozen after Phase 3; battery must never become a dependency of repro | Reproduction shields refactors; refactors must not touch reproduction |

---

## Sources

- Appendix C toolkit source and Appendix D certificate facts — `/Users/alton/projects/hadwiger-alpha2/.planning/reference/alpha2-program-source.md` (primary; HIGH — component boundaries, RNG usage, ILP construction, and the `ilp_had2` status-conflation finding read directly from code)
- Project constraints and pipeline definition — `/Users/alton/projects/hadwiger-alpha2/.planning/PROJECT.md` (primary; HIGH)
- CP-SAT determinism parameters (`random_seed`, `num_workers`, `interleave_search` — "deterministic (independently of num_workers!)") — [google/or-tools `sat_parameters.proto`](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto) (HIGH — authoritative parameter comments, fetched directly and via Context7 CLI)
- Python `random` reproducibility guarantees (only `random()` + compatible seeding guaranteed; `shuffle`/`randrange` "subject to change") — [docs.python.org/3/library/random.html](https://docs.python.org/3/library/random.html) (HIGH — official docs, quoted)
- src layout vs flat layout — [packaging.python.org discussion](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) (HIGH — official PyPA)
- `geng -t` (triangle-free generation) and geng option surface — [geng manpage (ManKier)](https://www.mankier.com/1/geng), [Ubuntu manpage](https://manpages.ubuntu.com/manpages/jammy/man1/nauty-geng.1.html), [nauty/Traces home](https://pallini.di.uniroma1.it/) (HIGH for `-t`; MEDIUM-HIGH for `res/mod` sharding — standard documented usage)
- Specialized maximal-triangle-free generators as a P0 throughput option (LOW — flagged for Phase 9 research; default architecture does not depend on it)

---
*Architecture research for: the α = 2 hunt-and-certify harness (Python package milestone)*
*Researched: 2026-07-21*
