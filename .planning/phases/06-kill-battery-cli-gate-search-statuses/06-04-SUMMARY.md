---
phase: 06-kill-battery-cli-gate-search-statuses
plan: 04
subsystem: status-and-gate
tags: [status, derived-view, vrf-03, gate-03, safe-families, read-only, append-only, role-b, raises-only]
requires:
  - corpus/manifest.py (manifest_key — the frozen A5 instance-key scheme reused by the view)
  - corpus/schema.py + corpus/store.py (immutable, hash-chained record shape the view READS)
  - battery/log.py + battery/pipeline.py (Plan 06-02 — the append-only results-log event stream + terminal states)
  - gate/runner.py + gate/checks.py (Plan 06-01 — the D-01 Role B chain; g6 hook wired here)
  - paths.CORPUS + paths.RESULTS_LOG (sole path authority)
provides:
  - status/views.py (build_status_view / load_status_view / summarize — derived KILLED/SHC-CANDIDATE/RESISTANT)
  - gate/safe_families.py (SAFE_FAMILIES family->citation map + screen_safe_families membership screen)
  - cli.py `alpha2 status` subcommand (read-only derived-view printer)
  - gate/checks.py g6_safe_families (now consults the screen, flag_only Role B)
affects:
  - Plan 06-05 (gate-trust sign-off consumes the safe-family map; B7-free screen deferred here)
  - Phase 10 P4/P5 (the settled/open safe-family map absorbs results as classes settle — GATE-03 growth)
  - future status consumers (queue dashboards read the derived view; RESISTANT queue feeds Phase 3)
tech-stack:
  added: []
  patterns:
    - derived read-only view over immutable facts (manifest.build_manifest analog; VRF-03)
    - append-only transition by precedence — a stronger fact supersedes a weaker one, never edits a record
    - RESISTANT gated on an EXACT-method timeout marker (spoof guard refuses non-exact RESISTANT)
    - settled/open family->citation map as DATA (stub-and-grow; frozen verbatim from §2, never invented)
    - screen consulted flag_only (D-01 Role B) — a safe hit is a cited flag, never a hard-kill
    - raises-only, 0 asserts, networkx NOT imported in gate/safe_families (confinement preserved)
key-files:
  created:
    - src/alpha2/status/__init__.py
    - src/alpha2/status/views.py
    - src/alpha2/gate/safe_families.py
    - tests/test_status_views.py
    - tests/test_safe_family_screen.py
  modified:
    - src/alpha2/cli.py
    - src/alpha2/gate/checks.py
decisions:
  - Status is a PURE function of (immutable corpus records + append-only log events); build_status_view deep-copies provenance so it never aliases/mutates an input — the RESISTANT->KILLED transition recomputes to KILLED by PRECEDENCE, leaving the stored RESISTANT event byte-identical
  - RESISTANT is derivable ONLY from a results-log event whose method records an EXACT-method timeout; a heuristic-miss (non-terminal) event yields NO status and a RESISTANT terminal_state carrying a non-exact method is REFUSED (raise) — T-06-15 test-locked
  - SAFE_FAMILIES frozen VERBATIM (ASCII-normalized) from §2 line 644: explicit §2 authors where given (Reed-Seymour / Chudnovsky-Fradkin / PST / Blasiak / Furedi-Gyarfas-Simonyi;Chen-Deng), the Dec-2025/PST §2 provenance where §2 names none — never a fabricated author
  - MVP implements ONE cheap/decidable membership test (C5-free via a stdlib induced-C5 scan over G=complement(H), no networkx); every other family screens as "screen not yet active" — never a false safe verdict; B7-free screen DEFERRED to Plan 05 (author sign-off)
  - g6_safe_families consults the screen flag_only (D-01 Role B): a cited safe hit is a flag on the record, never a hard-kill — seed-137 keeps passing the hard-gate
metrics:
  duration: ~16min
  tasks: 3
  files: 7
  completed: 2026-07-22
