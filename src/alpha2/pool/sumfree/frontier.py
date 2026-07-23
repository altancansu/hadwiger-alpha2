"""Empirical ILP optimality-proof frontier for the sum-free Cayley family (RESEARCH A4).

WHAT THIS MEASURES (and what it does NOT):

  * `frontier_n` is **measured, budget-dependent evidence**, not a theorem and not an
    assumption. For a grid of group orders `n` this driver records, per n, whether the
    exact had_2 (and, on a proved had_2 < chi, the Tier-1 had_3) optimality PROVED inside a
    FIXED deterministic budget on BOTH co-equal backends. It answers RESEARCH open-question
    A4 empirically instead of guessing the frontier sits at n≈150–200.

  * "PROVED" here means BOTH backends reach `Status.PROVED_OPTIMAL` within the budget —
    CP-SAT bounded by `det_time` (`max_deterministic_time`, num_workers=1), CBC bounded by
    `det_nodes` (`maxNodes`, threads=1). NO wall-clock `time_limit_s` is passed to any timed
    call: a wall-clock cutoff would make the frontier machine-speed-dependent and flip under
    contention on the shared box — the exact failure this plan closes (T-8-07). The measured
    frontier is therefore a function of (n, det_budget), NEVER of hardware speed.

  * This driver measures FEASIBILITY of the optimality PROOF (did it prove in-budget?), it
    does NOT adjudicate g or emit any impossibility verdict. A CBC node-cap incumbent maps to
    `INCUMBENT_ONLY` (not `PROVED_OPTIMAL`), so "not proved" stays honest.

  * Only gate SURVIVORS are timed. A hard-gate KILL (or a generator that declines to build a
    valid instance for this Γ) is recorded as un-timed, never fed to a backend.

The derived `frontier_n` (largest n at which the STRUCTURED had_2 optimality still proved on
both backends, with every smaller measured n also proved — the conservative downward
boundary) is the input the 08-06 grid sweep reads via `exact_window_max` to decide, per
instance, whether a non-packing outcome is an exact `g>0` candidate (n ≤ window) or a
RESISTANT E3-queue instance (n > window). It is empirical, not a claim about the true
Hadwiger number.
"""
import json
import os
import tempfile
from pathlib import Path

from alpha2 import paths
from alpha2.battery.log import append_event
from alpha2.gate.runner import Verdict, run_gate
from alpha2.invariants import cliques
from alpha2.invariants.matching import matching_number
from alpha2.pool.sumfree.generate import (
    cayley_adj_abelian,
    green_ruzsa_sumfree,
    middle_interval_sumfree,
    random_maximal_symmetric_sumfree,
)
from alpha2.pool.sumfree.group import Abelian
from alpha2.pool.sumfree.rng import gen_rng
from alpha2.solvers.backend import get_backend
from alpha2.solvers.result import SolveParams, Status

# The default per-n instance kinds. Structured kinds (the frontier-defining ones) carry the
# "structured:" prefix; random-greedy is measured alongside for the structured-vs-random
# contrast (Locked Decision 1) but does NOT define frontier_n.
DEFAULT_KINDS = (
    "structured:green_ruzsa",
    "structured:middle_interval",
    "random_greedy",
)

# When only a single `det_budget` knob is supplied (the dev/unit path), derive the CBC
# node cap from it so BOTH backends stay deterministically bounded — a coarse, machine
# INDEPENDENT node budget tied to the deterministic-time knob (never wall-clock). The real
# box probe (`run_frontier_probe`) passes an explicit `det_nodes`, overriding this.
_DET_NODES_PER_BUDGET_UNIT = 100_000


def _is_structured(kind):
    return kind.startswith("structured:")


def _generate_S(kind, group, rng):
    """Build the sum-free set S for `kind` over `group`; return None if this Γ is unserved.

    A generator that raises (ValueError: the arithmetic band is not sum-free for this Γ;
    NotImplementedError: the RESEARCH-flagged Green–Ruzsa 3∣n coset case) means this kind
    simply does not build a valid instance for this Γ — recorded as un-timed, never a crash.
    """
    try:
        if kind == "structured:green_ruzsa":
            return green_ruzsa_sumfree(group)
        if kind == "structured:middle_interval":
            return middle_interval_sumfree(group)
        if kind == "random_greedy":
            return random_maximal_symmetric_sumfree(group, rng)
    except (ValueError, NotImplementedError):
        return None
    raise ValueError(f"unknown frontier instance kind {kind!r}; known kinds are {DEFAULT_KINDS}")


