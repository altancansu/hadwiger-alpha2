---
phase: 8
slug: p1-p2-seeded-families-at-scale
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-23
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 08-RESEARCH.md § Validation Architecture + the 7 plan test contracts.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (+ pytest-xdist for the instance-level grid fan-out) — already the repo's suite |
| **Config file** | `pyproject.toml` (existing `[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/pool/sumfree -x -q -m "not slow"` |
| **Full suite command** | `uv run pytest` (frozen 296-corpus reproduction + CDM batch + sumfree + `python -O` canary) |
| **Estimated runtime** | quick ~seconds (small-Γ fixtures, honesty gate, RED/GREEN unit modules); full n=31–500 sweep + n≈1001–2001 showpieces are `@pytest.mark.slow`, minutes under `-n auto` |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/pool/sumfree -x -q -m "not slow"`
- **After every plan wave:** full suite incl. the frozen 296-corpus reproduction guard
  (`uv run pytest tests/test_reproduction_contract.py tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_corpus_r3.py tests/test_seed137_regression.py -q -m "not slow"`) — the det-budget edit (08-02) is additive and MUST
  leave the reproduction byte-identical; the CBC `maxNodes` cap defaults to `None` (unbounded) so the
  reproduction path is untouched.
- **Before `/gsd:verify-work`:** full suite green, **including the frozen 296-corpus + `python -O`
  verifier canary untouched**.
- **Max feedback latency:** quick loop < ~30 s (all non-slow sumfree unit modules).

### Determinism sampling note (Locked Decision 3 — reproducibility invariant)

Every recorded `had_k < χ` / RESISTANT verdict must be a deterministic function of `(n, seed)`,
independent of machine speed or core count. Both exact backends are bounded by a **deterministic**
budget for any recorded verdict — CP-SAT by `max_deterministic_time` (`SolveParams.det_time`) and CBC
by a **node-count cap** (`SolveParams.det_nodes` → CBC `-maxNodes`, deterministic under
`threads=1`). A wall-clock cutoff (`time_limit_s`) is **forbidden** on any path feeding a reported
verdict. `test_determinism` (08-04) is the sampler: two runs of a fixed g>0 / RESISTANT instance under
the deterministic budget must agree; it may be marked `@pytest.mark.slow`.

---

## Phase Requirements → Test Map

(Task IDs bind at planning time; rows below are the POOL-1/POOL-2 behaviors the plans must cover.)

| Req ID | Behavior | Plan(s) | Threat Ref | Test Type | Automated Command | File Exists | Status |
|--------|----------|---------|------------|-----------|-------------------|-------------|--------|
| POOL-2 | sum-free `S` is sum-free + symmetric + maximal (verify_sumfree_maximal net) | 08-01 (RED) / 08-02 (GREEN) | T-8-14 | unit | `uv run pytest tests/pool/sumfree/test_generate.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | `H = Cay(Γ,S)` triangle-free ⇒ `G = H̄` is α=2 | 08-01 / 08-02 | — | unit | `uv run pytest tests/pool/sumfree/test_generate.py::test_triangle_free -x` | ❌ W0 | ⬜ pending |
| POOL-2 | Green–Ruzsa/Andrásfai sizes: Z_31=10, Z_53=18 (keyed on arithmetic condition, A1) | 08-01 / 08-02 | — | unit | `uv run pytest tests/pool/sumfree/test_structured.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | canonical dedup collapses isomorphic (Γ,S); WL-hash never the key | 08-01 / 08-02 | T-8-06 | unit | `uv run pytest tests/pool/sumfree/test_dedup.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | RNG v2 sha256 per-stage subseeds; descriptor rebuild byte-exact | 08-01 / 08-02 | — | unit | `uv run pytest tests/pool/sumfree/test_rng_v2.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | g(G) record schema round-trips; carries provenance + honesty statement | 08-01 / 08-03 | T-8-01 | unit | `uv run pytest tests/pool/sumfree/test_schema.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | g(G) certificate states ONLY "no K_χ minor branch≤3"; forbids "counterexample"/"had(G) <" | 08-01 / 08-03 / 08-04 | T-8-01 | unit | `uv run pytest tests/pool/sumfree/test_screen.py::test_certificate_honesty -x` | ❌ W0 | ⬜ pending |
| POOL-2 | stdlib g(G) verifier re-derives χ = n−ν, fails closed under `python -O` | 08-03 | T-8-09 | unit | `uv run pytest tests/pool/sumfree/test_screen.py -x -k "verify or honesty"` | ❌ W0 | ⬜ pending |
| POOL-2 | g(G) store append-only + verify-at-append + hash-chained, isolated from frozen corpora | 08-01 / 08-03 | T-8-08 | integration | `uv run pytest tests/pool/sumfree/test_store.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | had₂→had₃ tiering: KILLED(g≤0 verified) / SHC-CANDIDATE(g>0 proven bound) / RESISTANT; heuristic miss ≠ g>0 | 08-04 | T-8-13, T-8-15 | integration | `uv run pytest tests/pool/sumfree/test_screen.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | recorded verdict deterministic across two runs (CP-SAT det_time + CBC det_nodes, num_workers=1/threads=1) | 08-04 | T-8-07 | integration (slow) | `uv run pytest tests/pool/sumfree/test_determinism.py -x` | ❌ W0 | ⬜ pending |
| POOL-2 | ILP optimality frontier MEASURED per-n under a deterministic budget (A4) | 08-05 | T-8-07, T-8-10 | integration | `uv run pytest tests/pool/sumfree/test_frontier.py -x` | ❌ W0 | ⬜ pending |
| POOL-1 | n=31/32 critical sweep exact had₂ matches corpus lineage | 08-07 | — | integration | `uv run pytest tests/pool/sumfree/test_p1_sweep.py -x` | ❌ W0 | ⬜ pending |
| POOL-1 | n≈1001 showpiece heuristic HIT verified by trust root; MISS → RESISTANT (never a result) | 08-07 | T-8-11 | integration (slow) | `uv run pytest tests/pool/sumfree/test_showpiece.py -x -m slow` | ❌ W0 | ⬜ pending |
| POOL-2 | frozen `generators/cayley.py` untouched; 296-corpus reproduction still green (det-budget additive) | 08-02 | T-8-02 | regression | `uv run pytest tests/test_reproduction_contract.py tests/test_corpus_r1.py tests/test_corpus_r2.py tests/test_corpus_r3.py tests/test_seed137_regression.py -q -m "not slow"` | ✅ (existing CI) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 (08-01) lands the full executable RED contract before any implementation wave. All 13 test
modules + conftest must collect clean and fail on the missing `alpha2.pool.sumfree.*` modules:

- [ ] `tests/pool/sumfree/conftest.py` — shared small-Γ fixtures (Z_31, Z_53, Z_3×Z_3), a valid
      KILLED(g≤0) g(G) record, an honesty-CANARY g>0 record
- [ ] `tests/pool/sumfree/test_group.py` — abelian add/neg/enumerate, factor validation + n≤500 bound
- [ ] `tests/pool/sumfree/test_generate.py` — sum-free/symmetric/maximal + triangle-free (POOL-2)
- [ ] `tests/pool/sumfree/test_structured.py` — Green–Ruzsa/Andrásfai sizes keyed on arithmetic condition (POOL-2)
- [ ] `tests/pool/sumfree/test_dedup.py` — canonical dedup + WL-hash-forbidden guard (POOL-2)
- [ ] `tests/pool/sumfree/test_rng_v2.py` — sha256 subseeds + descriptor rebuild (POOL-1/2)
- [ ] `tests/pool/sumfree/test_schema.py` — g(G) record round-trip + honesty statement (POOL-2)
- [ ] `tests/pool/sumfree/test_store.py` — append-only verify-at-append hash chain (POOL-2)
- [ ] `tests/pool/sumfree/test_screen.py` — g(G) + certificate-honesty gate (the radioactive one) (POOL-2)
- [ ] `tests/pool/sumfree/test_determinism.py` — deterministic-budget verdict stability across two runs (POOL-1/2)
- [ ] `tests/pool/sumfree/test_frontier.py` — per-n PROVED/UNPROVED under a deterministic budget (POOL-2)
- [ ] `tests/pool/sumfree/test_p1_sweep.py`, `test_showpiece.py` — P1 secondary (POOL-1)
- [ ] Slow tests (n≥14 / large-n / two-run determinism) markable `@pytest.mark.slow` and shardable for CI fan-out

**Baseline:** `uv run pytest tests/pool/sumfree -q -m "not slow"` is RED (sumfree failures) while
`uv run pytest -q --ignore=tests/pool/sumfree -m "not slow"` stays green (no regression).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Structured-vs-random g-vs-\|Γ\| curve reads as falsified / resistant-tail / inconclusive; every g>0 cert is honest | POOL-2 | Research judgment on the plot outcome — a RESISTANT tail is a screen, not a break (E3 + referee gate the word "break", LD-4) | 08-06 `checkpoint:human-verify`: run the **full** odd \|Γ\|=31–~500 sweep (`--order-max 500`; `--order-max 151` is a fast pre-check only), inspect `data/results/sumfree_sweep.jsonl` per family, spot-check one g>0 certificate for the honest literal, confirm two-run determinism |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 (08-01) covers all MISSING references (13 modules + conftest)
- [x] No watch-mode flags
- [x] Feedback latency < 30s (quick loop)
- [x] Reproducibility invariant sampled: `test_determinism` guards CP-SAT det_time + CBC det_nodes determinism
- [x] Frozen 296-corpus reproduction guard preserved (det-budget edit additive)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-23 (generated during plan revision to close the Dimension-8 validation gate).
