"""DFS ≡ CP-SAT differential (POOL-0) — the release-blocking agreement gate.

The DFS reference `has_cdm` (trusted, solver-free) and the CP-SAT cross-check
`cdm_cpsat` (independent second engine, deterministic single-worker on UNSAT) must
return the SAME CDM verdict on every instance:

    (has_cdm(adj, n) is not None) == cdm_cpsat(adj, n)

>>> Any disagreement is RELEASE-BLOCKING: two independent engines cannot both be
>>> right about a decision. It quarantines the instance and halts the batch
>>> (mirrors solvers/differential.CriticalDisagreement). <<<

Small conftest fixtures run in the fast loop; the full n=12–14 batch is
`@pytest.mark.slow`, geng-gated, and res/mod-shardable for CI fan-out.

RED until 07-02 (`has_cdm`) + 07-04 (`cdm_cpsat`/`stream_mtf`); all imports of
`alpha2.pool.cdm.*` are function-local so `--collect-only` stays clean.
"""
import shutil

import networkx as nx
import pytest


def test_dfs_cpsat_agree_c5_has_cdm(c5_g_adj):
    """G = C5 (HAS CDM): DFS and CP-SAT agree it is feasible."""
    from alpha2.pool.cdm.cpsat import cdm_cpsat
    from alpha2.pool.cdm.reference import has_cdm

    adj, n = c5_g_adj, len(c5_g_adj)
    assert (has_cdm(adj, n) is not None) == cdm_cpsat(adj, n)


def test_dfs_cpsat_agree_disconnected_no_cdm(disjoint_cliques_g_adj):
    """G = K_3 ⊔ K_3 (NO CDM): DFS and CP-SAT agree it is infeasible."""
    from alpha2.pool.cdm.cpsat import cdm_cpsat
    from alpha2.pool.cdm.reference import has_cdm

    adj, n = disjoint_cliques_g_adj, len(disjoint_cliques_g_adj)
    assert (has_cdm(adj, n) is not None) == cdm_cpsat(adj, n)


@pytest.mark.slow
@pytest.mark.parametrize("n", [12, 13, 14])
def test_dfs_cpsat_agree_full_batch(n):
    """DFS ≡ CP-SAT on the full MTF frontier at n (res/mod-shardable in CI)."""
    if shutil.which("geng") is None or shutil.which("pickg") is None:
        pytest.skip("nauty geng/pickg not on PATH")
    from alpha2.pool.cdm.cpsat import cdm_cpsat
    from alpha2.pool.cdm.generate import stream_mtf
    from alpha2.pool.cdm.reference import has_cdm

    for _i, g6, _shard in stream_mtf(n):
        H = nx.from_graph6_bytes(g6.encode())
        G = nx.complement(H)
        adj = [set(G.neighbors(u)) for u in range(G.number_of_nodes())]
        dfs = has_cdm(adj, n) is not None
        sat = cdm_cpsat(adj, n)
        assert dfs == sat, (
            f"DFS≡CP-SAT DISAGREEMENT n={n} g6={g6!r} (DFS={dfs}, CP-SAT={sat}) "
            "— RELEASE-BLOCKING: quarantine + halt the batch"
        )
