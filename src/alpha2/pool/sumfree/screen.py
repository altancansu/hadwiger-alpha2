"""g(G)-screen METRIC + the had_2 -> had_3 tiering over a descriptor-built adj (POOL-2).

The screen gap is

    g(G) = (chi - had_k) / chi ,  had_k the deepest PROVED bound (had_3, else had_2),

with the LOCKED interpretation (RESEARCH §"g(G) rigour", 08-CONTEXT Locked Decision 1):

  * g <= 0  =>  the K_chi minor already packs at branch sets <=3 => KILLED (Hadwiger
    holds on this instance, by construction); the deciding family is trust-root verified.
  * g > 0   =>  an SHC_CANDIDATE — necessary, NOT sufficient (small branch sets cannot
    reach chi; size->=4 sets are not excluded), queued for the E3 survivor protocol.
    A g>0 screen is NEVER a "break" and NEVER a "had(G) < chi" claim (Pitfall 1).
  * RESISTANT  =>  no exact bound was proved inside the deterministic budget (had_k
    None, g None). A heuristic MISS is RESISTANT, it is NEVER a g>0 point.

`compute_g` / `classify_screen_outcome` are the pure metric+labelling helpers the RED
contract pins. `screen_gap` is the tiering DRIVER over a pre-built H-adjacency `adj` and
its `chi`: it runs had_2 dual-backend (CBC + CP-SAT) optimize under a DETERMINISTIC
budget, feeds both outcomes to the SOLE licenser `differential_verdict`, and escalates a
proved had_2 < chi to the Tier-1 had_3 seagull the same bounded way. Both co-equal
backends are bounded WITHOUT wall-clock — CP-SAT by `det_time` (max_deterministic_time,
num_workers=1), CBC by `det_nodes` (maxNodes, threads=1) — so every recorded verdict is a
function of (n, seed), never machine speed (T-8-07). `verify_certificate` (the frozen
trust root) is the SOLE authority on a family and is called OUTSIDE any truth-expression.

stdlib + the solver legs (`backend`/`result`/`differential` are all stdlib-only); the
networkx-touching legs (matching/witness/corpus-verifier) are imported INSIDE the family
re-verification helper only, so importing this module never loads a graph library.
"""
from collections import namedtuple

from alpha2.pool.sumfree.schema import _compute_g
from alpha2.solvers.backend import get_backend
from alpha2.solvers.differential import (
    CriticalDisagreement,
    UnverifiedKill,
    differential_verdict,
)
from alpha2.solvers.result import SolveParams, Status

# The structured tiering outcome the caller (adjudicate) turns into a stored certificate.
#   terminal_state : KILLED | SHC_CANDIDATE | RESISTANT
#   had_2 / had_3  : the proved bounds (None when unproved in budget)
#   g              : the screen gap (None when RESISTANT)
#   family         : the trust-root-verified K_chi model for a KILLED verdict, else None
ScreenOutcome = namedtuple("ScreenOutcome", ["terminal_state", "had_2", "had_3", "g", "family"])

KILLED = "KILLED"
SHC_CANDIDATE = "SHC_CANDIDATE"
RESISTANT = "RESISTANT"


def compute_g(chi, had_k):
    """The screen gap g = (chi - had_k) / chi; None when had_k is None (RESISTANT).

    Pure metric — no solve. `had_k` is the deciding PROVED bound (had_3, else had_2).
    Delegates to the schema's `_compute_g` so the emit-time derivation and this
    screen-time derivation share ONE formula (a divergence could mislabel an instance).
    """
    if not (isinstance(chi, int) and chi >= 1):
        raise ValueError(f"chi must be a positive int, got {chi!r}")
    return _compute_g(chi, None, had_k)


def classify_screen_outcome(*, chi, had_k, heuristic_hit, exact_proved):
    """Label a screen outcome from its evidence; return {terminal_state, g, had_k}.

    The radioactive-discipline truth table (Pitfall 1, T-8-01):
      * heuristic_hit               -> KILLED  (a size-chi K_chi model packs => g <= 0);
      * exact_proved & had_k < chi  -> SHC_CANDIDATE (g > 0, screen-only);
      * exact_proved & had_k >= chi -> KILLED  (proved packs => g <= 0);
      * otherwise (miss / not proved in budget) -> RESISTANT (g None, E3 queue).

    A heuristic MISS above the exact frontier is RESISTANT with g None — NEVER a g>0
    point. `had_k is None` with `exact_proved` false is the RESISTANT signature.
    """
    if not (isinstance(chi, int) and chi >= 1):
        raise ValueError(f"chi must be a positive int, got {chi!r}")

    if heuristic_hit:
        # A verified size-chi family proves had_2 >= chi => g <= 0 (packs).
        g = compute_g(chi, had_k) if had_k is not None else 0.0
        return {"terminal_state": KILLED, "g": g, "had_k": had_k}

    if exact_proved and had_k is not None:
        g = compute_g(chi, had_k)
        state = SHC_CANDIDATE if had_k < chi else KILLED
        return {"terminal_state": state, "g": g, "had_k": had_k}

    # No exact bound proved in the deterministic budget: RESISTANT, queued for E3.
    return {"terminal_state": RESISTANT, "g": None, "had_k": None}


