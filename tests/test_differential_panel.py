"""Dual-backend CI agreement panel (EXACT-04 / EXACT-03, SC1 capstone).

The phase-5 anchor: prove the CP-SAT backend AGREES with CBC on every shared
CI-panel instance — both `PROVED_OPTIMAL`, equal had_2, both extracted families
independently verified — and that every agreement is licensed through the SOLE
gate (`differential_verdict`), never a single backend's value.

Two tiers:

  * FAST (every-commit, ms): C5 (had_2=3), empty-H n=5 (had_2=n=5), and a batch
    of tiny triangle-free-process instances (n in {6,7,8}, seeds 1/2). Each TFP
    instance is regenerated from the frozen generator and gated on its pinned
    (m, nu, chi) invariants BEFORE any solve is trusted (the R2 discipline — a
    drifted generator must never self-certify through a solver run). Both
    backends solve had_2 optimize; the agreement is licensed through
    `differential_verdict(cbc, cpsat, chi)` == "AGREED_KILL" (every panel
    instance has had_2 >= chi); BOTH families are routed through the frozen
    trust root (`verify_certificate` — the ONLY truth-conferring step).

  * SLOW (`@pytest.mark.slow`, joins the release gate via -m slow): the seed-137
    (n=31, m=177, chi=16) dual-backend optimality proof — CBC AND CP-SAT both
    reach `PROVED_OPTIMAL` had_2 = 17 (CP-SAT in DETERMINISTIC recorded mode:
    num_workers=1 + a pinned random_seed, both baked into cpsat.py), the
    agreement is licensed through the gate (17 >= 16 -> AGREED_KILL), and BOTH
    17-set families independently pass the trust root. This closes SC1
    end-to-end: the CP-SAT engine proves the 296-lineage anchor and AGREES with
    the CBC reference at had_2 = 17.

Open-Q3 resolution (recorded for audit): the committed seed-137 corpus record is
NOT upgraded to the 17-set family here. The dual-backend proof lives IN MEMORY
(like the Phase-4 seed-137 regression) — the frozen corpus / repro / R1 /
manifest stay byte-untouched; the only data/ touch is one read-only load for the
metamorphic anchor. The corpus upgrade remains a deferred, deliberate freeze
amendment (first consumer: the Phase-11 falsification harness).

Embedded-literal discipline (test_corpus_r1 / test_seed137_regression precedent):
adjacencies and the pinned regeneration invariants are in-file literals; no
cross-test imports. Trust-root / exact-accessor calls are made OUTSIDE any test
truth-expression — call, bind k, then compare — so no verification is an
optimization-strippable statement. The recorded seed-137 contract is SEMANTIC
(value/status/bound/verifiability), NEVER which 17-set family a backend returned
(ENV-05 / Assumption A1).
"""
import json
import random

import pytest

from alpha2 import paths
from alpha2.corpus.schema import build_record, provenance_params, provenance_seed
from alpha2.corpus.verifier import verify_certificate
from alpha2.generators.tfp import triangle_free_process
from alpha2.invariants.matching import matching_number
from alpha2.invariants.witness import extract_witness
from alpha2.solvers.backend import get_backend
from alpha2.solvers.differential import (
    CriticalDisagreement,
    differential_verdict,
)
from alpha2.solvers.result import ExactOutcome, SolveParams, Status


# --------------------------------------------------------------------------- #
# In-file instance literals
# --------------------------------------------------------------------------- #
def _c5_adj():
    """H = C5: edges 0-1, 1-2, 2-3, 3-4, 4-0 (n=5, nu=2, chi=3, had_2=3)."""
    return [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {3, 0}]


def _empty_adj(n):
    """H with no edges: G = K_n (nu=0, chi=n, had_2=n via n singletons)."""
    return [set() for _ in range(n)]


def _h_edges(adj, n):
    return sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)


# Pinned tiny-TFP regeneration invariants (embedded literals; live-verified in
# the pinned .venv). Each row: (n, seed) -> (m, nu, chi, had_2). Every instance
# has had_2 >= chi, so every panel agreement is AGREED_KILL through the gate.
_TFP_PANEL = {
    (6, 1): {"m": 9, "nu": 3, "chi": 3, "had_2": 3},
    (6, 2): {"m": 7, "nu": 3, "chi": 3, "had_2": 4},
    (7, 1): {"m": 9, "nu": 3, "chi": 4, "had_2": 4},
    (7, 2): {"m": 12, "nu": 3, "chi": 4, "had_2": 4},
    (8, 1): {"m": 13, "nu": 4, "chi": 4, "had_2": 4},
    (8, 2): {"m": 13, "nu": 4, "chi": 4, "had_2": 5},
}


