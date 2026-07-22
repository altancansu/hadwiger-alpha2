"""SC1 status-honesty proof for CP-SAT: FEASIBLE can NEVER read as an exact had_2.

The CP-SAT twin of `test_cbc_status_honesty.py`. CP-SAT's whole reason to exist
here is to DISAGREE with CBC when one of them has a bug, so the load-bearing
work is the status honesty, not the API:

  * the pure map_status table — every (CpSolverStatus, mode) row maps to the
    exact locked Status; OPTIMAL-with-obj!=bound and INFEASIBLE-optimize both
    map to ERROR (never PROVED_OPTIMAL, never PROVED_INFEASIBLE);
  * FEASIBLE (optimize) -> INCUMBENT_ONLY and `exact_value()` RAISES
    NotProvedOptimal — the CP-SAT incumbent-as-optimum hole is unrepresentable,
    proven both by the pure map (deterministic, ms) AND by a live tight-budget
    solve of the real seed-137 instance;
  * PROVED_OPTIMAL requires round(obj)==round(bound) (defense-in-depth): the
    gate returns ERROR when they differ, and a genuine PROVED_OPTIMAL carries
    bound == value;
  * determinism: num_workers==1 and the pinned random_seed are actually applied
    to the solver that runs a recorded solve (introspected at solve() time).

Embedded-literal discipline: adjacency is an in-file literal; the seed-137 H is
regenerated fresh from the frozen deterministic generator. All exact/trust-root
reads are made OUTSIDE any assert truth-expression — call, bind, then compare.
This test reads and writes NOTHING under data/.
"""
import random
import types

import pytest

from ortools.sat.python import cp_model

from alpha2.generators.tfp import triangle_free_process
from alpha2.solvers import cpsat
from alpha2.solvers.backend import get_backend
from alpha2.solvers.cpsat import map_status
from alpha2.solvers.result import ExactOutcome, NotProvedOptimal, SolveParams, Status


def _c5_adj():
    """H = C5: edges 0-1, 1-2, 2-3, 3-4, 4-0 (n=5, had_2=3)."""
    return [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]


def _solver_stub(obj, bound):
    """Minimal solver-shaped object: map_status reads only these two fields."""
    return types.SimpleNamespace(objective_value=obj, best_objective_bound=bound)


# --------------------------------------------------------------------------- #
# Test 1 — the pure map_status table (no solve; the Pattern-1 status table).
# Non-OPTIMAL rows never read the solver, so solver=None documents that.
# --------------------------------------------------------------------------- #
def test_map_status_table():
    equal = _solver_stub(3.0, 3.0)  # OPTIMAL: obj == bound

    # optimize mode
    assert map_status(cp_model.OPTIMAL, equal, "optimize") is Status.PROVED_OPTIMAL
    assert map_status(cp_model.FEASIBLE, None, "optimize") is Status.INCUMBENT_ONLY
    assert map_status(cp_model.INFEASIBLE, None, "optimize") is Status.ERROR
    assert map_status(cp_model.UNKNOWN, None, "optimize") is Status.UNKNOWN
    assert map_status(cp_model.MODEL_INVALID, None, "optimize") is Status.ERROR

    # decision mode
    assert map_status(cp_model.OPTIMAL, equal, "decision") is Status.MODEL_FOUND
    assert map_status(cp_model.FEASIBLE, None, "decision") is Status.MODEL_FOUND
    assert (
        map_status(cp_model.INFEASIBLE, None, "decision")
        is Status.PROVED_INFEASIBLE
    )
    assert map_status(cp_model.UNKNOWN, None, "decision") is Status.UNKNOWN
    assert map_status(cp_model.MODEL_INVALID, None, "decision") is Status.ERROR


# --------------------------------------------------------------------------- #
# Test 2 — FEASIBLE(optimize) -> INCUMBENT_ONLY; exact_value() raises.
#   (a) the pure map is unambiguous;
#   (b) an INCUMBENT_ONLY outcome cannot yield an exact value.
# --------------------------------------------------------------------------- #
def test_feasible_optimize_is_incumbent_only():
    assert map_status(cp_model.FEASIBLE, None, "optimize") is Status.INCUMBENT_ONLY
    assert map_status(cp_model.FEASIBLE, None, "decision") is Status.MODEL_FOUND

    incumbent = ExactOutcome(
        problem="had2",
        mode="optimize",
        status=Status.INCUMBENT_ONLY,
        value=3,
        bound=5,
        bound_source="trivial_n",
        family=None,
        backend="cpsat",
        backend_version="ortools==9.15.6755",
    )
    with pytest.raises(NotProvedOptimal):
        incumbent.exact_value()


# --------------------------------------------------------------------------- #
# Test 3 — live integration leg: a tight-budget seed-137 optimize can never
# read as exact. A near-zero max_time cannot prove optimality on n=31, so the
# honest status is INCUMBENT_ONLY or UNKNOWN and exact_value() raises.
# --------------------------------------------------------------------------- #
def test_tight_budget_optimize_never_exact():
    rng = random.Random(137)
    adj, _m = triangle_free_process(31, rng)  # frozen generator; nothing stored
    out = get_backend("cpsat").solve_had2(
        adj, 31, mode="optimize", params=SolveParams(time_limit_s=1e-4)
    )

    assert out.status in {Status.INCUMBENT_ONLY, Status.UNKNOWN}, (
        f"a ~0 s-budget seed-137 optimize must be INCUMBENT_ONLY or UNKNOWN, "
        f"got {out.status.name}"
    )
    with pytest.raises(NotProvedOptimal):
        out.exact_value()  # the incumbent-as-optimum hole is closed under fire
    if out.status is Status.UNKNOWN:
        assert out.value is None  # garbage objective suppressed


# --------------------------------------------------------------------------- #
# Test 4 — the obj==bound gate: ERROR off the gate, bound==value on it.
# --------------------------------------------------------------------------- #
def test_proved_optimal_requires_obj_equals_bound():
    # round(obj) != round(bound) on an OPTIMAL return -> ERROR (never a value).
    assert map_status(cp_model.OPTIMAL, _solver_stub(3.0, 4.0), "optimize") is Status.ERROR
    assert map_status(cp_model.OPTIMAL, _solver_stub(3.0, 3.0), "optimize") is Status.PROVED_OPTIMAL

    out = get_backend("cpsat").solve_had2(_c5_adj(), 5, mode="optimize")
    assert out.status is Status.PROVED_OPTIMAL
    k = out.exact_value()
    assert k == 3
    assert out.bound == out.value  # bound == value by definition on PROVED_OPTIMAL


# --------------------------------------------------------------------------- #
# Test 5 — determinism: num_workers==1 + the pinned random_seed are actually
# applied to the solver used for a recorded solve (introspected at solve time).
# --------------------------------------------------------------------------- #
def test_determinism_params_set(monkeypatch):
    captured = {}
    real_solve = cpsat.cp_model.CpSolver.solve

    def spy_solve(self, model, *args, **kwargs):
        captured["num_workers"] = self.parameters.num_workers
        captured["random_seed"] = self.parameters.random_seed
        return real_solve(self, model, *args, **kwargs)

    monkeypatch.setattr(cpsat.cp_model.CpSolver, "solve", spy_solve)
    out = get_backend("cpsat").solve_had2(_c5_adj(), 5, mode="optimize")

    assert out.status is Status.PROVED_OPTIMAL
    assert captured["num_workers"] == 1
    assert captured["random_seed"] == cpsat._RANDOM_SEED
