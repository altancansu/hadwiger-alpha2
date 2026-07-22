"""`python -O` fail-closed canary for the NEW solver paths (EXACT-03 / EXACT-04).

Under `python -O`, `assert` statements are stripped (`__debug__ is False`), which
would turn an assert-based guard into a rubber stamp. The CP-SAT adapter and the
differential gate use `if not cond: raise ...` throughout, so they must STILL
fail closed under -O. This file extends the existing `-O` discipline
(`test_verifier_dash_O.py`) over the two Phase-5 paths.

Each subprocess script first checks `if __debug__: sys.exit(3)` — a REAL branch
(not `assert __debug__ is False`, which is itself stripped under -O and would be
dead code). Exit-code contract, shared by both canaries:
  * 3 = NOT actually optimized (__debug__ was True) -> parent fails the test;
  * 0 = the guard fired / raised (fail-closed, correct);
  * 2 = the guard was rubber-stamped (a value crossed a gate it should not have).

Canary 1 (CP-SAT path): a FEASIBLE optimize status must map to INCUMBENT_ONLY,
and the resulting outcome's `exact_value()` must RAISE — the incumbent-as-optimum
hole stays unrepresentable under -O, without needing a long solve.

Canary 2 (differential path): `differential_verdict` on two UNEQUAL PROVED_OPTIMAL
outcomes must still raise `CriticalDisagreement` under -O — disagreement stays
release-blocking.
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Canary 1 — CP-SAT path. A FEASIBLE (stopped-with-incumbent) optimize result is
# INCUMBENT_ONLY, never PROVED_OPTIMAL; the constructed outcome's exact_value()
# must raise NotProvedOptimal under -O. map_status is driven directly (solver
# arg unused on the FEASIBLE branch), so no real solve is needed.
SCRIPT_CPSAT = textwrap.dedent('''
    import sys
    if __debug__:
        sys.exit(3)   # real branch: NOT under -O -> parent treats as failure
    from ortools.sat.python import cp_model
    from alpha2.solvers.cpsat import map_status
    from alpha2.solvers.result import ExactOutcome, Status, NotProvedOptimal

    st = map_status(cp_model.FEASIBLE, None, "optimize")
    if st is Status.PROVED_OPTIMAL:
        sys.exit(2)   # BUG: FEASIBLE rubber-stamped as an exact optimum under -O
    out = ExactOutcome(
        problem="had2", mode="optimize", status=st, value=3, bound=3,
        bound_source="trivial_n", family=None,
        backend="cpsat", backend_version="x",
    )
    try:
        out.exact_value()
        sys.exit(2)   # BUG: an incumbent read as exact under -O
    except NotProvedOptimal:
        sys.exit(0)   # fail-closed: correct
''')

# Canary 2 — differential path. Two unequal PROVED_OPTIMAL outcomes still raise
# CriticalDisagreement under -O (the gate is raises-only, not assert-based).
SCRIPT_DIFFERENTIAL = textwrap.dedent('''
    import sys
    if __debug__:
        sys.exit(3)   # real branch: NOT under -O -> parent treats as failure
    from alpha2.solvers.differential import differential_verdict, CriticalDisagreement
    from alpha2.solvers.result import ExactOutcome, Status

    def proved(v):
        return ExactOutcome(
            problem="had2", mode="optimize", status=Status.PROVED_OPTIMAL,
            value=v, bound=v, bound_source="definition", family=((0, 1),),
            backend="x", backend_version="y",
        )
    try:
        differential_verdict(proved(3), proved(4), 10)
        sys.exit(2)   # BUG: disagreement silently skipped under -O
    except CriticalDisagreement:
        sys.exit(0)   # fail-closed: correct
''')


def _run_dash_O(script):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-O", "-c", script],
        env=env, cwd=str(REPO), capture_output=True,
    )


def test_cpsat_path_fails_closed_under_dash_O():
    """A FEASIBLE optimize outcome never reads as exact, even under -O."""
    r = _run_dash_O(SCRIPT_CPSAT)
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())


def test_differential_path_fails_closed_under_dash_O():
    """Two unequal proven optima still raise CriticalDisagreement under -O."""
    r = _run_dash_O(SCRIPT_DIFFERENTIAL)
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())
