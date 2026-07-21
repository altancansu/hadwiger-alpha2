# α = 2 Program — preserved source (toolkit + certificate facts)

**Provenance.** Canonical design document *"The α = 2 Program"* provided by the author on 2026-07-21 at project initialization. The narrative (principles, gate, phases, literature, strategy) is synthesized in `../PROJECT.md`; this file preserves the parts that must remain **byte-exact and cannot drift**: the complete Appendix C toolkit source, and the structured certificate facts (invariants + verified models) for the two exemplar instances plus the stored-certificate table.

**Reproducibility.** All generators are deterministic in `(n, seed)`, so every instance below is rebuildable exactly. The machine-readable corpus `hadwiger_alpha2_certificates.json` was *not* shipped with the document — it is regenerable from the code here. The two exemplar certificates' full `H_edges` arrays are omitted here purely for size (they are hundreds of lines of deterministic output); they are regenerated exactly by running the Appendix C code at the stated seeds. Invariants and the verified `model_branch_sets` are kept in full.

**Porting note.** The scripts as given write to `/mnt/user-data/outputs/hadwiger_alpha2_certificates.json` (the original sandbox path). Phase 1 must replace this with a **repo-relative** path (e.g. `data/hadwiger_alpha2_certificates.json`) as part of "make paths repo-relative," without altering the algorithms.

---

## Appendix C — Complete toolkit source code (verbatim)

**Environment.** Python 3 with `networkx` (Edmonds blossom matching) and `pulp` (CBC integer programming): `pip install networkx pulp`.

**Reproduction.** `python3 hadwiger_tfp.py` reruns the 12 baseline instances and writes the certificate file; `python3 sweep.py` runs the 270-seed sweep plus the n=301 and n=501 instances; `python3 cayley_test.py` runs the 12 sum-free Cayley instances; `python3 investigate_137.py` reruns the exact analysis of the seed-137 case study.

### C.1 — `hadwiger_tfp.py`

*Core pipeline: Bohman triangle-free process, exact chromatic number via matching, profile heuristic for K_chi models, independent verifier, baseline driver.*

