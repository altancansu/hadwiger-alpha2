"""Shared CDM fixtures (POOL-0, Wave 0) — embedded-literal discipline.

Every fixture here is a self-contained in-file literal: NO import from any other
test module, NO import of the (not-yet-written) `alpha2.pool.cdm.*` proposer
modules, and NO import of 07-04's generator. Mirrors the embedded-literal shape of
`tests/test_cpsat_backend.py::_c5_adj` so a fixture bug can never share a code path
with the code under test.

Adjacency convention (LOCKED, RESEARCH §"Complement + α=2 sanity"):
`adj = list[set[int]]`, `adj[u]` = neighbours of u in G (the complement of the
graph6-decoded MTF graph H). `has_cdm`/`cdm_cpsat` consume G's adjacency.

The load-bearing fixture is `mtf_n_le_11_graph6`: the FULL connected
maximal-triangle-free set at every n≤11 (134 graphs; 61 at n=11). It is the ONLY
independent oracle that our A1 reading of "connected dominating matching" == CLWY's
CDM — dual-engine (DFS ≡ CP-SAT) agreement cannot catch a shared wrong A1 reading,
and a hand-picked handful can pass while the definition is subtly wrong on an
unsampled graph. Embedded as literals (generated once via `geng -ctq n | pickg -Z2`,
nauty 2.9.3) so the definition-regression gate can NEVER silently skip for want of
a `geng` binary.
"""
import copy

import pytest

# --------------------------------------------------------------------------- #
# Small α=2 graphs as in-file adjacency literals (adj[u] = N_G(u))
# --------------------------------------------------------------------------- #
_C5_G_ADJ = [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]  # G = C5: 0-1-2-3-4-0
# C5 is self-complementary and α(C5)=2. It HAS a connected dominating matching:
# M = {(0,1),(2,3)} — a matching (0,1,2,3 distinct); connected (1-2 ∈ G links the
# two edges); dominating (the lone outside vertex 4 is adjacent to 0 and to 3, so
# to each M-edge). This is the positive small witness for the verifier + DFS tests.
_C5_CDM_WITNESS = [(0, 1), (2, 3)]

# K_3 ⊔ K_3: two disjoint triangles. α=2 (one vertex per clique), G DISCONNECTED,
# complement H = K_{3,3} (complete bipartite, triangle-free, diameter 2 — an MTF
# graph in the `pickg -Z2` stream). Legitimately CDM-FAILS: an edge inside one
# clique cannot dominate the other clique, and cross-clique edges do not exist so
# no size-≥2 matching is connected. NOT a Hadwiger counterexample (Conjecture 10
# hypothesises *connected* G) — the disconnected-complement carve-out (Open Q1).
_K33_COMPLEMENT_G_ADJ = [{1, 2}, {0, 2}, {0, 1}, {4, 5}, {3, 5}, {3, 4}]
_K33_H_GRAPH6 = "EFz_"  # graph6 of H = K_{3,3} (complement of K_3 ⊔ K_3)

# --------------------------------------------------------------------------- #
# Hand-built VALID CDM certificate record (the verifier's known-good input)
# --------------------------------------------------------------------------- #
# Concretely: G = C5, H = complement(C5) (also a 5-cycle, triangle-free ⇒ α(G)=2).
# H_edges are H's canonical [min,max] pairs; matching_M is a matching of G-edges
# (NOT H-edges). The record shape mirrors the build_cdm_record contract:
# {provenance(graph6), H_edges, H_edges_sha256, matching_M, invariants{n,
#  complement_connected, cdm}}. sha256/graph6 computed from H via nauty+networkx.
_VALID_H_EDGES = [[0, 2], [0, 3], [1, 3], [1, 4], [2, 4]]
_VALID_H_GRAPH6 = "DUW"
_VALID_H_SHA256 = "f1b0f49a2d041764fea9ec52f8eef80bcb1b9b1b0d8eff4256867fd9b074068e"
_VALID_MATCHING_M = [[0, 1], [2, 3]]  # G-edges of C5; connected + dominating (vtx 4)


def _valid_cdm_record():
    return {
        "provenance": {
            "kind": "graph6",
            "family": "mtf_complement",
            "n": 5,
            "graph6": _VALID_H_GRAPH6,
        },
        "H_edges": [list(e) for e in _VALID_H_EDGES],
        "H_edges_sha256": _VALID_H_SHA256,
        "matching_M": [list(e) for e in _VALID_MATCHING_M],
        "invariants": {"n": 5, "complement_connected": True, "cdm": True},
        "verified": True,
        "method": "dfs reference + cp-sat cross-check (CDM)",
    }