requirements: [VRF-03, GATE-03]
---

# Phase 6 Plan 04: Derived Statuses (VRF-03) + G5/G6 Safe-Family Map (GATE-03) Summary

Two hardening deliverables off the SC1 critical path. **VRF-03**: KILLED / SHC-CANDIDATE /
RESISTANT is now a READ-ONLY DERIVED VIEW — `build_status_view(corpus_records, log_events)`
is a pure function of the immutable, hash-chained corpus + the append-only JSONL results log,
computed on read, keyed by the frozen A5 `manifest_key` scheme. A RESISTANT→KILLED transition
recomputes to KILLED by *appending* a stronger fact (precedence), leaving the earlier stored
RESISTANT event byte-identical; RESISTANT is derivable ONLY from an exact-method timeout, a
heuristic miss NEVER. **GATE-03**: `gate/safe_families.py` freezes the enumerated, CITED
proven-safe family list verbatim from Appendix E §2 line 644 into a maintained family→citation
map, with an MVP C5-free membership screen the gate consults flag_only (Role B) — proven
terrain is flagged, never re-hunted, and deferred families log "screen not yet active" rather
than falsely killing.

## What Was Built

**Task 1 — Wave-0 derived-status + safe-family tests** (`af5b167`)
- `tests/test_status_views.py` — synthetic in-memory corpus records + log events assert:
  KILLED from a verified corpus record, SHC-CANDIDATE from a differential value-fact event,
  RESISTANT ONLY from an exact-timeout event; the explicit **miss≠RESISTANT** invariant (a
  non-terminal HEURISTIC-MISS event yields no status); the **spoof guard** (a RESISTANT
  terminal_state without an exact method raises); and the **append-only transition** (a later
  KILL supersedes RESISTANT while the stored RESISTANT event stays byte-identical — `copy`
  snapshot compare).
- `tests/test_safe_family_screen.py` — asserts every mapped family carries a non-empty
  citation, the pinned §2 families are present by name with faithful citations, an implemented
  screen returns a cited C5-free hit (G=K5), an unimplemented family screens as "screen not yet
  active", a C5-rich graph is NOT a false C5-free member, and no B7 family is registered.
- Under-test imports deferred INSIDE each test so both files `--collect-only` before Tasks 2-3
  land the modules (Plan 06-02 Wave-0 convention). 14 tests collect.

**Task 2 — `status/views.py` derived statuses + `alpha2 status`** (`d7e9a79`)
- `status/__init__.py` (imports no solver libs) + `status/views.py`:
  `build_status_view(corpus_records, log_events)` folds verified corpus certificates (→KILLED)
  then results-log events by append order, a stronger fact superseding a weaker one via a
  `_PRECEDENCE` map (KILLED>SHC-CANDIDATE>KILLED-BY-GATE>RESISTANT>QUARANTINED). Each derived
  fact `{status, method, certificate_ref, reason, seed, provenance}` **deep-copies** provenance
  so the view never aliases/mutates an input. RESISTANT is gated on `_is_exact_method`; a
  non-exact RESISTANT event raises. Instance keys reuse `corpus.manifest.manifest_key`.
- `load_status_view()` `json.load`s `paths.CORPUS` and reads `paths.RESULTS_LOG` line-by-line
  (both READ-ONLY; a missing log yields corpus-only statuses); `summarize()` returns per-status
  counts + the sorted per-instance view.
- `cli.py` — a `status` subparser dispatching to `load_status_view` + `summarize`, printing a
  sorted-key JSON summary. Thin; no math. Raises-only; 0 asserts; imports clean under `-O`.

**Task 3 — `gate/safe_families.py` G5/G6 settled/open map (GATE-03)** (`2bdd643`)
- `SAFE_FAMILIES` — an `OrderedDict` of the 12 proven-safe classes frozen verbatim
  (ASCII-normalized) from §2 line 644, each → its citation (explicit §2 authors where given;
  the Dec-2025/PST §2 provenance where §2 names none — never invented).
