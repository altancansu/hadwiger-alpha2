"""Per-instance CDM adjudication runbook (POOL-0) — the Wave-3 integration.

`adjudicate_instance` decodes one MTF survivor, runs the DUAL decision (the trusted
DFS reference `has_cdm` ≡ the CP-SAT cross-check `cdm_cpsat`), and DISPATCHES on the
outcome; `adjudicate_batch` drives it over the full n=12–14 frontier via `stream_mtf`.
It owns NO new CDM mathematics — it wires the already-built decide/verify/store legs
together in the §"System Architecture" order (07-RESEARCH.md), mirroring the battery
runbook (`battery/pipeline.run_candidate`) and the differential agreement gate
(`solvers/differential.differential_verdict` / `CriticalDisagreement`).

networkx confinement (07-PATTERNS.md): this is the ONLY module besides `generate.py`
permitted to touch a graph library, and it is confined to the DECODE/CLASSIFY
boundary — `from_graph6_bytes` (decode H), `complement` (G = Ḡ), `is_connected`
(the Open-Q1 carve-out). The reference/verifier/store legs never see a graph object;
they consume a plain `adj = list[set[int]]` or a stored record.

The runbook per instance (Asymmetry Principle enforced end to end):

  [0] Decode.  H = from_graph6_bytes(g6); ASSERT H.number_of_nodes() == n (V5
      boundary: an untrusted-but-bounded graph6 whose decoded n ≠ the requested n
      is rejected before it is adjudicated). G = complement(H); adj = list[set].
  [1] Dual decide.  witness = has_cdm(adj, n) (reference/arbiter, M or None) and
      sat = cdm_cpsat(adj, n) (independent second engine). Agreement gate:
      (witness is not None) != sat  ->  raise CDMCriticalDisagreement (quarantine +
      HALT the batch; never pick a winner — mirrors solvers/differential).
  [2a] CDM-HOLDS (cheap, stored existence).  build_cdm_record(...,
      complement_connected=is_connected(G), generation=<SC1 provenance>) -> route the
      witness through the stdlib trust root `verify_cdm_witness` -> append_certificate
      to paths.CDM_CORPUS. Nothing counts as found until the independent verifier passes.
  [2b] CDM-FAILS (radioactive impossibility).  classify complement-connectivity:
      * disconnected complement (K_a ⊔ K_b, complete-bipartite H) — the EXPECTED
        carve-out (Open Q1): catalogue out-of-scope, NEVER escalate, no battery call.
      * connected complement — the RADIOACTIVE, Hadwiger-relevant event (not expected
        under Conjecture 10): route to the existing battery (`run_candidate` had₂
        dual-backend) + record + quarantine (the escalation HOOK; full E3 → Phase 11).

stdlib + networkx (decode/classify only) + the sibling CDM legs; the frozen
296-instance had_2 corpus and its trust root are byte-untouched.
"""
import networkx as nx

from alpha2.battery.log import append_event
from alpha2.pool.cdm.cpsat import cdm_cpsat
from alpha2.pool.cdm.generate import provenance_for, stream_mtf
from alpha2.pool.cdm.reference import has_cdm
from alpha2.pool.cdm.schema import build_cdm_record
from alpha2.pool.cdm.store import append_certificate
from alpha2.pool.cdm.verifier import verify_cdm_witness

# Verdict tags (returned by adjudicate_instance; aggregated by adjudicate_batch).
HOLDS = "CDM-HOLDS"
FAIL_DISCONNECTED = "CDM-FAIL:disconnected_complement"
FAIL_CONNECTED = "CDM-FAIL:connected_complement"

_METHOD = "dfs reference + cp-sat cross-check (CDM)"


class CDMCriticalDisagreement(Exception):
    """Release-blocking: the DFS reference and the CP-SAT cross-check disagree on one
    instance's CDM verdict. Two independent engines cannot both be right about a
    decision, so a mismatch is a solver/encoding bug BY CONSTRUCTION: quarantine the
    instance and HALT the batch — never pick a winner, never skip (mirrors
    solvers/differential.CriticalDisagreement)."""


class ConnectedComplementCDMFail(Exception):
    """Release-blocking RADIOACTIVE event: a CONNECTED-complement graph with α=2 that
    fails CDM. Not expected under CLWY Conjecture 10; if it ever fires it is the
    Hadwiger-relevant finding, not a bug to route around. The escalation hook records
    it (battery had₂ dual-backend cross-check + event log) and quarantines + HALTS —
    full E1/E2/E3 reproduction is deferred to Phase 11."""


def _decode(graph6, n):
    """Decode graph6 -> H, ASSERT decoded n == requested n (V5), return (H, G, adj_G).

    The decoded-n check is the trust boundary T-7-10: a graph6 line is untrusted-but-
    bounded external input, and a size mismatch (a truncated/forged line) must be
    rejected before the graph is adjudicated, never silently decoded at the wrong n.
    """
    H = nx.from_graph6_bytes(graph6.encode())
    if H.number_of_nodes() != n:
        raise ValueError(
            f"decoded n mismatch (V5 boundary): graph6 {graph6!r} decodes to "
            f"{H.number_of_nodes()} vertices, requested n={n}"
        )
    G = nx.complement(H)
    adj = [set(G.neighbors(u)) for u in range(G.number_of_nodes())]
    return H, G, adj


