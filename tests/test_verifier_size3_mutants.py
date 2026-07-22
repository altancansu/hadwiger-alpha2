"""Adversarial size-3 mutant suite for the widened trust root (EXACT-05).

Phase 5 widens `verify_model_record`'s size gate from {1,2} to {1,2,3}: a size-3
branch set is accepted ONLY when it is CONNECTED in G, i.e. >=2 of its 3 internal
pairs are G-edges (<=1 internal H-edge). This suite pins that contract
adversarially, mirroring `test_verifier_mutants.py`'s good_record/mutant idiom but
with small HAND-BUILT records (each embeds its own tiny H and computes the
canonical sha256 in-file, exactly as `test_verifier_dash_O` embeds `[[0,1]]`).

Graph fact (exact for 3 vertices): connected-in-G triple <=> >=2 internal G-edges
<=> <=1 internal H-edge. `adj` is H's adjacency; a G-edge {a,b} is `b not in adj[a]`.

Discipline: the size-<=2 legs of the verifier stay byte-unchanged — the last test
re-runs the frozen Phase-2 mutant suite (good_record() still returns k=16) to prove
the widening did not regress any size-<=2 behavior.
"""
import hashlib
import json

import pytest

from alpha2.corpus.verifier import VerificationError, verify_model_record
from tests import test_verifier_mutants as tvm


def _sha(edges):
    """Canonical sha256 over sorted [min,max] edges — matches verify_model_record."""
    return hashlib.sha256(
        json.dumps(edges, separators=(",", ":")).encode()
    ).hexdigest()


def make_record(n, chi, H_edges, model):
    """Build a schema-free record from a tiny hand-built H + branch-set model.

    H_edges is canonicalised (sorted [min,max]) and its sha256 stored, so the
    integrity check passes and the record fails (or passes) purely on the
    branch-set structure under test. verify_model_record reads only invariants.n
    and invariants.chi_G, so the other invariant fields are placeholders.
    """
    edges = sorted([min(a, b), max(a, b)] for a, b in H_edges)
    return {
        "H_edges": edges,
        "H_edges_sha256": _sha(edges),
        "invariants": {
            "n": n, "num_H_edges": len(edges), "nu_H": None,
            "chi_G": chi, "omega_G": None, "had_2": None,
        },
        "model_branch_sets": [list(s) for s in model],
    }


# --- ACCEPT: a connected triple verifies and returns k -----------------------

def test_accepts_connected_triple():
    """A size-3 branch set with exactly 1 internal H-edge (2 G-edges = connected
    in G), disjoint from a size-2 G-edge set and cross-adjacent to it, verifies
    and returns k = 2.

    n=6, H = {(1,2)}: triple {0,1,2} has G-edges (0,1),(0,2) and H-edge (1,2)
    -> 2 G-edges (a path 1-0-2 in G) -> connected. Pair {3,4} is a G-edge; every
    cross pair between the sets is a G-edge -> the two sets are adjacent in G.
    """
    rec = make_record(6, 2, [(1, 2)], [[0, 1, 2], [3, 4]])
    assert verify_model_record(rec) == 2


# --- REJECT: every malformed triple raises VerificationError -----------------

def test_rejects_disconnected_triple():
    """A triple with only 1 G-edge (2 internal H-edges) is disconnected in G -> raise.

    H = {(0,1),(1,2)}: among (0,1)H,(0,2)G,(1,2)H the triple has 1 G-edge < 2.
    """
    rec = make_record(3, 1, [(0, 1), (1, 2)], [[0, 1, 2]])
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_rejects_triple_zero_g_edges():
    """A fully-H triple (H-triangle, 0 G-edges) is disconnected in G -> raise.

    H = {(0,1),(0,2),(1,2)}: all three internal pairs are H-edges -> 0 G-edges.
    """
    rec = make_record(3, 1, [(0, 1), (0, 2), (1, 2)], [[0, 1, 2]])
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_rejects_missing_cross_adjacency():
    """A connected triple that is fully NON-adjacent in G to another set -> raise.

    n=4, H = {(1,2),(0,3),(1,3),(2,3)}: triple {0,1,2} is connected in G
    (G-edges (0,1),(0,2)) but every cross pair to singleton {3} is an H-edge, so
    the two sets are non-adjacent in G (_is_conflict True, size-agnostic, unchanged).
    """
    rec = make_record(4, 2, [(1, 2), (0, 3), (1, 3), (2, 3)], [[0, 1, 2], [3]])
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_rejects_size4_set():
    """A size-4 branch set still raises — the gate is exactly {1,2,3}."""
    rec = make_record(4, 1, [], [[0, 1, 2, 3]])
    with pytest.raises(VerificationError):
        verify_model_record(rec)


def test_rejects_aliased_vertex():
    """A triple reusing a vertex from another set -> disjointness violation -> raise."""
    rec = make_record(4, 2, [], [[0, 1, 2], [2, 3]])
    with pytest.raises(VerificationError):
        verify_model_record(rec)


# --- REGRESSION: the size-<=2 legs stay byte-unchanged -----------------------

def test_all_existing_size2_records_unchanged():
    """The frozen size-<=2 contract is unaffected by the widening.

    good_record() (the Appendix D.2 K16 model) still returns 16, and every
    Phase-2 mutant still raises (re-running the frozen assertions directly).
    """
    rec, _ = tvm.good_record()
    assert verify_model_record(rec) == 16
    tvm.test_mutant_a_overlapping_sets()
    tvm.test_mutant_b_h_edge_pair()
    tvm.test_mutant_c_missing_cross_adjacency()
    tvm.test_mutant_d_truncated_family()
    tvm.test_mutant_e_wrong_chi()
