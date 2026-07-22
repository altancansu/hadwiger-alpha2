"""OR-Tools CP-SAT adapter — the ONLY module that imports the ortools library.

Second independent exact engine for had_2 (EXACT-03), the CP-SAT twin of the
frozen `cbc.py` reference adapter. It translates the SAME checksum-gated
`Had2Problem` object into a CP-SAT model — identical *instance*, independent
*encoding* — which is exactly what makes a CBC-vs-CP-SAT agreement meaningful.

Model shape (mirrors cbc.py, swapping pulp -> cp_model):
  * Boolean var m_{u}_{v} per G-edge (pair variable, G-edges ONLY: that
    indexing IS the size-2 connectivity constraint), Boolean s_{v} per vertex;
  * per-vertex AddAtMostOne over its incident pair vars + its singleton;
  * conflict rows single-single / single-pair / pair-pair from the
    checksum-gated obstruction enumeration, iterated in sorted() order
    (determinism), each as an AddAtMostOne;
  * optimize: maximize(sum); decision: add(sum >= target_k), no objective.

Status honesty (the whole epistemic point — CP-SAT exists to DISAGREE with CBC
when one has a bug, so a mis-mapped status is a false claim):
  * PROVED_OPTIMAL is assigned ONLY when status == cp_model.OPTIMAL AND
    round(objective_value) == round(best_objective_bound) — the two-condition
    gate, the CP-SAT analog of pulp's two-field LpStatusOptimal AND
    LpSolutionOptimal. A stopped solve returns FEASIBLE with an incumbent it
    could not prove optimal -> INCUMBENT_ONLY (optimize) / MODEL_FOUND
    (decision); `exact_value()` is reachable only from PROVED_OPTIMAL, so the
    CP-SAT incumbent-as-optimum hole is unrepresentable.
  * INFEASIBLE in optimize mode is an encoding bug (the empty family is always
    feasible) and maps to ERROR — NEVER PROVED_INFEASIBLE.

Determinism (recorded / impossibility mode — Open-Q4 resolution): every solve
runs num_workers=1 with a pinned random_seed (the simplest clearly-deterministic
mode; `interleave_search` is deliberately NOT used here and is reserved for
later exploration/survivor scaling). The CP-SAT dual bound is read directly from
`solver.best_objective_bound`; unlike the CBC path there is NO archived search
log (none is generated and none is needed — nothing here rests on a log).

Extraction happens ONLY inside the status gate and is recompute-guarded:
CP-SAT booleans are exact (no fractional LP junk, so the CBC integrality loop
is dropped) but the count==objective recompute and the internal-disjointness
`used`-set guard are KEPT as the fail-closed check — any trip maps the whole
outcome to Status.ERROR. All guards raise or map to ERROR; nothing here is an
optimization-strippable statement. The returned family is an UNTRUSTED
proposal — only the frozen trust root confers truth on it.
"""
import importlib.metadata
import math
import time

from ortools.sat.python import cp_model

from alpha2.solvers.backend import register_backend
from alpha2.solvers.problems.had2 import build_had2_problem
from alpha2.solvers.problems.had3 import build_had3_problem
from alpha2.solvers.result import ExactOutcome, SolveParams, Status

# Pinned recorded-mode seed (Open-Q4: num_workers=1 + a fixed seed is the
# simplest clearly-deterministic mode). Matches the 04/05-RESEARCH live probe.
_RANDOM_SEED = 137

# Extraction is permitted ONLY for these statuses; for every other status the
# solver-side variable/objective values are meaningless (or radioactive) and
# are never read.
_EXTRACTABLE = frozenset(
    {Status.PROVED_OPTIMAL, Status.MODEL_FOUND, Status.INCUMBENT_ONLY}
)


def map_status(status, solver, mode):
    """Map (CpSolverStatus, solver, mode) to the locked Status table.

    PROVED_OPTIMAL requires status == cp_model.OPTIMAL AND
    round(objective_value) == round(best_objective_bound) — the two-condition
    conjunction, nothing weaker (defense-in-depth: obj != bound should never
    occur on an OPTIMAL return, and if it does it is an ERROR, not a value).

    FEASIBLE is NOT OPTIMAL: a stopped solve with an incumbent maps to
    INCUMBENT_ONLY (optimize) / MODEL_FOUND (decision), never to an exact value.

    Optimize mode can never be legitimately infeasible (the empty family is
    always feasible), so INFEASIBLE in optimize mode is an encoding bug and
    maps to ERROR — NEVER PROVED_INFEASIBLE. MODEL_INVALID / anything
    unrecognized is likewise ERROR.
    """
    if status == cp_model.OPTIMAL:
        if round(solver.objective_value) != round(solver.best_objective_bound):
            return Status.ERROR  # obj != bound on an OPTIMAL return: never happens
        return Status.MODEL_FOUND if mode == "decision" else Status.PROVED_OPTIMAL
    if status == cp_model.FEASIBLE:
        return Status.MODEL_FOUND if mode == "decision" else Status.INCUMBENT_ONLY
    if status == cp_model.INFEASIBLE:
        return Status.PROVED_INFEASIBLE if mode == "decision" else Status.ERROR
    if status == cp_model.UNKNOWN:
        return Status.UNKNOWN
    return Status.ERROR  # MODEL_INVALID or any unrecognized status


