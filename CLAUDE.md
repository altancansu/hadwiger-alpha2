<!-- GSD:project-start source:PROJECT.md -->
## Project

**The α = 2 Program**

A disciplined, fully reproducible harness that redoes the Hadwiger **α = 2 attempt** under strict epistemic hygiene — not a reconstruction of a lost proof, but a reconstruction of the *attempt*, as a competent adversary would run it. Working in the restriction α(G) = 2 (equivalently: H = Ḡ is triangle-free), it builds an exact, certificate-emitting "kill battery" that hunts structured candidate graphs for K_χ minors, verifies every existence claim with a hand-checkable certificate, and treats every impossibility claim as radioactive until exhaustively cross-examined. It is for the author's research program on Hadwiger's Conjecture — the α = 2 case Seymour regards as the crux — and its outputs (a seeded certificate corpus, the toolkit, and datasets) bear directly on questions the current literature poses as open.

**Core Value:** **Reconstruct the *attempt*, under discipline: build the adversary so that anything surviving it is a correct road to a disproof, and anything dying leaves a machine-verified result — never invent the missing hour.** The procedure is identical whether Hadwiger's Conjecture holds for α = 2 or fails, so the program is designed to be maximally valuable under both truths. When tradeoffs arise, epistemic integrity (verified existence, radioactive impossibility) wins over speed, coverage, or narrative.

### Constraints

