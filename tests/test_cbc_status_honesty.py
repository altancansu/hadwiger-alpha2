"""SC1 status-honesty proof: a timed-out CBC incumbent can NEVER read as exact.

THE soundness-hole test (ROADMAP SC1, proven by live execution): pulp 3.3.2
deliberately maps a "Stopped ... objective value" run to status=Optimal
(live-reproduced in 04-RESEARCH: 20 s limit -> status=1, incumbent 17, true
bound 20.879; 0.05 s limit -> NotSolved with fractional garbage 23.25). This
test solves the real seed-137 instance under a 10 s limit — far below the
~149 s proof time — and requires:

  * the outcome status lands in {INCUMBENT_ONLY, UNKNOWN} (which of the two
    depends on whether CBC found the incumbent in time — both are honest);
  * `exact_value()` RAISES NotProvedOptimal — the incumbent-as-optimum hole
    is closed under live fire, not just by construction;
  * the garbage-objective class (fractional 23.25) never surfaces: UNKNOWN
    carries value=None, INCUMBENT_ONLY carries an int with bound evidence.

Plus the bound-parse fixture: the captured CBC 2.10.3 stopped-run log grammar
("Upper bound: 20.879") is pinned as an in-file literal, and the absent-line
path returns None (caller falls back to the trivial bound n, provenance-tagged
"trivial_n").

The seed-137 H is regenerated fresh each run from the frozen deterministic
generator (`random.Random(137)` -> `triangle_free_process(31, rng)`); this
test reads and writes NOTHING under data/.
"""
import random

import pytest

from alpha2.generators.tfp import triangle_free_process
from alpha2.solvers.backend import get_backend
from alpha2.solvers.cbc import parse_bound
from alpha2.solvers.result import NotProvedOptimal, SolveParams, Status

# ---------------------------------------------------------------------------
# Captured CBC 2.10.3 log literals (04-RESEARCH Pattern 3, live-verified logs;
# embedded-literal discipline — no cross-test imports, no external fixtures).
# ---------------------------------------------------------------------------
CAPTURED_STOPPED_LOG = (
    "Result - Stopped on time limit\n"
    "\n"
    "Objective value:                17.00000000\n"
    "Upper bound:                    20.879\n"
    "Gap:                            0.23\n"
    "Enumerated nodes:               0\n"
    "Total iterations:               12345\n"
)

CAPTURED_OPTIMAL_LOG = (
    "Result - Optimal solution found\n"
    "\n"
    "Objective value:                17.00000000\n"
    "Enumerated nodes:               964\n"
    "Total iterations:               571553\n"
)


# ---------------------------------------------------------------------------
# Test 1 — THE soundness-hole proof (live, ~10-15 s; every-commit tier).
# One solve shared by the assertions below via a module-scoped fixture.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def timeout_outcome():
    """Solve seed-137 optimize under a 10 s limit (proof needs ~149 s)."""
    rng = random.Random(137)
    adj, _m = triangle_free_process(31, rng)  # regenerate H; frozen generator
    backend = get_backend("cbc")
    return backend.solve_had2(
        adj, 31, mode="optimize", params=SolveParams(time_limit_s=10)
    )


def test_timeout_status_is_incumbent_only_or_unknown(timeout_outcome):
    # Both are honest; which one occurs depends on whether CBC found the
    # incumbent within the limit. What is NOT acceptable is PROVED_OPTIMAL
    # (or any other status) on a run stopped far short of the proof time.
    assert timeout_outcome.status in {Status.INCUMBENT_ONLY, Status.UNKNOWN}, (
        f"10 s-limited seed-137 optimize must be INCUMBENT_ONLY or UNKNOWN, "
        f"got {timeout_outcome.status.name}"
    )


def test_exact_value_raises_on_timed_out_run(timeout_outcome):
    # The central SC1 claim: a CBC incumbent can NEVER read as an exact had_2.
    with pytest.raises(NotProvedOptimal):
        timeout_outcome.exact_value()


def test_no_garbage_value_surfaces(timeout_outcome):
    # The fractional-garbage class (23.25 observed live on a 0.05 s stop) must
    # never surface as a value; bound evidence must carry provenance.
    out = timeout_outcome
    if out.status is Status.INCUMBENT_ONLY:
        assert isinstance(out.value, int), (
            f"INCUMBENT_ONLY value must be an int, got {out.value!r}"
        )
        assert out.bound is not None, "INCUMBENT_ONLY must carry a dual bound"
        assert out.bound_source in {"cbc_log", "trivial_n"}, (
            f"bound provenance must be recorded, got {out.bound_source!r}"
        )
        # The bound may exceed the incumbent (20.879 > 17 observed live) —
        # equality is NEVER required here: that would smuggle optimality back.
    else:  # Status.UNKNOWN
        assert out.value is None, (
            f"UNKNOWN must carry value=None (garbage objective suppressed), "
            f"got {out.value!r}"
        )


# ---------------------------------------------------------------------------
# Test 2 — bound-parse fixture from the captured log grammar (no solver run).
# ---------------------------------------------------------------------------
def test_parse_bound_extracts_dual_bound_from_stopped_log():
    assert parse_bound(CAPTURED_STOPPED_LOG) == 20.879


def test_parse_bound_returns_none_when_line_absent():
    assert parse_bound(CAPTURED_OPTIMAL_LOG) is None
    assert parse_bound("") is None


# ---------------------------------------------------------------------------
# Test 3 — fallback provenance (no extra solver run): the adapter's documented
# contract is bound=n with bound_source == "trivial_n" whenever the log line
# is absent on a stopped run; on the live outcome we assert the provenance
# field is populated from the two legitimate sources whenever a bound exists.
# ---------------------------------------------------------------------------
def test_bound_provenance_recorded_on_stopped_run(timeout_outcome):
    out = timeout_outcome
    # Stopped optimize runs (either honest status) always record a bound with
    # provenance: parsed from the archived log, or the trivial fallback n.
    assert out.bound is not None
    assert out.bound_source in {"cbc_log", "trivial_n"}
    if out.bound_source == "trivial_n":
        assert out.bound == 31