```python
#!/usr/bin/env python3
"""
Test Hadwiger's conjecture on complements of triangle-free-process graphs.

For each instance:
  1. Run Bohman's triangle-free process -> maximal triangle-free H on n vertices.
     (So G = complement(H) has alpha(G) = 2, and H has diameter 2: the hard regime.)
  2. Compute chi(G) EXACTLY: chi(G) = n - nu(H), nu = max matching (Edmonds blossom).
  3. Search for a K_{chi(G)} model in G with branch sets of size <= 2.
  4. Independently VERIFY any found model: disjointness, pairs are G-edges,
     and ALL C(chi,2) pairwise adjacencies between branch sets.

A verified model is a certificate that had(G) >= chi(G), i.e. Hadwiger holds
for that instance. Seeds are recorded; everything is reproducible.
"""
import random, itertools, json, time, sys

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

# ---------- exact chromatic number of G = complement(H) ----------
def matching_number(adj, n):
    import networkx as nx
    Hg = nx.Graph(); Hg.add_nodes_from(range(n))
    Hg.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
    M = nx.max_weight_matching(Hg, maxcardinality=True)
    return len(M)

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

def solve(adj, n, k, rng, time_budget=90.0):
    p = n - k; s = 2 * k - n
    assert p >= 0 and s >= 0 and 2 * p + s == n
    start = time.time()
    restarts = 0
    best_init = None
    while time.time() - start < time_budget:
        restarts += 1
        sets = initial_state(adj, n, p, s, rng)
        if sets is None:
            continue
        conf = full_conflicts(sets, adj)
        if best_init is None:
            best_init = len(conf)
        moves = 0; stall = 0
        while conf and time.time() - start < time_budget:
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

# ---------- independent verifier ----------
def verify_model(sets, adj, n, k):
    assert len(sets) == k, "wrong number of branch sets"
    used = set()
    for S in sets:
        assert len(S) in (1, 2), "branch set size must be 1 or 2"
        for v in S:
            assert 0 <= v < n and v not in used, "branch sets not disjoint"
            used.add(v)
        if len(S) == 2:
            a, b = S
            assert b not in adj[a], "pair is not an edge of G"
    for i in range(k):
        for j in range(i + 1, k):
            assert not is_conflict(sets[i], sets[j], adj), \
                f"branch sets {i},{j} not adjacent in G"
    return True

# ---------- driver ----------
def run_instance(n, seed, records):
    rng = random.Random(seed)
    t0 = time.time()
    adj, m = triangle_free_process(n, rng)
    tf = is_triangle_free(adj, n)
    mx = is_edge_maximal_tf(adj, n)
    assert tf, "process produced a triangle?!"
    nu = matching_number(adj, n)
    chi = n - nu
    sets, init_conf, moves, restarts, tsolve = solve(adj, n, chi, rng)
    ok = False
    if sets is not None:
        ok = verify_model(sets, adj, n, chi)
    status = "K_chi MODEL FOUND + VERIFIED" if ok else "NOT FOUND (inconclusive)"
    print(f"n={n:4d} seed={seed:3d} |E(H)|={m:5d} nu(H)={nu:4d} chi(G)={chi:4d} "
          f"maxTF={str(mx):5s} init_conflicts={init_conf} repair_moves={moves} "
          f"{status}  [{time.time()-t0:5.1f}s]", flush=True)
    rec = {
        "n": n, "seed": seed, "process": "Bohman uniform triangle-free process",
        "H_edges": sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v),
        "H_triangle_free": tf, "H_edge_maximal": mx,
        "matching_number_H": nu, "chi_G": chi,
        "model_branch_sets": [list(S) for S in sets] if ok else None,
        "verified": ok,
    }
    records.append(rec)
    return ok

def main():
    instances = [(31, 1), (31, 2), (31, 3), (32, 4), (51, 5), (51, 6),
                 (76, 7), (101, 8), (101, 9), (151, 10), (200, 11), (201, 12)]
    records = []
    all_ok = True
    print("Hadwiger check on complements of triangle-free-process graphs")
    print("target: K_chi(G) minor, chi(G) = n - nu(H) computed exactly\n", flush=True)
    for n, seed in instances:
        ok = run_instance(n, seed, records)
        all_ok = all_ok and ok
    path = "/mnt/user-data/outputs/hadwiger_alpha2_certificates.json"
    with open(path, "w") as f:
        json.dump(records, f)
    print(f"\ncertificates + seeds + edge lists saved to {path}")
    print("ALL INSTANCES VERIFIED" if all_ok else "SOME INSTANCES UNRESOLVED - see above")

if __name__ == "__main__":
    main()
```

### C.2 — `sweep.py`

*Multi-seed sweep at the critical sizes plus the large-n showpieces.*

```python
import json, time, random
from hadwiger_tfp import (triangle_free_process, matching_number, solve,
                          verify_model, run_instance)

def quick(n, seed):
    rng = random.Random(seed)
    adj, m = triangle_free_process(n, rng)
    nu = matching_number(adj, n)
    chi = n - nu
    sets, ic, moves, restarts, t = solve(adj, n, chi, rng, time_budget=60)
    ok = sets is not None and verify_model(sets, adj, n, chi)
    return ok, (ic or 0)

t0 = time.time()
for n, seeds in [(31, range(100, 300)), (51, range(100, 150)), (101, range(100, 120))]:
    good = 0; tot = 0; maxic = 0; fails = []
    for s in seeds:
        ok, ic = quick(n, s)
        tot += 1; good += ok; maxic = max(maxic, ic)
        if not ok: fails.append(s)
    print(f"n={n:4d}: {good}/{tot} instances -> K_chi model found+verified; "
          f"max initial conflicts={maxic}; failures={fails}", flush=True)
print(f"sweep time {time.time()-t0:.1f}s\n", flush=True)

# larger showpieces, appended to the certificate file
path = "/mnt/user-data/outputs/hadwiger_alpha2_certificates.json"
recs = json.load(open(path))
for n, seed in [(301, 13), (501, 14)]:
    run_instance(n, seed, recs)
json.dump(recs, open(path, "w"))

# print the n=31 seed=1 certificate for display in chat
r = [x for x in recs if x["n"] == 31 and x["seed"] == 1][0]
print("\nn=31 seed=1: chi(G) =", r["chi_G"], "branch sets of the K_16 model:")
print(r["model_branch_sets"])
```

