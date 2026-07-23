"""omega(G), kappa(G), connectivity of G = complement(H) — the CHI-01 sibling.

These are the clique/connectivity invariants the G3/G4 gate checks consume. Exactly as
`invariants/matching.py` is the SOLE exact-chi path, this module is the SOLE
omega/kappa/connectivity path: networkx is confined here (imported INSIDE each function),
and the CHI-01 AST guard (`tests/test_chi_no_estimate.py`) pins
`max_weight_clique`/`node_connectivity`/`is_connected`/`complement` to this file only.

networkx 3.6.1 REMOVED the old clique-number helper; omega(G) is computed via
`max_weight_clique(G, weight=None)` (RESEARCH stale-API gotcha). Every guard RAISES; no
`assert` anywhere (the gate path must survive `python -O`).
"""

# ---------- networkx-confined clique / connectivity of G = complement(H) ----------
def _H_graph(adj, n):
    """Build H as an nx.Graph exactly as matching.py does (nodes range(n); edges u<v).

    Raises on malformed (n, adj); networkx confined to this module.
    """
    import networkx as nx
    if not isinstance(n, int) or n < 0:
        raise ValueError(f"n must be a non-negative int, got {n!r}")
    if len(adj) != n:
        raise ValueError(f"adj has {len(adj)} rows, expected n={n}")
    Hg = nx.Graph()
    Hg.add_nodes_from(range(n))
    Hg.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
    return Hg


def omega_G(adj, n):
    """omega(G) = clique number of G = complement(H). seed-137 (n=31) => 14.

    Uses max_weight_clique(G, weight=None) — the old clique-number helper was removed
    in networkx 3.x, so it is NEVER referenced here.
    """
    import networkx as nx
    G = nx.complement(_H_graph(adj, n))
    clique, _ = nx.max_weight_clique(G, weight=None)
    return len(clique)


def kappa_G(adj, n):
    """kappa(G) = vertex connectivity of G = complement(H). seed-137 => 11."""
    import networkx as nx
    return nx.node_connectivity(nx.complement(_H_graph(adj, n)))


def is_connected_G(adj, n):
    """True iff G = complement(H) is connected. seed-137 => True.

    Raises on n == 0 (is_connected is undefined on the null graph); the gate never
    hands a 0-vertex candidate here.
    """
    import networkx as nx
    if n == 0:
        raise ValueError("is_connected_G undefined for n == 0 (null graph)")
    return nx.is_connected(nx.complement(_H_graph(adj, n)))
