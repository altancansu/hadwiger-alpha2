"""Profile heuristic for K_chi models (branch sets of size <= 2).

Verbatim port of the search cluster from Appendix C.1. Bodies are byte-identical
to the reference source; only the module location changed. Output is an UNTRUSTED
proposal that the independent verifier (verify/model.py) must rule on.

Determinism note: `pr = tuple(conf)[rng.randrange(len(conf))]` iterates a set of
int-tuples and MUST be preserved character-for-character. Do NOT reformat this
module or run `ruff --fix`/format on it (excluded in pyproject.toml).
"""
import time, itertools

# ---------- model search: branch sets of size <= 2 ----------
# Branch sets: pairs must be G-edges (i.e. NOT H-edges); two branch sets are
# adjacent iff SOME cross pair is a G-edge, i.e. NOT all cross pairs in H.

def is_conflict(A, B, adj):
    """True iff branch sets A,B are NON-adjacent in G (all cross pairs are H-edges)."""
    for x in A:
        ax = adj[x]
        for y in B:
            if y not in ax:
                return False
    return True

def full_conflicts(sets, adj):
    C = set()
    K = len(sets)
    for i in range(K):
        Si = sets[i]
        for j in range(i + 1, K):
            if is_conflict(Si, sets[j], adj):
                C.add((i, j))
    return C

def update_conflicts(conf, sets, changed, adj):
    ch = set(changed)
    conf2 = {pr for pr in conf if pr[0] not in ch and pr[1] not in ch}
    K = len(sets)
    for x in ch:
        Sx = sets[x]
        for y in range(K):
            if y == x: continue
            if y in ch and y < x: continue
            if is_conflict(Sx, sets[y], adj):
                conf2.add((min(x, y), max(x, y)))
    return conf2

def initial_state(adj, n, p, s, rng, tries=500):
    for _ in range(tries):
        verts = list(range(n)); rng.shuffle(verts)
        singles = verts[:s]; pool = verts[s:]
        pairs = []; fail = False
        while pool:
            a = pool.pop()
            idx = -1
            for i in range(len(pool)):
                if pool[i] not in adj[a]:
                    idx = i; break
            if idx < 0:
                fail = True; break
            b = pool.pop(idx); pairs.append((a, b))
        if not fail and len(pairs) == p:
            sets = [(v,) for v in singles] + [tuple(pr) for pr in pairs]
            rng.shuffle(sets)
            return sets
    return None

def initial_state_profile(adj, n, p, s, rng, tries=500):
    # Profile-general initial state: p pairs + s singletons using 2*p + s <= n
    # vertices, leaving n - 2*p - s UNUSED (the seed-137 non-spanning fix, SRCH-01).
    # Unlike initial_state, this does NOT pair the entire pool: it stops at p pairs
    # and drops an unpairable vertex (leaving it unused) rather than failing the try,
    # so it can represent the D.3 optimum (9 pairs + 7 singletons = 25 of 31 verts).
    for _ in range(tries):
        verts = list(range(n)); rng.shuffle(verts)
        singles = verts[:s]; pool = verts[s:]
        pairs = []
        while pool and len(pairs) < p:
            a = pool.pop()
            idx = -1
            for i in range(len(pool)):
                if pool[i] not in adj[a]:
                    idx = i; break
            if idx < 0:
                continue
            b = pool.pop(idx); pairs.append((a, b))
        if len(pairs) == p:
            sets = [(v,) for v in singles] + [tuple(pr) for pr in pairs]
            rng.shuffle(sets)
            return sets
    return None

def assignments(verts, sizes):
    if not sizes:
        yield (); return
    k0 = sizes[0]
    for grp in itertools.combinations(verts, k0):
        gs = set(grp)
        rest = tuple(v for v in verts if v not in gs)
        for tail in assignments(rest, sizes[1:]):
            yield (grp,) + tail

def valid_groups(cand, adj):
    for g in cand:
        if len(g) == 2 and g[1] in adj[g[0]]:
            return False
    return True

