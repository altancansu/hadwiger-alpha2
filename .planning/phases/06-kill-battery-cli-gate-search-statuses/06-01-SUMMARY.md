---
phase: 06-kill-battery-cli-gate-search-statuses
plan: 01
subsystem: gate
tags: [gate, invariants, criticality, role-b, networkx-confinement, chi-01]
requires:
  - invariants/matching.py (nu_H, hence chi_G = n - nu_H)
  - generators/tfp.py (is_triangle_free / is_edge_maximal_tf for G2)
  - solvers/result.py (frozen validated-dataclass raises-only shape, analog)
provides:
  - invariants/cliques.py (omega_G, kappa_G, is_connected_G — networkx-confined)
  - gate/checks.py (G1-G6 pure predicates over (adj, n, inv))
  - gate/runner.py (Pass/Fail/Error/GateKill/GateResult + run_gate + default_chain)
affects:
  - Plan 02 (SC1 battery slice consumes run_gate as runbook step 1)
tech-stack:
  added: []
  patterns:
    - networkx confined to invariants/cliques.py (CHI-01 discipline extended)
    - raises-only validated dataclasses (survive python -O)
    - lazy chain resolution via PEP 562 __getattr__ (no import cycle)
key-files:
  created:
    - src/alpha2/invariants/cliques.py
    - src/alpha2/gate/__init__.py
    - src/alpha2/gate/checks.py
    - src/alpha2/gate/runner.py
    - tests/test_gate_criticality.py
    - tests/test_gate_outcomes.py
    - tests/test_gate_runner.py
    - tests/test_gate_seed137_pass.py
  modified:
    - tests/test_chi_no_estimate.py
decisions:
  - G1 criticality encoded as `nu == n // 2` (even-n fix, LOCKED); forbidden `n = 2·chi−1` absent
  - D-01 Role B — hard-gate {g1,g2,connectivity} may KILL; g3/g4/g5/g6 flag_only
  - omega/kappa/connectivity networkx-confined to invariants/cliques.py; CHI-01 guard extended
  - default_chain() resolves checks lazily so DEFAULT_CHAIN never forms an import cycle
metrics:
  duration: ~16min
  tasks: 3
  files: 9
  completed: 2026-07-22
requirements: [GATE-01, GATE-02]
---

# Phase 6 Plan 01: G1-G6 Gate + Networkx-Confined Clique/Connectivity Invariants Summary

The G1–G6 gate is now a configured, cost-ordered predicate chain (GATE-01) with definitions
frozen verbatim from Appendix E §2 (GATE-02), enforcing D-01 Role B (LOCKED): the ONLY checks
that may KILL are the minimal hard-gate `{G1 even-n criticality nu==n//2, G2 triangle-free/
diameter-2, connectivity}`; G3-deep (kappa, delta), G4 (omega window), G5, G6 run flag-only —
they record reason + witness onto the result but never terminate the runbook. seed-137 (n=31)
PASSES the hard-gate with G3/G4 recorded as flags, proving a deep gate does NOT kill a studied
instance.

## What Was Built

**Task 1 — `invariants/cliques.py` + CHI-01 guard extension + gate test scaffolds** (`e5252c0`)
- `omega_G`/`kappa_G`/`is_connected_G` over `G = complement(H)`, networkx imported INSIDE each
  function (CHI-01 confinement, mirroring `matching.py`). omega via
  `max_weight_clique(G, weight=None)` — the removed 3.x clique-number helper is never referenced.
  Raises-only; `_H_graph` private helper. seed-137 verified = `(14, 11, True)`.
- Extended the CHI-01 AST guard (`tests/test_chi_no_estimate.py`): a new cliques.py-scoped
  allow-list `CLIQUES_NX_ATTRS = {complement, max_weight_clique, node_connectivity, is_connected}`
  permits that networkx surface ONLY inside `invariants/cliques.py` (via `_is_cliques_module`),
  exactly as `max_weight_matching` is pinned to `matching.py`. The global `ALLOWED_NX_ATTRS` was
  NOT loosened — those attrs still fail the guard everywhere else.
- Four Wave-0 gate test files created as RED scaffolds (populated across Tasks 2–3).

