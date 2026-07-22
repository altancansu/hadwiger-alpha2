"""`python -O` fail-closed canary for the trust root (VRF-01, crit-1).

Under `python -O`, `assert` statements are stripped (`__debug__ is False`), which
would turn an assert-based verifier into a rubber stamp. The trust root uses
`if not cond: raise VerificationError(...)`, so it must STILL reject a known-bad
model under -O.

The subprocess script first checks `if __debug__: sys.exit(3)` — a REAL branch
(not `assert __debug__ is False`, which is itself stripped under -O and would be
dead code). Exit 3 therefore means "not actually optimized" and the parent fails
the test. Exit 0 = the verifier raised (fail-closed, correct). Exit 2 = the
verifier rubber-stamped a bad model (the WR-01 bug).
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The bad record is embedded directly (must not import the test module). A tiny
# self-consistent H ([[0,1]]) lets the script compute its own canonical sha256, so
# the record passes the integrity check and fails on the OVERLAPPING branch sets.
SCRIPT = textwrap.dedent('''
    import sys, json, hashlib
    if __debug__:
        sys.exit(3)   # real branch: we are NOT under -O -> parent treats as failure
    from alpha2.corpus.verifier import verify_model_record, VerificationError
    edges = [[0, 1]]
    sha = hashlib.sha256(json.dumps(edges, separators=(",", ":")).encode()).hexdigest()
    bad = {
        "H_edges": edges,
        "H_edges_sha256": sha,
        "invariants": {"n": 4, "num_H_edges": 1, "nu_H": 1, "chi_G": 2,
                       "omega_G": None, "had_2": 2},
        "model_branch_sets": [[2, 3], [2, 0]],   # vertex 2 reused -> must raise
    }
    try:
        verify_model_record(bad)
        sys.exit(2)   # BUG: rubber-stamped a bad model under -O
    except VerificationError:
        sys.exit(0)   # fail-closed: correct
''')

# Phase-5 extension: the widened {1,2,3} gate must ALSO fail closed under -O on a
# bad size-3 record. A DISCONNECTED triple (2 internal H-edges => 1 G-edge < 2)
# must be rejected by the size-3 connectivity check — a check that would be
# rubber-stamped if written as an assert. H = [[0,1],[1,2]] is embedded so the
# script computes its own canonical sha256; model_branch_sets carries the bad
# triple [0,1,2].
SCRIPT_SIZE3 = textwrap.dedent('''
    import sys, json, hashlib
    if __debug__:
        sys.exit(3)   # real branch: we are NOT under -O -> parent treats as failure
    from alpha2.corpus.verifier import verify_model_record, VerificationError
    edges = [[0, 1], [1, 2]]
    sha = hashlib.sha256(json.dumps(edges, separators=(",", ":")).encode()).hexdigest()
    bad = {
        "H_edges": edges,
        "H_edges_sha256": sha,
        "invariants": {"n": 3, "num_H_edges": 2, "nu_H": 1, "chi_G": 1,
                       "omega_G": None, "had_2": 1},
        "model_branch_sets": [[0, 1, 2]],   # disconnected triple (1 G-edge) -> must raise
    }
    try:
        verify_model_record(bad)
        sys.exit(2)   # BUG: rubber-stamped a disconnected size-3 triple under -O
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


def test_verifier_fails_closed_under_dash_O():
    r = _run_dash_O(SCRIPT)
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())


def test_verifier_fails_closed_on_bad_size3_under_dash_O():
    """The widened size-3 path stays raises-only: a disconnected triple is still
    rejected under `python -O` (never rubber-stamped)."""
    r = _run_dash_O(SCRIPT_SIZE3)
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())
