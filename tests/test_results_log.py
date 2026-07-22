"""CLI-02: the results log is append-only and every event carries the required fields.

Fast tier (no slow solve): drives `run_candidate` on a hard-gate-KILL case (n < 31 <
Carter's bound → G1 kills before any solve) so the full runbook emits real events in
milliseconds. Asserts (1) each JSONL event carries the CLI-02 field set
{terminal_state, method, certificate_ref, reason, seed, provenance, budgets}; (2) the log
is append-only — a second run only GROWS the file, never truncates or edits a prior line.
"""
import json

from alpha2.battery import pipeline

# CLI-02 required fields on every emitted event.
_REQUIRED = ("terminal_state", "method", "certificate_ref", "reason",
             "seed", "provenance", "budgets")


def _events(path):
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def test_every_event_carries_the_cli02_fields(tmp_path):
    log = tmp_path / "results.jsonl"
    res = pipeline.run_candidate("tfp", 20, 1, log_path=str(log))

    # Gate-kill terminal (n=20 < 31): a fast, solve-free path.
    assert res["terminal_state"] == "KILLED-BY-GATE"

    events = _events(log)
    assert events, "expected at least one results-log event"
    for event in events:
        for key in _REQUIRED:
            assert key in event, (key, event)
        # provenance is the tagged-union dict; seed is echoed top-level too.
        assert isinstance(event["provenance"], dict)
        assert event["seed"] == 1
        assert set(event["budgets"]) == {"heuristic", "had2", "had3"}

    # A terminal event exists and names the terminal state.
    terminal = [e for e in events if e.get("terminal")]
    assert terminal, events
    assert any(e["terminal_state"] == "KILLED-BY-GATE" for e in terminal)


def test_results_log_is_append_only(tmp_path):
    log = tmp_path / "results.jsonl"

    pipeline.run_candidate("tfp", 20, 1, log_path=str(log))
    first = log.read_text()
    n_first = len(_events(log))
    assert n_first >= 1

    pipeline.run_candidate("tfp", 20, 1, log_path=str(log))
    second = log.read_text()
    n_second = len(_events(log))

    # Append-only: the second run GREW the file and left the first run's bytes as a prefix.
    assert n_second == 2 * n_first
    assert second.startswith(first)
