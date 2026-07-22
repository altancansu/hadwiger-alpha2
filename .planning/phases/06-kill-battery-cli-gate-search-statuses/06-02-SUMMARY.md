---
phase: 06-kill-battery-cli-gate-search-statuses
plan: 02
subsystem: battery
tags: [battery, cli, runbook, sc1, seed-137, results-log, single-rng, trust-discipline, in-memory]
requires:
  - gate/runner.py (run_gate / GateResult — Plan 06-01, runbook step 1)
  - invariants/matching.py + invariants/cliques.py (nu/chi + omega/kappa gate inputs)
  - search/heuristic.py (solve — step 3 profile heuristic, size-<=2)
  - solvers/backend.py + cbc + cpsat (dual-backend solve_had2 optimize)
  - solvers/differential.py (differential_verdict — sole SHC/kill licenser)
  - corpus/schema.py (build_record + provenance) + corpus/verifier.py (verify_certificate trust root)
provides:
  - battery/pipeline.py (run_candidate — the 7-step runbook + status assignment)
  - battery/log.py (append_event — append-only JSONL results log, CLI-02)
  - cli.py (argparse `battery` subcommand; alpha2.cli:main entry point)
  - paths.RESULTS_LOG (data/results/battery_results.jsonl)
affects:
  - Plan 03+ (search-status views / pool runs consume run_candidate + the results log)
tech-stack:
  added: []
  patterns:
    - single-RNG contract v1 extended to the battery (generator FIRST, then solve)
    - append-only JSONL results log — separate/simpler contract from the hash-chained corpus
    - trust discipline — verify_certificate called OUTSIDE any truth-expression; differential_verdict the sole licenser
    - stdlib argparse thin dispatch; zero new deps
key-files:
  created:
    - src/alpha2/battery/__init__.py
    - src/alpha2/battery/log.py
    - src/alpha2/battery/pipeline.py
    - src/alpha2/cli.py
    - tests/test_battery_seed137_e2e.py
    - tests/test_results_log.py
    - tests/test_battery_determinism.py
  modified:
    - src/alpha2/paths.py
    - pyproject.toml
decisions:
  - SC1 seed-137 KILL is IN-MEMORY (build_record + verify_certificate, NO append_certificate); corpus sha256 byte-untouched
  - run_candidate deterministic in (n,seed) via single-RNG contract v1; log events carry no timestamp -> two runs byte-identical
  - heuristic MISS is an unconditional edge to exact; RESISTANT only via exact INSUFFICIENT; differential_verdict the sole kill/SHC licenser
  - results log = append-only JSONL (paths.RESULTS_LOG), a separate contract from the corpus; CLI is thin stdlib argparse
metrics:
  duration: ~20min
  tasks: 3
  files: 9
  completed: 2026-07-22
requirements: [CLI-01, CLI-02]
---

# Phase 6 Plan 02: alpha2 battery CLI — 7-step runbook, SC1 seed-137 KILL Summary

The MVP thin end-to-end slice (SC1). `alpha2 battery --family tfp --n 31 --seed 137` now runs
the full §4 runbook per candidate — hard-gate PASS (G3/G4 as flags, D-01 Role B) -> exact
chi=16 -> heuristic miss routes UNCONDITIONALLY onward -> dual-backend had_2=17 AGREED_KILL ->
`verify_certificate`==17 -> terminal **KILLED** — reproducing the standing seed-137 case study
**in memory**, with the frozen corpus byte-untouched (sha256 `7064c3ae…` unchanged across the
run). Phase 6 owns NO new mathematics: this is control flow, status assignment, an append-only
results log, and the CLI surface, composing Plan 06-01's gate with the existing
solvers/verifier/schema.

## What Was Built

**Task 1 — `paths.RESULTS_LOG` + `battery/log.py` + entry point + failing SC1 e2e** (`952099a`)
- `paths.RESULTS_LOG = REPO_ROOT/"data"/"results"/"battery_results.jsonl"` beside `CORPUS`
  (sole path authority; `ensure_parent` already generalizes).
- `battery/log.py::append_event(event, path=None)` — append-only JSONL writer using the
  `store.py` atomic discipline (read existing bytes -> tempfile in same dir -> write -> flush ->
  `os.fsync` -> `os.replace`); `json.dumps` runs BEFORE any file touch so a bad event never
  produces a torn line. Path resolves from `paths.RESULTS_LOG` when None; stdlib-only, raises-only.
- `battery/__init__.py` imports NO submodules (importing the package never pulls in the solver
  libraries — lazy at call time).
- `pyproject.toml [project.scripts] alpha2 = "alpha2.cli:main"`; dependencies unchanged.
- `tests/test_battery_seed137_e2e.py` — the Wave-0 RED SC1 e2e (`@pytest.mark.slow`); the
  `pipeline` import is deferred INSIDE the test so the file collects before Task 2 exists.

**Task 2 — `battery/pipeline.py`: the 7-step runbook + status assignment** (`cacc7d0`)
- `run_candidate(family, n, seed, *, params=None, budgets=None, log_path=None)` — deterministic
  in (n,seed) via the single-RNG contract v1 (one `random.Random(seed)` feeds the generator
  FIRST, then `solve`). Steps: **[1]** compute nu/chi/omega/kappa, `run_gate` — a HARD Fail
  short-circuits to `KILLED-BY-GATE` (results-log only, no certificate); an Error `QUARANTINED`
  (never a kill); G3/G4 flags travel on the record. **[2]** chi=n-nu exact. **[3]** heuristic
  `solve`: a HIT routes the UNTRUSTED family through `verify_certificate` -> `KILLED`(heuristic);
  a MISS (`sets is None`) is an UNCONDITIONAL edge to step 4 (never RESISTANT). **[4]**
  dual-backend `solve_had2` optimize -> `differential_verdict` (the SOLE licenser):
  `AGREED_KILL` -> `build_record` (FULL CBC family, CBC binary stamped) + `verify_certificate` ->
  `KILLED`(exact-had2); `SHC_CANDIDATE` -> `SHC-CANDIDATE` (+ had_3 escalation hook, deferred);
  `INSUFFICIENT` -> `RESISTANT`; `CriticalDisagreement` -> `QUARANTINED` + re-raise (HALT).
