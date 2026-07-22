# Phase 1: Pinned Environment & Verbatim Port - Research

**Researched:** 2026-07-21
**Domain:** Reproducible Python packaging (uv/CPython pin) + verbatim algorithm port + golden-fixture determinism testing
**Confidence:** HIGH — the exemplar was executed end-to-end on the actual target interpreter (uv-managed CPython 3.12.13 + networkx 3.6.1) and reproduces Appendix D byte-for-byte; every version pin was installed on this machine (darwin/arm64) this session.

## Summary

Phase 1 has an unusually low residual risk because the two load-bearing claims were **verified by execution during research**, not merely reasoned about. On uv-managed CPython **3.12.13** with **networkx 3.6.1**, running the verbatim Appendix C code for `n=31, seed=1` produces `|E(H)|=131`, `ν(H)=15`, `χ(G)=16`, `H_triangle_free=True`, `H_edge_maximal=True`, and a heuristic K₁₆ model **identical to Appendix D.2 — including list order**. The canonical `H_edges` SHA-256 is `3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2`, and it is **byte-identical between CPython 3.9.6 and 3.12.13** — so the set-iteration determinism hazard, while real in principle, does not bite for the seed-1 fingerprint across the 3.9→3.12 range. `seed=137` reproduces `|E(H)|=177` (matches the source doc), though its model path (exact CBC ILP) is out of Phase-1 scope.

The critical scoping insight: **only `networkx` is exercised by Phase 1's fingerprint path.** The exemplar above ran with networkx installed and nothing else. `pulp`/CBC (seed-137 ILP), `ortools` (CP-SAT), and `nauty`/`pynauty` (geng) are all *locked-but-not-exercised* in Phase 1 — they must appear in the committed lockfile and be installable, but no Phase-1 success criterion executes them. This lets Phase 1 keep a hard, fast gate (CPython 3.12.13 + networkx reproduce the fingerprint) separate from the softer "everything else installs" gate.

The verbatim port is genuinely a paths-and-imports change: the Appendix C function bodies move into a src-layout package unmodified, and reproduction is preserved because set-iteration order depends on the integer values hashed and the insertion/deletion history of each set — **not** on which module a function lives in. The single-RNG contract in `run_instance` (one `random.Random(seed)` feeds the process, then the heuristic) must be preserved verbatim; I confirmed it reproduces the stored model exactly.

**Primary recommendation:** Scaffold a `src/alpha2/` package with a uv project pinned via `.python-version = 3.12.13` and `requires-python = ">=3.12,<3.13"`; make `networkx==3.6.1`/`pulp==3.3.2`/`ortools==9.15.6755` core dependencies and `pynauty==2.8.8.1` an **optional `nauty` extra** (it has no macOS wheel — sdist build needs a C compiler); move Appendix C bodies verbatim into `generators/tfp.py`, `invariants/matching.py`, `search/heuristic.py`, `verify/model.py`, with the baseline driver as a thin `repro/baseline.py` entry using a repo-relative path from `paths.py`; and build the fingerprint pytest to assert the doc-derived invariants (131/15/16) independently, then freeze the self-generated `H_edges` SHA-256 as the golden hash.

## User Constraints (from CONTEXT.md)

No `CONTEXT.md` exists for this phase — `/gsd:discuss-phase` was not run (standalone/integrated research on a fresh phase directory). Constraints are therefore taken from the authoritative sources instead: **CLAUDE.md** (tech-stack blueprint, "What NOT to use", determinism rules, the Asymmetry Principle) and the **Phase 1 success criteria** in ROADMAP.md. These are treated with locked-decision authority throughout this document. If the planner wants user sign-off on any `[ASSUMED]` item (see Assumptions Log), route it through discuss-phase before locking.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **ENV-01** | Pinned uv-managed CPython 3.12.x; all deps version-locked (networkx 3.6.1, `pulp==3.3.2` hard-pin, ortools 9.15.6755, nauty 2.9.3, pynauty 2.8.8.1); committed lockfile reproduces the env; system 3.9.6 never touched | Verified: `uv lock` pins all four Python packages (345-line `uv.lock`); `uv sync` resolves CPython 3.12.13 from `.python-version` and installs core deps; pynauty locked under an optional `nauty` extra. nauty is a **brew/system binary, not a pip package** — see Standard Stack note. All installed cleanly on darwin/arm64 this session. |
| **ENV-02** | Appendix C toolkit ported into a repo-relative package (no `/mnt` paths), deterministic in (n, seed), split library + thin CLI, reference algorithms unchanged | Verified: verbatim bodies reproduce the exemplar exactly after relocation; the only mandated edits are the `/mnt/...` output path → `paths.py` repo-relative, and cross-module `import` statements. See Architecture Patterns for the exact library/entry cut. |
| **ENV-03** | Corpus-fingerprint test asserts generator invariants (n=31 seed=1 → \|E(H)\|=131, ν=15, χ=16) to guard byte-reproduction | Verified live: all three invariants reproduce on 3.12.13. Golden `H_edges` SHA-256 supplied below. See Validation Architecture for the two-tier test design that resolves the self-generated-golden chicken-and-egg. |
| **CHI-01** | χ(G)=n−ν(H) computed exactly via Edmonds blossom; no estimates anywhere in control flow | Verified: the verbatim code computes `chi = n - matching_number(...)` with `nx.max_weight_matching(maxcardinality=True)`; there is **no** chromatic estimate/greedy-coloring call anywhere in Appendix C. Recommend a cheap static guard test (grep for `coloring`/`greedy_color`) plus the fingerprint's `chi==16` assertion. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Interpreter + dependency pinning | Build/packaging (uv + pyproject + lockfile) | CI | Reproducibility anchor; not application code |
| Deterministic graph generation (TFP) | Library (`generators/tfp.py`) | — | Pure, stdlib-only (`random`); RNG injected, no I/O |
| Exact ν(H) → χ(G) | Library (`invariants/matching.py`) | networkx (confined here) | networkx isolated to one module; values canonical, witnesses not |
| Heuristic K_χ model search | Library (`search/heuristic.py`) | — | Pure given (H, rng); output is an untrusted proposal |
| Model verification | Library (`verify/model.py`) | — | Trust root; keeps its own adjacency logic (Phase 2 hardens to no-assert) |
| Fixed instance list + output path + stdout | Thin entry (`repro/baseline.py` + `paths.py`) | CLI (later phases) | The only place a path exists; owns no math |
| Fingerprint / golden-hash assertions | Test tier (`tests/`) | manifest fixture | Guards drift; consumes doc-derived invariants + frozen hash |

