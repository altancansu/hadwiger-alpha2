"""12-instance Cayley reproduction driver (schema-v1, inline H_edges).

Cayley complements Cay(Z_p, S)-bar with S a random maximal symmetric sum-free
subset of Z_p (Appendix C.3). Unlike the reference — which stored only `S` — this
driver reconstructs and stores the INLINE canonical `H_edges` so each record
verifies from the stored JSON alone (Pitfall 2 / T-3-01): the trust-root verifier
re-derives adjacency from stored bytes, never from a reconstruction routine.

Single-RNG contract v1 (byte-reproduction anchor): one `random.Random(seed)` feeds
`random_maximal_symmetric_sumfree(p, rng)` (consumes rng via `rng.shuffle`) FIRST,
then `solve(adj, p, chi, rng, time_budget=...)` — never a per-stage subseed.

Instances (Pitfall 1 — 12 total): p in (31, 53, 101, 151); for k in range(3),
seed = 5000 + 10*p + k. All 12 resolve heuristically — no ilp fallback (Phase 3 is
solver-free). Provenance is `provenance_params("cayley_maximal_sumfree_Zp", p,
{"S": sorted(S)}, seed=seed)` so R2 can regenerate.

Correctness routes ONLY through the raise-based trust root; the verified path is
assert-free (`python -O` safe). This driver appends onto `path`; it does NOT empty
or freeze the corpus — `repro/freeze.py` owns the single ordered freeze to 296.

Run:  python -m alpha2.repro.cayley_run
"""
import random
import time

from alpha2 import paths
from alpha2.generators.cayley import random_maximal_symmetric_sumfree, cayley_adj
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.search.heuristic import solve
from alpha2.corpus import schema, store


# ---------- driver ----------
def run_instance(p, seed, path, time_budget=60.0):
    """Regenerate Cayley (p, seed), search a K_chi model, store the schema-v1 cert.

    RNG contract v1: one stream feeds random_maximal_symmetric_sumfree FIRST (via
    rng.shuffle), then solve. Inline canonical H_edges are reconstructed from the
    Cayley adjacency so the record is self-contained (Pitfall 2).
    """
    rng = random.Random(seed)
    t0 = time.time()
    S = random_maximal_symmetric_sumfree(p, rng)               # consumes rng FIRST
    adj = cayley_adj(p, S)                                      # reconstruct adjacency
    nu = matching_number(adj, p)
    chi = p - nu
    sets, init_conf, moves, restarts, tsolve = solve(adj, p, chi, rng, time_budget=time_budget)
    M, U, nu2 = extract_witness(adj, p)                         # emission-time witness
    H_edges = sorted([min(u, v), max(u, v)] for u in range(p) for v in adj[u] if u < v)
    rec = schema.build_record(
        provenance=schema.provenance_params(
            "cayley_maximal_sumfree_Zp", p, {"S": sorted(S)}, seed=seed),
        H_edges=H_edges, nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in sets],
        matching_M=M, tutte_berge_U=U, method="heuristic",
        omega_G=None, verified=True,
    )
    store.append_certificate(rec, path=path)                   # verify-at-append + atomic write
    print(f"p={p:4d} seed={seed:5d} |S|={len(S):3d} nu(H)={nu:4d} chi(G)={chi:4d} "
          f"init_conflicts={init_conf} repair_moves={moves} "
          f"stored+verified  [{time.time()-t0:5.1f}s]", flush=True)
    return rec


def main(path=None, time_budget=60.0):
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    print("Cayley complements Cay(Z_p, S)-bar, S = random maximal symmetric sum-free")
    print("target: K_chi(G) minor; inline H_edges stored (self-contained certs)\n", flush=True)
    count = 0
    for p in (31, 53, 101, 151):
        for k in range(3):
            seed = 5000 + 10 * p + k
            run_instance(p, seed, path, time_budget=time_budget)
            count += 1
    print(f"\n{count} schema-v1 Cayley certificates stored + verified at {path}")


if __name__ == "__main__":
    main()
