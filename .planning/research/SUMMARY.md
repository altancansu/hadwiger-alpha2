# Project Research Summary

**Project:** The α = 2 Program — reproducible Hadwiger α = 2 hunt-and-certify harness
**Domain:** Exact computational graph theory (certificate-emitting minor search; Python milestone 1, Lean deferred to milestone 2)
**Researched:** 2026-07-21
**Confidence:** HIGH

## Executive Summary

This is a reproducibility-first computational research harness, not an app: a "kill battery" that hunts structured α(G) = 2 candidate graphs (H = Ḡ triangle-free) for K_χ minors with branch sets of size ≤ 2, verifies every existence claim with a hand-checkable certificate, and treats every impossibility-flavored claim as radioactive. Experts build this shape of system as a trust-topology problem: everything (generators, gate, heuristic, exact solvers) is an **untrusted proposer**; a single pure, stdlib-only, independently implemented verifier is the **trust root**; and an append-only certificate corpus doubles as a falsification suite for future impossibility arguments. The research settles the stack (uv-managed CPython 3.12.x, networkx 3.6.1, pulp==3.3.2 hard-pinned, ortools 9.15.6755, nauty 2.9.3), confirms the strategic literature position (CDM ⟹ SHC ⟹ HC verified in arXiv 2512.17114 with the CDM frontier stopping at n ≤ 11; the Odd Hadwiger Conjecture fell in Dec 2025, proving strengthenings can fail), and finds two data-ready pools (P0's entire frontier is 1,813 graphs; P6's 477,142 Ramsey(3,8,27) graphs are downloadable).

The recommended approach is **characterization before refactor**: pin the interpreter and port the Appendix C toolkit verbatim, harden the verifier, reproduce the 296-instance corpus as the regression harness, and only then refactor solvers behind an `ExactBackend` interface with a proven-optimality contract — then run the pools certifiability-first (P0 CDM before everything else). The build order maps cleanly onto 12 phases with hard sequential prerequisites in phases 1–4 and a dual-backend gate (phase 6) in front of everything that can ever assign SHC-CANDIDATE.

The key risks are all **soundness** risks in the impossibility direction, and three of the four researchers independently converged on the same short list: the system Python cannot run the stack at all (interpreter is the keystone); the current verifier is assert-based and strippable (`python -O` turns the trust root into a no-op); and the legacy exact solver never checks solver status, so a CBC timeout incumbent can read as an exact had₂ and fabricate an SHC counterexample with no certificate to catch it. Every one of these has a concrete, cheap prescription (below) that must land in the foundation phases — a bug that over-counts existence is caught by the verifier; a bug that under-counts existence produces a false impossibility signal that nothing downstream can detect.

## Convergent Findings (multiple researchers independently — these reshape the foundation phases)