### C.3 — `cayley_test.py`

*Sum-free Cayley family: maximal symmetric sum-free construction, heuristic search, exact ILP fallback.*

```python
import random, json, time
from hadwiger_tfp import (matching_number, solve, verify_model,
                          is_triangle_free, is_edge_maximal_tf)

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

# ---- exact ILP fallback: compute had_2(G) ----
def ilp_had2(adj, n, chi, time_limit=300):
    import pulp
    Gedges = [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]
    prob = pulp.LpProblem("had2", pulp.LpMaximize)
    mv = {e: pulp.LpVariable(f"m_{e[0]}_{e[1]}", cat="Binary") for e in Gedges}
    sv = {v: pulp.LpVariable(f"s_{v}", cat="Binary") for v in range(n)}
    prob += pulp.lpSum(mv.values()) + pulp.lpSum(sv.values())
    for v in range(n):
        prob += pulp.lpSum(mv[e] for e in Gedges if v in e) + sv[v] <= 1
    for i in range(len(Gedges)):
        a, b = Gedges[i]
        ai, bi = adj[a], adj[b]
        for j in range(i + 1, len(Gedges)):
            c, d = Gedges[j]
            if c == a or c == b or d == a or d == b: continue
            if c in ai and d in ai and c in bi and d in bi:
                prob += mv[Gedges[i]] + mv[Gedges[j]] <= 1
    for v in range(n):
        av = adj[v]
        for (a, b) in Gedges:
            if v != a and v != b and a in av and b in av:
                prob += sv[v] + mv[(a, b)] <= 1
    for u in range(n):
        for v in adj[u]:
            if v > u: prob += sv[u] + sv[v] <= 1
    prob.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    val = pulp.value(prob.objective)
    if val is None: return None, None
    had2 = int(round(val))
    fam = [tuple(e) for e in Gedges if mv[e].value() and mv[e].value() > 0.5] + \
          [(v,) for v in range(n) if sv[v].value() and sv[v].value() > 0.5]
    return had2, fam

def run(p, seed, records):
    rng = random.Random(seed)
    t0 = time.time()
    S = random_maximal_symmetric_sumfree(p, rng)
    adj = cayley_adj(p, S)
    assert is_triangle_free(adj, p), "S not sum-free?!"
    mx = is_edge_maximal_tf(adj, p)
    nu = matching_number(adj, p); chi = p - nu
    sets, ic, moves, restarts, t = solve(adj, p, chi, rng, time_budget=60)
    method = "heuristic"
    ok = sets is not None and verify_model(sets, adj, p, chi)
    had2 = None
    if not ok:
        method = "exact ILP"
        had2, fam = ilp_had2(adj, p, chi)
        if had2 is not None and had2 >= chi:
            sets = fam[:chi]
            ok = verify_model(sets, adj, p, chi)
    print(f"p={p:4d} seed={seed:5d} |S|={len(S):3d} deg={len(S):3d} "
          f"maxTF={str(mx):5s} nu={nu:4d} chi={chi:4d} "
          f"{'K_chi MODEL FOUND + VERIFIED' if ok else f'NOT RESOLVED (had2={had2})'} "
          f"[{method}, {time.time()-t0:5.1f}s]", flush=True)
    records.append({"family": "cayley_maximal_sumfree_Zp", "p": p, "seed": seed,
                    "S": sorted(S), "H_triangle_free": True, "H_edge_maximal": mx,
                    "matching_number_H": nu, "chi_G": chi,
                    "model_branch_sets": [list(x) for x in sets] if ok else None,
                    "verified": ok, "method": method,
                    "had2_exact": had2})
    return ok

def main():
    path = "/mnt/user-data/outputs/hadwiger_alpha2_certificates.json"
    records = json.load(open(path))
    print("Cayley complements Cay(Z_p, S)-bar, S = random maximal symmetric sum-free")
    print("(open family: algebraic construction, pseudorandom flavor, blow-up-adjacent)\n", flush=True)
    all_ok = True
    for p in (31, 53, 101, 151):
        for k in range(3):
            all_ok &= run(p, 5000 + 10 * p + k, records)
    json.dump(records, open(path, "w"))
    print("\nappended to certificate file")
    print("ALL CAYLEY INSTANCES VERIFIED" if all_ok else "SOME UNRESOLVED - see above")

if __name__ == "__main__":
    main()
```

