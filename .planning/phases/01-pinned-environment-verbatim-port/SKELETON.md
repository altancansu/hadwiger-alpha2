# Walking Skeleton — The α = 2 Program

**Phase:** 1
**Generated:** 2026-07-21

## Phase Goal (user story)

> The ROADMAP `**Goal:**` line for Phase 1 is written as an outcome sentence, not the canonical
> "As a / I want to / so that" user-story form. Per the MVP user-story rules this discrepancy is
> surfaced rather than silently normalized; the story below is a faithful reframing of the existing
> ROADMAP goal (no new scope invented). If a stricter form is wanted, run `/gsd mvp-phase 1`.

**As a** maintainer of the α = 2 program, **I want to** run the Appendix C toolkit from the repo on a pinned CPython 3.12.13, **so that** n=31 seed=1 reproduces byte-identically (|E(H)|=131, ν=15, χ=16) and every downstream phase builds on a locked, verified foundation.

## Capability Proven End-to-End

Running `uv run python -m alpha2.repro.baseline` on a clean checkout resolves the pinned interpreter and dependencies from the committed lockfile, executes the ported verbatim toolkit, and regenerates the n=31 seed=1 instance to a verified K₁₆ model whose H_edges hash matches the frozen golden — proving the full env → generate → matching → search → verify → fingerprint stack works from repo-relative paths alone.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Runtime | uv-managed CPython **3.12.13** (exact patch, via `.python-version`) | Only minor version all pins support; byte-reproduction depends on CPython set-iteration internals. System 3.9.6 (EOL) cannot run networkx 3.6.1. |
| Dependency pinning | `pyproject.toml` + committed `uv.lock` | uv fetches the exact CPython patch and produces a reproducible lockfile; "nothing rests on memory" applied to packaging. |
| Core deps | networkx==3.6.1, pulp==3.3.2 (hard pin), ortools==9.15.6755 | Only networkx is exercised in Phase 1; pulp/ortools are locked-but-not-exercised (needed Phase 3+). pulp 4.0 removes bundled CBC — hard pin 3.3.2. |
| Optional extra | `nauty = ["pynauty==2.8.8.1"]` | No macOS wheel (sdist build needs a compiler); default `uv sync` must succeed compiler-free. nauty itself is a brew binary, cannot live in uv.lock. |
| Package layout | src-layout `src/alpha2/` split into generators / invariants / search / verify / repro + `paths.py` | The ENV-02 library/thin-entry cut; networkx confined to invariants/matching.py; the only path lives in paths.py (replaces `/mnt/...`). |
| χ computation | χ = n − ν via `nx.max_weight_matching(maxcardinality=True)` ONLY | CHI-01: Edmonds blossom, integer-exact; no estimate/coloring anywhere in control flow (statically guarded). |
| Determinism contract | single-RNG Contract v1 (`random.Random(seed)` → process → solve) | The stored heuristic model depends on exact RNG consumption order; verbatim bodies preserve set-iteration order. |
| Trust-root boundary | verifier keeps its own `is_conflict`; imports nothing from search | Establishes the "verifier imports nothing from proposers" rule from day one (hardened to no-assert in Phase 2). |
| Golden-fixture strategy | freeze `H_edges` sha256 ONLY after doc-derived invariants pass | Prevents a porting bug from self-certifying as "golden" (research two-tier design). |
| Test runner | pytest 8.x; quick `pytest tests/test_fingerprint.py -x`, full `pytest -q` | ~2s networkx-only feedback; the fingerprint is the drift tripwire. |

## Stack Touched in Phase 1

- [x] Project scaffold — uv project, `.python-version`, committed `uv.lock`, ruff, pytest
- [x] Package/routing analogue — importable `src/alpha2/` package with a runnable `python -m alpha2.repro.baseline` entry
- [x] Data read/write — regenerated certificate JSON written to repo-relative `data/corpus/` via `paths.CORPUS`; golden manifest read from `data/manifests/fingerprint.json`
- [x] "UI" interaction analogue — the CLI baseline entry runs the full pipeline and emits the n=31 seed=1 result line
- [x] Local full-stack run — `uv sync && uv run python -m alpha2.repro.baseline && uv run pytest -q` exercises env → toolkit → fingerprint end-to-end

## Out of Scope (Deferred to Later Slices)

- **Solver execution** — pulp/CBC (seed-137 ILP), ortools/CP-SAT, nauty/pynauty (geng) are locked+installable but NOT exercised in Phase 1 (Phases 3–9).
- **Verifier hardening** — rewriting `verify_model` from asserts to real checks + a `python -O` assert-stripping canary is Phase 2 (VRF-01, ENV-06).
- **Full 296-corpus regeneration + independent re-verification + CI-on-every-commit** — Phase 3 (ENV-04, ENV-06).
- **Certificate schema v1 / Tutte–Berge witnesses / append-only store** — Phase 2 (VRF-02, CHI-02).
- **Reproduction contract (byte-exact vs semantic) + per-record version stamps** — Phase 2 (ENV-05).
- **seed-137 model/had₂=17 (exact ILP)** — only its H-only graph identity (|E(H)|=177) is pre-locked here; the model is Phase 4.
- **nauty brew install as a gate** — documented + skippable only (research Assumption A1).

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: independent stdlib-only verifier (fails closed under `python -O`) + witness-complete certificate schema v1.
- Phase 3: full 296-instance corpus regenerated + independently re-verified; golden manifest frozen; reproduction + verifier run as CI.
- Phase 4: status-honest `ExactBackend` + CBC reference (seed-137 → had₂=17, PROVED_OPTIMAL).
- Phase 5+: CP-SAT, differential gate, had₃; then the kill-battery CLI and the candidate pools.