def _require_deterministic_budget(det_time, det_nodes):
    """A recorded screen verdict MUST bound BOTH co-equal backends deterministically.

    CP-SAT reads `det_time` (max_deterministic_time); CBC reads `det_nodes` (maxNodes).
    If either is absent the corresponding backend would run unbounded and a reported
    had_k < chi / RESISTANT verdict would depend on machine speed — forbidden (T-8-07,
    CLAUDE.md #3590/#3842/#4839). Wall-clock `time_limit_s` is never in this path.
    """
    if det_time is None or det_nodes is None:
        raise ValueError(
            "a recorded g(G) screen verdict MUST bound BOTH backends deterministically: "
            f"det_time (CP-SAT) and det_nodes (CBC) are required, got det_time={det_time!r}, "
            "det_nodes={det_nodes!r}. Wall-clock/unbounded is forbidden for a reported verdict."
        )


def _optimize_both(adj, n, method, det_time, det_nodes):
    """Solve `method` (solve_had2|solve_had3) on BOTH backends under the det budget.

    CP-SAT bounded by det_time, CBC by det_nodes; NO wall-clock time_limit_s. Returns the
    two ExactOutcomes (a=CBC, b=CP-SAT) for the SAME instance/mode/problem.
    """
    params = SolveParams(det_time=det_time, det_nodes=det_nodes)
    a = getattr(get_backend("cbc"), method)(adj, n, mode="optimize", params=params)
    b = getattr(get_backend("cpsat"), method)(adj, n, mode="optimize", params=params)
    return a, b


def trust_root_verify_family(adj, n, chi, family):
    """Route an UNTRUSTED solver family through the frozen trust root; return k or None.

    Builds a corpus record (Tutte-Berge M/U via `extract_witness`, the FULL family) and
    calls `verify_certificate` — the SOLE authority on a family. Returns the verified size
    k (>= chi) on success; returns None if the family does NOT certify a K_chi minor (a
    >=chi upper-bound number that fails verification licenses NO kill — UnverifiedKill
    discipline). Called OUTSIDE any truth-expression by both screen and adjudicate.

    networkx-touching legs (matching/witness) are imported HERE, lazily, so importing the
    screen module never loads a graph library.
    """
    from alpha2.corpus import schema as corpus_schema
    from alpha2.corpus.verifier import VerificationError, verify_certificate
    from alpha2.invariants.witness import extract_witness

    if not family or len(family) < chi:
        return None
    matching_m, tutte_u, nu = extract_witness(adj, n)
    h_edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
    prov = corpus_schema.provenance_params(
        "sumfree_cayley_gscreen", n, {"screen": "g(G)"}
    )
    try:
        rec = corpus_schema.build_record(
            provenance=prov,
            H_edges=h_edges,
            nu_H=nu,
            chi_G=chi,
            model_branch_sets=[list(s) for s in family],
            matching_M=matching_m,
            tutte_berge_U=tutte_u,
            method="g(G) screen dual-backend family",
            verified=True,
        )
        return verify_certificate(rec)   # call, bind k, compare — OUTSIDE a truth-expression
    except (VerificationError, ValueError):
        return None