def _verify_family(adj, n, nu, chi, family, method):
    """Route a solver family (UNTRUSTED proposal) through the frozen trust root.

    Builds an IN-MEMORY schema-v1 record and calls `verify_certificate`; returns
    the trust-root-conferred k. The call is made OUTSIDE any truth-expression.
    No data/ path is written — the record lives and dies in memory.
    """
    M, U, _nu2 = extract_witness(adj, n)
    rec = build_record(
        provenance=provenance_params("synthetic_panel", n, {"n": n}),
        H_edges=_h_edges(adj, n),
        nu_H=nu,
        chi_G=chi,
        model_branch_sets=[list(s) for s in family],  # FULL family, never truncated
        matching_M=M,
        tutte_berge_U=U,
        method=method,
    )
    return verify_certificate(rec)  # trust root arbitrates; raises on any defect


def _agree_optimize_both(adj, n, nu, chi, expected_had_2):
    """One panel leg: both backends optimize, licensed through the gate, both
    families verified. Returns nothing — every check is an assertion here."""
    cbc = get_backend("cbc").solve_had2(adj, n, mode="optimize")
    cpsat = get_backend("cpsat").solve_had2(adj, n, mode="optimize")

    # Both engines must PROVE optimality (never an incumbent read as exact).
    assert cbc.status is Status.PROVED_OPTIMAL, cbc.status
    assert cpsat.status is Status.PROVED_OPTIMAL, cpsat.status
    assert cbc.exact_value() == expected_had_2, cbc.exact_value()
    assert cpsat.exact_value() == expected_had_2, cpsat.exact_value()
    assert cbc.bound == expected_had_2
    assert cpsat.bound == expected_had_2

    # The SOLE licenser: no backend value is trusted without its pair. Every
    # panel instance has had_2 >= chi, so the verdict is AGREED_KILL.
    verdict = differential_verdict(cbc, cpsat, chi)
    assert verdict == "AGREED_KILL", verdict

    # BOTH families are UNTRUSTED proposals until the frozen trust root confers
    # truth — verify each independently (call, bind, then compare).
    k_cbc = _verify_family(
        adj, n, nu, chi, cbc.family, f"exact ILP (CBC): had_2(G)={expected_had_2}"
    )
    k_cpsat = _verify_family(
        adj, n, nu, chi, cpsat.family, f"exact CP-SAT: had_2(G)={expected_had_2}"
    )
    assert k_cbc == expected_had_2, k_cbc
    assert k_cpsat == expected_had_2, k_cpsat


# --------------------------------------------------------------------------- #
# FAST tier — dual-backend agreement on the tiny closed-form + TFP instances
# --------------------------------------------------------------------------- #
def test_agreement_panel_fast():
    """Every shared tiny instance: CBC == CP-SAT, PROVED_OPTIMAL, both families
    verified, agreement licensed ONLY through the differential gate."""
    # C5: had_2 = chi = 3.
    _agree_optimize_both(_c5_adj(), 5, nu=2, chi=3, expected_had_2=3)

    # empty-H at n=5 (G = K5): had_2 = n = 5.
    _agree_optimize_both(_empty_adj(5), 5, nu=0, chi=5, expected_had_2=5)

    # tiny TFP battery: regenerate, gate invariants BEFORE any solve (R2), agree.
    for (n, seed), inv in _TFP_PANEL.items():
        adj, m = triangle_free_process(n, random.Random(seed))
        # Regeneration gate: a drifted generator fails HERE, before any solve.
        assert m == inv["m"], (n, seed, m)
        nu = matching_number(adj, n)
        assert nu == inv["nu"], (n, seed, nu)
        chi = n - nu
        assert chi == inv["chi"], (n, seed, chi)
        _agree_optimize_both(adj, n, nu=nu, chi=chi, expected_had_2=inv["had_2"])


# --------------------------------------------------------------------------- #
# Negative control — a disagreement would HALT the panel, never skip
# --------------------------------------------------------------------------- #
def _proved(value, family=((0, 1),)):
    """A hand-built PROVED_OPTIMAL outcome (value == bound; non-None family)."""
    return ExactOutcome(
        problem="had2",
        mode="optimize",
        status=Status.PROVED_OPTIMAL,
        value=value,
        bound=value,
        bound_source="definition",
        family=family,
        backend="synthetic",
        backend_version="test",
    )


