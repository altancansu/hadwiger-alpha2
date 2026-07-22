"""The program's TRUST ROOT: an independent, stdlib-only certificate verifier.

Everything downstream (schema, store, corpus, CI) rests on this one module. It
consumes a stored certificate record (a plain JSON dict) and RAISES
`VerificationError` on any structural or semantic violation.

Trust-boundary discipline (VRF-01):
  * stdlib ONLY (json, hashlib, collections) — imports NOTHING from
    generators / search / verify / invariants / solver, and no third-party
    graph library.
  * carries its OWN private `_is_conflict` (byte-identical LOGIC to Appendix C.1,
    a private copy, never an import) so it shares no code path with any proposer.
  * rebuilds H's adjacency from the STORED `H_edges` — it never trusts a live
    adjacency object handed in by the toolkit.
  * every check is `if not cond: raise VerificationError(...)` with no
    optimization-stripped statements, so it is correct under `python -O`.

Reimplemented from the CONTRACT (Appendix C.1 semantics + Appendix E §4.6), NOT
by re-deriving the reference `verify/model.py` (that module stays byte-verbatim as
the Phase-1 reproduction anchor).

(Docstring prose deliberately avoids the trigger tokens the Phase-1 grep-based
guards scan for — the AST isolation guard is the real mechanism check.)
"""
import hashlib
import json
from collections import deque


class VerificationError(Exception):
    """Raised on any structural or semantic certificate violation."""


def _is_conflict(A, B, adj):
    """True iff branch sets A,B are NON-adjacent in G.

    Non-adjacent in G <=> every cross pair {x in A, y in B} is an H-edge
    (y in adj[x]). Private byte-identical-logic copy of Appendix C.1 is_conflict;
    imported from nowhere.
    """
    for x in A:
        ax = adj[x]
        for y in B:
            if y not in ax:
                return False
    return True


