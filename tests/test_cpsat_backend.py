"""End-to-end CP-SAT backend panel — the Phase-5 MVP slice (EXACT-03).

Fast integration tests over `get_backend("cpsat")` — the CP-SAT twin of the
frozen `test_cbc_backend.py`, driving the SECOND independent exact engine:

  * H = C5 solved optimize -> PROVED_OPTIMAL had_2 = 3, family routed through
    the frozen trust root (`verify_certificate` — the ONLY truth-conferring
    step; the solver family is an UNTRUSTED proposal until it passes);
  * H = empty (G = K5) closed form -> PROVED_OPTIMAL had_2 = 5;
  * decision mode both legs: target_k=3 -> MODEL_FOUND, target_k=4 ->
    PROVED_INFEASIBLE (value None, family None);
  * WR-04 regression: a bool target_k must raise, never silently mean k=1;
  * the ortools version stamp is carried on every outcome;
  * an exhaustive brute-force had_2 differential at n <= 8 — a SECOND-engine
    cross-check with INDEPENDENT semantics (imports nothing from the module
    under test; candidates + compatibility re-derived from first principles),
    so a CP-SAT-side encoding bug shows as CP-SAT != brute on a tiny instance.

Embedded-literal discipline (test_cbc_backend precedent): adjacencies are
in-file literals; no cross-test imports. Trust-root / exact-value reads are
made OUTSIDE any test truth-expression — call, bind k, then compare — so the
verification itself is never an optimization-strippable statement.
"""
import pytest

from alpha2.corpus.schema import build_record, provenance_params
from alpha2.corpus.verifier import verify_certificate
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.witness import extract_witness
from alpha2.solvers.backend import get_backend
from alpha2.solvers.result import NotProvedOptimal, Status

import random


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
    """Every CP-SAT outcome carries the ortools version stamp + a real wall time."""
    assert out.backend == "cpsat"
    assert "ortools==9.15.6755" in out.backend_version
    assert out.wall_time_s > 0


# --------------------------------------------------------------------------- #
# Test — E2E happy path: C5 optimize -> PROVED_OPTIMAL -> trust root
# --------------------------------------------------------------------------- #
def test_c5_optimize_proved_optimal_through_trust_root():
    adj = _c5_adj()
    backend = get_backend("cpsat")
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
        method="exact CP-SAT (ortools): had_2(G)=3",
    )
    k = verify_certificate(rec)  # trust root arbitrates; raises on any defect
    assert k == 3


# --------------------------------------------------------------------------- #
# Test — closed form: H = empty at n=5 (G = K5) -> had_2 = 5
# --------------------------------------------------------------------------- #
def test_empty_h_k5():
    adj = _empty_adj(5)
    backend = get_backend("cpsat")
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
        method="exact CP-SAT (ortools): had_2(G)=5",
    )
    k = verify_certificate(rec)
    assert k == 5


# --------------------------------------------------------------------------- #
# Test — decision mode, both legs (SC4)
# --------------------------------------------------------------------------- #
def test_decision_both_legs():
    adj = _c5_adj()
    backend = get_backend("cpsat")

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


# --------------------------------------------------------------------------- #
# Test — WR-04 regression: bool target_k must raise, never mean k=1.
# isinstance(True, int) is True, so without the explicit bool rejection a
# caller bug passing a comparison result runs a k=1 decision solve and
# returns an honest-looking MODEL_FOUND (wrong question, right answer).
# --------------------------------------------------------------------------- #
def test_decision_rejects_bool_target_k():
    backend = get_backend("cpsat")
    for bad in (True, False):
        with pytest.raises(ValueError):
            backend.solve_had2(_c5_adj(), 5, mode="decision", target_k=bad)
    # Non-int and non-positive targets stay rejected too.
    for bad in (0, -1, None, 3.0, "3"):
        with pytest.raises(ValueError):
            backend.solve_had2(_c5_adj(), 5, mode="decision", target_k=bad)


# --------------------------------------------------------------------------- #
# Test — the ortools version stamp + backend name.
# --------------------------------------------------------------------------- #
def test_stamp():
    out = get_backend("cpsat").solve_had2(_c5_adj(), 5, mode="optimize")
    assert out.backend == "cpsat"
    assert "ortools==9.15.6755" in out.backend_version
    assert out.wall_time_s > 0


# --------------------------------------------------------------------------- #
# Test-local exhaustive brute-force had_2 reference — INDEPENDENT semantics.
# Imports NOTHING from alpha2.solvers.problems.had2 (that is the point of a
# second-engine differential): candidates and compatibility are re-derived
# here from first principles. Two branch sets are mutually usable iff they are
# disjoint AND joined by at least one G-edge (some a in A, b in B with a != b
# and b not in adj_H[a]). Candidate count <= 8 + C(8,2) = 36 at n <= 8 —
# trivially exhaustive, correctness over speed.
# --------------------------------------------------------------------------- #
def _brute_had2(adj, n):
    """Exhaustive had_2: max clique in the candidate-compatibility graph."""
    cands = [frozenset((v,)) for v in range(n)]
    cands += [
        frozenset((u, v))
        for u in range(n) for v in range(u + 1, n)
        if v not in adj[u]                       # size-2 branch sets are G-edges
    ]

    def compatible(A, B):
        if A & B:                                # branch sets must be disjoint
            return False
        for a in A:                              # ... and adjacent in G
            for b in B:
                if a != b and b not in adj[a]:
                    return True
        return False

    m = len(cands)
    comp = [
        [i != j and compatible(cands[i], cands[j]) for j in range(m)]
        for i in range(m)
    ]

    best = 0

    def extend(size, allowed):
        nonlocal best
        if size > best:
            best = size
        for idx, i in enumerate(allowed):
            if size + (len(allowed) - idx) <= best:
                return                           # cardinality bound only
            extend(size + 1, [j for j in allowed[idx + 1:] if comp[i][j]])

    extend(0, list(range(m)))
    return best


def _matching6_adj():
    """H = perfect matching on n=6: edges 0-1, 2-3, 4-5."""
    return [{1}, {0}, {3}, {2}, {5}, {4}]


def _panel():
    """(id, adj, n) — closed-form anchors + seeded TFP at n in {6, 7, 8}."""
    instances = [
        ("c5", _c5_adj(), 5),
        ("empty5", _empty_adj(5), 5),
        ("matching6", _matching6_adj(), 6),
    ]
    for n, s in [(6, 1), (6, 2), (7, 1), (7, 2), (8, 1), (8, 2)]:
        adj, _m = triangle_free_process(n, random.Random(s))
        instances.append((f"tfp-n{n}-s{s}", adj, n))
    return instances


PANEL = _panel()
PANEL_IDS = [name for name, _adj, _n in PANEL]


@pytest.mark.parametrize("name,adj,n", PANEL, ids=PANEL_IDS)
def test_brute_force_differential_n_le_8(name, adj, n):
    """CP-SAT optimize == independent brute had_2 on the tiny panel (2nd engine)."""
    expected = _brute_had2(adj, n)

    out = get_backend("cpsat").solve_had2(adj, n, mode="optimize")
    assert out.status is Status.PROVED_OPTIMAL   # gate BEFORE any value read
    k = out.exact_value()
    assert k == expected
