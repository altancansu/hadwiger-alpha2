#!/usr/bin/env python3
"""Bohman triangle-free process + triangle-free/edge-maximal checks.

Verbatim port of the generation core from Appendix C.1 (hadwiger_tfp.py). Bodies
are byte-identical to the reference source; only the module location changed.

Determinism note: byte-reproduction depends on CPython set-iteration order, which
depends on the exact code here. Do NOT reformat, reorder comprehensions, merge/split
loops, or alter the RandomSet swap-with-last layout. Do NOT run `ruff --fix`/format
on this module (it is excluded in pyproject.toml).
"""

# ---------- random-access set for the process ----------
class RandomSet:
    __slots__ = ("items", "pos")
    def __init__(self, iterable=()):
        self.items = []; self.pos = {}
        for x in iterable: self.add(x)
    def add(self, x):
        if x in self.pos: return
        self.pos[x] = len(self.items); self.items.append(x)
    def discard(self, x):
        i = self.pos.pop(x, None)
        if i is None: return
        last = self.items.pop()
        if i < len(self.items):
            self.items[i] = last; self.pos[last] = i
    def random(self, rng):
        return self.items[rng.randrange(len(self.items))]
    def __len__(self): return len(self.items)

# ---------- Bohman's triangle-free process ----------
def triangle_free_process(n, rng):
    adj = [set() for _ in range(n)]
    open_pairs = RandomSet((i, j) for i in range(n) for j in range(i + 1, n))
    m = 0
    while len(open_pairs):
        u, v = open_pairs.random(rng)
        open_pairs.discard((u, v))
        adj[u].add(v); adj[v].add(u); m += 1
        for w in adj[v]:
            if w != u:
                open_pairs.discard((u, w) if u < w else (w, u))
        for w in adj[u]:
            if w != v:
                open_pairs.discard((v, w) if v < w else (w, v))
    return adj, m

def is_triangle_free(adj, n):
    for u in range(n):
        for v in adj[u]:
            if v > u and adj[u] & adj[v]:
                return False
    return True

def is_edge_maximal_tf(adj, n):
    # every non-edge closes a triangle  <=>  H has diameter 2 (for connected H)
    for u in range(n):
        for v in range(u + 1, n):
            if v not in adj[u] and not (adj[u] & adj[v]):
                return False
    return True
