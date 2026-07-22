"""Runner outcome semantics (GATE-01): hard FAIL kills + stops; ERROR is never a kill.

These use synthetic chains so the control flow — not any particular G-check — is what is
pinned: a hard Fail terminates the chain (later checks are never invoked), a flag_only
Fail is recorded and execution continues, and an Error quarantines to ERROR (distinct from
KILLED).
"""
from alpha2.gate.runner import Error, Fail, GateResult, Pass, Verdict, run_gate


def test_hard_fail_stops_chain_and_kills():
    calls = []

    def c1(adj, n, inv):
        calls.append("c1")
        return Fail("hard boom", {"where": "c1"})

    def c2(adj, n, inv):
        calls.append("c2")
        return Pass({})

    chain = [("c1", "hard", c1), ("c2", "hard", c2)]
    r = run_gate(None, 0, {}, chain=chain)
    assert isinstance(r, GateResult)
    assert r.verdict is Verdict.KILLED
    assert r.killing == "c1"
    assert "c2" not in calls  # a hard FAIL stops the chain: c2 never ran


def test_error_is_never_killed():
    def c1(adj, n, inv):
        return Error("integrality kaboom")

    def c2(adj, n, inv):
        raise AssertionError("must not run after an ERROR")

    chain = [("c1", "hard", c1), ("c2", "hard", c2)]
    r = run_gate(None, 0, {}, chain=chain)
    assert r.verdict is Verdict.ERROR
    assert r.verdict is not Verdict.KILLED
    assert r.killing is None


def test_flag_only_fail_records_and_continues():
    calls = []

    def c1(adj, n, inv):
        calls.append("c1")
        return Fail("flag me", {"regime": "studied"})

    def c2(adj, n, inv):
        calls.append("c2")
        return Pass({})

    chain = [("c1", "flag_only", c1), ("c2", "hard", c2)]
    r = run_gate(None, 0, {}, chain=chain)
    assert r.verdict is Verdict.PASS
    assert "c1" in [name for name, _ in r.flags]
    assert "c2" in calls  # execution continued past the flag_only FAIL
