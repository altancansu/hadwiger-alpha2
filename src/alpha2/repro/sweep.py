"""269-instance TFP sweep reproduction driver (schema-v1, trust-root emission).

Copies the FINALIZED `repro/baseline.py` emission path verbatim — same
single-RNG contract v1 (one `random.Random(seed)` feeds `triangle_free_process`
THEN `solve`, in that order), same witness -> build_record -> append_certificate
tail through the store's verify-at-append trust root. The ONLY difference is the
instance list, encoded as data.

Sweep decomposition (Pitfall 1 — seed-137 EXCLUDED; it is stored once by
seed137.py as the exact study):
    n=31   seeds 100..299  (200) minus seed 137  -> 199
    n=51   seeds 100..149  (50)
    n=101  seeds 100..119  (20)
                                                  -> 269 total

Correctness routes ONLY through the raise-based trust root
(`store.append_certificate` -> `verify_certificate`), never through an `assert`,
so `python -O` cannot turn a check into a no-op (Pitfall 6). The `len == 269`
assert governs the instance-count accounting, not a verification decision.

This driver appends onto whatever corpus `path` points at; it does NOT empty or
freeze the corpus — `repro/freeze.py` owns the single ordered freeze to 296.

Run:  python -m alpha2.repro.sweep
"""
import random
import time

from alpha2 import paths
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.search.heuristic import solve
from alpha2.corpus import schema, store


# ---------- driver ----------
def run_instance(n, seed, path):
    """Regenerate (n, seed), search a K_chi model, store the schema-v1 certificate.

    RNG contract v1: one stream feeds triangle_free_process FIRST, then solve.
    The emission-time witness (M, U) is UNTRUSTED — append_certificate re-checks the
    Tutte-Berge inequality and the branch-set model from the stored bytes alone.
    """
    rng = random.Random(seed)
    t0 = time.time()
    adj, m = triangle_free_process(n, rng)                      # consumes rng FIRST
    nu = matching_number(adj, n)
    chi = n - nu
    sets, init_conf, moves, restarts, tsolve = solve(adj, n, chi, rng)  # SAME rng, next
    M, U, nu2 = extract_witness(adj, n)                         # emission-time witness
    H_edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
    rec = schema.build_record(
        provenance=schema.provenance_seed(
            "triangle_free_process_complement", n, seed,
            "Bohman uniform triangle-free process"),
        H_edges=H_edges, nu_H=nu, chi_G=chi,
        model_branch_sets=[list(s) for s in sets],
        matching_M=M, tutte_berge_U=U, method="heuristic",
        omega_G=None, verified=True,
    )
    store.append_certificate(rec, path=path)                   # verify-at-append + atomic write
    print(f"n={n:4d} seed={seed:3d} |E(H)|={m:5d} nu(H)={nu:4d} chi(G)={chi:4d} "
          f"init_conflicts={init_conf} repair_moves={moves} "
          f"stored+verified  [{time.time()-t0:5.1f}s]", flush=True)
    return rec


def main(path=None):
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    # 269 sweep instances (seed-137 EXCLUDED — stored once as the exact study):
    instances = ([(31, s) for s in range(100, 300) if s != 137]
                 + [(51, s) for s in range(100, 150)]
                 + [(101, s) for s in range(100, 120)])
    assert len(instances) == 269
    print("TFP sweep: complements of triangle-free-process graphs (269 instances)")
    print("target: K_chi(G) minor, chi(G) = n - nu(H) computed exactly\n", flush=True)
    for n, seed in instances:
        run_instance(n, seed, path)
    print(f"\n{len(instances)} schema-v1 sweep certificates stored + verified at {path}")


if __name__ == "__main__":
    main()