- `verify_certificate` is called OUTSIDE any truth-expression (call -> bind k -> compare); records
  are always assembled by `schema.build_record` + tagged-union provenance; **no
  `store.append_certificate` for seed-137** (in-memory only). Terminal-state constants are the
  derived VRF-03 vocabulary. Raises-only; 0 `assert` statements; imports clean under `python -O`.

**Task 3 — `cli.py` battery subcommand + determinism & results-log tests** (`7a50472`)
- `cli.py` — thin `argparse` `main()` with `add_subparsers`; `battery --family {tfp,cayley}`
  (V5 choices), `--n` (positive int), `--seed` (int), optional `--budget-heuristic/-had2/-had3`;
  delegates to `pipeline.run_candidate` and prints a sorted-key JSON summary line. No math/orchestration
  in the CLI. `__main__` guard; raises-only.
- `tests/test_results_log.py` — a gate-kill fast path (n=20 < Carter 31) asserts append-only and
  every event carries the CLI-02 field set `{terminal_state, method, certificate_ref, reason,
  seed, provenance, budgets}`.
- `tests/test_battery_determinism.py` — `run_candidate` byte-identical across two runs at the same
  (n,seed) (result dict AND event stream), budgets echoed into every event, different seeds diverge.

## Verification

- **SC1 slow e2e RUN once and GREEN**: `tests/test_battery_seed137_e2e.py` — **1 passed in 163.01s**.
  seed-137 -> gate PASS with `g3_deep`+`g4_omega_window` flags -> chi=16 (nu=15) -> heuristic miss
  (starved budget 0.0) -> dual-backend had_2=17 both PROVED_OPTIMAL -> AGREED_KILL ->
  `verify_certificate`==17 -> terminal KILLED, `verified=True`, `corpus_written=False`.
- **Corpus byte-untouched**: `data/corpus/hadwiger_alpha2_certificates.json` sha256
  `7064c3ae71566c1cc045b647c8c8ae268bacc336661441173692f9ca902770fe` — identical before and after.
- **Fast tier**: `-m "not slow"` -> **220 passed, 7 deselected** (215 prior + 5 new fast battery
  tests); no regression.
- **Input validation (V5)**: `alpha2 battery --family bogus …` and `--n -3` both exit code 2
  (argparse `choices`/`type`).
- **`python -O` canary**: `pipeline.py`/`log.py`/`cli.py` carry 0 `assert` statements (grep-verified
  per file) and import clean under `-O`.
- **CLI functional**: `python -m alpha2.cli --help` lists the `battery` subcommand; `[project.scripts]`
  entry point declared.

## Deviations from Plan

**1. [Rule 3 — Environment] `alpha2` console-script binary not physically installed**
- **Found during:** Task 3 acceptance (`alpha2 --help` entry point check).
- **Issue:** the sandbox `.venv` has no `pip` module and no `uv` on PATH, so `pip install -e .` /
  `uv sync` (which register the `alpha2` console script) cannot be run here.
- **Resolution:** the `[project.scripts] alpha2 = "alpha2.cli:main"` declaration is present and
  verified in `pyproject.toml`, and the CLI is functionally proven via `python -m alpha2.cli`
  (`--help`, `battery --help`, bogus-family/negative-n rejection). The console-script binary
  registration is an environment `uv sync` step, not a code defect — it activates on the next
  environment sync. NOT auto-fixable via a package install (Rule 3 exclusion); no substitution attempted.
- **Files modified:** none beyond the declared `pyproject.toml` entry.

## Threat Model Outcomes

- **T-06-04** (spoofing of a proof under timeout) — mitigated: had_2 is read only via
  `differential_verdict` on two `PROVED_OPTIMAL` outcomes; `exact_value()` raises unless proven;
  no new ungated objective read.
- **T-06-05** (false RESISTANT) — mitigated: a heuristic miss (`sets is None`) is an unconditional
  edge to the exact backends; RESISTANT is emitted ONLY on exact `INSUFFICIENT`.
- **T-06-06** (corpus tamper via seed-137 re-append) — mitigated: SC1 uses an in-memory
  `build_record` + `verify_certificate`, NO `store.append_certificate`; corpus sha256 asserted
  unchanged across the slow e2e.
- **T-06-07** (results-log integrity/repudiation) — mitigated: append-only JSONL, atomic write from
  `paths.RESULTS_LOG`; events are not facts (the hash-chained corpus remains the fact authority).
- **T-06-08** (nondeterminism) — mitigated: single-RNG contract v1; budgets are config echoed into
  every event; determinism test asserts byte-identical result + log across two runs.
- **T-06-09** (CLI input elevation) — mitigated: argparse `choices` (`--family` in {tfp,cayley}),
  `--n` positive int, `--seed` int; bogus/negative inputs exit non-zero.

## Self-Check: PASSED

- Files: all 7 created + 2 modified files present on disk.
- Commits: `952099a`, `cacc7d0`, `7a50472` all present in git log.
