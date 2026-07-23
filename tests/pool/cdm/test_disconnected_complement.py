"""Disconnected-complement carve-out (POOL-0, Open Q1) — catalogued, not escalated.

Some edge-minimal α=2 graphs are DISCONNECTED: exactly when the MTF complement is
complete bipartite K_{a,b}, giving G = K_a ⊔ K_b. Such a G legitimately has NO
connected dominating matching (an edge inside one clique cannot dominate the other),
but it is NOT a Hadwiger counterexample — Conjecture 10 hypothesises *connected* G.

The adjudicator must therefore classify each CDM-FAIL by complement-connectivity and
CATALOGUE a disconnected-complement fail as expected/out-of-scope, NEVER routing it
to E3 as a Hadwiger event (RESEARCH Pitfall 1). This test pins that contract: for
G = K_3 ⊔ K_3 the classifier returns the "disconnected_complement" disposition.

RED until 07-05 lands `alpha2.pool.cdm.adjudicate.classify_cdm_fail`; the import is
function-local so `--collect-only` stays clean.
"""


def test_disconnected_complement_is_catalogued_not_escalated(disjoint_cliques_g_adj):
    """K_a ⊔ K_b CDM-fail is classified disconnected-complement (catalogued)."""
    from alpha2.pool.cdm.adjudicate import classify_cdm_fail  # RED until 07-05

    adj = disjoint_cliques_g_adj
    disposition = classify_cdm_fail(adj, len(adj))
    # Contract: "disconnected_complement" = catalogued out-of-scope; the other
    # disposition ("connected_complement") is the escalation path. A K_a⊔K_b fail
    # must take the CATALOGUE path, never the Hadwiger-escalation path.
    assert disposition == "disconnected_complement"
