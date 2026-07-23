"""The CDM existence TRUST LEG: an independent, stdlib-only witness verifier.

`verify_cdm_witness(record)` consumes a stored CDM certificate (a plain JSON dict)
and RAISES `VerificationError` on any structural or semantic violation, returning a
truthy value (|M|) on a valid witness. It is a NEW, independent leg — deliberately
NOT a reuse of the frozen model-record verifier (RESEARCH anti-pattern: a
connected dominating matching is not a K_chi branch-set family, and reusing the
model verifier would share a wrong reading across both legs).

Trust-boundary discipline (mirrors `corpus/verifier.py`, VRF-01):
  * stdlib ONLY (json, hashlib) — imports NOTHING from proposers / deciders /
    generators / solvers, and no third-party graph library. It carries its OWN
    private CDM definition helper (`_vsets_adjacent`), the way the trust root
    carries its private `_is_conflict`, so it shares no code path with the DFS
    reference or the CP-SAT engine it is meant to independently re-check.
  * rebuilds H's adjacency from the STORED `H_edges`, then G = complement(H) — it
    never trusts a live adjacency object handed in by the toolkit.
  * every check is `if not cond: raise VerificationError(...)`, raises-only with no
    debug-check statements anywhere, so it STILL fails closed under `python -O` (a
    stripped debug check must never be able to rubber-stamp a bad witness).

CDM record shape (from `pool/cdm/schema.build_cdm_record`): `H_edges` is the MTF
triangle-free graph H; `matching_M` is a matching of G-edges (G = complement(H));
`invariants` carries {n, complement_connected, cdm}. The witness is a CDM iff M is
non-empty, a matching, connected (every disjoint edge-pair V-adjacent in G), and
dominating (every uncovered vertex adjacent to >=1 endpoint of EACH M-edge — the
A1 reading, LOCKED).
"""
import hashlib
import json


class VerificationError(Exception):
    """Raised on any structural or semantic CDM certificate violation."""


def _build_adj(H_edges, n):
    """Rebuild a fresh list[set] H-adjacency from the STORED H_edges.

    Raises on malformed (len != 2), non-canonical (not 0 <= u < v < n), or
    duplicate edges. Byte-identical-discipline copy of the trust root's helper;
    imported from nowhere.
    """
    adj = [set() for _ in range(n)]
    seen = set()
    for e in H_edges:
        if len(e) != 2:
            raise VerificationError(f"malformed H_edge {e!r} (len != 2)")
        u, v = e
        if not (isinstance(u, int) and isinstance(v, int) and 0 <= u < v < n):
            raise VerificationError(f"non-canonical H_edge {e!r} (need 0 <= u < v < {n})")
        if (u, v) in seen:
            raise VerificationError(f"duplicate H_edge {e!r}")
        seen.add((u, v))
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _complement_adj(adj_H, n):
    """G = complement(H): adj_G[u] = every other vertex NOT adjacent to u in H."""
    adj_G = [set() for _ in range(n)]
    for u in range(n):
        au = adj_H[u]
        for v in range(n):
            if u != v and v not in au:
                adj_G[u].add(v)
    return adj_G


def _vsets_adjacent(e, f, adj_G):
    """True iff the disjoint edges e, f have V-adjacent endpoint sets in G.

    Private byte-identical-logic copy of the CDM 'connected' predicate; imported
    from nowhere so the verifier shares no code path with the DFS reference.
    """
    a, b = e
    c, d = f
    return c in adj_G[a] or d in adj_G[a] or c in adj_G[b] or d in adj_G[b]


def verify_cdm_witness(record):
    """Verify a stored CDM witness record. Returns |M| (>= 1) on success.

    Raises VerificationError on any violation:
      1. n is an int >= 1.
      2. recomputed canonical H_edges sha256 == stored H_edges_sha256 (integrity).
      3. M is non-empty.
      4. every M-edge (a,b) has 0 <= a < b < n (CR-01 range-check BEFORE indexing,
         so a negative label cannot wrap `adj[-1] == adj[n-1]` and alias a vertex).
      5. every M-edge is a G-edge, i.e. NOT an H-edge (b not in adj_H[a]).
      6. M is a matching (no repeated vertex).
      7. M is connected — every disjoint edge-pair is V-adjacent in G.
      8. M is dominating — every vertex outside V(M) is adjacent to >=1 endpoint of
         EACH M-edge (A1 reading).
    """
    # WR-06: fail closed (VerificationError, not KeyError) on missing structure.
    if "invariants" not in record:
        raise VerificationError("record missing invariants")
    inv = record["invariants"]
    n = inv.get("n")
    if not (isinstance(n, int) and n >= 1):
        raise VerificationError(f"bad n (n={n!r})")

    # (2) integrity: canonical H_edges sha256 must match the stored value.
    if "H_edges" not in record:
        raise VerificationError("record missing H_edges")
    if "H_edges_sha256" not in record:
        raise VerificationError("record missing H_edges_sha256")
    edges = sorted([min(a, b), max(a, b)] for a, b in record["H_edges"])
    canon = json.dumps(edges, separators=(",", ":"))
    if hashlib.sha256(canon.encode()).hexdigest() != record["H_edges_sha256"]:
        raise VerificationError("H_edges_sha256 mismatch")

    adj_H = _build_adj(record["H_edges"], n)
    adj_G = _complement_adj(adj_H, n)

    # (3)-(6) M: non-empty, canonical G-edges, a matching.
    if "matching_M" not in record:
        raise VerificationError("record missing matching_M")
    M = [tuple(e) for e in record["matching_M"]]
    if not M:
        raise VerificationError("empty matching M: a CDM must be non-empty")

    covered = set()
    for e in M:
        if len(e) != 2:
            raise VerificationError(f"malformed M edge {e!r} (len != 2)")
        a, b = e
        # CR-01: range-check (and canonical a < b) BEFORE indexing adj. adj is a
        # plain list, so a negative label silently wraps (adj[-1] == adj[n-1]) and
        # would let a forged matching alias one vertex under two labels.
        if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < b < n):
            raise VerificationError(f"M edge {(a, b)!r} not canonical 0 <= a < b < {n}")
        # (5) each M-pair must be a G-edge = NOT an H-edge.
        if b in adj_H[a]:
            raise VerificationError(f"M edge {(a, b)} is an H-edge, not a G-edge")
        # (6) matching: no shared vertex.
        if a in covered or b in covered:
            raise VerificationError(f"M is not a matching (repeat at {(a, b)})")
        covered.add(a)
        covered.add(b)

    # (7) connected: every disjoint edge-pair is V-adjacent in G.
    k = len(M)
    for i in range(k):
        for j in range(i + 1, k):
            if not _vsets_adjacent(M[i], M[j], adj_G):
                raise VerificationError(
                    f"M is not connected: edges {M[i]} and {M[j]} are V-non-adjacent in G"
                )

    # (8) dominating: every uncovered vertex adjacent to >=1 endpoint of EACH edge.
    for w in range(n):
        if w in covered:
            continue
        for (a, b) in M:
            if w not in adj_G[a] and w not in adj_G[b]:
                raise VerificationError(
                    f"M is not dominating: vertex {w} not adjacent to edge {(a, b)}"
                )

    return k
