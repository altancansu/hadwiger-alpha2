"""Per-instance sum-free g(G) runbook (POOL-2) — the P2 break-hunt spine, complete.

`adjudicate_sumfree(descriptor, *, seed, det_time, det_nodes, ...)` turns ONE
`{invariant_factors, S, tag}` descriptor into a stored, verified, honestly-labelled g(G)
verdict. It owns NO new mathematics — it wires the already-built generation / gate /
matching / heuristic / screen / trust-root / store legs together in the §"System
Architecture" order, mirroring the battery runbook (`battery/pipeline.run_candidate`) and
the CDM runbook (`pool/cdm/adjudicate.adjudicate_instance`).

Why NOT `run_candidate`: it regenerates the instance from `(family, seed)` and its
`_generate` ignores `params` — it cannot consume an abelian descriptor + RNG contract v2.
P2 needs the descriptor-built adjacency, so the runbook legs are REPLICATED here on the
descriptor-built `adj` (exactly as `pool/cdm/adjudicate` replicates the escalation legs).

The runbook per descriptor (Asymmetry Principle end to end):

  [0] Build.  Abelian(invariant_factors); S from the descriptor or generated for its tag;
      adj_H = cayley_adj_abelian(group, S); n = group.n. Re-check S is symmetric + sum-free
      + maximal (`verify_sumfree_maximal`) — the descriptor is untrusted-but-bounded (V5;
      the group order is already capped n<=500 by Abelian).
  [1] Gate.  run_gate(adj_H, n, inv); a HARD G1/G2/connectivity fail -> KILLED-BY-GATE, a
      FIRST-CLASS non-g outcome (results-log only, NO g, NO certificate). The g-plot is
      over gate survivors only (T-8-13).
  [2] chi = n - matching_number(adj_H, n).
  [3] Heuristic.  solve(adj, n, chi, search_rng(seed)) HIT -> the size-<=2 family is routed
      through the frozen trust root (verify_certificate) -> KILLED(g<=0) stored. A MISS is
      an UNCONDITIONAL edge to the exact screen (never RESISTANT here).
  [4/5] screen_gap (det_time + det_nodes) -> terminal_state + g. KILLED(g<=0) carries the
      trust-root-verified family; SHC_CANDIDATE(g>0) carries HONEST_G_POSITIVE_STATEMENT
      (never "counterexample" / "had(G) <"); RESISTANT (had_k None, g None) is logged as an
      E3-queue entry (never a reported g>0). Every stored record is verified before append
      via `append_gscreen_certificate`.

Every recorded verdict is a deterministic function of (n, seed): BOTH co-equal backends are
node/work-count bounded (CP-SAT det_time, CBC det_nodes) — never wall-clock (T-8-07).
`CriticalDisagreement` propagates (QUARANTINE + HALT — never pick a winner).

networkx is confined to the matching/cliques/witness legs (imported by those modules); this
runbook consumes plain `adj`/records, mirroring the CDM runbook's confinement discipline.
"""
from alpha2.battery.log import append_event
from alpha2.invariants import cliques
from alpha2.invariants.matching import matching_number
from alpha2.pool.sumfree import screen as screen_mod
from alpha2.pool.sumfree.generate import (
    cayley_adj_abelian,
    green_ruzsa_sumfree,
    middle_interval_sumfree,
    random_maximal_symmetric_sumfree,
    verify_sumfree_maximal,
)
from alpha2.pool.sumfree.group import Abelian
from alpha2.pool.sumfree.rng import gen_rng, search_rng
from alpha2.pool.sumfree.schema import (
    HONEST_G_POSITIVE_STATEMENT,
    build_gscreen_record,
    honest_statement_for,
)
from alpha2.pool.sumfree.screen import screen_gap, trust_root_verify_family
from alpha2.pool.sumfree.store import append_gscreen_certificate
from alpha2.search.heuristic import solve

# Terminal states (mirrors screen.py; KILLED-BY-GATE is a first-class non-g outcome).
KILLED = "KILLED"
SHC_CANDIDATE = "SHC_CANDIDATE"
RESISTANT = "RESISTANT"
KILLED_BY_GATE = "KILLED-BY-GATE"

_DET_NODES_PER_BUDGET_UNIT = 100_000   # coarse machine-INDEPENDENT det_nodes per det_budget

_SUBSYSTEM = "pool/sumfree"


