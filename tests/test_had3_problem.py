"""had_3 (size-3 branch-set) obstruction-enumeration semantics — EXACT-05.

The size-3 escalation model (`alpha2.solvers.problems.had3`) is the ONE
genuinely-new piece of combinatorics in Phase 5, and RESEARCH Pitfall 3 warns
that size-3 conflicts are NOT a clean local substructure of H — so this file is
the first of the three independent guards (checksum here, verifier in Plan 03,
CBC/CP-SAT differential in Plan 05).

It pins the size-3 contract from BOTH sides, exactly like `test_had2_problem`:

  * the TRIPLE INDEX is the size-3 connectivity constraint by indexing — a
    triple {a,b,c} is legal iff it induces a CONNECTED subgraph of G, i.e.
    >=2 of the 3 internal pairs are G-edges <=> <=1 pair is an H-edge. Proved
    SET-equal (not merely count-equal) against a test-local naive all-triples
    reference on >=3 synthetic H;
  * CONFLICTS are enumerated from each triple's common H-neighborhood
    W(T) = N_H(a) & N_H(b) & N_H(c): T conflicts with a set S iff every vertex
    of S lies in W(T) (every cross pair is an H-edge = non-adjacent in G). The
    naive reference here scans the DEFINITION (all cross pairs are H-edges),
    independent of the module's W-shortcut;
  * empirically-pinned structural checksum literals (len(triples),
    len(conflicts)) on fixed synthetic instances;
  * a mutation test proving the checksum gate RAISES `ChecksumError` (raise-
    based, not an -O-strippable assert) when any single element is dropped;
  * refusal of a triangle-containing H at build; backend-neutrality (importing
    had3 pulls in no solver library);
  * a genuine size-3-FORCED instance (had_2 < had_3 by test-local brute force —
    the size-3 branch set is load-bearing) whose forcing triple IS present in
    the index.

The naive loops live ONLY here as test-local reference code (they never become
a production path). Expected constants are in-file literals (embedded-literal
discipline, mirroring test_had2_problem).
"""
import subprocess
import sys
from itertools import combinations
from math import comb

import pytest

from alpha2.solvers.problems import had3 as had3_module
from alpha2.solvers.problems.had3 import (
    ChecksumError,
    build_had3_problem,
    enumerate_had3,
)


# --------------------------------------------------------------------------- #
# Instance builders (small, hand-checkable, triangle-free).
# --------------------------------------------------------------------------- #
def _adj(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _c5():
    """H = C5: every legal triple is a seagull (exactly 1 H-edge) -> W empty."""
    return _adj(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])


def _star_k14():
    """H = K_{1,4}: leaves form G-triangles with common H-neighbor (the hub)."""
    return _adj(5, [(0, 1), (0, 2), (0, 3), (0, 4)])


def _k23():
    """H = K_{2,3}: one G-triangle {2,3,4}, both parts hand-derivable."""
    return _adj(5, [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4)])


def _path6():
    """H = P6 (path): cherry-rich, all interior triples are seagulls."""
    return _adj(6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])


# A GENUINE size-3-forced triangle-free H (n=7): had_2 = 4 < had_3 = 5, so the
# size-3 branch set {0,5,6} is load-bearing (found by exhaustive search, then
# hand-frozen). NOTE: no triangle-free H with had_2 < chi is known (296/296 are
# killed at had_2 — that would be a Hadwiger counterexample), so the honest
# escalation signal is had_2 < had_3, verified below by test-local brute force.
_FORCED_EDGES = [(0, 1), (0, 2), (0, 5), (1, 6), (2, 6),
                 (3, 5), (3, 6), (4, 5), (4, 6)]


def _forced():
    return _adj(7, _FORCED_EDGES)


# (id, adj, n, (n_triples, n_conflicts)) — checksum literals from the
# INDEPENDENT naive reference below (never from the module under test).
CHECKSUM_LITERALS = [
    ("c5", _c5(), 5, (5, 0)),
    ("star_k14", _star_k14(), 5, (4, 4)),
    ("k23", _k23(), 5, (1, 3)),
    ("forced_n7", _forced(), 7, (19, 6)),
]
CHECKSUM_IDS = [name for name, *_ in CHECKSUM_LITERALS]