def _adj_to_graph(adj, n):
    """Build a plain nx.Graph from a G-adjacency `adj = list[set[int]]` (n nodes)."""
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for u in range(n):
        for v in adj[u]:
            if u < v:
                G.add_edge(u, v)
    return G


def classify_cdm_fail(adj, n):
    """Classify a CDM-FAIL by complement-connectivity (Open Q1 carve-out, Pitfall 1).

    `adj` is G's adjacency (G = complement of the MTF graph H). Returns:
      * "disconnected_complement" — G is DISCONNECTED (⟺ H complete-bipartite,
        G = K_a ⊔ K_b): an EXPECTED, legitimate CDM-fail (an edge inside one clique
        cannot dominate the other). Catalogued out-of-scope; NEVER a Hadwiger event.
      * "connected_complement" — G is CONNECTED: an UNEXPECTED, radioactive CDM-fail
        (the escalation path). Under Conjecture 10 this should never occur at n≤14.

    This classification happens BEFORE any escalation, so a K_a ⊔ K_b fail is never
    mis-routed to the battery/E3 as a Hadwiger anomaly (RESEARCH Pitfall 1).
    """
    G = _adj_to_graph(adj, n)
    return "connected_complement" if nx.is_connected(G) else "disconnected_complement"


def _escalate_connected_complement_fail(graph6, n, adj, provenance, log_path=None):
    """Escalation HOOK for a connected-complement CDM-fail (RESEARCH Open Q4).

    A connected α=2 graph that fails CDM is the radioactive, Hadwiger-relevant event.
    This hook routes it to the existing battery (`battery.pipeline.run_candidate`'s
    had₂ dual-backend, run here directly on the CDM-failing G to ask whether SHC/had₂
    still holds), RECORDS the event to the append-only results log, and QUARANTINES by
    raising `ConnectedComplementCDMFail` (release-blocking HALT). Full E1/E2/E3
    independent reproduction is deferred to Phase 11; at n≤14 this path is a safety
    net, not a mainline — it should never fire under Conjecture 10.
    """
    # Route to the battery had₂ dual-backend (CBC + CP-SAT) on the failing G, mirroring
    # run_candidate step [4]: does the size-≤2 SHC model (had₂ = χ) still hold here?
    from alpha2.battery import pipeline as battery_pipeline  # escalation target
    from alpha2.invariants.matching import matching_number
    from alpha2.solvers.backend import get_backend
    from alpha2.solvers.differential import differential_verdict
    from alpha2.solvers.result import SolveParams

    _ = battery_pipeline.run_candidate  # the deferred full-E3 escalation entrypoint
    chi = n - matching_number(adj, n)
    had2_verdict = None
    try:
        a = get_backend("cbc").solve_had2(
            adj, n, mode="optimize", params=SolveParams(time_limit_s=600.0)
        )
        b = get_backend("cpsat").solve_had2(
            adj, n, mode="optimize", params=SolveParams(time_limit_s=600.0)
        )
        had2_verdict = differential_verdict(a, b, chi)
    except Exception as exc:  # noqa: BLE001 — record any backend disagreement, then halt
        had2_verdict = f"had2-escalation-error: {exc}"

    reason = (
        f"RADIOACTIVE connected-complement CDM-FAIL (Hadwiger-relevant, quarantine + "
        f"HALT): graph6={graph6!r} n={n} chi={chi} had2_dual_backend={had2_verdict!r}"
    )
    append_event(
        {
            "subsystem": "pool/cdm",
            "event": "connected_complement_cdm_fail",
            "graph6": graph6,
            "n": n,
            "terminal_state": "QUARANTINED",
            "reason": reason,
            "provenance": provenance,
            "had2_dual_backend": str(had2_verdict),
        },
        path=log_path,
    )
    raise ConnectedComplementCDMFail(reason)