def _h_edges(adj, n):
    """Canonical sorted [min, max] H-edge pairs (frozen Phase-1 convention)."""
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _resolve_S(descriptor, group, seed):
    """Return the sum-free set S: the descriptor's own S, or one generated for its tag.

    A descriptor may pin `S` explicitly (byte-identical rebuild), or carry `S: None` and a
    `tag` in {"structured", "random"}: structured -> Green-Ruzsa (fallback middle-interval)
    over the arithmetic of |Gamma|; random -> greedy-maximal over `gen_rng(seed)`. The set
    is re-checked symmetric + sum-free + maximal by every generator before it is returned.
    """
    S = descriptor.get("S")
    if S is not None:
        S = {tuple(s) for s in S}
        verify_sumfree_maximal(group, S)   # untrusted-but-bounded descriptor (V5) re-check
        return S

    tag = descriptor.get("tag", "structured")
    if tag == "structured":
        try:
            return green_ruzsa_sumfree(group)
        except (ValueError, NotImplementedError):
            return middle_interval_sumfree(group)
    if tag == "random":
        return random_maximal_symmetric_sumfree(group, gen_rng(seed))
    raise ValueError(f"descriptor tag must be structured|random, got {tag!r}")


def _provenance(descriptor, group, S, tag):
    """The g(G) descriptor provenance the certificate schema validates + stores."""
    return {
        "kind": "descriptor",
        "family": "sumfree_cayley",
        "tag": tag,
        "n": group.n,
        "invariant_factors": list(group.factors),
        "S": sorted(tuple(int(x) for x in s) for s in S),
    }


def _emit(log_path, **event):
    """Append one runbook event (terminal_state, method, g, kind, |Gamma|) to the log."""
    append_event({"subsystem": _SUBSYSTEM, **event}, path=log_path)


def _verdict(descriptor, n, seed, tag, *, gate_survived, terminal_state, g,
             had_2, had_3, certificate_appended, statement=None):
    """The JSON-serializable per-instance verdict dict the sweep aggregates."""
    return {
        "descriptor": descriptor,
        "n": n,
        "seed": seed,
        "kind": tag,
        "gate_survived": gate_survived,
        "terminal_state": terminal_state,
        "g": g,
        "had_2": had_2,
        "had_3": had_3,
        "certificate_appended": certificate_appended,
        "certificate_statement": statement,
    }