# --------------------------------------------------------------------------- #
# The FULL connected n≤11 MTF set (graph6 of H; complement G has α=2)
# Generated via `geng -ctq n | pickg -Z2` (nauty 2.9.3). 134 graphs; 61 at n=11.
# --------------------------------------------------------------------------- #
_MTF_N_LE_11 = {
    3: ["BW"],
    4: ["CF", "C]"],
    5: ["D?{", "DFw", "DUW"],
    6: ["E?Bw", "E?~o", "ECxo", "EFz_"],
    7: ["F??Fw", "F?B~o", "F?bro", "F?o~_", "F?~v_", "FCxv?"],
    8: [
        "G???F{", "G??F~w", "G?AFrw", "G?B@~o", "G?B~vo",
        "G?bvbo", "G?rF`w", "G?o~f_", "G?~vf_", "GCrb`o",
    ],
    9: [
        "H????B~", "H???F~}", "H??CFx}", "H??E@~{", "H??F?~{", "H??F~z{",
        "H?AFvp{", "H?BEFo}", "H?B@~rw", "H?B@xzw", "H?B~vrw", "H?bF`xw",
        "H?bvbro", "H?rF`zo", "H?q`qjo", "H?o~fbo",
    ],
    10: [
        "I??????~w", "I????B~~o", "I???CB}^o", "I???E?~~_", "I???F?^~_",
        "I???F~}~_", "I??CFz{^_", "I??EEB{No", "I??E@~{~?", "I??E@{}~?",
        "I??FF?^~?", "I??F?~{~?", "I??F~z{~?", "I?AEFo}^?", "I?AF?~w^?",
        "I?AFvrw^?", "I?AFvp{^?", "I?BEFo}}?", "I?BD@xY}?", "I?B@hzI}?",
        "I?B@~rw}?", "I?B@xzw}?", "I?BfFBwFo", "I?B~vrw}?", "I?`FBqsF_",
        "I?bF`xw{?", "I?bF`xw]?", "I?`cn@wFO", "I?rFf_{N?", "I?q`qjo{?",
        "ICOf@pSb?",
    ],
    11: [
        "J???????F~_", "J??????~~~?", "J????A?~r~?", "J????B?N~}?", "J????B_F~}?",
        "J????BoB~}?", "J????B~~v}?", "J???CB}~b}?", "J???EB?~`~?", "J???E?~~f{?",
        "J???E?~Nv{?", "J???FB_F~{?", "J???F?^~f{?", "J???F?^Fv{?", "J???F~}~f{?",
        "J??CEB{Nr{?", "J??CF?^^fw?", "J??CFz{~B{?", "J??CFz{^b{?", "J??EEB{Nvw?",
        "J??ED?}VVw?", "J??EF?}Fvw?", "J??ED`LNfw?", "J??E@c}rVw?", "J??E@~{~Fw?",
        "J??E@{}~Fw?", "J??E@{}Nfw?", "J??FFB_~?~?", "J??FF?^~Fw?", "J??FF?^Fvw?",
        "J??FCo]XVw?", "J??F?~{~Fw?", "J??F~z{~Fw?", "J?AAF?^^Ds?", "J?AAFo}^Ds?",
        "J?AEFrwNbw?", "J?AEFo}^Bw?", "J?AEAJw^@u?", "J?ABFAYFrw?", "J?ABCc]ZVo?",
        "J?ABCs]}Bw?", "J?AFF?^^Fo?", "J?AFCo]XVo?", "J?AF?~w}Bw?", "J?AFvrw^Fo?",
        "J?BEFo}}@{?", "J?BDB?{Ucq?", "J?BD@g]Qvo?", "J?BD@w{Ufo?", "J?BD@xY}Fo?",
        "J?BD?{{Ufo?", "J?BFF?{}?}?", "J?B@hzI}Fo?", "J?B@~rw}Fo?", "J?B@xzw}Fo?",
        "J?BfFBwFvo?", "J?`F?|wlF_?", "J?`F?|wlBo?", "J?bFF`wN?{?", "J?`cn@w]?y?",
        "JCOf@pSb?{?",
    ],
}


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def c5_g_adj():
    """G = C5 adjacency (α=2, HAS a connected dominating matching)."""
    return [set(s) for s in _C5_G_ADJ]


@pytest.fixture
def c5_cdm_witness():
    """The connected dominating matching M for G = C5: [(0,1),(2,3)]."""
    return [tuple(e) for e in _C5_CDM_WITNESS]


@pytest.fixture
def disjoint_cliques_g_adj():
    """G = K_3 ⊔ K_3 adjacency (α=2, DISCONNECTED, expected CDM-FAIL)."""
    return [set(s) for s in _K33_COMPLEMENT_G_ADJ]


@pytest.fixture
def disjoint_cliques_h_graph6():
    """graph6 of H = K_{3,3} (complement of K_3 ⊔ K_3; disconnected complement)."""
    return _K33_H_GRAPH6


@pytest.fixture
def valid_cdm_record():
    """A hand-built VALID CDM certificate record (fresh deep copy per test).

    `verify_cdm_witness` MUST accept this record (return truthy). The verifier
    mutant suite perturbs a single field of a copy and asserts a raise, so each
    request returns an independent deep copy that tests may mutate freely.
    """
    return copy.deepcopy(_valid_cdm_record())


@pytest.fixture
def mtf_n_le_11_graph6():
    """The FULL connected MTF set at every n≤11 as {n: [graph6, ...]} (134 graphs).

    Self-contained embedded literals — the definition-regression gate never skips.
    Returns a fresh copy so a test cannot corrupt the shared oracle.
    """
    return {n: list(gs) for n, gs in _MTF_N_LE_11.items()}