def _time_optimality(adj, n, *, method, det_time, det_nodes):
    """Time one exact solve on BOTH co-equal backends under the deterministic budget.

    `method` is "solve_had2" or "solve_had3". Returns (proved, cbc_status, cpsat_status,
    value) where `proved` is True iff BOTH backends reached PROVED_OPTIMAL. NO wall-clock
    `time_limit_s` is ever passed: CP-SAT is bounded by det_time, CBC by det_nodes.
    """
    cbc = getattr(get_backend("cbc"), method)(
        adj, n, mode="optimize", params=SolveParams(det_nodes=det_nodes)
    )
    cpsat = getattr(get_backend("cpsat"), method)(
        adj, n, mode="optimize", params=SolveParams(det_time=det_time)
    )
    proved = cbc.status is Status.PROVED_OPTIMAL and cpsat.status is Status.PROVED_OPTIMAL
    value = cbc.exact_value() if proved else None
    return proved, cbc.status.name, cpsat.status.name, value


def _resolve_budget(det_budget, det_time, det_nodes):
    """Resolve (det_time, det_nodes) from the supplied knobs; a frontier MUST be bounded.

    Raises if NO deterministic budget is given — an unbounded (or wall-clock) frontier
    verdict is forbidden (T-8-07/T-8-10). When only `det_budget` is supplied, it sets
    `det_time` directly and derives a coarse machine-independent `det_nodes` cap.
    """
    if det_time is None:
        det_time = det_budget
    if det_nodes is None and det_budget is not None:
        det_nodes = int(det_budget * _DET_NODES_PER_BUDGET_UNIT)
    if det_time is None and det_nodes is None:
        raise ValueError(
            "a recorded frontier verdict MUST be deterministically bounded: supply "
            "det_budget (or det_time and/or det_nodes). Wall-clock/unbounded is forbidden "
            "(the frontier must be a function of (n, budget), never machine speed)."
        )
    return det_time, det_nodes


def measure_ilp_frontier(
    ns,
    *,
    det_budget=None,
    det_time=None,
    det_nodes=None,
    num_workers=1,
    kinds=DEFAULT_KINDS,
    seed=0,
    table_path=None,
):
    """Measure the per-n ILP optimality-proof frontier under a deterministic budget.

    For each n in `ns`: over each kind, generate one representative sum-free S (structured
    deterministic; random via `gen_rng(seed)`), build H = Cay(Γ, S), run the hard gate, and
    time ONLY gate survivors on BOTH co-equal backends under the deterministic budget. On a
    proved had_2 < chi, escalate to the Tier-1 had_3 the same bounded way.

    Returns `{n: {"proved": bool, "rows": [...], "frontier_reached": bool}}` where "proved"
    (== "frontier_reached") is True iff at least one STRUCTURED gate-survivor at n had its
    had_2 optimality PROVED on both backends within budget — the flag that defines whether
    the structured exact window still reaches n. When `table_path` is given, every per-(n,
    kind) row is appended there (the box path); default None writes nothing (dev/unit path).
    """
    if num_workers != 1:
        raise ValueError(
            f"a recorded frontier must be single-worker (num_workers=1); got {num_workers!r}. "
            "Cores scale breadth of the hunt, never the determinism of a reported verdict "
            "(CLAUDE.md CP-SAT #3590/#3842/#4839)."
        )
    det_time, det_nodes = _resolve_budget(det_budget, det_time, det_nodes)

    table = {}
    for n in ns:
        group = Abelian([n])
        rng = gen_rng(seed)
        rows = []
        structured_proved = False
        for kind in kinds:
            S = _generate_S(kind, group, rng)
            if S is None:
                rows.append({
                    "n": n, "kind": kind, "gate_survived": False,
                    "generated": False, "had2_proved": False, "had3_proved": None,
                })
                continue
            adj = cayley_adj_abelian(group, S)
            nu = matching_number(adj, n)
            chi = n - nu
            omega = cliques.omega_G(adj, n)
            kappa = cliques.kappa_G(adj, n)
            inv = {"nu_H": nu, "chi_G": chi, "omega_G": omega, "kappa_G": kappa}
            gate = run_gate(adj, n, inv)
            if gate.verdict is not Verdict.PASS:
                rows.append({
                    "n": n, "kind": kind, "gate_survived": False, "generated": True,
                    "gate_verdict": gate.verdict.name, "gate_killing": gate.killing,
                    "chi": chi, "had2_proved": False, "had3_proved": None,
                })
                continue

            had2_proved, cbc2, cpsat2, had2_val = _time_optimality(
                adj, n, method="solve_had2", det_time=det_time, det_nodes=det_nodes
            )
            had3_proved = None
            cbc3 = cpsat3 = None
            if had2_proved and had2_val is not None and had2_val < chi:
                # had_2 < chi -> Tier-1 had_3 escalation, timed the same bounded way.
                had3_proved, cbc3, cpsat3, _ = _time_optimality(
                    adj, n, method="solve_had3", det_time=det_time, det_nodes=det_nodes
                )
            rows.append({
                "n": n, "kind": kind, "gate_survived": True, "generated": True,
                "chi": chi, "had2": had2_val,
                "had2_proved": bool(had2_proved), "had3_proved": had3_proved,
                "det_time": det_time, "det_nodes": det_nodes,
                "backends": {
                    "had2": {"cbc": cbc2, "cpsat": cpsat2},
                    "had3": {"cbc": cbc3, "cpsat": cpsat3},
                },
            })
            if _is_structured(kind) and had2_proved:
                structured_proved = True

        table[n] = {
            "proved": bool(structured_proved),
            "frontier_reached": bool(structured_proved),
            "rows": rows,
        }
        if table_path is not None:
            for row in rows:
                append_event(
                    {"subsystem": "pool/sumfree", "event": "frontier_row", **row},
                    path=os.fspath(table_path),
                )
    return table


