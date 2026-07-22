"""Dual-backend had_3 escalation panel (EXACT-05, escalation half) — the seagull
tier fired on BOTH exact engines and arbitrated by the widened trust root.

This is the Wave-2 composition test: it wires together the had_3 model (Plan 02,
`solvers/problems/had3.py`), the widened size-{1,2,3} verifier (Plan 03,
`corpus/verifier.py`), and the CP-SAT backend (Plan 01, `solvers/cpsat.py`) to
prove the size-3 escalation is REAL and cross-checked on a synthetic
size-3-forced instance.

EPISTEMIC NOTE — the escalation trigger (honesty over the plan's literal wording).
The runbook step-5 escalation fires on a certified had_2 < chi. But NO
triangle-free H with had_2 < chi is known: 296/296 corpus instances are killed at
had_2, and an exhaustive small-graph search (n <= 11) finds none (a had_2 < chi
triangle-free instance would be a genuine research artifact, not something to
invent — CORE value: "never invent the missing hour"). So, exactly as Plan 02
established for the had_3 *model* test, the honest escalation signal proven here
is had_2 < had_3: the size-2 optimum falls strictly short of what a size-3 family
reaches, so the size-3 branch set is load-bearing. On this instance had_2 == chi
(Hadwiger already holds at had_2) and had_3 == 5 > 4 == chi; the size-3 family the
escalation extracts is still arbitrated by the widened trust root exactly as a
real had_2 < chi escalation family would be. The machinery — a flagged
`solve_had3` on both backends, the shared frozen Had3Problem, the widened
verifier, and the CBC-vs-CP-SAT had_3 differential — is what this test proves,
synthetic by necessity.

Three independent guards against a lost size-3 constraint are exercised: the
had3 checksum (Plan 02, inside `build_had3_problem`), the widened
`verify_certificate` (Plan 03), and the CBC-vs-CP-SAT had_3 differential (this
plan) — a lost size-3 row would inflate one backend's had_3 above the other's.

Embedded-literal discipline (test_cbc_backend / test_had3_problem precedent):
the size-3-forced adjacency and its pinned invariants are in-file literals; no
cross-test imports. Trust-root reads are made OUTSIDE any test truth-expression
(call, bind k, then compare) so the verification is never an
optimization-strippable statement.
"""
from alpha2.corpus.schema import build_record, provenance_params
from alpha2.corpus.verifier import verify_certificate
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.solvers.backend import get_backend
from alpha2.solvers.result import Status


# --------------------------------------------------------------------------- #
# The synthetic size-3-forced instance (in-file literals; hand-frozen).
#
# A genuine triangle-free H (n=7) with had_2 = 4 < had_3 = 5: the size-3 branch
# set {0,5,6} is load-bearing (established by exhaustive brute force in
# test_had3_problem.py::test_size3_forced_instance_shape, and re-derived here by
# the real backends). Its pinned invariants:
#     n = 7,  nu(H) = 3,  chi(G) = n - nu = 4,  had_2 = 4,  had_3 = 5.
# NOTE had_2 == chi (no triangle-free had_2 < chi instance is known — see module
# docstring); the escalation signal is had_2 < had_3.
# --------------------------------------------------------------------------- #
_FORCED_EDGES = [(0, 1), (0, 2), (0, 5), (1, 6), (2, 6),
                 (3, 5), (3, 6), (4, 5), (4, 6)]
_N = 7
_CHI = 4        # n - nu
_NU = 3
_HAD2 = 4       # size-2 optimum (both backends)
_HAD3 = 5       # size-3 optimum (both backends) — strictly > had_2


def _forced_adj():
    adj = [set() for _ in range(_N)]
    for u, v in _FORCED_EDGES:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