def _guarded_extract(solver, mv, sv, problem, n, mode, target_k):
    """Extract the family from the CP-SAT booleans, guarded. None on any trip.

    Guards (each maps the whole outcome to Status.ERROR at the caller):
      (a) recompute — optimize: the reported objective, rounded to the nearest
          integer, EXACTLY equals the count of extracted sets; decision:
          count >= target_k (the target constraint is the recompute, there
          being no objective);
      (b) internal disjointness of the extracted sets.
    CP-SAT booleans are exact, so no fractional-integrality loop is needed.
    """
    fam = [tuple(e) for e in problem.Gedges if solver.boolean_value(mv[e])] + [
        (v,) for v in range(n) if solver.boolean_value(sv[v])
    ]
    if mode == "optimize":
        if round(solver.objective_value) != len(fam):
            return None  # recompute guard: fail closed
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


def _guarded_extract3(solver, mv, sv, tv, problem2, triples, n, mode, target_k):
    """had_3 analog of `_guarded_extract`: same guards, extended over triple vars.

    The extracted family now mixes size-1/2/3 sets. CP-SAT booleans are exact, so
    (as in the had_2 extractor) no fractional-integrality loop is needed; the
    count==objective recompute and the internal-disjointness `used`-set guard are
    KEPT as the fail-closed check. solve_had2 and its `_guarded_extract` are left
    byte-unchanged.
    """
    fam = (
        [tuple(e) for e in problem2.Gedges if solver.boolean_value(mv[e])]
        + [(v,) for v in range(n) if solver.boolean_value(sv[v])]
        + [tuple(T) for T in triples if solver.boolean_value(tv[T])]
    )
    if mode == "optimize":
        if round(solver.objective_value) != len(fam):
            return None  # recompute guard: fail closed
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


