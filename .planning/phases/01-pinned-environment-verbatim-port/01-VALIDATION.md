---
phase: 1
slug: pinned-environment-verbatim-port
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-21
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `01-RESEARCH.md` § Validation Architecture (values live-verified on CPython 3.12.13 + networkx 3.6.1, 2026-07-21).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (add via `uv add --dev pytest ruff`) |
| **Config file** | none yet — Wave 0 creates `[tool.pytest.ini_options]` in `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_fingerprint.py -x` |
| **Full suite command** | `uv run pytest -q` |
| **Estimated runtime** | ~2 seconds (networkx-only; sub-second fingerprint) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_fingerprint.py -x`
- **After every plan wave:** Run `uv run pytest -q`
- **Before `/gsd:verify-work`:** Full suite green **and** `uv sync` core smoke green
- **Max feedback latency:** ~2 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| pkg-scaffold | 01 | 0 | ENV-01 | T-1 supply-chain drift | `uv.lock` pins exact versions + interpreter patch | smoke | `uv sync && uv run python -c "import sys;assert sys.version.split()[0]=='3.12.13'"` | ❌ W0 | ⬜ pending |
| lib-entry-split | 01 | 1 | ENV-02 | — | verbatim bodies relocated, set-iteration order preserved | unit | `uv run pytest tests/test_fingerprint.py::test_stored_model_reverifies -x` | ❌ W0 | ⬜ pending |
| fingerprint-invariants | 01 | 1 | ENV-03 | T-3 self-cert golden | 131/15/16/tf/maxTF asserted from Appendix D (not our output) | unit | `uv run pytest tests/test_fingerprint.py::test_invariants -x` | ❌ W0 | ⬜ pending |
| fingerprint-golden | 01 | 1 | ENV-03 | T-2 cross-version drift | `sha256(H_edges)==3c953d90…41e2` | unit (golden) | `uv run pytest tests/test_fingerprint.py::test_golden_hash -x` | ❌ W0 | ⬜ pending |
| chi-no-estimate | 01 | 1 | CHI-01 | — | χ=n−ν only; no coloring/estimate call in `src/` | static/unit | `uv run pytest tests/test_chi_no_estimate.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` + `.python-version` (3.12.13) + committed `uv.lock` — packaging scaffold (ENV-01)
- [ ] `tests/test_fingerprint.py` — invariants + golden hash + stored-model reverify + heuristic replay (ENV-02/ENV-03)
- [ ] `tests/test_chi_no_estimate.py` — static guard that χ is only `n−ν` (CHI-01)
- [ ] `data/manifests/fingerprint.json` — golden fixture; pre-validated hash `3c953d90…41e2` available from research
- [ ] `uv add --dev pytest ruff` — framework install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| pynauty builds from sdist on macOS arm64 | ENV-01 (extra) | Needs Xcode CLT; PyPI ships only Linux cp312 wheel | `uv sync --extra nauty` (run in CI on Linux; on mac requires CLT) |
| pulp bundled CBC solves under Rosetta 2 | ENV-01 | arm64 runs osx/i64 binary via Rosetta; not asserted by fingerprint path | `uv run python -c "import pulp;..."` — one-time install smoke |

*All Phase-1 acceptance-critical behaviors (fingerprint, χ, lock reproduction) have automated verification. Only the soft "everything installs" gate has manual/CI-only steps.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
