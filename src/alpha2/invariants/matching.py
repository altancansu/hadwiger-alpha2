"""Exact chromatic number of G = complement(H) via matching (CHI-01).

Verbatim port of matching_number from Appendix C.1. This is the ONLY chi
computation path: chi(G) = n - matching_number(adj, n), where matching_number is
nu(H) = maximum matching computed by Edmonds blossom
(networkx.max_weight_matching, maxcardinality=True). chi is computed exactly and is
never estimated or approximated. networkx is confined to this module.
"""

# ---------- exact chromatic number of G = complement(H) ----------
def matching_number(adj, n):
    import networkx as nx
    Hg = nx.Graph()
    Hg.add_nodes_from(range(n))
    Hg.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
    M = nx.max_weight_matching(Hg, maxcardinality=True)
    return len(M)


def matching_edges(adj, n):
    """Return a maximum matching of H as canonical [min,max] edge pairs (emission).

    The blossom matching stays confined to this module (the CHI-01 AST guard pins
    max_weight_matching to invariants/matching.py). The Tutte-Berge witness
    extractor reuses this instead of calling networkx directly, so the trust-root
    verifier — which re-derives everything from stored H_edges — remains the sole
    authority. |matching_edges(adj, n)| == matching_number(adj, n) by construction.
    """
    import networkx as nx
    Hg = nx.Graph()
    Hg.add_nodes_from(range(n))
    Hg.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
    M = nx.max_weight_matching(Hg, maxcardinality=True)
    return [sorted(int(x) for x in e) for e in M]