def screen_gap(adj, n, chi, *, det_time, det_nodes):
    """Run the had_2 -> had_3 tiering over a pre-built adj; return a `ScreenOutcome`.

    Ladder (RESEARCH §"Tiering"):
      [had_2] dual-backend optimize -> differential_verdict:
          AGREED_KILL (>= chi)  -> KILLED g<=0, return the CBC family for the caller to
                                   verify (an exact had_2 optimum, not an upper bound);
          SHC_CANDIDATE (< chi) -> escalate to had_3;
          INSUFFICIENT          -> RESISTANT (g None).
      [had_3] Tier-1 seagull dual-backend optimize -> differential_verdict:
          SHC_CANDIDATE (U < chi PROVED) -> g>0 SHC-CANDIDATE (sound from the upper bound:
                                   true had_3 <= U < chi);
          UnverifiedKill (U >= chi)      -> Tier-2: extract + trust-root-verify a >=chi
                                   family. Verified >= chi -> g<=0 KILLED (packs); a family
                                   that does NOT verify licenses no claim -> RESISTANT
                                   (a >=chi upper-bound number alone is not a kill, and it
                                   does not prove had_3 < chi either) -> E3 / Tier-2 exact.
          INSUFFICIENT          -> RESISTANT (g None).

    `CriticalDisagreement` propagates (QUARANTINE + HALT — never pick a winner). Both
    backends are bounded deterministically (CP-SAT det_time, CBC det_nodes); wall-clock is
    forbidden. Returns (terminal_state, had_2, had_3, g, family_or_none).
    """
    if not (isinstance(chi, int) and chi >= 1):
        raise ValueError(f"chi must be a positive int, got {chi!r}")
    _require_deterministic_budget(det_time, det_nodes)

    # ---- Tier 0: exact had_2 dual-backend -> the SOLE licenser. ----
    a2, b2 = _optimize_both(adj, n, "solve_had2", det_time, det_nodes)
    verdict2 = differential_verdict(a2, b2, chi)   # CriticalDisagreement propagates

    if verdict2 == "INSUFFICIENT":
        return ScreenOutcome(RESISTANT, None, None, None, None)

    if verdict2 == "AGREED_KILL":
        # Exact had_2 optimum >= chi: g <= 0. The CBC family is UNTRUSTED — the caller
        # routes it through verify_certificate (mirrors pipeline's AGREED_KILL leg).
        had_2 = a2.exact_value()
        g = compute_g(chi, had_2)
        return ScreenOutcome(KILLED, had_2, None, g, [list(s) for s in a2.family])

    # verdict2 == "SHC_CANDIDATE": had_2 proved < chi -> escalate to had_3 (Tier-1 seagull).
    had_2 = a2.exact_value()
    a3, b3 = _optimize_both(adj, n, "solve_had3", det_time, det_nodes)
    try:
        verdict3 = differential_verdict(a3, b3, chi)   # CriticalDisagreement propagates
    except UnverifiedKill:
        # A PROVED had_3 UPPER bound U >= chi cannot license a kill from its number alone.
        # Tier-2: extract the winning family and route it through the frozen trust root.
        k = trust_root_verify_family(adj, n, chi, a3.family)
        if k is not None:
            # A real K_chi minor (branch sets <=3) packs: g <= 0, KILLED.
            g = compute_g(chi, k)
            return ScreenOutcome(KILLED, had_2, k, g, [list(s) for s in a3.family])
        # The >=chi upper bound did not certify a minor AND does not prove had_3 < chi:
        # conservatively RESISTANT (a full Tier-2 exact had_3 is an E3 obligation).
        return ScreenOutcome(RESISTANT, had_2, None, None, None)

    if verdict3 == "SHC_CANDIDATE":
        # Proved U < chi: sound g>0 (true had_3 <= U < chi). Screen-only SHC-CANDIDATE.
        had_3 = a3.exact_value()
        g = compute_g(chi, had_3)
        return ScreenOutcome(SHC_CANDIDATE, had_2, had_3, g, None)

    if verdict3 == "AGREED_KILL":
        # An EXACT (non-upper-bound) had_3 optimum >= chi — verify the family, then g<=0.
        had_3 = a3.exact_value()
        k = trust_root_verify_family(adj, n, chi, a3.family)
        if k is not None:
            g = compute_g(chi, had_3)
            return ScreenOutcome(KILLED, had_2, had_3, g, [list(s) for s in a3.family])
        return ScreenOutcome(RESISTANT, had_2, None, None, None)

    # verdict3 == "INSUFFICIENT": no proved had_3 bound in budget -> RESISTANT (E3 queue).
    return ScreenOutcome(RESISTANT, had_2, None, None, None)


# CriticalDisagreement is re-exported so callers can catch the quarantine at this boundary.
__all__ = [
    "ScreenOutcome",
    "compute_g",
    "classify_screen_outcome",
    "screen_gap",
    "trust_root_verify_family",
    "CriticalDisagreement",
    "KILLED",
    "SHC_CANDIDATE",
    "RESISTANT",
]
