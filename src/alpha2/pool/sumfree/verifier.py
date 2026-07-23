"""The g(G)-screen TRUST LEG: an independent, stdlib-only certificate verifier.

`verify_gscreen_record(record)` consumes a stored g(G)-screen certificate (a plain
JSON dict) and RAISES `VerificationError` on any structural or semantic violation,
returning a truthy summary on success. It is a NEW, independent leg — it re-derives
everything from stored data and trusts no emission artifact:

  * rebuilds H's adjacency from the STORED `H_edges`, then G = complement(H); it
    never trusts a live adjacency object handed in by the toolkit;
  * re-derives nu(H) via its OWN stdlib maximum-matching leg (a self-contained
    Edmonds blossom — imports NOTHING from generators/solvers/graph libs) and
    re-checks chi = n - nu(H) against the stored `chi`;
  * re-derives the screen gap g = (chi - had_k)/chi and re-checks the stored `g`;
  * for a g<=0 KILLED record, re-verifies the stored K_chi `model_branch_sets` is a
    valid minor model of size >= chi (branch sets of size <=3, each connected in G,
    pairwise cross-adjacent, disjoint) — the sound Hadwiger-holds direction;
  * for a g>0 SHC_CANDIDATE, re-checks had_3 < chi is internally consistent;
  * enforces the honesty gate in the TRUST ROOT: `certificate_statement` may contain
    NEITHER "counterexample" NOR "had(G) <" (RESEARCH Pitfall 1);
  * every check is `if not cond: raise VerificationError(...)` — raises-only, ZERO
    `assert`, so a stripped `python -O` run STILL fails closed (a debug check must
    never be able to rubber-stamp a bad record).

Trust-boundary discipline (mirrors `pool/cdm/verifier.py`, VRF-01): stdlib ONLY
(json, hashlib). The n is re-derived from the descriptor's `invariant_factors`
(the true |Gamma|) — NOT from `provenance.n`, which the store's records mark a
placeholder the verifier must re-derive.
"""
import hashlib
import json

# The two radioactive substrings a g(G) record may NEVER contain (Pitfall 1). Kept a
# private literal here (not imported) so the trust root shares no code path with the
# schema-side guard — the honesty gate is enforced independently in BOTH legs.
_RADIOACTIVE_LOWER = "counterexample"
_RADIOACTIVE_EXACT = "had(G) <"


class VerificationError(Exception):
    """Raised on any structural or semantic g(G)-screen certificate violation."""


def _n_from_provenance(record):
    """Re-derive n = |Gamma| from the descriptor's invariant_factors (their product).

    provenance.n is a documented placeholder in the store's records (the verifier
    re-derives from data), so n comes from the invariant factors — the true group
    order — never from the stored `n` field.
    """
    prov = record.get("provenance")
    if not isinstance(prov, dict):
        raise VerificationError("record missing descriptor provenance")
    factors = prov.get("invariant_factors")
    if not factors:
        raise VerificationError("provenance missing invariant_factors (cannot re-derive n)")
    n = 1
    for d in factors:
        if not (isinstance(d, int) and d >= 1):
            raise VerificationError(f"bad invariant factor {d!r}")
        n *= d
    return n


