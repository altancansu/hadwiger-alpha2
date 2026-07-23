"""Shared sum-free (POOL-1/POOL-2) fixtures — embedded-literal discipline.

Every fixture here is a self-contained in-file literal: NO import from any other
test module, and NO import of the (not-yet-written) `alpha2.pool.sumfree.*`
modules-under-test. Mirrors `tests/pool/cdm/conftest.py`'s embedded-literal shape so
a fixture bug can never share a code path with the code under test. The ONLY stdlib
touched is json/hashlib/copy for a self-contained sha256 over H_edges.

Adjacency / descriptor conventions (LOCKED, RESEARCH §"Group representation"):
  * Gamma is given by its INVARIANT FACTORS, e.g. Z_31 = (31,), Z_53 = (53,),
    Z_3 x Z_3 = (3, 3). Elements are integer tuples; the canonical vertex order is
    `itertools.product(*(range(d) for d in factors))`, so vertex i is the i-th such
    tuple (vertex 0 = the identity).
  * A descriptor is `{"invariant_factors": [...], "S": [element-tuple, ...]}`; the
    instance rebuilds FROM the descriptor, never from an RNG replay.
  * H = Cay(Gamma, S) is triangle-free (S symmetric sum-free) so G = complement(H)
    has alpha(G) = 2. `g(G) = (chi - had_k)/chi`, chi = n - nu(H).

The KILLED fixture is a brute-hand-built g<=0 instance whose K_chi minor is
hand-verifiable; the CANARY fixture pins the radioactive certificate-honesty rule
(Pitfall 1): a g>0 record may say ONLY "no K_chi minor with branch sets <=3 ... does
not prove had(G) ... queued for E3", NEVER "counterexample" / "had(G) <".
"""
import copy
import hashlib
import json

import pytest

# --------------------------------------------------------------------------- #
# (a) Invariant-factor tuples for the small-Gamma grid
# --------------------------------------------------------------------------- #
_Z_31 = (31,)          # 31 prime, 31 ≡ 1 (mod 3) -> max sum-free size (31-1)/3 = 10
_Z_53 = (53,)          # 53 ≡ 2 (mod 3) -> middle-interval max sum-free size 18
_Z_3x3 = (3, 3)        # tiny hand-checkable NON-cyclic abelian group, n = 9


# --------------------------------------------------------------------------- #
# self-contained sha256 over H_edges (matches the corpus canonical scheme:
# json.dumps(sorted [min,max] pairs, separators=(",",":")) then sha256).
# --------------------------------------------------------------------------- #
def _sha(h_edges):
    canon = json.dumps(
        sorted([min(a, b), max(a, b)] for a, b in h_edges), separators=(",", ":")
    )
    return hashlib.sha256(canon.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# (b) Hand-built VALID g<=0 KILLED record.
#
# Descriptor: Gamma = Z_5 = (5,), S = {(1,), (4,)} = ±1  (symmetric sum-free:
# 1+1=2, 1+4=0, 4+4=3 — none in S). H = Cay(Z_5, S) is the 5-cycle
# 0-1-2-3-4-0 (triangle-free), so G = complement(H) is the 5-cycle 0-2-4-1-3-0
# and alpha(G) = 2. nu(H) = 2 (max matching of C_5) => chi = 5 - 2 = 3.
#
# G has a hand-checkable K_3 minor with branch sets [[0], [2], [1, 3, 4]]:
#   G-edges = {02, 03, 13, 14, 24}
#   {1,3,4} is connected in G (1-3, 1-4); {0}-{2} via 0-2; {0}-{1,3,4} via 0-3;
#   {2}-{1,3,4} via 2-4. All three branch sets pairwise adjacent, max size 3 <= 3.
# So had_3 = 3 >= chi = 3 => g = (3 - 3)/3 = 0 <= 0: KILLED (packs).
# --------------------------------------------------------------------------- #
_KILLED_INVARIANT_FACTORS = [5]
_KILLED_S = [[1], [4]]
_KILLED_H_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]]   # Cay(Z_5, {1,4})
_KILLED_BRANCH_SETS = [[0], [2], [1, 3, 4]]                  # verified K_3 minor of G


