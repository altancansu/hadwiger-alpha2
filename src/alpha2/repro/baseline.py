"""Baseline reproduction driver (thin entry).

Verbatim port of run_instance + the baseline driver from Appendix C.1
(hadwiger_tfp.py main()). The ONLY changes vs the reference are (1) the output
path moves from the sandbox /mnt/... location to paths.CORPUS (repo-relative), and
(2) cross-module imports. Algorithm bodies are unchanged.

Single-RNG contract v1 (research Pattern 2): run_instance seeds exactly one
random.Random(seed) and lets triangle_free_process THEN solve consume that same
stream in that order. Do NOT introduce per-stage subseeds.

Run:  python -m alpha2.repro.baseline
"""
import random, time, json

from alpha2 import paths
from alpha2.generators.tfp import (
    triangle_free_process,
    is_triangle_free,
    is_edge_maximal_tf,
)
from alpha2.invariants.matching import matching_number
from alpha2.search.heuristic import solve
from alpha2.verify.model import verify_model

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
    path = paths.ensure_parent(paths.CORPUS)
    with open(path, "w") as f:
        json.dump(records, f)
    print(f"\ncertificates + seeds + edge lists saved to {path}")
    print("ALL INSTANCES VERIFIED" if all_ok else "SOME INSTANCES UNRESOLVED - see above")

if __name__ == "__main__":
    main()
