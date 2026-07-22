"""Status-contract unit tests for `alpha2.solvers.result` (EXACT-01).

Pure unit tests: no solver invocation, no third-party imports — only the
stdlib-only result module. The contract under test is the type-level soundness
guarantee this phase exists to land:

  * `exact_value()` RAISES `NotProvedOptimal` for every status except
    PROVED_OPTIMAL — an incumbent (or any weaker outcome) is structurally
    unable to read as an exact had_2;
  * `ExactOutcome.__post_init__` refuses inconsistent (status, value, bound)
    combinations at construction time (raise-based, survives optimized mode);
  * the outcome object is frozen — no field can be rewritten after the fact.
"""
import dataclasses

import pytest

from alpha2.solvers.result import (
    ExactOutcome,
    NotProvedOptimal,
    SolveParams,
    Status,
)


def _outcome(status, value=None, bound=None, family=None):
    """Construct a minimal ExactOutcome for the given status."""
    return ExactOutcome(
        problem="had2",
        mode="optimize",
        status=status,
        value=value,
        bound=bound,
        bound_source="none",
        family=family,
        backend="cbc",
        backend_version="pulp==3.3.2 / CBC 2.10.3",
        params=SolveParams(),
        wall_time_s=0.01,
    )


# --------------------------------------------------------------------------- #
# Test 1 — the raising accessor: the ONLY battery-facing exact read
# --------------------------------------------------------------------------- #
def test_exact_value_raises_for_every_non_proved_status():
    non_proved = [
        (Status.MODEL_FOUND, 3, None),
        (Status.PROVED_INFEASIBLE, None, None),
        (Status.INCUMBENT_ONLY, 17, 20.879),
        (Status.UNKNOWN, None, None),
        (Status.ERROR, None, None),
    ]
    for status, value, bound in non_proved:
        out = _outcome(status, value=value, bound=bound)
        with pytest.raises(NotProvedOptimal):
            out.exact_value()


def test_exact_value_returns_the_int_for_proved_optimal():
    out = _outcome(Status.PROVED_OPTIMAL, value=3, bound=3)
    v = out.exact_value()
    assert v == 3
    assert isinstance(v, int)


# --------------------------------------------------------------------------- #
# Test 2 — UNKNOWN/ERROR carry no value (garbage never surfaces)
# --------------------------------------------------------------------------- #
def test_unknown_and_error_refuse_a_value():
    for status in (Status.UNKNOWN, Status.ERROR):
        with pytest.raises(ValueError):
            _outcome(status, value=17)


# --------------------------------------------------------------------------- #
# Test 3 — PROVED_OPTIMAL means value == bound, by definition
# --------------------------------------------------------------------------- #
def test_proved_optimal_requires_value_equals_bound():
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_OPTIMAL, value=3, bound=4)


# --------------------------------------------------------------------------- #
# Test 4 — the outcome is frozen (immutable after construction)
# --------------------------------------------------------------------------- #
def test_outcome_is_frozen():
    out = _outcome(Status.PROVED_OPTIMAL, value=3, bound=3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        out.status = Status.ERROR