def _killed_gscreen_record():
    chi = 3
    had_2 = 3
    had_3 = 3
    g = (chi - had_3) / chi          # 0.0 <= 0 -> KILLED
    return {
        "provenance": {
            "kind": "descriptor",
            "family": "sumfree_cayley",
            "tag": "random",
            "n": 5,
            "invariant_factors": list(_KILLED_INVARIANT_FACTORS),
            "S": [list(s) for s in _KILLED_S],
        },
        "H_edges": [list(e) for e in _KILLED_H_EDGES],
        "H_edges_sha256": _sha(_KILLED_H_EDGES),
        "chi": chi,
        "had_2": had_2,
        "had_3": had_3,
        "g": g,
        "model_branch_sets": [list(b) for b in _KILLED_BRANCH_SETS],
        "terminal_state": "KILLED",
        "certificate_statement": (
            "had_3 = 3 >= chi = 3; verified K_chi minor family of size 3 extracted "
            "(branch sets <=3); Hadwiger holds on this instance (packs); g = 0."
        ),
        "verified": True,
        "method": "heuristic K_chi HIT + trust-root verify (sumfree g-screen)",
    }


# --------------------------------------------------------------------------- #
# (c) Honesty CANARY record — a g>0 SHC_CANDIDATE (screen only). Its
# certificate_statement carries EXACTLY the honest literal and NONE of the
# radioactive strings. This is the fixture the certificate-honesty gate pins.
# (The numbers here are an illustrative screen outcome, not a real solve.)
# --------------------------------------------------------------------------- #
_CANARY_H_EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]]


def _honesty_canary_record():
    chi = 3
    had_3 = 2
    g = (chi - had_3) / chi          # > 0 -> SHC_CANDIDATE (screen, NOT a break)
    return {
        "provenance": {
            "kind": "descriptor",
            "family": "sumfree_cayley",
            "tag": "structured",
            "n": 5,
            "invariant_factors": [5],
            "S": [[1], [4]],
        },
        "H_edges": [list(e) for e in _CANARY_H_EDGES],
        "H_edges_sha256": _sha(_CANARY_H_EDGES),
        "chi": chi,
        "had_2": 2,
        "had_3": had_3,
        "g": g,
        "model_branch_sets": None,   # no K_chi family exists at branch sets <=3
        "terminal_state": "SHC_CANDIDATE",
        "certificate_statement": (
            "had_3 = 2 < chi = 3 (both backends PROVED_OPTIMAL); establishes only "
            "that there is no K_chi minor with branch sets <=3; this does not prove "
            "had(G) drops below chi (size->=4 branch sets are not excluded); "
            "queued for E3."
        ),
        "verified": True,
        "method": "dual-backend had_2->had_3 seagull Tier-1 PROVED_OPTIMAL (screen)",
    }


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def gamma_factors():
    """The small-Gamma grid as {label: invariant-factor tuple} (fresh copy)."""
    return {"Z_31": _Z_31, "Z_53": _Z_53, "Z_3xZ_3": _Z_3x3}


@pytest.fixture
def z31_factors():
    """Invariant factors of Z_31 = (31,) — max sum-free size 10 (Green-Ruzsa)."""
    return _Z_31


@pytest.fixture
def z53_factors():
    """Invariant factors of Z_53 = (53,) — middle-interval max sum-free size 18."""
    return _Z_53


@pytest.fixture
def z3x3_factors():
    """Invariant factors of the non-cyclic Z_3 x Z_3 = (3, 3), n = 9."""
    return _Z_3x3


@pytest.fixture
def valid_gscreen_record():
    """A hand-built VALID g<=0 KILLED g-screen record (fresh deep copy per test).

    The (future) `pool/sumfree` verifier MUST accept this record: chi = 3,
    had_3 = 3, g = 0, with a hand-verified K_3 minor family of G = complement of
    Cay(Z_5, {1,4}). Returned as an independent deep copy so mutant-perturbation
    tests may edit a single field freely.
    """
    return copy.deepcopy(_killed_gscreen_record())


@pytest.fixture
def honesty_canary_record():
    """A g>0 SHC_CANDIDATE record whose certificate_statement is honesty-clean.

    Says ONLY "no K_chi minor with branch sets <=3 ... does not prove had(G) ...
    queued for E3"; contains NEITHER "counterexample" NOR "had(G) <". Fresh deep
    copy per test.
    """
    return copy.deepcopy(_honesty_canary_record())
