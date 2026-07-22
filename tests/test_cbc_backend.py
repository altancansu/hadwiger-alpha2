"""End-to-end CBC backend panel — the Phase-4 MVP slice (EXACT-01 / EXACT-02).

Fast integration tests over `get_backend("cbc")`:

  * the empirically-pinned status-mapping table (pure function, no solve);
  * H = C5 solved optimize -> PROVED_OPTIMAL had_2 = 3, family routed through
    the frozen trust root (`verify_certificate` — the ONLY truth-conferring
    step; the solver family is an UNTRUSTED proposal until it passes);
  * H = empty (G = K5) closed form -> PROVED_OPTIMAL had_2 = 5;
  * decision mode both legs: target_k=3 -> MODEL_FOUND, target_k=4 ->
    PROVED_INFEASIBLE (value None, family None).

Plus the 296-lineage every-commit kill panel (ROADMAP SC2, every-commit leg):

  * seed-1 and seed-137 (n=31) regenerated from the frozen generator, gated on
    their pinned invariants BEFORE any solve is trusted (the R2 discipline —
    a drifted generator must never self-certify), then killed in decision
    mode at k = chi = 16 (~2.5 s each) with the family routed through the
    trust root as an IN-MEMORY schema-v1 record (never written to data/);
  * a Cayley p=31 (seed 5310) kill in the slow tier, structurally gated
    (|S|-regular, symmetric — the R2 Cayley tripwire) and provenance-shaped
    to mirror the committed cayley:p31:s5310 record (read-only comparison).

Embedded-literal discipline (test_corpus_r1 precedent): adjacencies and the
pinned regeneration invariants are in-file literals; no cross-test imports.
Trust-root calls are made OUTSIDE any test truth-expression — call, bind k,
then compare — so the verification itself is never an optimization-strippable
statement.
"""
import json
import random

import pytest

from alpha2 import paths
from alpha2.corpus.schema import build_record, provenance_params, provenance_seed
from alpha2.corpus.verifier import verify_certificate
from alpha2.generators.cayley import cayley_adj, random_maximal_symmetric_sumfree
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
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


# --------------------------------------------------------------------------- #
# Test 8b — WR-04 regression: bool target_k must raise, never mean k=1.
# isinstance(True, int) is True, so without the explicit bool rejection a
# caller bug passing a comparison result runs a k=1 decision solve and
# returns an honest-looking MODEL_FOUND (wrong question, right answer).
# --------------------------------------------------------------------------- #
def test_decision_mode_rejects_bool_target_k():
    backend = get_backend("cbc")
    for bad in (True, False):
        with pytest.raises(ValueError):
            backend.solve_had2(_c5_adj(), 5, mode="decision", target_k=bad)
    # Non-int and non-positive targets stay rejected too.
    for bad in (0, -1, None, 3.0, "3"):
        with pytest.raises(ValueError):
            backend.solve_had2(_c5_adj(), 5, mode="decision", target_k=bad)


# --------------------------------------------------------------------------- #
# Test 9 — WR-03 regression: the recompute guard is scale-robust (no solve).
#
# Per-variable drift up to _INTEGRALITY_TOL accumulates across the objective
# sum, so the old flat 1e-6 gate on |count - reported| spuriously ERRORed a
# genuine integral optimum once #vars * 1e-6 exceeded 1e-6 (~0.125 at n=501).
# Drive _guarded_extract directly with real pulp objects and hand-set
# varValues: deterministic, milliseconds, no CBC invocation.
# --------------------------------------------------------------------------- #
def _drifted_singleton_model(n_vars, per_var_value, objective_shift=0.0):
    import pulp

    prob = pulp.LpProblem("wr03", pulp.LpMaximize)
    sv = {v: pulp.LpVariable(f"s_{v}", cat="Binary") for v in range(n_vars)}
    prob += pulp.lpSum(sv.values()) + objective_shift
    for var in sv.values():
        var.varValue = per_var_value
    return prob, {}, sv  # mv empty: singletons keep the family disjoint


def test_recompute_guard_accepts_accumulated_per_variable_drift():
    from alpha2.solvers.cbc import _guarded_extract

    # 100 binaries each 9e-7 below 1.0 — every one passes the per-variable
    # integrality gate, but the summed objective is 9e-5 off the count, far
    # above the old flat 1e-6 gate. A genuine integral optimum must extract.
    prob, mv, sv = _drifted_singleton_model(100, 1.0 - 9e-7)
    fam = _guarded_extract(prob, mv, sv, [], 100, "optimize", None)
    assert fam is not None, "accumulated float drift spuriously tripped the guard"
    assert len(fam) == 100
    assert all(len(s) == 1 for s in fam)


def test_recompute_guard_stays_fail_closed_on_count_mismatch():
    from alpha2.solvers.cbc import _guarded_extract

    # A true count mismatch (reported objective a full unit off the extracted
    # count) must still trip the guard — fail-closed is non-negotiable.
    prob, mv, sv = _drifted_singleton_model(100, 1.0, objective_shift=1.0)
    fam = _guarded_extract(prob, mv, sv, [], 100, "optimize", None)
    assert fam is None, "unit-level count mismatch crossed the recompute guard"


