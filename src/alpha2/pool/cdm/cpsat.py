"""CDM CP-SAT cross-check — the ONLY new module that imports the ortools library.

`cdm_cpsat(adj, n)` is the independent second engine for the CDM property
(Costa-Luu-Wood-Yip arXiv:2512.17114, Conjecture 10). It re-decides — from an
INDEPENDENT Boolean encoding — the same question the trusted DFS reference
(`pool/cdm/reference.has_cdm`) answers, which is exactly what makes a
DFS-vs-CP-SAT agreement meaningful. It returns only a boolean verdict:
`True` iff G has a non-empty connected dominating matching.

ortools confinement (mirrors `solvers/cpsat.py`): this is the single module in
`pool/cdm/` allowed to `from ortools.sat.python import cp_model`; the reference
arbiter imports no solver at all.

Impossibility discipline (LOCKED — the whole epistemic point): a CDM-FAIL is an
INFEASIBLE verdict, and INFEASIBLE is impossibility-flavored, hence RADIOACTIVE.
Documented CP-SAT wrong-INFEASIBLE / nondeterminism regressions (#3590/#3842/
#4839) make a multi-worker UNSAT untrustworthy, so every solve here runs
`num_workers=1` with a pinned `random_seed = 137` (the exact idiom established in
`solvers/cpsat.py`). This function NEVER reports CDM-FAIL as truth on its own —
the exhaustive DFS reference is the arbiter, and their agreement is enforced
(release-blocking) in the differential gate. A SAT witness is likewise NOT
trusted here (adjudicate.py routes it through `verify_cdm_witness`); this
function is a decision oracle, not a certificate source.

Encoding (a direct Boolean transcription of the §1 definitions; adj =
list[set[int]], adj[u] = neighbours of u in G):
  * x[e] Bool per G-edge e=(a,b), a<b;
  * matching  — per vertex, AddAtMostOne over its incident edge vars;
  * non-empty — Add(sum(x) >= 1);
  * connected — for every disjoint, NON-V-adjacent edge pair (e,f):
    Add(x[e] + x[f] <= 1) (the two edges may not both be chosen);
  * dominating — for each edge e and each vertex w not adjacent to EITHER
    endpoint of e: Add(x[e] <= sum(inc_w)) (choosing e forces w to be matched).
All three constraint families iterate their sources in sorted() order so the
built model — and therefore the deterministic solve — is reproducible.
"""
from ortools.sat.python import cp_model

# Pinned deterministic seed: num_workers=1 + a fixed seed is the simplest
# clearly-deterministic mode, mandatory because a CDM-FAIL (INFEASIBLE) is
# radioactive. Matches solvers/cpsat.py._RANDOM_SEED.
_RANDOM_SEED = 137


def cdm_cpsat(adj, n):
    """Return True iff G has a non-empty connected dominating matching.

    Independent CP-SAT cross-check of `reference.has_cdm`. The INFEASIBLE (CDM-
    FAIL) direction is decided under num_workers=1 + pinned seed (deterministic);
    the verdict is never trusted as truth without the DFS reference agreeing.
    """
    E = [(a, b) for a in range(n) for b in sorted(adj[a]) if a < b]

    m = cp_model.CpModel()
    x = {e: m.new_bool_var(f"x_{e[0]}_{e[1]}") for e in E}

    # matching: each vertex lies in at most one chosen edge.
    for v in range(n):
        inc = [x[e] for e in E if v in e]
        if inc:
            m.add_at_most_one(inc)

    # non-empty.
    m.add(sum(x.values()) >= 1)

    # connected: forbid two disjoint, non-V-adjacent edges together (sorted).
    for i, e in enumerate(E):
        a, b = e
        for f in E[i + 1:]:
            c, d = f
            if c == a or c == b or d == a or d == b:
                continue  # share a vertex -> matching constraint already excludes
            if not (c in adj[a] or d in adj[a] or c in adj[b] or d in adj[b]):
                m.add(x[e] + x[f] <= 1)

    # dominating: w non-adjacent to BOTH endpoints of e => choosing e forces w matched.
    for e in E:
        a, b = e
        for w in range(n):
            if w == a or w == b:
                continue
            if w not in adj[a] and w not in adj[b]:
                inc_w = [x[g] for g in E if w in g]
                m.add(x[e] <= sum(inc_w))

    solver = cp_model.CpSolver()
    # Deterministic impossibility mode: single worker + pinned seed. A pure
    # feasibility model (no objective) — stop at the first solution when SAT.
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = _RANDOM_SEED
    solver.parameters.stop_after_first_solution = True

    status = solver.solve(m)
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
