"""SC1 end-to-end: `alpha2 battery --family tfp --n 31 --seed 137` reproduces the
seed-137 case study through the FULL 7-step runbook to a verified KILL — IN MEMORY,
with the frozen corpus byte-untouched.

The MVP thin slice (SC1). This drives `battery.pipeline.run_candidate` for
(family=tfp, n=31, seed=137) with a STARVED heuristic budget (0.0 s → the spanning
heuristic deterministically misses, `heuristic_found is False`) and generous had_2
budgets, and asserts the terminal state is KILLED via a verified had_2 = 17 exact
certificate — gate PASS (with G3/G4 as flags, D-01 Role B) → chi = 16 → heuristic miss
routes UNCONDITIONALLY onward → dual-backend had_2 = 17 → AGREED_KILL → verify_certificate
== 17. The corpus sha256 is asserted unchanged across the run (no `append_certificate`).

Slow tier: the dual-backend optimize is ~149 s (CBC) + CP-SAT time. Marked
`@pytest.mark.slow` (marker registered in pyproject.toml) so it joins the release-gate
`-m slow` selector; the fast tier (`test_results_log`, `test_battery_determinism`) gives
sub-30 s feedback.

Trust-root / exact-accessor results are inspected OUTSIDE any truth-expression — the
pipeline binds `k = verify_certificate(rec)` internally; this test reads the returned dict.
"""
import hashlib

import pytest

from alpha2 import paths


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


@pytest.mark.slow
def test_seed137_battery_e2e_killed_in_memory(tmp_path):
    # Deferred import: the pipeline is Task 2's deliverable. Importing inside the test
    # keeps this file COLLECTIBLE as a Wave-0 RED scaffold before the pipeline exists.
    from alpha2.battery import pipeline

    corpus_before = _sha256(paths.CORPUS)  # frozen-corpus tripwire (byte-untouched)

    log_path = tmp_path / "battery_results.jsonl"
    budgets = pipeline.Budgets(heuristic=0.0, had2=1800.0)
    res = pipeline.run_candidate(
        "tfp", 31, 137, budgets=budgets, log_path=str(log_path)
    )

    # ---- Gate: PASS (hard-gate) with G3/G4 travelling as flags (D-01 Role B). ----
    assert res["gate_verdict"] == "PASS", res["gate_verdict"]
    assert "g3_deep" in res["flags"], res["flags"]
    assert "g4_omega_window" in res["flags"], res["flags"]

    # ---- Exact chi = 16 (n - nu, no estimate). ----
    assert res["chi"] == 16, res["chi"]
    assert res["invariants"]["nu_H"] == 15, res["invariants"]

    # ---- Heuristic MISS (starved budget) routed onward — NEVER RESISTANT. ----
    assert res["heuristic_found"] is False, res["heuristic_found"]

    # ---- Terminal state: verified KILL via exact had_2 = 17. ----
    assert res["terminal_state"] == "KILLED", res["terminal_state"]
    assert "exact" in res["method"], res["method"]
    assert res["had_2"] == 17, res["had_2"]
    assert res["verified"] is True, res["verified"]
    assert res["corpus_written"] is False, res["corpus_written"]

    # ---- Results log: the terminal KILLED event was appended (CLI-02 fields). ----
    import json

    lines = [json.loads(ln) for ln in log_path.read_text().splitlines() if ln.strip()]
    terminal = [e for e in lines if e.get("terminal")]
    assert any(e["terminal_state"] == "KILLED" for e in terminal), terminal
    for e in lines:
        for key in ("terminal_state", "method", "certificate_ref", "reason",
                    "seed", "provenance", "budgets"):
            assert key in e, (key, e)

    # ---- Frozen corpus byte-untouched (no append_certificate for seed-137). ----
    assert _sha256(paths.CORPUS) == corpus_before