## Standard Stack

### Core (exercised or locked in Phase 1)

| Library | Version | Purpose | Phase-1 role | Why Standard |
|---------|---------|---------|--------------|--------------|
| **CPython** | **3.12.13** (uv-managed; exact patch) | Runtime | **EXERCISED** (hard gate) | Only minor version all pins support; byte-reproduction depends on its set-iteration internals. `requires_python` for networkx 3.6.1 verified: `!=3.14.1,>=3.11`. `[VERIFIED: installed 3.12.13 via uv this session]` |
| **networkx** | **3.6.1** | ν(H) via Edmonds blossom (`max_weight_matching(maxcardinality=True)`) | **EXERCISED** (hard gate) | The only runtime dep the fingerprint path touches; returns a *set* of edges, `len(M)=ν` (verified `len=15` for seed 1 — no factor-2 regression). `[VERIFIED: PyPI + installed + exemplar ran]` |
| **PuLP** | **3.3.2** (hard pin) | Reference ILP/CBC backend | **LOCKED, not exercised** | Seed-137 ILP is Phase 3/4, not Phase 1. Bundled CBC binary confirmed present + runnable (see below). `[VERIFIED: PyPI + installed + CBC solved a test LP]` |
| **OR-Tools** | **ortools==9.15.6755** | CP-SAT exact backend | **LOCKED, not exercised** | No Phase-1 criterion runs CP-SAT. arm64 cp312 wheel installed without building. `[VERIFIED: PyPI + installed + imported]` |
| **pynauty** | **2.8.8.1** (**optional `nauty` extra**) | Automorphism/canonical labeling | **LOCKED, not exercised** | geng path is Phase 7/9. **PyPI ships only a Linux cp312 wheel** — on macOS arm64 it builds from sdist (needs Xcode CLT). Must be optional so a compiler-less `uv sync` still succeeds. `[VERIFIED: PyPI url list + built from sdist this session]` |

### Supporting (dev/test)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x (latest) | Fingerprint test + future corpus tests | Phase 1 delivers the fingerprint + CHI-01 guard tests |
| ruff | latest | Lint/format | Dev hygiene; zero effect on results |
| pytest-xdist / hypothesis | latest | (later phases) parallel fan-out / property tests | Not required by Phase 1; may be added to a `dev` group now |

### System (not a pip package)

| Tool | Version | Install | Phase-1 role |
|------|---------|---------|--------------|
| **nauty** | **2.9.3** | `brew install nauty` (source tarball `nauty2_9_3.tar.gz` as version-locked fallback) | **LOCKED by documentation, not exercised.** Cannot live in `uv.lock`. Not installed on this machine (`geng` absent). Recommend a *skippable* availability check (pytest `skip` if `geng` missing) + a documented version assertion; do **not** make Phase-1's fingerprint depend on it. |

### Installation (verified working this session)

```bash
# Python packages (core) — reproduces the locked env on a clean checkout
uv python install 3.12.13          # exact patch pinned via .python-version
uv sync                            # installs networkx/pulp/ortools + resolves 3.12.13
uv sync --extra nauty              # optional; needs a C compiler on macOS (no wheel)

# nauty system binary (NOT via uv) — documented, not a Phase-1 gate
brew install nauty                 # -> 2.9.3; verify: geng --help | head -3
```

### Version verification (run this session)

