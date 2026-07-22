"""Assume-and-verify symmetry-breaking discipline (EXACT-06).

The load-bearing regression here is the H = C5 "WLOG vertex 0 unused" disaster:
C5 has had_2 = 3 = chi and every optimal family is spanning (uses all five
vertices), so a *hand* symmetry-breaking constraint forcing vertex 0 to be
unused is satisfied by NO optimum -> the solver returns an OPTIMAL objective of
2, a FABRICATED sub-chi (had_2 = 2 < 3) counterexample on five vertices. This is
exactly the kind of "impossibility-flavored" result symmetry breaking may never
own.

The discipline (`solvers/symmetry.py`, stdlib-only control flow):

  * `assume_and_verify(sb_outcome, rerun_no_sb, *, chi)` — if the SB-on outcome
    is impossibility-flavored (PROVED_OPTIMAL with exact_value() < chi), it MUST
    rerun WITHOUT symmetry breaking and return that no-SB outcome. If no rerun
    callable is supplied it raises `SBContaminationError` — an SB-on run can
    never surface a < chi conclusion unre-verified.
  * An SB-on outcome that verifies >= chi is the existence branch (the
    certificate self-justifies) and is returned unchanged.

The sound acceleration path uses CP-SAT's internal `symmetry_level`
(objective-preserving, sound by construction, no new dependency); the on/off
differential asserts had_2(sound SB) == had_2(no SB) on a small
vertex-transitive battery. pynauty (hand orbit SB) is DEFERRED — no EXACT-06
criterion needs it, and `solvers/symmetry.py` imports NO solver library at all.

Embedded-literal discipline (test_cbc_backend precedent): adjacencies are
in-file literals; `exact_value()` reads are bound to a local BEFORE any assert
so the truth-conferring read is never an optimization-strippable statement.
"""
import subprocess
import sys

import pytest

from ortools.sat.python import cp_model

from alpha2.solvers.backend import get_backend
from alpha2.solvers.problems.had2 import build_had2_problem
from alpha2.solvers.result import ExactOutcome, Status
from alpha2.solvers.symmetry import (
    SBContaminationError,
    assume_and_verify,
    is_impossibility_flavored,
)

_CHI_C5 = 3


# --------------------------------------------------------------------------- #
# In-file instance literals
# --------------------------------------------------------------------------- #
def _c5_adj():
    """H = C5: edges 0-1, 1-2, 2-3, 3-4, 4-0 (n=5, chi=3, had_2=3=chi)."""
    return [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]


def _empty_adj(n):
    """H with no edges: G = K_n (had_2 = n via n singletons)."""
    return [set() for _ in range(n)]


def _fabricate_c5_vertex0_unused_outcome():
    """Build the C5 had_2 CP-SAT model INLINE with the INVALID "vertex 0 unused"
    hand symmetry-breaking constraint, solve it, and wrap the fabricated result
    in an ExactOutcome.

    The hand constraint (sv[0] == 0 AND every G-edge touching vertex 0 forced
    off) is satisfied by no optimal family -> CP-SAT proves OPTIMAL at objective
    2, a fabricated had_2 = 2 < 3 = chi. Returns (outcome, fabricated_value).
    """
    adj = _c5_adj()
    n = 5
    problem = build_had2_problem(adj, n)
    Gedges = problem.Gedges

    m = cp_model.CpModel()
    mv = {e: m.new_bool_var(f"m_{e[0]}_{e[1]}") for e in Gedges}
    sv = {v: m.new_bool_var(f"s_{v}") for v in range(n)}
    m.maximize(sum(mv.values()) + sum(sv.values()))
    for v in range(n):
        m.add_at_most_one([mv[e] for e in Gedges if v in e] + [sv[v]])
    for (u, v) in sorted(problem.ss):
        m.add_at_most_one([sv[u], sv[v]])
    for (v, (a, b)) in sorted(problem.sp):
        m.add_at_most_one([sv[v], mv[(a, b)]])
    for e1, e2 in sorted(tuple(sorted(pair)) for pair in problem.pp):
        m.add_at_most_one([mv[e1], mv[e2]])

    # The INVALID hand "WLOG vertex 0 is unused" constraint (no computed Aut(H)
    # licenses it; C5 optima are all spanning, so it deletes every optimum).
    m.add(sv[0] == 0)
    for e in Gedges:
        if 0 in e:
            m.add(mv[e] == 0)

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = 137
    solver.parameters.log_search_progress = False
    cp_status = solver.solve(m)

    fabricated = round(solver.objective_value)
    family = tuple(
        [tuple(e) for e in Gedges if solver.boolean_value(mv[e])]
        + [(v,) for v in range(n) if solver.boolean_value(sv[v])]
    )
    outcome = ExactOutcome(
        problem="had2",
        mode="optimize",
        status=Status.PROVED_OPTIMAL if cp_status == cp_model.OPTIMAL else Status.ERROR,
        value=fabricated,
        bound=fabricated,
        bound_source="definition",
        family=family,
        backend="cpsat",
        backend_version="ortools==fabricated-hand-SB",
    )
    return outcome, fabricated


