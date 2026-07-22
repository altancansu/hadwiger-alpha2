# Phase 6: Kill Battery CLI (Gate, Search, Statuses) - Research

**Researched:** 2026-07-22
**Domain:** Pipeline orchestration over an existing solver/verifier stack — a necessary-conditions gate, a profile-general local-search heuristic, a 7-step runbook CLI, and derived-status/append-only-log discipline. Pure-Python; no new external dependency.
**Confidence:** HIGH (all machinery to be wired already exists and is tested in-repo; the pinned gate text is present in Appendix E §2; the one true blocker is a bounded author sign-off, and its scope is verified below by direct computation on seed-137)

## Summary

Phase 6 is almost entirely **wiring**, not invention. Phases 1–5 already delivered every hard part: exact χ (`invariants/matching.py`), the status-honest dual-backend exact stack (`solvers/{cbc,cpsat}.py` + `differential.py`), the frozen stdlib-only trust root (`corpus/verifier.py`), and the append-only verify-at-append corpus store (`corpus/store.py`). What is missing is (a) a `gate/` predicate chain, (b) a **profile-general** rewrite of the heuristic's profile loop (the current `search/heuristic.py:solve` hard-codes the single spanning profile that provably misses seed-137), (c) a `battery/` pipeline that runs the 7-step runbook and assigns statuses, (d) an append-only **JSONL results log** distinct from the certificate corpus, (e) a `status` view that derives KILLED/SHC-CANDIDATE/RESISTANT from corpus+log without editing records, and (f) an `alpha2` console entry point (none exists in `pyproject.toml`).

**The GATE-02 question resolves favorably: the exact G1–G6 definitions ARE pinned in-repo, at `.planning/reference/alpha2-program-source.md:635-644` (Appendix E §2). No definition needs to be invented — the hard blocker does not exist.** What remains is a bounded author sign-off (§ GATE-02 below): (1) reconcile the *labels* of the Appendix-E §2 "original" gate against the differently-decomposed FEATURES.md "reconstruction," (2) confirm what "B₇" denotes in the PST citation (needed only for a G6 known-safe screen, irrelevant to the SC1 slice), and — the finding this research surfaces as most consequential — (3) **decide the gate's kill-semantics for the studied candidate pools, because seed-137 provably FAILS the strict Appendix-E §2 gate at G3 and G4** (verified by direct computation: κ(G)=11 < χ=16; δ(G)=16 < χ+1=17; ω(G)=14 > χ−3=13; ω/n=0.45 ≫ 0.25). A strict kill-on-first-failure gate would gate-kill seed-137 (and, by construction, most of the 296-instance corpus) before the had₂ step ever runs — contradicting both SC1 and the very existence of the certificate corpus.

**Primary recommendation:** Ship the gate as a configured, cost-ordered predicate chain (mechanism), but run the **SC1 MVP slice against a criticality+regime gate (G1 with the even-n fix + G2 triangle-free/diameter-2 + connectivity) that seed-137 demonstrably PASSES**, and treat G3's deep conditions (κ, δ, Hamiltonicity, vertex-criticality, H−v matching), G4's ω-window, and the G5/G6 unavoidables/safe-family map as **hardening whose hard-kill-vs-flag role is exactly the author reconciliation GATE-02 demands**. Build everything provable-now autonomously; gate the word "trusted" (not the machinery) behind the sign-off.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| G1–G6 necessary-conditions filter | `gate/` (new) | `invariants/` (ν, ω, connectivity values) | Pure predicates over (H, invariants); owns no math beyond composing invariant values into pass/fail/error + witness |
| Exact χ = n − ν(H) | `invariants/matching.py` (exists) | — | Canonical value; already the sole χ path (CHI-01 AST guard) |
| ω(G) = α(H) for G4 | `invariants/` (new `cliques.py`) | networkx `max_weight_clique` | Exact max clique of G; networkx confined here |
| Profile-general heuristic search | `search/heuristic.py` (rewrite profile loop) | — | Untrusted proposal generator; verifier arbitrates |
| Exact had₂ / had₃ + dual-backend gate | `solvers/{cbc,cpsat,differential}.py` (exist) | — | Status-honest; SHC-CANDIDATE licensed ONLY by `differential_verdict` |
| Independent verification | `corpus/verifier.py` (frozen) | — | The trust root; confers truth on every model |
| Certificate persistence (facts) | `corpus/store.py` (exists) | `corpus/schema.py` | Append-only, verify-at-append, hash-chained |
| Results log (events) | `battery/` JSONL (new) | — | Every event incl. gate-kills/timeouts; NOT the corpus |
| 7-step runbook orchestration | `battery/pipeline.py` (new) | all above | Owns NO math; deterministic given (config, seeds) modulo declared solver modes |
| Derived statuses (KILLED/SHC/RESISTANT) | `status` view (new) | corpus + results log | Pure function of immutable facts; never edits a record (VRF-03) |
| CLI surface (`battery`, `status`, …) | `cli.py` (new) + `[project.scripts]` | argparse (stdlib) | Thin; no logic; keep `verify/` importable without CLI deps |

## Phase Requirements