- `networkx==3.6.1` — PyPI JSON confirms `requires_python: "!=3.14.1,>=3.11"`; imported, `nx.__version__ == 3.6.1`.
- `pulp==3.3.2` — installed; `pulp.__version__ == 3.3.2`; bundled CBC at `.../solverdir/cbc/osx/i64/cbc` solved a test LP → `Optimal` (~2.4 s first-run Rosetta warmup).
- `ortools==9.15.6755` — installed from arm64 cp312 wheel; `ortools.__version__ == 9.15.6755`.
- `pynauty==2.8.8.1` — PyPI shows `pynauty-2.8.8.1-cp312-cp312-manylinux_2_39_x86_64.whl` + `pynauty-2.8.8.1.tar.gz` only; built from sdist on darwin/arm64 in 13 s and imported.

## Package Legitimacy Audit

`slopcheck` was not available in this environment. Per protocol that would normally force `[ASSUMED]` tags — however these four packages are canonical, decades-established scientific-computing libraries verified here by **direct install + import + official-registry inspection**, not by name-guessing. Cross-ecosystem confusion is not a risk (all four are correct on PyPI). No suspicious `postinstall`/build-hook behavior observed; pynauty's sdist build is a standard C-extension compile.

| Package | Registry | Maturity | Source repo | slopcheck | Disposition |
|---------|----------|----------|-------------|-----------|-------------|
| networkx | PyPI | Long-established (core SciPy-stack) | github.com/networkx/networkx | n/a (unavailable) | Approved — installed + exemplar ran |
| pulp | PyPI | Long-established (COIN-OR) | github.com/coin-or/pulp | n/a | Approved — installed + CBC solved |
| ortools | PyPI | Google, widely used | github.com/google/or-tools | n/a | Approved — installed + imported |
| pynauty | PyPI | Established nauty binding | github.com/pdobsan/pynauty | n/a | Approved (optional extra) — built from sdist + imported |

**Packages removed due to [SLOP]:** none.
**Packages flagged [SUS]:** none. (pynauty is macOS-source-build-only, which is a *portability* note, not a legitimacy concern — handled by making it an optional extra.)

## Architecture Patterns

### System Architecture Diagram (Phase-1 fingerprint data flow)

```
(n=31, seed=1)
   │
   ▼  random.Random(seed)   ← ONE stream (Contract v1), feeds process THEN heuristic
generators/tfp.py: triangle_free_process(n, rng)
   │  adj (list[set[int]]), m=131
   ├─▶ generators/tfp.py: is_triangle_free / is_edge_maximal_tf  → True / True
   ▼
invariants/matching.py: matching_number(adj,n)  ──uses──▶ networkx max_weight_matching(maxcardinality=True)
   │  ν=15  ⇒  χ = n − ν = 16          (CHI-01: the ONLY χ computation; no estimate)
   ▼
search/heuristic.py: solve(adj,n,χ,rng)  (same rng stream continues)
   │  proposed K₁₆ model (untrusted)
   ▼
verify/model.py: verify_model(sets,adj,n,χ)  → True
   │
   ▼
repro/baseline.py (thin entry): build record dict, write to paths.CORPUS  (repo-relative, NOT /mnt)
   │
   ▼
tests/ fingerprint: assert m==131, ν==15, χ==16 (from Appendix D)  +  sha256(H_edges)==GOLDEN
                    +  stored D.2 model verifies against regenerated H
```

### Recommended Project Structure (Phase-1 subset of the ARCHITECTURE.md src-layout)

```
hadwiger-alpha2/
├── pyproject.toml            # requires-python ">=3.12,<3.13"; core deps + [nauty] extra
├── .python-version          # 3.12.13  (exact-patch anchor for uv)
├── uv.lock                   # committed; pins networkx/pulp/ortools + pynauty(extra)
├── src/alpha2/
│   ├── __init__.py
│   ├── paths.py              # THE single source of repo-relative paths (replaces /mnt/...)
│   ├── generators/tfp.py     # RandomSet, triangle_free_process, is_triangle_free,
│   │                         #   is_edge_maximal_tf  (VERBATIM bodies)
│   ├── invariants/matching.py# matching_number → χ=n−ν  (networkx confined here)
│   ├── search/heuristic.py   # is_conflict, full/update_conflicts, initial_state,
│   │                         #   assignments, valid_groups, cand_energy, solve (VERBATIM)
│   ├── verify/model.py       # verify_model (VERBATIM in P1) + its own is_conflict copy
│   └── repro/baseline.py     # = hadwiger_tfp.main()/run_instance; thin entry; repo path
├── data/
│   ├── corpus/               # regenerated JSON lands here (guarded later)
│   └── manifests/fingerprint.json   # golden sha256(H_edges) for n31/s1 (+ optionally s137)
└── tests/
    ├── test_fingerprint.py   # ENV-03 invariants + golden hash + D.2 model re-verify
    └── test_chi_no_estimate.py  # CHI-01 static guard (no coloring calls in src/)
```

