"""A1 definition-regression gate (POOL-0) — the HIGHEST-priority CDM test.

Reproduces the Costa–Luu–Wood–Yip (arXiv:2512.17114) result: **every connected
graph G with α(G)=2 on n≤11 vertices has a non-empty connected dominating matching
(CDM).** This is the ONLY independent check that our A1 reading of vertex-edge
adjacency in the *dominating* condition ("w adjacent to edge e ⟺ w adjacent to ≥1
endpoint of e", RESEARCH §DFS / Pitfall 4) matches CLWY's CDM. Dual-engine (DFS ≡
CP-SAT) agreement CANNOT catch a shared wrong A1 reading — only reproducing the
paper's exhaustive n≤11 result can.

The `mtf_n_le_11_graph6` fixture is the FULL connected maximal-triangle-free set at
every n≤11 (134 graphs; 61 at n=11), NOT a hand-picked sample: a subtly wrong
definition can pass on a handful yet fail on an unsampled graph, so the gate
iterates ALL of them.

>>> Any connected α=2 graph at n≤11 reported CDM-less is a DEFINITION bug (A1),
>>> NOT new science. <<<

RED until 07-02 lands `alpha2.pool.cdm.reference.has_cdm` — the import is
function-local so `--collect-only` stays clean while the body errors.
"""
import networkx as nx


def _g_adj_from_h_graph6(g6):
    """Decode an MTF graph6 (H), take the complement G (α=2), return (adj, n, connected).

    adj = list[set[int]] is G's adjacency (the convention has_cdm consumes). The
    disconnected complements (G = K_a ⊔ K_b, H = complete bipartite) are legitimately
    outside the connected-frontier claim and reported via `connected=False`.
    """
    H = nx.from_graph6_bytes(g6.encode())
    G = nx.complement(H)
    n = G.number_of_nodes()
    adj = [set(G.neighbors(u)) for u in range(n)]
    return adj, n, nx.is_connected(G)


def test_every_connected_alpha2_graph_n_le_11_has_cdm(mtf_n_le_11_graph6):
    """Definition gate: has_cdm returns a witness for EVERY connected α=2 graph n≤11."""
    from alpha2.pool.cdm.reference import has_cdm  # RED until 07-02

    checked = 0
    for n in sorted(mtf_n_le_11_graph6):
        for g6 in mtf_n_le_11_graph6[n]:
            adj, nn, connected = _g_adj_from_h_graph6(g6)
            if not connected:
                # Disconnected complement (K_a ⊔ K_b) — carve-out, not the gate.
                continue
            M = has_cdm(adj, nn)
            assert M is not None, (
                f"connected α=2 graph n={nn} g6={g6!r} reported CDM-less — this "
                "contradicts CLWY's n≤11 result and indicates a DEFINITION bug in "
                "the A1 vertex-edge adjacency reading, NOT new science"
            )
            checked += 1
    # Sanity: the gate actually iterated the full connected set (not a vacuous
    # pass). Of the 134 embedded MTF-complements, exactly floor(n/2) per n are
    # complete-bipartite complements G = K_a ⊔ K_b (disconnected, carved out
    # above): 1+2+2+3+3+4+4+5+5 = 29 disconnected, so 134 − 29 = 105 connected
    # instances every one of which must report CDM.
    assert checked == 105, f"expected 105 connected instances, checked {checked}"


def test_disconnected_complement_has_no_cdm(disjoint_cliques_g_adj):
    """The carve-out direction: G = K_a ⊔ K_b (disconnected) has NO CDM → None."""
    from alpha2.pool.cdm.reference import has_cdm  # RED until 07-02

    adj = disjoint_cliques_g_adj
    assert has_cdm(adj, len(adj)) is None
