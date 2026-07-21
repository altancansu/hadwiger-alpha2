# Stack Research

**Domain:** Exact graph-minor certification harness (Hadwiger's Conjecture, α = 2 restriction) — exhaustive generation, exact matching, exact ILP/CP-SAT model search, certificate verification, deferred Lean 4 formalization
**Researched:** 2026-07-21
**Confidence:** HIGH (every version and API name below verified against a primary source today; exceptions flagged inline)

The stack decision itself (networkx + pulp/CBC reference + nauty `geng -t` + OR-Tools CP-SAT behind one interface) is settled and is not re-litigated here. This document says how to do it well: exact versions, exact flags, exact API shapes, and the places where reproducibility can silently break.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **CPython** | **3.12.x** (uv-managed; **not** system 3.9.6) | Runtime for the whole harness | The only minor version every pinned dependency verifiably supports today: networkx 3.6.1 requires ≥3.11; PuLP 3.3.2 requires ≥3.10; ortools 9.15 ships cp39–cp314 wheels; pynauty's classifiers stop at 3.12. Pin the *exact* patch in CI — corpus byte-reproduction depends on CPython `set` iteration internals (see Blueprint 2). |
| **networkx** | **3.6.1** (PyPI, 2025-12-08) | ν(H) via Edmonds blossom (`max_weight_matching(maxcardinality=True)`), `max_weight_clique`, graph6 parsing (`from_graph6_bytes`), invariant checks | O(n³) exact blossom implementation, integer-arithmetic exact for unit weights (official docs). n ≤ 501 solves in seconds. Already the reference implementation for the 296-instance corpus. |
| **PuLP** | **3.3.2** (PyPI, 2026-05-25) — **hard pin** | Reference ILP backend (`PULP_CBC_CMD`) — reproduces Appendix C verbatim | Wheel inspected: still bundles CBC binaries under `pulp/solverdir/cbc/{linux,osx,win}/…` and still exports `PULP_CBC_CMD`. But the 3.3.2 source carries a `_skip_v4_deprecation` flag: **PuLP 4.0 (in alpha) removes the bundled CBC / reworks the solver API.** Pinning 3.3.2 is what keeps Appendix C byte-compatible. |
| **OR-Tools (CP-SAT)** | **ortools == 9.15.6755** (PyPI, 2026-01-14) | Stronger exact backend: had₂ / had₃ optimality proofs, scaled search, matching cross-check | State-of-the-art exact CP solver, integer-exact objective bounds, proves optimality, model export for audit. macOS arm64 cp312 wheel verified present. |
| **nauty** | **2.9.3** (`brew install nauty`; same version upstream at ANU) | `geng` exhaustive isomorph-free generation, `pickg`/`countg` C-speed property filters, `shortg`/`labelg` canonical dedup | The canonical exhaustive generator. `geng -t` prunes triangle-free during generation; `pickg -Z2` gives maximal-triangle-free at C speed (flags verified from 2.9.3 source). Note: nauty 2.9.0 had a serious `dreadnaut` bug — use 2.9.3, never 2.9.0. |
| **pynauty** | **2.8.8.1** (PyPI, 2024-06-06) — *optional extra* | Automorphism groups / vertex orbits in-process (CP-SAT symmetry breaking), canonical certificates for in-Python dedup | Bundles its own nauty 2.8.8 (independent of the brew install — no conflict). **Only** canonical labeling + `autgrp()`; it does **not** wrap `geng` (verified) — generation always shells out. Classifiers list 3.12; 3.13+ unverified → another reason to hold Python at 3.12. |
| **Lean 4 + mathlib** | Lean **v4.32.0** (current stable) + mathlib pinned release tag — *milestone 2 only* | Formal certificate checking | Mathlib has **no graph-minor theory** (verified today: no `Minor.lean`/`Contraction.lean` in `Mathlib/Combinatorics/SimpleGraph/`). Everything needed for size-≤2/≤3 *models* is easy to define locally; see Blueprint 5. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x (latest) | Verifier + corpus-reproduction as tests | Always; the corpus regeneration and 27 stored certificates run as the test suite |
| pytest-xdist | latest | Parallel test/instance fan-out | Sweeps (270-seed) and P0 batch runs in CI |
| uv | latest | Python pinning, lockfile, venv | Always — `uv python install 3.12` + `uv.lock` is the reproducibility anchor |
| ruff | latest | Lint/format | Dev hygiene; zero effect on results |
| hypothesis | latest | Property tests for the independent verifier (e.g., verifier rejects mutated models) | Optional but high-value: the verifier is the trust root |

Everything else is stdlib: `subprocess` (geng pipes), `json` (corpus), `random` (deterministic generators), `itertools`.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Homebrew `nauty` | Installs `geng`, `pickg`, `countg`, `shortg`, `labelg`, `showg` | Formula currently at 2.9.3 (verified). Nothing is installed on this machine yet — `which geng` fails today. |
| GitHub Actions | CI: verifier + corpus fingerprint tests | Run on `ubuntu-latest` **and** macOS. Make **Linux x86_64 the canonical reference platform** for regenerating ILP-method certificates (see CBC platform note in Version Compatibility). |
| `uv lock` / pinned `requirements.txt` | Freeze the five version numbers above | The program's "nothing rests on memory" rule applied to packaging |

---

## Installation

```bash
# 1. nauty (geng, pickg, countg, shortg, labelg, showg)
brew install nauty                # -> 2.9.3; verify: geng -help | head -3
# (Version-locked alternative: build from source tarball nauty2_9_3.tar.gz
#  at https://users.cecs.anu.edu.au/~bdm/nauty/ — ./configure && make)

# 2. Python — never the system 3.9.6
uv python install 3.12
uv venv --python 3.12
uv pip install \
  networkx==3.6.1 \
  pulp==3.3.2 \
  ortools==9.15.6755 \
  pynauty==2.8.8.1        # optional; needs a C compiler (Xcode CLT on macOS)

# 3. Dev
uv pip install pytest pytest-xdist ruff hypothesis

# 4. Milestone 2 only (Lean)
# curl elan installer; then a lake project pinned to a mathlib release tag.
# mathlib's own lean-toolchain file dictates the exact Lean (v4.32.0-era).
```

Record at runtime into every certificate/run log: `platform`, `sys.version`, `networkx.__version__`, `pulp.__version__`, the CBC banner (run the bundled binary once with `msg=1`, or invoke it with no args), and `ortools` version. The corpus is only as reproducible as the versions written into it.

---

## Blueprint 1 — Exhaustive generation (nauty geng → Python)

### Flags (verified verbatim from nauty 2.9.3 `geng.c`)

```
geng [-cCmtfkbd#D#] [-kTSPF] [-uygsnh] [-lvq] [-x#X#] n [mine[:maxe]] [res/mod] [file]
  -c  connected only          -C  biconnected only
  -t  triangle-free           -f  4-cycle-free       -b  bipartite
  -d# min-degree lower bound  -D# max-degree upper bound
  -u  count only, no output   -g  graph6 output (default)   -s  sparse6
  -l  canonically label outputs
  -q  suppress auxiliary output
  res/mod : generate part res of mod parts (parallelism); tuned by -x#/-X#,
            which MUST be identical across all parts of one split
```

### Maximal triangle-free (MTF): there is no geng flag — filter by diameter

Maximality is not a hereditary property, so `geng` cannot prune on it. Use the standard characterization (confirmed by OEIS A216783's own comment): **for n ≥ 3, maximal triangle-free ⟺ triangle-free ∧ diameter 2** (disconnected or diameter-≥3 TF graphs always accept a triangle-free edge addition). `pickg` computes diameter in C — flag `-Z#` verified in the 2.9.3 `testg.c` help text (`-z# radius  -Z# diameter`, ranges as `#:#`, `#:`, `:#`):

```bash
# The whole P0 generation, per n (n = 12, 13, 14):
geng -ctq 12 | pickg -Z2 mtf12.g6     # expect exactly  147 graphs
geng -ctq 13 | pickg -Z2 mtf13.g6     # expect exactly  392 graphs
geng -ctq 14 | pickg -Z2 mtf14.g6     # expect exactly 1274 graphs
```

**Scale (verified via OEIS JSON API today):**

| n | all triangle-free (A006785) | maximal triangle-free (A216783) |
|---|---------------------------:|--------------------------------:|
| 11 | 105,071 | 61 |
| 12 | 1,262,180 | **147** |
| 13 | 20,797,002 | **392** |
| 14 | 467,871,369 | **1,274** |
| 15 | 1.4 × 10¹⁰ | 5,036 |
| 16 | — | 25,617 |

So P0's entire frontier is **1,813 graphs** — generation cost lives in the geng/pickg pipe (n=14 pushes ~446M connected TF graphs through pickg; hours single-core, minutes with `res/mod` splitting, e.g. `geng -ctq 14 0/8 | pickg -Z2 part0.g6 &` …). The CDM ILP per instance, not generation, is the real work.

**Why maximal-only suffices for the CDM frontier** (derivation — re-verify in phase): if H ⊆ H′ with H′ a maximal TF completion, then G = H̄ ⊇ H̄′ = G′; a connected dominating matching of G′ is edge-subset, domination and connectivity all preserved in the denser G. Every TF H completes to a maximal one, so CDM verified on complements of all maximal TF graphs of order n settles CDM for **all** α=2 graphs of order n (special-case H = complete bipartite, where G′ is disconnected and CLWY's hypothesis excludes it). This is why 1,813 graphs close the n=12–14 frontier that CLWY (arXiv 2512.17114) verified only to n ≤ 11.

### Piping into Python

```python
import subprocess, networkx as nx

def mtf_stream(n: int):
    geng  = subprocess.Popen(["geng", "-ctq", str(n)], stdout=subprocess.PIPE)
    pickg = subprocess.Popen(["pickg", "-q", "-Z2"], stdin=geng.stdout,
                             stdout=subprocess.PIPE)
    geng.stdout.close()
    for line in pickg.stdout:                       # one graph6 per line
        yield nx.from_graph6_bytes(line.strip())    # or a local bitset parser
    # check pickg/geng return codes; assert stream count == A216783[n]
```

- Keep the C filter in the pipe; Python only ever sees the ~10³ survivors. For anything where Python must touch millions of graphs, parse graph6 into `int` bitset adjacency rows with a ~15-line local decoder instead of building `nx.Graph` objects.
- `showg`/`listg` (human-readable dumps) are unnecessary in the pipeline — parse graph6 directly.
- **pynauty vs shelling out:** shelling out is not a choice, it's forced — pynauty has no generation API (verified). pynauty's role is `autgrp()` (orbits for symmetry breaking, Blueprint 3) and `certificate()` (dict-key dedup inside Python).

### Canonical-form dedup

- `geng` output is **already isomorph-free** (McKay canonical-augmentation) — no dedup needed on a single geng stream.
- Merging streams from *other* generators (P7 local-search flips, Cayley constructions): pipe through **`shortg`** (canonical-label + sort + unique, the dedicated tool) or `labelg` + `sort -u` on canonical graph6 lines; in-process, use `pynauty.certificate`.
- **Never** use networkx's Weisfeiler–Lehman hash for dedup — it is not canonical (collisions possible), which violates the exactness discipline. Prefilter at most.

### Cross-checks (Falsification-Rule spirit applied to our own generator)

1. Counts vs OEIS A216783 (147 / 392 / 1274) as a pytest assertion.
2. Recount with `countg` on the filtered file: `countg -Z2 -T0 mtf14.g6` (also `-T0` = zero triangles — an independent property audit; `pickg`/`countg` additionally expose `-N#` chromatic number, `-t` vertex-transitive, `-k#` max clique for spot audits).
3. Optional third opinion: the Brandt–Brinkmann–Harmuth **MTF** generator / Goedgebeur's **triangleramsey** (caagt.ugent.be, linked from A216783) generate maximal TF graphs directly — useful once the frontier moves past n=16 where the filter pipeline gets expensive; treat as cross-check, not primary (aging C code, less ubiquitous than nauty).

---

## Blueprint 2 — Exact maximum matching (ν(H), hence χ(G) = n − ν(H))

### networkx is correct and sufficient — keep it

`nx.max_weight_matching(H, maxcardinality=True)` implements Edmonds' blossom + primal-dual method, **O(n³)**, and per official docs is exact under integer arithmetic for integer weights (all weights here are 1). n = 501 is milliseconds-to-seconds. `len(M)` is ν(H).

### Determinism analysis (the hazards, precisely)

1. **ν itself is a graph invariant** — the *value* cannot vary across networkx versions, platforms, or hash seeds. Only the matching *set* can vary, and nothing in the pipeline stores the matching, only ν and the (independently verified) branch-set models. So `matching_number` is version-proof.
2. **Int nodes are hash-stable**: `PYTHONHASHSEED` randomizes str/bytes only; all vertices are `int` (hash = identity). No env flags needed.
3. **The real reproducibility hazard is upstream of networkx**, in `triangle_free_process`: it iterates CPython `set`s (`for w in adj[v]`), and the discard order feeds `RandomSet`'s swap-with-last layout, which decides which pair each `rng.randrange` draw picks. Set iteration order for ints is deterministic *within* one CPython version but **not guaranteed across versions**. Likewise `random.shuffle`/`randrange` are stable in practice across 3.10–3.13 but only `Random.random()` is formally guaranteed by the docs. **Mitigation (mandatory):** pin CPython 3.12.x exactly; add a corpus-fingerprint pytest that regenerates n=31 seed=1 (must give |E(H)| = 131 and the stored `H_edges` byte-exactly) plus one Cayley exemplar before any batch run. If a future Python bumps set internals, the fingerprint test catches it before the corpus lies.
4. Keep Appendix C's habit of building graphs from **sorted edge lists** — insertion order is the only thing networkx iteration order depends on.

### Independent cross-check (Asymmetry Principle applied to χ)

χ enters every kill; give ν a second, independent exact method: a 10-line CP-SAT model (one Bool per H-edge, `add_at_most_one` per vertex, maximize) must reproduce ν on every instance. Two independent exact solvers agreeing beats trusting one library. Optional but recommended for milestone-2 future-proofing: also store a **Tutte–Berge witness** (a vertex set U with |U| + odd-components bound tight) so the ν-maximality half of χ = n − ν becomes formally *checkable* later; extraction needs Gallai–Edmonds structure, which networkx does not expose — schedule as a small internal implementation if M2 wants it (flagged, not required for M1).

### What not to use here

- **SciPy**: `scipy.sparse.csgraph` has bipartite matching only — no general-graph blossom (MEDIUM-HIGH; long-standing API surface). H is not bipartite.
- **Blossom V (Kolmogorov)**: fastest known implementation, but research-only license, no redistribution — incompatible with a reproducible public harness, and unnecessary at n ≤ 501.
- **NetworKit / igraph** matchings: approximate or bipartite-focused; nothing to gain.

---

## Blueprint 3 — Exact had₂: PuLP/CBC (reference) + CP-SAT (prover), one interface

### Division of labor

| Role | Backend | Why |
|------|---------|-----|
| Reference / corpus continuity | PuLP 3.3.2 + bundled CBC, single thread (`PULP_CBC_CMD(msg=0, timeLimit=…)`) | Byte-compatible with Appendix C; deterministic (1 thread); reproduces the 296-corpus lineage |
| Optimality prover / scaled search | CP-SAT 9.15 | Integer-exact bounds, parallel portfolio, hints, symmetry handling, model export |
| Any **impossibility-flavored** result (had₂ < χ, INFEASIBLE) | **Both**, in disagreement-hunting mode | Radioactive-impossibility protocol below |

Appendix C's pulp encoding stays **verbatim** as the reference implementation. Two operational notes: PuLP 3.3.2 emits a v4 deprecation warning around `PULP_CBC_CMD` — silence it, do not "fix" it by upgrading; and the seed-137-style `model_branch_sets` produced by CBC are *solver-version-dependent among optimal solutions* — reproduction of ILP-method certificates is **semantic** (same had₂ value, verifier passes), while heuristic-method certificates (26 of 27 stored) reproduce byte-exactly from (n, seed). Say so in the corpus schema.

### Constraint generation: enumerate obstructions from H, not pairs of G-edges

Appendix C builds pair-pair conflicts with an O(|E_G|²) double loop — fine at n=31, hopeless at n=301+ (|E_G| ~ 10⁴–10⁵). Triangle-freeness of H gives an equivalent near-linear enumeration (same constraint set — assert equal counts against the naive loop in tests at n=31):

- **pair–pair** (obstructing C4 in H): edges m_{ab}, m_{cd} conflict ⟺ {c,d} ⊆ N_H(a) ∩ N_H(b). Enumerate: for each G-edge {a,b}, every 2-subset of W = N_H(a) ∩ N_H(b) (each such {c,d} is automatically a G-edge, since c,d ∈ N_H(a) and H is triangle-free). Cost Σ C(codeg,2).
- **single–pair** (obstructing path a–v–b in H): s_v conflicts m_{ab} ⟺ {a,b} ⊆ N_H(v). Enumerate 2-subsets of each N_H(v) (again automatically G-edges). Cost Σ C(deg_H(v),2).
- **single–single**: exactly the H-edges.

### CP-SAT model (API names verified against `cp_model.py` on the or-tools `stable` branch)

```python
from ortools.sat.python import cp_model
import itertools
from collections import defaultdict

def had2_cpsat(adj, n, chi=None, *, workers=8, seed=1, time_limit=None,
               hint=None, mode="optimize", log_path=None):
    m = cp_model.CpModel()
    Gedges = [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]
    mv = {e: m.new_bool_var(f"m_{e[0]}_{e[1]}") for e in Gedges}
    sv = [m.new_bool_var(f"s_{v}") for v in range(n)]

    at_vertex = defaultdict(list)
    for e in Gedges:
        at_vertex[e[0]].append(mv[e]); at_vertex[e[1]].append(mv[e])
    for v in range(n):                                   # vertex-disjointness
        m.add_at_most_one(at_vertex[v] + [sv[v]])

    seen = set()
    for (a, b) in Gedges:                                # pair-pair via C4 in H
        for c, d in itertools.combinations(sorted(adj[a] & adj[b]), 2):
            key = ((a, b), (c, d)) if (a, b) < (c, d) else ((c, d), (a, b))
            if key not in seen:
                seen.add(key)
                m.add_at_most_one([mv[(a, b)], mv[(c, d)]])
    for v in range(n):                                   # single-pair via P3 in H
        for a, b in itertools.combinations(sorted(adj[v]), 2):
            m.add_at_most_one([sv[v], mv[(a, b)]])
    for u in range(n):                                   # single-single: H-edges
        for w in adj[u]:
            if w > u:
                m.add_at_most_one([sv[u], sv[w]])

    obj = sum(mv.values()) + sum(sv)
    if mode == "certify" and chi is not None:
        m.add(obj >= chi)            # existence mode: any feasible sol certifies
    m.maximize(obj)

    if hint is not None:             # warm start from the heuristic model
        for e in Gedges: m.add_hint(mv[e], e in hint["pairs"])
        for v in range(n): m.add_hint(sv[v], v in hint["singles"])

    s = cp_model.CpSolver()
    s.parameters.num_workers = workers          # 0 = all cores (default)
    s.parameters.random_seed = seed             # default 1
    if time_limit: s.parameters.max_time_in_seconds = time_limit
    if mode == "certify": s.parameters.stop_after_first_solution = True
    s.parameters.log_search_progress = True     # capture log for the run archive
    m.export_to_file("had2_model.pb.txt")       # audit artifact (Falsification suite)
    status = s.solve(m)

    proven = (status == cp_model.OPTIMAL)
    val = int(s.objective_value) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
    bound = s.best_objective_bound
    fam = ([e for e in Gedges if s.boolean_value(mv[e])] +
           [(v,) for v in range(n) if s.boolean_value(sv[v])]) if val is not None else None
    return val, bound, proven, s.status_name(status), fam
```

Everything above is the current snake_case API (`new_bool_var`, `add_at_most_one`, `add_bool_or`, `add_exactly_one`, `add_hint(var, value)`, `maximize`, `export_to_file`, `solve`, `value`/`boolean_value`, `objective_value`, `best_objective_bound`, `status_name`; module constants `OPTIMAL/FEASIBLE/INFEASIBLE/MODEL_INVALID/UNKNOWN`). Write snake_case only; legacy CamelCase is deprecated compatibility surface.

**Two solve modes, matching the Asymmetry Principle:**
- `certify` (cheap, lavish use): constrain `obj ≥ χ`, `stop_after_first_solution=true` — any solution found goes straight to the *independent verifier*, which is the actual arbiter. Solver nondeterminism is irrelevant here: certificates are checked, not trusted.
- `optimize` (expensive, careful use): full maximize; had₂ is exact **iff** `status == OPTIMAL`; always record `objective_value` *and* `best_objective_bound` (they must coincide) plus the search log.

**Determinism doctrine (verified from `sat_parameters.proto`, stable branch):** `random_seed` default 1; `num_workers` default 0 = all cores; the parallel portfolio is *not* run-to-run deterministic — determinism is available two ways: `num_workers = 1` with fixed seed, or `interleave_search: true` + fixed `interleave_batch_size`, whose proto comment states the search is then "deterministic (independently of num_workers!)". Policy: hunt phases may run the fast nondeterministic portfolio (existence results get verified anyway); **any reported optimality or infeasibility gets a deterministic re-run** (1 worker, pinned seed, logged).

**Radioactive impossibility protocol (had₂ < χ or INFEASIBLE):** CP-SAT has real, documented soundness regressions in parallel mode — nondeterministic results (issue #3590), *Optimal-with-1-worker vs Infeasible-with-8-workers* (issue #3842), rare wrong-infeasible reports (issue #4839). Therefore an SHC-counterexample claim requires all of: (a) CP-SAT `OPTIMAL` with `best_objective_bound == objective_value < χ` in a deterministic single-worker run; (b) independent CBC agreement on the same instance (Appendix C encoding); (c) the exported model proto + logs archived in the corpus; (d) the constraint-set count cross-check (obstruction enumeration ≡ naive enumeration) passing on that instance. Only then is it a certified `had₂(G) < χ(G)`.

**Symmetry breaking for vertex-transitive candidates (P2 Cayley, P4 Kneser, P3 Higman–Sims):** CP-SAT already detects model symmetry in presolve (`symmetry_level` default 2 — verified). One safe manual cut: if the candidate is vertex-transitive and had₂ ≥ 1, some optimal family covers any chosen vertex (map a covered vertex onto it by an automorphism), so `model.add(sv[0] + sum(mv[e] for e in Gedges if 0 in e) == 1)` is sound. Compute orbits with `pynauty.autgrp` to confirm transitivity programmatically before applying. Do not hand-roll lex-leader constraints unless profiling demands it — wrong symmetry breaking silently deletes optima, which in this program is a soundness bug, not a performance bug.

**Scale expectations:** n=31: trivial (sub-second). n≈150: ~10⁴ pair vars, fine. n=501: ~10⁵ vars — Python model *construction* becomes minutes; keep the obstruction enumeration (near-linear) and consider building once and re-solving with different objective thresholds.

---

## Blueprint 4 — Branch-set-3 escalation (had₃, seagulls)

All structure below follows from H triangle-free; each claim is a two-line proof to re-derive in-phase (and to encode as verifier assertions).

**Valid triples.** A branch set T = {a,b,c} needs G[T] connected ⟺ H[T] has ≤ 1 edge (2 H-edges on 3 vertices leave G[T] a single edge + isolated vertex; 3 is a triangle in H, impossible). Two classes:

1. **Seagull triples** — exactly one H-edge, say uv ∈ H, w with uw, vw ∉ H. Then G[T] is an induced path: G-edges {u,w},{v,w}, non-edge {u,v} — an induced P3 of G, i.e. exactly a **Chudnovsky–Seymour seagull**. Key structural fact: their common H-neighborhood N_H(u) ∩ N_H(v) ∩ N_H(w) ⊆ N_H(u) ∩ N_H(v) = ∅ (triangle-freeness). **A seagull triple conflicts with nothing** — every other disjoint branch set is automatically G-adjacent to it. Model impact: seagull variables join only the vertex-disjointness `add_at_most_one` rows; zero new conflict constraints. Count: Σ_{uv∈E(H)} (n − |N_H(u) ∪ N_H(v)|) ≈ m·n (n=31: ~3–4k; n=151: ~10⁵ — still tractable).
2. **G-triangle triples** — H-independent {a,b,c}. Conflicts are governed by W(T) = N_H(a) ∩ N_H(b) ∩ N_H(c): T conflicts with singleton v ⟺ v ∈ W(T); with pair {x,y} ⟺ {x,y} ⊆ W(T); with triple T′ ⟺ T′ ⊆ W(T). **Prune by empty common neighborhood:** compute W(T) per candidate triple (bitset AND); if empty — the typical case in sparse TFP-style H — the triple generates no conflict constraints at all; skip constraint emission entirely and optionally skip low-value triples.

**Tiered escalation (recommended runbook order):**
- **Tier 0:** had₂ exact (Blueprint 3). Only escalate on a certified had₂ < χ.
- **Tier 1:** add seagull triples only. Model grows by ~m·n conflict-free Bools; objective unchanged (maximize family size). Cheap, and covers exactly the Chudnovsky–Seymour mechanism.
- **Tier 2:** add G-triangle triples with W(T)-pruned conflicts (full had₃).

**Chudnovsky–Seymour seagull conditions as a free pre-gate** ("Packing seagulls", Combinatorica 32 (2012) 251–282; statement re-verified via its restatement as Thm 3.1 in arXiv 2510.12564): for α(G) ≤ 2 (and G ≠ W₅ when ℓ = 2), G has ℓ pairwise disjoint seagulls ⟺ (i) |V(G)| ≥ 3ℓ, (ii) G is ℓ-connected, (iii) every clique has capacity ≥ ℓ, (iv) G has an **anti-matching** of cardinality ℓ — i.e. a matching of size ℓ in Ḡ = H. Condition (iv) is literally **ν(H) ≥ ℓ**, already computed exactly; (i) is arithmetic; (ii) is `nx.node_connectivity` (exact). Use (i), (ii), (iv) as instant necessary checks before spending solver time on tier-1/2; implement clique-capacity (iii) only if the gate proves useful (lift the exact capacity definition from the paper when implementing — the restatement's formula should be taken from the primary source, MEDIUM confidence on its transcription here). The paper also gives a poly-time seagull-packing algorithm — an optional independent oracle for tier-1 feasibility.

**P0's CDM ILP note:** CP-SAT has **no lazy-constraint/user-cut callback**, so "connected" in connected-dominating-matching must be encoded explicitly (single-commodity flow over the contact structure is tiny at n ≤ 14) or checked by enumeration — at 12–14 vertices, enumerate-and-check with bitsets is honest and fast, with CP-SAT as the cross-check. If the CDM frontier later needs lazy separation at larger n, the escape hatch is PySCIPOpt (SCIP supports constraint handlers) — do not contort CP-SAT into it.

---

## Blueprint 5 — Lean 4 + mathlib (milestone 2 only)

**State of mathlib (verified 2026-07-21 against the mathlib4 master tree and docs):**
- `Mathlib/Combinatorics/SimpleGraph/` contains **no minor theory**: no `Minor.lean`, no `Contraction.lean`, no subdivision. (Matroid minors exist; graph minors do not.)
- Present and useful: `Subgraph.lean`, `Connectivity/`, `Walk/`, `Matching.lean` (`Subgraph.IsMatching`, `Subgraph.IsPerfectMatching` — **no `matchingNumber`**, no Berge/Tutte–Berge), `Tutte.lean` (Tutte's perfect-matching theorem), `Coloring.lean` (+ `chromaticNumber`), `Clique.lean`, `Girth.lean`, `Diam.lean`, `Operations.lean`, `Bipartite.lean`, `Cayley.lean`, `StronglyRegular.lean`.
- Toolchain: Lean stable is **v4.32.0**; pin mathlib to a dated release tag and let its `lean-toolchain` file pick the compiler (release-date rendering on the fetched page was ambiguous — version number verified, treat the date as approximate; MEDIUM-HIGH).

**What must be defined locally** (small, and deliberately certificate-shaped — general minor theory is *not needed* to state what the harness proves):

```lean
-- K_k model with branch sets of size ≤ 2 (SHC certificates)
structure ModelLE2 (G : SimpleGraph (Fin n)) (k : ℕ) where
  sets     : Fin k → Finset (Fin n)
  card_le  : ∀ i, (sets i).card ∈ ({1, 2} : Set ℕ)
  disjoint : ∀ i j, i ≠ j → Disjoint (sets i) (sets j)
  pairEdge : ∀ i, ∀ a ∈ sets i, ∀ b ∈ sets i, a ≠ b → G.Adj a b   -- size-2 ⇒ G-edge
  cross    : ∀ i j, i ≠ j → ∃ a ∈ sets i, ∃ b ∈ sets j, G.Adj a b
```

with a `Decidable` instance so each stored certificate closes by `decide` (n=31 easily; `native_decide` for the n≥151 showpieces — and the program's reporting rule already prescribes the honest phrasing: "this file compiles, and its statement says exactly X"). Extending to size ≤ 3 adds the trivial connectivity case-split of Blueprint 4. If a genuine `IsMinor` is wanted, prove once, locally: `ModelLE2 G k → (K k) ≼ G` with contraction defined via a quotient map — but this is optional polish, not the certificate.

**The honest formalization asymmetry (flag for M2 planning):** the model/adjacency side is decidable-trivial; the χ(G) = n − ν(H) side splits into χ ≤ n − ν (constructive coloring from an explicit matching — easy) and χ ≥ n − ν (needs *maximality* of the matching — requires a Tutte–Berge/Gallai–Edmonds witness, none of which is in mathlib). Hence the Blueprint-2 recommendation to start storing Tutte–Berge witnesses in milestone 1 certificates: it converts M2's hardest lemma into another finite check.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| geng + `pickg -Z2` filter | Brandt–Brinkmann–Harmuth MTF / Goedgebeur triangleramsey (direct MTF generators) | Frontier past n≈16, where filtering 10¹⁰ TF graphs stops being fun; until then, cross-check only |
| pynauty for orbits/dedup | python-igraph (BLISS canonical labeling) | If pynauty won't build on a future Python; igraph is faster on huge graphs but adds a second canonical-form convention — don't mix conventions within one corpus |
| CP-SAT for exact optimization | PySCIPOpt (SCIP) | Only if lazy separation / constraint handlers become necessary (CDM connectivity at larger n); SCIP is also a third independent optimality opinion for radioactive claims |
| PuLP 3.3.2 + bundled CBC | HiGHS via PuLP | Never for the reference lineage; acceptable as yet another cross-check backend |
| networkx blossom | Hand-rolled Gallai–Edmonds implementation | Only to extract Tutte–Berge witnesses (Blueprint 2/5); keep networkx as the ν oracle |
| Lean 4 + mathlib (M2) | Isabelle/AFP (has some graph theory) | No — mathlib momentum, SimpleGraph maturity, and the author's stated plan |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| System Python 3.9.6 | networkx 3.6.1 needs ≥3.11; PuLP 3.3.2 needs ≥3.10; would force stale networkx 3.2.x | uv-managed CPython 3.12.x |
| PuLP 4.0.0a* | Removes bundled CBC / deprecates `PULP_CBC_CMD` mid-stream — breaks Appendix C verbatim and corpus continuity | Hard pin `pulp==3.3.2` |
| nauty 2.9.0 | Upstream-documented serious dreadnaut bug in that release | 2.9.3 |
| Blossom V | Research-only license, no redistribution; kills reproducibility of a public harness | networkx blossom + CP-SAT cross-check |
| SciPy for ν(H) | csgraph offers bipartite matching only; H is non-bipartite | networkx `max_weight_matching(maxcardinality=True)` |
| WL-hash (networkx) for isomorph dedup | Not canonical — hash collisions would silently merge distinct candidates | `shortg` / `labelg` / pynauty `certificate` |
| pynauty for generation | It has no geng binding at all (verified) | `subprocess` → `geng` |
| CP-SAT default parallel portfolio for *reported* impossibility | Documented wrong-INFEASIBLE / nondeterminism regressions (#3590, #3842, #4839) | Deterministic re-run (1 worker or `interleave_search`) + CBC agreement |
| Solver-found models trusted as-is | Violates the program's trust root | The independent verifier rules on every model, always |
| `geng -l` in the pipeline | Pointless canonical-labeling cost pre-filter | Label only survivors if needed |

## Stack Patterns by Variant

**Corpus-reproduction mode (tests, CI):** exact pins (3.12.x, networkx 3.6.1, pulp 3.3.2, ortools 9.15.6755); Linux x86_64 as the canonical platform for ILP-method certificate regeneration; fingerprint tests (n=31 seed 1 and seed 137; one Cayley) run before anything else; CBC single-thread.

**Hunt mode (P1–P7 kills):** CP-SAT `certify` mode with hints from the Appendix C heuristic, full parallel portfolio, generous `max_time_in_seconds`; nondeterminism acceptable because the verifier is the arbiter; every kill logs (n, seed, method, solver versions, wall time).

**Radioactive mode (had₂ < χ, RESISTANT instances, survivor protocol):** deterministic CP-SAT re-run (workers=1, pinned seed; or `interleave_search` + fixed `interleave_batch_size` for deterministic parallelism) + CBC cross-solve + exported `.pb.txt` model + logs archived; scaled retries with symmetry breaking and `max_deterministic_time` budgets (reproducible budget accounting) before anyone utters "impossible".

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| networkx 3.6.1 | Python ≥ 3.11 (3.11–3.14) | Verified on PyPI today |
| PuLP 3.3.2 | Python ≥ 3.10 | Wheel bundles CBC for linux/{arm64,i32,i64}, osx/**i64 only**, win — on Apple Silicon the bundled CBC runs under **Rosetta 2** (x86_64). Determinism unaffected; make Linux the reference regeneration platform |
| ortools 9.15.6755 | Python 3.9–3.14; macosx_11_0_arm64 cp312 wheel verified | CP-SAT API is the snake_case surface quoted above |
| pynauty 2.8.8.1 | Declared 3.8–3.12 (3.13 unverified); bundles nauty 2.8.8 internally | The 2.8.8-vs-2.9.3 split (pynauty vs brew geng) is harmless: canonical forms are never mixed across the two |
| nauty 2.9.3 (brew) | any | `geng`/`pickg` flags quoted here are from the 2.9.3 sources |
| Lean v4.32.0 + mathlib master/tag | elan-managed | Mathlib pin dictates toolchain; no graph-minor prerequisites exist to be version-matched |
| CPython 3.12.x (exact patch pinned) | everything above | Set-iteration order + `random` stability are the byte-reproduction dependencies; fingerprint tests guard them |

## Sources

Primary (HIGH confidence — fetched/inspected 2026-07-21):
- PyPI project pages: [networkx](https://pypi.org/project/networkx/) (3.6.1), [PuLP](https://pypi.org/project/PuLP/) (3.3.2), [ortools](https://pypi.org/project/ortools/) (9.15.6755, cp39–cp314; [arm64 wheel files](https://pypi.org/project/ortools/9.15.6755/#files)), [pynauty](https://pypi.org/project/pynauty/) (2.8.8.1, no geng, bundles nauty 2.8.8)
- [nauty homepage (B. McKay, ANU)](https://users.cecs.anu.edu.au/~bdm/nauty/) — 2.9.3 stable; **nauty2_9_3.tar.gz downloaded; `geng.c` and `testg.c` usage/help texts quoted verbatim** (geng `-t/-c/-d#/-D#/res-mod/-u/-q`; pickg/countg `-Z#` diameter, `-T#` triangles, `-N#` chromatic number, `-t` vertex-transitive)
- [Homebrew nauty formula](https://formulae.brew.sh/formula/nauty) — 2.9.3
- OR-Tools stable branch: [`sat_parameters.proto`](https://raw.githubusercontent.com/google/or-tools/stable/ortools/sat/sat_parameters.proto) (random_seed=1, num_workers=0, symmetry_level=2, `interleave_search` determinism quote, `stop_after_first_solution`, `max_deterministic_time`) and [`cp_model.py`](https://raw.githubusercontent.com/google/or-tools/stable/ortools/sat/python/cp_model.py) (snake_case API + module status constants, grepped locally)
- CP-SAT soundness/determinism regressions: [google/or-tools#3590](https://github.com/google/or-tools/issues/3590), [#3842](https://github.com/google/or-tools/issues/3842), [#4839](https://github.com/google/or-tools/issues/4839); [CP-SAT primer](https://d-krupke.github.io/cpsat-primer/parameters.html) (workers default, hints, logging) — MEDIUM-HIGH secondary
- PuLP 3.3.2 **wheel inspected locally** (solverdir CBC binaries incl. osx/i64-only; `PULP_CBC_CMD` with `_skip_v4_deprecation`) — ground truth for the reference-solver pin
- OEIS via JSON API: [A216783](https://oeis.org/A216783) (maximal TF counts 147/392/1274; diameter-2 characterization; MTF & triangleramsey links), [A006785](https://oeis.org/A006785) (TF counts incl. 467,871,369 at n=14)
- [mathlib4 `Mathlib/Combinatorics/SimpleGraph/` tree](https://github.com/leanprover-community/mathlib4/tree/master/Mathlib/Combinatorics/SimpleGraph) (no Minor/Contraction; Matching/Tutte/Coloring present) + [Matching docs](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Matching.html) (no matchingNumber); [Lean 4 releases](https://github.com/leanprover/lean4/releases) (v4.32.0 stable — version HIGH, displayed date ambiguous → MEDIUM on date)
- Literature anchors: [Costa–Luu–Wood–Yip, arXiv:2512.17114](https://arxiv.org/abs/2512.17114) (CDM verified to n ≤ 11; CDM ⇒ SHC ⇒ HC — matches PROJECT.md); [arXiv:2510.12564](https://arxiv.org/html/2510.12564) (restates Packing-seagulls Thm as its Thm 3.1); Chudnovsky–Seymour, *Packing seagulls*, Combinatorica 32 (2012) 251–282 (capacity formula transcription MEDIUM — lift from the paper when implementing); [networkx `max_weight_matching` docs](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) (blossom, O(n³), integer-exact)

Derivations made here and flagged for in-phase re-verification (MEDIUM-HIGH, short proofs from triangle-freeness): obstruction-based conflict enumeration ≡ Appendix C constraint set; seagull triples are conflict-free; maximal-TF-only suffices for the CDM frontier; vertex-transitive "vertex 0 covered" symmetry cut.

---
*Stack research for: The α = 2 Program (Hadwiger α = 2 certification harness)*
*Researched: 2026-07-21*
