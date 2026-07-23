---
phase: 7
slug: p0-cdm-frontier
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-22
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 07-RESEARCH.md § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (+ pytest-xdist for n=14 fan-out) — already the repo's suite |
| **Config file** | `pyproject.toml` (existing `[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/pool/cdm -x -q` |
| **Full suite command** | `pytest -q` (frozen 296-corpus regression + CDM batch) |
| **Estimated runtime** | quick ~seconds (n≤13 counts, verifier mutants, n≤11 regression); full n=14 batch minutes under `-n auto` |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/pool/cdm -x -q`
- **After every plan wave:** full n=12–14 adjudication batch under xdist (`-n auto`), asserting all 1,813 HOLD and DFS ≡ CP-SAT everywhere
- **Before `/gsd:verify-work`:** full suite green, **including the frozen 296-corpus regression untouched**
- **Max feedback latency:** quick loop < ~30 s

---

## Per-Requirement Verification Map

(Task IDs bind at planning time; rows below are the POOL-0 behaviors the plan must cover.)

| Behavior | Requirement | Threat Ref | Test Type | Automated Command | File Exists | Status |
|----------|-------------|------------|-----------|-------------------|-------------|--------|
| `geng -ctq \| pickg -Z2` yields exactly 147/392/1,274 at n=12/13/14 | POOL-0 | T-7-gen | integration | `pytest tests/pool/cdm/test_generation_counts.py -x` | ❌ W0 | ⬜ pending |
| Generation cross-checks OEIS A216783 + a second route | POOL-0 | T-7-gen | integration | `pytest tests/pool/cdm/test_generation_crosscheck.py -x` | ❌ W0 | ⬜ pending |
| DFS `has_cdm` reproduces CLWY n≤11 all-CDM (definition regression, A1) | POOL-0 | — | unit | `pytest tests/pool/cdm/test_cdm_n_le_11.py -x` | ❌ W0 | ⬜ pending |
| DFS ≡ CP-SAT on all 1,813 (disagreement release-blocking) | POOL-0 | T-7-diff | integration (slow) | `pytest tests/pool/cdm/test_dfs_cpsat_agree.py -x` | ❌ W0 | ⬜ pending |
| `verify_cdm_witness` accepts valid M, rejects mutants | POOL-0 | — | unit | `pytest tests/pool/cdm/test_cdm_verifier.py -x` | ❌ W0 | ⬜ pending |
| `verify_cdm_witness` fails closed under `python -O` (no asserts) | POOL-0 | — | unit | `pytest tests/pool/cdm/test_cdm_verifier_dash_O.py -x` (run under `-O`) | ❌ W0 | ⬜ pending |
| Transfer-lemma predicates: Lemma 2.5 equiv + CDM edge-addition monotonicity | POOL-0 | — | property (hypothesis) | `pytest tests/pool/cdm/test_transfer_lemma.py -x` | ❌ W0 | ⬜ pending |
| Disconnected-complement (K_a⊔K_b) classified, not mis-escalated | POOL-0 | — | unit | `pytest tests/pool/cdm/test_disconnected_complement.py -x` | ❌ W0 | ⬜ pending |
| CDM store append-only + witness-verified-at-append | POOL-0 | — | integration | `pytest tests/pool/cdm/test_cdm_store.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/pool/cdm/conftest.py` — fixtures: small α=2 graphs (C₅, K_a⊔K_b, hand CDM witnesses), a cached n≤11 MTF sample
- [ ] `tests/pool/cdm/test_cdm_n_le_11.py` — the A1 definition regression (reproduce CLWY n≤11). **Highest-priority gate** — validates the CDM definition before any new-science claim
- [ ] `tests/pool/cdm/test_generation_counts.py` + `test_generation_crosscheck.py` — 147/392/1,274 + OEIS + second route
- [ ] `tests/pool/cdm/test_cdm_verifier*.py` — mutant suite + `-O` canary (trust-root discipline)
- [ ] The n=14 full-batch test markable `@pytest.mark.slow` and shardable (res/mod) for CI fan-out

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Transfer-lemma write-up is mathematically sound (connected-complement carve-out) | POOL-0 | Prose proof — needs human/author read (Open Q1) | Review `docs/` transfer-lemma note against CLWY Lemma 2.5 + monotonicity argument |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-22 (plan-checker VERIFICATION PASSED, revision iteration 2)
