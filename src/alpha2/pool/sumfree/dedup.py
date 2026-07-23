"""Canonical-certificate dedup over merged (Γ, S) streams (POOL-2, Wave 2 GREEN).

Structured + random generators over many Γ WILL produce isomorphic Cayley graphs H
from distinct (Γ, S) descriptors. Unlike Phase-7's single already-isomorph-free geng
stream, these MERGED streams require dedup. The key is a nauty CANONICAL certificate
(`pynauty.certificate`) — ONE convention per key set (Pitfall 5). The non-canonical
networkx graph hash is FORBIDDEN as a dedup key (CLAUDE.md "What NOT to Use": it is
not canonical, and its silent collisions violate the exactness discipline).

On an isomorphic collision the FIRST descriptor is KEPT as provenance and the
collapsed duplicates are recorded on the class (a structured-vs-random collision — a
structured S and a random S yielding the same H — is itself a datapoint and is logged
under `duplicates`, never silently dropped).
"""
from pynauty import Graph as _NautyGraph
from pynauty import certificate as _certificate

from alpha2.pool.sumfree.generate import adjacency_from_descriptor


def canonical_key(adj_H, n):
    """The nauty canonical certificate of H (the single dedup convention).

    `pynauty.certificate` is a canonical form: isomorphic graphs share it, and
    (unlike a WL-hash) non-isomorphic graphs never collide. Returns the certificate
    bytes, used directly as a dict key.
    """
    adjacency_dict = {u: sorted(adj_H[u]) for u in range(n)}
    g = _NautyGraph(n, directed=False, adjacency_dict=adjacency_dict)
    return _certificate(g)


def dedup(descriptors):
    """Collapse isomorphic (Γ, S) descriptors to one canonical class each.

    Returns a list of class dicts, one per canonical certificate, in first-seen
    order. Each class is
        {"representative": <first descriptor>, "duplicates": [<later ...>], "key": <cert>}
    — the FIRST descriptor per class is the kept provenance; every later descriptor
    whose H is isomorphic is recorded under `duplicates` (never dropped).
    """
    classes = []
    by_key = {}
    for d in descriptors:
        adj = adjacency_from_descriptor(d)
        key = canonical_key(adj, len(adj))
        if key in by_key:
            by_key[key]["duplicates"].append(d)
        else:
            entry = {"representative": d, "duplicates": [], "key": key}
            by_key[key] = entry
            classes.append(entry)
    return classes
