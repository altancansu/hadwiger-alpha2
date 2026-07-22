"""Reproduction contract proof (ENV-05).

Every certificate distinguishes byte-exact reproduction (heuristic/seed-derived
models — byte-reproducible from (n, seed) on the pinned interpreter) from semantic
reproduction (exact-method models — the *claim* is reproducible, the model bytes
are not cross-solver/-platform), stamps solver/platform versions, and designates
Linux x86_64 the canonical reference-regeneration platform.

The reproduction/backends blocks are metadata the stdlib-only trust root ignores
structurally — records carrying them still verify.
"""
import random

from alpha2.corpus.schema import (
    build_record,
    make_backends,
    make_reproduction,
    provenance_seed,
    reproduction_kind_for_method,
)
from alpha2.corpus.verifier import verify_chi_witness, verify_model_record
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.witness import extract_witness

D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]
D3_INTERIM_MODEL = [
    [2, 20], [4, 7], [8, 18], [9, 13], [12, 27], [16, 22], [17, 24], [19, 29],
    [26, 28], [0], [1], [3], [10], [11], [21], [23],
]


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _seed_record(seed, model, method, omega_G=None):
    n = 31
    adj, _ = triangle_free_process(n, random.Random(seed))
    M, U, nu = extract_witness(adj, n)
    return build_record(
        provenance=provenance_seed(
            "triangle_free_process_complement", n, seed,
            "Bohman uniform triangle-free process",
        ),
        H_edges=_h_edges(adj, n),
        nu_H=nu,
        chi_G=n - nu,
        omega_G=omega_G,
        model_branch_sets=model,
        matching_M=M,
        tutte_berge_U=U,
        method=method,
    )


def test_heuristic_record_is_byte_exact_with_null_solvers():
    rec = _seed_record(1, D2_MODEL, "heuristic")
    repro = rec["reproduction"]
    assert repro["kind"] == "byte_exact"
    assert repro["canonical_platform"] == "linux-x86_64"
    assert repro["seed"] == 1

    b = rec["backends"]
    assert b["python"] == "3.12.13"
    assert b["networkx"] == "3.6.1"
    assert b["pulp"] is None
    assert b["cbc"] is None
    assert b["ortools"] is None
    assert isinstance(b["platform"]["cbc_under_rosetta"], bool)
    assert isinstance(b["platform"]["system"], str)
    assert isinstance(b["platform"]["machine"], str)

    # The reproduction/backends blocks do not disturb the trust root.
    assert verify_model_record(rec) == 16
    assert verify_chi_witness(rec) is True


def test_exact_ilp_record_is_semantic_with_solver_stamps():
    rec = _seed_record(137, D3_INTERIM_MODEL, "exact ILP (CBC): had_2(G)=17", omega_G=14)
    repro = rec["reproduction"]
    assert repro["kind"] == "semantic"
    assert repro["canonical_platform"] == "linux-x86_64"

    b = rec["backends"]
    assert b["pulp"] == "3.3.2"
    assert b["cbc"] is not None  # CBC backend stamped for the exact-ILP method
    assert b["ortools"] is None
    assert isinstance(b["platform"]["cbc_under_rosetta"], bool)
    assert "exact ILP (CBC)" in rec["method"]

    assert verify_model_record(rec) == 16
    assert verify_chi_witness(rec) is True


def test_reproduction_kind_dispatch():
    assert reproduction_kind_for_method("heuristic") == "byte_exact"
    assert reproduction_kind_for_method("exact ILP (CBC): had_2(G)=17") == "semantic"
    assert reproduction_kind_for_method("exact CP-SAT") == "semantic"


def test_canonical_platform_always_linux_x86_64():
    for method in ("heuristic", "exact ILP (CBC): had_2(G)=17", "exact CP-SAT"):
        assert make_reproduction(method, seed=1)["canonical_platform"] == "linux-x86_64"


def test_cp_sat_stamps_ortools_not_pulp():
    b = make_backends("exact CP-SAT")
    assert b["ortools"] == "9.15.6755"
    assert b["pulp"] is None
    assert b["cbc"] is None
