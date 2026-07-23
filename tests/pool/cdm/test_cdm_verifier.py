"""Single-perturbation mutant suite for the CDM trust leg `verify_cdm_witness`.

Mirrors `tests/test_verifier_mutants.py`: one KNOWN-GOOD CDM record (the
`valid_cdm_record` fixture — G = C5, H = complement(C5), M = [(0,1),(2,3)]) that
`verify_cdm_witness` MUST accept, then one test per single mutation asserting a
`VerificationError`. The CDM leg is NOT `verify_model_record` (RESEARCH anti-pattern:
a connected dominating matching is not a K_χ branch-set family) — it has its own
checks: non-empty M; M a matching; M connected (every edge-pair V-adjacent in G);
M dominating (every uncovered vertex adjacent to ≥1 endpoint of each M-edge); each
M-pair a G-edge (not an H-edge); H_edges_sha256 integrity.

All imports of `alpha2.pool.cdm.verifier` are FUNCTION-LOCAL so `--collect-only`
succeeds while the bodies error RED until 07-02/07-03.
"""
import hashlib
import json

import pytest


def _sha(h_edges):
    """Canonical H_edges sha256 — mirrors `corpus/schema.h_edges_sha256` (stdlib)."""
    canon = json.dumps(
        sorted([min(a, b), max(a, b)] for a, b in h_edges), separators=(",", ":")
    )
    return hashlib.sha256(canon.encode()).hexdigest()


# --- sanity: the good record is genuinely accepted --------------------------

def test_good_record_passes(valid_cdm_record):
    from alpha2.pool.cdm.verifier import verify_cdm_witness  # RED until 07-03

    assert verify_cdm_witness(valid_cdm_record)  # truthy (True or |M|)


# --- six adversarial mutants: each MUST raise -------------------------------

def test_mutant_a_empty_matching(valid_cdm_record):
    """(a) Empty M — a CDM must be NON-empty."""
    from alpha2.pool.cdm.verifier import VerificationError, verify_cdm_witness

    valid_cdm_record["matching_M"] = []
    with pytest.raises(VerificationError):
        verify_cdm_witness(valid_cdm_record)


def test_mutant_b_not_a_matching_shared_vertex(valid_cdm_record):
    """(b) Two M-edges share vertex 1 — not a matching."""
    from alpha2.pool.cdm.verifier import VerificationError, verify_cdm_witness

    # (0,1) and (1,2) are both G-edges of C5 but share vertex 1.
    valid_cdm_record["matching_M"] = [[0, 1], [1, 2]]
    with pytest.raises(VerificationError):
        verify_cdm_witness(valid_cdm_record)


def test_mutant_c_not_connected(valid_cdm_record):
    """(c) M = two disjoint V-non-adjacent G-edges — not connected.

    C5 is too small to host a disconnected 2-edge matching (all disjoint edge
    pairs are V-adjacent), so this mutant uses a targeted G = K_2 ⊔ K_2 record
    (H = C4 = K_{2,2}) whose sha256 is correct — the CONNECTED leg is what fires,
    not the integrity leg.
    """
    from alpha2.pool.cdm.verifier import VerificationError, verify_cdm_witness

    h_edges = [[0, 2], [0, 3], [1, 2], [1, 3]]  # H = K_{2,2}; G = K_2 ⊔ K_2
    rec = {
        "provenance": {"kind": "graph6", "family": "mtf_complement", "n": 4, "graph6": "C]"},
        "H_edges": h_edges,
        "H_edges_sha256": _sha(h_edges),
        # (0,1) and (2,3) are G-edges (disjoint cliques) but V-non-adjacent in G.
        "matching_M": [[0, 1], [2, 3]],
        "invariants": {"n": 4, "complement_connected": False, "cdm": True},
        "verified": True,
        "method": "cdm",
    }
    with pytest.raises(VerificationError):
        verify_cdm_witness(rec)


def test_mutant_d_not_dominating(valid_cdm_record):
    """(d) M = [(0,1)] leaves vertex 3 uncovered AND non-adjacent — not dominating."""
    from alpha2.pool.cdm.verifier import VerificationError, verify_cdm_witness

    # In C5, vertex 3's neighbours are {2,4}; it is adjacent to neither 0 nor 1.
    valid_cdm_record["matching_M"] = [[0, 1]]
    with pytest.raises(VerificationError):
        verify_cdm_witness(valid_cdm_record)


def test_mutant_e_h_edge_not_g_edge(valid_cdm_record):
    """(e) A size-2 M-set that is an H-edge (non-edge of G), not a G-edge."""
    from alpha2.pool.cdm.verifier import VerificationError, verify_cdm_witness

    # (0,2) is an H-edge of complement(C5) (0 and 2 non-adjacent in G); (3,4) is a
    # genuine G-edge — a matching, but (0,2) is not a G-edge.
    valid_cdm_record["matching_M"] = [[0, 2], [3, 4]]
    with pytest.raises(VerificationError):
        verify_cdm_witness(valid_cdm_record)


def test_mutant_f_sha256_mismatch(valid_cdm_record):
    """(f) Corrupt H_edges_sha256 — the integrity gate must refuse."""
    from alpha2.pool.cdm.verifier import VerificationError, verify_cdm_witness

    valid_cdm_record["H_edges_sha256"] = "0" * 64
    with pytest.raises(VerificationError):
        verify_cdm_witness(valid_cdm_record)