- **Tech stack:** Python 3 · `networkx` (Edmonds blossom) · `pulp`/CBC (reference ILP) · **OR-Tools CP-SAT** (exact backend, added now) · **nauty `geng -t`** (exhaustive triangle-free generation, added now). Lean 4 + mathlib arrive in milestone 2.
- **The Asymmetry Principle (the central design constraint).** K_k-minor *existence* has a tiny certificate (branch sets, checkable in seconds); *non-existence* has no known certificate of any kind. All epistemic risk concentrates in the impossibility half. The machinery therefore spends existence-checking lavishly and treats every impossibility claim as radioactive. (This is also *why* a formal-verification session can feel conclusive while certifying nothing: the easy-to-formalize direction was never in doubt.)
- **The Falsification Rule.** Any proposed "no K_k minor" argument must first be mechanically executed against the certificate corpus and must decline to prove impossibility on every instance where a verified model exists. The corpus is not merely a results file — it is a falsification suite for bogus impossibility proofs, and it strengthens with every kill.
- **The Monotonicity Audit.** Invariant-based impossibility claims must use genuinely minor-monotone invariants (essentially Colin de Verdière μ and relatives). Rank methods, spectral gaps, and rigidity notions are disqualified at the door — contraction destroys linear structure. Each certificate already proves μ(G) ≥ χ(G) − 1 on its instance.
- **Reporting discipline.** Nothing counts as *found* until the independent verifier passes; nothing counts as *absent* until an exact method proves it. Heuristic resistance is never a result. The phrase "we leanproofed it" is banned; the permitted phrase is "this file compiles, and its statement says exactly X."
- **Reproducibility.** Deterministic in (n, seed); every instance seeded and rebuildable; nothing rests on memory — everything rests on seeds and code.
- **The gate.** G1–G6 run in increasing order of cost; kill on first failure; log the reason and seed.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| Homebrew `nauty` | Installs `geng`, `pickg`, `countg`, `shortg`, `labelg`, `showg` | Formula currently at 2.9.3 (verified). Nothing is installed on this machine yet — `which geng` fails today. |
| GitHub Actions | CI: verifier + corpus fingerprint tests | Run on `ubuntu-latest` only; **Linux x86_64 is the canonical reference platform** for regenerating ILP-method certificates (see CBC platform note in Version Compatibility). macOS CI is **out of scope** per the reproduction-contract decision — the reproduction phase is solver-free and cross-platform byte-exact heuristic replay is explicitly excluded (REQUIREMENTS.md Out of Scope: "Byte-exact cross-platform / cross-interpreter heuristic replay"). |
| `uv lock` / pinned `requirements.txt` | Freeze the five version numbers above | The program's "nothing rests on memory" rule applied to packaging |
## Installation
# 1. nauty (geng, pickg, countg, shortg, labelg, showg)
# (Version-locked alternative: build from source tarball nauty2_9_3.tar.gz
#  at https://users.cecs.anu.edu.au/~bdm/nauty/ — ./configure && make)
# 2. Python — never the system 3.9.6
# 3. Dev
# 4. Milestone 2 only (Lean)
# curl elan installer; then a lake project pinned to a mathlib release tag.
# mathlib's own lean-toolchain file dictates the exact Lean (v4.32.0-era).
## Blueprint 1 — Exhaustive generation (nauty geng → Python)
### Flags (verified verbatim from nauty 2.9.3 `geng.c`)
### Maximal triangle-free (MTF): there is no geng flag — filter by diameter
# The whole P0 generation, per n (n = 12, 13, 14):
| n | all triangle-free (A006785) | maximal triangle-free (A216783) |
|---|---------------------------:|--------------------------------:|
| 11 | 105,071 | 61 |
| 12 | 1,262,180 | **147** |
| 13 | 20,797,002 | **392** |
| 14 | 467,871,369 | **1,274** |
| 15 | 1.4 × 10¹⁰ | 5,036 |
| 16 | — | 25,617 |
### Piping into Python
- Keep the C filter in the pipe; Python only ever sees the ~10³ survivors. For anything where Python must touch millions of graphs, parse graph6 into `int` bitset adjacency rows with a ~15-line local decoder instead of building `nx.Graph` objects.
- `showg`/`listg` (human-readable dumps) are unnecessary in the pipeline — parse graph6 directly.
- **pynauty vs shelling out:** shelling out is not a choice, it's forced — pynauty has no generation API (verified). pynauty's role is `autgrp()` (orbits for symmetry breaking, Blueprint 3) and `certificate()` (dict-key dedup inside Python).
### Canonical-form dedup
- `geng` output is **already isomorph-free** (McKay canonical-augmentation) — no dedup needed on a single geng stream.
- Merging streams from *other* generators (P7 local-search flips, Cayley constructions): pipe through **`shortg`** (canonical-label + sort + unique, the dedicated tool) or `labelg` + `sort -u` on canonical graph6 lines; in-process, use `pynauty.certificate`.
- **Never** use networkx's Weisfeiler–Lehman hash for dedup — it is not canonical (collisions possible), which violates the exactness discipline. Prefilter at most.
### Cross-checks (Falsification-Rule spirit applied to our own generator)
## Blueprint 2 — Exact maximum matching (ν(H), hence χ(G) = n − ν(H))
### networkx is correct and sufficient — keep it
### Determinism analysis (the hazards, precisely)
### Independent cross-check (Asymmetry Principle applied to χ)
### What not to use here
- **SciPy**: `scipy.sparse.csgraph` has bipartite matching only — no general-graph blossom (MEDIUM-HIGH; long-standing API surface). H is not bipartite.
- **Blossom V (Kolmogorov)**: fastest known implementation, but research-only license, no redistribution — incompatible with a reproducible public harness, and unnecessary at n ≤ 501.
- **NetworKit / igraph** matchings: approximate or bipartite-focused; nothing to gain.
## Blueprint 3 — Exact had₂: PuLP/CBC (reference) + CP-SAT (prover), one interface
### Division of labor
| Role | Backend | Why |
|------|---------|-----|
| Reference / corpus continuity | PuLP 3.3.2 + bundled CBC, single thread (`PULP_CBC_CMD(msg=0, timeLimit=…)`) | Byte-compatible with Appendix C; deterministic (1 thread); reproduces the 296-corpus lineage |
| Optimality prover / scaled search | CP-SAT 9.15 | Integer-exact bounds, parallel portfolio, hints, symmetry handling, model export |
| Any **impossibility-flavored** result (had₂ < χ, INFEASIBLE) | **Both**, in disagreement-hunting mode | Radioactive-impossibility protocol below |
### Constraint generation: enumerate obstructions from H, not pairs of G-edges
- **pair–pair** (obstructing C4 in H): edges m_{ab}, m_{cd} conflict ⟺ {c,d} ⊆ N_H(a) ∩ N_H(b). Enumerate: for each G-edge {a,b}, every 2-subset of W = N_H(a) ∩ N_H(b) (each such {c,d} is automatically a G-edge, since c,d ∈ N_H(a) and H is triangle-free). Cost Σ C(codeg,2).
- **single–pair** (obstructing path a–v–b in H): s_v conflicts m_{ab} ⟺ {a,b} ⊆ N_H(v). Enumerate 2-subsets of each N_H(v) (again automatically G-edges). Cost Σ C(deg_H(v),2).
- **single–single**: exactly the H-edges.
### CP-SAT model (API names verified against `cp_model.py` on the or-tools `stable` branch)
- `certify` (cheap, lavish use): constrain `obj ≥ χ`, `stop_after_first_solution=true` — any solution found goes straight to the *independent verifier*, which is the actual arbiter. Solver nondeterminism is irrelevant here: certificates are checked, not trusted.
- `optimize` (expensive, careful use): full maximize; had₂ is exact **iff** `status == OPTIMAL`; always record `objective_value` *and* `best_objective_bound` (they must coincide) plus the search log.
## Blueprint 4 — Branch-set-3 escalation (had₃, seagulls)
- **Tier 0:** had₂ exact (Blueprint 3). Only escalate on a certified had₂ < χ.
- **Tier 1:** add seagull triples only. Model grows by ~m·n conflict-free Bools; objective unchanged (maximize family size). Cheap, and covers exactly the Chudnovsky–Seymour mechanism.
- **Tier 2:** add G-triangle triples with W(T)-pruned conflicts (full had₃).
## Blueprint 5 — Lean 4 + mathlib (milestone 2 only)
- `Mathlib/Combinatorics/SimpleGraph/` contains **no minor theory**: no `Minor.lean`, no `Contraction.lean`, no subdivision. (Matroid minors exist; graph minors do not.)
- Present and useful: `Subgraph.lean`, `Connectivity/`, `Walk/`, `Matching.lean` (`Subgraph.IsMatching`, `Subgraph.IsPerfectMatching` — **no `matchingNumber`**, no Berge/Tutte–Berge), `Tutte.lean` (Tutte's perfect-matching theorem), `Coloring.lean` (+ `chromaticNumber`), `Clique.lean`, `Girth.lean`, `Diam.lean`, `Operations.lean`, `Bipartite.lean`, `Cayley.lean`, `StronglyRegular.lean`.
- Toolchain: Lean stable is **v4.32.0**; pin mathlib to a dated release tag and let its `lean-toolchain` file pick the compiler (release-date rendering on the fetched page was ambiguous — version number verified, treat the date as approximate; MEDIUM-HIGH).
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
- PyPI project pages: [networkx](https://pypi.org/project/networkx/) (3.6.1), [PuLP](https://pypi.org/project/PuLP/) (3.3.2), [ortools](https://pypi.org/project/ortools/) (9.15.6755, cp39–cp314; [arm64 wheel files](https://pypi.org/project/ortools/9.15.6755/#files)), [pynauty](https://pypi.org/project/pynauty/) (2.8.8.1, no geng, bundles nauty 2.8.8)
- [nauty homepage (B. McKay, ANU)](https://users.cecs.anu.edu.au/~bdm/nauty/) — 2.9.3 stable; **nauty2_9_3.tar.gz downloaded; `geng.c` and `testg.c` usage/help texts quoted verbatim** (geng `-t/-c/-d#/-D#/res-mod/-u/-q`; pickg/countg `-Z#` diameter, `-T#` triangles, `-N#` chromatic number, `-t` vertex-transitive)
- [Homebrew nauty formula](https://formulae.brew.sh/formula/nauty) — 2.9.3
- OR-Tools stable branch: [`sat_parameters.proto`](https://raw.githubusercontent.com/google/or-tools/stable/ortools/sat/sat_parameters.proto) (random_seed=1, num_workers=0, symmetry_level=2, `interleave_search` determinism quote, `stop_after_first_solution`, `max_deterministic_time`) and [`cp_model.py`](https://raw.githubusercontent.com/google/or-tools/stable/ortools/sat/python/cp_model.py) (snake_case API + module status constants, grepped locally)
- CP-SAT soundness/determinism regressions: [google/or-tools#3590](https://github.com/google/or-tools/issues/3590), [#3842](https://github.com/google/or-tools/issues/3842), [#4839](https://github.com/google/or-tools/issues/4839); [CP-SAT primer](https://d-krupke.github.io/cpsat-primer/parameters.html) (workers default, hints, logging) — MEDIUM-HIGH secondary
- PuLP 3.3.2 **wheel inspected locally** (solverdir CBC binaries incl. osx/i64-only; `PULP_CBC_CMD` with `_skip_v4_deprecation`) — ground truth for the reference-solver pin
- OEIS via JSON API: [A216783](https://oeis.org/A216783) (maximal TF counts 147/392/1274; diameter-2 characterization; MTF & triangleramsey links), [A006785](https://oeis.org/A006785) (TF counts incl. 467,871,369 at n=14)
- [mathlib4 `Mathlib/Combinatorics/SimpleGraph/` tree](https://github.com/leanprover-community/mathlib4/tree/master/Mathlib/Combinatorics/SimpleGraph) (no Minor/Contraction; Matching/Tutte/Coloring present) + [Matching docs](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Matching.html) (no matchingNumber); [Lean 4 releases](https://github.com/leanprover/lean4/releases) (v4.32.0 stable — version HIGH, displayed date ambiguous → MEDIUM on date)
- Literature anchors: [Costa–Luu–Wood–Yip, arXiv:2512.17114](https://arxiv.org/abs/2512.17114) (CDM verified to n ≤ 11; CDM ⇒ SHC ⇒ HC — matches PROJECT.md); [arXiv:2510.12564](https://arxiv.org/html/2510.12564) (restates Packing-seagulls Thm as its Thm 3.1); Chudnovsky–Seymour, *Packing seagulls*, Combinatorica 32 (2012) 251–282 (capacity formula transcription MEDIUM — lift from the paper when implementing); [networkx `max_weight_matching` docs](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.matching.max_weight_matching.html) (blossom, O(n³), integer-exact)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

## Remote Compute (Phase 8+ sweeps)

Heavy sweeps (Phase 8's sum-free Cayley break-hunt and later large-n pools) do NOT run here — they run on a **rented remote Linux box driven over SSH from the author's Mac session**. Full runbook: **`docs/COMPUTE.md`** (provisioning, verification, sweep commands, discipline).

- The box is compute muscle only. Develop + small-scale-test on the Mac → `git push` → box `git pull && uv sync --all-extras --all-groups` → run `uv run pytest -n <N> -m slow` in `tmux`.
- The **live SSH endpoint is NOT committed** (public repo + ephemeral rental): it lives in the gitignored **`.compute-box`** at the repo root. To reconnect after a re-rent, update that file.
- On-box discipline: instance-level parallelism only; **`num_workers=1` + deterministic solver budgets** (`max_deterministic_time` / CBC `maxNodes`) on any reported impossibility/RESISTANT verdict, so DECIDED-vs-RESISTANT depends on `(n, seed)`, never machine speed.
