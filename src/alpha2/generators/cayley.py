#!/usr/bin/env python3
"""Maximal symmetric sum-free subsets of Z_p + Cayley adjacency (generator).

Verbatim port of the generation core from Appendix C.3 (cayley_test.py). Bodies
are byte-identical to the reference source; only the module location changed.

Determinism note: byte-reproduction depends on CPython set-iteration order AND
rng.shuffle order. Do NOT reformat, reorder comprehensions, merge/split loops, or
alter loop layout. Do NOT run `ruff --fix`/format on this module (it is excluded in
pyproject.toml).

`rng` is injected, never a global — `random_maximal_symmetric_sumfree(p, rng)`
consumes the caller's stream via `rng.shuffle(elems)`; never seed inside the module.
The exact ILP fallback from C.3 is intentionally NOT ported — Phase 3 is
solver-free; all 12 Cayley instances resolve heuristically.
"""

# ---- maximal symmetric sum-free subsets of Z_p ----
def can_add(S, p, a):
    b = (-a) % p
    T = S | {a, b}
    for u in (a, b):
        for x in T:
            if (u + x) % p in T:  # u + x = z violation
                return False
            if (u - x) % p in T:  # x + (u-x) = u violation
                return False
    return True

def random_maximal_symmetric_sumfree(p, rng):
    S = set(); elems = list(range(1, p))
    changed = True
    while changed:
        changed = False
        rng.shuffle(elems)
        for a in elems:
            if a in S: continue
            if can_add(S, p, a):
                S.add(a); S.add((-a) % p); changed = True
    return S

def cayley_adj(p, S):
    adj = [set() for _ in range(p)]
    for u in range(p):
        for s in S:
            adj[u].add((u + s) % p)
    return adj
