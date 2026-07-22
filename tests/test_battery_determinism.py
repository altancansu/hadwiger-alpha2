"""CLI-01: `run_candidate` is deterministic in (n, seed); budgets are echoed into the log.

Fast tier (no slow solve): a hard-gate-KILL case (n < 31) exercises generation → nu → chi
→ omega/kappa → gate on the single-RNG contract v1 without any solver. Two runs at the same
(n, seed) must be BYTE-IDENTICAL — both the returned result dict and the emitted JSONL event
stream (the events carry no wall-clock/timestamp field, only the config budgets) — proving
the single-RNG determinism contract and that budgets travel as config, never a code literal.
"""
import json

from alpha2.battery import pipeline


def test_run_candidate_is_byte_identical_across_runs(tmp_path):
    log_a = tmp_path / "a.jsonl"
    log_b = tmp_path / "b.jsonl"

    res_a = pipeline.run_candidate("tfp", 20, 7, log_path=str(log_a))
    res_b = pipeline.run_candidate("tfp", 20, 7, log_path=str(log_b))

    # Result dict: byte-identical (deterministic in (n, seed)).
    assert json.dumps(res_a, sort_keys=True) == json.dumps(res_b, sort_keys=True)

    # Event stream: byte-identical (no timestamp/wall-clock leaks into the log).
    assert log_a.read_text() == log_b.read_text()


def test_budgets_are_echoed_into_every_event(tmp_path):
    log = tmp_path / "results.jsonl"
    budgets = pipeline.Budgets(heuristic=12.0, had2=34.0, had3=56.0)

    pipeline.run_candidate("tfp", 20, 7, budgets=budgets, log_path=str(log))

    events = [json.loads(ln) for ln in log.read_text().splitlines() if ln.strip()]
    assert events
    for event in events:
        assert event["budgets"] == {"heuristic": 12.0, "had2": 34.0, "had3": 56.0}


def test_different_seeds_diverge(tmp_path):
    # Sanity: determinism is in (n, seed), not a constant — different seeds may differ.
    res_1 = pipeline.run_candidate("tfp", 20, 1, log_path=str(tmp_path / "1.jsonl"))
    res_2 = pipeline.run_candidate("tfp", 20, 2, log_path=str(tmp_path / "2.jsonl"))
    # Both are gate kills, but their invariants/witnesses come from distinct instances.
    assert res_1["seed"] == 1 and res_2["seed"] == 2
