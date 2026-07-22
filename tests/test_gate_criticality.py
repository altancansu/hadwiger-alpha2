"""G1 even-n criticality (GATE-02 / T-06-02): `nu == n//2`, NEVER `n == 2*chi - 1`.

The forbidden `n == 2*chi - 1` form silently drops even n (n=32, nu=16 is the standing
corpus counterexample). These tests pin the even-n fix: n=31 (nu=15) and n=32 (nu=16)
pass criticality identically, and the Carter bound n>=31 rejects small critical instances.
"""
import random

from alpha2.generators.tfp import triangle_free_process
from alpha2.gate import checks
from alpha2.gate.runner import Fail, Pass


def _dummy_adj(n):
    # g1_criticality reads only (n, inv); adjacency is unused by the criticality predicate.
    return [set() for _ in range(n)]


def test_g1_accepts_odd_critical_seed137():
    adj, _ = triangle_free_process(31, random.Random(137))
    r = checks.g1_criticality(adj, 31, {"nu_H": 15, "chi_G": 16})
    assert isinstance(r, Pass)


def test_g1_accepts_even_n_criticality():
    # n=32, nu=16 == 32//2 must PASS exactly as the odd n=31 case (the even-n fix).
    r = checks.g1_criticality(_dummy_adj(32), 32, {"nu_H": 16, "chi_G": 16})
    assert isinstance(r, Pass)


def test_g1_rejects_non_critical():
    # nu != n//2 -> not critical.
    r = checks.g1_criticality(_dummy_adj(31), 31, {"nu_H": 14, "chi_G": 17})
    assert isinstance(r, Fail)


def test_g1_rejects_below_carter_bound():
    # n=30 with nu=15 satisfies nu==n//2 but is below the Carter bound n>=31 -> Fail.
    r = checks.g1_criticality(_dummy_adj(30), 30, {"nu_H": 15, "chi_G": 15})
    assert isinstance(r, Fail)