# --------------------------------------------------------------------------- #
# Test-local naive reference — INDEPENDENT of the module under test.
#   triples: all C(n,3) triples kept iff <=1 internal H-edge (>=2 G-edges).
#   conflicts: (T, S) by DEFINITION (every cross pair is an H-edge), S ranging
#              over singletons and G-edge pairs. Element conventions match the
#              module: T = (a,b,c) with a<b<c; S = (v,) or (u,w) with u<w.
# --------------------------------------------------------------------------- #
def _naive_triples(adj, n):
    return [
        (a, b, c)
        for a in range(n) for b in range(a + 1, n) for c in range(b + 1, n)
        if ((b in adj[a]) + (c in adj[a]) + (c in adj[b])) <= 1
    ]


def _naive_conflicts(adj, n):
    conf = set()
    for (a, b, c) in _naive_triples(adj, n):
        T = (a, b, c)
        for v in range(n):                       # triple-single
            if v in T:
                continue
            if a in adj[v] and b in adj[v] and c in adj[v]:   # all cross H-edges
                conf.add((T, (v,)))
        for u in range(n):                       # triple-pair (G-edge pairs)
            for w in range(u + 1, n):
                if u in T or w in T:
                    continue
                if w in adj[u]:                  # must be a G-edge pair variable
                    continue
                if (a in adj[u] and b in adj[u] and c in adj[u]
                        and a in adj[w] and b in adj[w] and c in adj[w]):
                    conf.add((T, (u, w)))
    return conf


# --------------------------------------------------------------------------- #
# Test-local exhaustive brute-force had_k — INDEPENDENT semantics (imports
# nothing from had3). had_k = max K_m minor with all branch sets connected in G
# and of size <= k, pairwise disjoint AND pairwise adjacent in G.
# --------------------------------------------------------------------------- #
def _connected_in_G(S, adj):
    S = list(S)
    seen = {S[0]}
    stack = [S[0]]
    members = set(S)
    while stack:
        x = stack.pop()
        for y in members:
            if y not in seen and y not in adj[x]:   # a G-edge x-y
                seen.add(y)
                stack.append(y)
    return len(seen) == len(S)


def _g_adjacent(A, B, adj):
    return any(a != b and b not in adj[a] for a in A for b in B)


def _brute_had_k(adj, n, k):
    cands = []
    for size in range(1, k + 1):
        for S in combinations(range(n), size):
            if size == 1 or _connected_in_G(S, adj):
                cands.append(frozenset(S))
    m = len(cands)
    comp = [
        [i != j and not (cands[i] & cands[j]) and _g_adjacent(cands[i], cands[j], adj)
         for j in range(m)]
        for i in range(m)
    ]
    best = 0

    def extend(size, allowed):
        nonlocal best
        if size > best:
            best = size
        for idx, i in enumerate(allowed):
            if size + (len(allowed) - idx) <= best:
                return
            extend(size + 1, [j for j in allowed[idx + 1:] if comp[i][j]])

    extend(0, list(range(m)))
    return best


# --------------------------------------------------------------------------- #
# Test 1 — triple index = connectivity-by-index, SET-equal to the naive loop.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name,adj,n,_cs", CHECKSUM_LITERALS, ids=CHECKSUM_IDS)
def test_triple_index_is_connectivity_by_index(name, adj, n, _cs):
    triples, _conflicts = enumerate_had3(adj, n)
    assert set(triples) == set(_naive_triples(adj, n))
    # canonical: sorted ascending tuples a<b<c
    assert all(a < b < c for (a, b, c) in triples)
    assert list(triples) == sorted(triples)


def test_triple_index_covers_cherry_rich_path():
    """A path (cherry-rich) H: every interior triple is a seagull, none dropped
    for the wrong reason — set-equality against the naive reference."""
    adj = _path6()
    triples, _ = enumerate_had3(adj, 6)
    assert set(triples) == set(_naive_triples(adj, 6))


# --------------------------------------------------------------------------- #
# Test 2 — every indexed triple has <=1 internal H-edge (checked vs adj).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name,adj,n,_cs", CHECKSUM_LITERALS, ids=CHECKSUM_IDS)
def test_triples_have_at_most_one_H_edge(name, adj, n, _cs):
    triples, _ = enumerate_had3(adj, n)
    for (a, b, c) in triples:
        h_edges = (b in adj[a]) + (c in adj[a]) + (c in adj[b])
        assert h_edges <= 1


# --------------------------------------------------------------------------- #
# Test 3 — conflict pruning by common H-neighborhood.
# --------------------------------------------------------------------------- #
def test_conflict_pruning_common_neighborhood():
    """K_{2,3}: the single G-triangle {2,3,4} has W = {0,1}, giving exactly the
    two triple-single and one triple-pair conflicts — hand-derived."""
    adj = _k23()
    _triples, conflicts = enumerate_had3(adj, 5)
    expected = {
        ((2, 3, 4), (0,)),
        ((2, 3, 4), (1,)),
        ((2, 3, 4), (0, 1)),
    }
    assert conflicts == expected
    # SET-equal to the independent naive definitional scan as well
    assert conflicts == _naive_conflicts(adj, 5)


