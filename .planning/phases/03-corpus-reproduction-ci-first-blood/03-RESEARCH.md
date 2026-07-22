# Phase 3: Corpus Reproduction & CI (First Blood) - Research

**Researched:** 2026-07-22
**Domain:** Deterministic corpus regeneration + certificate re-verification + CI harness (Python reproducibility engineering; no solver, no new deps)
**Confidence:** HIGH

## Summary

Phase 3 turns the trust machinery built in Phases 1–2 into a *live, frozen artifact*: it regenerates all **296** instances (284 triangle-free-process complements n=31–501 + 12 sum-free Cayley p≤151), stores each as a witness-complete schema-v1 certificate, freezes a golden-hash manifest, and wires the whole thing into CI as the permanent regression harness. Every load-bearing component already exists and is adversarially proven — `corpus/verifier.py` (trust root), `corpus/schema.py` (schema-v1 builder + frozen sha256 convention), `corpus/store.py` (append-only atomic store), `invariants/witness.py` (Tutte–Berge extractor), `generators/tfp.py` (deterministic generator). The Phase-3 work is *assembly and freezing*, not discovery. `[VERIFIED: codebase grep + Phase 1/2 VERIFICATION.md]`

The single most important finding that de-risks this phase: **Phase 3 needs no ILP/CBC solver at all.** All 12 Cayley instances resolved by the heuristic (Appendix D.1 rows 16–27 all read `method=heuristic`) `[CITED: reference/alpha2-program-source.md D.1]`, and the one instance that required exact ILP — seed-137 — has its verified K₁₆ model already stored as a literal in Appendix D.3 and already carried in the Phase-2 corpus as the interim 16-set record `[CITED: 02-02-SUMMARY.md]`. The independent verifier re-checks that stored literal model against a regenerated H from the seed alone; no solver runs. CBC/PuLP execution is entirely Phase 4. This means Phase 3's CI can be solver-free and fast.

The second finding the planner must design around: the reference stored **only 27** self-contained certificates; the other **269** sweep instances were verified *in-run* and never persisted `[CITED: reference D-accounting]`. Success Criterion 1 demands "re-verified from stored JSON alone" for all 296, so Phase 3 must **promote the 269 in-run sweep instances into full stored schema-v1 certificates** (regenerate → extract witness → build record → append). Two ported pieces are missing and must be added: `generators/cayley.py` (the `can_add`/`random_maximal_symmetric_sumfree`/`cayley_adj` cluster from Appendix C.3, currently only `tfp.py` exists) and a `corpus/manifest.py` module to freeze the 296-entry golden manifest.

**Primary recommendation:** Build one MVP vertical slice first — regenerate `(31,1)` → `extract_witness` → `schema.build_record` → `store.append_certificate` → recompute manifest hash → R1 re-verify from JSON — then scale that exact path to all 296 (baseline → sweep → showpieces → Cayley → seed-137-literal), freeze the manifest, freeze the four `repro/` drivers, and wire R1/R2/R3 + `python -O` + fingerprint + newer-Python-canary CI jobs. Reuse every existing module verbatim; write no new verification, hashing, or storage logic.

## User Constraints (from CONTEXT.md)

**No CONTEXT.md exists for Phase 3** — `/gsd:discuss-phase` has not been run (`.planning/phases/03-corpus-reproduction-ci-first-blood/` contains no CONTEXT file). The constraints below are therefore derived from the ROADMAP success criteria, REQUIREMENTS (ENV-04, ENV-06), and the locked project-level decisions in STATE.md / PROJECT.md, not from a user discussion. The planner should treat the **Open Questions** and **Assumptions Log** as the items a discuss-phase pass would resolve.

Locked decisions inherited from STATE.md that bound this phase:
- Phases 1→2→3 strictly sequential; nothing downstream starts until 296/296 is green. `[CITED: STATE.md Decisions]`
- Linux x86_64 is the canonical reference-regeneration platform for ILP-method certificates (CI must provide it) — though **Phase 3 runs no ILP**, the designation stays stamped in records for Phase 4. `[CITED: STATE.md Blockers, ENV-05]`
- Interpreter pinned to CPython `3.12.13` exact patch; byte-reproduction depends on CPython set-iteration internals. `[CITED: STATE.md, pyproject.toml, .python-version]`

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-04 | The full 296-instance corpus (284 TFP complements n=31–501, 12 sum-free Cayley p≤151, seed-137) is regenerated and independently re-verified; all 27 stored certificates reproduce. | Regenerate via ported `generators/tfp.py` (exists) + `generators/cayley.py` (must port from C.3); re-verify via `corpus/verifier.verify_certificate` from stored JSON alone; witness via `invariants/witness.extract_witness`; store via `corpus/store.append_certificate`. See Standard Stack, Architecture Patterns, Code Examples. |
| ENV-06 | A test suite + CI run the verifier over the stored corpus on every commit, including a `python -O` job (assert-stripping canary) and the fingerprint test. | GitHub Actions + `astral-sh/setup-uv`; R1 corpus-validity job, R2 determinism panel, R3 replay release gate, `python -O` job (pattern already in `tests/test_verifier_dash_O.py`), fingerprint job (`tests/test_fingerprint.py` exists), newer-Python canary. See Validation Architecture, Code Examples. |
</phase_requirements>

## Architectural Responsibility Map

