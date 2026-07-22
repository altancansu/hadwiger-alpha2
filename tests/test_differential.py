"""The differential agreement gate contract (EXACT-04) — the SOLE licenser.

`solvers/differential.py` cross-examines two `ExactOutcome`s for the SAME
instance and returns a verdict. It is the only component permitted to license an
SHC-CANDIDATE and the only place a backend disagreement becomes release-blocking.

The five verdict paths + the metamorphic guard + the no-solver-import invariant:

  * AGREED_KILL   — both PROVED_OPTIMAL, equal value >= chi (built from REAL
                    CBC+CP-SAT optimize solves on C5 and empty-H, so a lost
                    encoding constraint on either backend would surface here);
  * SHC_CANDIDATE — both PROVED_OPTIMAL, equal value < chi (hand-built proved
                    outcomes: no triangle-free H with had_2 < chi is known, so a
                    real instance cannot exist; the gate LOGIC is what is pinned);
  * CriticalDisagreement — two PROVED_OPTIMAL with UNEQUAL value (release-
                    blocking: quarantine + halt; the message carries both values);
  * INSUFFICIENT  — NOT both proved (a timeout/incumbent/unknown on either side):
                    never SHC, never CRITICAL — a single proof licenses nothing;
  * metamorphic (verifier trumps solver) — a PROVED_OPTIMAL value below a
                    verified size-k family (k from the frozen `verify_certificate`
                    on a REAL record) is CriticalDisagreement, no verdict returned;
  * no-solver-import — importing `alpha2.solvers.differential` loads neither pulp
                    nor ortools (the stdlib-only trust-boundary discipline).

Trust-root / exact-accessor calls are made OUTSIDE any test truth-expression —
call, bind, then compare — so no verification is an optimization-strippable
statement. Hand-built proved outcomes exercise the gate deterministically without
needing a (nonexistent) real had_2 < chi instance.
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from alpha2.corpus.schema import build_record, provenance_params
from alpha2.corpus.verifier import verify_certificate
from alpha2.invariants.witness import extract_witness
from alpha2.solvers.backend import get_backend
from alpha2.solvers.differential import (
    CriticalDisagreement,
    assert_not_below_verified,
    differential_verdict,
)
from alpha2.solvers.result import ExactOutcome, Status

REPO = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# In-file instance literals + hand-built outcome factories
# --------------------------------------------------------------------------- #
def _c5_adj():
    """H = C5 (n=5, nu=2, chi=3, had_2=3)."""
    return [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]


def _empty_adj(n):
    """H with no edges: G = K_n (nu=0, chi=n, had_2=n)."""
    return [set() for _ in range(n)]


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _proved(value, family=((0, 1),)):
    """A hand-built PROVED_OPTIMAL outcome (value == bound; non-None family)."""
    return ExactOutcome(
        problem="had2",
        mode="optimize",
        status=Status.PROVED_OPTIMAL,
        value=value,
        bound=value,
        bound_source="definition",
        family=family,
        backend="synthetic",
        backend_version="test",
    )


def _incumbent(value):
    """A stopped-with-incumbent outcome: NOT exact (exact_value() would raise)."""
    return ExactOutcome(
        problem="had2",
        mode="optimize",
        status=Status.INCUMBENT_ONLY,
        value=value,
        bound=value,
        bound_source="trivial_n",
        family=None,
        backend="synthetic",
        backend_version="test",
    )


def _unknown():
    """A nothing-usable outcome: no value, no family."""
    return ExactOutcome(
        problem="had2",
        mode="optimize",
        status=Status.UNKNOWN,
        value=None,
        bound=None,
        bound_source="none",
        family=None,
        backend="synthetic",
        backend_version="test",
    )


def _dual_optimize(adj, n):
    """Real CBC + CP-SAT optimize outcomes on the same instance."""
    a = get_backend("cbc").solve_had2(adj, n, mode="optimize")
    b = get_backend("cpsat").solve_had2(adj, n, mode="optimize")
    return a, b


# --------------------------------------------------------------------------- #
# AGREED_KILL — two REAL proven optima, equal value >= chi
# --------------------------------------------------------------------------- #
def test_agreed_kill_c5_real_dual_backend():
    adj = _c5_adj()
    a, b = _dual_optimize(adj, 5)
    assert a.status is Status.PROVED_OPTIMAL
    assert b.status is Status.PROVED_OPTIMAL
    assert a.exact_value() == 3
    assert b.exact_value() == 3
    verdict = differential_verdict(a, b, chi=3)  # 3 >= 3 -> agreement on the kill
    assert verdict == "AGREED_KILL"


def test_agreed_kill_empty_h_real_dual_backend():
    adj = _empty_adj(5)
    a, b = _dual_optimize(adj, 5)
    assert a.exact_value() == 5
    assert b.exact_value() == 5
    verdict = differential_verdict(a, b, chi=5)  # had_2 = n = chi -> AGREED_KILL
    assert verdict == "AGREED_KILL"


# --------------------------------------------------------------------------- #
# SHC_CANDIDATE — two proven optima, equal value < chi (hand-built)
# --------------------------------------------------------------------------- #
def test_shc_candidate_when_both_proven_equal_below_chi():
    verdict = differential_verdict(_proved(2), _proved(2), chi=3)
    assert verdict == "SHC_CANDIDATE"


def test_equal_proven_at_chi_is_agreed_kill_not_shc():
    # Equal proven value EXACTLY at chi is a kill, never an SHC-CANDIDATE.
    verdict = differential_verdict(_proved(3), _proved(3), chi=3)
    assert verdict == "AGREED_KILL"


# --------------------------------------------------------------------------- #
# CriticalDisagreement — two proven optima, UNEQUAL value (release-blocking)
# --------------------------------------------------------------------------- #
def test_unequal_proven_raises_critical_disagreement():
    with pytest.raises(CriticalDisagreement) as exc:
        differential_verdict(_proved(3), _proved(4), chi=10)
    msg = str(exc.value)
    assert "3" in msg and "4" in msg  # both values surfaced for the quarantine log


def test_unequal_proven_raises_regardless_of_chi():
    # A disagreement halts the batch no matter the chi context (even below chi,
    # where a naive gate might have "licensed" the smaller value as SHC).
    with pytest.raises(CriticalDisagreement):
        differential_verdict(_proved(2), _proved(5), chi=100)


# --------------------------------------------------------------------------- #
# INSUFFICIENT — NOT both proved (single proof licenses nothing)
# --------------------------------------------------------------------------- #
def test_single_proof_plus_incumbent_is_insufficient():
    assert differential_verdict(_proved(3), _incumbent(3), chi=5) == "INSUFFICIENT"
    assert differential_verdict(_incumbent(3), _proved(3), chi=5) == "INSUFFICIENT"


def test_single_proof_plus_unknown_is_insufficient():
    assert differential_verdict(_proved(2), _unknown(), chi=5) == "INSUFFICIENT"


def test_neither_proved_is_insufficient():
    assert differential_verdict(_incumbent(3), _unknown(), chi=5) == "INSUFFICIENT"


# --------------------------------------------------------------------------- #
# Metamorphic guard — verifier trumps solver
# --------------------------------------------------------------------------- #
def test_metamorphic_verifier_trumps_solver():
    # k is conferred by the FROZEN trust root on a REAL C5 record (had_2 = 3).
    adj = _c5_adj()
    M, U, nu = extract_witness(adj, 5)
    rec = build_record(
        provenance=provenance_params("synthetic_c5", 5, {"cycle": 5}),
        H_edges=_h_edges(adj, 5),
        nu_H=nu,
        chi_G=5 - nu,
        model_branch_sets=[list(s) for s in get_backend("cbc")
                           .solve_had2(adj, 5, mode="optimize").family],
        matching_M=M,
        tutte_berge_U=U,
        method="exact ILP (CBC): had_2(G)=3",
    )
    k = verify_certificate(rec)  # trust root arbitrates OUTSIDE the assert below
    assert k == 3

    # A backend that PROVED had_2 = 2 while a size-3 family verifies is a
    # CRITICAL encoding/solver bug by construction — verifier trumps solver.
    with pytest.raises(CriticalDisagreement):
        assert_not_below_verified(_proved(2), k)


def test_metamorphic_allows_value_at_or_above_verified():
    # A proven value >= the verified family size is consistent — no raise.
    assert_not_below_verified(_proved(3), 3)
    assert_not_below_verified(_proved(4), 3)


def test_metamorphic_ignores_non_proved_outcomes():
    # An incumbent/unknown is not an optimality PROOF, so it cannot trip the
    # verifier-trumps-solver guard (only a PROVED_OPTIMAL value is a fact).
    assert_not_below_verified(_incumbent(1), 3)
    assert_not_below_verified(_unknown(), 3)


# --------------------------------------------------------------------------- #
# No-solver-import — stdlib-only trust boundary
# --------------------------------------------------------------------------- #
def test_no_solver_import():
    """Importing the gate must not load pulp or ortools (stdlib-only)."""
    script = textwrap.dedent('''
        import sys
        import alpha2.solvers.differential  # noqa: F401
        bad = [m for m in sys.modules
               if m == "pulp" or m == "ortools"
               or m.startswith("pulp.") or m.startswith("ortools.")]
        sys.exit(1 if bad else 0)
    ''')
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run(
        [sys.executable, "-c", script], env=env, cwd=str(REPO), capture_output=True
    )
    assert r.returncode == 0, (
        "differential.py loaded a solver library: " + r.stderr.decode()
    )