def adjudicate_sumfree(descriptor, *, seed, det_time, det_nodes, corpus_path=None, log_path=None):
    """Run the full g(G) runbook on ONE descriptor; return a JSON verdict dict.

    `det_time` (CP-SAT) and `det_nodes` (CBC) thread through unchanged so every recorded
    verdict is a deterministic function of (n, seed). A HARD gate fail is KILLED-BY-GATE
    (first-class, no g, no certificate); a heuristic HIT is a trust-root-verified KILLED
    (g<=0); the screen tiering yields KILLED / SHC_CANDIDATE (g>0, honest statement) /
    RESISTANT (E3 queue). `CriticalDisagreement` propagates (QUARANTINE + HALT).
    """
    # ---- [0] Build the group + adjacency from the (untrusted-but-bounded) descriptor. ----
    group = Abelian(descriptor["invariant_factors"])   # V5: n<=500 cap enforced here
    tag = descriptor.get("tag", "structured")
    S = _resolve_S(descriptor, group, seed)
    adj = cayley_adj_abelian(group, S)
    n = group.n
    prov = _provenance(descriptor, group, S, tag)

    # ---- [2] Exact chi + gate inputs (computed before the checks consume them). ----
    nu = matching_number(adj, n)
    chi = n - nu
    omega = cliques.omega_G(adj, n)
    kappa = cliques.kappa_G(adj, n)
    inv = {"nu_H": nu, "chi_G": chi, "omega_G": omega, "kappa_G": kappa}

    # ---- [1] Gate (D-01 Role B). A HARD fail is a FIRST-CLASS KILLED-BY-GATE outcome. ----
    from alpha2.gate.runner import Verdict, run_gate   # gate legs imported at use site
    gate = run_gate(adj, n, inv)
    if gate.verdict is Verdict.KILLED:
        reason = f"hard-gate KILL at {gate.killing}: {gate.witness}"
        _emit(log_path, event="killed_by_gate", n=n, kind=tag, terminal_state=KILLED_BY_GATE,
              method=f"gate:{gate.killing}", g=None, reason=reason, gamma=list(group.factors))
        return _verdict(descriptor, n, seed, tag, gate_survived=False,
                        terminal_state=KILLED_BY_GATE, g=None, had_2=None, had_3=None,
                        certificate_appended=False)
    if gate.verdict is Verdict.ERROR:
        # A quarantining gate error is NEVER a kill: surface it, do not screen.
        reason = f"gate quarantined (never a kill): {gate.error.trace}"
        _emit(log_path, event="gate_error", n=n, kind=tag, terminal_state="QUARANTINED",
              method="gate", g=None, reason=reason, gamma=list(group.factors))
        return _verdict(descriptor, n, seed, tag, gate_survived=False,
                        terminal_state="QUARANTINED", g=None, had_2=None, had_3=None,
                        certificate_appended=False)

    # ---- [3] Heuristic size-<=2 model search. A HIT is UNTRUSTED until the trust root. ----
    sets, _init, _moves, _restarts, _t = solve(adj, n, chi, search_rng(seed))
    if sets is not None:
        family = [list(s) for s in sets]
        k = trust_root_verify_family(adj, n, chi, family)   # SOLE family authority
        if k is not None:
            g = screen_mod.compute_g(chi, k)
            statement = honest_statement_for(KILLED, k, chi)
            rec = build_gscreen_record(
                provenance=prov, H_edges=_h_edges(adj, n), chi=chi, had_2=k, had_3=None,
                terminal_state=KILLED, certificate_statement=statement,
                method="heuristic K_chi HIT + trust-root verify (sumfree g-screen)",
                model_branch_sets=family, verified=True,
            )
            append_gscreen_certificate(rec, path=corpus_path)
            _emit(log_path, event="killed_heuristic", n=n, kind=tag, terminal_state=KILLED,
                  method="heuristic", g=g, reason=f"verified K_chi model had_2={k}",
                  gamma=list(group.factors))
            return _verdict(descriptor, n, seed, tag, gate_survived=True, terminal_state=KILLED,
                            g=g, had_2=k, had_3=None, certificate_appended=True,
                            statement=statement)
        # A heuristic proposal that fails the trust root is NOT a result: fall through to
        # the exact screen (never a heuristic-only claim; Pitfall 1).

    # ---- [4/5] Exact had_2 -> had_3 screen tiering under the deterministic budget. ----
    outcome = screen_gap(adj, n, chi, det_time=det_time, det_nodes=det_nodes)

    if outcome.terminal_state == RESISTANT:
        # No exact bound proved in budget: queue for E3, NEVER a reported g>0.
        _emit(log_path, event="resistant_e3_queue", n=n, kind=tag, terminal_state=RESISTANT,
              method="exact-screen", g=None,
              reason="no exact had_k proved in deterministic budget -> E3 queue",
              gamma=list(group.factors))
        return _verdict(descriptor, n, seed, tag, gate_survived=True, terminal_state=RESISTANT,
                        g=None, had_2=outcome.had_2, had_3=None, certificate_appended=False)

    if outcome.terminal_state == KILLED:
        # g<=0 packs. The screen family is UNTRUSTED — route it through the trust root.
        family = outcome.family
        k = trust_root_verify_family(adj, n, chi, family)
        if k is None:
            # Family did not certify: conservatively RESISTANT (no unverified kill).
            _emit(log_path, event="resistant_unverified_family", n=n, kind=tag,
                  terminal_state=RESISTANT, method="exact-screen", g=None,
                  reason="screen KILL family failed the trust root -> E3 queue",
                  gamma=list(group.factors))
            return _verdict(descriptor, n, seed, tag, gate_survived=True,
                            terminal_state=RESISTANT, g=None, had_2=outcome.had_2, had_3=None,
                            certificate_appended=False)
        had_deciding = outcome.had_3 if outcome.had_3 is not None else outcome.had_2
        statement = honest_statement_for(KILLED, had_deciding, chi)
        rec = build_gscreen_record(
            provenance=prov, H_edges=_h_edges(adj, n), chi=chi,
            had_2=outcome.had_2, had_3=outcome.had_3, terminal_state=KILLED,
            certificate_statement=statement,
            method="dual-backend exact had_2/had_3 AGREED_KILL + trust-root verify",
            model_branch_sets=family, verified=True,
        )
        append_gscreen_certificate(rec, path=corpus_path)
        _emit(log_path, event="killed_exact", n=n, kind=tag, terminal_state=KILLED,
              method="exact-screen", g=outcome.g, reason=f"AGREED_KILL had_k={had_deciding}",
              gamma=list(group.factors))
        return _verdict(descriptor, n, seed, tag, gate_survived=True, terminal_state=KILLED,
                        g=outcome.g, had_2=outcome.had_2, had_3=outcome.had_3,
                        certificate_appended=True, statement=statement)

    # outcome.terminal_state == SHC_CANDIDATE: g>0 screen. HONEST statement ONLY.
    statement = HONEST_G_POSITIVE_STATEMENT.format(had_3=outcome.had_3, chi=chi)
    rec = build_gscreen_record(
        provenance=prov, H_edges=_h_edges(adj, n), chi=chi,
        had_2=outcome.had_2, had_3=outcome.had_3, terminal_state=SHC_CANDIDATE,
        certificate_statement=statement,
        method="dual-backend had_2->had_3 seagull Tier-1 PROVED_OPTIMAL (screen)",
        model_branch_sets=None, verified=True,
    )
    append_gscreen_certificate(rec, path=corpus_path)
    _emit(log_path, event="shc_candidate", n=n, kind=tag, terminal_state=SHC_CANDIDATE,
          method="exact-screen", g=outcome.g,
          reason=f"g>0 screen: had_3={outcome.had_3} < chi={chi} (E3 queue, NOT a break)",
          gamma=list(group.factors))
    return _verdict(descriptor, n, seed, tag, gate_survived=True, terminal_state=SHC_CANDIDATE,
                    g=outcome.g, had_2=outcome.had_2, had_3=outcome.had_3,
                    certificate_appended=True, statement=statement)


