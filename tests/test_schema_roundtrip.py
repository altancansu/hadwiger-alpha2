"""Schema v1 round-trip proof (VRF-02).

Builds witness-complete schema-v1 records for the two real exemplars (Appendix
D.2 heuristic K16 model; Appendix D.3 seed-137 *interim* K16 model) plus two
synthetic shapes (kind=params, kind=graph6), and proves:

  * json.dumps -> json.loads is a deep-field-equality round-trip (no tuples leak);
  * the frozen canonical H_edges sha256 matches the Phase-1 golden for D.2;
  * the trust-root verifier ACCEPTS every record the schema builds
    (verify_model_record + verify_chi_witness);
  * the FULL had_2 family is stored (len == had_2, never fam[:chi]);
  * all three provenance shapes validate, and a missing discriminator raises.

Note: seed-137's TRUE 17-set had_2 family requires the CBC ILP (Phase 4). Phase 2
round-trips the 16-set K16 interim model shown in Appendix D.3.
"""
import json
import random

import pytest

from alpha2.corpus.schema import (
    SCHEMA_VERSION,
    build_record,
    provenance_graph6,
    provenance_params,
    provenance_seed,
    validate_provenance,
)
from alpha2.corpus.verifier import VerificationError, verify_chi_witness, verify_model_record
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.witness import extract_witness

# D.2 golden canonical H_edges sha256 (frozen Phase 1).
D2_GOLDEN = "3c953d9029ea09463ec838b670aaec8619f1018c79ee89e26fbcea7b2beb41e2"

# Stored Appendix D.2 K16 model (heuristic).
D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]

# Stored Appendix D.3 seed-137 INTERIM K16 model (9 pairs + 7 singletons).
# The true 17-set had_2 family is produced in Phase 4 (CBC ILP).
D3_INTERIM_MODEL = [
    [2, 20], [4, 7], [8, 18], [9, 13], [12, 27], [16, 22], [17, 24], [19, 29],
    [26, 28], [0], [1], [3], [10], [11], [21], [23],
]


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


def _seed_record(seed, model, method, omega_G=None):
    n = 31
    adj, _ = triangle_free_process(n, random.Random(seed))
    H_edges = _h_edges(adj, n)
    M, U, nu = extract_witness(adj, n)
    return build_record(
        provenance=provenance_seed(
            "triangle_free_process_complement", n, seed,
            "Bohman uniform triangle-free process",
        ),
        H_edges=H_edges,
        nu_H=nu,
        chi_G=n - nu,
        omega_G=omega_G,
        model_branch_sets=model,
        matching_M=M,
        tutte_berge_U=U,
        method=method,
    )


def _synthetic_empty_h(provenance):
    """A tiny fully verifiable record: H has no edges => G is complete K5.

    nu=0, chi=5, model = 5 singletons (all pairwise G-adjacent), M=[], U=[].
    """
    n = 5
    return build_record(
        provenance=provenance,
        H_edges=[],
        nu_H=0,
        chi_G=5,
        model_branch_sets=[[0], [1], [2], [3], [4]],
        matching_M=[],
        tutte_berge_U=[],
        method="heuristic",
    )


def test_d2_roundtrips_and_verifies():
    rec = _seed_record(1, D2_MODEL, "heuristic")
    assert rec["schema_version"] == SCHEMA_VERSION == 1
    assert rec["provenance"]["kind"] == "seed"
    assert rec["H_edges_sha256"] == D2_GOLDEN

    rt = json.loads(json.dumps(rec))
    assert rt == rec  # deep field-equality: no tuples leaked through

    assert verify_model_record(rt) == 16
    assert verify_chi_witness(rt) is True

    # FULL family: len == had_2 == 16, and NOT fam[:chi] truncation.
    assert len(rec["model_branch_sets"]) == 16
    assert rec["invariants"]["had_2"] == 16
    assert rec["invariants"]["chi_G"] == 16


def test_d3_interim_roundtrips_and_verifies():
    rec = _seed_record(
        137, D3_INTERIM_MODEL, "exact ILP (CBC): had_2(G)=17", omega_G=14,
    )
    rt = json.loads(json.dumps(rec))
    assert rt == rec
    assert verify_model_record(rt) == 16
    assert verify_chi_witness(rt) is True
    assert rec["invariants"]["omega_G"] == 14
    # Interim: the stored family is the 16-set K16 model (true 17-set is Phase 4).
    assert len(rec["model_branch_sets"]) == 16
    assert rec["invariants"]["had_2"] == 16
    assert "had_2(G)=17" in rec["method"]


def test_synthetic_params_shape_validates():
    prov = provenance_params(
        "cayley_maximal_sumfree_Zp", 5, {"p": 5, "connection_set": [1, 4]},
    )
    assert validate_provenance(prov) is True
    rec = _synthetic_empty_h(prov)
    rt = json.loads(json.dumps(rec))
    assert rt == rec
    assert rec["provenance"]["kind"] == "params"
    assert verify_model_record(rt) == 5
    assert verify_chi_witness(rt) is True


def test_synthetic_graph6_shape_validates():
    prov = provenance_graph6("nauty_geng", 5, "D??")
    assert validate_provenance(prov) is True
    rec = _synthetic_empty_h(prov)
    rt = json.loads(json.dumps(rec))
    assert rt == rec
    assert rec["provenance"]["kind"] == "graph6"
    assert verify_model_record(rt) == 5


def test_params_kind_missing_params_raises():
    with pytest.raises((ValueError, VerificationError)):
        validate_provenance({"kind": "params", "family": "x", "n": 5})


def test_graph6_kind_missing_graph6_raises():
    with pytest.raises((ValueError, VerificationError)):
        validate_provenance({"kind": "graph6", "family": "x", "n": 5})


def test_seed_kind_missing_seed_raises():
    with pytest.raises((ValueError, VerificationError)):
        validate_provenance({"kind": "seed", "family": "x", "n": 5, "process": "p"})


def test_seed_kind_missing_process_raises():
    # WR-04: the documented seed-provenance shape is {kind, family, n, seed, process}.
    # A seed record without `process` is a rejected input, not a silent pass.
    with pytest.raises((ValueError, VerificationError)):
        validate_provenance({"kind": "seed", "family": "f", "n": 5, "seed": 1})


def test_short_family_refused_never_truncated():
    # A family shorter than chi must RAISE (no fam[:chi], no silent truncation).
    with pytest.raises((ValueError, VerificationError)):
        build_record(
            provenance=provenance_seed("f", 5, 1, "p"),
            H_edges=[],
            nu_H=0,
            chi_G=5,
            model_branch_sets=[[0], [1]],  # len 2 < chi 5
            matching_M=[],
            tutte_berge_U=[],
            method="heuristic",
        )