### C.4 — `investigate_137.py`

*Case-study script for the seed-137 instance (exact invariants and ILP).*

```python
import random, json, time
import networkx as nx
from hadwiger_tfp import (triangle_free_process, is_triangle_free, is_edge_maximal_tf,
                          matching_number, verify_model, solve)

n, seed = 31, 137
rng = random.Random(seed)
adj, m = triangle_free_process(n, rng)
print(f"instance n={n} seed={seed}: |E(H)|={m}, triangle-free={is_triangle_free(adj,n)}, "
      f"edge-maximal={is_edge_maximal_tf(adj,n)}")
nu = matching_number(adj, n)
chi = n - nu
print(f"nu(H)={nu}  =>  chi(G)={chi}  (exact, Gallai/PST)")

H = nx.Graph(); H.add_nodes_from(range(n))
H.add_edges_from((u, v) for u in range(n) for v in adj[u] if u < v)
Gc = nx.complement(H)
clq, _ = nx.max_weight_clique(Gc, weight=None)
print(f"omega(G) = alpha(H) = {len(clq)}   (R(3,8)=28 forces omega>=8 at n=31)")

# retry heuristic with a fresh RNG and 5x budget
sets, ic, moves, restarts, t = solve(adj, n, chi, random.Random(999), time_budget=300)
if sets is not None and verify_model(sets, adj, n, chi):
    print(f"heuristic retry: FOUND + VERIFIED after {restarts} restarts, {t:.1f}s")
    print("model:", [list(S) for S in sets])
else:
    print(f"heuristic retry: still not found ({restarts} restarts, {t:.1f}s) -> going exact via ILP")

# ---- exact: ILP computing had_2(G) = max pairwise-adjacent family of branch sets of size <= 2
import pulp
Gedges = [(u, v) for u in range(n) for v in range(u + 1, n) if v not in adj[u]]
prob = pulp.LpProblem("had2", pulp.LpMaximize)
mvar = {e: pulp.LpVariable(f"m_{e[0]}_{e[1]}", cat="Binary") for e in Gedges}
svar = {v: pulp.LpVariable(f"s_{v}", cat="Binary") for v in range(n)}
prob += pulp.lpSum(mvar.values()) + pulp.lpSum(svar.values())
for v in range(n):
    prob += pulp.lpSum(mvar[e] for e in Gedges if v in e) + svar[v] <= 1
npp = 0
for i in range(len(Gedges)):
    a, b = Gedges[i]
    for j in range(i + 1, len(Gedges)):
        c, d = Gedges[j]
        if len({a, b, c, d}) < 4: continue
        if c in adj[a] and d in adj[a] and c in adj[b] and d in adj[b]:
            prob += mvar[Gedges[i]] + mvar[Gedges[j]] <= 1; npp += 1
nsp = 0
for v in range(n):
    for (a, b) in Gedges:
        if v == a or v == b: continue
        if a in adj[v] and b in adj[v]:
            prob += svar[v] + mvar[(a, b)] <= 1; nsp += 1
nss = 0
for u in range(n):
    for v in adj[u]:
        if v > u:
            prob += svar[u] + svar[v] <= 1; nss += 1
print(f"ILP: {len(Gedges)} pair-vars, {n} singleton-vars; conflicts: "
      f"pair-pair={npp}, single-pair={nsp}, single-single={nss}")
t0 = time.time()
prob.solve(pulp.PULP_CBC_CMD(msg=0))
had2 = int(round(pulp.value(prob.objective)))
print(f"ILP status={pulp.LpStatus[prob.status]}  had_2(G) = {had2}  "
      f"(need >= chi = {chi})   [{time.time()-t0:.1f}s]")
if had2 >= chi:
    fam = [tuple(e) for e in Gedges if mvar[e].value() > 0.5] + \
          [(v,) for v in range(n) if svar[v].value() > 0.5]
    model = fam[:chi]
    ok = verify_model(model, adj, n, chi)
    print("exact model extracted, independently VERIFIED:", ok)
    print("model:", [list(S) for S in model])
    # append to certificate file
    path = "/mnt/user-data/outputs/hadwiger_alpha2_certificates.json"
    recs = json.load(open(path))
    recs.append({"n": n, "seed": seed, "process": "Bohman uniform triangle-free process",
                 "H_edges": sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v),
                 "H_triangle_free": True, "H_edge_maximal": True,
                 "matching_number_H": nu, "chi_G": chi, "omega_G": len(clq),
                 "model_branch_sets": [list(S) for S in model], "verified": ok,
                 "method": "exact ILP (CBC), had_2(G) = %d" % had2})
    json.dump(recs, open(path, "w"))
    print("appended to certificate file")
else:
    print("!!! had_2(G) < chi(G): no size-<=2 model exists for this instance.")
    print("!!! This does NOT yet decide Hadwiger here - escalating to branch sets of size 3 next.")
```

