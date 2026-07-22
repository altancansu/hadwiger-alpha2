---
phase: 2
slug: trust-root-corpus-schema
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-21
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `02-RESEARCH.md` § Validation Architecture (verifier `-O` fix + Tutte–Berge witness live-verified on CPython 3.12.13 + networkx 3.6.1, 2026-07-21).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing `tests/` suite from Phase 1) |
| **Config file** | `pyproject.toml [tool.pytest.ini_options]` (existing) |
| **Quick run command** | `uv run pytest tests/test_verifier_mutants.py tests/test_tutte_berge.py tests/test_verifier_dash_O.py -x` |
| **Full suite command** | `uv run pytest -q` (plus the standalone `python -O` subprocess job) |
| **Estimated runtime** | ~2–3 seconds (stdlib verifier + one subprocess) |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_verifier_mutants.py tests/test_tutte_berge.py tests/test_verifier_dash_O.py -x`
- **After every plan wave:** `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite green **including** the `-O` fail-closed job
- **Max feedback latency:** ~3 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| verifier-raises | 01 | 1 | VRF-01 | trust-root -O strip | real checks raise `VerificationError`; zero asserts | unit | `uv run pytest tests/test_verifier_mutants.py -x` | ❌ W0 | ⬜ pending |
| verifier-dash-O | 01 | 1 | VRF-01 | trust-root -O strip | fails closed under `python -O` on known-bad model | subprocess | `uv run pytest tests/test_verifier_dash_O.py -x` | ❌ W0 | ⬜ pending |
| verifier-isolation | 01 | 1 | VRF-01 | logic-sharing | `corpus/verifier.py` imports only stdlib (own is_conflict) | unit (AST) | `uv run pytest tests/test_verifier_isolation.py -x` | ❌ W0 | ⬜ pending |
| tutte-berge | 01 | 1 | CHI-02 | matching-lib trust | M+U pins χ=n−ν both directions (seed 1 & 137, U=∅); general U≠∅ path exercised | unit | `uv run pytest tests/test_tutte_berge.py -x` | ❌ W0 | ⬜ pending |
| schema-roundtrip | 02 | 2 | VRF-02 | truncated family | v1 round-trips D.2 & D.3; FULL family never fam[:χ]; sha256==golden | unit | `uv run pytest tests/test_schema_roundtrip.py -x` | ❌ W0 | ⬜ pending |
| store-append-only | 02 | 2 | VRF-02 | record mutation | atomic write (os.replace) + prefix-immutability guard refuses edits | unit | `uv run pytest tests/test_store_append_only.py -x` | ❌ W0 | ⬜ pending |
| reproduction-contract | 02 | 2 | ENV-05 | version drift | cert carries reproduction.kind + backend/platform stamps; Linux x86_64 canonical | unit | `uv run pytest tests/test_reproduction_contract.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_verifier_mutants.py` — VRF-01 crit-2 (5 mutants: overlap / H-edge pair / missing cross-adj / truncated / wrong χ, each must raise)
- [ ] `tests/test_verifier_dash_O.py` — VRF-01 crit-1 (subprocess `python -O`; assert `__debug__ is False` then require `VerificationError`)
- [ ] `tests/test_verifier_isolation.py` — import-boundary (stdlib-only, no toolkit imports)
- [ ] `tests/test_tutte_berge.py` — CHI-02 (seed 1 & 137 U=∅ + a synthetic U≠∅ general-path case)
- [ ] `tests/test_schema_roundtrip.py` — VRF-02 (D.2 + D.3 16-set + synthetic params/graph6 shapes)
- [ ] `tests/test_store_append_only.py` — VRF-02 (atomicity + append-only guard)
- [ ] `tests/test_reproduction_contract.py` — ENV-05
- [ ] Source: `src/alpha2/corpus/{__init__,verifier,schema,store}.py` + emission-time `extract_witness` helper

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI `-O` job wired into pipeline | VRF-01 / ENV-06 | CI config not runnable inside the unit suite | Confirm a CI step runs `python -O -m pytest` (or the standalone `-O` script) on Linux x86_64 |

*The `-O` fail-closed behavior itself IS automated (subprocess test); only the CI wiring is manual/config. All acceptance-critical verifier/schema/witness behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
