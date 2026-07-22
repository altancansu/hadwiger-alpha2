"""PULP_CBC_CMD adapter — the ONLY module that imports the pulp library.

Reference engine for exact had_2 (EXACT-02), byte-compatible with the Appendix
C.3 model shape: LpProblem("had2", LpMaximize), Binary variables named
m_{u}_{v} (pair, G-edges only) and s_{v} (singleton), objective
lpSum(mv) + lpSum(sv), per-vertex disjointness rows. Conflict rows come from
the checksum-gated obstruction enumeration in problems/had2.py (proven
set-equal to the C.3/C.4 naive loops).

What this adapter deliberately does NOT copy from Appendix C.3 (the soundness
holes Phase 4 closes):
  * the ungated objective read — extraction happens ONLY inside the status
    gate, and values are integrality- and recompute-guarded;
  * int(round(...)) of a possibly-fractional objective;
  * any family truncation — the FULL family is returned, always.

The PROVED_OPTIMAL gate is the two-field conjunction
    prob.status == LpStatusOptimal AND prob.sol_status == LpSolutionOptimal
— NOTHING WEAKER. pulp 3.3.2 maps a timed-out run with an incumbent to
(LpStatusOptimal, LpSolutionIntegerFeasible), so prob.status alone is provably
insufficient (the incumbent-as-optimum hole reproduced live in 04-RESEARCH).

Every solve runs single-thread with logPath set (evidence + dual bound; msg=0
would otherwise hide the "Stopped" line). All guards raise or map the outcome
to Status.ERROR — no optimization-strippable statements.
"""
import subprocess
import tempfile
import time
from pathlib import Path

import pulp

from alpha2.solvers.backend import register_backend
from alpha2.solvers.problems.had2 import build_had2_problem
from alpha2.solvers.result import ExactOutcome, SolveParams, Status

_INTEGRALITY_TOL = 1e-6

# Extraction is permitted ONLY for these statuses; for every other status the
# solver-side variable/objective values are garbage (fractional LP junk on
# NotSolved, stale values on Infeasible — both observed live) and never read.
_EXTRACTABLE = frozenset(
    {Status.PROVED_OPTIMAL, Status.MODEL_FOUND, Status.INCUMBENT_ONLY}
)


def map_status(status, sol_status, mode):
    """Map (prob.status, prob.sol_status, mode) to the locked Status table.

    PROVED_OPTIMAL requires status == LpStatusOptimal AND sol_status ==
    LpSolutionOptimal — the two-field conjunction, nothing weaker.

    Optimize mode can never be legitimately infeasible (the empty family is
    always feasible), so Infeasible in optimize mode is an encoding bug and
    maps to ERROR — never PROVED_INFEASIBLE. Unbounded is likewise ERROR (the
    objective is structurally <= n).
    """
    if status == pulp.LpStatusOptimal and sol_status == pulp.LpSolutionOptimal:
        return Status.MODEL_FOUND if mode == "decision" else Status.PROVED_OPTIMAL
    if status == pulp.LpStatusOptimal and sol_status == pulp.LpSolutionIntegerFeasible:
        # Stopped with an incumbent: in decision mode a feasible incumbent still
        # witnesses the target (the verifier arbitrates); in optimize mode it is
        # NOT exact.
        return Status.MODEL_FOUND if mode == "decision" else Status.INCUMBENT_ONLY
    if status == pulp.LpStatusInfeasible:
        return Status.PROVED_INFEASIBLE if mode == "decision" else Status.ERROR
    if status == pulp.LpStatusNotSolved:
        return Status.UNKNOWN
    return Status.ERROR  # Unbounded or any unrecognized pairing


def parse_bound(log_text):
    """Parse the dual bound ("Upper bound:" line) from a CBC 2.10.3 log.

    Returns None when the line is absent (caller falls back to the trivial
    bound n, provenance-tagged). Grammar is CBC-2.10.3-specific — one more
    reason the library pin is load-bearing.
    """
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Upper bound:"):
            try:
                return float(stripped.split(":", 1)[1])
            except ValueError:
                return None
    return None


