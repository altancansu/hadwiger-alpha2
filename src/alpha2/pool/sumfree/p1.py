"""P1 (the secondary track) — the signature TFP-complement family at scale.

Phase 8 reorients the roadmap into a P2 break-hunt spine; P1 is kept but deliberately
lighter (08-CONTEXT Locked Decision 1). This module grows the P1 lineage under the same
zero-heuristic-only discipline as the rest of the program, in two pieces:

  * `run_p1_tfp` / `critical_sweep` — the critical-size sweep at n=31–32 with many new
    seeds, each instance EXACT-had_2 adjudicated by the dual-backend battery (CBC +
    CP-SAT) under `differential_verdict` (the SOLE licenser) and the frozen trust root
    (`corpus.verifier.verify_certificate`). Every AGREED_KILL is certificated; every
    non-proof is RESISTANT and surfaces in the derived E3 queue (resistance tracking,
    SC1). No verdict rests on wall-clock: the reported verdict is a deterministic
    function of (n, seed, det_budget) via the 08-02 additive `SolveParams.det_time`
    (CP-SAT `max_deterministic_time`) / `det_nodes` (CBC `maxNodes`) budgets — never a
    machine-speed timeout (CLAUDE.md determinism; CP-SAT #3590/#3842/#4839).

  * `run_showpiece` — large-n showpieces toward n≈1001–2001 as EXISTENCE-ONLY results
    (RESEARCH §"g(G) rigor & cost", SRCH-02). These n are far past the ILP range, so
    there is NO exact solve here: the heuristic proposes a size-≤2 K_χ model, and a HIT
    counts ONLY after the independent trust root verifies it (a genuine existence
    certificate, appended to a NEW dedicated corpus). A MISS is RESISTANT — it queues
    for E3, NEVER a reported result, NEVER an impossibility claim (heuristic resistance
    is never a result).

RNG contract v2 (POOL-1/2): every instance is built from a per-stage sha256 subseed
(`gen_rng` feeds `triangle_free_process`; `search_rng` feeds the heuristic) and rebuilds
byte-exactly from its stored descriptor — never RNG replay (cross-platform set-iteration
safety). The frozen 296-instance CORPUS, `generators/cayley.py`, and `generators/tfp.py`
stay byte-untouched: the sweep keeps its records IN MEMORY and the showpieces append to
`paths.P1_SHOWPIECE_CORPUS` (T-8-12).

Raises-only (survives `python -O`); no `assert`. The trust root is called OUTSIDE any
truth-expression (call, bind k, compare) — it is the sole authority on existence.
"""
from alpha2 import paths
from alpha2.corpus import schema
from alpha2.corpus.store import append_certificate
from alpha2.corpus.verifier import verify_certificate
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.pool.sumfree.rng import gen_rng, search_rng
from alpha2.search.heuristic import solve
from alpha2.solvers.backend import get_backend
from alpha2.solvers.differential import differential_verdict
from alpha2.solvers.result import SolveParams

# Existence-only showpiece default heuristic budget (dev-scale on the Mac; a canonical
# large push belongs on the box, docs/COMPUTE.md). A MISS under it is RESISTANT, never
# a result — the budget can only under-report existence, never manufacture it.
DEFAULT_SHOWPIECE_BUDGET = 20.0

# Deterministic CBC node cap per unit of `det_budget`: a fixed pure function of the
# budget, so a recorded CBC verdict is machine-speed-independent (paired with CP-SAT's
# `max_deterministic_time = det_budget`). The value only bounds work; it never changes
# a proof into a non-proof for a given (n, seed, det_budget).
_CBC_NODES_PER_UNIT = 5000

_TFP_PROCESS = "Bohman uniform triangle-free process"
_TFP_FAMILY = "triangle_free_process_complement"


def _h_edges(adj, n):
    """Canonical sorted [min, max] H-edge pairs (frozen Phase-1 convention)."""
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _tfp_instance(n, seed):
    """RNG contract v2: `gen_rng(seed)` -> `triangle_free_process`; return (adj, descriptor).

    The descriptor is the byte-exact rebuild contract ({family, n, seed, H_edges}) — a
    second run rebuilds the identical adjacency from it, independent of any RNG replay.
    """
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError(f"n must be a positive int, got {n!r}")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f"seed must be an int, got {seed!r}")
    adj, _m = triangle_free_process(n, gen_rng(seed))
    h_edges = _h_edges(adj, n)
    descriptor = {
        "family": _TFP_FAMILY,
        "n": n,
        "seed": seed,
        "rng_contract": "v2",
        "H_edges": h_edges,
        "H_edges_sha256": schema.h_edges_sha256(h_edges),
    }
    return adj, descriptor


