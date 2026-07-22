"""had_3 (size-3 branch-set) obstruction model data (EXACT-05) — pure,
backend-neutral, stdlib ONLY.

The size-3 escalation adds triple branch sets to the had_2 model (`had2.py`,
reused unchanged). It is the ONE genuinely-new piece of combinatorics in
Phase 5, and unlike the had_2 edge/cherry/C4 conflicts, size-3 conflicts are
NOT a clean local substructure of H (RESEARCH Pitfall 3) — so this module is
the FIRST of three independent guards (the checksum here, the trust-root
verifier, and the CBC-vs-CP-SAT had_3 differential).

Built straight from H's structure (H triangle-free, G = complement(H)):

  * TRIPLE INDEX = the size-3 connectivity constraint, enforced BY the
    indexing (the direct analog of had2's "pair vars exist ONLY for G-edges").
    A triple {a,b,c} is a legal branch set iff it induces a CONNECTED subgraph
    of G, i.e. >=2 of the 3 internal pairs are G-edges <=> <=1 pair is an
    H-edge (3 vertices are connected iff >=2 edges present). Widening the index
    to all triples would silently admit disconnected "branch sets".
  * CONFLICTS = triple-vs-set non-adjacency in G, enumerated from each triple's
    common H-neighborhood W(T) = N_H(a) & N_H(b) & N_H(c). A triple T conflicts
    with a set S iff EVERY cross pair is an H-edge (T and S non-adjacent in G)
    <=> every vertex of S lies in W(T). Scope (seagull / Tier-1): S ranges over
    singletons and G-edge pairs drawn from W(T) — never an all-pairs scan.
    Triangle-freeness makes W total: any two vertices in W(T) share a common
    H-neighbor (each vertex of T), so they cannot be H-adjacent, hence every
    pair within W(T) is automatically a G-edge. A triple with EXACTLY one
    internal H-edge (a seagull/path in G) has W(T) empty — a common H-neighbor
    would close that H-edge into a triangle — so only 0-H-edge (G-triangle)
    triples carry conflicts.

EVERY model build passes the raise-based STRUCTURAL CHECKSUM gate: the counts
are recomputed INDEPENDENTLY from H's degrees/codegrees and any mismatch raises
ChecksumError (the same ChecksumError had2.py uses):

  * n_triples  = C(n,3) - sum_v C(deg(v), 2)
        (triples with >=2 H-edges have a unique H-cherry center v, counted by
         sum_v C(deg,2); triangle-free H has no 3-H-edge triple);
  * n_triple_single = sum_v C(deg(v), 3)
        (a (T, {v}) conflict <=> {a,b,c} is a 3-subset of N_H(v));
  * n_triple_pair   = sum_{u<w} C(codeg(u,w), 3)
        (a (T, {u,w}) conflict <=> {a,b,c} is a 3-subset of N_H(u) & N_H(w));
  * n_conflicts = n_triple_single + n_triple_pair.

This module imports NO solver library — Phase 5's CBC and CP-SAT backends
translate the same Had3Problem object.
"""
from dataclasses import dataclass
from math import comb

from alpha2.generators.tfp import is_triangle_free
from alpha2.solvers.problems.had2 import ChecksumError

__all__ = ["ChecksumError", "Had3Problem", "enumerate_had3", "build_had3_problem"]


@dataclass(frozen=True)
class Had3Problem:
    """Plain size-3 model data (backend-neutral): triple index + conflict sets.

    triples   — the triple-variable index: sorted (a, b, c) with a < b < c and
                <=1 internal H-edge (>=2 internal G-edges = connected in G);
    conflicts — triple-vs-set non-adjacency conflicts as (T, S) with
                T = (a, b, c) and S = (v,) (triple-single) or (u, w) with u < w
                (triple-pair); each S drawn from the common H-neighborhood W(T).
    """

    n: int
    triples: list
    conflicts: set


def enumerate_had3(adj, n):
    """Enumerate the triple index + size-3 conflicts from H. Returns (triples, conflicts).

    triples: every {a,b,c} with <=1 internal H-edge (connectivity by indexing).
    conflicts: for each triple T, the singletons and G-edge pairs drawn from the
    common H-neighborhood W(T) = N_H(a) & N_H(b) & N_H(c) (each such S is
    non-adjacent in G to T). Every conflict is discovered exactly once from its
    unique triple, so a plain set cannot double-count.
    """
    triples = [
        (a, b, c)
        for a in range(n) for b in range(a + 1, n) for c in range(b + 1, n)
        if ((b in adj[a]) + (c in adj[a]) + (c in adj[b])) <= 1
    ]
    conflicts = set()
    for (a, b, c) in triples:
        W = sorted(adj[a] & adj[b] & adj[c])     # common H-neighborhood of T
        T = (a, b, c)
        for v in W:                              # triple-single (singleton in W)
            conflicts.add((T, (v,)))
        for i in range(len(W)):                  # triple-pair (G-edge pair in W)
            for j in range(i + 1, len(W)):
                conflicts.add((T, (W[i], W[j])))  # W[i]W[j] is a G-edge (see docstring)
    return triples, conflicts


def build_had3_problem(adj, n):
    """Enumerate + checksum-gate a Had3Problem for triangle-free H. Raises on defect.

    Raises ValueError if H is not triangle-free (the enumeration is only total
    on triangle-free H — a common H-neighbor of a triple would otherwise not
    force a G-edge) and ChecksumError if the (triples, conflicts) counts
    disagree with the independent recomputation from H's degrees/codegrees.
    """
    if not is_triangle_free(adj, n):
        raise ValueError(
            "H must be triangle-free: the size-3 obstruction enumeration is "
            "only total on triangle-free H"
        )
    triples, conflicts = enumerate_had3(adj, n)

    deg = [len(adj[v]) for v in range(n)]
    ntriples_expect = comb(n, 3) - sum(comb(d, 2) for d in deg)
    nts_expect = sum(comb(d, 3) for d in deg)                       # triple-single
    ntp_expect = sum(                                              # triple-pair
        comb(len(adj[u] & adj[w]), 3)
        for u in range(n) for w in range(u + 1, n))
    nconf_expect = nts_expect + ntp_expect
    if (len(triples), len(conflicts)) != (ntriples_expect, nconf_expect):
        raise ChecksumError(
            f"size-3 counts {(len(triples), len(conflicts))} "
            f"!= H-structure {(ntriples_expect, nconf_expect)}"
        )
    return Had3Problem(n=n, triples=triples, conflicts=conflicts)