This project is a trust-topology, not a web app. Tiers are layers of the trust chain; the map assigns each Phase-3 capability to the layer that owns it.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Regenerate H from (n,seed)/(p,seed) | Generator (`generators/tfp`, new `generators/cayley`) | — | Deterministic-in-(n,seed) generation is the generator layer's sole job; RNG injected, never global. |
| Compute ν(H) → χ(G), extract M+U witness | Invariant (`invariants/matching`, `invariants/witness`) | — | networkx blossom is confined here (CHI-01 guard); witness extraction is emission-time UNTRUSTED. |
| Build schema-v1 record + canonical sha256 | Persistence/schema (`corpus/schema`) | — | Frozen sha256 convention + tagged-union provenance already live here; stdlib-only. |
| Re-verify certificate from JSON alone | Trust root (`corpus/verifier`) | — | The independent stdlib-only checker is the *only* thing that confers truth; imports nothing from proposers. |
| Append-only atomic persistence | Persistence (`corpus/store`) | Trust root (verify-at-append) | Store gates every write through the verifier and chains records; crash-safe via os.replace. |
| Freeze golden-hash manifest (296 entries) | Persistence (new `corpus/manifest`) | Generator (regenerates to hash) | Manifest is the R2 determinism anchor; must use the SAME sha256 convention the verifier recomputes. |
| Frozen `repro/` drivers (baseline/sweep/cayley/seed137) | Orchestration (`repro/`) | all proposer layers | The executable *definition* of the 296; frozen forever after Phase 3 — battery must never depend on them. |
| CI jobs (R1/R2/R3, -O, fingerprint, canary) | CI (`.github/workflows/`) | Trust root, Persistence | CI runs the verifier over stored JSON on every commit; the `-O` job protects the assert-free trust boundary. |

## Standard Stack

### Core
No new runtime dependencies. Phase 3 uses only what Phases 1–2 already pinned. `[VERIFIED: pyproject.toml, uv.lock via 01-VERIFICATION.md]`

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CPython | 3.12.13 (exact, uv-managed) | Runtime; byte-reproduction anchor | Set-iteration + `random` internals guard byte-exact regeneration; pinned in `.python-version`. `[VERIFIED: .python-version]` |
| networkx | 3.6.1 | ν(H) via Edmonds blossom (confined to `invariants/`) | Sole χ path; already the corpus's reference. `[VERIFIED: uv.lock]` |
| stdlib (json, hashlib, collections, os, tempfile) | 3.12.13 | Verifier, schema, store, manifest | Trust root is stdlib-only by design. `[VERIFIED: verifier.py/store.py/schema.py imports]` |

### Supporting (test + CI)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (currently unpinned `dev` extra) | R1/R2/R3 + fingerprint + `-O` as the test suite | Always — corpus reproduction *is* the test suite (PROJECT.md). **Recommend pinning** (e.g. `pytest==8.x`) for CI reproducibility. `[VERIFIED: pyproject.toml dev extra]` |
| pytest-xdist | optional, latest | Parallel fan-out of the 296-instance R2 panel / witness extraction | Only if the 296 regeneration + witness extraction (n=501 is ~500 blossom calls) makes the suite slow; not required for MVP. `[ASSUMED]` |
| GitHub Actions | n/a (service) | CI on every commit | ENV-06 mandates CI; ubuntu-latest canonical + optional macOS. `[CITED: ARCHITECTURE.md Integration Points]` |
| `astral-sh/setup-uv` | v6 (pin to a commit SHA) | Install uv + pinned Python in CI, cache deps | Official Astral action; `uv sync --locked` + `uv run --frozen pytest` is the canonical uv-CI pattern. `[CITED: docs.astral.sh/uv/guides/integration/github]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `astral-sh/setup-uv` | `actions/setup-python` + `pip install uv` | Loses lockfile-native `--locked`/`--frozen` guarantees and built-in caching; setup-uv is the reproducibility-first choice. |
| `astral-sh/setup-uv` | `step-security/setup-uv` (hardened drop-in) | Only if a supply-chain-hardening policy is adopted; not required. `[ASSUMED]` |
| Sequential `append_certificate` for the 296 freeze | Batch `build_corpus` (verify-each-once, chain-once, single write) | Sequential reuses the *proven* store but is O(N²) re-verification (~44k verifies for 296); batch is O(N) but is new untested code that bypasses prefix-immutability. Recommend sequential for MVP unless measured too slow. See Pitfall 5. |

**Installation:** none. CI only adds workflow YAML under `.github/workflows/`.

**Version verification:** pytest is currently declared as a bare `dev` extra (`dev = ["pytest", "ruff"]`) with no pin `[VERIFIED: pyproject.toml]`. Recommend pinning pytest to a specific 8.x before freezing CI so the newer-Python canary can't drift the runner silently. No registry lookups are needed for Phase 3 because it installs nothing new to PyPI.

## Package Legitimacy Audit

> Phase 3 installs **no new PyPI packages**. The only new external artifact is a GitHub Actions dependency (`astral-sh/setup-uv`), which is not a package-registry install.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none new) | — | — | — | — | n/a | — |
| `astral-sh/setup-uv` | GitHub Action | mature (Astral, official) | — | github.com/astral-sh/setup-uv | n/a (not PyPI) | Approved — pin to a commit SHA |
| pytest (already declared) | PyPI | 15+ yrs | very high | github.com/pytest-dev/pytest | not run (absent) | Approved — recommend adding a version pin |

**Packages removed due to slopcheck [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

*slopcheck was unavailable at research time (`slopcheck: absent`) and could not be installed (no network-verified install path in this session). This does not gate Phase 3 because no new packages are introduced — the runtime stack is unchanged from the Phase-1 lockfile that was already verified in 01-VERIFICATION.md. Pin the `setup-uv` action to a commit SHA (supply-chain hygiene) rather than a moving tag.*

## Architecture Patterns

### System Architecture Diagram

```
        (n,seed) or (p,seed)                         one-time freeze
              │                                            │
              ▼                                            ▼
   ┌────────────────────┐   adj (list[set])      ┌───────────────────┐
   │ generators/tfp     │───────────────┐        │ corpus/manifest   │
   │ generators/cayley  │               │        │  sha256(H_edges)  │
   │  (deterministic)   │               │        │  per (fam,n|p,s)  │
   └────────────────────┘               │        └─────────┬─────────┘
              │                          ▼                  │ freeze
              │                ┌──────────────────┐         ▼
              │                │ invariants/      │   corpus-v1.manifest.json
              │                │  matching (ν→χ)  │        (committed)
              │                │  witness (M,U)   │
              │                └────────┬─────────┘
              ▼  H_edges                │ M,U,ν,χ
   ┌────────────────────┐   record dict │
   │ search/heuristic   │──── model ───▶├──────────┐
   │ (RNG contract v1)  │               ▼          │
   └────────────────────┘     ┌──────────────────┐ │
   seed-137 model = D.3 ─────▶│ corpus/schema    │ │
   literal (no solver)        │  build_record    │ │
                              └────────┬─────────┘ │
                                       ▼           │
                            ┌──────────────────────▼─────┐
                            │ corpus/store               │
                            │  append_certificate:       │
                            │   verify-at-append (TRUST   │
                            │   ROOT) + hash-chain +      │
                            │   os.replace atomic write   │
                            └────────────┬───────────────┘
                                         ▼
                     data/corpus/hadwiger_alpha2_certificates.json (296)
                                         │
        ┌────────────────────────────────┼───────────────────────────────┐
        ▼ R1 every commit                ▼ R2 every commit                ▼ R3 release
   verify_certificate over          regenerate H, compare           rerun repro/ drivers,
   ALL 296 from JSON alone          sha256 to manifest              assert identical JSON
   (+ python -O job, + fingerprint, + newer-Python canary)