def cand_energy(sets, idxs, cand, adj):
    e = 0
    for a in range(len(cand)):
        for b in range(a + 1, len(cand)):
            if is_conflict(cand[a], cand[b], adj): e += 1
    excl = set(idxs)
    K = len(sets)
    for a in range(len(cand)):
        A = cand[a]
        for j2 in range(K):
            if j2 in excl: continue
            if is_conflict(A, sets[j2], adj): e += 1
    return e

# Per-restart cap on inner local-search iterations, so restarts CYCLE across the
# profile list instead of one restart consuming the whole time budget (a spanning
# restart on seed-137 never stalls out — moves keep resetting `stall` — so without
# this cap round-robin never reaches the profile that holds the model). The cap is a
# deterministic count (not a wall-clock slice), and is large enough that the byte-exact
# D.2 reproduction (seed=1 solves the spanning profile in 3 iterations on restart 1)
# is never truncated by it.
PER_RESTART_ITERS = 1000

def solve(adj, n, k, rng, time_budget=90.0):
    # PROFILE-GENERAL head (SRCH-01): iterate (p', s') with p' + s' = k and
    # 2*p' + s' <= n (i.e. s' from max(0, 2*k - n) up to k, p' = k - s'), allowing
    # UNUSED vertices — never an `assert` (the old spanning-only assert crashed on
    # pool instances with k < n/2). The spanning profile (2*p' + s' == n) is first and
    # uses the byte-exact initial_state; non-spanning profiles use initial_state_profile.
    # Restarts round-robin across the profiles; a single rng is threaded through, so the
    # searcher stays deterministic in (n, seed).
    profiles = []
    for s in range(max(0, 2 * k - n), k + 1):
        p = k - s
        if p >= 0 and 2 * p + s <= n:
            profiles.append((p, s))
    start = time.time()
    restarts = 0
    best_init = None
    pidx = 0
    while profiles and time.time() - start < time_budget:
        p, s = profiles[pidx % len(profiles)]
        pidx += 1
        restarts += 1
        if 2 * p + s == n:
            sets = initial_state(adj, n, p, s, rng)
        else:
            sets = initial_state_profile(adj, n, p, s, rng)
        if sets is None:
            continue
        conf = full_conflicts(sets, adj)
        if best_init is None:
            best_init = len(conf)
        moves = 0; stall = 0; iters = 0
        while conf and time.time() - start < time_budget and iters < PER_RESTART_ITERS:
            iters += 1
            pr = tuple(conf)[rng.randrange(len(conf))]
            i, j = pr
            applied = False
            thirds = [l for l in range(len(sets)) if l != i and l != j]
            rng.shuffle(thirds)
            for l in thirds[:60]:
                idxs = (i, j, l)
                sizes = tuple(len(sets[t]) for t in idxs)
                verts = tuple(v for t in idxs for v in sets[t])
                cur = cand_energy(sets, idxs, [sets[t] for t in idxs], adj)
                best_e = cur; best_c = None
                for cand in assignments(verts, sizes):
                    if not valid_groups(cand, adj): continue
                    ce = cand_energy(sets, idxs, cand, adj)
                    if ce < best_e:
                        best_e = ce; best_c = cand
                        if best_e == 0: break
                if best_c is not None:
                    for t, g in zip(idxs, best_c):
                        sets[t] = tuple(g)
                    conf = update_conflicts(conf, sets, idxs, adj)
                    applied = True; moves += 1
                    break
            if not applied:
                stall += 1
                l = thirds[0] if thirds else None
                if l is not None:
                    idxs = (i, j, l)
                    sizes = tuple(len(sets[t]) for t in idxs)
                    verts = tuple(v for t in idxs for v in sets[t])
                    cands = [c for c in assignments(verts, sizes) if valid_groups(c, adj)]
                    if cands:
                        c = cands[rng.randrange(len(cands))]
                        for t, g in zip(idxs, c):
                            sets[t] = tuple(g)
                        conf = update_conflicts(conf, sets, idxs, adj)
                if stall > 300:
                    break
            else:
                stall = 0
        if not conf:
            return sets, best_init, moves, restarts, time.time() - start
    return None, best_init, None, restarts, time.time() - start