# --------------------------------------------------------------------------- #
# Test 1 — the disaster: an invalid hand SB constraint fabricates had_2 = 2 < chi
# --------------------------------------------------------------------------- #
def test_c5_sb_fabricates_sub_chi():
    outcome, fabricated = _fabricate_c5_vertex0_unused_outcome()

    assert outcome.status is Status.PROVED_OPTIMAL
    assert fabricated == 2  # a FABRICATED sub-chi counterexample on five vertices
    v = outcome.exact_value()
    assert v == 2
    assert v < _CHI_C5
    assert is_impossibility_flavored(outcome, _CHI_C5)


# --------------------------------------------------------------------------- #
# Test 2 — assume-and-verify reruns WITHOUT SB and restores had_2 = 3
# --------------------------------------------------------------------------- #
def test_assume_verify_restores_had2_3():
    outcome, _ = _fabricate_c5_vertex0_unused_outcome()
    adj = _c5_adj()

    def rerun_no_sb():
        return get_backend("cpsat").solve_had2(adj, 5, mode="optimize")

    restored = assume_and_verify(outcome, rerun_no_sb, chi=_CHI_C5)

    assert restored.status is Status.PROVED_OPTIMAL
    v = restored.exact_value()
    assert v == 3  # the honest no-SB optimum: the fabrication never surfaces


# --------------------------------------------------------------------------- #
# Test 3 — an unguarded < chi SB outcome can NEVER surface (SBContaminationError)
# --------------------------------------------------------------------------- #
def test_unguarded_sub_chi_raises():
    outcome, _ = _fabricate_c5_vertex0_unused_outcome()
    with pytest.raises(SBContaminationError):
        assume_and_verify(outcome, None, chi=_CHI_C5)


# --------------------------------------------------------------------------- #
# Test 4 — the existence branch: an SB-on outcome that verifies >= chi passes
# through unchanged and does NOT force a rerun (certificate self-justifies).
# --------------------------------------------------------------------------- #
def test_existence_branch_passthrough():
    adj = _c5_adj()
    # A genuine SB-on solve (sound path: CP-SAT symmetry_level) that reaches chi.
    sb_on = get_backend("cpsat").solve_had2(adj, 5, mode="optimize", symmetry_level=2)
    v = sb_on.exact_value()
    assert v >= _CHI_C5

    def rerun_no_sb():
        raise AssertionError("rerun must NOT be called on the existence branch")

    passed = assume_and_verify(sb_on, rerun_no_sb, chi=_CHI_C5)
    assert passed is sb_on
    assert not is_impossibility_flavored(sb_on, _CHI_C5)


# --------------------------------------------------------------------------- #
# Test 5 — on/off differential on a small vertex-transitive battery:
# had_2(sound SB via CP-SAT symmetry_level) == had_2(no SB).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "adj, n",
    [
        (_c5_adj(), 5),        # C5: vertex-transitive, had_2 = 3
        (_empty_adj(5), 5),    # empty H = K5: vertex-transitive, had_2 = 5
    ],
)
def test_on_off_differential(adj, n):
    backend = get_backend("cpsat")
    on = backend.solve_had2(adj, n, mode="optimize", symmetry_level=2)
    off = backend.solve_had2(adj, n, mode="optimize")

    assert on.status is Status.PROVED_OPTIMAL
    assert off.status is Status.PROVED_OPTIMAL
    v_on = on.exact_value()
    v_off = off.exact_value()
    assert v_on == v_off  # sound SB is objective-preserving


# --------------------------------------------------------------------------- #
# Test 6 — solvers/symmetry.py is stdlib-only control-flow discipline: importing
# it pulls in NO solver library (no pynauty, no ortools, no pulp).
# --------------------------------------------------------------------------- #
def test_no_pynauty_import():
    code = (
        "import sys\n"
        "import alpha2.solvers.symmetry\n"
        "bad = [m for m in ('pynauty', 'ortools', 'pulp') if m in sys.modules]\n"
        "sys.exit('imported: ' + ','.join(bad) if bad else 0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