def adjudicate_instance(
    graph6,
    n,
    *,
    provenance,
    generation=None,
    corpus_path=None,
    log_path=None,
):
    """Adjudicate one MTF survivor for CDM; return a JSON-serializable verdict dict.

    Decodes `graph6` (asserting decoded n == `n`), runs the dual decision, and
    dispatches: CDM-HOLDS verifies + appends a certificate (carrying `generation`, the
    SC1 per-instance provenance) to `corpus_path` (default paths.CDM_CORPUS);
    CDM-FAILS classifies complement-connectivity and either catalogues the disconnected
    carve-out or routes a connected-complement fail through the escalation hook. Raises
    `CDMCriticalDisagreement` on any DFS≡CP-SAT mismatch (batch-halting).
    """
    H, G, adj = _decode(graph6, n)

    witness = has_cdm(adj, n)          # reference / arbiter: M (list of a<b edges) or None
    dfs_holds = witness is not None
    sat_holds = cdm_cpsat(adj, n)      # independent CP-SAT cross-check (boolean)

    # ---- Dual-decision agreement gate (release-blocking; never pick a winner). ----
    if dfs_holds != sat_holds:
        reason = (
            f"DFS≡CP-SAT DISAGREEMENT (release-blocking, quarantine + HALT): "
            f"graph6={graph6!r} n={n} DFS={dfs_holds} CP-SAT={sat_holds}"
        )
        append_event(
            {
                "subsystem": "pool/cdm",
                "event": "critical_disagreement",
                "graph6": graph6,
                "n": n,
                "terminal_state": "QUARANTINED",
                "reason": reason,
                "provenance": provenance,
            },
            path=log_path,
        )
        raise CDMCriticalDisagreement(reason)

    complement_connected = bool(nx.is_connected(G)) if n >= 1 else False

    if dfs_holds:
        # ---- [2a] CDM-HOLDS: cheap stored existence, verified before it counts. ----
        H_edges = sorted([min(u, v), max(u, v)] for u, v in H.edges())
        matching_M = [[int(a), int(b)] for (a, b) in witness]
        rec = build_cdm_record(
            provenance=provenance,
            H_edges=H_edges,
            matching_M=matching_M,
            complement_connected=complement_connected,
            method=_METHOD,
            generation=generation,
            verified=True,
        )
        verify_cdm_witness(rec)   # trust root re-check — nothing counts until it passes
        append_certificate(rec, path=corpus_path)   # append-only, verify-at-append
        append_event(
            {
                "subsystem": "pool/cdm",
                "event": "cdm_holds",
                "graph6": graph6,
                "n": n,
                "terminal_state": "CDM-HOLDS",
                "reason": f"CDM witness verified + appended (|M|={len(matching_M)})",
                "provenance": provenance,
            },
            path=log_path,
        )
        return {
            "graph6": graph6,
            "n": n,
            "verdict": HOLDS,
            "complement_connected": complement_connected,
            "matching_M": matching_M,
            "certificate_appended": True,
        }

    # ---- [2b] CDM-FAILS: classify complement-connectivity BEFORE any escalation. ----
    disposition = classify_cdm_fail(adj, n)
    if disposition == "disconnected_complement":
        # EXPECTED carve-out (K_a ⊔ K_b): catalogue out-of-scope. NO escalation, NO
        # battery call (RESEARCH Pitfall 1) — this is not a Hadwiger event.
        append_event(
            {
                "subsystem": "pool/cdm",
                "event": "disconnected_complement_carveout",
                "graph6": graph6,
                "n": n,
                "terminal_state": "OUT-OF-SCOPE",
                "reason": "K_a ⊔ K_b disconnected-complement CDM-fail: catalogued, not escalated",
                "provenance": provenance,
            },
            path=log_path,
        )
        return {
            "graph6": graph6,
            "n": n,
            "verdict": FAIL_DISCONNECTED,
            "complement_connected": False,
            "matching_M": None,
            "certificate_appended": False,
        }

    # connected_complement — the radioactive escalation path (should never fire ≤14).
    _escalate_connected_complement_fail(graph6, n, adj, provenance, log_path=log_path)
    # _escalate always raises; the return is unreachable but keeps the function total.
    return {
        "graph6": graph6,
        "n": n,
        "verdict": FAIL_CONNECTED,
        "complement_connected": True,
        "matching_M": None,
        "certificate_appended": False,
    }


def adjudicate_batch(ns, res=None, mod=None, *, corpus_path=None, log_path=None):
    """Adjudicate the full MTF frontier over `ns` (e.g. [12, 13, 14]); return a summary.

    Iterates `stream_mtf(n, res, mod)` per n; for each survivor builds the schema-v1
    graph6 provenance + its SC1 `generation` sidecar via `provenance_for`, then calls
    `adjudicate_instance`. Aggregates: total adjudicated, #CDM-HOLDS (certificated),
    #disconnected carve-outs, #connected-complement fails (expected 0). A
    `CDMCriticalDisagreement` or `ConnectedComplementCDMFail` propagates (batch HALTS)
    — those are findings to surface, not exceptions to swallow.
    """
    summary = {
        "total": 0,
        "holds": 0,
        "disconnected_carveouts": 0,
        "connected_fails": 0,
        "per_n": {},
    }
    for n in ns:
        n_total = n_holds = n_disc = n_conn = 0
        for index, g6, shard in stream_mtf(n, res, mod):
            prov = provenance_for(n, g6, shard, index)
            generation = prov.get("params")   # {geng_version, flags, shard, index} (SC1)
            result = adjudicate_instance(
                g6,
                n,
                provenance=prov,
                generation=generation,
                corpus_path=corpus_path,
                log_path=log_path,
            )
            n_total += 1
            verdict = result["verdict"]
            if verdict == HOLDS:
                n_holds += 1
            elif verdict == FAIL_DISCONNECTED:
                n_disc += 1
            else:
                n_conn += 1
        summary["per_n"][n] = {
            "total": n_total,
            "holds": n_holds,
            "disconnected_carveouts": n_disc,
            "connected_fails": n_conn,
        }
        summary["total"] += n_total
        summary["holds"] += n_holds
        summary["disconnected_carveouts"] += n_disc
        summary["connected_fails"] += n_conn
    return summary