def derive_frontier_n(table):
    """The conservative downward boundary: largest n whose structured had_2 proved AND every
    smaller measured n also proved. Returns None when the smallest measured n did not prove.

    Conservative (contiguous-from-bottom) so a single hard blip above the boundary can never
    inflate the exact window the sweep trusts — routing errs toward the RESISTANT E3 queue.
    """
    frontier = None
    for n in sorted(table):
        if table[n]["proved"]:
            frontier = n
        else:
            break
    return frontier


# The default coarse group-order grid the box probe walks (odd |Γ|, Locked Decision 1).
DEFAULT_PROBE_NS = (31, 61, 101, 151, 201, 251, 301)


def _atomic_write_json(path, payload):
    """Write `payload` as pretty JSON to `path` atomically (tempfile -> fsync -> replace)."""
    path = os.fspath(path)
    paths.ensure_parent(Path(path))
    directory = os.path.dirname(path) or "."
    line = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path


def run_frontier_probe(
    det_time,
    det_nodes,
    ns=None,
    *,
    seed=0,
    table_path=None,
    report_path=None,
):
    """Walk the coarse grid, persist the compact frontier report, and return it.

    The report — per-n structured-proved booleans + the derived `frontier_n` boundary + the
    (det_time, det_nodes) budget + solver versions — is what the 08-06 sweep consumes via
    `exact_window_max`. Every per-n row is logged to the append-only event stream. Persists
    atomically to `report_path` (default `paths.SUMFREE_FRONTIER_REPORT`); the AUTHORITATIVE
    report is regenerated on the shared box, not on a dev machine (docstring A4).
    """
    if ns is None:
        ns = DEFAULT_PROBE_NS
    if table_path is None:
        table_path = paths.SUMFREE_FRONTIER_TABLE
    if report_path is None:
        report_path = paths.SUMFREE_FRONTIER_REPORT

    table = measure_ilp_frontier(
        ns, det_time=det_time, det_nodes=det_nodes, seed=seed, table_path=table_path
    )
    per_n = {int(n): bool(table[n]["proved"]) for n in table}
    frontier_n = derive_frontier_n(table)

    solver_versions = {
        "cbc": get_backend("cbc").backend_version(),
        "cpsat": get_backend("cpsat").backend_version(),
    }
    report = {
        "kind": "sumfree_ilp_optimality_frontier",
        "a4_note": (
            "MEASURED budget-dependent evidence (RESEARCH A4): frontier_n is a function of "
            "(n, det_time, det_nodes), NOT wall-clock hardware speed, and NOT a theorem."
        ),
        "ns": list(int(n) for n in ns),
        "per_n_structured_had2_proved": per_n,
        "frontier_n": frontier_n,
        "det_time": det_time,
        "det_nodes": det_nodes,
        "solver_versions": solver_versions,
        "seed": seed,
    }

    for n in sorted(table):
        append_event(
            {
                "subsystem": "pool/sumfree",
                "event": "frontier_probe",
                "n": int(n),
                "structured_had2_proved": bool(table[n]["proved"]),
                "det_time": det_time,
                "det_nodes": det_nodes,
                "seed": seed,
            },
            path=os.fspath(table_path),
        )

    _atomic_write_json(report_path, report)
    return report


def exact_window_max(report):
    """The exact-window boundary the 08-06 sweep reads: the largest n where STRUCTURED had_2
    optimality proved on both backends (the conservative downward frontier).

    Returns `frontier_n` when present; else the largest contiguous-from-bottom proved n
    re-derived from the per-n booleans; 0 when no n proved (route everything to E3 — the
    conservative default). A non-packing instance at n ≤ window is an exact `g>0` candidate;
    at n > window it is a RESISTANT E3-queue instance, never a claimed break.
    """
    if not isinstance(report, dict):
        raise TypeError(f"report must be a dict, got {type(report).__name__}")
    frontier_n = report.get("frontier_n")
    if frontier_n is not None:
        return int(frontier_n)
    per_n = report.get("per_n_structured_had2_proved", {})
    window = 0
    for n in sorted(int(k) for k in per_n):
        if per_n[n] if n in per_n else per_n[str(n)]:
            window = n
        else:
            break
    return window
