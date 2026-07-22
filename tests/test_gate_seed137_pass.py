"""D-01 Role B PROOF (T-06-01): seed-137 (n=31) PASSES the hard-gate.

seed-137 provably fails the strict Appendix-E §2 gate at G3 (kappa=11 < chi=16;
delta=16 < chi+1=17) and G4 (omega=14 > chi-3=13; omega/n=0.45 >> 1/4), yet it MUST reach
the had_2=17 step. So a deep gate killing seed-137 is WRONG: G3/G4 must be recorded as
flags, never as kills. This test is the standing guard on that invariant.

Also pins invariants/cliques.py at seed-137 = (omega, kappa, connected) == (14, 11, True)
and on a small hand instance (complement of K5 = the empty graph on 5 vertices).
"""
import random

from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.cliques import is_connected_G, kappa_G, omega_G
from alpha2.invariants.matching import matching_number
from alpha2.gate.runner import Verdict, run_gate


def _seed137():
    n = 31
    adj, _ = triangle_free_process(n, random.Random(137))
    nu = matching_number(adj, n)
    inv = {
        "nu_H": nu,
        "chi_G": n - nu,
        "omega_G": omega_G(adj, n),
        "kappa_G": kappa_G(adj, n),
    }
    return adj, n, inv


def test_seed137_invariants_are_the_known_values():
    adj, n, inv = _seed137()
    assert (inv["nu_H"], inv["chi_G"]) == (15, 16)
    assert inv["omega_G"] == 14
    assert inv["kappa_G"] == 11
    assert is_connected_G(adj, n) is True


def test_seed137_passes_hard_gate_with_g3_g4_as_flags():
    adj, n, inv = _seed137()
    r = run_gate(adj, n, inv)
    # Role B: the deep gate does NOT kill a studied instance.
    assert r.verdict is Verdict.PASS
    assert r.killing is None
    flag_names = [name for name, _ in r.flags]
    assert "g3_deep" in flag_names       # kappa=11<16, delta=16<17 -> flag, not kill
    assert "g4_omega_window" in flag_names  # omega=14>13, omega/n=0.45 -> flag, not kill


def test_cliques_hand_instance_complement_of_k5():
    # H = K5 (complete on 5 vertices) => G = complement(H) = empty graph on 5 vertices.
    n = 5
    adj = [set(v for v in range(n) if v != u) for u in range(n)]
    assert omega_G(adj, n) == 1          # empty G: largest clique is a single vertex
    assert kappa_G(adj, n) == 0          # empty G: disconnected -> connectivity 0
    assert is_connected_G(adj, n) is False