_CBC_VERSION_CACHE = None


def cbc_binary_version():
    """Probe the bundled CBC binary's banner version (e.g. "2.10.3").

    Runs `[cbc_path, "-exit"]` once per process and caches the parsed
    "Version:" banner line. Returns "unknown" on any probe failure (the
    outcome then still records the honest string).
    """
    global _CBC_VERSION_CACHE
    if _CBC_VERSION_CACHE is not None:
        return _CBC_VERSION_CACHE
    ver = "unknown"
    try:
        path = pulp.PULP_CBC_CMD(msg=0).path
        out = subprocess.run(
            [path, "-exit"], capture_output=True, text=True, timeout=30
        )
        for line in out.stdout.splitlines():
            if line.strip().startswith("Version:"):
                ver = line.split(":", 1)[1].strip()
                break
    except (OSError, subprocess.SubprocessError):
        ver = "unknown"
    _CBC_VERSION_CACHE = ver
    return ver


def _guarded_extract(prob, mv, sv, Gedges, n, mode, target_k):
    """Extract the family (Appendix C.3 shape), guarded. None when a guard trips.

    Guards (each maps the whole outcome to Status.ERROR at the caller):
      (a) integrality — every binary within 1e-6 of {0, 1} (pulp#517 defense);
      (b) recompute — optimize: the reported objective, rounded to the nearest
          integer, equals the count of extracted sets EXACTLY, and the
          sub-integer drift stays within #vars * 1e-6 (per-variable drift up
          to the integrality tolerance accumulates across the sum, so a flat
          1e-6 gate would spuriously ERROR a genuine optimum at scaled n —
          04-REVIEW WR-03; a real count mismatch is >= 1 - #vars*1e-6 and
          always trips). Decision: count >= target_k (the objective is the
          constant 0 there, so the target constraint is the recompute);
      (c) internal disjointness of the extracted sets.
    """
    for var in list(mv.values()) + list(sv.values()):
        x = var.value()
        if x is None:
            return None
        if min(abs(x), abs(x - 1.0)) > _INTEGRALITY_TOL:
            return None
    fam = [tuple(e) for e in Gedges if mv[e].value() > 0.5] + [
        (v,) for v in range(n) if sv[v].value() > 0.5
    ]
    if mode == "optimize":
        reported = pulp.value(prob.objective)
        if reported is None:
            return None
        # Scale-robust count comparison (WR-03): every binary already passed
        # the per-variable integrality gate above, so compare at count
        # resolution — round the reported sum to the nearest integer and
        # require EXACT equality with the extracted count — while keeping
        # sub-integer drift fatal beyond the accumulated per-variable budget
        # (#vars * _INTEGRALITY_TOL). Fail-closed: a genuine count mismatch
        # shifts the sum by >= 1 - #vars*tol and trips the round check.
        nvars = len(mv) + len(sv)
        if round(reported) != len(fam):
            return None
        if abs(reported - round(reported)) > nvars * _INTEGRALITY_TOL:
            return None
    else:
        if len(fam) < target_k:
            return None
    used = set()
    for s in fam:
        for v in s:
            if v in used:
                return None
            used.add(v)
    return tuple(fam)