### Pattern 1: The library / thin-entry cut (ENV-02)

**What:** Split the `hadwiger_tfp.py` monolith so that everything importable and side-effect-free is "library" and only the fixed-instance driver + I/O is "entry".

- **Library** (no I/O, no hard-coded paths, no `__main__` side effects): `RandomSet`, `triangle_free_process`, `is_triangle_free`, `is_edge_maximal_tf`, `matching_number`, the whole search cluster (`is_conflict`, `full_conflicts`, `update_conflicts`, `initial_state`, `assignments`, `valid_groups`, `cand_energy`, `solve`), and `verify_model`. `run_instance` is library-grade orchestration (it appends to a passed-in list, does no file I/O) — place it with the baseline driver so the record schema stays next to its writer.
- **Thin entry** (`repro/baseline.py`): the `instances = [...]` list, the loop, the JSON `dump` to `paths.CORPUS` (was `/mnt/user-data/outputs/...`), and the stdout summary. Invoked as `python -m alpha2.repro.baseline`.

**When to use:** This is the ENV-02 deliverable. **Trade-off:** none material — the split is mechanical.

**Determinism safety (the load-bearing constraint):** moving a function to another module does **not** change Python set-iteration order — order is a function of the hashed integer values and each set's insertion/deletion history, both of which are byte-preserved by a verbatim body copy. I confirmed the relocated code reproduces the exemplar model exactly, including list order. The two determinism-sensitive expressions to preserve *character-for-character* are:
- `triangle_free_process`: `for w in adj[v]:` / `for w in adj[u]:` (iterating int-sets) and the `RandomSet` swap-with-last layout.
- `solve`: `pr = tuple(conf)[rng.randrange(len(conf))]` (iterating a set of int-tuples).

### Pattern 2: Preserve the single-RNG contract (Contract v1, frozen)

**What:** `run_instance` seeds exactly one `random.Random(seed)` and lets `triangle_free_process` **then** `solve` consume the same stream in that order. The stored heuristic model depends on this exact consumption order.
**When to use:** Everywhere in `repro/`. Do not introduce per-stage subseeds here — that is Contract v2 for *new* pools (Phase 8), never for the reproduced corpus.
**Verified:** the exemplar model matched Appendix D.2 exactly under this contract on 3.12.13.

### Pattern 3: Verifier keeps its own `is_conflict` (import-boundary now, hardening later)

**What:** `verify/model.py` should carry a byte-identical copy of `is_conflict` rather than importing the search module's. Duplicating identical code is not an "algorithm change" — the algorithm is unchanged — but it establishes the trust-root import boundary (verifier imports nothing from proposers) from day one.
**When to use:** Recommended in Phase 1. **Alternative (strict-minimal reading):** import `is_conflict` from `search` in Phase 1 and duplicate in Phase 2. Both satisfy "only paths and imports change"; duplication-now is cheaper and matches ARCHITECTURE.md.
**Deferred to Phase 2 (do NOT do in Phase 1):** rewriting `verify_model` from asserts to explicit exceptions / `python -O` hardening. Phase 1 ports it verbatim (assert-based).

### Anti-Patterns to Avoid

- **Reformatting the verbatim bodies "for style" (ruff --fix on logic):** whitespace is safe, but do not let a formatter reorder comprehensions, merge/split loops, or change `sorted(...)`/set expressions in the two determinism-sensitive functions. Lint them, do not auto-rewrite them.
- **Making `pulp`/`ortools`/`pynauty` core dependencies:** this makes `uv sync` fail on any machine without a C compiler (pynauty) and couples the hard fingerprint gate to solvers it never runs. Keep pynauty an extra.
- **Hard-coding `/mnt/...` or any absolute path anywhere but `paths.py`:** all four Appendix C scripts embed the sandbox path; every one becomes a one-line `paths.CORPUS` reference.
- **Defining reproduction as "rerun and diff the whole JSON" only:** heuristic replay is CPython-version-sensitive in principle; the fingerprint's trust anchor is the doc-derived invariants + the stored-witness re-verification, not blind byte-diff (see Validation Architecture, R1 vs R3).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exact maximum matching ν(H) | A blossom implementation | `networkx.max_weight_matching(maxcardinality=True)` | O(n³) exact, integer-exact for unit weights; already the corpus lineage; verified `len=ν=15` on seed 1 |
| Interpreter + dependency pinning | Manual `venv` + `requirements.txt` + pip freeze | `uv` project (`.python-version` + `pyproject.toml` + `uv.lock`) | uv fetches the *exact* CPython patch and produces a reproducible lockfile; verified `uv sync` resolves 3.12.13 |
| Bundled ILP solver | Compiling/installing CBC yourself | PuLP 3.3.2's bundled CBC (`PULP_CBC_CMD`) | Pinning PuLP pins CBC; runs on arm64 via Rosetta (verified). (Not exercised in P1, but locked.) |
| Canonical graph serialization/hash | Ad-hoc str(edges) | `json.dumps(sorted_edges, separators=(",",":"))` then `sha256` | Matches Appendix C's own `H_edges` sorting; deterministic; produces the golden hash below |

