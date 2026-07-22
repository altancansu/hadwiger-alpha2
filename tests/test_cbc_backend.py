"""End-to-end CBC backend panel — the Phase-4 MVP slice (EXACT-01 / EXACT-02).

Fast integration tests over `get_backend("cbc")`:

  * the empirically-pinned status-mapping table (pure function, no solve);
  * H = C5 solved optimize -> PROVED_OPTIMAL had_2 = 3, family routed through
    the frozen trust root (`verify_certificate` — the ONLY truth-conferring
    step; the solver family is an UNTRUSTED proposal until it passes);
  * H = empty (G = K5) closed form -> PROVED_OPTIMAL had_2 = 5;
  * decision mode both legs: target_k=3 -> MODEL_FOUND, target_k=4 ->
    PROVED_INFEASIBLE (value None, family None).

Embedded-literal discipline (test_corpus_r1 precedent): adjacencies are in-file
literals; no cross-test imports. Trust-root calls are made OUTSIDE any test
truth-expression — call, bind k, then compare — so the verification itself is
never an optimization-strippable statement.
"""
import pytest

from alpha2.corpus.schema import build_record, provenance_params
from alpha2.corpus.verifier import verify_certificate
from alpha2.invariants.witness import extract_witness
from alpha2.solvers.backend import get_backend
from alpha2.solvers.result import NotProvedOptimal, Status


# --------------------------------------------------------------------------- #
# In-file instance literals
# --------------------------------------------------------------------------- #
def _c5_adj():
    """H = C5: edges 0-1, 1-2, 2-3, 3-4, 4-0 (n=5, nu=2, chi=3, had_2=3)."""
    return [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]


def _empty_adj(n):
    """H with no edges: G = K_n (nu=0, chi=n, had_2=n via n singletons)."""
    return [set() for _ in range(n)]


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _assert_stamp(out):
    """Every outcome carries the probed backend versions and a real wall time."""
    assert "pulp==3.3.2" in out.backend_version
    assert "2.10.3" in out.backend_version
    assert out.wall_time_s > 0


# --------------------------------------------------------------------------- #
# Test 5 — the locked status-mapping table (pure; uses pulp's exported constants)
# --------------------------------------------------------------------------- #
def test_status_mapping_table_is_the_locked_empirical_table():
    import pulp

    from alpha2.solvers.cbc import map_status

    all_sol = (
        pulp.LpSolutionOptimal,
        pulp.LpSolutionIntegerFeasible,
        pulp.LpSolutionNoSolutionFound,
        pulp.LpSolutionInfeasible,
    )

    # optimize mode
    assert (
        map_status(pulp.LpStatusOptimal, pulp.LpSolutionOptimal, "optimize")
        is Status.PROVED_OPTIMAL
    )
    assert (
        map_status(pulp.LpStatusOptimal, pulp.LpSolutionIntegerFeasible, "optimize")
        is Status.INCUMBENT_ONLY
    )
    assert (
        map_status(pulp.LpStatusNotSolved, pulp.LpSolutionNoSolutionFound, "optimize")
        is Status.UNKNOWN
    )
    for sol in all_sol:
        # optimize can never be legitimately infeasible (empty family feasible)
        assert map_status(pulp.LpStatusInfeasible, sol, "optimize") is Status.ERROR
        assert map_status(pulp.LpStatusUnbounded, sol, "optimize") is Status.ERROR

    # decision mode
    assert (
        map_status(pulp.LpStatusOptimal, pulp.LpSolutionOptimal, "decision")
        is Status.MODEL_FOUND
    )
    for sol in all_sol:
        assert (
            map_status(pulp.LpStatusInfeasible, sol, "decision")
            is Status.PROVED_INFEASIBLE
        )
        assert map_status(pulp.LpStatusNotSolved, sol, "decision") is Status.UNKNOWN


# --------------------------------------------------------------------------- #
# Test 6 — E2E happy path: C5 optimize -> PROVED_OPTIMAL -> trust root
# --------------------------------------------------------------------------- #
def test_c5_end_to_end_proved_optimal_through_trust_root():
    adj = _c5_adj()
    backend = get_backend("cbc")
    out = backend.solve_had2(adj, 5, mode="optimize")

    assert out.status is Status.PROVED_OPTIMAL
    assert out.exact_value() == 3
    assert out.bound == 3
    assert out.family is not None
    assert len(out.family) == 3
    _assert_stamp(out)

    M, U, nu = extract_witness(adj, 5)
    rec = build_record(
        provenance=provenance_params("synthetic_c5", 5, {"cycle": 5}),
        H_edges=_h_edges(adj, 5),
        nu_H=nu,
        chi_G=5 - nu,
        model_branch_sets=[list(s) for s in out.family],
        matching_M=M,
        tutte_berge_U=U,
        method="exact ILP (CBC): had_2(G)=3",
    )
    k = verify_certificate(rec)  # trust root arbitrates; raises on any defect
    assert k == 3


# --------------------------------------------------------------------------- #
# Test 7 — closed form: H = empty at n=5 (G = K5) -> had_2 = 5
# --------------------------------------------------------------------------- #
def test_empty_h_k5_end_to_end():
    adj = _empty_adj(5)
    backend = get_backend("cbc")
    out = backend.solve_had2(adj, 5, mode="optimize")

    assert out.status is Status.PROVED_OPTIMAL
    assert out.exact_value() == 5
    assert out.bound == 5
    assert out.family is not None
    assert len(out.family) == 5
    assert all(len(s) == 1 for s in out.family)
    assert sorted(v for s in out.family for v in s) == [0, 1, 2, 3, 4]
    _assert_stamp(out)

    rec = build_record(
        provenance=provenance_params("synthetic_empty_h", 5, {"n": 5}),
        H_edges=[],
        nu_H=0,
        chi_G=5,
        model_branch_sets=[list(s) for s in out.family],
        matching_M=[],
        tutte_berge_U=[],
        method="exact ILP (CBC): had_2(G)=5",
    )
    k = verify_certificate(rec)
    assert k == 5


# --------------------------------------------------------------------------- #
# Test 8 — decision mode, both legs (SC4)
# --------------------------------------------------------------------------- #
def test_decision_mode_both_legs_on_c5():
    adj = _c5_adj()
    backend = get_backend("cbc")

    found = backend.solve_had2(adj, 5, mode="decision", target_k=3)
    assert found.status is Status.MODEL_FOUND
    assert found.family is not None
    assert len(found.family) >= 3
    with pytest.raises(NotProvedOptimal):
        found.exact_value()  # a decision witness is never an exact value
    _assert_stamp(found)

    refused = backend.solve_had2(adj, 5, mode="decision", target_k=4)
    assert refused.status is Status.PROVED_INFEASIBLE
    assert refused.value is None
    assert refused.family is None
    with pytest.raises(NotProvedOptimal):
        refused.exact_value()
    _assert_stamp(refused)