<phase_requirements>
| ID | Description | Research Support |
|----|-------------|------------------|
| GATE-01 | G1–G6 as a configurable cost-ordered chain, kill on first failure, log reason + provenance | Pattern: gate as predicate chain (ARCHITECTURE Pattern 7); PASS/FAIL(witness)/ERROR outcome type (PITFALLS 10.4); gate-kills log-only, no certificate |
| GATE-02 | Exact G1–G6 frozen from author §2 (Appendix E), each with witness; reconstructed↔original labels reconciled with author before the gate is trusted | **Definitions pinned at ref §2 lines 635-644**; reconciliation + B₇ + kill-semantics sign-off scoped in the GATE-02 section below; SC1 slice runs autonomously on a reduced gate |
| GATE-03 | G5/G6 known-safe screen = maintained settled/open map with citations, consulted so proven terrain is never re-hunted | Proven-safe family list pinned at ref §2 line 644; ship as a data file (family → citation) + membership screens; MVP may stub with "screen not yet active" logging (FEATURES.md:229) |
| SRCH-01 | Profile-general heuristic: iterate (p′,s′) with p′+s′=χ and 2p′+s′≤n (seed-137 non-spanning fix); per-profile local-search + restarts | Current `solve()` hard-codes spanning profile (`heuristic.py:99-101`); **empirically MISSES seed-137 (verified: found=False in 45s)**; PITFALLS 4 gives the exact fix |
| SRCH-02 | Expose restarts-to-solution + initial-conflict instrumentation for P7 fitness; "not found" is a RESISTANT queue state only via exact, never a result | `solve()` already returns `(best_init, moves, restarts, elapsed)`; heuristic "not found" NEVER → RESISTANT (only exact timeout does — PITFALLS 4.1, ARCHITECTURE status table) |
| CLI-01 | One tested CLI runs the 7-step runbook, deterministic in (n,seed), per-step budgets, structured JSON logging; `--family` selects the pool | New `battery/pipeline.py` + `cli.py`; budgets are config not code (PITFALLS 4.3); driver pattern mirrors `repro/baseline.py:run_instance` |
| CLI-02 | Append-only results log: every terminal state + method + certificate ref + reason + seed/provenance | New JSONL log, separate contract from corpus (ARCHITECTURE "Corpus vs results-log") |
| VRF-03 | Status is a DERIVED view over immutable corpus + results log; transitions never edit stored records; RESISTANT only via exact-method timeout | ARCHITECTURE Pattern 4 + status semantics; store is append-only by construction (`store.py`) |
</phase_requirements>

---

## ⚠️ GATE-02 — Author-Input Finding (READ FIRST)

**Bottom line: Phase 6 is NOT hard-blocked. The SC1 seed-137 slice and all of GATE-01/SRCH/CLI/VRF machinery can be built and proven autonomously today. What must be gated behind an explicit author sign-off is only the word "trusted" applied to the full G1–G6 gate — specifically three bounded items, none of which require inventing a missing definition.**

### 1. Are the G1–G6 definitions pinned in-repo? YES.

They are at **`.planning/reference/alpha2-program-source.md:635-644`** (Appendix E §2), preserved verbatim as "the author's §2" (provenance note at line 629). Quoted exactly:

| # | Requirement (Appendix E §2) | Source / reason |
|---|---|---|
| G1 | n ≥ 31, n odd, n = 2χ(G) − 1 | Carter's computational bound; criticality |
| G2 | H = Ḡ triangle-free with diameter 2 (edge-maximal triangle-free) | no dominating edge may exist |
| G3 | χ(G) ≥ 7, κ(G) ≥ χ(G), δ(G) ≥ χ(G)+1, G Hamiltonian, G vertex-critical, H−v has a perfect matching ∀v | RST for K₆; PST properties |
| G4 | 8 ≤ ω(G) ≤ χ(G) − 3, and clique ratio ω/n below ≈ ¼ | K₈ unavoidable; seagull theorem |
| G5 | Every non-adjacent pair in an induced C₅; contains W₅, K₈, all 33 Carter unavoidables | unavoidability |
| G6 | outside every proven-safe family | (safe-family list at line 644) |

The proven-safe family list (for G6/GATE-03) is fully enumerated at line 644 with citations. `[VERIFIED: repo grep + Read of ref §2]`

### 2. What concretely still requires the human author?

**No invention — only three bounded confirmations:**

- **(a) Label reconciliation.** A *different* G1–G6 decomposition exists in `FEATURES.md:46-54` (a pre-pinning "reconstruction": G1=tri-free≥1 edge, G2=connected, G3=edge-maximal, G4=dominating-edge, G5=safe-screens, G6=χ≤6/ω≥χ). This is a **different partition of the same facts**, not a contradiction. GATE-02's "reconcile reconstructed vs. original" = pick the Appendix-E §2 labeling as authoritative and map the FEATURES checks onto it. This is a documentation/sign-off task, not a code blocker.  `[VERIFIED: both tables Read]`
- **(b) B₇ meaning.** The token "B₇" appears ONLY in the FEATURES.md reconstruction of a G5/G6 known-safe screen ("B₇-free per PST … CLWY [53]", `FEATURES.md:54,297`). It does **not** appear in Appendix E §2 at all. It is needed only for one G6 safe-family membership test and is **irrelevant to the SC1 slice**. Defer to GATE-03 hardening. `[VERIFIED: grep — B₇ absent from ref §2]`
- **(c) ⚠️ Gate kill-semantics for studied pools (the consequential one — surfaced by this research).** See item 3.

### 3. seed-137 FAILS the strict Appendix-E §2 gate — the central design decision

Direct computation on the regenerated (n=31, seed=137) instance (`./.venv/bin/python`, networkx 3.6.1):

| Gate condition (strict §2) | seed-137 actual | Verdict |
|---|---|---|
| G1 n≥31 ✓, n=2χ−1 (31=2·16−1) ✓ | passes | **PASS** |
| G1 "n odd" | n=31 odd ✓ (but n=32 corpus row is even — see below) | PASS for 137 |
| G2 triangle-free + diameter-2/edge-maximal | True, True | **PASS** |
| G3 χ≥7 | χ=16 | pass |
| **G3 κ(G) ≥ χ** | **κ(G)=11 < 16** | **FAIL** |
| **G3 δ(G) ≥ χ+1** | **δ(G)=16 < 17** | **FAIL** |
| **G4 8 ≤ ω(G) ≤ χ−3** | **ω(G)=14 > 13** | **FAIL** |
| **G4 ω/n ≲ ¼** | **ω/n=0.45** | **FAIL** |

