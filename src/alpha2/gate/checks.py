"""G1-G6 pure predicates, frozen verbatim from Appendix E §2 (GATE-02) — stdlib + confined nx.

Each predicate is a pure function of `(adj, n, inv)` where `inv` is a dict of PRE-computed
invariants — `nu_H` (via invariants/matching), `chi_G = n - nu_H`, `omega_G`, `kappa_G` (via
invariants/cliques). A predicate returns a `Pass(witness)` or `Fail(reason, witness)`; the
outcome types live in `gate/runner.py`. Guards RAISE (no `assert` — the gate path must
survive `python -O`, mirroring `corpus/verifier.py`'s `if not cond: raise` discipline).

Tier assignment (hard vs flag_only, D-01 Role B) is NOT decided here — the checks are pure;
the runner (`gate/runner.py`) owns the tiers. `reason` strings quote the §2 "Source/reason"
column verbatim (never paraphrased): the definitions are frozen, not invented.
"""
from alpha2.generators import tfp
from alpha2.invariants import cliques
from alpha2.gate.runner import Fail, Pass

# Verbatim §2 "Source / reason" column (alpha2-program-source.md:635-644). Quoted, not paraphrased.
_SRC = {
    "G1": "Carter's computational bound; criticality",
    "G2": "no dominating edge may exist",
    "G3": "RST for K6; PST properties",
    "G4": "K8 is unavoidable (Carter; also R(3,8)=28); Chudnovsky-Seymour's seagull "
          "theorem builds the minor above the threshold",
}


def _delta_G(adj, n):
    """delta(G) = min degree of G = complement(H): deg_G(v) = (n - 1) - deg_H(v)."""
    if n <= 0:
        raise ValueError(f"delta(G) undefined for n={n}")
    return min((n - 1) - len(adj[v]) for v in range(n))


def g1_criticality(adj, n, inv):
    """G1: n >= 31, criticality encoded as `nu == n // 2` (EVEN-n fix, LOCKED).

    The forbidden odd-only `n = 2·chi − 1` form silently drops even n (n=32, nu=16 is the
    standing counterexample). We test `nu(H) == n // 2` instead, which accepts n=31 (nu=15)
    AND n=32 (nu=16), then apply the Carter bound n >= 31.
    """
    if "nu_H" not in inv:
        raise KeyError("g1_criticality requires inv['nu_H']")
    nu = inv["nu_H"]
    if not isinstance(nu, int) or isinstance(nu, bool):
        raise ValueError(f"nu_H must be a genuine int, got {nu!r}")
    chi = n - nu
    if nu != n // 2:
        return Fail(
            f"not critical [{_SRC['G1']}]: nu(H)={nu} != n//2={n // 2}",
            witness={"nu_H": nu, "n_over_2": n // 2, "chi_G": chi},
        )
    if n < 31:
        return Fail(
            f"below Carter bound [{_SRC['G1']}]: n={n} < 31",
            witness={"n": n, "chi_G": chi},
        )
    return Pass(witness={"nu_H": nu, "chi_G": chi, "n_over_2": n // 2})


def g2_triangle_free_diam2(adj, n, inv):
    """G2: H triangle-free with diameter 2 (equivalently edge-maximal triangle-free).

    Delegates to the already-tested tfp primitives — never re-derived here.
    """
    if not tfp.is_triangle_free(adj, n):
        return Fail(f"H not triangle-free [{_SRC['G2']}]", witness={"triangle_free": False})
    if not tfp.is_edge_maximal_tf(adj, n):
        return Fail(
            f"H not edge-maximal / diameter != 2 [{_SRC['G2']}]",
            witness={"triangle_free": True, "edge_maximal_tf": False},
        )
    return Pass(witness={"triangle_free": True, "edge_maximal_tf": True})


def g_connectivity(adj, n, inv):
    """Connectivity (hard, D-01): G = complement(H) must be connected."""
    if not cliques.is_connected_G(adj, n):
        return Fail("G = complement(H) is disconnected", witness={"is_connected_G": False})
    return Pass(witness={"is_connected_G": True})


def g3_deep(adj, n, inv):
    """G3: chi >= 7, kappa(G) >= chi, delta(G) >= chi + 1 (+ Hamiltonicity / vertex-critical /
    H-v-PM, logged as not-yet-screened for MVP).

    FLAG-ONLY (D-01 Role B): seed-137 fails here (kappa=11 < chi=16; delta=16 < 17) yet must
    reach had_2. Each screened sub-condition is recorded in the witness.
    """
    for key in ("chi_G", "kappa_G"):
        if key not in inv:
            raise KeyError(f"g3_deep requires inv['{key}']")
    chi = inv["chi_G"]
    kappa = inv["kappa_G"]
    delta = _delta_G(adj, n)
    checks = {
        "chi_ge_7": chi >= 7,
        "kappa_ge_chi": kappa >= chi,
        "delta_ge_chi_plus_1": delta >= chi + 1,
    }
    witness = {
        "chi_G": chi, "kappa_G": kappa, "delta_G": delta,
        "hamiltonian": "not yet screened", "vertex_critical": "not yet screened",
        "H_minus_v_perfect_matching": "not yet screened",
        **checks,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return Fail(
            f"G3-deep failed {failed} [{_SRC['G3']}]: "
            f"chi={chi}, kappa={kappa}, delta={delta}",
            witness=witness,
        )
    return Pass(witness=witness)


def g4_omega_window(adj, n, inv):
    """G4: 8 <= omega(G) <= chi - 3, and clique ratio omega/n below ~1/4.

    FLAG-ONLY (D-01 Role B): seed-137 fails here (omega=14 > chi-3=13; omega/n=0.45 >> 1/4).
    """
    for key in ("chi_G", "omega_G"):
        if key not in inv:
            raise KeyError(f"g4_omega_window requires inv['{key}']")
    if n <= 0:
        raise ValueError(f"g4_omega_window undefined for n={n}")
    chi = inv["chi_G"]
    omega = inv["omega_G"]
    ratio = omega / n
    checks = {
        "omega_ge_8": omega >= 8,
        "omega_le_chi_minus_3": omega <= chi - 3,
        "ratio_below_quarter": ratio < 0.25,
    }
    witness = {"omega_G": omega, "chi_G": chi, "omega_over_n": ratio, **checks}
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return Fail(
            f"G4 omega-window failed {failed} [{_SRC['G4']}]: "
            f"omega={omega}, chi-3={chi - 3}, omega/n={ratio:.4f}",
            witness=witness,
        )
    return Pass(witness=witness)


def g5_unavoidables(adj, n, inv):
    """G5: induced-C5 / W5 / K8 / 33-Carter-unavoidables screen — GATE-03, Plan 04.

    FLAG-ONLY stub: the unavoidable-subgraph screen is not yet active; passes with a note.
    """
    return Pass(witness={"screen": "G5 unavoidables not yet active (GATE-03, Plan 04)"})


def g6_safe_families(adj, n, inv):
    """G6: outside every proven-safe family (safe-family list, §2:644) — GATE-03, Plan 04.

    FLAG-ONLY stub: the safe-family membership screen is not yet active; passes with a note.
    """
    return Pass(witness={"screen": "G6 safe-families not yet active (GATE-03, Plan 04)"})