def _resolve_det_budget(det_budget, det_time, det_nodes):
    """Resolve (det_time, det_nodes) from `det_budget`; a recorded verdict MUST be bounded.

    `det_budget` sets `det_time` directly and derives a coarse machine-INDEPENDENT
    `det_nodes` cap so CBC stays deterministically bounded in the single-knob path (mirrors
    frontier's convenience knob). Raises if no deterministic budget is supplied.
    """
    if det_time is None:
        det_time = det_budget
    if det_nodes is None and det_budget is not None:
        det_nodes = int(det_budget * _DET_NODES_PER_BUDGET_UNIT)
    if det_time is None or det_nodes is None:
        raise ValueError(
            "a recorded g(G) verdict MUST be deterministically bounded on BOTH backends: "
            "supply det_budget (or det_time and det_nodes). Wall-clock/unbounded is forbidden."
        )
    return det_time, det_nodes


def adjudicate_gscreen(
    descriptor,
    *,
    seed,
    det_budget=None,
    det_time=None,
    det_nodes=None,
    num_workers=1,
    corpus_path=None,
    log_path=None,
    **forbidden,
):
    """Determinism-contract entry: adjudicate under a deterministic budget, single-worker.

    Mirrors the frontier's convenience signature: `det_budget` sets the CP-SAT `det_time`
    and derives the CBC `det_nodes` cap. A recorded verdict MUST be single-worker
    (`num_workers=1`) — any other value RAISES (CLAUDE.md CP-SAT #3590/#3842/#4839). A
    wall-clock budget (`wallclock_budget`, `time_limit_s`, ...) for a REPORTED verdict is
    refused (Pitfall 2): those knobs would make DECIDED-vs-RESISTANT depend on machine speed.
    """
    if forbidden:
        raise ValueError(
            f"a recorded g(G) verdict rejects wall-clock / unknown budget knobs {sorted(forbidden)}: "
            "only a DETERMINISTIC budget (det_budget / det_time+det_nodes) may be sought "
            "(a wall-clock cutoff makes the verdict machine-speed-dependent; Pitfall 2)."
        )
    if num_workers != 1:
        raise ValueError(
            f"a recorded g(G) verdict must be single-worker (num_workers=1); got {num_workers!r}. "
            "Cores scale breadth of the hunt, never the determinism of a reported verdict."
        )
    det_time, det_nodes = _resolve_det_budget(det_budget, det_time, det_nodes)
    return adjudicate_sumfree(
        descriptor, seed=seed, det_time=det_time, det_nodes=det_nodes,
        corpus_path=corpus_path, log_path=log_path,
    )


def adjudicate_grid_point(descriptor, seed, det_time, det_nodes, *, corpus_path=None, log_path=None):
    """Return the compact row the grid sweep aggregates: {n, kind, gate_survived, ...}.

    A thin projection of the full `adjudicate_sumfree` verdict to the columns the 08-06
    sweep plots (g vs |Gamma|, structured vs random).
    """
    v = adjudicate_sumfree(
        descriptor, seed=seed, det_time=det_time, det_nodes=det_nodes,
        corpus_path=corpus_path, log_path=log_path,
    )
    return {
        "n": v["n"],
        "kind": v["kind"],
        "gate_survived": v["gate_survived"],
        "terminal_state": v["terminal_state"],
        "g": v["g"],
        "had_2": v["had_2"],
        "had_3": v["had_3"],
    }


__all__ = [
    "adjudicate_sumfree",
    "adjudicate_gscreen",
    "adjudicate_grid_point",
    "KILLED",
    "SHC_CANDIDATE",
    "RESISTANT",
    "KILLED_BY_GATE",
]