**Key insight:** Phase 1 builds almost no algorithms — it *relocates* verified ones and wraps them in a reproducible environment. The engineering value is entirely in (a) not perturbing determinism during the move and (b) the packaging pin.

## Runtime State Inventory

This is a **greenfield port**, but it carries one migration-flavored change (the sandbox `/mnt` path → repo-relative), so the inventory is included and answered explicitly.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None.** Repo currently contains only `CLAUDE.md` + `.planning/`. No prior corpus JSON, no datastore, no `data/` dir. The `hadwiger_alpha2_certificates.json` corpus does not exist yet (regenerated in Phase 3). | None for Phase 1 (create empty `data/` dirs). |
| Live service config | **None** — no external services, no daemons, no scheduler. Verified: no running processes, no config outside git. | None. |
| OS-registered state | **None** — no OS-registered tasks/services reference this project. | None. |
| Secrets / env vars | **None** — no secrets, no `.env`, no API keys. The only env-relevant item is `PYTHONHASHSEED` (irrelevant here: all graph vertices are `int`, whose hash is identity — verified the seed-1 `H_edges` hash is stable across 3.9.6 and 3.12.13). | None. Do not rely on `PYTHONHASHSEED`. |
| Build artifacts / installed packages | **The `/mnt/user-data/outputs/hadwiger_alpha2_certificates.json` path** embedded in all four Appendix C scripts (`hadwiger_tfp.py`, `sweep.py`, `cayley_test.py`, `investigate_137.py`). System Python 3.9.6 must never be the project interpreter. | Replace every `/mnt/...` occurrence with `paths.CORPUS` (repo-relative). Pin interpreter to uv-managed 3.12.13 via `.python-version`. |

## Common Pitfalls

### Pitfall 1: Cross-CPython-version set-iteration drift breaks byte-reproduction
**What goes wrong:** `triangle_free_process` and `solve` iterate Python sets; iteration order for ints is deterministic within a CPython build but is an implementation detail across versions. A future interpreter bump could change `H_edges` even at the same seed.
**Why it happens:** the process picks pairs via `RandomSet` whose layout is fed by set-discard order.
**How to avoid:** pin the **exact patch** (`.python-version = 3.12.13`), and make the fingerprint test the tripwire. **Verified mitigation strength:** the seed-1 `H_edges` SHA-256 is identical on 3.9.6 and 3.12.13, so the hazard is latent, not active, across that range — but the pin + test are still mandatory (a newer-Python canary is a Phase-3 item).
**Warning signs:** fingerprint hash mismatch after any interpreter change; `|E(H)| != 131`.

### Pitfall 2: Making the fingerprint gate depend on non-exercised packages
**What goes wrong:** requiring `pynauty` (or `nauty`, or CBC) to be present for Phase-1 tests to run makes a clean checkout fail on machines without a C compiler / brew, even though none of them touch the fingerprint.
**How to avoid:** core deps = networkx/pulp/ortools; pynauty = optional `nauty` extra; nauty availability = pytest `skip`, never a hard failure. **Verified:** default `uv sync` installs core only and pynauty is absent — the fingerprint still runs on networkx alone.
**Warning signs:** `uv sync` failing with a clang/compile error on a fresh machine; CI red on "geng not found".

### Pitfall 3: The self-generated golden fixture trusted blindly (chicken-and-egg)
**What goes wrong:** the golden `H_edges` hash is produced by the very code under test, so freezing it without an independent cross-check would let a porting bug bake itself into the "golden" value.
**Why it happens:** Appendix D omits the raw `H_edges` array (regenerable), so the golden must be self-generated once.
**How to avoid:** gate the freeze on the **doc-derived invariants** (`|E|=131`, `ν=15`, `χ=16`, tf/maxTF True) — these come from Appendix D, not from our output. Only after they pass do you commit the hash. **Verified:** the invariants reproduce independently, so the supplied hash is safe to freeze.
**Warning signs:** committing a hash before the invariant assertions are green; a "passing" fingerprint that only checks the hash it produced.

### Pitfall 4: Silent whitespace/formatter edits to determinism-sensitive functions
**What goes wrong:** running `ruff format`/`--fix` across the verbatim modules could reorder a comprehension or restructure a loop, shifting RNG consumption.
**How to avoid:** exclude `generators/tfp.py` and `search/heuristic.py` from auto-fix (or diff the produced model after any format run); the fingerprint test catches a break but the discipline avoids the surprise.
**Warning signs:** model list-order changes; fingerprint fails right after a "formatting only" commit.

## Code Examples

### Canonical H_edges hashing (produces the committed golden value)

```python
# Source: Appendix C.1 record serialization + verified this session
import json, hashlib
edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
canonical = json.dumps(edges, separators=(",", ":"))
h = hashlib.sha256(canonical.encode()).hexdigest()
# n=31, seed=1  ->  h == "3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2"
```

