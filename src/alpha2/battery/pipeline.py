"""The 7-step kill-battery runbook (SC1) — control flow, status assignment, logging.

`run_candidate` wires the already-built machinery into the §4 runbook order
(`.planning/reference/alpha2-program-source.md:646-656`); it owns NO new mathematics.
Deterministic in (n, seed) via the single-RNG contract v1: ONE `random.Random(seed)`
feeds the generator FIRST, then the heuristic `solve` — never a per-stage subseed.

Runbook (studied-pool semantics, D-01 Role B):

  [1] Gate.   Compute the invariants the gate consumes (nu, chi, omega, kappa), then
              `run_gate`. A HARD Fail short-circuits to KILLED-BY-GATE (results-log only,
              NO certificate). An Error QUARANTINES (never a kill). G3/G4 flags travel on
              the record; they do NOT stop the runbook.
  [2] Chi.    chi = n - nu, exact (computed in step 1; no estimate anywhere).
  [3] Heuristic.  `solve` for a K_chi size-<=2 model. A HIT is an UNTRUSTED proposal
              routed through `verify_certificate` -> KILLED(heuristic). A MISS
              (`sets is None`) is an UNCONDITIONAL edge to step 4 — NEVER RESISTANT.
  [4] Exact had_2.  Dual-backend (CBC + CP-SAT) optimize -> `differential_verdict`, the
              SOLE licenser: AGREED_KILL -> build_record + verify_certificate ->
              KILLED(exact-had2); SHC_CANDIDATE -> SHC-CANDIDATE (had_3 escalation hook,
              runbook step 5, deferred); INSUFFICIENT (exact timeout) -> RESISTANT;
              CriticalDisagreement -> QUARANTINE + HALT (release-blocking, re-raised).

Trust discipline (LOCKED): `verify_certificate` is the SOLE truth on a family and is
called OUTSIDE any truth-expression (call, bind k, compare); `differential_verdict` is the
SOLE SHC-CANDIDATE / kill licenser; RESISTANT is reachable ONLY via exact INSUFFICIENT, a
heuristic miss NEVER. The seed-137 SC1 demonstration lives IN MEMORY — no
`store.append_certificate` — so the frozen corpus is byte-untouched. Records are always
assembled by `schema.build_record` + tagged-union provenance, never a hand dict. Raises-only
(survives ``python -O``); no `assert` statements.
"""
import random
from dataclasses import asdict, dataclass

from alpha2.battery.log import append_event
from alpha2.corpus import schema
from alpha2.corpus.verifier import verify_certificate
from alpha2.gate.runner import Verdict, run_gate
from alpha2.generators.cayley import cayley_adj, random_maximal_symmetric_sumfree
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants import cliques
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.search.heuristic import solve
from alpha2.solvers.backend import get_backend
from alpha2.solvers.cbc import cbc_binary_version
from alpha2.solvers.differential import CriticalDisagreement, differential_verdict
from alpha2.solvers.result import SolveParams

# ---- Terminal states (derived views over the immutable corpus + append-only log) ----
KILLED = "KILLED"                    # a verified K_k model (heuristic or exact)
KILLED_BY_GATE = "KILLED-BY-GATE"    # a HARD gate check killed — no compute, no certificate
SHC_CANDIDATE = "SHC-CANDIDATE"      # differential-licensed had_2 < chi (SHC refutation)
RESISTANT = "RESISTANT"              # exact INSUFFICIENT (timeout) — a queue state, never a heuristic miss
QUARANTINED = "QUARANTINED"          # gate Error, or release-blocking backend disagreement

FAMILIES = ("tfp", "cayley")


@dataclass(frozen=True)
class Budgets:
    """Per-step budgets — CONFIG echoed into every log line (never a code literal)."""

    heuristic: float = 60.0
    had2: float = 600.0
    had3: float = 600.0


def _h_edges(adj, n):
    """Canonical sorted [min, max] H-edge pairs (frozen Phase-1 convention)."""
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _generate(family, n, seed, rng):
    """Regenerate the candidate + its tagged-union provenance. Consumes `rng` FIRST."""
    if family == "tfp":
        adj, _m = triangle_free_process(n, rng)
        prov = schema.provenance_seed(
            "triangle_free_process_complement", n, seed,
            "Bohman uniform triangle-free process",
        )
        return adj, prov
    if family == "cayley":
        subset = random_maximal_symmetric_sumfree(n, rng)
        adj = cayley_adj(n, subset)
        prov = schema.provenance_params(
            "cayley_maximal_sumfree_Zp", n, {"S": sorted(subset)}, seed=seed,
        )
        return adj, prov
    raise ValueError(f"unknown family {family!r}; known families are {FAMILIES}")