def test_recompute_guard_stays_fail_closed_on_excess_subunit_drift():
    from alpha2.solvers.cbc import _guarded_extract

    # Sub-unit drift beyond the accumulated per-variable budget
    # (#vars * 1e-6 = 1e-4 here) is still fatal: 0.4 rounds back to the
    # count, but exceeds any legitimate accumulation.
    prob, mv, sv = _drifted_singleton_model(100, 1.0, objective_shift=0.4)
    fam = _guarded_extract(prob, mv, sv, [], 100, "optimize", None)
    assert fam is None, "excess sub-unit drift crossed the recompute guard"


# --------------------------------------------------------------------------- #
# 296-lineage every-commit kill panel (ROADMAP SC2, every-commit leg)
#
# Decision mode IS the kill path: ~2.5 s per instance vs ~149 s for the
# optimality proof (60x cheaper), so these run on every commit. The family a
# kill produces is an UNTRUSTED proposal; it becomes a result only when the
# frozen trust root verifies it via an in-memory schema-v1 record. NEVER
# truncated before build_record — schema derives had_2 = len and refuses
# len < chi.
# --------------------------------------------------------------------------- #

# Pinned regeneration invariants (embedded literals; live-verified in
# 04-RESEARCH): (n=31) seed-1 -> |E(H)|=131, nu=15, chi=16;
# seed-137 -> |E(H)|=177, nu=15, chi=16 (the instance the heuristic misses).
_TFP_GATES = {1: 131, 137: 177}


def _tfp_kill_at_chi(seed):
    """Regenerate (31, seed), gate invariants, kill at k=16, verify the family.

    The regeneration gate runs BEFORE any solve is trusted (the R2 discipline):
    a drifted generator must never self-certify through a solver run.
    """
    n = 31
    adj, m = triangle_free_process(n, random.Random(seed))
    assert m == _TFP_GATES[seed], (seed, m)
    nu = matching_number(adj, n)
    assert nu == 15, (seed, nu)
    chi = n - nu
    assert chi == 16, (seed, chi)

    out = get_backend("cbc").solve_had2(adj, n, mode="decision", target_k=chi)
    assert out.status is Status.MODEL_FOUND
    assert out.family is not None
    assert len(out.family) >= chi
    _assert_stamp(out)

    M, U, nu2 = extract_witness(adj, n)
    rec = build_record(
        provenance=provenance_seed(
            "triangle_free_process_complement", n, seed,
            "Bohman uniform triangle-free process",
        ),
        H_edges=_h_edges(adj, n),
        nu_H=nu,
        chi_G=chi,
        model_branch_sets=[list(s) for s in out.family],  # FULL family, never truncated
        matching_M=M,
        tutte_berge_U=U,
        method=f"exact ILP (CBC): decision k={chi}",
    )
    k = verify_certificate(rec)  # trust root arbitrates; raises on any defect
    assert k >= chi


def test_seed1_decision_kill_at_chi_every_commit():
    _tfp_kill_at_chi(1)


def test_seed137_decision_kill_at_chi_every_commit():
    _tfp_kill_at_chi(137)


@pytest.mark.slow
def test_cayley_p31_decision_kill_at_chi():
    """Cayley p=31 (seed 5310) kill — guards the second generator family.

    Structural gate (the R2 Cayley tripwire) before any solve: adj must be
    |S|-regular and symmetric, and the regenerated S must match the committed
    cayley:p31:s5310 record's stored params (read-only via paths.CORPUS).
    """
    p = 31
    seed = 5000 + 10 * p + 0  # seed convention: 5000 + 10*p + k -> 5310
    S = random_maximal_symmetric_sumfree(p, random.Random(seed))
    adj = cayley_adj(p, S)

    # Structural gate: |S|-regular, symmetric, no self-loops.
    assert all(len(adj[u]) == len(S) for u in range(p))
    assert all(u in adj[v] for u in range(p) for v in adj[u])
    assert all(u not in adj[u] for u in range(p))

    # Provenance-shape anchor: the committed record (READ-ONLY) pins S and chi.
    with open(paths.CORPUS) as fh:
        records = json.load(fh)
    stored = [
        r for r in records
        if r["provenance"].get("family") == "cayley_maximal_sumfree_Zp"
        and r["provenance"].get("n") == p
        and r["provenance"].get("seed") == seed
    ]
    assert len(stored) == 1, len(stored)
    assert sorted(S) == stored[0]["provenance"]["params"]["S"]

    nu = matching_number(adj, p)
    chi = p - nu
    assert chi == stored[0]["invariants"]["chi_G"]

    out = get_backend("cbc").solve_had2(adj, p, mode="decision", target_k=chi)
    assert out.status is Status.MODEL_FOUND
    assert out.family is not None
    assert len(out.family) >= chi
    _assert_stamp(out)

    M, U, nu2 = extract_witness(adj, p)
    rec = build_record(
        provenance=provenance_params(
            "cayley_maximal_sumfree_Zp", p, {"S": sorted(S)}, seed=seed,
        ),
        H_edges=_h_edges(adj, p),
        nu_H=nu,
        chi_G=chi,
        model_branch_sets=[list(s) for s in out.family],  # FULL family, never truncated
        matching_M=M,
        tutte_berge_U=U,
        method=f"exact ILP (CBC): decision k={chi}",
    )
    k = verify_certificate(rec)
    assert k >= chi