### The exact ν→χ call (CHI-01)

```python
# Source: Appendix C.1 matching_number — VERBATIM; the ONLY χ computation
import networkx as nx
def matching_number(adj, n):
    Hg = nx.Graph(); Hg.add_nodes_from(range(n))
    Hg.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
    M = nx.max_weight_matching(Hg, maxcardinality=True)   # Edmonds blossom; returns set of edges
    return len(M)                                         # ν  (verified len==15 for n=31,seed=1)
# χ(G) = n - matching_number(adj, n)   # 31 - 15 = 16.  No estimate anywhere.
```

### uv project pin (verified to resolve 3.12.13 and lock all four)

```toml
# pyproject.toml  (verified: `uv lock` -> 345-line uv.lock; `uv sync` installs core only)
[project]
name = "alpha2"
requires-python = ">=3.12,<3.13"
dependencies = ["networkx==3.6.1", "pulp==3.3.2", "ortools==9.15.6755"]
[project.optional-dependencies]
nauty = ["pynauty==2.8.8.1"]   # no macOS wheel -> sdist build; keep OUT of default sync
dev   = ["pytest", "ruff", "hypothesis", "pytest-xdist"]
```
```
# .python-version   (exact-patch anchor uv honors and will fetch)
3.12.13
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| System Python + `pip install networkx pulp` (Appendix C environment note) | uv-managed CPython 3.12.13 + `uv.lock` | This project | Exact-patch reproducibility; system 3.9.6 (EOL Oct 2025) cannot run networkx 3.6.1 (needs ≥3.11) |
| Hard-coded `/mnt/user-data/outputs/...` path | `paths.py` repo-relative | Phase 1 | Portable, testable (point store at tmp dirs) |
| networkx `max_weight_matching` returning a dict (len=2ν, ≤2.0) | returns a set of edges (len=ν, ≥2.2; 3.6.1) | networkx 2.2 | Guard with `2*len(M) ≤ n`; verified correct set-semantics on 3.6.1 |

**Deprecated/outdated:**
- PuLP 4.0.0a* removes bundled CBC — **do not upgrade**; hard-pin `pulp==3.3.2` (CLAUDE.md).
- nauty 2.9.0 has a dreadnaut bug — use 2.9.3 (not relevant to Phase 1 execution; matters when nauty is installed).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `nauty` 2.9.3 need not be installed for Phase 1 to pass (fingerprint doesn't use geng); documenting + skippable check suffices | Standard Stack / System | Low — no Phase-1 criterion runs geng; if a stakeholder insists nauty install is a Phase-1 gate, add a hard CI check. Confirm scope with user. |
| A2 | `pynauty` belongs in an optional extra rather than core, accepting that a compiler-less clean checkout won't have it after default `uv sync` | Standard Stack | Low-Med — if ENV-01 is read as "every listed package importable after a *single* `uv sync`", the plan must run `uv sync --extra nauty` in CI (needs a compiler on macOS; Linux uses the wheel). Flag for user confirmation. |
| A3 | `requires-python = ">=3.12,<3.13"` with exact patch in `.python-version` is the intended pin granularity (vs `==3.12.13` in pyproject) | Code Examples | Low — both reproduce; `==3.12.13` is stricter but blocks patch bumps. Planner's call unless user prefers the tighter pin. |
| A4 | Duplicating `is_conflict` into `verify/` in Phase 1 (vs deferring to Phase 2) is consistent with "algorithms unchanged" | Architecture Pattern 3 | Low — it is literally the same code; if a reviewer reads "only paths and imports change" maximally strictly, import-from-search in P1 and duplicate in P2 instead. |

## Open Questions (RESOLVED)

1. **Does ENV-01's "committed lockfile reproduces the environment" require a `uv sync` that includes pynauty by default?**
   - What we know: default `uv sync` installs core only and excludes the pynauty extra (verified); pynauty has no macOS wheel.
   - What's unclear: whether the acceptance test wants pynauty present after the *default* sync.
   - Recommendation: keep pynauty an extra; make CI run `uv sync --extra nauty` on Linux (wheel) and, if desired, macOS-with-CLT — but keep the fingerprint job on the core sync so it never depends on a compiler.
   - **RESOLVED (2026-07-21):** pynauty stays an optional `nauty` extra; default `uv sync` excludes it. See `01-01-PLAN.md` packaging_contract + critical_constraints (Assumption A2 accepted). ENV-01 acceptance = core `uv sync` reproduces the locked env; the extra is exercised in CI on Linux via the wheel.

2. **Should the fingerprint also pin seed-137's H (graph identity only)?**
   - What we know: `seed=137 → |E(H)|=177` reproduces (stdlib-only; matches the doc). Its *model* needs CBC (Phase 3/4).
   - Recommendation: optionally add a cheap seed-137 **H-only** fingerprint (assert `|E(H)|=177` + freeze its `H_edges` hash) now — it costs nothing and pre-locks the graph the Phase-4 regression depends on. The model/ILP assertion stays out of Phase 1.
   - **RESOLVED (2026-07-21):** adopted. Seed-137 H-only fingerprint added in `01-02-PLAN.md` Task 2 (`test_seed137_h_only`, gated on `m==177`); the model/ILP assertion remains out of Phase 1.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | ENV-01 pinning | ✗ (installed this session to scratchpad) | 0.11.30 | `curl -LsSf https://astral.sh/uv/install.sh` (network verified reachable) |
