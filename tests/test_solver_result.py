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


_FAM3 = ((0,), (1,), (2,))  # minimal 3-set family for PROVED_OPTIMAL literals


def test_exact_value_returns_the_int_for_proved_optimal():
    out = _outcome(Status.PROVED_OPTIMAL, value=3, bound=3, family=_FAM3)
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
        _outcome(Status.PROVED_OPTIMAL, value=3, bound=4, family=_FAM3)


# --------------------------------------------------------------------------- #
# Test 4 — the outcome is frozen (immutable after construction)
# --------------------------------------------------------------------------- #
def test_outcome_is_frozen():
    out = _outcome(Status.PROVED_OPTIMAL, value=3, bound=3, family=_FAM3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        out.status = Status.ERROR


# --------------------------------------------------------------------------- #
# Test 5 — WR-02 regressions: the construction-time invariants that make the
# "unrepresentable at the type level" claim true for the one status callers
# trust. All three inconsistencies constructed live in 04-REVIEW must RAISE.
# --------------------------------------------------------------------------- #
def test_proved_optimal_refuses_value_none():
    # (a) PROVED_OPTIMAL with value=None used to construct, and exact_value()
    # silently returned None on the one status callers trust.
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_OPTIMAL, value=None, bound=None, family=_FAM3)


def test_proved_optimal_refuses_float_value():
    # (b) value=3.0 (float) with bound=3 used to construct; a declared-int
    # accessor must never yield a float.
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_OPTIMAL, value=3.0, bound=3.0, family=_FAM3)


def test_proved_optimal_refuses_bool_value():
    # bool subclasses int: True must not read as an exact had_2 of 1.
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_OPTIMAL, value=True, bound=True, family=((0,),))


def test_proved_optimal_refuses_family_none():
    # The exact value is only honest alongside the model attaining it.
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_OPTIMAL, value=3, bound=3, family=None)


def test_proved_infeasible_refuses_value_and_family():
    # (c) a valued PROVED_INFEASIBLE used to construct — a garbage value on an
    # impossibility-flavored (radioactive) status.
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_INFEASIBLE, value=99)
    with pytest.raises(ValueError):
        _outcome(Status.PROVED_INFEASIBLE, family=_FAM3)


def test_valued_statuses_refuse_non_int_values():
    # INCUMBENT_ONLY / MODEL_FOUND carry a value by contract — it must be a
    # genuine int (None/float/bool rejected), never solver-side float junk.
    for status in (Status.INCUMBENT_ONLY, Status.MODEL_FOUND):
        for bad in (None, 17.0, True):
            with pytest.raises(ValueError):
                _outcome(status, value=bad, bound=None)


def test_unknown_and_error_refuse_a_family():
    # Guard trips force ERROR with family=None — nothing may cross the gate.
    for status in (Status.UNKNOWN, Status.ERROR):
        with pytest.raises(ValueError):
            _outcome(status, family=_FAM3)


def test_unknown_bound_source_is_rejected():
    with pytest.raises(ValueError):
        ExactOutcome(
            problem="had2",
            mode="optimize",
            status=Status.UNKNOWN,
            value=None,
            bound=None,
            bound_source="vibes",
            family=None,
            backend="cbc",
            backend_version="pulp==3.3.2 / CBC 2.10.3",
        )