def test_empty_common_neighborhood_yields_no_conflict():
    """C5: every legal triple is a seagull (exactly 1 H-edge) so W(T) is empty
    for all of them -> zero conflicts (the pruning excludes empty-W triples)."""
    adj = _c5()
    _triples, conflicts = enumerate_had3(adj, 5)
    assert conflicts == set()


@pytest.mark.parametrize("name,adj,n,_cs", CHECKSUM_LITERALS, ids=CHECKSUM_IDS)
def test_conflicts_set_equal_to_naive(name, adj, n, _cs):
    _triples, conflicts = enumerate_had3(adj, n)
    assert conflicts == _naive_conflicts(adj, n)


# --------------------------------------------------------------------------- #
# Test 4 — empirically-pinned checksum literals.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name,adj,n,cs", CHECKSUM_LITERALS, ids=CHECKSUM_IDS)
def test_checksum_literals(name, adj, n, cs):
    triples, conflicts = enumerate_had3(adj, n)
    assert (len(triples), len(conflicts)) == cs


def test_unmutated_build_passes_the_gate():
    """Control leg: a clean build returns the pinned counts without raising."""
    adj = _k23()
    problem = build_had3_problem(adj, 5)
    assert (len(problem.triples), len(problem.conflicts)) == (1, 3)


# --------------------------------------------------------------------------- #
# Test 5 — mutation -> ChecksumError (raise-based; -O-correct).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mutated_class", ["triples", "conflicts"])
def test_mutation_raises_checksum_error(mutated_class, monkeypatch):
    """Drop one enumerated element; build must raise ChecksumError because the
    gate recomputes the counts independently from H's degrees/codegrees."""
    adj = _star_k14()            # 4 triples, 4 conflicts (both classes nonzero)
    real = had3_module.enumerate_had3

    def tampered(a, n):
        triples, conflicts = real(a, n)
        if mutated_class == "triples":
            triples = list(triples)[:-1]
        else:
            conflicts = conflicts - {min(conflicts)}
        return triples, conflicts

    monkeypatch.setattr(had3_module, "enumerate_had3", tampered)
    with pytest.raises(ChecksumError):
        had3_module.build_had3_problem(adj, 5)


# --------------------------------------------------------------------------- #
# Test 6 — triangle-containing H refused at build.
# --------------------------------------------------------------------------- #
def test_triangle_containing_h_refused_at_build():
    adj = [{1, 2}, {0, 2}, {0, 1}, set()]     # triangle 0-1-2
    with pytest.raises(ValueError):
        build_had3_problem(adj, 4)


# --------------------------------------------------------------------------- #
# Test 7 — backend-neutrality: importing had3 pulls in NO solver library.
# --------------------------------------------------------------------------- #
def test_had3_imports_no_solver_library():
    code = (
        "import sys\n"
        "import alpha2.solvers.problems.had3\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in ('ortools', 'pulp')]\n"
        "assert not bad, bad\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


# --------------------------------------------------------------------------- #
# Test 8 — genuine size-3-forced instance: had_2 < had_3 and the forcing triple
# is present in the index (the model can REPRESENT the escalation).
# --------------------------------------------------------------------------- #
def test_size3_forced_instance_shape():
    adj = _forced()
    n = 7
    # genuine escalation, established by INDEPENDENT brute force:
    had2 = _brute_had_k(adj, n, 2)
    had3 = _brute_had_k(adj, n, 3)
    assert had2 == 4
    assert had3 == 5
    assert had2 < had3          # the size-3 branch set is load-bearing

    triples, _conflicts = enumerate_had3(adj, n)
    # the forcing branch set of the had_3 = 5 witness family is {0,5,6}
    assert (0, 5, 6) in set(triples)


def test_size3_forced_checksum_independent_recompute():
    """The forced instance's counts also match an in-test degree/codegree
    recompute — a second independent witness of the checksum semantics."""
    adj = _forced()
    n = 7
    deg = [len(adj[v]) for v in range(n)]
    ntri = comb(n, 3) - sum(comb(d, 2) for d in deg)
    nts = sum(comb(d, 3) for d in deg)
    ntp = sum(comb(len(adj[u] & adj[w]), 3)
              for u in range(n) for w in range(u + 1, n))
    triples, conflicts = enumerate_had3(adj, n)
    assert (len(triples), len(conflicts)) == (ntri, nts + ntp) == (19, 6)