def _det_params(det_budget):
    """Additive deterministic budget on BOTH co-equal backends (never wall-clock)."""
    if not isinstance(det_budget, (int, float)) or isinstance(det_budget, bool):
        raise ValueError(f"det_budget must be a number, got {det_budget!r}")
    if det_budget <= 0:
        raise ValueError(f"det_budget must be positive, got {det_budget!r}")
    det_nodes = max(1, int(det_budget * _CBC_NODES_PER_UNIT))
    return SolveParams(det_time=float(det_budget), det_nodes=det_nodes, threads=1)


def run_p1_tfp(n, *, seed, det_budget, num_workers=1):
    """One EXACT-had_2 sweep point on the n=31–32 TFP-complement critical row.

    Deterministic in (n, seed, det_budget). Returns a JSON-serializable verdict dict:
    `terminal_state` is "DECIDED" (both backends PROVED_OPTIMAL, agree, and — on a kill
    — the trust root verified the family) or "RESISTANT" (differential INSUFFICIENT:
    at least one backend did not prove optimality within its deterministic budget). A
    RESISTANT point is a queue state, NEVER a heuristic-only number.
    """
    if num_workers != 1:
        # A reported had_2 verdict MUST be deterministic single-worker (CLAUDE.md;
        # CP-SAT wrong-INFEASIBLE / nondeterminism regressions #3590/#3842/#4839).
        raise ValueError(
            f"a reported had_2 verdict must run num_workers=1 (deterministic), got {num_workers!r}"
        )
    adj, descriptor = _tfp_instance(n, seed)
    nu = matching_number(adj, n)
    chi = n - nu
    params = _det_params(det_budget)
    a = get_backend("cbc").solve_had2(adj, n, mode="optimize", params=params)
    b = get_backend("cpsat").solve_had2(adj, n, mode="optimize", params=params)
    # differential_verdict is the SOLE licenser; a CriticalDisagreement propagates
    # (quarantine + HALT) — we never pick a winner between the two exact backends.
    verdict = differential_verdict(a, b, chi)

    if verdict == "INSUFFICIENT":
        return _sweep_verdict(descriptor, chi, "RESISTANT", had_2=None,
                              optimality_proved=False, verified=False,
                              reason="dual-backend INSUFFICIENT -> RESISTANT (E3 queue)")
    if verdict == "SHC_CANDIDATE":
        # Both PROVED_OPTIMAL at an exact value < chi: a decided exact had_2 bound
        # (SHC refutation candidate). Optimality IS proved; no K_chi model exists at
        # size <= 2, so there is nothing for the trust root to verify.
        return _sweep_verdict(descriptor, chi, "DECIDED", had_2=a.exact_value(),
                              optimality_proved=True, verified=False,
                              reason="differential SHC-CANDIDATE: exact had_2 < chi")
    # AGREED_KILL: both PROVED_OPTIMAL, equal, >= chi. The family is UNTRUSTED until
    # the frozen trust root passes on it (call, bind k, compare).
    matching_m, tutte_u, _nu2 = extract_witness(adj, n)
    rec = schema.build_record(
        provenance=schema.provenance_seed(_TFP_FAMILY, n, seed, _TFP_PROCESS),
        H_edges=descriptor["H_edges"], nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in a.family],
        matching_M=matching_m, tutte_berge_U=tutte_u,
        method=f"exact ILP dual-backend (CBC + CP-SAT) had_2={a.exact_value()}",
        verified=True,
    )
    k = verify_certificate(rec)
    return _sweep_verdict(descriptor, chi, "DECIDED", had_2=k,
                          optimality_proved=True, verified=True,
                          reason=f"AGREED_KILL had_2={k} verified by the trust root")