---

## Appendix D — Certificate facts (structured)

**Accounting.** 296 instances generated and verified: 284 triangle-free-process complements (n = 31–501) + 12 sum-free Cayley complements (p ≤ 151). 27 carry fully self-contained stored certificates in the JSON corpus (27/27 verified). The remaining 269 were the in-run sweep — n=31 seeds 100–299 (seed 137 resolved by exact ILP, stored in full), n=51 seeds 100–149, n=101 seeds 100–119 — each verified at run time and exactly reproducible from its (n, seed) pair.

### D.1 — Stored certificates (table)

| # | family | n | seed | chi(G) | method | verified |
|---|---|---|---|---|---|---|
| 1 | triangle_free_process_complement | 31 | 1 | 16 | heuristic | yes |
| 2 | triangle_free_process_complement | 31 | 2 | 16 | heuristic | yes |
| 3 | triangle_free_process_complement | 31 | 3 | 16 | heuristic | yes |
| 4 | triangle_free_process_complement | 32 | 4 | 16 | heuristic | yes |
| 5 | triangle_free_process_complement | 51 | 5 | 26 | heuristic | yes |
| 6 | triangle_free_process_complement | 51 | 6 | 26 | heuristic | yes |
| 7 | triangle_free_process_complement | 76 | 7 | 38 | heuristic | yes |
| 8 | triangle_free_process_complement | 101 | 8 | 51 | heuristic | yes |
| 9 | triangle_free_process_complement | 101 | 9 | 51 | heuristic | yes |
| 10 | triangle_free_process_complement | 151 | 10 | 76 | heuristic | yes |
| 11 | triangle_free_process_complement | 200 | 11 | 100 | heuristic | yes |
| 12 | triangle_free_process_complement | 201 | 12 | 101 | heuristic | yes |
| 13 | triangle_free_process_complement | 301 | 13 | 151 | heuristic | yes |
| 14 | triangle_free_process_complement | 501 | 14 | 251 | heuristic | yes |
| 15 | triangle_free_process_complement | 31 | 137 | 16 | exact ILP (CBC): had_2(G)=17 | yes |
| 16 | cayley_maximal_sumfree_Zp | 31 | 5310 | 16 | heuristic | yes |
| 17 | cayley_maximal_sumfree_Zp | 31 | 5311 | 16 | heuristic | yes |
| 18 | cayley_maximal_sumfree_Zp | 31 | 5312 | 16 | heuristic | yes |
| 19 | cayley_maximal_sumfree_Zp | 53 | 5530 | 27 | heuristic | yes |
| 20 | cayley_maximal_sumfree_Zp | 53 | 5531 | 27 | heuristic | yes |
| 21 | cayley_maximal_sumfree_Zp | 53 | 5532 | 27 | heuristic | yes |
| 22 | cayley_maximal_sumfree_Zp | 101 | 6010 | 51 | heuristic | yes |
| 23 | cayley_maximal_sumfree_Zp | 101 | 6011 | 51 | heuristic | yes |
| 24 | cayley_maximal_sumfree_Zp | 101 | 6012 | 51 | heuristic | yes |
| 25 | cayley_maximal_sumfree_Zp | 151 | 6510 | 76 | heuristic | yes |
| 26 | cayley_maximal_sumfree_Zp | 151 | 6511 | 76 | heuristic | yes |
| 27 | cayley_maximal_sumfree_Zp | 151 | 6512 | 76 | heuristic | yes |

