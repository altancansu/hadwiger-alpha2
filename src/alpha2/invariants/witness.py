"""Emission-time (UNTRUSTED) Tutte-Berge witness extractor (CHI-02).

`extract_witness(adj, n)` produces the maximum matching M and the Tutte-Berge
witness set U that make chi = n - nu hand-checkable. This runs at CERTIFICATE
EMISSION and is NEVER trusted: the stdlib-only `corpus/verifier.py` re-checks the
Tutte-Berge inequality (|M| == nu and (n - odd_components(H-U) + |U|)/2 == nu)
from the stored record — a wrong M or U simply fails that re-check.

Extraction recipe (Gallai-Edmonds via probing; RESEARCH Pattern 5):
  D = { v : nu(H - v) == nu(H) }   (exposable/inessential vertices)
  A = { u not in D : u has a neighbor in D }
  U = sorted(A)
For factor-critical H (the gate-G3 corpus case) U == [] — but the verifier's check
is GENERAL and this extractor makes no such assumption.

This module is emission-side and MUST NOT be imported by corpus/verifier.py. It
sources its matching from invariants/matching.py (which owns the sole blossom call)
rather than touching a graph library directly.
"""
from alpha2.invariants.matching import matching_edges, matching_number


def _adj_without(adj, n, drop):
    """H with vertex `drop` deleted (isolated: its incident edges removed)."""
    new = [set() for _ in range(n)]
    for u in range(n):
        if u == drop:
            continue
        for v in adj[u]:
            if v != drop:
                new[u].add(v)
    return new


def extract_witness(adj, n):
    """Return (M, U, nu): near-perfect matching edges, witness set, matching number."""
    nu = matching_number(adj, n)
    M = matching_edges(adj, n)
    D = {v for v in range(n) if matching_number(_adj_without(adj, n, v), n) == nu}
    A = {u for u in range(n) if u not in D and any(w in D for w in adj[u])}
    U = sorted(A)
    return M, U, nu