def _sweep_verdict(descriptor, chi, terminal_state, *, had_2, optimality_proved,
                   verified, reason):
    """Build the deterministic, JSON-serializable sweep verdict dict."""
    return {
        "family": descriptor["family"],
        "n": descriptor["n"],
        "seed": descriptor["seed"],
        "rng_contract": descriptor["rng_contract"],
        "H_edges_sha256": descriptor["H_edges_sha256"],
        "chi": chi,
        "terminal_state": terminal_state,
        "had_2": had_2,
        "optimality_proved": optimality_proved,
        "verified": verified,
        "reason": reason,
        "corpus_written": False,  # SC1 in-memory: the frozen 296-corpus is byte-untouched
    }


def critical_sweep(seeds, *, ns=(31, 32), det_budget=5.0, num_workers=1):
    """Aggregate the n=31–32 many-seed exact sweep; surface the derived E3 queue.

    Returns {results, counts, resistant_queue}. The RESISTANT set IS the derived E3
    queue (resistance tracking, SC1): those instances are queued for the survivor
    protocol (Phase 11), never concluded here.
    """
    results = []
    counts = {}
    resistant_queue = []
    for n in ns:
        for seed in seeds:
            v = run_p1_tfp(n, seed=seed, det_budget=det_budget, num_workers=num_workers)
            results.append(v)
            counts[v["terminal_state"]] = counts.get(v["terminal_state"], 0) + 1
            if v["terminal_state"] == "RESISTANT":
                resistant_queue.append({"n": v["n"], "seed": v["seed"]})
    return {"results": results, "counts": counts, "resistant_queue": resistant_queue}


def run_showpiece(n, *, seed, time_budget=DEFAULT_SHOWPIECE_BUDGET, corpus_path=None):
    """A large-n (≈1001–2001) EXISTENCE-ONLY showpiece: heuristic HIT -> trust root.

    Above the ILP frontier there is no exact solve. Generate the TFP instance (RNG v2),
    compute chi = n - nu (blossom, exact + fast to n≈2001), and run the heuristic for a
    size-≤2 K_chi model. A HIT is an UNTRUSTED proposal routed through
    `verify_certificate` (the SOLE authority); once verified it is a genuine existence
    certificate and is appended to the NEW dedicated `paths.P1_SHOWPIECE_CORPUS` (the
    frozen 296-corpus is never touched, T-8-12). A MISS is RESISTANT — it queues for E3,
    NEVER a reported result and NEVER an impossibility claim (T-8-11 / SRCH-02).
    """
    adj, descriptor = _tfp_instance(n, seed)
    nu = matching_number(adj, n)
    chi = n - nu
    sets, _init_conf, _moves, _restarts, _tsolve = solve(
        adj, n, chi, search_rng(seed), time_budget=time_budget
    )
    if sets is None:
        # MISS -> RESISTANT. Heuristic resistance is never a result; no exact bound
        # exists at this size, so had_2 is None and it queues for E3.
        return _showpiece_result(descriptor, chi, "RESISTANT", verified=False, had_2=None,
                                 reason="heuristic MISS -> RESISTANT (E3 queue); no exact solve at this n")
    # HIT: the family is UNTRUSTED until the trust root passes (call, bind k, compare).
    matching_m, tutte_u, _nu2 = extract_witness(adj, n)
    rec = schema.build_record(
        provenance=schema.provenance_seed(_TFP_FAMILY, n, seed, _TFP_PROCESS),
        H_edges=descriptor["H_edges"], nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in sets],
        matching_M=matching_m, tutte_berge_U=tutte_u,
        method=f"heuristic existence-only (K_{chi} size-<=2 model, verifier-adjudicated)",
        verified=True,
    )
    k = verify_certificate(rec)
    path = paths.ensure_parent(corpus_path or paths.P1_SHOWPIECE_CORPUS)
    append_certificate(rec, path=path)
    return _showpiece_result(descriptor, chi, "VERIFIED", verified=True, had_2=k,
                             reason=f"heuristic HIT verified by the trust root (had_2={k})")


def _showpiece_result(descriptor, chi, terminal_state, *, verified, had_2, reason):
    """Build the deterministic, JSON-serializable existence-only showpiece dict."""
    return {
        "family": descriptor["family"],
        "n": descriptor["n"],
        "seed": descriptor["seed"],
        "rng_contract": descriptor["rng_contract"],
        "H_edges_sha256": descriptor["H_edges_sha256"],
        "kind": "existence_only",
        "chi": chi,
        "terminal_state": terminal_state,
        "verified": verified,
        "had_2": had_2,
        "reason": reason,
    }
