"""`python -O` fail-closed canary for the CDM trust leg (POOL-0).

Under `python -O`, `assert` statements are stripped (`__debug__ is False`), which
would turn an assert-based guard into a rubber stamp. `verify_cdm_witness` MUST use
`if not cond: raise VerificationError(...)` throughout (mirroring the frozen
`corpus/verifier.py` discipline), so it STILL fails closed under -O. This file
extends the existing `-O` canary (`tests/test_solver_paths_dash_O.py`) over the CDM
leg.

The subprocess script first checks `if __debug__: sys.exit(3)` — a REAL branch (not
`assert __debug__ is False`, which is itself stripped under -O). Exit-code contract:
  * 3 = NOT actually optimized (__debug__ was True) -> parent fails the test;
  * 0 = the verifier RAISED on the mutant (fail-closed, correct);
  * 2 = the mutant was rubber-stamped (a non-dominating witness slipped through).

Canary: a NON-DOMINATING mutant CDM witness (G = C5, M = [(0,1)] leaves vertex 3
uncovered and non-adjacent) must STILL raise `VerificationError` under -O — proving
the verifier is raises-only, not assert-based.

RED until 07-03: the subprocess import of `alpha2.pool.cdm.verifier` fails, the
uncaught ImportError yields returncode 1 (≠ 0), so the parent assertion is RED —
while COLLECTION stays clean (this module imports no CDM code at import time).
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Non-dominating mutant CDM witness. sha256 is computed inline (stdlib) so the
# integrity gate passes and the DOMINATING leg is what must fire under -O.
SCRIPT_CDM_VERIFIER = textwrap.dedent('''
    import sys
    if __debug__:
        sys.exit(3)   # real branch: NOT under -O -> parent treats as failure
    import hashlib, json
    from alpha2.pool.cdm.verifier import verify_cdm_witness, VerificationError

    def _sha(h_edges):
        canon = json.dumps(sorted([min(a, b), max(a, b)] for a, b in h_edges),
                           separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()

    H_edges = [[0, 2], [0, 3], [1, 3], [1, 4], [2, 4]]   # H = complement(C5)
    rec = {
        "provenance": {"kind": "graph6", "family": "mtf_complement",
                       "n": 5, "graph6": "DUW"},
        "H_edges": H_edges,
        "H_edges_sha256": _sha(H_edges),
        "matching_M": [[0, 1]],   # NON-dominating: vertex 3 uncovered & non-adjacent
        "invariants": {"n": 5, "complement_connected": True, "cdm": True},
        "verified": True,
        "method": "cdm",
    }
    try:
        verify_cdm_witness(rec)
        sys.exit(2)   # BUG: a non-dominating witness rubber-stamped under -O
    except VerificationError:
        sys.exit(0)   # fail-closed: correct
''')


def _run_dash_O(script):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-O", "-c", script],
        env=env, cwd=str(REPO), capture_output=True,
    )


def test_cdm_verifier_fails_closed_under_dash_O():
    """A non-dominating CDM witness still raises VerificationError under -O."""
    r = _run_dash_O(SCRIPT_CDM_VERIFIER)
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())
