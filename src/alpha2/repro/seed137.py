"""seed-137 exact-study reproduction driver (schema-v1, SOLVER-FREE literal carry).

Phase 3 is solver-free: this driver regenerates H from `random.Random(137)` via
`triangle_free_process(31, rng)` and carries the Appendix D.3 K16 model as a stored
LITERAL. It does NOT call `solve`, does NOT run CBC/ortools, and does NOT re-solve
seed-137 (Anti-Pattern "Re-solving seed-137"; the true had_2(G)=17 family arrives in
Phase 4 via CBC on the canonical Linux platform).

The carried record matches the Phase-2 interim exactly (02-02-SUMMARY.md):
  * model_branch_sets = the D.3 K16 literal (9 pairs + 7 singletons) -> had_2 = 16
    (the interim derived value; len(model) == 16);
  * method = "exact ILP (CBC): had_2(G)=17" — documents the TRUE had_2; the "ILP"
    substring makes reproduction.kind = semantic (schema.reproduction_kind_for_method);
  * omega_G = 14.

Correctness routes ONLY through the raise-based trust root (`append_certificate` ->
`verify_certificate`), never an `assert`, so `python -O` cannot no-op a check. This
driver appends onto `path`; it does NOT empty or freeze the corpus — `repro/freeze.py`
owns the single ordered freeze to 296. seed-137 is stored ONCE here (excluded from the
sweep loop, Pitfall 1).

Run:  python -m alpha2.repro.seed137
"""
import random
import time

from alpha2 import paths
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.corpus import schema, store

# Source: Appendix D.3 — K16 model (9 pairs + 7 singletons). The verifier re-checks
# this branch-set family against the regenerated H from the stored bytes alone.
SEED137_MODEL = [[2, 20], [4, 7], [8, 18], [9, 13], [12, 27], [16, 22], [17, 24],
                 [19, 29], [26, 28], [0], [1], [3], [10], [11], [21], [23]]


def run(path=None):
    """Regenerate seed-137 H, carry the D.3 literal, store the schema-v1 record."""
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    t0 = time.time()
    rng = random.Random(137)
    adj, m = triangle_free_process(31, rng)        # regenerate H only; do NOT call solve
    nu = matching_number(adj, 31)
    chi = 31 - nu
    M, U, nu2 = extract_witness(adj, 31)           # emission-time witness (verifier re-checks)
    H_edges = sorted([min(u, v), max(u, v)] for u in range(31) for v in adj[u] if u < v)
    rec = schema.build_record(
        provenance=schema.provenance_seed(
            "triangle_free_process_complement", 31, 137,
            "Bohman uniform triangle-free process"),
        H_edges=H_edges, nu_H=nu, chi_G=chi,
        model_branch_sets=SEED137_MODEL,           # literal; had_2 = len = 16 (interim)
        matching_M=M, tutte_berge_U=U,
        method="exact ILP (CBC): had_2(G)=17",     # documents true had_2; family arrives Phase 4
        omega_G=14, verified=True,
    )
    store.append_certificate(rec, path=path)       # verify-at-append + atomic write
    print(f"n=  31 seed=137 |E(H)|={m:5d} nu(H)={nu:4d} chi(G)={chi:4d} "
          f"had_2(model)={len(SEED137_MODEL)} (D.3 literal, no solver) "
          f"stored+verified  [{time.time()-t0:5.1f}s]", flush=True)
    return rec


def main(path=None):
    print("seed-137 exact study: Appendix D.3 K16 model carried as a literal (no solver)\n",
          flush=True)
    run(path)


if __name__ == "__main__":
    main()