**Task 2 — `gate/checks.py` G1-G6 predicates + outcome vocabulary** (`9b15ca8`)
- `gate/runner.py` outcome types: `Pass`/`Fail`/`Error`/`GateKill`/`GateResult`/`Verdict`, all
  frozen raises-only dataclasses (mirror `solvers/result.py`; survive `python -O`).
- `gate/checks.py`: pure predicates over `(adj, n, inv)`. `g1_criticality` uses `nu == n // 2`
  (accepts n=31/nu=15 AND n=32/nu=16) plus the Carter bound n≥31 — the forbidden `n = 2·chi−1`
  form is grep-asserted absent. `g2_triangle_free_diam2` delegates to `tfp` primitives (not
  re-derived); `g_connectivity` calls `cliques.is_connected_G`; `g3_deep` reads kappa from inv
  and computes delta directly (chi≥7, kappa≥chi, delta≥chi+1, each sub-condition witnessed;
  Hamiltonicity / vertex-criticality / H−v-PM logged "not yet screened"); `g4_omega_window`
  checks 8≤omega≤chi−3 and omega/n<0.25 from inv; `g5`/`g6` are flag-only stubs (GATE-03, Plan 04).
  §2 "Source/reason" text quoted verbatim into each reason string.

**Task 3 — `gate/runner.py` cost-ordered chain + Role B tiers** (`4258e89`)
- `run_gate(adj, n, inv, chain=None)` walks the chain: a HARD `Fail` stops → `KILLED` (later
  checks never run); a FLAG_ONLY `Fail` is appended to `flags` and execution continues; an
  `Error` quarantines → `ERROR` (never a kill). `default_chain()` resolves checks lazily so
  `checks → runner` stays one-directional (no import cycle); `DEFAULT_CHAIN` exposed via PEP 562
  `__getattr__`. Hard set = `{g1_criticality, g2_triangle_free_diam2, g_connectivity}`; the rest
  flag_only. seed-137 ⇒ `PASS` with `g3_deep` + `g4_omega_window` in flags.

## Verification

- `tests/test_gate_criticality.py test_gate_outcomes.py test_gate_runner.py test_gate_seed137_pass.py`
  — 14 passed.
- Full fast suite: **215 passed, 6 deselected (slow)** — no regression; `tests/test_chi_no_estimate.py`
  (CHI-01 guard) green with the cliques.py extension.
- `python -O` canary: gate path (`gate.checks`, `gate.runner`, `invariants.cliques`) carries zero
  `assert` (grep-verified per file) and imports clean under `-O`.
- seed-137 panel: g1/g2/connectivity PASS; g3_deep FAIL(kappa=11<16, delta=16<17); g4 FAIL(omega=14>13,
  omega/n=0.45) — recorded as flags, verdict PASS.

## Deviations from Plan

None — plan executed exactly as written. The four gate test files were populated incrementally
across Tasks 1–3 (Task 1 creates them as RED scaffolds; Tasks 2–3 turn them green), which is the
plan's stated TDD flow. The K5-complement hand-instance cliques test (Task 1 behavior) was placed
in `test_gate_seed137_pass.py` alongside the seed-137 invariant assertions rather than a separate
file (no separate cliques test file is listed in `files_modified`).

## Threat Model Outcomes

- **T-06-01** (deep-gate kill of a studied instance) — mitigated: `test_gate_seed137_pass` asserts
  seed-137 verdict is PASS with g3_deep/g4 as flags; a hard-tier kill of seed-137 is structurally
  impossible (only {g1,g2,connectivity} are hard).
- **T-06-02** (spoofing of criticality) — mitigated: `nu == n // 2` accepts even n; forbidden
  `n = 2·chi−1` form grep-asserted absent in `checks.py`.
- **T-06-03** (bypass on malformed input) — mitigated: hard-set guards are raises-only (survive
  `python -O`).
- **T-06-SC** (supply chain) — accepted: zero new packages; only stdlib + already-audited networkx 3.6.1.

## Self-Check: PASSED

- Files: all 8 created files + 1 modified file present on disk.
- Commits: `e5252c0`, `9b15ca8`, `4258e89` all present in git log.