def _build_adj_H(H_edges, n):
    """Rebuild a fresh list[set] H-adjacency from the STORED H_edges.

    Raises on malformed (len != 2), non-canonical (not 0 <= u < v < n), or duplicate
    edges (CR-01 range-check BEFORE indexing, so a negative label cannot wrap and
    alias a vertex).
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


def _max_matching(adj, n):
    """Maximum-cardinality matching nu of a general graph (self-contained blossom).

    An independent stdlib Edmonds blossom (augmenting-path contraction) — imports
    nothing, so the chi = n - nu re-derivation shares no code path with the networkx
    blossom the toolkit uses. Returns |M| (nu).
    """
    match = [-1] * n
    p = [-1] * n
    base = list(range(n))
    used = [False] * n
    blossom = [False] * n

    def lca(a, b):
        seen = [False] * n
        while True:
            a = base[a]
            seen[a] = True
            if match[a] == -1:
                break
            a = p[match[a]]
        while True:
            b = base[b]
            if seen[b]:
                return b
            b = p[match[b]]

    def mark_path(v, b, child):
        while base[v] != b:
            blossom[base[v]] = True
            blossom[base[match[v]]] = True
            p[v] = child
            child = match[v]
            v = p[match[v]]

    def find_path(root):
        for i in range(n):
            used[i] = False
            p[i] = -1
            base[i] = i
        used[root] = True
        queue = [root]
        head = 0
        while head < len(queue):
            v = queue[head]
            head += 1
            for to in adj[v]:
                if base[v] == base[to] or match[v] == to:
                    continue
                if to == root or (match[to] != -1 and p[match[to]] != -1):
                    curbase = lca(v, to)
                    for i in range(n):
                        blossom[i] = False
                    mark_path(v, curbase, to)
                    mark_path(to, curbase, v)
                    for i in range(n):
                        if blossom[base[i]]:
                            base[i] = curbase
                            if not used[i]:
                                used[i] = True
                                queue.append(i)
                elif p[to] == -1:
                    p[to] = v
                    if match[to] == -1:
                        return to
                    used[match[to]] = True
                    queue.append(match[to])
        return -1

    for v in range(n):
        if match[v] == -1:
            u = find_path(v)
            while u != -1:
                pv = p[u]
                ppv = match[pv]
                match[u] = pv
                match[pv] = u
                u = ppv
    return sum(1 for v in range(n) if match[v] != -1) // 2


def _assert_honest(record):
    """RAISE VerificationError if certificate_statement carries a radioactive claim."""
    stmt = record.get("certificate_statement")
    if not isinstance(stmt, str):
        raise VerificationError("record missing certificate_statement")
    if _RADIOACTIVE_LOWER in stmt.lower():
        raise VerificationError(
            "radioactive certificate_statement: a g(G) record may never say "
            "'counterexample' (the screen is necessary-not-sufficient; Pitfall 1)"
        )
    if _RADIOACTIVE_EXACT in stmt:
        raise VerificationError(
            "radioactive certificate_statement: a g(G) record may never claim "
            "'had(G) < chi' (branch sets of size >=4 are not excluded; Pitfall 1)"
        )


def _connected_in_G(bset, adj_G):
    """True iff the vertices of `bset` induce a connected subgraph of G."""
    if len(bset) <= 1:
        return True
    members = set(bset)
    seen = {bset[0]}
    stack = [bset[0]]
    while stack:
        u = stack.pop()
        for w in adj_G[u]:
            if w in members and w not in seen:
                seen.add(w)
                stack.append(w)
    return seen == members


def _verify_branch_set_family(record, adj_G, n, chi):
    """Re-verify a KILLED record's K_chi minor model (the sound existence direction).

    RAISES unless `model_branch_sets` is a valid minor model of K_m with m >= chi:
    non-empty, each set size 1..3, all vertices canonical and pairwise-disjoint, each
    set connected in G, and every pair of sets cross-adjacent in G.
    """
    fam = record.get("model_branch_sets")
    if not fam:
        raise VerificationError(
            "KILLED / g<=0 record requires a non-empty model_branch_sets family"
        )
    if len(fam) < chi:
        raise VerificationError(
            f"branch-set family size {len(fam)} < chi {chi}: a K_chi minor needs >= chi "
            "pairwise-adjacent branch sets"
        )

    seen_vertices = set()
    sets = []
    for b in fam:
        if not b:
            raise VerificationError("empty branch set in model_branch_sets")
        if len(b) > 3:
            raise VerificationError(f"branch set {b!r} exceeds size 3 (had_3 bound)")
        for v in b:
            if not (isinstance(v, int) and 0 <= v < n):
                raise VerificationError(f"branch-set vertex {v!r} not in 0..{n - 1}")
            if v in seen_vertices:
                raise VerificationError(f"branch sets overlap at vertex {v}")
            seen_vertices.add(v)
        if not _connected_in_G(b, adj_G):
            raise VerificationError(f"branch set {b!r} is not connected in G")
        sets.append(set(b))

    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            if not any(w in adj_G[u] for u in sets[i] for w in sets[j]):
                raise VerificationError(
                    f"branch sets {sorted(sets[i])} and {sorted(sets[j])} are not "
                    "cross-adjacent in G (minor model incomplete)"
                )


def verify_gscreen_record(record):
    """Verify a stored g(G)-screen record. Returns a truthy summary dict on success.

    Raises VerificationError on any violation:
      1. structure present (provenance, H_edges, H_edges_sha256, chi, terminal_state).
      2. recomputed canonical H_edges sha256 == stored H_edges_sha256 (integrity).
      3. honesty gate: certificate_statement carries no radioactive substring.
      4. chi re-derived: chi == n - nu(H), n = |Gamma| from invariant_factors.
      5. g re-derived: stored g == (chi - had_k)/chi (None when had_k is None).
      6. terminal_state consistent with g (KILLED<=>g<=0, SHC_CANDIDATE<=>g>0,
         RESISTANT<=>g is None).
      7. for KILLED: model_branch_sets is a valid K_chi minor model (size <=3 sets).
      8. for SHC_CANDIDATE: had_3 < chi is internally consistent.
    """
    # WR-06: fail closed (VerificationError, not KeyError) on missing structure.
    for field in ("H_edges", "H_edges_sha256", "chi", "terminal_state"):
        if field not in record:
            raise VerificationError(f"record missing {field}")

    # (3) honesty gate FIRST — the trust root refuses a radioactive claim outright.
    _assert_honest(record)

    n = _n_from_provenance(record)

    # (2) integrity: canonical H_edges sha256 must match the stored value.
    edges = sorted([min(a, b), max(a, b)] for a, b in record["H_edges"])
    canon = json.dumps(edges, separators=(",", ":"))
    if hashlib.sha256(canon.encode()).hexdigest() != record["H_edges_sha256"]:
        raise VerificationError("H_edges_sha256 mismatch")

    adj_H = _build_adj_H(record["H_edges"], n)
    adj_G = _complement_adj(adj_H, n)

    # (4) chi re-derivation: chi = n - nu(H).
    chi = record["chi"]
    if not (isinstance(chi, int) and chi >= 1):
        raise VerificationError(f"bad chi (chi={chi!r})")
    nu = _max_matching(adj_H, n)
    if chi != n - nu:
        raise VerificationError(
            f"chi mismatch: stored chi={chi} but n - nu(H) = {n} - {nu} = {n - nu}"
        )

    had_2 = record.get("had_2")
    had_3 = record.get("had_3")
    had_k = had_3 if had_3 is not None else had_2

    # (5) g re-derivation.
    g = record.get("g")
    if had_k is None:
        if g is not None:
            raise VerificationError("g must be None when no exact bound (had_k) was proved")
    else:
        expected_g = (chi - had_k) / chi
        if g is None or abs(g - expected_g) > 1e-12:
            raise VerificationError(
                f"g mismatch: stored g={g!r} but (chi - had_k)/chi = {expected_g!r}"
            )

    # (6) terminal_state <-> g consistency.
    terminal = record["terminal_state"]
    if terminal == "RESISTANT":
        if g is not None:
            raise VerificationError("RESISTANT record must have g is None")
    elif terminal == "KILLED":
        if g is None or g > 0:
            raise VerificationError(f"KILLED record requires g <= 0, got g={g!r}")
        # (7) the sound existence direction: a valid K_chi minor model.
        _verify_branch_set_family(record, adj_G, n, chi)
    elif terminal == "SHC_CANDIDATE":
        if g is None or g <= 0:
            raise VerificationError(f"SHC_CANDIDATE record requires g > 0, got g={g!r}")
        # (8) had_3 < chi internal consistency (screen, NOT a break).
        if had_3 is None or not (had_3 < chi):
            raise VerificationError(
                f"SHC_CANDIDATE requires a proved had_3 < chi, got had_3={had_3!r}, chi={chi}"
            )
    else:
        raise VerificationError(f"unknown terminal_state {terminal!r}")

    return {"n": n, "nu_H": nu, "chi": chi, "g": g, "terminal_state": terminal}


# The store's verify-at-append gate links to this leg via the `verify_gscreen`
# name (plan key-link pattern); `verify_gscreen_record` is the canonical public name.
verify_gscreen = verify_gscreen_record
