"""The CDM TRUSTED REFERENCE: a stdlib-only, solver-free exhaustive decider.

`has_cdm(adj, n)` decides whether a graph G with alpha(G)=2 has a non-empty
**connected dominating matching** (CDM, Costa-Luu-Wood-Yip arXiv:2512.17114,
Conjecture 10) and, when it does, returns a hand-checkable witness M. It is the
ARBITER the CP-SAT cross-check (`pool/cdm/cpsat.py`) is measured against: a
disagreement between the two is release-blocking, and any CDM-FAIL (impossibility,
radioactive) is trusted only when THIS exhaustive DFS agrees.

Trust-leg discipline (mirrors `corpus/verifier.py`, VRF-01):
  * stdlib ONLY — imports NOTHING (no networkx, no ortools, no proposer module,
    not even the sibling `cpsat`); it carries its OWN private copies of the two
    CDM definition helpers (`vsets_adjacent`, `dominates`), the way the trust
    root carries its private `_is_conflict`, so it shares no code path with any
    engine it is meant to check.
  * every check is a plain `if` branch, raises-only, with NO debug-check
    statements anywhere, so the decision procedure is correct under `python -O`
    (an optimization-stripped check must never be able to weaken the arbiter).

Definitions (adj = list[set[int]], adj[u] = neighbours of u in G):
  * matching M — pairwise vertex-disjoint edges; V(M) = the covered vertices.
  * connected — for every two edges e,f in M, V(e) and V(f) are adjacent in G
    (>=1 of the four cross vertex-pairs is a G-edge). For disjoint edges this is
    exactly "the two size-2 branch sets are adjacent" (a K_|M| size-2 minor).
  * dominating — every vertex w not in V(M) is adjacent to EACH edge e of M,
    where "w adjacent to edge e={a,b}" means w adjacent to >=1 endpoint (the A1
    reading, LOCKED; validated by reproducing CLWY's n<=11 all-CDM result).

Search (the "grow to cover an undominated vertex" formulation — self-pruning and
terminating): seed over every G-edge, then extend M only by an edge that (i)
covers a currently-undominated vertex, (ii) keeps M a matching, and (iii) is
pairwise V-adjacent to every current M-edge (keeps M connected). Completeness:
an undominated vertex w is not adjacent to some FIXED edge already in M, so no
future edge can dominate w -- w must be MATCHED; hence forcing candidates to
cover w discards no valid completion. Termination: every step covers a new
vertex, so depth <= n // 2.
"""


def has_cdm(adj, n):
    """Return a witness matching M (list of ``(a, b)`` edges, ``a < b``) if G has
    a non-empty connected dominating matching, else ``None``.

    Exhaustive and trusted: the reference the CP-SAT model is checked against.
    """
    G_edges = [(a, b) for a in range(n) for b in sorted(adj[a]) if a < b]

    def vsets_adjacent(e, f):
        """True iff the disjoint edges e, f have V-adjacent endpoint sets in G."""
        a, b = e
        c, d = f
        return c in adj[a] or d in adj[a] or c in adj[b] or d in adj[b]

    def dominates(M, cover):
        """True iff every vertex outside V(M) is adjacent to each edge of M."""
        for w in range(n):
            if w in cover:
                continue
            for (a, b) in M:
                if w not in adj[a] and w not in adj[b]:
                    return False
        return True

    def first_undominated(M, cover):
        """The lowest vertex outside V(M) not adjacent to some edge of M, or None."""
        for w in range(n):
            if w in cover:
                continue
            for (a, b) in M:
                if w not in adj[a] and w not in adj[b]:
                    return w
        return None

    def dfs(M, cover):
        if M and dominates(M, cover):
            return list(M)
        if not M:
            # Seed step: a non-empty connected matching may start at any edge.
            candidates = G_edges
        else:
            target = first_undominated(M, cover)
            if target is None:
                # M is non-empty but already dominates -> handled above; a None
                # target with a non-empty M cannot reach here, but stay total.
                return None
            candidates = [
                (a, b)
                for (a, b) in G_edges
                if (a == target or b == target)          # must cover the target
                and a not in cover and b not in cover     # keep M a matching
                and all(vsets_adjacent((a, b), e) for e in M)  # keep M connected
            ]
        for (a, b) in candidates:
            r = dfs(M + [(a, b)], cover | {a, b})
            if r is not None:
                return r
        return None

    return dfs([], set())