class CPSATBackend:
    """ExactBackend over OR-Tools CP-SAT (the second, independent exact engine)."""

    name = "cpsat"

    def backend_version(self):
        return f"ortools=={importlib.metadata.version('ortools')}"

    def solve_had2(self, adj, n, *, mode, target_k=None, params=None, symmetry_level=None):
        if mode not in ("optimize", "decision"):
            raise ValueError(f"mode must be 'optimize' or 'decision', got {mode!r}")
        if mode == "decision":
            # bool subclasses int (isinstance(True, int) is True), so a caller
            # bug passing a comparison result would silently run a k=1 decision
            # solve and return an honest-looking MODEL_FOUND — a
            # wrong-question-right-answer failure the status discipline cannot
            # catch (WR-04). Reject bool explicitly.
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
        t0 = time.monotonic()

        problem = build_had2_problem(adj, n)  # checksum-gated on EVERY build
        Gedges = problem.Gedges

        m = cp_model.CpModel()
        mv = {e: m.new_bool_var(f"m_{e[0]}_{e[1]}") for e in Gedges}
        sv = {v: m.new_bool_var(f"s_{v}") for v in range(n)}
        size = sum(mv.values()) + sum(sv.values())
        if mode == "optimize":
            m.maximize(size)
        else:
            m.add(size >= target_k)  # constant objective: pure feasibility
        for v in range(n):
            m.add_at_most_one([mv[e] for e in Gedges if v in e] + [sv[v]])
        # Conflict rows from the checksum-gated enumeration (sorted: determinism).
        for (u, v) in sorted(problem.ss):
            m.add_at_most_one([sv[u], sv[v]])
        for (v, (a, b)) in sorted(problem.sp):
            m.add_at_most_one([sv[v], mv[(a, b)]])
        for e1, e2 in sorted(tuple(sorted(pair)) for pair in problem.pp):
            m.add_at_most_one([mv[e1], mv[e2]])

        solver = cp_model.CpSolver()
        # Deterministic recorded/impossibility mode: single worker + pinned seed.
        solver.parameters.num_workers = 1
        solver.parameters.random_seed = _RANDOM_SEED
        if p.time_limit_s is not None:
            solver.parameters.max_time_in_seconds = p.time_limit_s
        if mode == "decision":
            solver.parameters.stop_after_first_solution = True
        if symmetry_level is not None:
            solver.parameters.symmetry_level = symmetry_level
        # No search log is captured or archived: the CP-SAT bound is read
        # directly from solver.best_objective_bound, so there is no CBC-style
        # logPath to write (log_search_progress is left at its default-off —
        # enabling it would only add solver overhead for output we discard).
        # NOTE: do NOT set search_branching with a bare int — it is an enum and
        # a plain integer raises TypeError. It is not needed here.

        cp_status = solver.solve(m)
        status = map_status(cp_status, solver, mode)

        value = None
        family = None
        if status in _EXTRACTABLE:
            fam = _guarded_extract(solver, mv, sv, problem, n, mode, target_k)
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
                # No cbc_log analog exists — do NOT invent one. Use the solver's
                # dual bound when finite, else the trivial bound n; either way
                # the provenance is "trivial_n".
                bb = solver.best_objective_bound
                bound = round(bb) if math.isfinite(bb) else n
                bound_source = "trivial_n"

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

    def solve_had3(self, adj, n, *, mode, target_k=None, params=None, symmetry_level=None):
        """had_3 escalation tier (EXACT-05), behind its own method (a flag).

        The CP-SAT twin of `CBCBackend.solve_had3`: the had_2 Bools (G-edge pairs +
        singletons) AND the checksum-gated triple Bools (<=1 internal H-edge) from
        the SAME frozen `Had3Problem`, so a CBC-vs-CP-SAT had_3 agreement is
        meaningful (identical instance, independent encoding). Objective unchanged
        (maximize family size). Same OPTIMAL + round(obj)==round(bound) gate and
        determinism (num_workers=1 + pinned seed) as solve_had2, which is left
        byte-unchanged. The returned family is an UNTRUSTED proposal.
        """
        if mode not in ("optimize", "decision"):
            raise ValueError(f"mode must be 'optimize' or 'decision', got {mode!r}")
        if mode == "decision":
            # bool subclasses int: reject explicitly (WR-04), as solve_had2 does.
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
        t0 = time.monotonic()

        problem2 = build_had2_problem(adj, n)  # checksum-gated on EVERY build
        problem3 = build_had3_problem(adj, n)  # checksum-gated on EVERY build
        Gedges = problem2.Gedges
        triples = problem3.triples

        m = cp_model.CpModel()
        mv = {e: m.new_bool_var(f"m_{e[0]}_{e[1]}") for e in Gedges}
        sv = {v: m.new_bool_var(f"s_{v}") for v in range(n)}
        tv = {T: m.new_bool_var(f"t_{T[0]}_{T[1]}_{T[2]}") for T in triples}
        size = sum(mv.values()) + sum(sv.values()) + sum(tv.values())
        if mode == "optimize":
            m.maximize(size)
        else:
            m.add(size >= target_k)  # constant objective: pure feasibility
        # Per-vertex disjointness INCLUDING the triple vars that cover a vertex.
        for v in range(n):
            m.add_at_most_one(
                [mv[e] for e in Gedges if v in e]
                + [sv[v]]
                + [tv[T] for T in triples if v in T]
            )
        # had_2 conflict rows (sorted: determinism).
        for (u, v) in sorted(problem2.ss):
            m.add_at_most_one([sv[u], sv[v]])
        for (v, (a, b)) in sorted(problem2.sp):
            m.add_at_most_one([sv[v], mv[(a, b)]])
        for e1, e2 in sorted(tuple(sorted(pair)) for pair in problem2.pp):
            m.add_at_most_one([mv[e1], mv[e2]])
        # had_3 size-3 conflict rows: triple-single and triple-pair (sorted).
        for (T, S) in sorted(problem3.conflicts):
            if len(S) == 1:
                m.add_at_most_one([tv[T], sv[S[0]]])
            else:
                m.add_at_most_one([tv[T], mv[S]])

        solver = cp_model.CpSolver()
        # Deterministic recorded/impossibility mode: single worker + pinned seed.
        solver.parameters.num_workers = 1
        solver.parameters.random_seed = _RANDOM_SEED
        if p.time_limit_s is not None:
            solver.parameters.max_time_in_seconds = p.time_limit_s
        if mode == "decision":
            solver.parameters.stop_after_first_solution = True
        if symmetry_level is not None:
            solver.parameters.symmetry_level = symmetry_level
        # No search log is captured or archived: the bound comes directly from
        # solver.best_objective_bound (see solve_had2 for the full rationale).

        cp_status = solver.solve(m)
        status = map_status(cp_status, solver, mode)

        value = None
        family = None
        if status in _EXTRACTABLE:
            fam = _guarded_extract3(
                solver, mv, sv, tv, problem2, triples, n, mode, target_k
            )
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
                bb = solver.best_objective_bound
                bound = round(bb) if math.isfinite(bb) else n
                bound_source = "trivial_n"

        return ExactOutcome(
            problem="had3",
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


register_backend("cpsat", CPSATBackend)