class CBCBackend:
    """ExactBackend over the bundled CBC via PULP_CBC_CMD (reference lineage)."""

    name = "cbc"

    def backend_version(self):
        return f"pulp=={pulp.__version__} / CBC {cbc_binary_version()}"

    def solve_had2(self, adj, n, *, mode, target_k=None, params=None):
        if mode not in ("optimize", "decision"):
            raise ValueError(f"mode must be 'optimize' or 'decision', got {mode!r}")
        if mode == "decision":
            # bool subclasses int (isinstance(True, int) is True), so a caller
            # bug passing a comparison result would silently run a k=1
            # decision solve and return an honest-looking MODEL_FOUND — a
            # wrong-question-right-answer failure the status discipline
            # cannot catch (04-REVIEW WR-04). Reject bool explicitly.
            if (
                not isinstance(target_k, int)
                or isinstance(target_k, bool)
                or target_k < 1
            ):
                raise ValueError(
                    f"decision mode requires a positive int target_k "
                    f"(bool rejected: True would silently mean k=1), "
                    f"got {target_k!r}"
                )
        elif target_k is not None:
            raise ValueError("target_k is only meaningful in decision mode")
        p = params if params is not None else SolveParams()
        if p.threads != 1:
            raise ValueError(
                "the CBC reference backend is single-thread by contract "
                f"(deterministic reference lineage); got threads={p.threads!r}"
            )
        t0 = time.monotonic()

        problem = build_had2_problem(adj, n)  # checksum-gated on EVERY build
        Gedges = problem.Gedges

        # Appendix C.3 model shape (byte-compat): names, objective, disjointness.
        prob = pulp.LpProblem("had2", pulp.LpMaximize)
        mv = {
            e: pulp.LpVariable(f"m_{e[0]}_{e[1]}", cat="Binary") for e in Gedges
        }
        sv = {v: pulp.LpVariable(f"s_{v}", cat="Binary") for v in range(n)}
        size = pulp.lpSum(mv.values()) + pulp.lpSum(sv.values())
        if mode == "optimize":
            prob += size
        else:
            prob += 0  # constant objective: pure feasibility
            prob += size >= target_k
        for v in range(n):
            prob += pulp.lpSum(mv[e] for e in Gedges if v in e) + sv[v] <= 1
        # Conflict rows from the checksum-gated enumeration (sorted: determinism).
        for (u, v) in sorted(problem.ss):
            prob += sv[u] + sv[v] <= 1
        for (v, (a, b)) in sorted(problem.sp):
            prob += sv[v] + mv[(a, b)] <= 1
        for e1, e2 in sorted(tuple(sorted(pair)) for pair in problem.pp):
            prob += mv[e1] + mv[e2] <= 1

        solve_error = False
        log_text = ""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "cbc.log"
            solver = pulp.PULP_CBC_CMD(
                msg=0,
                threads=1,  # single-thread: deterministic reference lineage
                timeLimit=p.time_limit_s,
                logPath=str(log_path),  # ALWAYS: evidence + dual bound
            )
            try:
                prob.solve(solver)
            except pulp.PulpSolverError:
                solve_error = True
            if log_path.exists():
                log_text = log_path.read_text()

        status = (
            Status.ERROR
            if solve_error
            else map_status(prob.status, prob.sol_status, mode)
        )

        value = None
        family = None
        if status in _EXTRACTABLE:
            fam = _guarded_extract(prob, mv, sv, Gedges, n, mode, target_k)
            if fam is None:
                status = Status.ERROR  # guard tripped: nothing crosses the gate
            else:
                family = fam
                value = len(fam)

        bound = None
        bound_source = "none"
        if mode == "optimize":
            if status is Status.PROVED_OPTIMAL:
                bound, bound_source = value, "definition"
            elif status in (Status.INCUMBENT_ONLY, Status.UNKNOWN):
                parsed = parse_bound(log_text)
                if parsed is not None:
                    bound, bound_source = parsed, "cbc_log"
                else:
                    bound, bound_source = n, "trivial_n"

        return ExactOutcome(
            problem="had2",
            mode=mode,
            status=status,
            value=value,
            bound=bound,
            bound_source=bound_source,
            family=family,
            backend=self.name,
            backend_version=self.backend_version(),
            params=p,
            wall_time_s=time.monotonic() - t0,
        )


register_backend("cbc", CBCBackend)