### D.2 — Exemplar n=31, seed 1 (invariants + verified model)

- process: Bohman uniform triangle-free process; H_triangle_free: true; H_edge_maximal: true
- |E(H)| = 131; matching_number_H (ν) = 15; **chi_G = 16**
- `H_edges`: **regenerable** — run `triangle_free_process(31, random.Random(1))` (deterministic).
- verified: true; **model_branch_sets** (K₁₆ model, size-≤2 branch sets):

```json
[[16,20],[14,3],[11,4],[10,19],[26,9],[6,29],[18,25],[13,24],[30,8],[15,28],[27,12],[23,7],[17,2],[0],[21,22],[1,5]]
```

### D.3 — Exemplar n=31, seed 137 (the case study — resisted heuristic, fell to exact ILP)

- process: Bohman uniform triangle-free process; H_triangle_free: true; H_edge_maximal: true
- matching_number_H (ν) = 15; **chi_G = 16**; **omega_G = 14**; **had_2(G) = 17** (exact ILP, CBC)
- `H_edges`: **regenerable** — run `triangle_free_process(31, random.Random(137))` (deterministic).
- method: `exact ILP (CBC): had_2(G)=17`; verified: true; **model_branch_sets** (9 pairs + 7 singletons — the profile the original heuristic could not represent):

```json
[[2,20],[4,7],[8,18],[9,13],[12,27],[16,22],[17,24],[19,29],[26,28],[0],[1],[3],[10],[11],[21],[23]]
```

---

## Appendix E — Pinned verbatim: gate (§2), kill-battery runbook (§4), governing rules (§5)

*Preserved from the source document because §2/§4/§5 were digested (not stored byte-exact) in the initial preservation, and the project-research agents flagged the exact G1–G6 definitions as needed downstream. Rendered in unicode; content is the author's §2/§4/§5.*

### §2 — The gate: anatomy of a minimal counterexample

Everything below is proven about a minimal counterexample G to the α=2 case (Plummer–Stiebitz–Toft 2003; Bosse 2019; Carter 2024; Costa–Luu–Wood–Yip 2025). The gate exists so that no compute is ever spent on a candidate that is dead on arrival, and it is run in increasing order of cost.

| # | Requirement | Source / reason |
|---|---|---|
| G1 | n ≥ 31, n odd, n = 2χ(G) − 1 | Carter's computational bound; criticality |
| G2 | H = Ḡ triangle-free with diameter 2 (equivalently: edge-maximal triangle-free) | no dominating edge may exist |
| G3 | χ(G) ≥ 7, κ(G) ≥ χ(G), δ(G) ≥ χ(G)+1, G Hamiltonian, G vertex-critical, H − v has a perfect matching for all v | RST for K₆; PST properties |
| G4 | 8 ≤ ω(G) ≤ χ(G) − 3, and clique ratio ω/n below ≈ 1/4 | K₈ is unavoidable (Carter; also R(3,8)=28); Chudnovsky–Seymour's seagull theorem builds the minor above the threshold |
| G5 | Every non-adjacent pair lies in an induced C₅; G contains W₅, K₈, and all 33 of Carter's unavoidable graphs as induced subgraphs | unavoidability results |
| G6 | G lies outside every proven-safe family | see list below |