```

The reader can trace the primary use case: an instance's (n,seed) enters the generator, its H flows through invariants (ν/χ + M,U witness) and the heuristic (model), schema assembles a witness-complete record, the store verifies-and-appends it, the manifest freezes its hash, and CI's R1/R2/R3 jobs re-check the result three independent ways on every commit.

### Recommended Project Structure (Phase-3 additions only)
```
src/alpha2/
├── generators/
│   └── cayley.py            # NEW: verbatim port of C.3 can_add / random_maximal_symmetric_sumfree / cayley_adj
├── corpus/
│   └── manifest.py          # NEW: build + freeze 296-entry golden manifest (reuses schema.h_edges_sha256)
├── repro/
│   ├── baseline.py          # FINALIZE: emit schema-v1 via store (RNG contract v1 unchanged), then FROZEN
│   ├── sweep.py             # NEW: 269 sweep + 2 showpieces → full stored certs (not in-run-only), then FROZEN
│   ├── cayley_run.py        # NEW: 12 Cayley → full stored certs (H_edges reconstructed), then FROZEN
│   └── seed137.py           # NEW: carries D.3 K16 model literal, verifies vs regenerated H — NO solver, then FROZEN
data/
├── corpus/hadwiger_alpha2_certificates.json   # regenerated 296, then git-committed (immutability anchor)
└── manifests/corpus-v1.manifest.json          # NEW: 296 golden hashes, committed
.github/workflows/
└── ci.yml                   # NEW: R1 + R2 + fingerprint + python -O (every commit); R3 + full-296 + canary (release/nightly)
tests/
├── test_corpus_r1.py        # NEW: R1 — every stored cert re-verifies from JSON alone
├── test_corpus_r2.py        # NEW: R2 — regenerate panel, sha256 == manifest
└── test_corpus_r3.py        # NEW: R3 — replay slice, identical JSON (marked slow)
```

### Pattern 1: MVP vertical slice — one instance end-to-end, then scale
**What:** Wire the full pipeline for a single instance before touching 296.
**When to use:** First task of the phase (phase is `mvp` mode).
**Example:**
```python
# Source: composed from existing modules (generators/tfp, invariants/*, corpus/*)
import random
from alpha2.generators.tfp import triangle_free_process, is_triangle_free, is_edge_maximal_tf
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.search.heuristic import solve
from alpha2.corpus import schema, store

def build_and_store_tfp(n, seed, path):
    rng = random.Random(seed)                     # RNG contract v1: ONE stream
    adj, m = triangle_free_process(n, rng)        # generator consumes rng first
    assert is_triangle_free(adj, n)
    nu = matching_number(adj, n)
    chi = n - nu
    sets, *_ = solve(adj, n, chi, rng)            # heuristic consumes SAME rng next
    M, U, nu2 = extract_witness(adj, n)           # emission-time witness (untrusted; verifier re-checks)
    H_edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
    rec = schema.build_record(
        provenance=schema.provenance_seed("triangle_free_process_complement", n, seed,
                                           "Bohman uniform triangle-free process"),
        H_edges=H_edges, nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in sets],
        matching_M=M, tutte_berge_U=U, method="heuristic",
        omega_G=None, verified=True,
    )
    store.append_certificate(rec, path=path)      # verify-at-append (trust root) + atomic write
```
Then scale: baseline 12 → sweep 269 → showpieces 2 → Cayley 12 → seed-137 (literal). Same path, different generators.

### Pattern 2: seed-137 as a carried literal (no solver in Phase 3)
**What:** seed-137's verified model is the 16-set (9 pairs + 7 singletons) from Appendix D.3 — produced by the ILP historically, but stored as a fixed literal. Phase 3 regenerates H from `random.Random(137)`, then verifies the *stored* D.3 model against it. `[CITED: reference D.3]`
**When to use:** the seed137 driver.
**Example:**
```python
# Source: Appendix D.3 (reference/alpha2-program-source.md)
SEED137_MODEL = [[2,20],[4,7],[8,18],[9,13],[12,27],[16,22],[17,24],[19,29],[26,28],
                 [0],[1],[3],[10],[11],[21],[23]]   # K16 model; verifier re-checks vs regenerated H
