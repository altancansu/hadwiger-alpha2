# Phase 2: Trust Root & Corpus Schema - Research

**Researched:** 2026-07-21
**Domain:** Independent stdlib-only verifier design · witness-complete certificate schema · Tutte–Berge witness extraction · append-only atomic store · reproduction contract
**Confidence:** HIGH (crux claims verified by live execution on the pinned interpreter this session)

---

<user_constraints>
## User Constraints

No `CONTEXT.md` exists for Phase 2 (`/gsd:discuss-phase` was not run). Per the Phase-1 precedent, constraints are taken from the authoritative in-repo sources and treated with **locked-decision authority**: **CLAUDE.md** (stack, "What NOT to use", the Asymmetry Principle, reporting discipline), the **Phase 2 success criteria** in `ROADMAP.md`, the requirement text of **VRF-01/VRF-02/CHI-02/ENV-05**, and the byte-exact facts in `.planning/reference/alpha2-program-source.md` (Appendix C code semantics, Appendix D exemplars, Appendix E §4.6 verification contract). If the planner wants user sign-off on any `[ASSUMED]` item (see Assumptions Log), route it through discuss-phase before locking.

### Locked Decisions (from CLAUDE.md + ROADMAP + requirements)
- **Stack is frozen.** CPython 3.12.13 (exact), networkx 3.6.1, `pulp==3.3.2` hard-pin, ortools 9.15.6755. Phase 2 adds **no new third-party dependency** — the verifier and store are **stdlib-only**.
- **The independent verifier is the trust root.** It must (a) be stdlib-only, (b) carry its **own** `is_conflict`, (c) import **nothing** from generator/search/solver/invariants code, (d) consume **stored JSON only** (never a live adjacency object handed in by the toolkit), (e) use **real checks that RAISE** — **zero `assert`** — so it is correct under `python -O`.
- **The verbatim `verify/model.py` stays.** Phase 2 *adds* an independent hardened verifier; it does **not** replace or edit the byte-verbatim assert-based `verify_model` (that module is the reproduction anchor for Phase 1's fingerprint and is excluded from reformatting).
- **Full optimal family, never `fam[:χ]`.** The stored `model_branch_sets` is the complete had₂-optimal family; for `had₂ > χ` (seed-137's k=17) the family has **more** than χ sets and must never be truncated.
- **Corpus is append-only + immutable.** Existing records are never edited; instance status (KILLED/SHC-CANDIDATE/RESISTANT) is a **derived view** (VRF-03, Phase 6), never a stored-record mutation.
- **Linux x86_64 is the canonical reference-regeneration platform** (CLAUDE.md Version Compatibility: bundled CBC runs under Rosetta 2 / x86_64 on Apple Silicon).
- **Determinism / "nothing rests on memory."** Everything rebuildable from seeds/params/graph6 + code; canonical `H_edges` sha256 convention is frozen from Phase 1.
- **What NOT to use** (CLAUDE.md): no WL-hash for identity; no SciPy/Blossom V/NetworKit for matching; solver-found models are never trusted as-is — the independent verifier rules on every model.

### Claude's Discretion
- Module layout/naming of the new verifier and store; exact `VerificationError` taxonomy; whether the corpus substrate is a single JSON array (rewrite-with-atomic-replace) or JSON Lines (this doc recommends **JSON array + atomic replace + append-only prefix guard** — see Pattern 4); the precise U-extraction algorithm (probing vs. alternating-forest) so long as verification stays general and untrusting.

### Deferred Ideas (OUT OF SCOPE for Phase 2)
- Size-3 branch-set (had₃) verification — **Phase 5** (verifier extended to triples there).
- The derived status view / results log (VRF-03, CLI-02) — **Phase 6**.
- Regenerating the 296 / freezing the golden manifest / wiring CI incl. the `-O` job over the *full* corpus — **Phase 3** (ENV-04, ENV-06). Phase 2 builds and unit-proves the machinery; Phase 3 runs it at corpus scale.
- The actual 17-set seed-137 family (needs CBC ILP) — **Phase 4**. Phase 2's schema must *support* k≥χ, but round-trips only the models it already has (D.2, D.3).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **VRF-01** | Independent verifier (own stdlib code path, shares no logic with searchers) checks disjointness, valid sizes, pairs/triples inducing connected G-subgraphs, all C(χ,2) cross-adjacencies — **real checks, not `assert`** (correct under `python -O`). | Pattern 1 (verifier design) + Pattern 2 (assert→raise, empirically demonstrated) + Code Examples §1–2 + Validation §-O canary. |
| **VRF-02** | Nothing enters unverified; append-only corpus stores full certificates (provenance, invariants ν/χ/ω, Tutte–Berge witness, **FULL** family, verified flag, method, backend statuses+versions). | Pattern 3 (schema v1) + Pattern 4 (append-only atomic store) + Code Examples §5–6. |
| **CHI-02** | Each cert stores maximum matching M + Tutte–Berge witness set U making χ = n − ν hand-checkable without trusting the matching library. | Pattern 5 (Tutte–Berge recipe, **verified on seed 1 & 137**) + Code Examples §3–4 + Validation §hand-check. |
| **ENV-05** | Reproduction contract distinguishes byte-exact (heuristic/seed) vs semantic (exact-method); records solver/platform versions per cert; Linux x86_64 canonical. | Pattern 6 (reproduction contract) + schema `reproduction`/`backends` blocks. |
</phase_requirements>

---

## Summary

Phase 2 builds the **trust root** — the one piece of code the whole program's epistemic integrity rests on — and the **witness-complete schema** every future certificate is written in. It is deliberately small, stdlib-only, and adversarially proven *before any record is written*. There is **no third-party stack decision** to make here: CLAUDE.md locks the stack, and the verifier is forbidden from importing any of it. The research effort therefore went into (a) the exact hardened design of the verifier, (b) a concrete, verified Tutte–Berge witness recipe, and (c) the schema/store mechanics — all confirmed by live execution on the pinned CPython 3.12.13 + networkx 3.6.1 this session.

Two load-bearing claims were **verified by execution, not reasoned about**:

1. **The `python -O` vulnerability is real and the fix is exactly assert→raise.** Under `python -O`, `assert x>0` on bad input silently returns `True` (the current `verify/model.py` becomes a rubber stamp); an explicit `if not cond: raise ...` still rejects. Demonstrated live this session. This is precisely WR-01 from the Phase-1 review, and VRF-01 is its fix.
2. **The Tutte–Berge witness for this corpus is trivially hand-checkable and the extraction recipe works.** For n=31 seeds 1 and 137: ν=15, and the witness set **U = ∅** with `odd_components(H − U) = 1`, giving the upper bound ν ≤ (n − 1 + |U|)/2 = 15, which the 15-edge matching M meets from below — pinning χ = n − ν = 16 in both directions. This holds because gate condition **G3 makes H factor-critical** (odd, connected, H−v perfectly matchable ∀v), so U is empty for every gate-passing candidate. The verifier must nonetheless implement the **general** odd-component check (never hardcode U=∅) so it is correct for even-n (n=32) and any future family with deficiency > parity.

**Primary recommendation:** Add `src/alpha2/corpus/verifier.py` (stdlib-only, own `is_conflict`, builds its own adjacency from stored `H_edges`, raises `VerificationError`, verifies model + Tutte–Berge witness), `src/alpha2/corpus/schema.py` (schema v1 dataclass/dict + validation + canonical serialization reusing the frozen sha256 convention), and `src/alpha2/corpus/store.py` (append-only, `tempfile`+`os.replace` atomic write, prefix-immutability guard). Prove it with a mutant suite + a real `-O` subprocess CI test + a Tutte–Berge hand-check test, all runnable in Phase 2 before Phase 3 runs it at corpus scale.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Verify a stored model (VRF-01) | **Verifier (stdlib-only, isolated)** | — | Trust root; imports nothing; builds its own H-adjacency from stored `H_edges`; raises. |
| Verify χ = n−ν via M+U (CHI-02) | **Verifier (stdlib-only)** | — | Odd-component count + matching validity are pure graph traversal; no networkx in the *check*. |
| Compute ν(H) oracle (for emission) | Invariants (`matching.py`, networkx) | — | networkx confined to emission time; **never** trusted by the verifier. |
| Extract witness U (for emission) | Emission helper (may use networkx) | Verifier re-checks | Extraction is **untrusted**; a wrong U simply fails the verifier's equality check. |
| Certificate schema v1 (VRF-02) | **Schema module (stdlib)** | Verifier (gates writes) | Field list + canonical serialization; verified flag set only after verifier passes. |
| Append-only atomic store (VRF-02) | **Store module (stdlib `os`/`tempfile`/`json`)** | — | `os.replace` atomicity + prefix-immutability guard; no external deps. |
| Reproduction/version stamping (ENV-05) | Schema `reproduction`+`backends` blocks | Store | Captured at emission; Linux x86_64 flagged canonical. |

**Sanity note for the planner:** the verifier tier must have a *zero-edge* dependency graph into `generators/`, `search/`, `invariants/`, and any solver module. A plan task should include a static import-boundary test (grep/AST) proving `corpus/verifier.py` imports only stdlib.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib only (`json`, `hashlib`, `os`, `tempfile`, `sys`, `platform`, `dataclasses`, `collections`) | 3.12.13 | The verifier, schema, and store | VRF-01 **mandates** stdlib-only for the trust root; determinism; zero supply-chain surface. `[VERIFIED: live import this session]` |

### Supporting (emission-time only — NOT imported by the verifier)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| networkx | 3.6.1 | ν(H) oracle + candidate U extraction at **certificate emission** | Only in emission helpers (`invariants/matching.py` and a new emission helper); the verifier re-derives everything from stored JSON. `[VERIFIED: installed, 3.6.1]` |
| pytest | 8.x | Mutant suite, `-O` canary, round-trip, hand-check tests | Always. |
| hypothesis | latest | Property tests (verifier rejects random mutations) | Optional, high-value — the verifier is the trust root (CLAUDE.md lists it for exactly this). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Own odd-component BFS in verifier | `networkx.connected_components` | **Rejected** — verifier must be stdlib-only; a ~10-line stdlib BFS keeps the trust boundary clean. |
| JSON array + atomic replace | JSON Lines (`O_APPEND`) | JSONL is naturally append-only, but single-write atomicity only holds below `PIPE_BUF`; full certs (n=501 `H_edges`) far exceed it → torn writes. Array + `os.replace` + prefix guard is safer (Pattern 4). |
| Probing U extraction | Alternating-forest (blossom) extraction | Probing (`ν(H−v)==ν`) is simple and robust but O(n) matchings; forest extraction is faster but re-implements Edmonds. Extraction is untrusted either way — recommend probing as reference, forest as optional optimization. |

**Installation:** none — no new packages. (Phase 1's `uv.lock` already provides everything.)

**Version verification (this session):**
```
.venv/bin/python -c "import networkx; print(networkx.__version__)"  # -> 3.6.1  [VERIFIED]
```

## Package Legitimacy Audit

**No external packages are installed in this phase.** The verifier, schema, and store are Python-stdlib-only; networkx/pytest/hypothesis are already pinned by Phase 1's lockfile. Nothing to slopcheck.

| Package | Registry | Disposition |
|---------|----------|-------------|
| (none — stdlib only) | — | N/A |

**Packages removed due to slopcheck [SLOP]:** none. **Flagged [SUS]:** none.

---

## Architecture Patterns

### System Architecture Diagram

```
                        EMISSION TIME (trusted toolkit)                    │  VERIFICATION TIME (trust root)
                                                                           │
 (n, seed | params | graph6)                                               │
        │                                                                  │
        ▼                                                                  │
  generators/*  ──►  adj (H)  ──►  matching.py: ν(H) via networkx  ──┐     │
        │                          │                                 │     │
        │                          ├─► χ = n − ν                     │     │
        │                          ├─► M = max_weight_matching       │     │
        │                          └─► U = extract_witness(adj,n,ν)  │     │   ┌───────────────────────────────┐
        ▼                                (UNTRUSTED helper)          │     │   │ corpus/verifier.py (stdlib)   │
  search/ | solver ──► model_branch_sets (FULL had₂ family, k≥χ)     │     │   │  builds OWN adj from H_edges  │
        │                                                            │     │   │  own is_conflict              │
        ▼                                                            ▼     │   │  verify_model_record():       │
  schema.py: assemble record ──────────────────────────────────► RECORD ──┼──►│   disjoint/size/G-edge/       │
   {provenance, H_edges, sha256, invariants, model, M, U,                  │   │   all C(k,2) cross-adj  RAISE  │
    method, reproduction, backends}                                        │   │  verify_chi_witness():        │
        │                                                                  │   │   |M|=ν, M⊆H, matching;       │
        │  verified = verifier.verify(record)  ◄────────────────────────── ┼── │   odd_comps(H−U); ub==|M|     │
        ▼  (write ONLY if verified)                                        │   └───────────────────────────────┘
  store.py: load ─► assert prefix immutable ─► append ─► tmp+os.replace    │            (imports: json,hashlib,
        │                                                                  │             os,sys,collections ONLY)
        ▼                                                                  │
  data/corpus/hadwiger_alpha2_certificates.json  (append-only, atomic)     │
```

The data flow crux: the verifier's input is **only the serialized record** (right of the `┼`). It reconstructs H's adjacency from `H_edges` and re-derives conflict/adjacency itself. The emission-side ν/M/U (left) are conveniences the verifier **re-checks and never trusts** — a corrupted M or wrong U fails the verifier's own inequality.

### Recommended Project Structure
```
src/alpha2/
├── verify/
│   └── model.py          # UNCHANGED: verbatim assert-based verify_model (P1 anchor)
├── corpus/               # NEW package (Phase 2)
│   ├── __init__.py
│   ├── verifier.py       # stdlib-only trust root: own is_conflict, VerificationError, raises
│   ├── schema.py         # schema v1: field list, validation, canonical serialize + sha256
│   └── store.py          # append-only atomic store (tempfile + os.replace + prefix guard)
└── invariants/
    └── matching.py       # UNCHANGED ν oracle; + (option) witness.py emission helper here
tests/
├── test_verifier_mutants.py     # adversarial mutant suite (VRF-01 crit-2)
├── test_verifier_dash_O.py      # subprocess `python -O` fail-closed canary (VRF-01 crit-1)
├── test_schema_roundtrip.py     # schema v1 round-trip on D.2/D.3 (VRF-02 crit-3)
├── test_tutte_berge.py          # M+U hand-check both directions (CHI-02)
└── test_store_append_only.py    # atomicity + prefix-immutability (VRF-02)
```

### Pattern 1: The independent verifier (VRF-01)
**What:** A stdlib-only module `corpus/verifier.py` exposing `verify_model_record(record)` and `verify_chi_witness(record)`. It builds H-adjacency from `record["H_edges"]` (a fresh `list[set]`), carries its **own** `is_conflict` (byte-identical logic to Appendix C, private copy — the Phase-1 "Pattern 3" trust-root import boundary, now hardened), and derives `k = len(model_branch_sets)` internally (asserting nothing — checking with raises).
**When to use:** This is the VRF-01 deliverable. The old `verify/model.py` remains untouched.
**Contract (Appendix E §4.6), each as an explicit raise:**
1. Structural: `n`, `chi` are ints ≥ 1; every `H_edges` entry is `[u,v]` with `0 ≤ u < v < n`, no duplicates → build `adj`.
2. Integrity: recomputed canonical `H_edges` sha256 == stored `H_edges_sha256` (reuse Phase-1 convention).
3. `k = len(model_branch_sets)`; require `k ≥ chi` (Hadwiger claim needs a K_k, k≥χ) and store/verify k as `had_2`.
4. Each branch set size ∈ {1,2}; every vertex in `[0,n)`; **global disjointness** (no vertex reused across sets).
5. Each size-2 set `{a,b}`: `{a,b}` is a **G-edge**, i.e. `b ∉ adj[a]` (NOT an H-edge).
6. Every pair `i<j` of branch sets is **adjacent in G**: `not is_conflict(sets[i], sets[j], adj)` — i.e. some cross pair is a G-edge. This is all `C(k,2)` cross-adjacencies.

**Key discipline:** `is_conflict(A,B,adj)` returns `True` iff A,B are **non-adjacent in G** (every cross pair is an H-edge). The verifier's own copy — do not import from `search/`.

### Pattern 2: Real checks that RAISE (correct under `python -O`)
**What:** Every check is `if not cond: raise VerificationError(msg)` — **never** `assert`. Define `class VerificationError(Exception)`. Optionally collect *all* violated invariants before raising (addresses Phase-1 WR-02: assert-order can mask the interesting defect), e.g. accumulate messages and raise once with the full list.
**Why (verified live this session):**
```
python -O -c "assert (-1)>0"      # -> silently passes (no error): rubber stamp
python -O -c "... raise ...(-1)"  # -> still raises: fail-closed
```
Under `-O`, `__debug__ is False` and all `assert` statements are stripped. The trust root must not depend on `assert`. **Belt-and-suspenders:** also add a module-load guard is *optional* — but note the success criterion wants the verifier to *still verify correctly* under `-O` (fail-closed on bad input), which requires the raise-based checks, **not** a refuse-to-run guard. (A refuse-to-run `if not __debug__: raise` guard would make the `-O` CI job unable to run the verifier at all — do **not** use it as the primary mechanism; raise-based checks are mandatory.)

### Pattern 3: Certificate schema v1 (VRF-02)
**What:** One record dict per instance, `schema_version: 1`, with a **tagged-union provenance** discriminated by `kind`. Full field list (concrete example below in Code Examples §5, instantiated from D.2/D.3).

Provenance shapes (all three required by criterion 3):
- `kind: "seed"` — deterministic in (n, seed). TFP complements. `{kind, family, n, seed, process}`; `seed` present.
- `kind: "params"` — deterministic in structured parameters (sum-free Cayley Z_p, Kneser, inflation). `{kind, family, n, params:{...}}`; `seed` **optional**, `params` **required**.
- `kind: "graph6"` — external/ingested identity (nauty `geng`, Ramsey datasets). `{kind, family, n, graph6}`; `graph6` **required**, no seed/params.

Body fields: `H_edges` (canonical sorted `[min,max]`), `H_edges_sha256`, `invariants: {n, num_H_edges, nu_H, chi_G, omega_G|null, had_2|null}`, `model_branch_sets` (**FULL** family, length k = had₂ ≥ χ — never `fam[:χ]`), `matching_M` (list of ν edges), `tutte_berge_U` (list of vertices; **`[]` for the current corpus**), `verified` (bool, set only after verifier passes), `method` (`"heuristic"` | `"exact ILP (CBC): had_2=..."` | `"exact CP-SAT"`), `reproduction` + `backends` (Pattern 6).

**Critical subtlety — full family vs χ-model:** D.2 and D.3 both show 16-set `model_branch_sets` (= χ). But seed-137 has **had₂ = 17 > χ = 16**: its FULL optimal family is 17 sets, and that 17-set family is **not in Appendix D** (only the K₁₆ model is) — it requires the CBC ILP (Phase 4). So Phase 2's schema must **support k ≥ χ**, but Phase 2 round-trips only the models it has (the 16-set D.2/D.3 families). Flag this to the planner: do **not** try to produce the 17-set seed-137 family in Phase 2.

### Pattern 4: Append-only atomic store (VRF-02)
**What:** `store.py` with `append_certificate(record, path=paths.CORPUS)`:
1. Load current array (or `[]` if absent).
2. **Append-only guard:** recompute a per-record content hash for every *existing* record and compare against the just-loaded prefix (i.e., the new array's first `len(old)` records must be byte-identical to the old array). Refuse (`raise`) if any prior record changed. (Existing records are immutable — VRF-03.)
3. Verify the new record with `corpus/verifier.py`; refuse to append unless `verified` is true. **Nothing enters unverified.**
4. Append, then **atomic write**: `tempfile.NamedTemporaryFile(dir=path.parent, delete=False)` → `json.dump` → `flush` + `os.fsync(fd)` → `os.replace(tmp, path)` → optionally `os.fsync` the directory fd for durability.

**Why `os.replace`:** on POSIX (and Windows) `os.replace` is atomic *within the same filesystem* — a reader sees either the old or the new file, never a truncated one. The temp file must be in the **same directory** (`dir=path.parent`) so the rename doesn't cross filesystems. `[CITED: docs.python.org os.replace — "If dst exists ... the replacement is atomic ... on many operating systems"]`

**Current corpus state:** `data/corpus/` holds only `.gitkeep`; `baseline.py` writes a flat unversioned list but has **not** been committed-run into the repo corpus (no data migration needed — Phase 3 regenerates under schema v1). See Runtime State Inventory.

### Pattern 5: Tutte–Berge witness (CHI-02) — the crux, VERIFIED
**Statement:** ν(H) = (1/2)·min_{U⊆V}( n − odd_components(H−U) + |U| ). For **any** U, ν ≤ (1/2)(n − c_odd(H−U) + |U|) (upper bound). A matching M gives ν ≥ |M| (lower bound). When they meet, ν — hence χ = n − ν — is pinned in **both directions**, hand-checkable without trusting the matching library or formalizing Edmonds.

**Extraction (emission, UNTRUSTED):** `U = A(G)` from Gallai–Edmonds. Robust reference method — probing:
- `D = { v : ν(H − v) == ν(H) }` (exposable/inessential vertices; n matching calls).
- `A = { u ∉ D : u has a neighbor in D }`; set `U = A`.
- (Faster optional: alternating-forest labels from one matching — but that re-implements blossom; probing is preferred since extraction is untrusted.)

**Verification (trust root, stdlib-only, GENERAL):**
- `M` is a valid matching: every edge ∈ `H_edges`, edges vertex-disjoint; `|M| == nu_H` (= n − chi).  → ν ≥ |M|.
- Build `H − U` from `H_edges` minus vertices in `U`; count **odd-order connected components** `c_odd` by stdlib BFS/DFS.
- Require `(n − c_odd + |U|)` even and `(n − c_odd + |U|) // 2 == |M|`.  → ν ≤ that = |M| → ν pinned → χ = n − ν.

**VERIFIED this session (real instances):**
```
seed=1  : n=31 ν=15 χ=16 |U|=0 odd_comps(H−U)=1 ub=(31−1+0)/2=15 == |M|  ✓
seed=137: n=31 ν=15 χ=16 |U|=0 odd_comps(H−U)=1 ub=(31−1+0)/2=15 == |M|  ✓
```
**Why U=∅ for this corpus (structural, HIGH confidence):** gate condition **G3** requires H **factor-critical** (n odd, H connected/diameter-2, and "H − v has a perfect matching for all v"). Factor-critical ⇒ D(G) = V, A(G) = ∅ ⇒ **U = ∅**, and the single odd component is H itself (order n odd) ⇒ ν ≤ (n−1)/2, met by the near-perfect M. This *is* why χ = (n+1)/2 and G1's `n = 2χ − 1`. **The hand-check reduces to one sentence:** "H is connected of odd order n, so ν ≤ (n−1)/2; M is a matching of (n−1)/2 edges, so ν = (n−1)/2 and χ = (n+1)/2." **But keep the verifier general** — n=32 (even) and any future deficiency->parity family need the full odd-component computation; never hardcode U=∅.

### Pattern 6: Reproduction contract (ENV-05)
**What:** Two `reproduction.kind` values + per-cert version stamps.
- `kind: "byte_exact"` — heuristic/seed-derived models. The `model_branch_sets` are byte-reproducible **only on the pinned interpreter** from `(n, seed)` via the single-RNG contract (depends on CPython set-iteration + `random`). Record `seed`, `python`, `networkx`.
- `kind: "semantic"` — exact-method (CBC ILP / CP-SAT) models. The *model bytes* are **not** cross-platform/cross-solver reproducible (CBC threading/Rosetta nondeterminism), but the *claim* (had₂ value, optimality) is semantically reproducible and the stored model is a valid witness verified independently. Record `pulp`/`cbc` or `ortools` versions + platform.
- `backends` block: `{python, networkx, pulp|null, cbc|null, ortools|null, platform:{system, machine, cbc_under_rosetta:bool}}` via `platform.python_version()`, `platform.machine()`, `sys.platform`.
- `reproduction.canonical_platform: "linux-x86_64"` — CLAUDE.md: bundled CBC on Apple Silicon runs under **Rosetta 2** (x86_64 emulation); make Linux x86_64 the reference for regenerating ILP-method certs so semantic reproduction is deterministic.

### Anti-Patterns to Avoid
- **`assert` in the verifier.** Stripped under `-O` → rubber stamp. Use raises. (Verified live.)
- **Trusting the passed-in adjacency / the emission ν, M, U.** The verifier must rebuild `adj` from `H_edges` and re-derive everything; extraction is untrusted.
- **Importing `is_conflict` (or anything) from `search`/`generators`/`solver` into the verifier.** Breaks the trust boundary; add an import-boundary test.
- **Truncating the family to `fam[:χ]`.** Destroys the k-level witness E1 (ESC-01) needs (seed-137 k=17).
- **Hardcoding U=∅.** Correct for this corpus but wrong in general; keep the odd-component computation.
- **In-place edit of an existing corpus record.** Violates append-only/VRF-03. Status is a derived view.
- **Writing directly to the corpus file (no temp+replace).** A crash mid-write corrupts the trust anchor.
- **JSON Lines relying on `O_APPEND` single-write atomicity.** Full certs exceed `PIPE_BUF`; torn writes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Max matching ν(H) at emission | A blossom implementation | `networkx.max_weight_matching(maxcardinality=True)` (existing `matching.py`) | O(n³) exact, integer-exact for unit weights; already the corpus oracle. `[VERIFIED]` |
| Atomic file replace | `open(...,'w')` + write + hope | `tempfile` + `os.fsync` + `os.replace` | `os.replace` is atomic same-FS; hand-rolled write leaves torn files on crash. `[CITED: python docs]` |
| Canonical graph hash | `str(edges)` / WL-hash | `sha256(json.dumps(sorted_edges, separators=(",",":")))` | Frozen Phase-1 convention; WL-hash is non-canonical (CLAUDE.md forbids it for identity). |
| Gallai–Edmonds decomposition | Formalizing/implementing Edmonds to *trust* U | Untrusted extraction + **verifier re-checks the Tutte–Berge inequality** | networkx has **no** Gallai–Edmonds helper (verified); and we never need to *trust* it — the odd-component count re-proves the bound. |

**Key insight:** the entire CHI-02 difficulty ("without trusting the matching library or formalizing Edmonds") dissolves because verification only needs to *count odd components* and *validate a matching* — both trivial stdlib graph operations — not to *reproduce* the decomposition. Store M and U; check two inequalities meet.

## Runtime State Inventory

> Phase 2 introduces a schema and a new store; the existing corpus writer changes shape. This is a light refactor/migration — inventory below.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `data/corpus/` contains only `.gitkeep` — **no committed corpus JSON**. `baseline.py` *can* write a flat unversioned list but it has not been run into the repo (verified: `find data -type f` shows only `.gitkeep`, `.gitkeep`, `fingerprint.json`). | **None** — no data migration. Phase 3 regenerates the corpus under schema v1. Phase 2 only defines schema+store and round-trips D.2/D.3 exemplars in tests. |
| Live service config | None — no databases, no external services, no daemons. | None. |
| OS-registered state | None. | None. |
| Secrets/env vars | None. `PYTHONOPTIMIZE`/`-O` is an *interpreter flag* the `-O` CI job sets deliberately (not a secret) — the verifier must be correct under it. | None (design for `-O`, don't store anything). |
| Build artifacts | `src/alpha2/**/__pycache__/*.pyc` present (harmless). The verbatim `verify/model.py` bytecode is unaffected — Phase 2 *adds* `corpus/` rather than editing it. | None — but the new `corpus/` package needs no reinstall (editable src-layout install from Phase 1 already picks up new modules). |

**Schema-shape change (not a data migration):** the flat record `baseline.py` writes (`{n, seed, process, H_edges, H_triangle_free, H_edge_maximal, matching_number_H, chi_G, model_branch_sets, verified}`) is a **subset** of schema v1. Phase 2 defines the v1 superset (adds `schema_version`, `provenance` union, `H_edges_sha256`, `invariants`, `matching_M`, `tutte_berge_U`, `method`, `reproduction`, `backends`). `baseline.py`'s writer is updated to emit v1 in Phase 3 when the corpus is regenerated; Phase 2 need only prove the schema round-trips.

## Common Pitfalls

### Pitfall 1: Verifier silently rubber-stamps under `-O`
**What goes wrong:** `assert`-based checks vanish under `python -O`/`PYTHONOPTIMIZE`; the trust root returns `True` for garbage. **Verified live: `python -O -c "assert (-1)>0"` passes.**
**Why:** CPython strips `assert` when `__debug__ is False`.
**How to avoid:** every check is `if not cond: raise VerificationError(...)`. Add the `-O` subprocess CI test (Validation §2) that feeds a known-bad model under `-O` and asserts a non-zero exit / `VerificationError`.
**Warning signs:** any `assert` token in `corpus/verifier.py`; a `-O` test that passes a bad model.

### Pitfall 2: Trust-boundary leak via imports
**What goes wrong:** verifier imports `is_conflict` from `search/heuristic.py` (or networkx) → shares logic with the proposer; a bug in the proposer's conflict logic is no longer independently caught.
**Why:** convenience/DRY instinct.
**How to avoid:** private byte-identical `is_conflict` copy; stdlib-only imports; an AST/grep import-boundary test asserting `corpus/verifier.py` imports only from an allow-list (`json, hashlib, os, sys, collections, ...`).
**Warning signs:** any `from alpha2.search`/`from alpha2.generators`/`import networkx` in `verifier.py`.

### Pitfall 3: Truncated family
**What goes wrong:** storing `fam[:χ]` when had₂ > χ (seed-137: 17→16) discards the extra branch set the k-level falsification check (ESC-01) needs.
**How to avoid:** store `len(sets) = had₂` sets; verifier derives `k = len(sets)`; schema documents "FULL family, never `fam[:χ]`". Note the true 17-set family arrives in Phase 4 — Phase 2 must not fake it.
**Warning signs:** `chi` used as the family length; `model_branch_sets[:chi]` anywhere.

### Pitfall 4: Hardcoding the empty witness
**What goes wrong:** since U=∅ for the current corpus, a lazy verifier skips the odd-component computation → wrong for n=32 (even) or any future deficiency-heavy family.
**How to avoid:** implement the general `odd_components(H−U)` check; U=∅ is just the common case, not an assumption.
**Warning signs:** verifier reads `U` but never removes it / never counts components.

### Pitfall 5: Non-atomic / mutating corpus writes
**What goes wrong:** direct-write corruption on crash; or editing an existing record (violates VRF-03 immutability).
**How to avoid:** `tempfile`+`os.replace`; prefix-immutability guard; append-only API only.
**Warning signs:** `open(CORPUS,'w')` outside the atomic helper; any record index reassigned.

### Pitfall 6: `H_edges` orientation / canonicality drift
**What goes wrong:** storing `[u,v]` unsorted or not globally sorted → sha256 mismatch vs the frozen golden.
**How to avoid:** reuse `sorted([min(u,v),max(u,v)] for ... if u<v)` + `json.dumps(..., separators=(",",":"))` exactly (Phase-1 convention); verifier recomputes and compares.
**Warning signs:** sha256 mismatch immediately after "formatting-only" changes.

## Code Examples

### 1. Verifier core (stdlib-only, raises) — VRF-01
```python
# src/alpha2/corpus/verifier.py  (stdlib ONLY)
# Source: Appendix C.1 is_conflict/verify_model semantics + Appendix E §4.6, hardened to raises.
import json, hashlib
from collections import deque

class VerificationError(Exception):
    pass

def _is_conflict(A, B, adj):
    """True iff A,B are NON-adjacent in G (every cross pair is an H-edge). Own copy."""
    for x in A:
        ax = adj[x]
        for y in B:
            if y not in ax:
                return False
    return True

def _build_adj(H_edges, n):
    adj = [set() for _ in range(n)]
    seen = set()
    for e in H_edges:
        if len(e) != 2:
            raise VerificationError(f"bad H_edge {e!r}")
        u, v = e
        if not (isinstance(u, int) and isinstance(v, int) and 0 <= u < v < n):
            raise VerificationError(f"non-canonical H_edge {e!r}")
        if (u, v) in seen:
            raise VerificationError(f"duplicate H_edge {e!r}")
        seen.add((u, v)); adj[u].add(v); adj[v].add(u)
    return adj

def verify_model_record(rec):
    n = rec["invariants"]["n"]; chi = rec["invariants"]["chi_G"]
    if not (isinstance(n, int) and isinstance(chi, int) and n >= 1 and chi >= 1):
        raise VerificationError("bad n/chi")
    # integrity: canonical H_edges sha256 must match stored
    edges = sorted([min(a, b), max(a, b)] for a, b in rec["H_edges"])
    canon = json.dumps(edges, separators=(",", ":"))
    if hashlib.sha256(canon.encode()).hexdigest() != rec["H_edges_sha256"]:
        raise VerificationError("H_edges_sha256 mismatch")
    adj = _build_adj(rec["H_edges"], n)
    sets = [tuple(s) for s in rec["model_branch_sets"]]
    k = len(sets)
    if k < chi:
        raise VerificationError(f"family size {k} < chi {chi}")
    used = set()
    for S in sets:
        if len(S) not in (1, 2):
            raise VerificationError(f"branch set size {len(S)} not in (1,2)")
        for v in S:
            if not (0 <= v < n):
                raise VerificationError(f"vertex {v} out of range")
            if v in used:
                raise VerificationError(f"branch sets not disjoint at {v}")
            used.add(v)
        if len(S) == 2:
            a, b = S
            if b in adj[a]:
                raise VerificationError(f"pair {S} is an H-edge, not a G-edge")
    for i in range(k):
        for j in range(i + 1, k):
            if _is_conflict(sets[i], sets[j], adj):
                raise VerificationError(f"branch sets {i},{j} not adjacent in G")
    return k  # = had_2 demonstrated (K_k minor)
```

### 2. `-O` fail-closed canary (subprocess) — VRF-01 crit-1
```python
# tests/test_verifier_dash_O.py
import subprocess, sys, textwrap
def test_verifier_rejects_bad_model_under_dash_O():
    script = textwrap.dedent('''
        import sys
        assert __debug__ is False           # confirm we are really under -O
        from alpha2.corpus.verifier import verify_model_record, VerificationError
        bad = {...}                         # a known-bad record (e.g. overlapping sets)
        try:
            verify_model_record(bad); sys.exit(2)   # BUG: rubber-stamped
        except VerificationError:
            sys.exit(0)                              # fail-closed: correct
    ''')
    r = subprocess.run([sys.executable, "-O", "-c", script],
                       env={"PYTHONPATH": "src"}, capture_output=True)
    assert r.returncode == 0, r.stderr.decode()
```

### 3. Tutte–Berge verification (stdlib odd-component count) — CHI-02
```python
def verify_chi_witness(rec):
    n = rec["invariants"]["n"]; nu = rec["invariants"]["nu_H"]; chi = rec["invariants"]["chi_G"]
    if n - nu != chi:
        raise VerificationError(f"chi {chi} != n-nu {n-nu}")
    adj = _build_adj(rec["H_edges"], n)
    M = [tuple(e) for e in rec["matching_M"]]
    covered = set()
    for a, b in M:                                   # M is a valid matching in H
        if b not in adj[a]:
            raise VerificationError(f"M edge {a,b} not in H")
        if a in covered or b in covered:
            raise VerificationError(f"M not a matching at {a,b}")
        covered.add(a); covered.add(b)
    if len(M) != nu:
        raise VerificationError(f"|M|={len(M)} != nu={nu}")          # nu >= |M|
    U = set(rec["tutte_berge_U"])
    keep = [v for v in range(n) if v not in U]
    keepset = set(keep); seen = set(); c_odd = 0
    for s in keep:                                   # odd components of H - U (stdlib BFS)
        if s in seen: continue
        seen.add(s); size = 0; dq = deque([s])
        while dq:
            x = dq.popleft(); size += 1
            for w in adj[x]:
                if w in keepset and w not in seen:
                    seen.add(w); dq.append(w)
        if size % 2 == 1: c_odd += 1
    tot = n - c_odd + len(U)
    if tot % 2 != 0 or tot // 2 != nu:               # nu <= (n - c_odd + |U|)/2, meets |M|
        raise VerificationError(f"Tutte-Berge upper bound {tot/2} != nu {nu}")
    return True   # nu pinned both directions -> chi = n - nu hand-checkable
```

### 4. Witness extraction (emission, UNTRUSTED) — CHI-02
```python
# emission helper (may import networkx; NOT imported by the verifier)
import networkx as nx
def extract_witness(adj, n):
    def nu_of(drop=None):
        G = nx.Graph(); G.add_nodes_from(v for v in range(n) if v != drop)
        for u in range(n):
            if u == drop: continue
            for v in adj[u]:
                if v > u and v != drop: G.add_edge(u, v)
        return G, len(nx.max_weight_matching(G, maxcardinality=True))
    G, nu = nu_of()
    M = list(nx.max_weight_matching(G, maxcardinality=True))
    D = {v for v in range(n) if nu_of(drop=v)[1] == nu}      # exposable vertices
    A = {u for u in range(n) if u not in D and any(w in D for w in adj[u])}
    U = sorted(A)                                            # == [] for factor-critical H
    return [sorted(map(int, e)) for e in M], U, nu
```

### 5. Schema v1 record — concrete instantiation from D.2 (n=31, s=1) — VRF-02
```json
{
  "schema_version": 1,
  "provenance": {
    "kind": "seed",
    "family": "triangle_free_process_complement",
    "n": 31,
    "seed": 1,
    "process": "Bohman uniform triangle-free process"
  },
  "H_edges": [[0, 3], "... 131 canonical [min,max] pairs, regenerable from seed 1 ..."],
  "H_edges_sha256": "3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2",
  "invariants": { "n": 31, "num_H_edges": 131, "nu_H": 15, "chi_G": 16, "omega_G": null, "had_2": 16 },
  "model_branch_sets": [[16,20],[14,3],[11,4],[10,19],[26,9],[6,29],[18,25],[13,24],
                        [30,8],[15,28],[27,12],[23,7],[17,2],[0],[21,22],[1,5]],
  "matching_M": ["... 15 vertex-disjoint H-edges (near-perfect; 1 vertex exposed) ..."],
  "tutte_berge_U": [],
  "verified": true,
  "method": "heuristic",
  "reproduction": { "kind": "byte_exact", "seed": 1, "canonical_platform": "linux-x86_64" },
  "backends": { "python": "3.12.13", "networkx": "3.6.1", "pulp": null, "cbc": null,
                "ortools": null, "platform": { "system": "Linux", "machine": "x86_64",
                "cbc_under_rosetta": false } }
}
```
And D.3 (n=31, s=137) differs by: `"seed": 137`, `omega_G: 14`, `had_2: 17` (with the FULL **17**-set family — Phase 4 produces it; Phase 2 may round-trip the 16-set K₁₆ model shown in D.3 as an interim), `method: "exact ILP (CBC): had_2(G)=17"`, `reproduction.kind: "semantic"`, `backends.pulp: "3.3.2"`, `cbc: "<version>"`. `tutte_berge_U` is still `[]` (verified).

### 6. Append-only atomic store — VRF-02
```python
# src/alpha2/corpus/store.py  (stdlib ONLY)
import json, os, tempfile
from alpha2 import paths
from alpha2.corpus.verifier import verify_model_record, verify_chi_witness, VerificationError

def append_certificate(rec, path=None):
    path = path or paths.ensure_parent(paths.CORPUS)
    old = json.load(open(path)) if os.path.exists(path) and os.path.getsize(path) else []
    verify_model_record(rec); verify_chi_witness(rec)     # nothing enters unverified
    if not rec.get("verified"):
        raise VerificationError("record not marked verified")
    new = old + [rec]
    # append-only guard: prefix must be byte-identical to the old array
    if json.dumps(new[:len(old)], sort_keys=True) != json.dumps(old, sort_keys=True):
        raise VerificationError("append-only violation: existing records changed")
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(new, f); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)                             # atomic same-filesystem swap
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `assert`-based `verify_model` (Appendix C / Phase 1 verbatim) | Explicit `raise VerificationError` in an independent stdlib module | Phase 2 (this) | Correct under `python -O`; fixes WR-01. Verbatim module stays as the P1 anchor. |
| Verifier reuses toolkit `is_conflict` (import) | Verifier's own private copy, zero toolkit imports | Phase 2 | True independence — the trust boundary. |
| Flat unversioned corpus list (`baseline.py`) | Schema v1 tagged-union provenance + witness fields + version stamps | Phase 2 schema; Phase 3 writer | Witness-complete, hand-checkable, reproducible-with-provenance. |
| Direct `open('w')` corpus write | `tempfile`+`os.replace` atomic + append-only prefix guard | Phase 2 | Crash-safe, immutable trust anchor. |

**Deprecated/outdated for this phase:** none discovered — the stack is locked and this is additive.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `tutte_berge_U = []` for *every* gate-passing corpus instance (via G3 factor-criticality) | Pattern 5 | Low — verified on seed 1 & 137; even if a future family has U≠∅, the **general** verifier handles it (only the "one-sentence hand-check" convenience is lost). |
| A2 | The full seed-137 17-set had₂ family is out of Phase 2 scope (needs CBC, Phase 4) | Pattern 3 | Low — schema supports k≥χ; only affects *which* model round-trips in Phase 2 tests. Confirm with planner that Phase 2 round-trips the 16-set D.3 model as interim. |
| A3 | Corpus substrate = single JSON array + atomic replace + prefix guard (not JSONL) | Pattern 4 | Low–Med — a design choice; JSONL is a viable alternative but has the torn-write caveat. Route to discuss-phase if the user prefers JSONL. |
| A4 | `omega_G` is optional/null unless a clique method already computed it (D.3 has 14; D.2 unknown) | Pattern 3 | Low — schema marks it nullable; ω computation is a later-phase concern. |
| A5 | No corpus data migration needed (repo corpus is empty) | Runtime State Inventory | Low — verified `find data`; if a corpus JSON is committed before Phase 2 executes, add a one-time v0→v1 upgrade (out of current scope). |

## Open Questions (RESOLVED)

1. **JSON array vs JSON Lines for the append-only substrate.**
   - What we know: array + `os.replace` + prefix guard is crash-safe and immutability-checkable with no deps.
   - What's unclear: at 296+ records with full n=501 `H_edges`, whole-file rewrite per append is O(corpus) per write. Fine for 296; revisit if the corpus grows to 10⁴+ (Phases 7/9 ingest 477k Ramsey graphs — though those may live in a separate ingested store, not the certificate corpus).
   - Recommendation: JSON array now (matches existing `baseline.py`); flag a possible JSONL/segmented migration for large-ingest phases.
   - **RESOLVED (2026-07-21):** JSON array + `os.replace` adopted for Phase 2 (see 02-02-PLAN.md store task); JSONL/segmented migration explicitly deferred to the large-ingest phases (7/9), not this phase.

2. **Should `verify_chi_witness` be mandatory on every append, or gated by a `has_witness` flag?**
   - What we know: CHI-02 requires the witness on each certificate.
   - Recommendation: mandatory — refuse to append a certificate lacking a valid M+U witness (enforces CHI-02 at the store boundary).
   - **RESOLVED (2026-07-21):** mandatory. 02-02-PLAN.md Task 2 gates every append on BOTH verify_model_record AND verify_chi_witness — no `has_witness` opt-out.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| CPython (pinned) | Everything | ✓ | 3.12.13 | — |
| networkx | Emission-time ν/M/U extraction only | ✓ | 3.6.1 | — (verifier itself needs none) |
| Python stdlib (`json/hashlib/os/tempfile/sys/platform/collections`) | Verifier, schema, store | ✓ | 3.12.13 | — |
| pytest | Test suite | ✓ (dev) | 8.x | — |
| `python -O` interpreter mode | `-O` fail-closed CI canary | ✓ (flag) | — | — |

**Missing dependencies with no fallback:** none. **With fallback:** none needed — the verifier is stdlib-only by mandate.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (Phase-1 suite in `tests/`) |
| Config file | `pyproject.toml` (existing) |
| Quick run command | `uv run pytest tests/test_verifier_mutants.py tests/test_tutte_berge.py -x` |
| Full suite command | `uv run pytest -q` (add the `-O` job separately) |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | File Exists? |
|-----|----------|-----------|-------------------|-------------|
| VRF-01 | Verifier refuses each mutant (overlap / H-edge pair / missing cross-adj / truncated / wrong χ) | unit | `pytest tests/test_verifier_mutants.py -x` | ❌ Wave 0 |
| VRF-01 | Fail-closed under `python -O` on a known-bad model | subprocess | `pytest tests/test_verifier_dash_O.py -x` | ❌ Wave 0 |
| VRF-01 | Import-boundary: `corpus/verifier.py` imports only stdlib | unit (AST/grep) | `pytest tests/test_verifier_isolation.py -x` | ❌ Wave 0 |
| VRF-02 | Schema v1 round-trips D.2 & D.3 exemplars; verifier accepts | unit | `pytest tests/test_schema_roundtrip.py -x` | ❌ Wave 0 |
| VRF-02 | Store: atomic write + append-only prefix guard refuses mutation | unit | `pytest tests/test_store_append_only.py -x` | ❌ Wave 0 |
| CHI-02 | M+U hand-check pins χ both directions (seed 1 & 137, U=[]) | unit | `pytest tests/test_tutte_berge.py -x` | ❌ Wave 0 |
| ENV-05 | Cert carries reproduction.kind + backend/platform stamps; Linux x86_64 canonical | unit | `pytest tests/test_reproduction_contract.py -x` | ❌ Wave 0 |

### Mutant suite design (VRF-01 crit-2)
Start from a known-good record (D.2). Each mutant = one perturbation; the verifier must **raise**:
- **Overlapping branch sets:** duplicate a vertex across two sets → "not disjoint".
- **H-edge pair:** replace a size-2 set with two vertices that *are* an H-edge → "pair is an H-edge, not a G-edge".
- **Missing cross-adjacency:** swap vertices so two sets become fully non-adjacent in G → "sets i,j not adjacent".
- **Truncated family:** drop the last set (`fam[:-1]`) → "family size k < chi" (k=15<16).
- **Wrong χ:** set `invariants.chi_G = 15` (or corrupt `nu_H`) → witness check "chi != n-nu" / family-size check.
Optionally property-test (hypothesis): random valid model + random single mutation ⇒ raises.

### `-O` fail-closed canary (VRF-01 crit-1)
Subprocess `python -O -c ...` (Code Examples §2). The script first asserts `__debug__ is False` (confirms real optimized mode), then feeds a known-bad record and requires `VerificationError` / exit 0. A companion assertion documents that a *bare-assert* verifier would have exit-2'd here — proving the raise-based checks are what fire.

### Schema round-trip (VRF-02 crit-3)
Build a v1 record from D.2 (and D.3's 16-set interim model), `json.dumps`→`json.loads`, assert field-equality, assert `verify_model_record` + `verify_chi_witness` both pass, assert `H_edges_sha256` == frozen golden `3c953d90…41e2` (D.2). Confirms all three provenance shapes validate (add a synthetic `params` Cayley record and a `graph6` record for shape coverage).

### Tutte–Berge hand-check (CHI-02)
Regenerate n=31 seed 1 and 137, compute M+U via `extract_witness`, assert `U == []`, assert `verify_chi_witness` passes, and assert the arithmetic `(n − odd_comps(H−U) + |U|)//2 == nu == |M| == 15` (matching the values verified live this session). Add a **general-path** test: a small even-n or deficiency-heavy synthetic graph with U≠∅ to prove the odd-component computation is exercised (guards Pitfall 4).

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_verifier_mutants.py tests/test_tutte_berge.py tests/test_verifier_dash_O.py -x` (sub-second + one subprocess).
- **Per wave merge:** `uv run pytest -q`.
- **Phase gate:** full suite green (incl. the `-O` job) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_verifier_mutants.py` — VRF-01 crit-2
- [ ] `tests/test_verifier_dash_O.py` — VRF-01 crit-1
- [ ] `tests/test_verifier_isolation.py` — import-boundary
- [ ] `tests/test_schema_roundtrip.py` — VRF-02
- [ ] `tests/test_store_append_only.py` — VRF-02
- [ ] `tests/test_tutte_berge.py` — CHI-02 (incl. general U≠∅ synthetic)
- [ ] `tests/test_reproduction_contract.py` — ENV-05
- [ ] Source modules: `src/alpha2/corpus/{__init__,verifier,schema,store}.py` + emission `extract_witness` helper

## Security Domain

This is a mathematics research harness — no auth, sessions, network, or user accounts. The one real security-relevant boundary is **input validation of untrusted stored JSON** by the trust-root verifier.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| **V5 Input Validation** | **yes** | The verifier treats the corpus record as **untrusted input**: validates types, ranges (`0≤u<v<n`), canonicality (sorted, no dups), sha256 integrity, and structural well-formedness before use — raising on any deviation. This is exactly the trust-root discipline. |
| V6 Cryptography | partial | `sha256` is used for **content integrity/identity** (canonical `H_edges` hash), not as a security control. No secrets, no signing. Do not hand-roll — use `hashlib.sha256`. |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/adversarial certificate (corrupt corpus, hostile mutant) | Tampering | Verifier raises on every structural/semantic violation (mutant suite proves it). |
| Silent verification bypass under `-O` | Elevation ("false verified") | Raise-based checks + `-O` CI canary. |
| Corpus corruption on crash mid-write | Denial / Tampering | `tempfile`+`os.replace` atomic write. |
| Undetected edit of an "immutable" record | Tampering / Repudiation | Append-only prefix-immutability guard; status is a derived view (VRF-03). |

## Sources

### Primary (HIGH confidence — verified by execution this session)
- **Live run, pinned interpreter:** `.venv/bin/python` (CPython 3.12.13) + networkx 3.6.1 — Tutte–Berge extraction on n=31 seeds 1 & 137 (U=∅, ν=15, χ=16, ub=15 both directions); `python -O` assert-stripping vs raise demonstration; networkx matching-module inventory (no Gallai–Edmonds/Tutte–Berge helper — only `max_weight_matching/is_matching/is_perfect_matching/matching_dict_to_set`).
- `.planning/reference/alpha2-program-source.md` — Appendix C.1 (`is_conflict` L102, `verify_model` L245, `matching_number` L91, record schema L280), Appendix D.1–D.3 (stored-cert table, D.2/D.3 exemplars + models), Appendix E §2 (G1–G6, G3 factor-criticality) + §4.6 (verification contract).
- `CLAUDE.md` — stack pins, "What NOT to use", Rosetta/CBC platform note, Asymmetry Principle, reporting discipline.
- `src/alpha2/{verify/model.py, invariants/matching.py, paths.py, generators/tfp.py, repro/baseline.py}` + `tests/test_fingerprint.py` (canonical sha256 convention, single-RNG contract).
- `.planning/phases/01-.../01-REVIEW.md` — WR-01 (`-O` vulnerability), WR-02 (assert-order masking).
- `.planning/REQUIREMENTS.md` (VRF-01/02/03, CHI-02, ENV-05/06), `.planning/ROADMAP.md` (Phase 2 success criteria).

### Secondary (MEDIUM — CITED)
- Python docs: `os.replace` atomicity (same-filesystem), `assert`/`__debug__` under `-O` (behavior confirmed by live run above, so effectively HIGH).

### Tertiary (LOW)
- None — no unverified web claims; the phase is internally sourced and the stack is locked.

## Metadata

**Confidence breakdown:**
- Verifier design (VRF-01): **HIGH** — semantics are Appendix C/E, hardening demonstrated live under `-O`.
- Tutte–Berge witness (CHI-02): **HIGH** — recipe executed on the two real exemplars; factor-criticality explains U=∅ structurally.
- Schema v1 (VRF-02): **HIGH** — instantiated concretely from D.2/D.3; the one caveat (17-set seed-137 family is Phase 4) is flagged.
- Store atomicity/append-only (VRF-02): **HIGH** — standard stdlib pattern, cited.
- Reproduction contract (ENV-05): **MEDIUM-HIGH** — byte-exact/semantic split and Rosetta rationale are from CLAUDE.md; exact version-stamp field names are Claude's discretion.

**Research date:** 2026-07-21
**Valid until:** ~2026-08-20 (30 days; stable — locked stack, stdlib mechanics, no fast-moving deps).