# --------------------------------------------------------------------------- #
# Test 1 — the had_2 baseline is the escalation trigger: both backends agree on
# had_2, and it falls strictly short of had_3 (had_2 < had_3). The pinned chi is
# also confirmed from nu, so the "had_2 vs chi" reading is explicit.
# --------------------------------------------------------------------------- #
def test_had2_baseline_agreement_is_the_escalation_trigger():
    adj = _forced_adj()

    nu = matching_number(adj, _N)
    assert nu == _NU
    assert _N - nu == _CHI                       # chi = n - nu, pinned

    cbc = get_backend("cbc").solve_had2(adj, _N, mode="optimize")
    cpsat = get_backend("cpsat").solve_had2(adj, _N, mode="optimize")
    assert cbc.status is Status.PROVED_OPTIMAL
    assert cpsat.status is Status.PROVED_OPTIMAL
    had2_cbc = cbc.exact_value()
    had2_cpsat = cpsat.exact_value()
    assert had2_cbc == had2_cpsat == _HAD2       # CBC == CP-SAT on had_2
    # Hadwiger already holds at had_2 here (had_2 == chi); the honest escalation
    # signal is had_2 < had_3 — the size-2 model falls short of the size-3 one.
    assert had2_cbc == _CHI
    assert had2_cbc < _HAD3


# --------------------------------------------------------------------------- #
# Test 2 — had_3 reaches the size-3 optimum on BOTH backends, and the extracted
# size-3 family passes the widened trust root (size-3 gate).
# --------------------------------------------------------------------------- #
def test_had3_reaches_optimum_both_backends_through_trust_root():
    adj = _forced_adj()

    # Trigger discipline: assert the had_2 < had_3 escalation signal FIRST (both
    # backends), THEN escalate to had_3 — never speculatively.
    had2 = get_backend("cbc").solve_had2(adj, _N, mode="optimize").exact_value()
    assert had2 == _HAD2 < _HAD3

    for name in ("cbc", "cpsat"):
        out = get_backend(name).solve_had3(adj, _N, mode="optimize")
        assert out.problem == "had3"
        assert out.status is Status.PROVED_OPTIMAL
        assert out.exact_value() == _HAD3        # size-3 optimum reached
        assert out.bound == _HAD3
        assert out.family is not None

        # The family is an UNTRUSTED proposal until the widened trust root passes.
        M, U, nu = extract_witness(adj, _N)
        rec = build_record(
            provenance=provenance_params("synthetic_size3_forced", _N,
                                         {"edges": _h_edges(adj, _N)}),
            H_edges=_h_edges(adj, _N),
            nu_H=nu,
            chi_G=_CHI,
            model_branch_sets=[list(s) for s in out.family],
            matching_M=M,
            tutte_berge_U=U,
            method=f"exact {name} had_3(G)={_HAD3} (size-3 escalation)",
        )
        k = verify_certificate(rec)              # trust root arbitrates; raises on defect
        assert k == _HAD3


# --------------------------------------------------------------------------- #
# Test 3 — CBC-vs-CP-SAT had_3 differential agreement (third guard). A lost
# size-3 conflict row would inflate one backend's had_3 above the other's.
# --------------------------------------------------------------------------- #
def test_had3_differential_agreement():
    adj = _forced_adj()

    cbc = get_backend("cbc").solve_had3(adj, _N, mode="optimize")
    cpsat = get_backend("cpsat").solve_had3(adj, _N, mode="optimize")
    assert cbc.status is Status.PROVED_OPTIMAL
    assert cpsat.status is Status.PROVED_OPTIMAL
    had3_cbc = cbc.exact_value()
    had3_cpsat = cpsat.exact_value()
    assert had3_cbc == had3_cpsat == _HAD3       # equal proven optima: the gate


# --------------------------------------------------------------------------- #
# Test 4 — the escalation genuinely USED a triple: every extracted branch set has
# size in {1,2,3} and at least one has size 3 (the size-3 branch set is load-
# bearing, not a coincidental size-<=2 family).
# --------------------------------------------------------------------------- #
def test_had3_family_uses_a_size3_branch_set():
    adj = _forced_adj()

    for name in ("cbc", "cpsat"):
        out = get_backend(name).solve_had3(adj, _N, mode="optimize")
        assert out.status is Status.PROVED_OPTIMAL
        sizes = sorted(len(s) for s in out.family)
        assert all(sz in (1, 2, 3) for sz in sizes)
        assert max(sizes) == 3                   # a triple is load-bearing