# method string documents the true had_2: "exact ILP (CBC): had_2(G)=17"
# invariants.had_2 is DERIVED as len(model)=16 (the INTERIM value); the true 17-set
# family arrives in Phase 4. Schema already supports k>=chi with no change.
```
This matches the Phase-2 interim record exactly `[CITED: 02-02-SUMMARY.md, 02-VERIFICATION.md Anti-Patterns note]`.

### Pattern 3: Cayley H_edges must be reconstructed and stored inline
**What:** The reference Cayley records stored only `S` and `p`, NOT `H_edges` — non-self-contained (Pitfall 6.5 in project PITFALLS). Schema-v1 requires inline `H_edges` + sha256. The driver reconstructs `adj = cayley_adj(p, S)` and emits full `H_edges`.
**When to use:** cayley_run.py.
**Example:**
```python
# Source: Appendix C.3 (must be ported verbatim into generators/cayley.py first)
S = random_maximal_symmetric_sumfree(p, random.Random(seed))
adj = cayley_adj(p, S)                              # reconstruct adjacency
H_edges = sorted([min(u,v),max(u,v)] for u in range(p) for v in adj[u] if u < v)
# provenance = params-kind: {kind:"params", family:"cayley_maximal_sumfree_Zp",
#              n:p, params:{"S": sorted(S)}, seed:seed}
```
All 12 Cayley resolve by heuristic — no ILP fallback fires. `[VERIFIED: reference D.1 — 12/12 method=heuristic]`

### Pattern 4: Golden-hash manifest uses the frozen verifier convention
**What:** `corpus/manifest.py` builds `{ (family,n|p,seed) → {h_edges_sha256, nu, chi} }` for all 296, using `schema.h_edges_sha256` — the EXACT convention `verifier.verify_model_record` recomputes (`json.dumps(sorted [min,max] pairs, separators=(",",":"))` then sha256). Committing it makes R2 a seconds-fast determinism check.
**When to use:** after all 296 are stored; freeze once, commit forever.
**Note:** the existing `data/manifests/fingerprint.json` (2 entries, ENV-03) is a *separate, smaller* fixture — keep it; add the full `corpus-v1.manifest.json` alongside. Do not overwrite the fingerprint. `[VERIFIED: fingerprint.json contents]`

### Anti-Patterns to Avoid
- **Re-solving seed-137 with CBC in Phase 3:** CBC/PuLP is Phase 4. Carry the D.3 literal. Introducing a solver here breaks the "solver-free CI" property and pulls Phase-4 risk forward.
- **Storing only 27 certificates:** SC1 requires all 296 re-verifiable "from stored JSON alone" — the 269 in-run sweep instances must become full stored certs.
- **Byte-exact search replay as the *only* reproduction notion:** heuristic replay is CPython-set-iteration-sensitive; use the three-level R1/R2/R3 contract (R1 verifies stored witnesses, version-proof). `[CITED: ARCHITECTURE.md Anti-Pattern 2]`
- **Overwriting/editing a stored record to "fix" it:** corpus is append-only + hash-chained; regeneration + re-verification only.
- **`assert`-based checks anywhere in the R1/verify path:** the `python -O` job exists precisely to catch this; the trust root is already assert-free — keep new test/driver code from reintroducing asserts in the verified path.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Certificate verification | A new checker in the repro driver | `corpus/verifier.verify_certificate` | It's the adversarially-proven trust root; any second implementation is a common-mode risk. `[VERIFIED: 02-VERIFICATION.md]` |
| Canonical H_edges hashing | Ad-hoc sha256 in manifest code | `corpus/schema.h_edges_sha256` | Must byte-match what the verifier recomputes; the convention is frozen. |
| Atomic append + immutability | Manual open/write | `corpus/store.append_certificate` | Provides verify-at-append, hash-chain, fsync+os.replace crash-safety already. |
| Tutte–Berge witness (M,U) | Hand-rolled Gallai–Edmonds | `invariants/witness.extract_witness` | Already delegates to the single blossom call site; keeps CHI-01 guard intact. |
| ν(H) / χ(G) | Any coloring/estimate | `invariants/matching.matching_number` (χ=n−ν) | CHI-01 AST guard forbids estimates; blossom confined to `matching.py`. |
| seed-137 optimal family | Re-run ILP | Appendix D.3 literal (carried) | Solver is Phase 4; the D.3 model is verifiable now. |
| `python -O` fail-closed test | New subprocess harness | Extend `tests/test_verifier_dash_O.py` pattern | The subprocess `-O` canary already exists and passes. `[VERIFIED: tests/ listing]` |

**Key insight:** Phase 3 is a *composition and freezing* phase. Every algorithmic and trust primitive it needs was built and proven in Phases 1–2. New code should be limited to: two verbatim ports (`generators/cayley.py`), one manifest builder, four thin repro drivers, three R-tests, and one CI workflow. Any new *verification*, *hashing*, or *storage* logic is a red flag.

## Runtime State Inventory

> Phase 3 is not a rename, but it *migrates what is stored* (27 → 296 certs; interim records; new manifest). This inventory records the state that must be reconciled, not grep-visible file edits.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `data/corpus/hadwiger_alpha2_certificates.json` is currently `.gitkeep`-only (Phase-2 tests wrote to `tmp_path`) — the real corpus is EMPTY. `data/manifests/fingerprint.json` has 2 entries (ENV-03 exemplars). | Regenerate all 296 into the corpus; add `corpus-v1.manifest.json` (296 entries) alongside the untouched fingerprint.json. `[VERIFIED: data/ listing, fingerprint.json]` |
| Interim records | Phase 2 documented a seed-137 *interim* 16-set K16 record (had_2=16) and the "true 17-set family arrives in Phase 4"; that interim was written to `tmp_path` in tests, not the repo corpus. | Phase 3's seed137 driver writes the D.3 16-set literal as the persistent record; keep had_2=16 (derived); method string documents had_2=17. `[CITED: 02-02-SUMMARY.md]` |
| Generator gaps | `generators/cayley.py` does NOT exist — only `generators/tfp.py` was ported in Phase 1. R2 for the 12 Cayley requires it. | Port `can_add`, `random_maximal_symmetric_sumfree`, `cayley_adj` verbatim from Appendix C.3 (add to ruff `extend-exclude` — determinism-sensitive, uses `rng.shuffle`). `[VERIFIED: src tree listing; C.3 uses rng.shuffle]` |
| Driver state | `repro/baseline.py` emits the OLD ad-hoc record format (no witness, no store, no schema-v1) and only 12 instances. | Finalize it to emit schema-v1 via `store.append_certificate` (RNG contract v1 core unchanged), then freeze. `[VERIFIED: baseline.py source]` |
| CI / build artifacts | No `.github/` directory; no CI exists. System Python is 3.9.6 (must never be used); uv-managed 3.12.13 in `.venv`. | Create `.github/workflows/ci.yml`; CI installs 3.12.13 via setup-uv, never touches system Python. `[VERIFIED: find .github → none; sys python 3.9.6]` |

**Nothing found in category (OS-registered state, secrets/env vars):** None — this is a pure code + data-regeneration phase with no OS registrations, no secrets, and no external services. Verified by inspection of the repo and config.json (no service configs, no `.env`).

## Common Pitfalls

### Pitfall 1: The 296 accounting is exact and easy to miscount
**What goes wrong:** Storing the wrong set of instances (e.g. only 27, or double-counting seed-137).
**Why it happens:** The reference stored 27; the other 269 were in-run only.
**The exact decomposition (must total 296):** `[CITED: reference D-accounting + C.1/C.2/C.3 drivers]`
- **284 TFP** = baseline 12 `[(31,1),(31,2),(31,3),(32,4),(51,5),(51,6),(76,7),(101,8),(101,9),(151,10),(200,11),(201,12)]` + showpieces 2 `[(301,13),(501,14)]` + seed-137 1 `[(31,137)]` + sweep 269 `[n=31 s100–299 = 200 minus seed137 = 199; n=51 s100–149 = 50; n=101 s100–119 = 20]` (199+50+20 = 269; 15+269 = 284).
- **12 Cayley** = `p∈{31,53,101,151}` × `seed=5000+10p+k, k∈{0,1,2}` → 31:{5310,5311,5312}, 53:{5530,5531,5532}, 101:{6010,6011,6012}, 151:{6510,6511,6512}.
**How to avoid:** Encode these instance lists as data in the drivers; assert `len(corpus)==296` after the freeze; a per-family count test (284 TFP + 12 Cayley) in R1.
**Warning signs:** corpus length ≠ 296; seed-137 appearing twice (once in sweep range 100–299, once as the exact study) — it is stored ONCE, as the exact-study record, and EXCLUDED from the sweep loop.

### Pitfall 2: Cayley records not self-contained
**What goes wrong:** Storing `S`/`p` without `H_edges` (as the reference did) makes the certificate unverifiable without re-running `cayley_adj` — violating "verify from stored JSON alone."
**How to avoid:** Reconstruct `adj = cayley_adj(p, S)` in the driver and store full canonical `H_edges` inline (Pattern 3). Provenance is `params`-kind with `params={"S": sorted(S)}` for regeneration + `seed` for R2. `[CITED: project PITFALLS Pitfall 6.5]`
**Warning signs:** a Cayley record whose `H_edges` is absent/empty; verifier `_build_adj` raising on it.

### Pitfall 3: RNG contract v1 must stay byte-exact (single shared stream)
**What goes wrong:** Introducing per-stage subseeds, or reordering generator-vs-heuristic RNG consumption, shifts the search stream and flips heuristic models — breaking byte-equality to Appendix D.
**Why it happens:** Contract v2 (derived subseeds) is the *future* convention; the 296 legacy corpus depends on v1 (one `random.Random(seed)` feeds `triangle_free_process` THEN `solve`). `[CITED: ARCHITECTURE.md Pattern 3; baseline.py docstring]`
**How to avoid:** Preserve the exact `run_instance` RNG order in all repro drivers; keep `tfp.py` and `heuristic.py` in ruff `extend-exclude` (already done); add `cayley.py` to it too. R3 (full replay on pinned CPython) is the guard.
**Warning signs:** seed-1 or seed-137 stored model differing from Appendix D.2/D.3; fingerprint test (131/15/16) flipping.

### Pitfall 4: Reproduction must be defined as R1 (witness re-verify), not search replay
**What goes wrong:** Treating "rerun the driver and diff the JSON" as the only reproduction, which is CPython-set-iteration-sensitive and would look "broken" on any interpreter bump even though every certificate stays valid.
**How to avoid:** Three-level contract — **R1** (regenerate H OR read inline `H_edges`, hash-check vs manifest, run `verify_certificate` on the STORED model — version-proof, every commit), **R2** (regenerate H from seed, compare sha256 to manifest — seconds), **R3** (full driver replay on pinned 3.12.13 — release gate only). `[CITED: ARCHITECTURE.md Reproduction Contract]`
**Warning signs:** R1 requiring the search to be re-run; CI failing on a Python patch bump for a reason other than a genuine hash mismatch.

### Pitfall 5: Bulk-loading 296 via `append_certificate` is O(N²)
**What goes wrong:** `append_certificate` re-verifies EVERY prior record on each append (append i does i verifications) and recomputes the full hash-chain — ~44k `verify_certificate` calls for 296, each bounded by the largest model (n=501 → 251 branch sets → ~31k pairwise checks + a 501-node BFS). Plus witness extraction at n=301/501 is ~300–500 blossom calls per instance. Total could be minutes.
**Why it happens:** The store is designed for incremental single-kill appends in the battery, not one-shot bulk load.
**How to avoid:** For MVP, accept sequential `append_certificate` (correctness over speed; likely low-minutes, tolerable one-time). If measured too slow: (a) parallelize witness extraction with pytest-xdist / a pre-pass, and/or (b) add a tested `build_corpus` batch path that verifies each record once, computes the chain once, and does a single atomic write — but this is new code that must be independently tested against the sequential result (same bytes). Do NOT weaken the verify-at-append guarantee to gain speed.
**Warning signs:** the freeze step taking many minutes; CI R3 timing out.

### Pitfall 6: `python -O` strips asserts in NEW driver/test code
**What goes wrong:** The trust root is assert-free, but new repro drivers or R-tests may add `assert` in a path that runs under the `-O` CI job, silently becoming a no-op.
**How to avoid:** Keep asserts out of any code the `-O` job executes; the R1 verification path routes only through `verify_certificate` (raise-based). The existing `tests/test_verifier_dash_O.py` subprocess pattern is the template for the `-O` job. `[VERIFIED: verifier.py is raise-based; test_verifier_dash_O.py exists]`
**Warning signs:** an R-test that passes under `python` but is vacuous under `python -O`.

### Pitfall 7: networkx matching dict-vs-set semantic drift
**What goes wrong:** `len(max_weight_matching(...))` meant 2ν (dict) in networkx 2.0 and ν (set) since 2.2 — a silent factor-2 on ν → χ.
**How to avoid:** networkx is pinned to 3.6.1 (set semantics); `matching_number` already wraps it. Add/keep runtime guards where witnesses are built: `2*len(M) <= n` and `chi >= ceil(n/2)`. `[CITED: project PITFALLS Pitfall 6.3, Integration Gotchas]`
**Warning signs:** χ values ≈ n/2 collapsing toward 0 after any env change.

## Code Examples

### R1 — every stored certificate re-verifies from JSON alone (the corpus-validity test)
```python
# Source: composed from corpus/verifier (trust root) + store layout
import json
from alpha2 import paths
from alpha2.corpus.verifier import verify_certificate, VerificationError

