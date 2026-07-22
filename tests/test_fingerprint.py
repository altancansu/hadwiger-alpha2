"""Invariant fingerprint for the n=31 seed=1 exemplar.

The invariants 131 / 15 / 16 are sourced from Appendix D.2 of the design document
(the doc, NOT our generated output), asserted independently so a porting bug cannot
self-certify. On the pinned interpreter (CPython 3.12.13) regenerating n=31 seed=1
must reproduce these values.
"""
import random

# Doc-derived invariants (Appendix D.2). Do NOT derive these from generated output.
EXPECTED_M = 131   # |E(H)|
EXPECTED_NU = 15   # matching_number_H (nu)
EXPECTED_CHI = 16  # chi_G = n - nu


def test_invariants():
    from alpha2.generators.tfp import (
        triangle_free_process,
        is_triangle_free,
        is_edge_maximal_tf,
    )
    from alpha2.invariants.matching import matching_number

    n = 31
    adj, m = triangle_free_process(n, random.Random(1))

    assert m == EXPECTED_M, ("m", m)
    assert matching_number(adj, n) == EXPECTED_NU, ("nu", matching_number(adj, n))
    assert n - matching_number(adj, n) == EXPECTED_CHI, ("chi", n - matching_number(adj, n))
    assert is_triangle_free(adj, n) is True
    assert is_edge_maximal_tf(adj, n) is True
