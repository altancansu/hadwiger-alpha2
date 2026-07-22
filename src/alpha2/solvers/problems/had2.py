"""had_2 obstruction model data (EXACT-02) — pure, backend-neutral, stdlib ONLY.

Builds the variable/conflict sets of the had_2 model straight from H's
structure (H triangle-free, G = complement(H)):

  * pair variables exist ONLY for G-edges — that indexing IS the size-2
    connectivity constraint. Widening the variable index set (e.g. to all
    vertex pairs) would silently admit disconnected "branch sets"; the trust
    root independently rejects non-G-edge pairs, but the model must never
    propose them in the first place.
  * single-single conflicts = H-edges;
  * single-pair conflicts   = cherries (2-subsets of each N_H(v));
  * pair-pair conflicts     = C4 diagonals (2-subsets of N_H(a) & N_H(b) per
    G-edge {a, b}). Each C4 is discovered twice — once from each diagonal —
    and the frozenset set-membership dedups the double discovery; without it
    the pair-pair count doubles.

Triangle-freeness is what makes the enumeration total: every 2-subset of
N_H(v) is automatically a G-edge (else H has a triangle), and every C4 of H is
chordless so both diagonals are legal pair variables. The builder therefore
re-checks triangle-freeness (raise-based) before enumerating.

EVERY model build passes the raise-based STRUCTURAL CHECKSUM gate: the three
conflict-class counts are recomputed independently from H's degrees/codegrees
(nss = |E(H)|, nsp = sum C(deg, 2), npp = half sum C(codeg, 2)) and any
mismatch raises ChecksumError. This module never imports a solver library —
Phase 5's CP-SAT backend translates the same Had2Problem object.
"""
from dataclasses import dataclass

from alpha2.generators.tfp import is_triangle_free


class ChecksumError(Exception):
    """Raised when the conflict-class counts disagree with H's structure."""


@dataclass(frozen=True)
class Had2Problem:
    """Plain model data (backend-neutral): variable index + conflict sets.

    Gedges — the pair-variable index (ONLY G-edges; see module docstring);
    ss     — single-single conflicts (H-edges, canonical (u, v) with u < v);
    sp     — single-pair conflicts (v, (a, b)) with a < b;
    pp     — pair-pair conflicts as frozenset({e1, e2}) of two G-edges.
    """

    n: int
    Gedges: list
    ss: set
    sp: set
    pp: set


def enumerate_had2(adj, n):
    """Enumerate variables + conflicts from H-obstructions. Returns (Gedges, ss, sp, pp)."""
    Gedges = [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]
    ss = {(u, v) for u in range(n) for v in adj[u] if v > u}          # H-edges
    sp = set()
    for v in range(n):                                                # cherries at v
        nb = sorted(adj[v])
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                sp.add((v, (nb[i], nb[j])))    # {a,b} in N_H(v) => ab is a G-edge
    pp = set()
    for (a, b) in Gedges:                                             # C4 diagonals
        W = sorted(adj[a] & adj[b])            # common H-neighborhood of a G-edge
        for i in range(len(W)):
            for j in range(i + 1, len(W)):
                c, d = W[i], W[j]              # cd is a G-edge (C4 of H is chordless)
                if len({a, b, c, d}) == 4:
                    pp.add(frozenset(((a, b), (c, d))))  # dedups the double discovery
    return Gedges, ss, sp, pp


def build_had2_problem(adj, n):
    """Enumerate + checksum-gate a Had2Problem for triangle-free H. Raises on defect.

    Raises ValueError if H is not triangle-free (the enumeration is only total
    on triangle-free H) and ChecksumError if any conflict-class count disagrees
    with the independent recomputation from H's degrees/codegrees.
    """
    if not is_triangle_free(adj, n):
        raise ValueError(
            "H must be triangle-free: the obstruction enumeration is only "
            "total on triangle-free H"
        )
    Gedges, ss, sp, pp = enumerate_had2(adj, n)

    deg = [len(adj[v]) for v in range(n)]
    nss_expect = sum(deg) // 2
    nsp_expect = sum(d * (d - 1) // 2 for d in deg)
    npp_expect = sum(
        (c := len(adj[u] & adj[v])) * (c - 1) // 2
        for u in range(n) for v in range(u + 1, n)) // 2
    if (len(ss), len(sp), len(pp)) != (nss_expect, nsp_expect, npp_expect):
        raise ChecksumError(
            f"conflict-class counts {(len(ss), len(sp), len(pp))} "
            f"!= H-structure {(nss_expect, nsp_expect, npp_expect)}"
        )
    return Had2Problem(n=n, Gedges=Gedges, ss=ss, sp=sp, pp=pp)