def test_r1_all_296_reverify():
    records = json.load(open(paths.CORPUS))
    assert len(records) == 296
    tfp = sum(1 for r in records if r["provenance"]["family"] == "triangle_free_process_complement")
    cay = sum(1 for r in records if r["provenance"]["family"] == "cayley_maximal_sumfree_Zp")
    assert (tfp, cay) == (284, 12)
    for i, rec in enumerate(records):
        k = verify_certificate(rec)          # raises VerificationError on any violation
        assert k >= rec["invariants"]["chi_G"]
```

### R2 — generator determinism panel (regenerate → hash → compare to manifest)
```python
# Source: corpus/schema.h_edges_sha256 (frozen convention) + generators
import json, random
from alpha2.generators.tfp import triangle_free_process
from alpha2.corpus.schema import h_edges_sha256

def regen_tfp_hash(n, seed):
    adj, _ = triangle_free_process(n, random.Random(seed))
    H_edges = [[min(u,v),max(u,v)] for u in range(n) for v in adj[u] if u < v]
    return h_edges_sha256(H_edges)

def test_r2_manifest_determinism():
    manifest = json.load(open("data/manifests/corpus-v1.manifest.json"))
    # per-commit: a slice; nightly: all 296
    assert regen_tfp_hash(31, 1) == manifest["tfp:n31:s1"]["h_edges_sha256"]