def _build_adj(H_edges, n):
    """Rebuild a fresh list[set] adjacency from the STORED H_edges.

    Raises on malformed (len != 2), non-canonical (not 0 <= u < v < n), or
    duplicate edges.
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


def verify_model_record(rec):
    """Verify a stored K_k branch-set model record. Returns k (= had_2 demonstrated).

    Contract (Appendix E §4.6, hardened to raises):
      1. n, chi are ints >= 1.
      2. recomputed canonical H_edges sha256 == stored H_edges_sha256.
      3. k = len(model_branch_sets); k >= chi.
      4. each branch set size in {1,2,3}; vertices in [0,n); globally disjoint.
      5. each size-2 set {a,b} is a G-edge (b not in adj[a], i.e. NOT an H-edge);
         each size-3 set {a,b,c} is CONNECTED in G, i.e. >=2 of its 3 internal
         pairs are G-edges (<=1 internal H-edge). (For 3 vertices, connected in G
         <=> >=2 internal G-edges.)
      6. every i<j pair of branch sets is adjacent in G (not _is_conflict) —
         i.e. all C(k,2) cross-adjacencies present.
    """
    inv = rec["invariants"]
    n = inv["n"]
    chi = inv["chi_G"]
    if not (isinstance(n, int) and isinstance(chi, int) and n >= 1 and chi >= 1):
        raise VerificationError(f"bad n/chi (n={n!r}, chi={chi!r})")

    # (2) integrity: canonical H_edges sha256 must match the stored value.
    edges = sorted([min(a, b), max(a, b)] for a, b in rec["H_edges"])
    canon = json.dumps(edges, separators=(",", ":"))
    if hashlib.sha256(canon.encode()).hexdigest() != rec["H_edges_sha256"]:
        raise VerificationError("H_edges_sha256 mismatch")

    adj = _build_adj(rec["H_edges"], n)

    sets = [tuple(s) for s in rec["model_branch_sets"]]
    k = len(sets)
    if k < chi:
        raise VerificationError(f"family size {k} < chi {chi}")

    used = set()
    for S in sets:
        if len(S) not in (1, 2, 3):
            raise VerificationError(f"branch set size {len(S)} not in (1,2,3): {S!r}")
        for v in S:
            if not (isinstance(v, int) and 0 <= v < n):
                raise VerificationError(f"vertex {v!r} out of range [0,{n})")
            if v in used:
                raise VerificationError(f"branch sets not disjoint at vertex {v}")
            used.add(v)
        if len(S) == 2:
            a, b = S
            if b in adj[a]:
                raise VerificationError(f"pair {S!r} is an H-edge, not a G-edge")
        if len(S) == 3:
            a, b, c = S
            g_edges = (b not in adj[a]) + (c not in adj[a]) + (c not in adj[b])
            if g_edges < 2:
                raise VerificationError(
                    f"triple {S!r} disconnected in G ({g_edges} G-edges < 2)"
                )

    for i in range(k):
        for j in range(i + 1, k):
            if _is_conflict(sets[i], sets[j], adj):
                raise VerificationError(f"branch sets {i},{j} not adjacent in G")

    return k


def verify_chi_witness(rec):
    """Verify chi = n - nu is pinned in BOTH directions from stored M + U (CHI-02).

    Tutte-Berge: nu = (1/2) min_U (n - odd_components(H-U) + |U|). For ANY U this
    gives nu <= (n - c_odd(H-U) + |U|)/2 (upper bound); a matching M gives
    nu >= |M| (lower bound). When they meet, nu — hence chi = n - nu — is pinned
    without trusting the matching library or formalizing Edmonds.

    GENERAL path: U is read and removed, never assumed empty. Stdlib-only.
    """
    # WR-06: fail closed (VerificationError, not KeyError) on missing structure.
    if "invariants" not in rec:
        raise VerificationError("record missing invariants")
    inv = rec["invariants"]
    n = inv.get("n")
    nu = inv.get("nu_H")
    chi = inv.get("chi_G")
    # WR-01: validate types BEFORE arithmetic, mirroring verify_model_record. A
    # non-int (e.g. nu_H: null) would otherwise raise a bare TypeError that callers
    # doing `except VerificationError` never catch.
    if not (isinstance(n, int) and isinstance(nu, int) and isinstance(chi, int)):
        raise VerificationError(f"bad n/nu/chi types (n={n!r}, nu={nu!r}, chi={chi!r})")
    if n - nu != chi:
        raise VerificationError(f"chi {chi} != n - nu ({n} - {nu} = {n - nu})")

    if "H_edges" not in rec:
        raise VerificationError("record missing H_edges")
    adj = _build_adj(rec["H_edges"], n)

    # M is a valid matching in H with |M| == nu  =>  nu >= |M|.
    if "matching_M" not in rec:
        raise VerificationError("record missing matching_M")
    M = [tuple(e) for e in rec["matching_M"]]
    covered = set()
    for e in M:
        if len(e) != 2:
            raise VerificationError(f"malformed M edge {e!r}")
        a, b = e
        # CR-01: range-check BEFORE indexing adj. adj is a plain list, so a
        # negative a/b silently wraps (adj[-1] == adj[n-1]) and would let a forged
        # matching alias one vertex under two labels, slipping past `covered` and
        # inflating |M| (hence nu, hence chi). Same 0 <= v < n discipline used for
        # H_edges and tutte_berge_U.
        if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < n and 0 <= b < n):
            raise VerificationError(f"M edge {(a, b)!r} vertex out of range [0,{n})")
        if b not in adj[a]:
            raise VerificationError(f"M edge {(a, b)} is not an H-edge")
        if a in covered or b in covered:
            raise VerificationError(f"M is not a matching (repeat at {(a, b)})")
        covered.add(a)
        covered.add(b)
    if len(M) != nu:
        raise VerificationError(f"|M| = {len(M)} != nu = {nu}")

    # Count odd-order connected components of H - U by stdlib BFS.
    if "tutte_berge_U" not in rec:
        raise VerificationError("record missing tutte_berge_U")
    U = set(rec["tutte_berge_U"])
    for v in U:
        if not (isinstance(v, int) and 0 <= v < n):
            raise VerificationError(f"witness vertex {v!r} out of range [0,{n})")
    keepset = set(range(n)) - U
    seen = set()
    c_odd = 0
    for start in keepset:
        if start in seen:
            continue
        seen.add(start)
        size = 0
        dq = deque([start])
        while dq:
            x = dq.popleft()
            size += 1
            for w in adj[x]:
                if w in keepset and w not in seen:
                    seen.add(w)
                    dq.append(w)
        if size % 2 == 1:
            c_odd += 1

    tot = n - c_odd + len(U)
    if tot % 2 != 0 or tot // 2 != nu:
        raise VerificationError(
            f"Tutte-Berge upper bound (n - c_odd + |U|)/2 = {tot / 2} != nu = {nu}"
        )
    return True


def verify_certificate(rec):
    """The single combined trust entry point: verify a FULL certificate record.

    A record is a valid certificate ONLY if it passes BOTH legs:
      * verify_model_record — the K_k branch-set model exists with k >= chi_G;
      * verify_chi_witness  — chi_G = n - nu is independently pinned in BOTH
        directions by the stored Tutte-Berge witness (M + U).

    verify_model_record's `k >= chi` gate is only sound because chi_G is pinned by
    verify_chi_witness; called alone it would trust an attacker-chosen chi_G. All
    production call sites (current and future) MUST route through this function and
    never treat verify_model_record's return value alone as a complete proof. The
    two individual functions remain available for fine-grained tests.

    Returns k (= demonstrated had_2). Raises VerificationError on any violation.
    """
    k = verify_model_record(rec)
    verify_chi_witness(rec)
    return k
