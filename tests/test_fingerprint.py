"""Two-tier reproduction fingerprint for the pinned-env verbatim port.

Tier 1 (hard, version-proof):
  - test_invariants:            n=31 s=1 -> m/nu/chi/tf/maxTF match Appendix D.2 (the doc).
  - test_golden_hash:           regenerated canonical H_edges sha256 == the frozen golden
                                (loaded FROM data/manifests/fingerprint.json, never a 2nd literal).
  - test_stored_model_reverifies: the stored Appendix D.2 K16 model re-verifies against a
                                freshly regenerated H (witness re-verification; no search replay).

Tier 2 (soft, pinned-interpreter):
  - test_heuristic_reproduces:  solve returns *a* verifying K16 model (CI-safe; decoupled from
                                heuristic fragility).
  - test_heuristic_matches_d2_exact_pinned_env: on CPython 3.12.13 the heuristic reproduces the
                                D.2 model EXACTLY under the single-RNG contract.

The invariants 131 / 15 / 16 (and seed-137 |E(H)|=177) are sourced from Appendix D (the doc,
NOT our generated output) and asserted independently so a porting bug cannot self-certify: the
golden manifest was frozen only after these doc-derived invariants passed.
"""
import hashlib
import json
import random
from pathlib import Path

# Doc-derived invariants (Appendix D.2). Do NOT derive these from generated output.
EXPECTED_M = 131   # |E(H)|
EXPECTED_NU = 15   # matching_number_H (nu)
EXPECTED_CHI = 16  # chi_G = n - nu

# Stored Appendix D.2 K16 model_branch_sets (external authority; verifies against regenerated H).
D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "data" / "manifests" / "fingerprint.json"


def canonical_h_edges_sha256(adj, n):
    """Canonical H_edges hash (research Validation Architecture).

    edges = sorted [min(u,v), max(u,v)] over u<v; compact JSON; sha256 hexdigest.
    """
    edges = sorted([min(u, v), max(u, v)] for u in range(n) for v in adj[u] if u < v)
    canonical = json.dumps(edges, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _load_manifest():
    with open(MANIFEST_PATH) as fh:
        return json.load(fh)


def _regen(n, seed):
    from alpha2.generators.tfp import triangle_free_process
    return triangle_free_process(n, random.Random(seed))


def test_invariants():
    from alpha2.generators.tfp import is_triangle_free, is_edge_maximal_tf
    from alpha2.invariants.matching import matching_number

    n = 31
    adj, m = _regen(n, 1)

    assert m == EXPECTED_M, ("m", m)
    assert matching_number(adj, n) == EXPECTED_NU, ("nu", matching_number(adj, n))
    assert n - matching_number(adj, n) == EXPECTED_CHI, ("chi", n - matching_number(adj, n))
    assert is_triangle_free(adj, n) is True
    assert is_edge_maximal_tf(adj, n) is True


def test_golden_hash():
    """Byte-exact reproduction tripwire (ENV-03): regenerated sha256 == frozen golden."""
    n = 31
    adj, m = _regen(n, 1)
    # Independent doc-invariant gate: the hash is only trusted if the invariants hold.
    assert m == EXPECTED_M, ("m", m)

    got = canonical_h_edges_sha256(adj, n)
    frozen = _load_manifest()["tfp:n31:s1"]["h_edges_sha256"]
    assert got == frozen, ("h_edges_sha256 drift", got, frozen)


def test_stored_model_reverifies():
    """Version-proof witness check (ENV-02): stored D.2 model re-verifies against fresh H.

    This never replays the search — it re-verifies the external-authority witness.
    """
    from alpha2.verify.model import verify_model

    n = 31
    adj, _ = _regen(n, 1)
    assert verify_model(D2_MODEL, adj, n, 16) is True


def test_heuristic_reproduces():
    """Soft tier (CI-safe): solve returns A verifying K16 model (single-RNG contract v1)."""
    from alpha2.generators.tfp import triangle_free_process
    from alpha2.search.heuristic import solve
    from alpha2.verify.model import verify_model

    n = 31
    rng = random.Random(1)              # single-RNG contract: one rng feeds generation THEN search
    adj, _ = triangle_free_process(n, rng)
    sets, *_ = solve(adj, n, 16, rng)
    assert sets is not None, "heuristic returned no model"
    assert verify_model(sets, adj, n, 16) is True


def test_heuristic_matches_d2_exact_pinned_env():
    """Strict pinned-interpreter tier: solve reproduces D.2 EXACTLY on CPython 3.12.13.

    Distinct, greppable function name makes the pinned-env-only assertion unambiguous.
    Requires the single-RNG contract v1 (one random.Random(1) feeds triangle_free_process
    THEN solve, in that order) — this is what byte-exactly reproduces Appendix D.2.
    """
    from alpha2.generators.tfp import triangle_free_process
    from alpha2.search.heuristic import solve

    n = 31
    rng = random.Random(1)
    adj, _ = triangle_free_process(n, rng)
    sets, *_ = solve(adj, n, 16, rng)
    assert sets is not None, "heuristic returned no model"
    assert [list(s) for s in sets] == D2_MODEL, ("did not reproduce D.2 exactly", sets)