```

### CI workflow (R1/R2/fingerprint/-O every commit; R3/full-296/canary on schedule)
```yaml
# Source: docs.astral.sh/uv/guides/integration/github (setup-uv + uv sync --locked)
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest          # Linux x86_64 = canonical reference platform
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6  # pin to a commit SHA in the real file
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"
      - run: uv sync --locked --extra dev
      - name: R1 + R2 + fingerprint (verifier over stored corpus)
        run: uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q
      - name: python -O assert-stripping canary
        run: uv run --frozen python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py -q
  canary:
    runs-on: ubuntu-latest          # newer-Python drift canary (informational)
    continue-on-error: true         # catches random/set-order drift ON PURPOSE
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with: { python-version: "3.13" }
      - run: uv run pytest tests/test_corpus_r2.py tests/test_fingerprint.py -q
```
*R3 (full `repro/` replay asserting identical corpus JSON) and the full-296 R2 panel run as a separate release/nightly job — slow, pinned to 3.12.13.*

## Common Pitfalls → covered above (see Common Pitfalls section).

## State of the Art

| Old Approach (reference) | Current Approach (Phase 3) | When Changed | Impact |
|--------------------------|----------------------------|--------------|--------|
| 27 self-contained certs; 269 in-run only | All 296 stored as schema-v1 certs | Phase 3 | R1 re-verifies all 296 "from JSON alone" (SC1). |
| Cayley records store `S`, not `H_edges` | Cayley reconstructs + stores inline `H_edges` | Phase 3 | Self-contained; verifiable without re-running `cayley_adj`. |
| seed-137 via live ILP (`fam[:chi]`) | seed-137 carried D.3 literal; ILP deferred | Phase 3 | Solver-free phase; true 17-set family → Phase 4. |
| `verify_model` assert-based, shared `is_conflict` | independent raise-based `verify_certificate` | Phase 2 (used here) | `-O`-safe trust root; Phase 3 just consumes it. |
| No CI | GitHub Actions R1/R2/R3 + `-O` + canary | Phase 3 | Every commit re-runs the trust root over the corpus. |

**Deprecated/outdated:**
- The reference `sweep.py` "verify in-run, don't store" pattern — replaced by full storage.
- `data/manifests/fingerprint.json` is NOT deprecated — it stays as the ENV-03 exemplar fixture; the new `corpus-v1.manifest.json` is additive.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | All 296 should become full stored schema-v1 certificates (not 27 stored + 269 regenerate-only) | Summary, Pitfall 1 | If the intent is "27 stored + 269 regenerate-and-verify-live," the storage/R1 design changes substantially. This is the top discuss-phase question. |
| A2 | seed-137 is stored as the Appendix D.3 16-set literal (had_2=16 interim), solver deferred to Phase 4 | Pattern 2 | If SC1's "seed-137 included" is read as requiring the true 17-set had_2 family now, Phase 3 would need CBC (Phase-4 scope) — contradicting the roadmap's phase split. |
| A3 | pytest-xdist / batch build only if sequential freeze is measured too slow | Standard Stack, Pitfall 5 | If the 296 freeze is unacceptably slow, a tested batch-append path is needed (new code). |
| A4 | CI on ubuntu-latest is sufficient; macOS matrix optional (Phase 3 is solver-free, no Rosetta CBC concern) | Validation Architecture, Code Examples | If a macOS reproduction guarantee is required now, add a macOS matrix leg. |
| A5 | Manifest key scheme extends the existing `fam:nNN:sSS` style (e.g. `tfp:n31:s1`, `cayley:p31:s5310`) | Pattern 4 | Cosmetic; a different key scheme just changes test lookups. |
| A6 | pytest should be version-pinned before freezing CI | Standard Stack | If left unpinned, the newer-Python canary and R3 could drift on a pytest release. |

**If this table is non-empty:** A1 and A2 are the load-bearing assumptions a `/gsd:discuss-phase` pass (or planner confirmation) should lock before execution.

## Open Questions

1. **Do all 296 become stored full certificates, or 27 stored + 269 regenerate-and-verify-live?**
   - What we know: SC1 says "re-verified from stored JSON alone" for all 296; the reference stored only 27.
   - What's unclear: whether "stored JSON" means a 296-record corpus or a 27-record corpus + a manifest that drives live regeneration of the 269.
   - Recommendation: store all 296 (A1) — it is the strongest reading of SC1, makes R1 a pure JSON re-verify, and the append-only store already supports it. Confirm with the author/planner.

2. **seed-137: carried D.3 literal (16-set) vs re-solved 17-set now?**
   - What we know: the roadmap puts CBC in Phase 4; Phase 2 stored the 16-set interim; Appendix D.3 shows a verifiable 16-set model.
   - What's unclear: whether SC1 "seed-137 included" is satisfied by the 16-set interim (it is a valid K₁₆ model) or demands the 17-set had_2 family.
   - Recommendation: carry the D.3 16-set literal (A2), keep Phase 3 solver-free; Phase 4 drops in the 17-set family with no schema change.

3. **Sequential `append_certificate` vs a batch builder for the 296 freeze?**
   - What we know: the store is O(N²) on bulk load; witness extraction at n=501 is heavy.
   - Recommendation: measure the MVP sequential path first; only add a tested batch path if it's too slow (A3). Never weaken verify-at-append.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv-managed CPython 3.12.13 | All regeneration + tests | ✓ (in `.venv`; uv not on PATH in this shell) | 3.12.13 | — |
| networkx 3.6.1 | ν(H) / witness | ✓ | 3.6.1 | — |
| pytest | R1/R2/R3 + `-O` + fingerprint | ✓ (`.venv/bin/pytest`) | unpinned dev extra | pin before CI freeze |
| git | Corpus immutability anchor (commit) | ✓ | 2.50.1 | — |
| GitHub Actions | CI on every commit (ENV-06) | ✓ (service) | — | any CI that runs uv would work |
| CBC / PuLP / ortools | NOT needed in Phase 3 | ✓ (installed) but unused | — | seed-137 model carried as literal → Phase 4 uses them |
| nauty / geng | NOT needed in Phase 3 | ✗ (`which geng` fails) | — | not used until Phase 7 (P0) |

**Missing dependencies with no fallback:** none — every Phase-3 dependency is present.
**Missing dependencies with fallback:** nauty/CBC are absent-or-unused but not required by Phase 3; both are future-phase concerns.

## Validation Architecture

> nyquist_validation is enabled (`workflow.nyquist_validation: true` in config.json). `[VERIFIED: .planning/config.json]`

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (currently unpinned `dev` extra; recommend `pytest==8.x`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["src"]`) |
| Quick run command | `uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q` |
| Full suite command | `uv run --frozen pytest -q` (adds R3 replay slice + existing 42 Phase-1/2 tests) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-04 | All 296 stored + `verify_certificate` passes from JSON alone; counts 284/12 | R1 (integration) | `pytest tests/test_corpus_r1.py -q` | ❌ Wave 0 |
| ENV-04 | seed-1 & seed-137 models byte-equal to Appendix D.2/D.3 | unit | `pytest tests/test_corpus_r1.py::test_golden_models -q` | ❌ Wave 0 (D.2 exemplar partly covered by existing `test_fingerprint.py`) |
| ENV-04 | Regenerated H_edges sha256 == manifest (296 panel) | R2 (determinism) | `pytest tests/test_corpus_r2.py -q` | ❌ Wave 0 |
| ENV-04 | Every record carries a valid Tutte–Berge witness (M,U) | unit (via verify_chi_witness in R1) | `pytest tests/test_corpus_r1.py -q` | ❌ Wave 0 |
| ENV-06 | Verifier runs over stored corpus on every commit | CI (R1) | GitHub Actions `test` job | ❌ Wave 0 |
| ENV-06 | `python -O` assert-stripping canary green | CI (`-O`) | `python -O -m pytest tests/test_verifier_dash_O.py tests/test_corpus_r1.py` | ⚠️ `test_verifier_dash_O.py` exists; extend to corpus |
| ENV-06 | Fingerprint invariants (131/15/16) hold | unit | `pytest tests/test_fingerprint.py -q` | ✅ exists |
| SC3 | R3 full pipeline replay = identical corpus JSON | slow (release gate) | `pytest tests/test_corpus_r3.py -q -m slow` | ❌ Wave 0 |
| SC3 | newer-Python canary catches drift on purpose | CI (informational) | canary job (continue-on-error) on 3.13 | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run --frozen pytest tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_fingerprint.py -q` (verifier over stored corpus + determinism slice).
- **Per wave merge:** `uv run --frozen pytest -q` (full suite incl. Phase-1/2 42 tests + `-O` job).
- **Phase gate:** full suite green + R3 replay green + `len(corpus)==296` + manifest committed, before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `generators/cayley.py` — verbatim C.3 port (blocks R2 for the 12 Cayley) — add to ruff `extend-exclude`.
- [ ] `corpus/manifest.py` — 296-entry golden manifest builder (uses `schema.h_edges_sha256`).
- [ ] `repro/sweep.py`, `repro/cayley_run.py`, `repro/seed137.py` — new drivers emitting schema-v1 via the store; `repro/baseline.py` finalized to schema-v1.
- [ ] `tests/test_corpus_r1.py` — R1 corpus-validity (covers ENV-04 + witness).
- [ ] `tests/test_corpus_r2.py` — R2 determinism panel (covers regeneration + manifest).
- [ ] `tests/test_corpus_r3.py` — R3 replay slice (marked `slow`).
- [ ] `.github/workflows/ci.yml` — R1/R2/fingerprint/-O every commit; R3/full-296/canary scheduled.
- [ ] Register a `slow` pytest marker (add to `[tool.pytest.ini_options]` markers) for R3.
- [ ] Pin pytest version in the `dev` extra before freezing CI.

## Security Domain

> `security_enforcement` is not set in config.json (absent = enabled); this is a computational-research harness with no auth/network/user-input surface, so classical web ASVS categories are largely N/A. The domain's real "security" is **epistemic integrity + supply-chain + artifact integrity**, which the existing trust machinery already addresses.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No users/sessions. |
| V3 Session Management | no | N/A. |
| V4 Access Control | no | Local artifacts only. |
| V5 Input Validation | yes | Verifier `_build_adj` + `verify_certificate` validate all stored JSON structurally (range-checked vertices, sha256 integrity, no `assert`). Any ingested `H_edges`/model is untrusted input re-checked from scratch. `[VERIFIED: verifier.py]` |
| V6 Cryptography (integrity, not secrecy) | yes | sha256 canonical H_edges hashing + per-record hash-chain in the store; **never hand-rolled** — reuse `schema.h_edges_sha256` / `schema.chain_hash`. `[VERIFIED: schema.py, store.py]` |
| Supply chain (SLSA-adjacent) | yes | Pin `astral-sh/setup-uv` to a commit SHA; `uv sync --locked` / `uv run --frozen`; corpus + manifest committed to git as the wholesale-rewrite immutability anchor. `[CITED: store.py docstring — git is the external anchor]` |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Silent corpus record tampering | Tampering | Append-only store + per-record hash-chain + verify-at-append; R1 re-verifies from JSON every commit. |
| `python -O` strips assert-based checks → trust root becomes no-op | Elevation/Repudiation | Assert-free raise-based verifier + dedicated `-O` CI job (already proven in Phase 2). |
| Environment/interpreter drift changes regenerated bytes | Tampering (accidental) | Pinned 3.12.13 + golden manifest (R2) + newer-Python canary that fails *on purpose*. |
| Malicious/typo'd CI action version | Tampering (supply chain) | Pin actions to commit SHAs; no `npx`/auto-download of unverified tools. |
| Non-self-contained cert (Cayley) forces trusting a reconstruction routine | Spoofing | Store inline `H_edges` + sha256 so the verifier trusts only stored bytes. |

## Sources

### Primary (HIGH confidence)
- `.planning/reference/alpha2-program-source.md` — Appendix C.1/C.2/C.3/C.4 (drivers), Appendix D (296 accounting, D.1 stored table, D.2 seed-1 model, D.3 seed-137 model), Appendix E §4 runbook. `[CITED]`
- `src/alpha2/corpus/{verifier,schema,store}.py`, `src/alpha2/invariants/{matching,witness}.py`, `src/alpha2/generators/tfp.py`, `src/alpha2/repro/baseline.py` — read directly. `[VERIFIED: file reads]`
- `.planning/phases/01-.../01-VERIFICATION.md`, `.planning/phases/02-.../02-01-SUMMARY.md`, `02-02-SUMMARY.md`, `02-VERIFICATION.md` — what Phases 1/2 delivered. `[CITED]`
- `.planning/research/{SUMMARY,ARCHITECTURE,PITFALLS,STACK}.md` — project-level research (R1/R2/R3 contract, reproduction anatomy, pitfalls). `[CITED]`
- `pyproject.toml`, `.python-version`, `data/manifests/fingerprint.json`, `.planning/config.json` — read directly. `[VERIFIED]`

### Secondary (MEDIUM confidence)
- [Using uv in GitHub Actions — Astral Docs](https://docs.astral.sh/uv/guides/integration/github/) — `setup-uv` + `uv sync --locked` + `uv run --frozen pytest` canonical pattern. `[CITED]`
- [astral-sh/setup-uv (GitHub)](https://github.com/astral-sh/setup-uv) — action inputs (enable-cache, cache-dependency-glob, python-version). `[CITED]`

### Tertiary (LOW confidence — flagged)
- [step-security/setup-uv](https://github.com/step-security/setup-uv) — hardened drop-in alternative (only if a supply-chain policy is adopted). `[ASSUMED]`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; everything verified against the committed lockfile and file reads.
- Architecture (R1/R2/R3, repro/ drivers, manifest): HIGH — derived from existing code + project ARCHITECTURE.md; the assembly path is fully specified.
- Corpus accounting (296 decomposition): HIGH — computed directly from the reference driver instance lists and D-accounting (verified to total 296).
- seed-137 / solver-free property: HIGH — D.1 shows 12/12 Cayley heuristic; D.3 model is a verifiable K₁₆ literal; CBC is Phase 4.
- CI specifics (exact action versions/pins): MEDIUM — pin `setup-uv` to a current SHA at implementation time; pytest version to be pinned.
- Open design questions (A1 all-296-stored, A2 seed-137 literal): MEDIUM — strong recommendation, but a discuss-phase/author confirmation should lock them.

**Research date:** 2026-07-22
**Valid until:** ~2026-08-21 (stable; internal-code-driven — the only external volatility is the `setup-uv` action version, pinned at implementation).