`[VERIFIED: computed this session — max_weight_clique, node_connectivity, degree on complement(H)]`

A literal **kill-on-first-failure** gate would gate-kill seed-137 at G3 (κ<χ) — logging a reason, **appending no certificate**, and **never reaching the had₂=17 step**. That directly contradicts SC1 ("gate pass → … → verified kill appended") *and* is inconsistent with the existence of the 296-instance corpus (every corpus instance is a TFP/Cayley complement that reached had₂ and got a **verified certificate** — so in practice the gate did NOT hard-kill them at G3/G4).

**Interpretation.** Appendix E §2 states necessary conditions on a *minimal counterexample*. seed-137 legitimately is not one (it has a K₁₇ minor). But the program's value is the *machine-verified certificate*, and a gate-kill yields only a reason, not a certificate. The gate therefore plays two different roles that the author must disambiguate:

- **Role A (strict filter):** hard kill-on-first-failure. Correct for *hunting* new candidates (don't spend solver time on dead-on-arrival graphs). Under this role, most TFP complements gate-kill at G3/G4 and the corpus stays empty.
- **Role B (regime pre-screen + queue-ordering):** G1 (criticality/regime) and G2 (α=2 restriction) hard-kill malformed/non-critical inputs; G3–G6 are **recorded as flags / plausibility scores** but the candidate still proceeds to model-search + had₂ so a certificate is produced. This is the only role consistent with the 296-cert corpus and with SC1.

**Recommendation to the planner (autonomous-safe):**
1. Build the gate mechanism to support **both** roles via config (per-pool `hard_kill` vs `flag_only` tier assignment per check).
2. Run the **SC1 slice** with G1 (even-n criticality: `ν == n//2`) + G2 + connectivity as **hard** checks (seed-137 PASSES all — verified) and G3-deep/G4/G5/G6 as **flag_only** (recorded in the results log, not killing). This yields exactly SC1's "gate pass → χ=16 → heuristic miss → had₂=17 → verified kill."
3. Emit a `checkpoint:human-verify` before declaring the gate "trusted": the author confirms (a) the §2 labeling, (b) B₇, and **(c) whether TFP/Cayley pools run Role A or Role B, and if Role A, that gate-killing most of the corpus family is intended.**

### 4. Autonomous-now vs. author-gated

| Buildable & provable NOW (autonomous) | Gated behind author sign-off (deferred trust) |
|---|---|
| Gate **mechanism**: ordered `[(name, tier, fn)]`, PASS/FAIL(witness)/ERROR, per-pool config | Declaring the full G1–G6 gate "**trusted**" (GATE-02 wording) |
| G1 even-n criticality (`ν==n//2`), G2, connectivity checks + witnesses | The G3-deep / G4 window's **hard-kill role** for TFP/Cayley pools (Role A vs B) |
| ω(G)=α(H) exact via networkx (G4 input value) | G5 unavoidables (W₅/K₈/33 Carter graphs) + G6 safe-family map completeness (GATE-03) |
| **SC1 end-to-end seed-137 slice** (gate-pass config → had₂=17 kill) | B₇-free screen (one G6 family) — irrelevant to SC1 |
| Profile-general heuristic (SRCH-01/02) | — |
| Dual-backend had₂ → SHC/kill (already Phase-5 real, never stubbed) | — |
| Results log + derived statuses + `status`/`battery` CLI | — |

**Conclusion: execute Phase 6 autonomously to a working, tested seed-137 SC1 slice; carry the gate-trust sign-off as an explicit deferred checkpoint. Nothing is hard-blocked.**

---

## User Constraints

> No `CONTEXT.md` exists for Phase 6 (`/gsd:discuss-phase` was not run). Per the Phase-1/2/4/5 precedent, constraints are taken from the authoritative in-repo sources and carry **locked-decision authority**: CLAUDE.md (stack, Asymmetry Principle, reporting discipline, "What NOT to use"), the Phase-6 success criteria in ROADMAP.md (lines 106-118), the requirement text of GATE/SRCH/CLI/VRF, and the pinned Appendix E §2/§4. Route any `[ASSUMED]` item needing sign-off through discuss-phase before locking.

### Locked Decisions (from CLAUDE.md + ROADMAP SC + Appendix E)
- **Reporting discipline:** nothing is *found* until the independent verifier passes; nothing is *absent* until an exact method proves it. **Heuristic resistance is NEVER a result** — RESISTANT is an internal queue state reachable only via exact-method timeout.
- **Asymmetry / radioactive impossibility:** any `had₂ < χ` (SHC-CANDIDATE) requires **both** backends PROVED_OPTIMAL at equal value in deterministic mode — licensed ONLY by `differential_verdict` (already enforced, `differential.py`). Never single-backend.
- **Determinism:** deterministic in (n, seed); budgets/restart policy are **config, logged per run**, never hard-coded (PITFALLS 4.3, 8).
- **Trust root is frozen:** `corpus/verifier.py` and the append-only store are untouched; the battery consumes them, never bypasses them. All new guard code **raises** (no `assert` in the trust/gate path — survives `python -O`).
- **Even-n criticality (ROADMAP SC2, explicit):** the criticality predicate MUST accept even n (the n=32, χ=16 corpus row passes) — encode as `ν(H) == n//2`, overriding G1's literal "n odd."
- **Corpus is append-only; status is derived (VRF-03):** transitions never edit records.
- **The dual-backend SHC rule is real from day one, never stubbed** (ROADMAP Phase-6 "Depends on Phase 5").
- **Stack pins unchanged:** Python 3.12.x, networkx 3.6.1, pulp==3.3.2, ortools 9.15.6755 (pyproject already pins). No new runtime dependency is warranted.

### Claude's Discretion
- CLI framework (recommend **argparse**, stdlib — see Standard Stack).
- Internal module layout under the ARCHITECTURE-suggested `gate/`, `battery/`, `cli.py`.
- Profile iteration order and per-profile restart budgets (data/config).
- Results-log JSONL field schema (must carry the CLI-02 required fields).

### Deferred Ideas (OUT OF SCOPE for Phase 6)
- **nauty/geng exhaustive generation** — not installed (`geng not found`, verified), deferred to Phase 7. Phase 6 must NOT require exhaustive generation; it runs over existing corpus/generated instances.
- G5 full unavoidables screen (W₅/K₈/33 Carter graphs) and complete G6 safe-family membership — GATE-03 hardening; MVP may stub with "screen not yet active" logging.
- B₇-free screen — one G6 family, pending author confirmation of B₇.
- Escalation harness E1/E2/E3 (Phase 11); P7 adversarial search (Phase 12). The battery merely emits the RESISTANT queue + instrumentation they will consume.

## Standard Stack

### Core (all already installed & pinned — no install step needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| networkx | 3.6.1 | ω(G) via `max_weight_clique(G, weight=None)`; `node_connectivity` (κ, G3); `is_connected`; diameter | Already the invariant engine; confined to `invariants/`. `[VERIFIED: import + call this session]` |
| pulp (CBC) | 3.3.2 | Reference had₂/had₃ backend (`solvers/cbc.py`) | Frozen Phase-4 reference; battery calls via `get_backend("cbc")` |
| ortools (CP-SAT) | 9.15.6755 | Second exact engine (`solvers/cpsat.py`) | Frozen Phase-5; dual-backend agreement |
| argparse | stdlib | CLI subcommands (`battery`, `status`, `verify`, …) | Zero new dependency; keeps `verify/` importable without CLI deps (ARCHITECTURE `cli/` note). STACK.md proposes no CLI lib; stdlib is the disciplined default. `[ASSUMED: framework choice — discretion]` |
| json / dataclasses / enum | stdlib | Results-log JSONL, gate outcome types, status enum | Matches the stdlib-only trust-boundary discipline of `result.py`/`differential.py` |

### networkx 3.6.1 API note (IMPORTANT — training data is stale)
`nx.graph_clique_number(...)` was **REMOVED** in networkx 3.x (`AttributeError` confirmed this session). Use:
```python
clique, _ = nx.max_weight_clique(G, weight=None)   # weight=None => maximum cardinality clique
omega = len(clique)
```
`[VERIFIED: AttributeError on graph_clique_number, then max_weight_clique returned ω=14 for seed-137, this session]`

### No new external packages
Phase 6 introduces **zero** new runtime dependencies. Everything is stdlib + the three already-pinned solver/graph libraries. **The Package Legitimacy Audit is therefore N/A** (no `npm/pip install` of any new package). If the planner later proposes a CLI helper library, it must pass the legitimacy gate first — but the recommendation is explicitly to avoid one.

**Version verification performed:** `./.venv/bin/python` imports of networkx 3.6.1 confirmed; solver backends already exercised by 207 collected tests (`pytest --collect-only` = 207 tests, this session).

## Package Legitimacy Audit

**Not applicable.** Phase 6 installs no external package. All capabilities are provided by the Python standard library and the three already-locked, already-audited dependencies (networkx 3.6.1, pulp 3.3.2, ortools 9.15.6755) pinned in `pyproject.toml` since Phase 1. No `[SLOP]`/`[SUS]` surface exists.

## Architecture Patterns

### System Architecture Diagram (per-candidate 7-step runbook)

```
(family, n, seed[, params])
    │  generators/{tfp,cayley}  → H (adj: list[set[int]]) + provenance
    ▼
[1] gate/runner  G1..G6 in cost order         ── FAIL Gi (hard) ──▶ status KILLED(gate:Gi)
    │  (SC1 hard set: G1 ν==n//2 crit + G2 tf/diam2 + connectivity;      [results-log ONLY,
    │   G3-deep/G4/G5/G6 = flag_only, recorded not killing)               no certificate]
    ▼ PASS                                     ── ERROR ──▶ quarantine + operator page (never a kill)
[2] invariants  ν(H)→χ=n−ν (canonical, exact); ω(G)=α(H) [G4 input, computed pre-gate]
    │            └─ fast path: ω(G) ≥ χ → max clique IS a verified singleton K_χ model → KILLED
    ▼
[3] search/heuristic  PROFILE-GENERAL: iterate (p′,s′), p′+s′=χ, 2p′+s′≤n, per-profile restarts
    │   model proposal ──▶ verify/ ── pass ──▶ KILLED(model:heuristic) + corpus append
    ▼ NOT FOUND (fact about the searcher, NOT the graph — never RESISTANT)
[4] solvers/had₂  optimize, BOTH backends → differential_verdict(cbc, cpsat, χ):
    │   AGREED_KILL (had₂ ≥ χ) → extract family → verify/ → KILLED(model:exact-had2) + corpus
    │   SHC_CANDIDATE (had₂ < χ, both PROVED_OPTIMAL equal) → status SHC-CANDIDATE + corpus value-fact
    │   CriticalDisagreement → quarantine + HALT batch (release-blocking)
    ▼
[5] solvers/had₃  (only on SHC-CANDIDATE): seagull Tier-1, verify size-≤3 → KILLED(model:exact-had3)
    ▼
[6] any TIMEOUT/UNKNOWN/INCUMBENT_ONLY at steps 4–5 within budget ──▶ status RESISTANT (queue)
    ▼
[7] corpus append (verified facts only) + results-log append (EVERY event)
```

### Recommended Project Structure (extends existing `src/alpha2/`)
```
src/alpha2/
├── gate/
│   ├── runner.py       # ordered chain; PASS/FAIL(witness)/ERROR; GateKill(reason, witness)
│   ├── checks.py       # G1..G6 predicates over (adj, n, invariants); pure
│   └── safe_families.py # GATE-03 settled/open map (family → citation); MVP-stubbable
├── invariants/
│   └── cliques.py      # ω(G)=α(H) via nx.max_weight_clique; κ via node_connectivity
├── search/heuristic.py # REWRITE solve(): profile-general (p′,s′) iteration + instrumentation
├── battery/
│   ├── pipeline.py     # 7-step runbook; status machine; results-log emission
│   └── log.py          # append-only JSONL results log (distinct contract from corpus)
├── status/
│   └── views.py        # derive KILLED/SHC-CANDIDATE/RESISTANT from corpus + log (VRF-03)
└── cli.py              # argparse subcommands; [project.scripts] alpha2 = "alpha2.cli:main"
```

### Pattern 1: Gate as configured predicate chain (GATE-01)
**What:** `runner.py` executes `[(name, cost_tier, hard, check_fn), ...]` in cost order; each `check_fn(adj, n, inv) -> GateResult(PASS | FAIL(witness) | ERROR(trace))`. A hard FAIL stops with `GateKill(reason=name, witness=...)`; a flag_only FAIL is recorded and execution continues. ERROR quarantines (never a kill).
**When to use:** every candidate, step 1.
**Example (witness-carrying, raises-only, `python -O`-safe):**
```python
# gate/checks.py — G1 criticality with the mandated even-n fix (PITFALLS 10.1/10.3)
def g1_criticality(adj, n, inv):
    nu = inv["nu_H"]                      # from invariants/matching (already exact)
    if nu != n // 2:                      # accepts n=31 (nu=15) AND n=32 (nu=16)
        return Fail("not critical: nu(H)=%d != n//2=%d" % (nu, n // 2))
    if n < 31:
        return Fail("below Carter bound n>=31")
    return Pass(witness={"nu_H": nu, "chi_G": n - nu})
```
Note: encode the criticality predicate as `nu == n // 2` — NEVER `n == 2*chi - 1` (that silently drops even-n critical instances; the n=32 corpus row is the standing counterexample — PITFALLS 10.1).

### Pattern 2: Profile-general heuristic (SRCH-01 — the seed-137 fix)
**What:** The current `solve()` sets `p = n-k; s = 2*k-n` and `assert 2*p+s == n` (`heuristic.py:100-101`) — the single **spanning** profile. It can represent only s′=1 at n=31,χ=16 and **empirically MISSES seed-137** (verified: `found=False` after 45s; the D.3 optimum is 9 pairs + 7 singletons = 25 vertices, 6 unused — a shape the data structure cannot hold). Rewrite to iterate profiles `(p′, s′)` with `p′ + s′ = χ` and `2p′ + s′ ≤ n` (i.e. `s′` from `max(0, 2χ−n)` up to `χ`), each with its own restart budget, seeding clique-rich profiles from a greedy large clique, allowing unused vertices.
**When to use:** step 3, every candidate.
**Critical:** the `assert p >= 0 and s >= 0` in the current code **crashes** on pool instances with χ < n/2 (live in P4/P6) — replace with a bounded profile enumeration, never an assert (PITFALLS 4, 10.3). Preserve the determinism-sensitive `tuple(conf)[rng.randrange(len(conf))]` idiom byte-for-byte (module is ruff-excluded in `pyproject.toml:35`).

### Pattern 3: Append-only facts, derived statuses (VRF-03)
**What:** Corpus stores immutable certificates (facts). Instance status is a **pure function** of (corpus records + results-log events), computed on read. A RESISTANT→KILLED transition after a longer budget appends a new log event + (on a kill) a new certificate; it **never edits** a stored record.
**Why:** the store is already append-only + hash-chained (`store.py`), so this is enforced by construction — the `status` view must only ever READ.

### Pattern 4: Two stores, two contracts
| | Certificate corpus (`data/corpus/…json`) | Results log (new JSONL, one file per run) |
|---|---|---|
| Content | Verified facts only (existence certs; dual-backend value-facts) | EVERY event: gate-kills+reason+witness, timeouts, solver stats, disagreements, run metadata |
| Mutability | Append-only, atomic, hash-chained, verify-at-append | Append-only JSONL |
| Written when | Only on a verified model kill / SHC value-fact | Every step outcome, every candidate |

### Anti-Patterns to Avoid
- **Counting gate-kills and model-kills in one number** — a gate failure means "not in the hard regime / malformed," NOT a verified Hadwiger instance. Separate ledgers: KILLED-BY-GATE vs KILLED-BY-MODEL vs SHC-CANDIDATE vs RESISTANT (PITFALLS 10.4/10.5, 4).
- **Heuristic "not found" → RESISTANT** — forbidden. Heuristic miss auto-escalates to exact (unconditional edge); only an *exact* timeout/UNKNOWN/INCUMBENT_ONLY yields RESISTANT (PITFALLS 4.1).
- **`n == 2*chi - 1` criticality** — drops even-n instances (use `nu == n//2`).
- **Reading `had₂ < χ` from one backend** — SHC-CANDIDATE requires `differential_verdict` on two equal PROVED_OPTIMAL.
- **`assert` anywhere in gate/verify/status path** — no-op under `python -O`; all guards must raise.
- **Re-appending seed-137** — it is already stored (frozen, 16-set interim, `repro/seed137.py`); the battery must not double-append (store refuses reorder, but the pipeline should route the SC1 demonstration through an in-memory record like `test_seed137_regression.py`, not a corpus write). See Runtime State note.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Max clique ω(G) for G4 | DIY Bron–Kerbosch | `nx.max_weight_clique(G, weight=None)` | Exact, tested; n≤501 trivial |
| Vertex connectivity κ (G3) | DIY max-flow | `nx.node_connectivity(G)` | Exact |
| Exact χ | anything | existing `invariants/matching.py` | Sole CHI-01-guarded path |
| had₂/had₃ solve + status honesty | new solver calls | `get_backend("cbc"/"cpsat").solve_had2/3` | Status contract already closes the incumbent-as-optimum hole |
| SHC licensing | ad-hoc `<` compare | `differential_verdict(a, b, chi)` | The SOLE licenser; halts on disagreement |
| Model verification | reuse searcher helpers | `corpus/verifier.verify_certificate` | Independent trust root; sharing logic voids it |
| Append-only persistence | new writer | `corpus/store.append_certificate` | Atomic, hash-chained, verify-at-append |
| Certificate assembly | hand dict | `schema.build_record` | Refuses `fam[:chi]` truncation; derives had₂; stamps repro/backends |
| Tutte–Berge witness | recompute | `invariants/witness.extract_witness` | Already the witness extractor |

**Key insight:** Phase 6 owns **no mathematics** — every math capability exists and is tested. The battery is an orchestrator; its only new "logic" is control flow, status derivation, logging, and the profile-general loop. Building anything mathematical from scratch here would bypass the trust root and violate the program's core discipline.

## Runtime State Inventory

> Not a rename/refactor phase, but Phase 6 introduces new persistent state and must respect existing frozen state. Recorded for planner awareness.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data (existing, frozen) | seed-137 corpus record: **16-set interim** K16 model, `method="exact ILP (CBC): had_2(G)=17"`, `omega_G=14` literal (`repro/seed137.py:35-58`). The TRUE had₂=17 17-set family exists only in the `@slow` regression test, never in the corpus (deferred to Phase 11). | Battery must NOT re-append seed-137. SC1 should demonstrate the kill via an **in-memory** record (pattern: `test_seed137_regression.py`), leaving the frozen corpus byte-untouched. |
| Stored data (unverified literal) | `omega_G=14` is a hand-carried literal; `build_record`/verifier ignore ω. Recomputed this session: ω(G)=14 (matches). | G4 must compute ω(G) live via `max_weight_clique`, not trust the stored literal. |
| New persistent state | Results-log JSONL (per run) — new file(s) under `data/` (choose a path via `paths.py`, the sole path authority). | Add a `RESULTS_LOG` path to `paths.py`; never embed a filesystem path elsewhere. |
| Build artifacts / entry point | No `[project.scripts]` in `pyproject.toml` (verified). `alpha2` console command does not exist. | Add `[project.scripts] alpha2 = "alpha2.cli:main"`; `uv sync`/editable reinstall to register the entry point. |
| Frozen modules (do not touch) | `corpus/verifier.py`, `corpus/store.py`, `corpus/schema.py`, `solvers/*`, `repro/*`, the ruff-excluded determinism modules | Consume, never edit. |

**Nothing found in:** OS-registered state (none — no schedulers/services), secrets/env vars (none — no auth surface).

## Common Pitfalls

### Pitfall 1: Gate kill-semantics contradict the seed-137 case study (the big one)
**What goes wrong:** A strict kill-on-first-failure G1–G6 gate-kills seed-137 at G3 (κ=11<16) before had₂ runs; SC1 fails and the corpus family becomes un-certifiable.
**Why it happens:** Appendix E §2 states necessary conditions on a *minimal counterexample*; the studied pools are not minimal counterexamples but must still be certified dead.
**How to avoid:** SC1 gate = hard{G1 even-n crit, G2, connectivity} + flag_only{G3-deep, G4, G5, G6}. Verified seed-137 passes the hard set.
**Warning signs:** any TFP/Cayley candidate vanishing before had₂; empty corpus after a battery run; even-n candidates dropped at criticality.

### Pitfall 2: Spanning-profile heuristic (SRCH-01)
**What goes wrong:** `solve()` cannot express non-spanning K_χ models; reports seed-137-class instances as "not found," which a sloppy runner mislabels RESISTANT.
**Why it happens:** `p=n-k; s=2k-n` + `assert 2p+s==n` encodes exactly one profile.
**How to avoid:** iterate `(p′,s′)`; and hard-wire "heuristic not found → exact solver" as an unconditional edge, never a judgment (PITFALLS 4.1).
**Warning signs:** failure rates that jump with n-parity; a searcher that cannot even *hold* the stored seed-137 model as an initial state (a good unit test).

### Pitfall 3: Incumbent-as-optimum on the impossibility side (PITFALLS 2)
**What goes wrong:** reading a timed-out CBC/CP-SAT objective as exact had₂ → false SHC-CANDIDATE.
**Why it happens:** solver APIs expose the objective regardless of proof status.
**How to avoid:** already closed — `exact_value()` raises unless PROVED_OPTIMAL; only route SHC through `differential_verdict`. Do not add new ungated objective reads.
**Warning signs:** a `method="exact"` record with no stored solver status; had₂ values that change with the time limit.

### Pitfall 4: Hidden gate prerequisite chains (PITFALLS 10.2)
**What goes wrong:** χ = n − ν is valid ONLY after triangle-free passes; running the χ/ω stages on a candidate that skipped G2 yields garbage χ and poisons everything downstream.
**How to avoid:** encode a gate DAG; expensive stages **re-assert** cheap prerequisites (`is_triangle_free` is trivial to re-run). ω(G) and κ(G) are gate INPUTS — compute χ (and ω) before the checks that consume them, so step 1/step 2 interleave rather than being strictly sequential.

### Pitfall 5: Budgets/statuses as code instead of data (PITFALLS 4.3, 8)
**What goes wrong:** hard-coded 60s vs 90s budgets (already inconsistent between `sweep.py` and `baseline.py`) make "resistance" unattributable.
**How to avoid:** per-step budgets are config, echoed into every results-log line; the status string is "NOT FOUND BY <searcher-id, budget, seed>", never "no model."

## Code Examples

### Dual-backend had₂ → verdict (the licensed kill/SHC decision)
```python
# Source: tests/test_differential.py:117-132, solvers/differential.py (verified in-repo)
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

### Verified in-memory kill record (SC1 pattern — corpus byte-untouched)
```python
# Source: tests/test_seed137_regression.py:92-119 (verified this session as the SC1 template)
from alpha2.corpus.schema import build_record, provenance_seed, make_backends
from alpha2.corpus.verifier import verify_certificate
rec = build_record(
    provenance=provenance_seed("triangle_free_process_complement", n, seed, "Bohman uniform triangle-free process"),
    H_edges=H_edges, nu_H=nu, chi_G=chi,
    model_branch_sets=[list(s) for s in outcome.family],   # FULL family, len == had_2 (>= chi)
    matching_M=M, tutte_berge_U=U, method="exact ILP (CBC): had_2(G)=17",
    omega_G=omega, verified=True, backends=backends,
)
k = verify_certificate(rec)   # trust root arbitrates; raises on any defect. k == had_2.
```

### ω(G) for G4 (networkx 3.6.1 correct API)
```python
import networkx as nx
G = nx.complement(H)                               # H built from stored/generated adj
clique, _ = nx.max_weight_clique(G, weight=None)   # NOT graph_clique_number (removed in 3.x)
omega = len(clique)                                # seed-137 => 14 (verified this session)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `nx.graph_clique_number(G)` | `len(nx.max_weight_clique(G, weight=None)[0])` | networkx 3.x | Old name raises `AttributeError` — G4 code must use the new API |
| Appendix-C `ilp_had2` ungated objective read | status-honest `ExactOutcome.exact_value()` (Phase 4/5) | in-repo | Incumbent-as-optimum hole already closed; battery must not reopen it |
| `fam[:chi]` truncation | full-family storage (`build_record` refuses short families) | Phase 2 | had₂>χ families (seed-137's 17-set) are storable |
| Spanning-only heuristic profile | profile-general `(p′,s′)` iteration | **this phase (SRCH-01)** | Fixes the seed-137-class miss |

**Deprecated/outdated:**
- Any reference to `n == 2*chi - 1` as the criticality test — superseded by `nu == n//2` (even-n fix, ROADMAP SC2).

## Validation Architecture

> nyquist_validation is enabled (`config.json workflow.nyquist_validation: true`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 (pinned `[dev]` extra) |
| Config file | `pyproject.toml [tool.pytest.ini_options]` (testpaths=tests, pythonpath=src, marker `slow`) |
| Quick run command | `./.venv/bin/python -m pytest -q -m "not slow"` |
| Full suite command | `./.venv/bin/python -m pytest -q` (207 tests collected this session; add `-m slow` for the release gate incl. seed-137 ~149s proof) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GATE-01 | ordered chain, kill-on-first-failure, witness+reason logged | unit | `pytest tests/test_gate_runner.py -x` | ❌ Wave 0 |
| GATE-01 | criticality accepts n=31 AND n=32 (`nu==n//2`) | unit | `pytest tests/test_gate_criticality.py -x` | ❌ Wave 0 |
| GATE-01 | gate outcome PASS/FAIL(witness)/ERROR; ERROR never a kill | unit | `pytest tests/test_gate_outcomes.py -x` | ❌ Wave 0 |
| GATE-02 | seed-137 passes the SC1 hard-gate set (crit+G2+conn) | unit | `pytest tests/test_gate_seed137_pass.py -x` | ❌ Wave 0 |
| GATE-03 | safe-family map screen consulted; MVP logs "screen not active" | unit | `pytest tests/test_safe_family_screen.py -x` | ❌ Wave 0 |
| SRCH-01 | non-spanning profile finds a seed-137-class K16 model the spanning profile misses | unit (may be `slow`) | `pytest tests/test_profile_general.py -x` | ❌ Wave 0 |
| SRCH-02 | instrumentation (restarts, initial-conflicts) exposed; miss never → RESISTANT | unit | `pytest tests/test_heuristic_instrumentation.py -x` | ❌ Wave 0 |
| CLI-01 | `alpha2 battery --family tfp --n 31 --seed 137` runs 7 steps end-to-end (SC1) | integration (`slow`) | `pytest tests/test_battery_seed137_e2e.py -x` | ❌ Wave 0 |
| CLI-01 | deterministic in (n,seed); per-step budgets from config | unit | `pytest tests/test_battery_determinism.py -x` | ❌ Wave 0 |
| CLI-02 | results log append-only JSONL; every terminal state + method + certref + reason + provenance | unit | `pytest tests/test_results_log.py -x` | ❌ Wave 0 |
| VRF-03 | status derived from corpus+log; transitions never edit records; RESISTANT only via exact timeout | unit | `pytest tests/test_status_views.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `./.venv/bin/python -m pytest -q -m "not slow"`
- **Per wave merge:** full non-slow suite + the new `battery`/`gate`/`status` unit tests
- **Phase gate:** full suite incl. `-m slow` green (SC1 e2e + seed-137 had₂=17 proof) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_gate_runner.py`, `test_gate_criticality.py`, `test_gate_outcomes.py`, `test_gate_seed137_pass.py` — GATE-01/02
- [ ] `tests/test_profile_general.py`, `test_heuristic_instrumentation.py` — SRCH-01/02 (include the "can the data structure even hold the D.3 model?" replay test — PITFALLS 4)
- [ ] `tests/test_battery_seed137_e2e.py` (slow), `test_battery_determinism.py`, `test_results_log.py`, `test_status_views.py` — CLI/VRF
- [ ] `python -O` canary extended over new gate/status/battery guard paths (the project's standing discipline)
- [ ] No framework install needed (pytest already pinned)

## Security Domain

> `security_enforcement` key is absent from `config.json` (treat as enabled). This is an offline research CLI with no auth/session/network surface; the applicable category is input validation.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no users/credentials) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Validate CLI args (`--family` ∈ known pools; `n` positive int; `seed` int) via argparse types; the trust root already validates all graph/model data structurally (raises, `-O`-safe) |
| V6 Cryptography | no (integrity, not secrecy) | sha256 hash-chain in `store.py` is an integrity anchor, already implemented — do not re-roll |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed graph / model input to the battery | Tampering | `verify_certificate` raises on any defect before persistence (frozen trust root) |
| Solver returning garbage under timeout read as truth | Spoofing (of a proof) | Status-honest `exact_value()` + dual-backend `differential_verdict` |
| Corpus record tamper/reorder | Tampering | Append-only hash-chain + verify-at-append (`store.py`) — reused, not rebuilt |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The gate runs **Role B** (flag-only G3-deep/G4/G5/G6) for TFP/Cayley pools; SC1 gate-pass uses the reduced hard set | GATE-02 §3 | If author wants strict Role A, seed-137 gate-kills at G3 and SC1's narrative must change to "KILLED-BY-GATE(G3:κ<χ)" — a different (still valid) outcome. **Highest-impact assumption; needs sign-off.** |
| A2 | argparse (stdlib) is the CLI framework | Standard Stack | Low — swap is mechanical if author prefers click/typer (would add a dependency) |
| A3 | B₇ is not needed for SC1 (only a G6 safe-family screen) | GATE-02 §2b | Low — B₇ confined to GATE-03 hardening |
| A4 | Results log is JSONL under a new `paths.py` entry | Architecture | Low — format is discretion; fields are constrained by CLI-02 |
| A5 | SC1 demonstrates the seed-137 kill via an in-memory record (corpus byte-untouched), not a corpus append | Runtime State | Low — mirrors the existing `@slow` regression test; a real re-append would violate the frozen corpus |
| A6 | ω(G)=14 for seed-137 is correct and G4's ω≤χ−3 fails | GATE-02 §3 | None — computed directly this session (not assumed) |

## Open Questions

1. **Gate kill-semantics for studied pools (Role A vs Role B) — THE decision.**
   - What we know: seed-137 fails strict G3/G4 (verified); the 296-cert corpus proves pools reach had₂ in practice; SC1 requires gate-pass.
   - What's unclear: whether the author intends G3-deep/G4 to hard-kill TFP/Cayley candidates (making them KILLED-BY-GATE with no certificate) or to flag them while still certifying via had₂.
   - Recommendation: build both via config; run SC1 as Role B; carry a `checkpoint:human-verify` before declaring the gate "trusted."
2. **G1 "n odd" vs even-n acceptance.**
   - Known: ROADMAP SC2 mandates even-n (n=32 passes); PITFALLS 10 gives `nu==n//2`.
   - Unclear: none for MVP — the roadmap already decided this. Note it deviates from the literal §2 G1 "n odd," which is part of the label reconciliation sign-off.
   - Recommendation: implement `nu==n//2`; flag the deviation in the reconciliation checkpoint.
3. **B₇ definition** — confirm at GATE-03 time; non-blocking for Phase 6.
4. **GATE-03 map scope for MVP** — how many safe-families to implement now vs stub. Recommendation: stub with "screen not yet active" logging (FEATURES.md:229) + the pinned family list as data; grow later.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| CPython | everything | ✓ | 3.12.x (`.venv`) | — |
| networkx | ω/κ/χ | ✓ | 3.6.1 | — |
| pulp/CBC | had₂/had₃ ref | ✓ | 3.3.2 | — |
| ortools/CP-SAT | had₂/had₃ 2nd engine | ✓ | 9.15.6755 | — |
| pytest | validation | ✓ | 8.3.4 | — |
| nauty/geng | exhaustive gen | ✗ | — | **Not needed in Phase 6** (deferred to Phase 7; battery runs over existing/generated instances) |

**Missing dependencies with no fallback:** none block Phase 6.
**Missing with fallback:** geng — intentionally out of scope this phase.

## Sources

### Primary (HIGH confidence)
- `.planning/reference/alpha2-program-source.md:627-656` — Appendix E §2 (pinned G1–G6 + safe-family list) and §4 (7-step runbook), the author's verbatim text
- In-repo source (Read this session): `search/heuristic.py`, `solvers/{backend,result,differential,cbc,cpsat}.py`, `solvers/problems/had2.py`, `corpus/{schema,store}.py`, `repro/{baseline,seed137}.py`, `invariants` signatures, `tests/test_seed137_regression.py`, `tests/test_differential.py`
- Direct computation this session (`./.venv/bin/python`): seed-137 gate invariants (κ=11, δ=16, ω=14, ω/n=0.45, nu==n//2, edge-maximal, connected) and heuristic spanning-profile MISS
- `.planning/research/ARCHITECTURE.md:257-349` — gate/pipeline/status/results-log patterns; `PITFALLS.md` Pitfalls 2, 4, 10; `REQUIREMENTS.md`, `ROADMAP.md` Phase 6

### Secondary (MEDIUM confidence)
- `.planning/research/FEATURES.md:46-54,229,297` — the "reconstructed" G1–G6 table (to be reconciled) + B₇ flag
- `.planning/research/STACK.md:287` — Chudnovsky–Seymour seagull pre-gate conditions (optional G-adjacent checks, MEDIUM on formula transcription)

### Tertiary (LOW confidence)
- None relied upon; no unverified web claims were used (all findings are in-repo or computed).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries installed/pinned; APIs exercised this session
- Architecture: HIGH — patterns are in-repo (ARCHITECTURE.md) and consistent with existing code
- GATE-02 blocker analysis: HIGH — definitions located + quoted; seed-137 gate-failure computed directly, not assumed
- Pitfalls: HIGH — drawn from the project's own PITFALLS.md and confirmed against code
- Gate kill-semantics decision (A1): the ONE item requiring author sign-off; everything else is autonomous

**Research date:** 2026-07-22
**Valid until:** ~2026-08-21 (stable; in-repo facts and pinned deps do not drift; only the author sign-off is pending)
