---
phase: 07-p0-cdm-frontier
plan: 06
subsystem: pool/cdm
tags: [cdm, adjudicate, integration, differential, dual-decision, frontier, carve-out, escalation, hadwiger, alpha2]

# Dependency graph
requires:
  - phase: 07-02
    provides: has_cdm DFS arbiter + cdm_cpsat CP-SAT cross-check (the dual deciders the runbook gates on)
  - phase: 07-03
    provides: build_cdm_record + verify_cdm_witness + append_certificate (the CDM-HOLDS trust/store leg)
  - phase: 07-04
    provides: stream_mtf + provenance_for (the 147/392/1274 instance source + SC1 provenance)
  - phase: 07-05
    provides: transfer-lemma proof + K_a⊔K_b carve-out semantics (the connected-vs-disconnected classification)
provides:
  - src/alpha2/pool/cdm/adjudicate.py — adjudicate_instance + adjudicate_batch: the per-instance CDM runbook (decode -> dual-decision gate -> verify/append -> carve-out/escalation)
  - the fully-wired CDM subsystem + the verified n=12–14 frontier (1794 stored certificates)
affects: [11-escalation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-instance CDM runbook mirrors battery/pipeline: emit/result closures + append-event logging + a release-blocking dual-decision gate (CDMCriticalDisagreement)"
    - "networkx confined to the decode/classify boundary of adjudicate.py (from_graph6_bytes/complement/is_connected); reference/verifier/store legs never see a graph object"
    - "Complement-connectivity carve-out enforced BEFORE escalation: K_a⊔K_b catalogued out-of-scope, connected-complement fail routed to the battery had₂ escalation hook"

key-files:
  created:
    - src/alpha2/pool/cdm/adjudicate.py
  modified:
    - tests/pool/cdm/test_disconnected_complement.py
    - tests/pool/cdm/test_dfs_cpsat_agree.py
    - tests/test_chi_no_estimate.py

key-decisions:
  - "adjudicate.py is the ONLY new module (besides generate.py) touching networkx, confined to decode/classify; the CHI-01 guard was extended with a pool/cdm/adjudicate.py-scoped allow-list mirroring the invariants/cliques.py scoping"
  - "The dual-decision gate is release-blocking: (has_cdm is not None) != cdm_cpsat raises CDMCriticalDisagreement (quarantine + HALT), never picks a winner (mirrors solvers/differential)"
  - "CDM corpus is intentionally gitignored runtime output (.gitignore data/corpus/*.json; only the frozen 296-corpus is negated); it exists on disk + re-verifies but is not a committed artifact"
  - "adjudicate_instance defaults its event log to paths.RESULTS_LOG; the bulk population wrote 1813 CDM events there and the transient log was removed (not a Task-2 deliverable)"

requirements-completed: [POOL-0]

# Metrics
duration: 32min
completed: 2026-07-23
---

# Phase 07 Plan 06: CDM Subsystem Integration + n=12–14 Frontier Summary

**The CDM subsystem is wired end to end and the full n=12–14 frontier is adjudicated: `adjudicate.py` decodes each MTF survivor, gates the trusted DFS reference against the CP-SAT cross-check (release-blocking on any disagreement), routes CDM-HOLDS through `verify_cdm_witness` + the dedicated corpus and CDM-FAILS through the connected-vs-disconnected carve-out — and the batch adjudicates ALL 1,813 instances with DFS≡CP-SAT everywhere (0 disagreements), 1,794 connected instances CDM-HOLDS (certificated), 19 K_a⊔K_b carve-outs, and 0 connected-complement fails — extending the verified CDM frontier past the literature's n≤11.**

## Batch Verdict (the epistemic payload)

| Quantity | Value |
|----------|-------|
| Total instances adjudicated | **1,813** (147 + 392 + 1,274 — OEIS A216783) |
| DFS≡CP-SAT agreements | **1,813 / 1,813** |
| CriticalDisagreements (release-blocking) | **0** |
| CDM-HOLDS (certificated, connected) | **1,794** (n=12: 141, n=13: 386, n=14: 1,267) |
| Disconnected K_a⊔K_b carve-outs (out-of-scope) | **19** (n=12: 6, n=13: 6, n=14: 7 = floor(n/2)) |
| **Connected-complement CDM-fails (radioactive)** | **0** (expected under Conjecture 10 — NO Hadwiger event) |
| Stored corpus records (unique) | **1,794**, chain + witness + SC1 `generation` re-verify end to end |

No CriticalDisagreement and no connected-complement CDM-fail occurred. Every connected
α=2 graph at n=12–14 has a machine-verified connected dominating matching; the verified
CDM frontier now extends past n≤11.

## Performance
- **Duration:** ~32 min (incl. two background full-batch runs; each n=14 pass is ~14 min of geng enumeration over 467M TF pre-images + per-instance DFS + CP-SAT)
- **Completed:** 2026-07-23
- **Tasks:** 2
- **Files:** 1 src created, 3 tests modified, 1 gitignored runtime corpus produced

## Accomplishments
- **`adjudicate_instance(graph6, n, *, provenance, generation, corpus_path, log_path)`** — the per-instance runbook: decode H via `from_graph6_bytes` (asserting decoded n == requested n, the V5/T-7-10 boundary), build `G = complement(H)` and `adj = list[set]`, run `has_cdm(adj,n)` (reference/arbiter) + `cdm_cpsat(adj,n)` (independent cross-check), gate on agreement, then dispatch. On CDM-HOLDS: `build_cdm_record(..., complement_connected=is_connected(G), generation=<SC1>)` → `verify_cdm_witness` (trust-root re-check) → `append_certificate`. On CDM-FAILS: `classify_cdm_fail` — disconnected (K_a⊔K_b) catalogued out-of-scope with NO escalation, connected-complement routed to the escalation hook.
- **`CDMCriticalDisagreement`** — the release-blocking dual-decision gate: `(has_cdm(...) is not None) != cdm_cpsat(...)` raises + quarantines + HALTS the batch, mirroring `solvers/differential.CriticalDisagreement` (never "best of two", never skip).
- **Escalation hook (`_escalate_connected_complement_fail`)** — a connected-complement CDM-fail routes to the existing battery (`battery.pipeline.run_candidate`'s had₂ dual-backend, run directly on the failing G), records the radioactive event, and raises `ConnectedComplementCDMFail` (quarantine + HALT); full E1/E2/E3 is deferred to Phase 11. Never fires at n≤14.
- **`adjudicate_batch(ns, res, mod)`** — drives `stream_mtf` per n, builds `provenance_for` + its SC1 `generation` sidecar per survivor, and aggregates the verdict. Populated the dedicated `paths.CDM_CORPUS` with 1,794 re-verifiable certificates.
- **networkx confinement** — adjudicate.py is the sole new networkx-touching module besides generate.py, confined to decode/classify; `grep -rnE "from (networkx|ortools)"` shows ortools only in cpsat.py; networkx (`import networkx as nx`) only in adjudicate.py.
- **Tests GREEN** — `test_disconnected_complement` (classifier + no-battery-escalation assertion), the full `test_dfs_cpsat_agree` slow batch (DFS≡CP-SAT on all 1,813 + the runbook corpus/generation/chain re-verification), and the CHI-01 guard extended for the confined CDM surface.

## Task Commits
1. **Task 1: adjudicate.py runbook — decode/dual-gate/verify+append/carve-out+escalation** — `7c19937` (feat)
2. **Task 2: full n=12–14 batch gate + CHI-01 networkx confinement for adjudicate** — `da39809` (test)

## Files Created/Modified
- `src/alpha2/pool/cdm/adjudicate.py` (created) — `adjudicate_instance`, `adjudicate_batch`, `classify_cdm_fail`, `_escalate_connected_complement_fail`, `CDMCriticalDisagreement`, `ConnectedComplementCDMFail`. networkx confined to the decode/classify boundary.
- `tests/pool/cdm/test_disconnected_complement.py` (modified) — added the full-runbook no-escalation assertion (K_a⊔K_b makes NO battery/E3 call).
- `tests/pool/cdm/test_dfs_cpsat_agree.py` (modified) — added the slow `test_full_batch_runbook_adjudicates_and_certificates` (runbook counts + corpus re-verify + SC1 generation + hash-chain).
- `tests/test_chi_no_estimate.py` (modified) — CHI-01 guard extended with the pool/cdm/adjudicate.py-scoped networkx allow-list (Rule 3 deviation, below).
- `data/corpus/cdm_certificates.json` (runtime output, **gitignored**) — 1,794 CDM certificates; chain re-verifies end to end.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CHI-01 networkx-confinement guard flagged the plan-authorized adjudicate.py networkx usage**
- **Found during:** Task 2 (full non-slow suite regression check).
- **Issue:** `tests/test_chi_no_estimate.py` AST-scans every `src/alpha2/**/*.py` and asserts each `nx.<attr>(...)` call is in a confined allow-list (base allow-list, plus a `cliques.py`-scoped clique/connectivity surface). adjudicate.py's plan-sanctioned decode/classify calls (`nx.from_graph6_bytes`, `nx.complement`, `nx.is_connected`) tripped it.
- **Fix:** Extended the guard with `CDM_ADJUDICATE_NX_ATTRS = {from_graph6_bytes, complement, is_connected}` scoped to `pool/cdm/adjudicate.py` via `_is_cdm_adjudicate_module`, exactly mirroring the existing `invariants/cliques.py` scoping. These attrs stay FORBIDDEN everywhere else — the confinement discipline is preserved, not weakened, and now recognizes the second sanctioned networkx module (07-PATTERNS.md networkx confinement).
- **Files modified:** `tests/test_chi_no_estimate.py`
- **Commit:** `da39809`

**2. [Rule 2 - Test hardening] Strengthened test_disconnected_complement with the no-escalation assertion**
- **Found during:** Task 1 (acceptance criterion: "a disconnected-complement CDM-fail makes NO call into battery/E3 — assert in the test").
- **Fix:** Added `test_disconnected_complement_makes_no_battery_escalation` which routes the K_{3,3} complement through the FULL `adjudicate_instance`, monkeypatch-spies the escalation entrypoint, and asserts it stays uncalled + verdict is the disconnected carve-out + no certificate written.
- **Files modified:** `tests/pool/cdm/test_disconnected_complement.py`
- **Commit:** `7c19937`

### Observations (not defects)

- **Event-log routing.** `adjudicate_instance` defaults its append-event log to `paths.RESULTS_LOG` (mirroring the battery runbook). The bulk population run (called without `log_path`) therefore wrote 1,813 CDM events (1,794 `cdm_holds` + 19 `disconnected_complement_carveout`) into the shared battery results log. That log is regenerable runtime output and not a Task-2 deliverable, so the transient file was removed after extracting the verdict; the corpus (the actual FACT authority) is unaffected. A future refinement could route CDM events to a dedicated CDM log to avoid mixing streams during bulk runs.
- **CDM corpus is gitignored runtime output.** `.gitignore` carries `data/corpus/*.json` with only `hadwiger_alpha2_certificates.json` negated, so `data/corpus/cdm_certificates.json` is deliberately NOT committed (it is the regenerable append-only runtime artifact; the frozen 296-corpus is the only committed corpus). It exists on disk and re-verifies end to end (acceptance "exists" satisfied); it was not force-added against the intentional ignore.
- **Tooling:** `uv` is not on this shell's PATH; verify commands ran as `.venv/bin/python -m pytest ...` (equivalent interpreter + pinned deps), matching the 07-04 execution note.

## Threat Register Compliance
- **T-7-diff (DFS≡CP-SAT disagreement silently resolved):** mitigated — `CDMCriticalDisagreement` raised on any mismatch → quarantine + HALT; 0 disagreements over all 1,813.
- **T-7-13 (disconnected-complement fail mis-escalated):** mitigated — `nx.is_connected` classification BEFORE escalation; K_a⊔K_b catalogued out-of-scope with NO battery/E3 call (asserted in test); 19 carve-outs, 0 mis-escalations.
- **T-7-10 (graph6 with n ≠ requested decoded):** mitigated — `H.number_of_nodes() != n` raises at the decode boundary before adjudication.
- **T-7-14 (miscounting the frontier):** mitigated — batch total asserted == 1,813 (per-n 147/392/1,274); corpus chain re-verifies end to end (append-only prefix-immutability + hash chain; 1,794 unique records, no doubling).
- **T-7-SC (package installs):** N/A — no new packages (networkx/ortools already pinned).

## Known Stubs
None. `adjudicate.py` is fully wired: decode, dual-decision gate, verify+append, carve-out, and the escalation hook are all live and exercised by the greened tests + the full-batch run. The escalation hook's connected-complement branch never fires at n≤14 (expected under Conjecture 10) but is real code (runs the battery had₂ dual-backend on the failing G, records + quarantines).

## Verification Results
- `pytest tests/pool/cdm/test_disconnected_complement.py tests/pool/cdm/test_dfs_cpsat_agree.py -x -q -m "not slow"` → **4 passed**.
- `pytest tests/pool/cdm/test_dfs_cpsat_agree.py -q -m slow` → **4 passed** in 1051.78s (DFS≡CP-SAT on all 1,813 across n=12/13/14 + the runbook corpus test).
- Full-batch population (runtime): total **1,813**, holds **1,794**, carve-outs **19**, connected_fails **0**, elapsed 1109s; corpus reloaded → 1,794 records re-verified (witness + hash chain + SC1 `generation` all OK); n-breakdown 141/386/1267; unique graph6 == records (no doubling); every record `complement_connected == True`.
- `pytest -q -m "not slow"` → **265 passed, 13 deselected** (no regressions; the pre-existing CHI-01 guard failure resolved by the scoped allow-list extension).
- Confinement greps: `from (networkx|ortools)` → ortools only in cpsat.py; `import networkx` → only adjudicate.py in pool/cdm/. `is_connected`, `number_of_nodes`/decoded-n assert, `has_cdm`/`cdm_cpsat`, `append_certificate`, `run_candidate`/`battery` links all present. `ruff check adjudicate.py` clean.
- Frozen 296-corpus **byte-untouched**: `data/corpus/hadwiger_alpha2_certificates.json` sha256 `7064c3ae…770fe` unchanged; `git status` clean for it and `src/alpha2/corpus/`.

## Next Phase Readiness
- The CDM subsystem is complete: generation (07-04) → dual decision (07-02) → trust/store leg (07-03) → transfer-lemma proof (07-05) → per-instance runbook + verified frontier (07-06). POOL-0 SC1 is satisfied at n=12–14.
- Phase 11 (escalation) inherits a live, wired escalation HOOK: a connected-complement CDM-fail (should it ever appear past n=14) already routes to the battery had₂ dual-backend + quarantine; full E1/E2/E3 independent reproduction is the Phase-11 build-out.
- Still pending (non-blocking, carried from 07-05): the transfer-lemma **A3 author-read** before any external connected-frontier claim; the empirical n≤11 definition gate + this 1,813-instance frontier are the standing correctness backstops.

---
*Phase: 07-p0-cdm-frontier*
*Completed: 2026-07-23*

## Self-Check: PASSED

`src/alpha2/pool/cdm/adjudicate.py` present on disk; `data/corpus/cdm_certificates.json` present (1,794 records, gitignored runtime output). Task commits `7c19937` (Task 1) and `da39809` (Task 2) present in git history. `pytest -q -m "not slow"` → 265 passed; `pytest -m slow` full batch → 4 passed (1,813 adjudicated, DFS≡CP-SAT everywhere, 0 disagreements, 0 connected-complement fails).