- `screen_safe_families(adj, n, inv)` — runs the registered membership tests and returns
  per-family `{family, citation, status}` (safe-member / not-a-member / screen not yet active)
  plus `hits` and `any_hit`. MVP implements ONE cheap decidable test: `_is_c5_free` via a
  stdlib induced-C5 scan over `G = complement(H)` (no networkx — confinement preserved). The
  map is DATA so it grows as classes settle (stub-and-grow).
- `gate/checks.py::g6_safe_families` now consults the screen: a hit returns `Fail` (recorded
  flag_only by the runner — Role B), no hit returns `Pass`. seed-137 (C5-rich) screens
  not-a-member → g6 passes → the hard-gate PASS is preserved.
- The B7-free screen is DEFERRED to Plan 05 (author sign-off on what B7 denotes) — a module
  comment marks the deferral; no B7 membership test exists.

## Verification

- **Plan tests green**: `pytest tests/test_status_views.py tests/test_safe_family_screen.py
  tests/test_gate_seed137_pass.py -q` → **17 passed in 0.12s**.
- **`alpha2 status` read-only**: `python -m alpha2.cli status` exits 0 and prints
  `total 296, counts {KILLED: 296}` (corpus-only view; results log absent). Corpus sha256
  `7064c3ae…` unchanged; no file written.
- **Full fast tier**: `pytest -q -m "not slow"` → **239 passed, 8 deselected** (220 prior +
  new/06-03 tests); no regression. seed-137 gate PASS test still green with the live g6 screen.
- **`python -O` canary**: `status/views.py` and `gate/safe_families.py` carry **0** `assert`
  statements (grep-verified per file) and import clean under `-O`.
- **T-06-14 (record edit)** — the RESISTANT→KILLED transition test asserts the stored event
  object is byte-identical after derivation (`resistant == frozen`); a verified corpus record is
  likewise unchanged.
- **T-06-15 (false RESISTANT)** — the miss≠RESISTANT and the non-exact-RESISTANT-refused tests
  lock RESISTANT to an exact-method timeout.

## Deviations from Plan

**1. [Rule 3 — Environment] `state.record-metric` requires named flags, not positional args**
- **Found during:** state updates (the documented positional form errored `phase, plan, and
  duration required`).
- **Resolution:** re-invoked as `gsd-sdk query state.record-metric --phase 06 --plan 04
  --duration 16min --tasks 3 --files 7` (accepted). Metric recorded; no code impact.
- **Files modified:** `.planning/STATE.md` (via the SDK handler).

Otherwise the plan executed exactly as written.

## Threat Model Outcomes

- **T-06-14** (record edit) — mitigated: `build_status_view` deep-copies provenance and never
  writes an input; the RESISTANT→KILLED transition recomputes by precedence; test asserts the
  stored record/event byte-unchanged.
- **T-06-15** (false RESISTANT) — mitigated: RESISTANT derives ONLY from an exact-method
  timeout event; a heuristic miss yields no status and a non-exact RESISTANT is refused (raise).
- **T-06-16** (false kill via G6) — mitigated: `g6_safe_families` is flag_only (Role B) — a
  cited hit is recorded, never a hard-kill; the seed-137 hard-gate PASS test re-runs green.
- **T-06-17** (invented citation) — mitigated: families + citations frozen verbatim from §2
  line 644; deferred membership tests report "screen not yet active", never a fabricated safe
  verdict; B7 deferred to Plan 05.

## Self-Check: PASSED

- Files: `src/alpha2/status/__init__.py`, `src/alpha2/status/views.py`,
  `src/alpha2/gate/safe_families.py`, `tests/test_status_views.py`,
  `tests/test_safe_family_screen.py`, `src/alpha2/cli.py`, `src/alpha2/gate/checks.py` — all
  present on disk.
- Commits: `af5b167`, `d7e9a79`, `2bdd643` all present in `git log`.