def run_candidate(family, n, seed, *, params=None, budgets=None, log_path=None):
    """Run the 7-step runbook on one candidate; return a JSON-serializable result dict.

    Deterministic in (n, seed). `budgets` (a `Budgets`) supplies per-step time budgets,
    echoed into every results-log event. `log_path` (a test tempfile) overrides
    `paths.RESULTS_LOG`. Emits an `append_event` at every step outcome carrying the CLI-02
    fields (terminal_state + method + certificate_ref + reason + seed/provenance + budgets).
    """
    if family not in FAMILIES:
        raise ValueError(f"unknown family {family!r}; known families are {FAMILIES}")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError(f"n must be a positive int, got {n!r}")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError(f"seed must be an int, got {seed!r}")
    if budgets is None:
        budgets = Budgets()
    budgets_d = asdict(budgets)

    # ---- Single-RNG contract v1: generator FIRST, then solve (same stream). ----
    rng = random.Random(seed)
    adj, provenance = _generate(family, n, seed, rng)

    # ---- [2] Exact chi + the gate inputs (computed BEFORE the checks consume them). ----
    nu = matching_number(adj, n)
    chi = n - nu
    omega = cliques.omega_G(adj, n)
    kappa = cliques.kappa_G(adj, n)
    inv = {"nu_H": nu, "chi_G": chi, "omega_G": omega, "kappa_G": kappa}
    invariants = {"n": n, "nu_H": nu, "chi_G": chi, "omega_G": omega, "kappa_G": kappa}

    def emit(step, terminal, terminal_state, method, certificate_ref, reason, flags):
        append_event(
            {
                "family": family,
                "n": n,
                "seed": seed,
                "step": step,
                "terminal": bool(terminal),
                "terminal_state": terminal_state,
                "method": method,
                "certificate_ref": certificate_ref,
                "reason": reason,
                "provenance": provenance,
                "budgets": budgets_d,
                "invariants": invariants,
                "flags": list(flags),
            },
            path=log_path,
        )

    def result(terminal_state, method, certificate_ref, reason, gate_verdict, flags,
               had_2=None, verified=False, heuristic_found=None):
        return {
            "family": family,
            "n": n,
            "seed": seed,
            "terminal_state": terminal_state,
            "method": method,
            "certificate_ref": certificate_ref,
            "reason": reason,
            "gate_verdict": gate_verdict,
            "flags": list(flags),
            "invariants": invariants,
            "chi": chi,
            "had_2": had_2,
            "verified": verified,
            "heuristic_found": heuristic_found,
            "budgets": budgets_d,
            "provenance": provenance,
            "corpus_written": False,   # SC1 in-memory: the frozen corpus is byte-untouched
        }

    # ---- [1] Gate (D-01 Role B: hard set may KILL; G3/G4/G5/G6 flag-only). ----
    gate = run_gate(adj, n, inv)
    flags = list(gate.flag_names)
    if gate.verdict is Verdict.ERROR:
        reason = f"gate quarantined (never a kill): {gate.error.trace}"
        emit("gate", True, QUARANTINED, "gate", None, reason, flags)
        return result(QUARANTINED, "gate", None, reason, "ERROR", flags,
                      heuristic_found=None)
    if gate.verdict is Verdict.KILLED:
        reason = f"hard-gate KILL at {gate.killing}: {gate.witness}"
        method = f"gate:{gate.killing}"
        emit("gate", True, KILLED_BY_GATE, method, None, reason, flags)
        return result(KILLED_BY_GATE, method, None, reason, "KILLED", flags,
                      heuristic_found=None)
    emit("gate", False, "GATE-PASS", "gate", None,
         f"hard-gate PASS; flags travel on the record: {flags}", flags)

    # ---- [3] Heuristic model search (profile heuristic, size-<=2 branch sets). ----
    sets, _init_conf, _moves, restarts, tsolve = solve(
        adj, n, chi, rng, time_budget=budgets.heuristic
    )
    if sets is not None:
        # A HIT is an UNTRUSTED proposal — the trust root is the SOLE authority.
        method = "heuristic"
        matching_m, tutte_u, _nu2 = extract_witness(adj, n)
        rec = schema.build_record(
            provenance=provenance, H_edges=_h_edges(adj, n), nu_H=nu, chi_G=chi,
            model_branch_sets=[list(s) for s in sets],
            matching_M=matching_m, tutte_berge_U=tutte_u,
            method=method, omega_G=omega, verified=True,
        )
        k = verify_certificate(rec)   # call, bind k, compare — OUTSIDE any truth-expression
        cert_ref = f"in-memory heuristic had_2={k} h_sha256={rec['H_edges_sha256'][:12]}"
        reason = f"heuristic K_{chi} model verified by trust root (had_2={k})"
        emit("heuristic", True, KILLED, method, cert_ref, reason, flags)
        return result(KILLED, method, cert_ref, reason, "PASS", flags,
                      had_2=k, verified=True, heuristic_found=True)
    # A MISS is an UNCONDITIONAL edge to the exact backends — NEVER RESISTANT.
    emit("heuristic", False, "HEURISTIC-MISS", "heuristic", None,
         f"heuristic miss (restarts={restarts}, elapsed={tsolve:.3f}s) -> routing to exact had_2",
         flags)

    # ---- [4] Exact had_2 dual-backend -> differential_verdict (the SOLE licenser). ----
    a = get_backend("cbc").solve_had2(
        adj, n, mode="optimize", params=SolveParams(time_limit_s=budgets.had2)
    )
    b = get_backend("cpsat").solve_had2(
        adj, n, mode="optimize", params=SolveParams(time_limit_s=budgets.had2)
    )
    try:
        verdict = differential_verdict(a, b, chi)
    except CriticalDisagreement as exc:
        reason = f"CRITICAL disagreement (release-blocking; quarantine + HALT): {exc}"
        emit("had2", True, QUARANTINED, "exact-had2", None, reason, flags)
        raise   # HALT: never pick a winner between backends

    if verdict == "INSUFFICIENT":
        reason = "exact had_2 INSUFFICIENT (timeout/incumbent on a backend) -> RESISTANT queue"
        emit("had2", True, RESISTANT, "exact-had2", None, reason, flags)
        return result(RESISTANT, "exact-had2", None, reason, "PASS", flags,
                      heuristic_found=False)
    if verdict == "SHC_CANDIDATE":
        val = a.exact_value()
        reason = (f"had_2={val} < chi={chi}: SHC-CANDIDATE (differential-licensed); "
                  "had_3 escalation is runbook step 5 (deferred hook)")
        emit("had2", True, SHC_CANDIDATE, "exact-had2", None, reason, flags)
        return result(SHC_CANDIDATE, "exact-had2", None, reason, "PASS", flags,
                      had_2=val, heuristic_found=False)

    # AGREED_KILL: both PROVED_OPTIMAL at an equal value >= chi. Build from the CBC
    # family and route it through the trust root (the family is UNTRUSTED until verified).
    method = f"exact ILP (CBC): had_2(G)={a.exact_value()}"
    matching_m, tutte_u, _nu2 = extract_witness(adj, n)
    backends = schema.make_backends(method)
    backends["cbc"] = f"CBC {cbc_binary_version()}"
    rec = schema.build_record(
        provenance=provenance, H_edges=_h_edges(adj, n), nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in a.family],   # FULL family (len == had_2)
        matching_M=matching_m, tutte_berge_U=tutte_u,
        method=method, omega_G=omega, verified=True, backends=backends,
    )
    k = verify_certificate(rec)   # call, bind k, compare — OUTSIDE any truth-expression
    cert_ref = f"in-memory exact had_2={k} h_sha256={rec['H_edges_sha256'][:12]}"
    reason = (f"dual-backend AGREED_KILL had_2={k} (CBC + CP-SAT both PROVED_OPTIMAL); "
              "verified by the trust root; corpus byte-untouched (in-memory record)")
    emit("had2", True, KILLED, "exact-had2", cert_ref, reason, flags)
    return result(KILLED, "exact-had2", cert_ref, reason, "PASS", flags,
                  had_2=k, verified=True, heuristic_found=False)
