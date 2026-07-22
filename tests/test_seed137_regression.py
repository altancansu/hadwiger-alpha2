"""seed-137 optimize regression — had_2 = 17 PROVED_OPTIMAL through the trust root.

The Phase-4 capstone (ROADMAP SC2, verbatim): regenerate the (n=31, seed=137)
instance from the frozen generator, prove had_2(G) = 17 with the CBC reference
backend in optimize mode, and route the FULL 17-set family through the frozen
trust root (`verify_certificate`) as an IN-MEMORY schema-v1 record.

LOCKED reconciliation (regression-as-test): the frozen corpus, the repro
drivers, R1/R2/R3 and the manifest stay byte-untouched. This test makes no
corpus-store call of any kind and never touches a data/ path except one
read-only load — the record lives and dies in memory. The corpus upgrade to the stored 17-set
family is a DEFERRED deliberate freeze amendment (first consumer: the Phase-11
Falsification-Rule harness).

Regression contract is SEMANTIC, never byte (ENV-05 / Assumption A1): the
locked constants asserted here are value/status/bound/verifiability — never
WHICH 17-set family CBC returned.

Slow tier: the single-thread optimality proof runs ~149 s; the test carries
`@pytest.mark.slow` (marker already registered in pyproject.toml) and joins
the existing release-gate `-m slow` selector automatically — no CI edit.

Trust-root calls are made OUTSIDE any test truth-expression — call, bind k,
then compare — so the verification itself is never an optimization-strippable
statement.
"""
import json
import random

import pytest

from alpha2 import paths
from alpha2.corpus.schema import build_record, make_backends, provenance_seed
from alpha2.corpus.verifier import verify_certificate
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.solvers.backend import get_backend
from alpha2.solvers.cbc import cbc_binary_version
from alpha2.solvers.result import SolveParams, Status


def _find_stored_seed_record(n, seed):
    """The single committed seed-kind (n, seed) record — READ-ONLY corpus load.

    Embedded locally (no cross-test import from test_corpus_r1, per the
    embedded-literal discipline).
    """
    with open(paths.CORPUS) as fh:
        records = json.load(fh)
    hits = [
        r for r in records
        if r["provenance"].get("kind") == "seed"
        and r["provenance"].get("n") == n
        and r["provenance"].get("seed") == seed
    ]
    assert len(hits) == 1, (n, seed, len(hits))
    return hits[0]


@pytest.mark.slow
def test_seed137_had2_17_proved_optimal_through_trust_root():
    n = 31

    # ---- Regeneration gates (the R2 discipline): a drifted generator must ----
    # ---- fail HERE, before any solve is trusted or even attempted.        ----
    rng = random.Random(137)
    adj, m = triangle_free_process(n, rng)
    assert m == 177, m
    nu = matching_number(adj, n)
    assert nu == 15, nu
    chi = n - nu
    assert chi == 16, chi

    # ---- The optimality proof (~149 s single-thread; 600 s headroom). ----
    out = get_backend("cbc").solve_had2(
        adj, n, mode="optimize", params=SolveParams(time_limit_s=600)
    )

    # ---- LOCKED constants: value/status/bound/verifiability, never bytes. ----
    assert out.status is Status.PROVED_OPTIMAL  # two-field gate by construction
    assert out.exact_value() == 17
    assert out.bound == 17
    assert out.family is not None
    assert len(out.family) == 17
    assert "2.10.3" in out.backend_version
    assert "pulp==3.3.2" in out.backend_version

    # ---- Trust root: the 17-set family is an UNTRUSTED proposal until the ----
    # ---- frozen verifier arbitrates. The record stays IN MEMORY: no store ----
    # ---- call, no file write — the frozen corpus is byte-untouched.       ----
    M, U, nu2 = extract_witness(adj, n)
    H_edges = sorted(
        [min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v
    )
    method = "exact ILP (CBC): had_2(G)=17"
    # Backend-version stamping closure (02-02 decision: backends overridable):
    # stamp the PROBED CBC binary version instead of the Phase-2
    # "bundled-with-pulp-3.3.2" stub. schema.py itself stays frozen.
    backends = make_backends(method)
    backends["cbc"] = f"CBC {cbc_binary_version()}"
    rec = build_record(
        provenance=provenance_seed(
            "triangle_free_process_complement", n, 137,
            "Bohman uniform triangle-free process",
        ),
        H_edges=H_edges,
        nu_H=nu,
        chi_G=chi,
        model_branch_sets=[list(s) for s in out.family],  # FULL family — 17 sets
        matching_M=M,
        tutte_berge_U=U,
        method=method,
        omega_G=14,
        verified=True,
        backends=backends,
    )
    k = verify_certificate(rec)  # trust root arbitrates; raises on any defect
    assert k == 17
    assert rec["invariants"]["had_2"] == 17
    assert "2.10.3" in rec["backends"]["cbc"]

    # ---- Metamorphic anchor (verifier trumps solver): the committed D.3    ----
    # ---- record stores a VERIFIED 16-set family; a PROVED_OPTIMAL value    ----
    # ---- below any stored verified family size is a CRITICAL encoding bug. ----
    stored = _find_stored_seed_record(n, 137)
    stored_size = len(stored["model_branch_sets"])
    assert stored_size == 16, stored_size
    assert out.exact_value() == 17 > stored_size
