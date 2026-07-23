---
phase: 07-p0-cdm-frontier
verified: 2026-07-23T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 7: P0 — CDM Frontier Verification Report

**Phase Goal:** First new science — every connected α=2 graph at n=12–14 is exactly
adjudicated for CDM, extending the literature's verified frontier past n≤11 with
per-instance certificates.
**Verified:** 2026-07-23
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `geng -ctq \| pickg -Z2` generates exactly 147/392/1,274 MTF graphs at n=12/13/14, cross-checked vs OEIS A216783 + a second route; per-instance provenance stored | ✓ VERIFIED | Live re-run: `geng -ctq 12 \| pickg -Z2 \| wc -l` = 147, n=13 = 392 (n=14 not re-run live — ~15min; asserted in `test_generation_counts.py::test_mtf_generation_counts[14-1274]`, marked `slow`, previously green per 07-04-SUMMARY). Second route: `is_edge_maximal_tf` predicate cross-check + `shortg` canonical dedup, ratified Q3→v1 in `07-04-SUMMARY.md`. Per-instance provenance: every one of the 1,794 stored certificates in `data/corpus/cdm_certificates.json` carries a top-level `generation` field `{geng_version, flags, shard, index}` — confirmed by direct inspection (`sample generation: {'geng_version': ..., 'flags': '-ctq \| pickg -Z2', 'shard': None, 'index': 2}`). |
| 2 | All 1,813 instances run exact CDM with DFS reference AND CP-SAT cross-check AGREEING on every instance; per-instance certificates enter the corpus | ✓ VERIFIED | `data/corpus/cdm_certificates.json` exists on disk (gitignored runtime artifact per `.gitignore`), contains exactly **1,794** records (n=12: 141, n=13: 386, n=14: 1,267 — matches 07-06-SUMMARY exactly). 1,813 − 1,794 = 19 disconnected K_a⊔K_b carve-outs (also matches SUMMARY: 6+6+7=19). Independently re-verified all 1,794 records through `verify_cdm_witness` in this session — all 1,794 pass with zero exceptions. The DFS≡CP-SAT full-batch slow test (`test_dfs_cpsat_agree.py -m slow`) is documented in 07-06-SUMMARY as green (0 CriticalDisagreements over 1,813) — not re-run here per task instruction (15-min runtime artifact). |
| 3 | Transfer lemma written up and proven in-repo (`docs/proofs/transfer-lemma.md`); the A3 coverage residual is discharged (not merely "assumed"), and `tests/pool/cdm/test_a3_coverage.py` exhaustively confirms every connected α=2 graph holds CDM for n≤12 | ✓ VERIFIED | Read `docs/proofs/transfer-lemma.md` in full (283 lines). §3 proves CDM edge-addition monotonicity in-repo (not merely cited). §5.1 proves "Lemma A3 (two-clique closure)" for **all n** — the single-cross-edge CDM witness for graphs whose only edge-minimal reduction is disconnected. §5.2 cites the exhaustive superset gate. Ran `tests/pool/cdm/test_a3_coverage.py -q` live (no slow-filter) in this session: **9 passed** in 48.17s — covers `n=4..11` (parametrized, exact expected-count assertions per n) AND the `slow`-marked `n=12` case (1,262,173 connected α=2 graphs), all asserting `has_cdm(...) is not None` for every connected instance. Doc's own summary table (n=4–10: 14,615; n=11: 105,065; n=12: 1,262,173, "all held CDM") matches. Git history confirms this was a genuine follow-up fix: commit `e28495d` ("exhaustive A3 coverage") + `4a60dfa` ("discharge A3 residual") land after the original 07-05 proof commit `33123f3`, and the doc's own header explicitly states the A3 residual is "now discharged" (no longer "assumed"). |
| 4 | The verified CDM frontier extends past n≤11; any CDM-less connected graph is escalated (zero should be found) | ✓ VERIFIED | Corpus inspection: `all(r['invariants']['complement_connected'] for r in data)` → **True** for all 1,794 stored certificates — every stored HOLDS record is a connected-complement instance at n∈{12,13,14}, i.e. strictly past n≤11. 07-06-SUMMARY explicitly reports "Connected-complement CDM-fails (radioactive): **0**" and "0 CriticalDisagreements" — no escalation fired (expected under Conjecture 10); the escalation hook (`_escalate_connected_complement_fail` / `ConnectedComplementCDMFail`) exists as live, exercised code in `adjudicate.py` (confirmed present, wired to `battery.pipeline.run_candidate`) but never triggers at n≤14. |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/alpha2/pool/cdm/generate.py` | geng/pickg subprocess MTF generator + provenance + sharding | ✓ VERIFIED | `stream_mtf`, `geng_version`, `count_mtf`, `provenance_for` present; `subprocess.Popen` arg lists only, no `shell=True`; live-verified 147/392 counts |
| `src/alpha2/pool/cdm/reference.py` | `has_cdm` DFS reference (stdlib, trusted) | ✓ VERIFIED | stdlib-only (no networkx/ortools imports), 0 `assert` statements (raises-only, `-O`-safe) |
| `src/alpha2/pool/cdm/cpsat.py` | `cdm_cpsat` CP-SAT cross-check | ✓ VERIFIED | sole `from ortools.sat.python import cp_model` importer in `pool/cdm/`; `num_workers=1`, `random_seed=_RANDOM_SEED=137` present |
| `src/alpha2/pool/cdm/schema.py` | `build_cdm_record` platform-agnostic schema | ✓ VERIFIED | present; corpus records carry `generation`, `invariants{n,complement_connected,cdm}`, no `canonical_platform`/CBC stamp |
| `src/alpha2/pool/cdm/verifier.py` | `verify_cdm_witness` + `VerificationError` trust leg | ✓ VERIFIED | stdlib-only, 0 asserts; independently re-ran against all 1,794 stored certificates in this session with zero failures |
| `src/alpha2/pool/cdm/store.py` | append-only CDM corpus writer | ✓ VERIFIED | writes to `paths.CDM_CORPUS`; frozen 296-corpus (`hadwiger_alpha2_certificates.json`, sha256 `7064c3ae...770fe`) confirmed byte-unchanged in this session |
| `src/alpha2/pool/cdm/adjudicate.py` | per-instance runbook + dual-decision gate + carve-out/escalation | ✓ VERIFIED | `adjudicate_instance`, `adjudicate_batch`, `classify_cdm_fail`, `CDMCriticalDisagreement`, `ConnectedComplementCDMFail` present; networkx confined here + generate.py only |
| `data/corpus/cdm_certificates.json` | populated CDM corpus (runtime, gitignored) | ✓ VERIFIED | exists on disk, 1,794 records, all re-verify via `verify_cdm_witness` (checked live this session) |
| `docs/proofs/transfer-lemma.md` | in-repo transfer-lemma proof + A3 discharge | ✓ VERIFIED | 283 lines; monotonicity proof, Lemma 2.5 citation, K_a⊔K_b carve-out, §5 A3-discharge (proven lemma + exhaustive gate) all present |
| `tests/pool/cdm/test_a3_coverage.py` | exhaustive n≤12 A3 coverage gate | ✓ VERIFIED | 164 lines; ran live, 9/9 passed (n=4..11 + slow n=12) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `adjudicate.py` | `has_cdm` + `cdm_cpsat` | dual-decision gate | ✓ WIRED | `CDMCriticalDisagreement` raised on disagreement; grep confirms both calls present |
| `adjudicate.py` | `verify_cdm_witness` + `store.append_certificate` | CDM-HOLDS existence path | ✓ WIRED | present; live re-verification of all 1,794 corpus records confirms the wiring produces valid, independently-checkable certificates |
| `adjudicate.py` | `battery.pipeline.run_candidate` | connected-complement CDM-fail escalation hook | ✓ WIRED (never triggered) | code path present and exercised by tests (`test_disconnected_complement_makes_no_battery_escalation` asserts the K_a⊔K_b carve-out path does NOT call it); never fires on the real batch since 0 connected-complement fails occurred |
| `docs/proofs/transfer-lemma.md` | `tests/pool/cdm/test_transfer_lemma.py` + `test_a3_coverage.py` | executable predicate backing | ✓ WIRED | doc explicitly names both files as "Executable backing"; both ran green in this session |
| `src/alpha2/paths.py` | `CDM_CORPUS` constant | additive, non-destructive | ✓ WIRED | `CORPUS` (frozen) and `CDM_CORPUS` (new) both present and distinct at paths.py:12,20 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| geng/pickg produces exact OEIS counts at n=12,13 | `geng -ctq 12\|pickg -Z2\|wc -l`; n=13 | 147; 392 | ✓ PASS |
| Fast suite green | `.venv/bin/python -m pytest -q -m "not slow"` | 273 passed, 14 deselected | ✓ PASS |
| CDM test tree (fast tier) green | `.venv/bin/python -m pytest tests/pool/cdm -q -m "not slow"` | 34 passed, 6 deselected | ✓ PASS |
| A3 coverage gate (incl. its own slow n=12 tier) | `.venv/bin/python -m pytest tests/pool/cdm/test_a3_coverage.py -q` | 9 passed in 48.17s | ✓ PASS |
| Corpus independently re-verifies | in-process loop calling `verify_cdm_witness` on all 1,794 records | 1,794/1,794 pass, 0 exceptions | ✓ PASS |
| Frozen 296-corpus untouched | `shasum -a 256 data/corpus/hadwiger_alpha2_certificates.json` | `7064c3ae...770fe` (matches 07-06-SUMMARY claim) | ✓ PASS |
| n=14 generation count (1,274) and full slow DFS≡CP-SAT batch | not re-run (per task instruction — ~15 min runtime artifact) | documented green in 07-04/07-06 SUMMARY | ? SKIP (accepted per instruction) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|--------------|--------|----------|
| POOL-0 | 07-01..07-06 (all 6 plans) | P0 CDM frontier — exhaustively generate 1,813 MTF graphs at n=12–14, exact CDM check (DFS+CP-SAT), transfer lemma proven in-repo, verified frontier extended past n≤11 | ✓ SATISFIED | All 4 truths above verified; REQUIREMENTS.md marks POOL-0 "Complete" for Phase 7; no orphaned requirement IDs found mapped to Phase 7 beyond POOL-0 |

### Anti-Patterns Found

None. Grepped all `src/alpha2/pool/cdm/*.py` for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER|not yet implemented|coming soon` — zero matches. `reference.py` and `verifier.py` both have 0 `assert` statements (raises-only discipline, required for `python -O` safety, independently confirmed via grep).

### Human Verification Required

None required for phase-goal achievement. One informational note, not a blocker:

- `STATE.md` "Pending Todos" still lists "⏳ AUTHOR READ PENDING (non-blocking): transfer-lemma A3" as open, but the codebase evidence (commits `e28495d`/`4a60dfa`, `docs/proofs/transfer-lemma.md` §5, `test_a3_coverage.py` passing) shows this residual was subsequently discharged by proof (§5.1, all n) plus exhaustive verification (§5.2, n≤12). This is stale documentation bookkeeping in `STATE.md`, not a gap in the phase's delivered artifacts — the task brief for this verification explicitly names the A3 fix as the expected state to confirm, which it does. Recommend updating `STATE.md`'s Pending Todos to reflect the discharge, but this does not block Phase 7 passing.

### Gaps Summary

No gaps. All four ROADMAP Success Criteria for Phase 7 are independently verified against the live codebase, not merely SUMMARY claims:

1. Generation counts reproduced live (147, 392) plus documented-and-previously-green slow n=14 (1,274); second-route cross-check and per-instance provenance both present and inspected directly in the corpus.
2. The corpus contains exactly the expected 1,794 connected-complement certificates (1,813 − 19 disconnected carve-outs); every one independently re-verifies via `verify_cdm_witness` in this session (fresh execution, not trusted from SUMMARY).
3. The transfer lemma is proven in-repo, including a genuine follow-up fix (commits `e28495d`, `4a60dfa`) that discharges the A3 residual with both a general proof (§5.1) and an exhaustive `n≤12` gate (`test_a3_coverage.py`), which was executed live in this session (9/9 passed, including the slow n=12 tier).
4. Frontier extends past n≤11 (all 1,794 stored records have `complement_connected=True` at n∈{12,13,14}); zero connected CDM-less graphs were found, so the escalation hook never fired — confirmed present and wired, not merely claimed.

The frozen 296-instance had₂ corpus remains byte-unchanged (SHA256 verified), preserving trust-root isolation. The fast test suite (273 passed) and the full CDM fast tier (34 passed) are green.

---

*Verified: 2026-07-23*
*Verifier: Claude (gsd-verifier)*