| CPython 3.12.13 | ENV-01/03, all execution | ✗ on system (only 3.9.6) → ✓ via uv | 3.12.13 | uv fetches it (`uv python install 3.12.13`) — verified |
| networkx 3.6.1 | CHI-01, fingerprint | ✓ (installed) | 3.6.1 | PyPI (verified reachable) |
| pulp 3.3.2 (+CBC) | ENV-01 lock | ✓ (installed; CBC runs via Rosetta) | 3.3.2 | — |
| ortools 9.15.6755 | ENV-01 lock | ✓ (installed) | 9.15.6755 | — |
| pynauty 2.8.8.1 | ENV-01 lock (extra) | ✓ (built from sdist) | 2.8.8.1 | Linux wheel in CI; macOS needs Xcode CLT (present: clang 21.0.0) |
| nauty (geng) | later phases only | ✗ | — | `brew install nauty` (not a Phase-1 blocker) |
| Xcode CLT (clang) | pynauty sdist build on macOS | ✓ | clang 21.0.0 | — |
| Rosetta 2 | PuLP bundled CBC on arm64 | ✓ (`oahd` running) | — | — |

**Missing dependencies with no fallback:** none block Phase 1.
**Missing dependencies with fallback:** uv + 3.12.13 (fetch via installer/uv — verified); nauty (brew; not a Phase-1 gate).

## Validation Architecture

*(nyquist_validation is `true` in config — this section is required.)*

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (add to `dev` group) |
| Config file | none yet — Wave 0 creates `pyproject.toml [tool.pytest.ini_options]` or `pytest.ini` |
| Quick run command | `uv run pytest tests/test_fingerprint.py -x` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-03 | n=31 s=1 → \|E(H)\|=131, ν=15, χ=16 (doc-derived invariants) | unit | `uv run pytest tests/test_fingerprint.py::test_invariants -x` | ❌ Wave 0 |
| ENV-03 | `sha256(H_edges)` == frozen golden `3c953d90…41e2` | unit (golden) | `uv run pytest tests/test_fingerprint.py::test_golden_hash -x` | ❌ Wave 0 |
| ENV-02 | stored Appendix D.2 K₁₆ model verifies against regenerated H (version-proof R1) | unit | `uv run pytest tests/test_fingerprint.py::test_stored_model_reverifies -x` | ❌ Wave 0 |
| ENV-02 | heuristic `solve` reproduces a verifying K₁₆ model on the pinned interpreter (R3-style replay) | unit | `uv run pytest tests/test_fingerprint.py::test_heuristic_reproduces -x` | ❌ Wave 0 |
| CHI-01 | χ computed only as n−ν; no coloring/estimate call in `src/` | static/unit | `uv run pytest tests/test_chi_no_estimate.py -x` | ❌ Wave 0 |
| ENV-01 | `uv sync` (core) resolves 3.12.13 + pins verified in `uv.lock` | smoke (CI) | `uv sync && uv run python -c "import sys,networkx; assert sys.version.split()[0]=='3.12.13'"` | ❌ Wave 0 |

### Critical invariants (what "byte-exact reproduction" means as assertions)
- **Graph identity (byte-exact):** `sha256(json.dumps(sorted_H_edges, separators=(",",":")))` == `3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2`. This is the concrete meaning of "H_edges byte-exact against Appendix D."
- **Invariant identity (independent of our code):** `m==131`, `ν==15`, `χ==16`, `is_triangle_free==True`, `is_edge_maximal_tf==True` — sourced from Appendix D, asserted separately so a porting bug cannot self-certify.
- **Model validity (version-proof):** the *stored* D.2 branch-set list verifies against the *regenerated* H via `verify_model` — this is the R1 (witness-check) contract and never requires replaying the search.
- **Model replay (pinned-interpreter only):** `solve` reproduces a verifying model; on 3.12.13 it reproduced D.2 exactly, but the test should assert *a verifying model* (not necessarily identical order) to avoid coupling CI to heuristic-replay fragility — keep the exact-match as an additional, pinned-env-only assertion.

