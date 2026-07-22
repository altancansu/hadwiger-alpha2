"""Baseline + showpiece reproduction driver (schema-v1, trust-root emission).

Finalized from the Appendix C.1 port: `run_instance` now emits a witness-complete
schema-v1 certificate through the append-only store's verify-at-append gate, instead
of the old ad-hoc pre-schema dict + `json.dump`. Correctness routes ONLY through the
raise-based trust root (`store.append_certificate` -> `verify_certificate`), never
through an `assert` — so `python -O` (assert-stripping CI job) cannot turn a check
into a no-op (Pitfall 6 / T-3-03).

Single-RNG contract v1 (byte-reproduction anchor, T-3-02): `run_instance` seeds
exactly one `random.Random(seed)` and lets `triangle_free_process` THEN `solve`
consume that same stream in that order. Do NOT introduce per-stage subseeds — the
(31, seed=1) model is byte-equal to Appendix D.2 only under this exact order.

Emits 14 triangle-free-process records: the 12 baseline instances + 2 showpieces
(n=301, n=501). The corpus is rebuilt from EMPTY on every run (the store is
append-only and refuses a reorder, so re-runs must not double-append).

Run:  python -m alpha2.repro.baseline
"""
import os
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
    if sets is None:
        # Wall-clock timeout: solve() found no model. Fail loudly and deterministically
        # (WR-02) — never fall through to an opaque TypeError downstream.
        raise RuntimeError(
            f"heuristic search timed out for n={n} seed={seed} "
            f"(restarts={restarts}, elapsed={tsolve:.1f}s) — no model found")
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
    instances = [(31, 1), (31, 2), (31, 3), (32, 4), (51, 5), (51, 6),
                 (76, 7), (101, 8), (101, 9), (151, 10), (200, 11), (201, 12),
                 (301, 13), (501, 14)]
    # Same `path=None` contract as the sibling drivers (sweep/cayley_run/seed137):
    # the default resolves to paths.CORPUS exactly as before; a caller-supplied
    # path is honored END-TO-END (empty + write + report all target the SAME path),
    # so `freeze(path=...)` can never destroy the committed corpus (CR-01).
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    # Begin from an EMPTY corpus: the store is append-only and refuses a reorder, so
    # a re-run must not double-append onto a non-empty corpus.
    if os.path.exists(path):
        os.remove(path)
    print("Hadwiger check on complements of triangle-free-process graphs")
    print("target: K_chi(G) minor, chi(G) = n - nu(H) computed exactly\n", flush=True)
    for n, seed in instances:
        run_instance(n, seed, path)
    print(f"\n{len(instances)} schema-v1 certificates stored + verified at {path}")


if __name__ == "__main__":
    main()
