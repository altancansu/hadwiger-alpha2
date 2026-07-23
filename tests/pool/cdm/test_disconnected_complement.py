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


def test_disconnected_complement_makes_no_battery_escalation(
    disjoint_cliques_h_graph6, tmp_path, monkeypatch
):
    """Full runbook on K_a⊔K_b: catalogued CDM-FAIL, NO escalation / battery call.

    Routing the disconnected-complement fail through `adjudicate_instance` must take
    the OUT-OF-SCOPE carve-out and never touch the battery/E3 escalation hook
    (RESEARCH Pitfall 1). We spy on the escalation entrypoint and assert it stays
    uncalled, and that no certificate is written for a CDM-FAIL.
    """
    from alpha2.pool.cdm import adjudicate

    escalated = {"called": False}

    def _spy(*args, **kwargs):
        escalated["called"] = True
        raise AssertionError("disconnected-complement fail must NOT escalate")

    monkeypatch.setattr(adjudicate, "_escalate_connected_complement_fail", _spy)

    g6 = disjoint_cliques_h_graph6  # H = K_{3,3} (n=6); G = K_3 ⊔ K_3 (disconnected)
    provenance = {"kind": "graph6", "family": "mtf_complement", "n": 6, "graph6": g6}
    result = adjudicate.adjudicate_instance(
        g6,
        6,
        provenance=provenance,
        corpus_path=tmp_path / "cdm_certs.json",
        log_path=tmp_path / "events.jsonl",
    )

    assert result["verdict"] == adjudicate.FAIL_DISCONNECTED
    assert result["complement_connected"] is False
    assert result["certificate_appended"] is False
    assert escalated["called"] is False  # NO battery/E3 call on a benign carve-out