1. **THE INTERPRETER IS THE KEYSTONE.** System Python 3.9.6 is EOL and cannot run the modern stack (networkx 3.6.1 requires ≥3.11; PuLP 3.3.2 requires ≥3.10; pynauty's classifiers stop at 3.12). Prescription: **uv-managed CPython 3.12.x, exact patch pinned**, with a corpus-fingerprint pytest (regenerate n=31 seed 1 → |E(H)| = 131 and byte-exact stored `H_edges`) run before any batch work — corpus byte-reproduction depends on CPython set-iteration internals. **Hard pin `pulp==3.3.2`** (PuLP 4.0 removes the bundled CBC and reworks the solver API — it would break Appendix C verbatim). macOS ships an x86_64-only bundled CBC (Rosetta on Apple Silicon) → **Linux x86_64 is the canonical reference-regeneration platform** for ILP-method certificates.
2. **THE TRUST ROOT MUST BE HARDENED FIRST.** The existing `verify_model` is 100% assert-based — under `python -O` it silently returns True on invalid models (demonstrated). It also shares `is_conflict` with the searcher (common-mode failure: one bug fools proposer and checker identically) and it trusts χ from networkx's blossom with no stored witness. Fixes, all in the foundation phases before corpus regeneration: real checks with explicit exceptions (zero asserts, plus a permanent `python -O` CI job); an independently implemented, stdlib-only verifier with its **own copy** of the conflict predicate that imports nothing from generator/searcher code and consumes only stored JSON; an adversarial mutant suite (the verifier is tested by what it refuses); and a stored **Tutte–Berge witness** (maximum matching M + set U) per certificate so χ = n − ν becomes hand-checkable both directions — this also converts milestone 2's hardest Lean lemma into a finite check.
3. **THE RADIOACTIVE-DIRECTION SOLVER BUGS.** Legacy `ilp_had2` reads the objective without ever checking solver status — a CBC `timeLimit` incumbent reads as an exact had₂, i.e., a fabricated SHC counterexample, the one wrong claim no certificate can catch. Contract: the `ExactBackend` interface separates **PROVED_OPTIMAL** from **INCUMBENT_ONLY** (tri-state; "had₂ < χ from an incumbent" must be unrepresentable). An **SHC-CANDIDATE requires BOTH CBC and CP-SAT to PROVE optimality with equal value**, in deterministic mode, versions and logs recorded. CP-SAT has documented parallel-mode soundness regressions (or-tools #3590, #3842, #4839): recorded claims use single-worker with pinned seed, or `interleave_search` deterministic parallelism. Also: **store FULL optimal families** — the legacy `fam[:chi]` truncation already discarded seed-137's 17-set family (had₂ = 17 > 16 = χ), creating a k-level blind spot in the Falsification-Rule suite above χ.
4. **IMPLEMENTATION WINS (verified derivations, re-verify in-phase).** (a) Obstruction-based constraint generation — enumerate C₄s / cherries / edges of sparse triangle-free H — replaces Appendix C's O(|E_G|²) pair-pair loop with a near-linear enumeration; assert equal counts vs the naive loop at n=31. (b) A structural checksum (single–single conflicts = |E(H)|; single–pair = Σ_v C(deg_H(v),2); pair–pair = ½ Σ C(codeg,2)) instantly detects a missing or inverted constraint class. (c) Branch-set-3 triples are valid ⟺ ≤ 1 H-edge among the three; the one-H-edge triples are exactly **Chudnovsky–Seymour seagulls and are conflict-free** — tier-1 had₃ escalation adds ~m·n variables and zero new conflict constraints, and the seagull-packing theorem's anti-matching condition is literally ν(H) ≥ ℓ (already computed) — a free pre-gate. (d) The Monotonicity Audit is mechanizable: a random-contraction falsifier catches every banned invariant (rank, spectral, χ itself) on ≤ 5-vertex counterexamples in seconds.
5. **DATA-READY POOLS.** P0's entire frontier is **1,813 maximal-triangle-free graphs** at n = 12–14 (147/392/1,274 per OEIS A216783; MTF ⟺ triangle-free ∧ diameter 2, so `geng -ctq n | pickg -Z2` generates them; a transfer lemma makes maximal-only sufficient for the whole CDM frontier). P6's **477,142 Ramsey(3,8,27) graphs** are downloadable from McKay's data page. Literature verified: **CDM ⟹ SHC ⟹ HC** (Costa–Luu–Wood–Yip, arXiv 2512.17114; CDM computationally verified only to n ≤ 11 — P0 extends a named frontier); the **Odd Hadwiger Conjecture was disproven Dec 2025** (arXiv 2512.20392) — strengthenings can and do fail, so hunting the strengthened rungs is live, not quixotic.
6. **OPEN QUESTION FOR THE AUTHOR.** The exact G1–G6 gate definitions were **not** preserved byte-exact in the reference file (only the toolkit code + certificates survived). FEATURES.md carries a reconstruction (cheap→expensive: α = 2 regime → connectivity → edge-maximality → dominating edge → known-safe screens → χ ≤ 6 / ω ≥ χ trivial wins), but the gate must be **pinned from the author's original §2 during the foundation phase**. Ship the gate as a configurable, cost-ordered predicate chain so the pinned definitions drop in as configuration, not code surgery.

## Key Findings

### Recommended Stack (locked — see STACK.md for API blueprints)

The stack decision itself was settled in PROJECT.md; research locked exact versions and verified every API surface against primary sources. The reproducibility anchor is uv (`uv python install 3.12` + `uv.lock`); every certificate records platform, interpreter, and library versions.

**Core technologies:**
- **CPython 3.12.x** (uv-managed, exact patch pinned; never system 3.9.6): the only minor version every pinned dependency verifiably supports; set-iteration and `random` internals guard byte-reproduction (fingerprint test mandatory)
- **networkx 3.6.1**: exact ν(H) via Edmonds blossom (`max_weight_matching(maxcardinality=True)`, O(n³), integer-exact) → χ(G) = n − ν; confined to `invariants/`
- **PuLP 3.3.2** (hard pin): reference ILP backend, bundles CBC — byte-compatible with Appendix C and the 296-corpus lineage; 4.0 drops bundled CBC
- **ortools 9.15.6755** (CP-SAT): optimality prover and scale solver; snake_case API verified; `certify` mode (feasibility, verifier arbitrates) vs `optimize` mode (PROVED_OPTIMAL only when value == bound)
- **nauty 2.9.3** (brew; never 2.9.0): `geng -ctq` exhaustive isomorph-free generation, `pickg -Z2` MTF filter at C speed, `shortg`/`labelg` canonical dedup (never networkx WL-hash — not canonical)
- **pynauty 2.8.8.1** (optional): in-process `autgrp()` orbits + `certificate()` dedup only — it has no geng binding; generation always shells out
- **pytest 8.x / pytest-xdist / hypothesis / ruff / uv**: verifier + corpus reproduction run as the test suite
- **Lean v4.32.0 + pinned mathlib** (milestone 2 only): mathlib has **no graph-minor theory** — certificate-shaped local definitions (`ModelLE2` + `decide`), not general minor theory

**What NOT to use** (full table in STACK.md): system Python 3.9.6; PuLP 4.0 alphas; nauty 2.9.0; Blossom V (license kills redistribution); SciPy for ν (bipartite-only); WL-hash for dedup; CP-SAT default parallel portfolio for *reported* impossibility; solver-found models trusted without the verifier.

### Expected Features

**Must have (table stakes — the harness does not run without these; TS-1..TS-10 in FEATURES.md):**
- Gate G1–G6 as a configurable cost-ordered chain, kill-on-first-failure with logged reason + machine-checkable witness (definitions pinned from the author — the one open input)
- Exact χ via matching (χ = n − ν(H)); ω(G) ≥ χ fast path (a max clique is already a verified singleton model)
- Profile-general heuristic model search — the seed-137 fix: iterate non-spanning profiles (p′, s′), p′ + s′ = χ, 2p′ + s′ ≤ n; "not found" is forever a statement about the searcher
- Exact had₂ ILP (the SHC decider) behind `ExactBackend` with the tri-state status contract; obstruction-based constraint generation + structural checksums
- Branch-set-3 escalation (had₃) designed now, implemented behind a flag, tested on synthetic instances; seagull tier first
- Independent verifier (trust root — hardened per convergent finding 2)
- Seeded certificate corpus + reproduction (296 regenerated and re-verified; 27 stored certificates byte-reproduced; append-only, atomic, canonical JSON, golden-hash manifest)
- Results log + status taxonomy: KILLED (gate vs model, separate ledgers) / SHC-CANDIDATE / RESISTANT — statuses derived, never stored mutable; RESISTANT reachable only via exact-method timeout
- One tested CLI running the 7-step runbook; backend abstraction (CBC reference never removed; CP-SAT for scale; backend disagreement = release-blocking bug)

**Should have (differentiators — the program's value):**
- **P0 CDM frontier** (1,813 graphs, n = 12–14; stretch ≤ 17): cheapest certified terrain, extends the literature's named n ≤ 11 frontier — first new science
- **P1 TFP complements at scale** (the signature family: 296/296 killed; probes the open linear-connected-matching asymptotic)
- **P6 Ramsey-extremal inflations** (downloadable data; minimum-clique-material regime ω/χ ≤ 1/2, structured counterpoint to TFP at proven-cheap sizes)
- **P2 sum-free Cayley complements** (general abelian groups, structured vs random — untouched by the literature)
- **P3 Higman–Sims complement inflations** (the named SRG gap CLWY could not settle; first real CP-SAT stress test; inflation operator shared with P6)
- **P4 generalized Kneser K(n,k,≥t)** outside CLWY's settled window (pin Theorem 3.12's exact window at phase start)
- **P5 crooked-graph families** (ETT 𝒲₃/𝒲₅ complements — newest, hardest, thin-witness regime; gated on a construction-study of arXiv 2508.19646)
- **P7 adversarial local search** (battery-as-fitness over MTF space; deliberately last; exact adjudication only)
- **E1 Falsification-Rule harness, E2 Monotonicity Audit, E3 survivor protocol** (the epistemic moat)

**Anti-features (deliberately NOT built — enforce in every phase):**
- Non-minor-monotone "impossibility" checks (rank / Frankl–Wilson / slice rank / minrank / spectral / rigidity) — contraction destroys linear structure; disqualified at the door by the audit registry
- Reporting heuristic "resistance" as a result — seed 137 is the standing lesson
- Any Lean impossibility claim; permitted phrase only: "this file compiles, and its statement says exactly X"
- Assuming HC's truth or falsity anywhere in control flow (priors may order the queue, never gate it)
- Reconstructing the original lost argument

### Architecture Approach

A src-layout Python package (`src/alpha2/`) organized as a trust topology: proposer layer (generators P0–P7 → gate → invariants → search + solvers) feeding a pure stdlib-only `verify/` trust root, below which sit an append-only corpus + golden-hash manifest + JSONL results-log, consumed read-only by the adversarial layer (`falsify/`). The four legacy drivers live in `repro/`, frozen after reproduction — they are the executable definition of the 296 corpus, and the forward-looking battery must never become their dependency. Reproduction is a three-level contract: **R1** certificate validity (stored witnesses re-verified from JSON alone — version-proof, every commit), **R2** generator determinism (golden hashes, seconds), **R3** full pipeline replay (pinned environment, release gate). Two RNG contracts: v1 frozen (legacy shared-stream, byte-exact for the 296), v2 derived (sha256 per-stage subseeds for all new pools). Statuses are derived views over corpus + log, never mutated records.

**Major components:** `graphs` (adj-set core, canonical serialization, sha256) · `generators/` (one module per pool, three descriptor shapes: seeded / parametric / exhaustive-stream) · `gate/` (configured predicate chain) · `invariants/` (networkx confined here; later Tutte–Berge witness extraction) · `search/` (heuristic, ported) · `solvers/` (ExactBackend + backend-neutral `problems/` had2/had3/cdm + differential harness) · `verify/` (trust root, own is_conflict) · `corpus/` (schema v1, atomic append-only store, manifest) · `battery/` (runbook steps 1–7, status machine) · `falsify/` (argument protocol + audit registry + corpus runner) · `repro/` (frozen) · `cli`.

### Critical Pitfalls (the "watch out for" list — top items from 11 in PITFALLS.md)

1. **Incumbent-as-optimum** (convergent finding 3) — tri-state Status; dual-backend rule for every "had₂ < χ"; `msg=1` in exact runs; store both value and bound always
2. **Strippable, non-independent verifier trusting χ** (convergent finding 2) — exception-based rewrite, `python -O` CI job, own conflict predicate, adversarial mutant suite, Tutte–Berge witnesses in schema before corpus regeneration
3. **Missing/inverted conflict class in the had₂ encoding** — structural checksums vs three independent combinatorial counts; brute-force differential at n ≤ 10; cross-solver agreement; seed-137 regression pinned (had₂ = 17); never report the objective without the verified witness
4. **Implicit branch-set connectivity lost in re-encodings** — the reference ILP enforces connectivity by variable indexing (pairs = G-edges only), never as a written constraint; every re-encoding (CP-SAT, had₃, Lean) audits the model-validity predicate item-by-item; verifier checks connectivity explicitly
5. **Unsound symmetry breaking** — "WLOG vertex 0" constraints fabricate had₂ = 2 < 3 = χ on C₅; SB only from computed Aut (nauty) or solver-internal `symmetry_level`; assume-and-verify: SB may speed the existence direction, the impossibility branch always reruns without SB
6. **Fixed-profile false resistance (seed 137)** — profile-general searcher; RESISTANT assignable only by exact-method code paths; budgets are config, not code
7. **Reproducibility rot** — shared RNG streams (contract v2), set-iteration coupling (pin CPython + fingerprint tests), networkx matching dict→set semantic drift (runtime guards: `2·len(M) ≤ n`, `χ ≥ ⌈n/2⌉`), solver-model nondeterminism (store witnesses, promise value-level not bit-level regeneration)
8. **Falsification-runner vacuity + k-level blind spot** — engagement telemetry with positive controls (a deliberately wrong argument must be caught); store full optimal families so k > χ levels are exercised (seed 137's k = 17)
9. **Gate wrong-reason kills** — criticality predicate must accept even n (corpus row n = 32, χ = 16; `ν(H) == n // 2`, not `n == 2χ − 1`); PASS/FAIL(witness)/ERROR three-way outcomes; gate-kill and model-kill ledgers never merged

## Implications for Roadmap

The reconciled build order below merges ARCHITECTURE.md's 12-phase dependency table (designed for exactly this granularity) with FEATURES.md's MVP sequencing and PITFALLS.md's phase mapping. **Phases 1→2→3→4 are strictly sequential — each is the safety net for the next. Do not begin phase 5 until 296/296 reproduces.** Phase 6 gates everything that can ever assign SHC-CANDIDATE.

### Phase 1: Pinned environment + scaffold + verbatim port
**Rationale:** The interpreter is the keystone (convergent finding 1); nothing else can even install. Characterization before refactor: the only code changes allowed are paths and imports.
**Delivers:** uv-managed CPython 3.12.x + locked deps (networkx 3.6.1, pulp==3.3.2, ortools 9.15.6755) + brew nauty 2.9.3; src-layout `alpha2/` package; Appendix C relocated into `graphs` / `generators/{tfp,cayley}` / `invariants/` / `search/` / `verify/` / `repro/` with algorithms byte-preserved; `paths.py` replaces the sandbox path; corpus-fingerprint test (n=31 seed 1 → |E(H)| = 131, stored `H_edges` byte-exact). **Includes the author task: pin the exact G1–G6 gate definitions from the original §2** (convergent finding 6).
**Avoids:** Pitfall 6 (interpreter/library matrix resolved before pinning).
**Exit:** n=31 seed=1 runs from the repo; `H_edges` + the K₁₆ model match the Appendix D exemplar.

### Phase 2: Trust root hardening + corpus schema
**Rationale:** The verifier must be trustworthy and the schema complete **before** 296 records exist in it (retrofitting witnesses means re-solving).
**Delivers:** `verify/` rewritten — zero asserts, explicit exceptions, own `is_conflict`, stdlib-only, imports nothing from proposers, consumes stored JSON only; adversarial mutant suite; `python -O` CI job; schema v1 with optional `seed` / required `params` / `graph6` shapes for all three generator kinds, inline `H_edges`, edge-list sha256, **full optimal families** (no `fam[:chi]` truncation), Tutte–Berge witness fields (M + U), solver status/bound/version fields; append-only atomic store; golden-hash manifest module.
**Avoids:** Pitfalls 7 (trust root), 8 (k-level blind spot), 6 (self-contained certificates).

### Phase 3: Reproduce + verify the 296
**Rationale:** The characterization suite for every later refactor and the trust anchor for the whole program.
**Delivers:** `repro/` drivers run (baseline 12 + sweep 269 + showpieces n=301/501 + Cayley 12 + seed-137 exact study); corpus regenerated; all instances verified; seed-1 and seed-137 stored models byte-equal to Appendix D; golden manifest frozen and committed; `repro/` frozen forever.
**Exit:** 296/296, manifest committed.

### Phase 4: Test suite + CI
**Rationale:** PROJECT.md requires verifier + corpus reproduction as tests; CI must exist before refactoring begins.
**Delivers:** pytest layers — unit (conflict machinery, invariants, store atomicity), R1 certificate validity over all stored certs, R2 manifest determinism panel, R3 replay slice; CI on pinned Python/deps (Linux canonical for ILP-certificate regeneration + macOS); newer-Python canary job to catch `random`/set-order drift on purpose; monotonicity-falsifier utility ships in the test toolkit (unit-tested against the verified ≤ 5-vertex counterexamples).
**Avoids:** Pitfalls 6, 9-falsifier groundwork.

### Phase 5: ExactBackend interface + CBC adapter
**Rationale:** First refactor under test; the interface shape is proven against known ground truth (seed 137) before a second engine exists. This phase *fixes* Appendix C, not just ports it.
**Delivers:** `solvers/result.py` (Status enum: MODEL_FOUND / PROVED_OPTIMAL / PROVED_INFEASIBLE / INCUMBENT_ONLY / UNKNOWN / ERROR), `backend.py`, `problems/had2.py` (backend-neutral obstruction enumeration — C₄s/cherries/H-edges — with structural checksums and equal-count assert vs the naive loop at n=31), `cbc.py` with decision + optimize modes and full status discipline; seed-137 regression: had₂ = 17, PROVED_OPTIMAL.
**Avoids:** Pitfalls 1, 2, and the O(|E_G|²) build-time trap (performance win 4a/4b).

### Phase 6: CP-SAT backend + differential harness
**Rationale:** The second engine and the cross-examination machinery — the precondition for ever assigning SHC-CANDIDATE. Gates phases 7, 8, 9, and the survivor protocol.
**Delivers:** `cpsat.py` (snake_case API; recorded mode = `num_workers=1` + pinned `random_seed`, or `interleave_search` deterministic parallelism; exploration mode free; `add_hint` warm starts; model proto + log export for radioactive claims); `differential.py`; CI agreement panel (both backends PROVED_OPTIMAL, equal values, both families independently verified); disagreement = CRITICAL, quarantine, halt batch.
**Avoids:** Pitfalls 2 (two-solver rule), 3 (cross-encoding differential catches lost connectivity).

### Phase 7: Battery pipeline + gate + CLI + results-log
**Rationale:** The "one tested CLI" Foundation requirement; needs both backends so the dual-backend status rule is real, not stubbed.
**Delivers:** `battery/pipeline.py` (steps 1–7 in cost order; status machine; reason + seed on every kill); `gate/` chain with the author-pinned G1–G6 as configuration + ω ≥ χ fast path + gate witnesses + PASS/FAIL/ERROR outcomes + correct even-n criticality predicate; JSONL results-log; `cli.py` (`reproduce`, `battery`, `verify`, `diff-backends`, `status`).
**Avoids:** Pitfall 10 (gate discipline), 5 (RESISTANT only via exact timeout).
**Exit:** `alpha2 battery --pool tfp --n 31 --seed 137` reproduces the case study end-to-end with correct statuses.

### Phase 8: Branch-set-3 escalation (had₃)
**Rationale:** Completes the pipeline contract before it is ever needed in anger; an SHC event during any later pool run can be escalated same-day.
**Delivers:** `problems/had3.py` on both backends using the tiered design (tier 1: conflict-free seagull triples only, ~m·n vars; tier 2: G-triangle triples with W(T)-pruned conflicts); Chudnovsky–Seymour necessary pre-gates (|V| ≥ 3ℓ, ℓ-connectivity, ν(H) ≥ ℓ); `verify/` extension to size-3 (explicit connectivity check); battery wiring of SHC-CANDIDATE → had₃; synthetic-target tests (no real SHC-candidate exists — 296/296 killed at ≤ 2).
**Avoids:** Pitfall 3's size-3 hazard (connectivity no longer a clean local substructure).

### Phase 9: nauty integration + P0 CDM frontier (first new science)
**Rationale:** Certifiability-first — a CDM counterexample is a single finitely checkable graph, and even all-kills extend a named literature frontier (n ≤ 11 → 14). Placed after 6–7 so CDM results get dual-backend cross-checks and battery logging. *(Reconciliation: FEATURES.md put P0 in v1 possibly ahead of CP-SAT using a DFS-only checker; ARCHITECTURE.md placed it after phases 6–7. Reconciled to after 6–7 — DFS remains the reference checker, CP-SAT the cross-check, and both agents' "first new science" intent is preserved.)*
**Delivers:** `generators/exhaustive.py` (`geng -ctq n | pickg -Z2` subprocess stream, graph6 decode, res/mod sharding; counts asserted against OEIS A216783: 147/392/1,274); the transfer lemma written up in-repo (maximal-TF-only suffices); `problems/cdm.py` (bitset DFS reference + CP-SAT with explicit connectivity encoding — CP-SAT has no lazy-cut callback; PySCIPOpt is the escape hatch if larger-n CDM ever needs separation); exhaustive n = 12–14 run; CDM certificates into corpus.
**Exit:** verified CDM frontier past n ≤ 11 — the cheapest publishable result the program can produce.

### Phase 10: Pool expansion — P1 at scale, P6, P2, then P3, P4
**Rationale:** Homogeneous work (each pool = generator + config, zero new infrastructure), internally ordered by cheapness: P1 (generator exists) and P6 (data exists; builds the inflation operator) first, P2 next (small generalization), then P3 (consumes the P6 inflation operator; first real CP-SAT stress test with HS symmetry) and P4 (parameter cartography against CLWY's settled window). P5 entry is gated on the ETT construction study and may defer to v2. The roadmapper may split this into two phases (P1/P6/P2 vs P3/P4) for finer grain — the pools are mutually independent.
**Delivers:** P1 larger-n sweeps with resistance tracking (RNG contract v2); shared inflation operator + P6 ingestion/sampling; P2 general abelian groups + structured sum-free catalogs; P3 HS construction + verification + symmetry-broken CP-SAT runs; P4 settled/open map maintained against the paper.
**Avoids:** Pitfall 4 (SB assume-and-verify rule enforced for P2/P3), Pitfall 10.3 (χ < n/2 instances crash the legacy profile assert — P4/P6 exercise this).

### Phase 11: Escalation harnesses — E1 Falsification Rule + E2 Monotonicity Audit + E3 survivor protocol
**Rationale:** Must exist before any impossibility argument is entertained, and before P7 (whose resistant elites route straight into E3). The falsification-runner half depends only on the corpus + a CLI hook and **may be pulled forward as parallel/slack work any time after phase 3** if an early discipline win is wanted — both ARCHITECTURE and FEATURES flag this flexibility.
**Delivers:** `falsify/` argument protocol (PROVES_IMPOSSIBLE / DECLINES / ERROR / TIMEOUT — errors never count as declines), engagement telemetry + synthetic wrong-argument positive control, k-level coverage up to stored had₂ families; audit registry (μ-family allowlist; rank/spectral/rigidity disqualified at the door) wired to the random-contraction falsifier from phase 4; survivor protocol runner (independent reproduction → scaled deterministic CP-SAT with long budgets and enumerated recorded seeds → `verify/reduction.py` independent enumeration audit → second family-membership audit).
**Avoids:** Pitfalls 8, 9, 4 (impossibility branch reruns without SB — codified here).

### Phase 12: P7 adversarial search
**Rationale:** Deliberately last: it consumes the entire battery as a stable library, needs the nauty canonical-label fitness cache, and its resistant elites must flow into an existing survivor protocol. *(Reconciliation: ARCHITECTURE.md ordered P7 (11) before escalation (12); FEATURES.md ordered escalation machinery before P7 and lists E3 as a hard P7 dependency. Reconciled: escalation at 11, P7 at 12 — FEATURES' dependency is structural, ARCHITECTURE's ordering was only maturity-based.)*
**Delivers:** `generators/adversarial.py` (triangle-preserving flips over MTF space at n = 31 where exact adjudication is proven cheap; tiered fitness with exact margins only at elite checkpoints; canonical-label dedup cache; full provenance lineage); exact-only reporting enforced by the status machine; elites feed back into P1–P6 as new family seeds.

### Phase Ordering Rationale

- **Characterization before refactor:** phases 1–4 reproduce the 296 with minimally moved code and build the safety net; the solver refactor (5–6) then has a regression harness. This is the single governing constraint all four researchers agree on.
- **Dual-backend before any status machinery:** phase 6 precedes the battery (7) so SHC-CANDIDATE's two-solver rule is real from day one — the radioactive direction is never live with one engine.
- **Escalation path before pools:** had₃ (8) precedes pool expansion so a had₂ < χ event anywhere can be escalated immediately rather than sitting as an unexamined bombshell.
- **Certifiability-first among pools:** P0 (9) before P1–P6 (10) — the CDM rung has the cheapest certificates and a named frontier to extend.
- **Epistemic apex last:** E1/E2/E3 (11) before P7 (12), because the only generative pool inherits every guardrail.
- **Pitfall coverage:** every critical pitfall has a named phase that closes it, and the foundation phases (1–4) close all soundness holes *before* the first new result can be produced.

### Research Flags

Phases likely needing deeper research during planning (`/gsd:plan-phase --research-phase`):
- **Phase 1:** not web research — **author input**: pin exact G1–G6 definitions (convergent finding 6); also confirm what B₇ denotes in the PST citation.
- **Phase 9 (P0):** re-derive the transfer lemma in-repo (flagged MEDIUM-HIGH); MTF-generator cross-check options (Brandt–Brinkmann–Harmuth / triangleramsey) if throughput hurts; geng res/mod split tuning at n = 14.
- **Phase 10 (P3/P4/P5):** pin CLWY Theorem 3.12's exact parameter window + intersection convention before declaring any P4 cell open; lift the Chudnovsky–Seymour clique-capacity formula from the primary paper; Green–Ruzsa classification details for P2 structured catalogs; **P5 requires reading ETT arXiv 2508.19646's construction sections** (crooked functions over F_{2^m}; instance sizes unverified — may exceed exact-ILP range) — heaviest research dependency in the program.
- **Milestone 2 (Lean):** re-verify mathlib's minor-theory absence at milestone start; `native_decide` axiom-budget policy; polarity-test design per definition.

Phases with standard patterns (skip research-phase):
- **Phases 2–8:** fully specified by the preserved Appendix C source + PROJECT.md + verified API surfaces (CP-SAT parameters, PuLP wheel contents, networkx docs all checked against primary sources in this research pass); the work is disciplined engineering, not discovery.
- **Phase 12 (P7):** engineering + guardrails already specified; no external unknowns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every version and API name verified against primary sources (PyPI, nauty 2.9.3 tarball, or-tools stable branch protos, PuLP wheel inspected locally) on 2026-07-21 |
| Features | HIGH (core) / MEDIUM-HIGH (pools) | Core pipeline fully specified by preserved Appendix C; all load-bearing pool citations verified against Oct–Dec 2025 arXiv; P4 window and P5 sizes flagged |
| Architecture | HIGH | Component design read directly from the Appendix C source + PROJECT.md constraints; determinism claims verified against official docs and issue trackers |
| Pitfalls | HIGH | Encoding claims checked line-by-line against source; monotonicity counterexamples and `python -O` behavior verified by direct computation; solver regressions cited to issue trackers |

**Overall confidence:** HIGH

### Gaps to Address

- **G1–G6 exact definitions** (not byte-preserved): pin from the author's original §2 in phase 1; gate ships as configuration so late pinning is cheap.
- **CLWY Theorem 3.12 window** ("2k − t ≤ n" vs "2k ≤ n" < (5/2)(k − t)): pin at P4 phase start before declaring cells open.
- **ETT crooked constructions + instance sizes** (P5): construction-study task gates the pool; sizes may force heuristic-only adjudication.
- **B₇ definition** (PST via CLWY [53]) and **exact form of Fox's bound**: pin during gate-G5 / P1 phase research; non-blocking.
- **Chudnovsky–Seymour clique-capacity formula**: lift from the primary paper when implementing the phase-8 pre-gate (transcription MEDIUM).
- **Green–Ruzsa classification details** (P2 structured catalogs): pin during P2 phase research.
- **pynauty on Python 3.13+** unverified — one more reason the interpreter holds at 3.12 for this milestone.
- **MTF generation throughput ceiling past n ≈ 16** (P0 stretch): evaluate dedicated MTF generators in phase 9 if the stretch is pursued.
- **mathlib minor-theory absence**: re-verify at milestone 2 start (state as of 2026-07-21: none).

## Sources

### Primary (HIGH confidence)
- `.planning/reference/alpha2-program-source.md` (Appendix C toolkit verbatim; Appendix D certificates incl. seed-137: χ = 16, ω = 14, had₂ = 17) and `.planning/PROJECT.md` — all encoding/architecture claims read from source
- PyPI: networkx 3.6.1, PuLP 3.3.2 (wheel inspected — bundled CBC incl. osx x86_64-only), ortools 9.15.6755 (arm64 cp312 wheel verified), pynauty 2.8.8.1 (no geng binding)
- nauty 2.9.3 (ANU tarball downloaded; `geng.c`/`testg.c` flags quoted verbatim); Homebrew formula
- or-tools stable branch: `sat_parameters.proto` (determinism knobs), `cp_model.py` (snake_case API); soundness issues #3590, #3842, #3943, #3948, #4839
- PuLP/CBC status issues: pulp#517, Cbc#440, discussion #486
- OEIS A216783 / A006785 (b-files fetched); McKay Ramsey data page (477,142 graphs downloadable)
- arXiv 2512.17114 (CLWY — ladder, n ≤ 11 frontier, settled/open map), 2512.20392 (Odd Hadwiger disproof), 2508.19646 (ETT), 2206.00186 (Norin–Seymour), 2409.05920 (Chen–Deng)
- mathlib4 SimpleGraph tree (no Minor/Contraction; `chromaticNumber` noncomputable ℕ∞ verified); Lean v4.32.0; native_decide soundness thread + RFC #12216
- python.org `random` reproducibility notes; PyPA src-layout discussion; networkx 2.0-vs-2.2 matching docs (dict→set drift)
- Direct computation (PITFALLS): rank/spectral/χ contraction counterexamples on ≤ 5 vertices; `python -O` strips the assert verifier; C₅ symmetry-breaking disaster; PYTHONHASHSEED set-order behavior

### Secondary (MEDIUM confidence — pin during phase research)
- Chudnovsky–Seymour "Packing seagulls" capacity formula (restated via arXiv 2510.12564); Green–Ruzsa classification; Bohman–Keevash / FGM TFP analyses; Fox bound exact form; B₇ definition

### Tertiary (LOW confidence — flagged)
- Exact original G1–G6 labels (reconstruction only — author must pin); ETT instance vertex counts; MTF-generation feasibility ceiling past n ≈ 16

---
*Research completed: 2026-07-21*
*Ready for roadmap: yes*
