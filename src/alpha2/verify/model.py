"""Independent verifier for K_chi branch-set models (the trust root).

Verbatim port of verify_model from Appendix C.1, assert-based as in the reference
(hardening to explicit exceptions / a `python -O` canary is Phase 2, not now).

Trust-root boundary (research Pattern 3): this module carries a byte-identical
PRIVATE copy of is_conflict rather than reusing the proposer's, so the verifier
depends on none of the proposer modules. It must never pull anything out of
alpha2.search.
"""

# ---------- private is_conflict copy (byte-identical to search/heuristic.py) ----------
def is_conflict(A, B, adj):
    """True iff branch sets A,B are NON-adjacent in G (all cross pairs are H-edges)."""
    for x in A:
        ax = adj[x]
        for y in B:
            if y not in ax:
                return False
    return True

# ---------- independent verifier ----------
def verify_model(sets, adj, n, k):
    assert len(sets) == k, "wrong number of branch sets"
    used = set()
    for S in sets:
        assert len(S) in (1, 2), "branch set size must be 1 or 2"
        for v in S:
            assert 0 <= v < n and v not in used, "branch sets not disjoint"
            used.add(v)
        if len(S) == 2:
            a, b = S
            assert b not in adj[a], "pair is not an edge of G"
    for i in range(k):
        for j in range(i + 1, k):
            assert not is_conflict(sets[i], sets[j], adj), \
                f"branch sets {i},{j} not adjacent in G"
    return True