def test_backends_disagreement_would_halt():
    """If the two backends returned UNEQUAL proven optima for one panel instance,
    the gate quarantines + halts (release-blocking) — it never picks a winner and
    never skips. Constructed unequal proven optima prove the panel would halt."""
    with pytest.raises(CriticalDisagreement) as exc:
        differential_verdict(_proved(3), _proved(4), chi=3)
    msg = str(exc.value)
    assert "3" in msg and "4" in msg  # both values surfaced for the quarantine log


# --------------------------------------------------------------------------- #
# SLOW tier — the seed-137 = 17 dual-backend optimality proof (SC1 capstone)
# --------------------------------------------------------------------------- #
def _find_stored_seed_record(n, seed):
    """The single committed seed-kind (n, seed) record — READ-ONLY corpus load.

    Embedded locally (no cross-test import), per the embedded-literal discipline.
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
def test_seed137_dual_backend():
    """SC1 end-to-end: CBC AND CP-SAT both PROVE had_2(seed-137) = 17 optimal,
    agree through the gate, and both 17-set families verify. CP-SAT runs in
    DETERMINISTIC recorded mode (num_workers=1 + pinned seed, baked into
    cpsat.py). Slow tier: CBC ~149 s single-thread + CP-SAT time (recorded in
    05-07-SUMMARY.md). No corpus write — the record lives in memory."""
    n = 31

    # ---- Regeneration gates (R2 discipline): a drifted generator fails HERE, ----
    # ---- before any solve is trusted or even attempted.                      ----
    rng = random.Random(137)
    adj, m = triangle_free_process(n, rng)
    assert m == 177, m
    nu = matching_number(adj, n)
    assert nu == 15, nu
    chi = n - nu
    assert chi == 16, chi

    # ---- The dual-backend optimality proof. CBC ~149 s (600 s headroom); ----
    # ---- CP-SAT deterministic single-worker (generous headroom — the      ----
    # ---- measured wall time is recorded in 05-07-SUMMARY.md).             ----
    cbc = get_backend("cbc").solve_had2(
        adj, n, mode="optimize", params=SolveParams(time_limit_s=600)
    )
    cpsat = get_backend("cpsat").solve_had2(
        adj, n, mode="optimize", params=SolveParams(time_limit_s=1800)
    )

    # ---- LOCKED constants: value/status/bound/verifiability, never bytes. ----
    assert cbc.status is Status.PROVED_OPTIMAL, cbc.status
    assert cpsat.status is Status.PROVED_OPTIMAL, cpsat.status
    assert cbc.exact_value() == 17, cbc.exact_value()
    assert cpsat.exact_value() == 17, cpsat.exact_value()
    assert cbc.bound == 17
    assert cpsat.bound == 17
    assert len(cbc.family) == 17
    assert len(cpsat.family) == 17
    assert "2.10.3" in cbc.backend_version
    assert "ortools==" in cpsat.backend_version

    # ---- The SOLE licenser: 17 >= 16 -> AGREED_KILL (both proofs required). ----
    verdict = differential_verdict(cbc, cpsat, chi)
    assert verdict == "AGREED_KILL", verdict

    # ---- Trust root: BOTH 17-set families are UNTRUSTED proposals until the ----
    # ---- frozen verifier arbitrates. IN-MEMORY records only; no data/ write. ----
    k_cbc = _verify_family(adj, n, nu, chi, cbc.family, "exact ILP (CBC): had_2(G)=17")
    k_cpsat = _verify_family(adj, n, nu, chi, cpsat.family, "exact CP-SAT: had_2(G)=17")
    assert k_cbc == 17, k_cbc
    assert k_cpsat == 17, k_cpsat

    # ---- Metamorphic anchor (verifier trumps solver): the committed D.3     ----
    # ---- record stores a VERIFIED 16-set family; both engines' PROVED 17    ----
    # ---- exceed it (a proved value BELOW a stored verified family would be  ----
    # ---- a CRITICAL encoding bug). READ-ONLY load; no corpus write.         ----
    stored = _find_stored_seed_record(n, 137)
    stored_size = len(stored["model_branch_sets"])
    assert stored_size == 16, stored_size
    assert cbc.exact_value() == 17 > stored_size
    assert cpsat.exact_value() == 17 > stored_size