**Proven-safe families** (membership here is an instant kill): line graphs (Reed–Seymour); quasi-line graphs (Chudnovsky–Fradkin); C₅-free graphs (PST); inflations of any graph on ≤ 11 vertices (PST); inflations of complements of girth-≥5 graphs, including the 5-cycle, Petersen, and Hoffman–Singleton graphs; inflations of complements of triangle-free Kneser graphs; the Clebsch, Mesner, and Gewirtz complements and their inflations; the Higman–Sims complement (explicit K₅₀ model); Andrásfai and odd-anticycle inflations; the Eberhard Cayley complements; graphs with fractional clique cover number below 3 and even order (Blasiak); and any graph on ≤ 87 vertices for the connected-matching weakening (Füredi–Gyárfás–Simonyi; Chen–Deng). Most of these were verified in the December 2025 paper *because they resemble hypothetical counterexamples* — which is exactly why a candidate must clear them.

### §4 — Phase 2: the kill battery (runbook)

For each candidate graph, execute in order. Nothing counts as *found* until step 6's verifier passes; nothing counts as *absent* until an exact method proves it.

1. **Gate.** Run G1–G6 in cost order; kill on first failure; log the reason and seed.
2. **Exact chromatic number.** Build H, confirm triangle-freeness and edge-maximality, compute ν(H) by Edmonds blossom, set χ = n − ν. No estimates anywhere.
3. **Heuristic model search, profile-general.** Search for a K_χ model with branch sets of size ≤ 2. Encode the seed-137 lesson: iterate over pair/singleton profiles (from all-pairs down to clique-heavy), seed clique-rich profiles from a greedy large clique, allow unused vertices, and repair conflicts with 3-set redistributions. Budget: 60 s.
4. **Exact ILP.** Compute had₂(G) exactly (variables: candidate pairs and singletons; constraints: vertex-disjointness plus one pairwise-conflict inequality per obstructing C₄, path, or edge of H). Use symmetry-breaking for vertex-transitive candidates. This step is decisive in both directions for the size-≤2 question.
5. **Branch-set-3 escalation.** If had₂(G) < χ exactly: first, record the instance as an **SHC candidate** — that inequality alone, verified, refutes Seymour's strengthening and is a prize independent of HC. Then attack HC proper with size-3 sets: check the Chudnovsky–Seymour seagull conditions, attempt clique-plus-seagull constructions, and extend the ILP with triple variables pruned by common-neighborhood emptiness (in a sparse triangle-free H, the common H-neighborhood of a connected triple is almost always empty, so triple-conflict constraints are few).
6. **Verification.** Any model found, by any method, passes the independent verifier: branch sets disjoint, sizes valid, every pair an actual edge of G, all C(χ,2) cross-adjacencies present. Verified instances are appended to the certificate corpus with seed, edge list, model, and method. Status: **KILLED**.
7. **Residue.** Anything not killed and not exactly resolved is **RESISTANT** and goes to Phase 3. Resistance is a statement about our searchers until an exact method says otherwise — seed 137 is the standing reminder that the first resistant instance we ever met was a bug in our own profile assumption, dissolved by the ILP in one run.

### §5 — The two governing rules (Phase 3)

**The Falsification Rule.** Any proposed "no K_k minor" argument must first be *mechanically executed* against the certificate corpus and must decline to prove impossibility on every instance where a verified model exists. An argument that "proves" non-existence for a graph holding a hand-checkable K_χ model is not evidence about the candidate — it is refuted, full stop. The corpus is thus not merely a results file; it is a falsification suite for bogus impossibility proofs, and it grows stronger with every kill.

**The Monotonicity Audit.** Any invariant-based impossibility claim must use a genuinely minor-monotone invariant. The known list is short — essentially the Colin de Verdière parameter μ and its relatives — and even there, upper-bounding μ for a dense graph means proving no high-corank certifying matrix exists, which has no known certificate technique. The celebrated rank methods (Frankl–Wilson, slice rank, Haemers minrank), spectral gaps, and rigidity notions are not minor-monotone, because contraction destroys linear structure; they are disqualified at the door. Note the corpus already speaks here: each certificate proves μ(G) ≥ χ(G) − 1 on its instance, so a rank-flavored impossibility claim about a tested graph contradicts an explicitly checkable object.