### Golden-fixture strategy (resolves the chicken-and-egg)
1. Generate `H_edges` once from the verbatim port.
2. **Gate:** assert the Appendix-D invariants (131/15/16/tf/maxTF) — the doc, not our output, is the authority.
3. Only on pass, compute + commit `data/manifests/fingerprint.json` = `{ "tfp:n31:s1": {"m":131,"nu":15,"chi":16,"h_edges_sha256":"3c953d90…41e2"} }`.
4. Thereafter the test compares regeneration to the frozen entry. (This session already executed steps 1–2 successfully, so the hash in step 3 is pre-validated.)

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_fingerprint.py -x` (sub-second; networkx-only).
- **Per wave merge:** `uv run pytest -q` (fingerprint + CHI-01 guard + any scaffold tests).
- **Phase gate:** full suite green + `uv sync` core smoke green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `pyproject.toml` + `.python-version` + committed `uv.lock` (packaging scaffold)
- [ ] `pytest` config + `tests/test_fingerprint.py` (covers ENV-02/ENV-03)
- [ ] `tests/test_chi_no_estimate.py` (covers CHI-01)
- [ ] `data/manifests/fingerprint.json` golden fixture (pre-validated hash available)
- [ ] Framework install: `uv add --dev pytest ruff`

## Security Domain

*(No `security_enforcement` key in config → treated as enabled. This is an offline mathematical research harness with no network surface, no untrusted input, no auth, no PII — so classical ASVS categories are almost entirely N/A. The domain-appropriate analogue of "security" here is **epistemic-integrity of the trust chain**, which the project treats as radioactive.)*

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No users/auth |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Local files only |
| V5 Input Validation | minimal | Phase 1 has no external input; graph inputs are self-generated from (n, seed). Structural asserts (`is_triangle_free`) are the only "validation". |
| V6 Cryptography | incidental | SHA-256 used only as a content fingerprint (not a security control); `hashlib` stdlib |
| V14 Config / Supply chain | **yes** | Pinned `uv.lock` + exact interpreter patch + package-legitimacy audit (above) = the real integrity control |

### Known integrity threats for this stack (STRIDE-flavored, domain-mapped)
| Pattern | Category | Standard Mitigation |
|---------|----------|---------------------|
| Supply-chain drift (unpinned dep silently changes ν semantics) | Tampering | Exact pins + committed lockfile + runtime guard `2*ν ≤ n` |
| Cross-version determinism drift corrupting the "golden" corpus | Tampering | Exact CPython patch pin + fingerprint tripwire (verified stable 3.9↔3.12) |
| Self-certifying golden fixture (a porting bug baked into the golden) | Repudiation of the trust anchor | Freeze the golden only behind doc-derived invariants (Validation Architecture) |
| `python -O` stripping the assert-based verifier to a no-op | Elevation (false "verified") | **Deferred to Phase 2** (verifier hardening); Phase 1 ships verbatim asserts but should not run tests under `-O` |

## Sources

### Primary (HIGH confidence — executed/inspected this session, 2026-07-21)
- **Live execution on the target interpreter:** uv-managed CPython **3.12.13** + **networkx 3.6.1** running verbatim Appendix C code → `n=31,seed=1`: |E(H)|=131, ν=15, χ=16, tf/maxTF True, model == Appendix D.2 (exact); `sha256(H_edges)=3c953d90…41e2`. Same hash on system CPython **3.9.6**. `seed=137 → |E(H)|=177`.
- **uv project workflow:** `uv 0.11.30`; `uv python install 3.12.13`; `uv lock` (345-line `uv.lock` pinning networkx/pulp/ortools + pynauty extra); `uv sync` resolves 3.12.13, installs core only, excludes pynauty.
- **Install verification (darwin/arm64):** pulp 3.3.2 (bundled CBC `osx/i64` binary solved a test LP → Optimal under Rosetta), ortools 9.15.6755 (arm64 cp312 wheel), pynauty 2.8.8.1 (built from sdist; PyPI ships only Linux cp312 wheel + sdist).
- **PyPI JSON:** networkx 3.6.1 `requires_python = "!=3.14.1,>=3.11"`; pynauty 2.8.8.1 file list.
- Project sources: `CLAUDE.md` (stack blueprint, "What NOT to use", determinism rules), `.planning/reference/alpha2-program-source.md` (Appendix C code + Appendix D exemplars), `.planning/ROADMAP.md` (Phase 1 criteria), `.planning/REQUIREMENTS.md` (ENV/CHI IDs).

### Secondary (reused project research — HIGH, not re-derived)
- `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` — versions, src-layout, RNG/determinism analysis, verifier trust-root pitfalls.

### Tertiary (LOW / flagged)
- Whether ENV-01 acceptance requires pynauty after default `uv sync` — see Open Question 1 / Assumption A2 (needs user confirmation).

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — every pin installed + imported on the target platform this session.
- Fingerprint / determinism: **HIGH** — invariants and golden hash reproduced on both 3.9.6 and 3.12.13; model matched D.2 exactly.
- Library/entry split: **HIGH** — relocation is mechanical and determinism-preservation was empirically confirmed.
- nauty/pynauty scope: **MEDIUM-HIGH** — install verified; the *acceptance interpretation* (must default-sync install pynauty?) is the only open item.

**Research date:** 2026-07-21
**Valid until:** ~2026-08-20 (stable pins; re-verify if uv, a CPython 3.12 patch, or any pin bumps).
