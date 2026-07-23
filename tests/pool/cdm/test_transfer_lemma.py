"""Transfer-lemma predicates (POOL-0, ROADMAP SC3) — the two executable ingredients.

The transfer lemma ("verify CDM on the MTF-complements ⟹ CDM for every connected
α=2 graph at n") rests on two testable predicates:

  1. **Lemma 2.5 equivalence** (CLWY): for a connected triangle-free graph H on ≥3
     vertices, edge-maximal-triangle-free ⟺ diameter(H) == 2. Checked here over the
     FULL connected n≤11 MTF survivor set (the embedded oracle) using the repo's
     independent `is_edge_maximal_tf` vs `networkx.diameter`. This leg is
     self-contained and runs NOW (no CDM module needed) — the empirical backbone of
     the in-repo proof.

  2. **CDM edge-addition monotonicity** (prove in-repo): if G has a non-empty
     connected dominating matching M and G' = G + one non-edge (still α≤2), then M
     is STILL a connected dominating matching in G' — "connected" and "dominating"
     are adjacency-POSITIVE, and adjacency only increases. Hence CDM(G) ⟹ CDM(G').
     RED until 07-02 (`has_cdm`); its import is function-local.
"""
import networkx as nx


def test_lemma_2_5_edge_maximal_iff_diameter_2(mtf_n_le_11_graph6):
    """Lemma 2.5: over the full connected n≤11 MTF set, edge-maximal-tf ⟺ diam==2."""
    from alpha2.generators.tfp import is_edge_maximal_tf

    checked = 0
    for n in sorted(mtf_n_le_11_graph6):
        for g6 in mtf_n_le_11_graph6[n]:
            H = nx.from_graph6_bytes(g6.encode())
            nn = H.number_of_nodes()
            adj = [set(H.neighbors(u)) for u in range(nn)]
            edge_maximal = is_edge_maximal_tf(adj, nn)
            diam2 = nx.is_connected(H) and nx.diameter(H) == 2
            assert edge_maximal == diam2, (
                f"Lemma 2.5 violated n={nn} g6={g6!r}: "
                f"edge_maximal={edge_maximal} diam2={diam2}"
            )
            checked += 1
    assert checked == 134, f"expected 134 MTF survivors n≤11, checked {checked}"


def test_cdm_monotone_under_edge_addition(c5_g_adj):
    """Monotonicity: adding any α-preserving non-edge to a CDM graph preserves CDM."""
    from alpha2.pool.cdm.reference import has_cdm  # RED until 07-02

    adj = c5_g_adj
    n = len(adj)
    assert has_cdm(adj, n) is not None  # C5 has a CDM to begin with

    non_edges = [
        (u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]
    ]
    assert non_edges, "C5 must have non-edges to add"
    for u, v in non_edges:
        # Adding an edge to an α=2 graph never raises α above 2, so G' stays in-scope.
        adj2 = [set(s) for s in adj]
        adj2[u].add(v)
        adj2[v].add(u)
        assert has_cdm(adj2, n) is not None, (
            f"CDM not preserved after adding non-edge ({u},{v}) — monotonicity broken"
        )
