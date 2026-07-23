"""Generation cross-checks (POOL-0) — Lemma 2.5 agreement + sharding-sum identity.

Two independent guards against silent generation drift (RESEARCH Pitfall 3):

  1. **Second-route agreement (Lemma 2.5).** Every `pickg -Z2` survivor H must be
     edge-maximal-triangle-free by the repo's INDEPENDENT predicate
     `generators.tfp.is_edge_maximal_tf` (add-any-edge-closes-a-triangle ⟺
     diameter 2). This is the "second route" cross-check: nauty's C diameter filter
     vs the repo's Python edge-maximality filter must agree on the survivor set
     (RESEARCH verified 61/147 agreement live). External anchor: OEIS A216783.

  2. **Sharding-sum identity.** Σ over res in 0..mod-1 of `len(list(stream_mtf(n,
     res, mod)))` must equal the single-stream count — a dropped/duplicated shard
     is caught here (Pitfall 3).

RED until 07-04 (`stream_mtf`); imports of it are function-local. `is_edge_maximal_tf`
already exists, so it is imported at module top (collection stays clean).
"""
import shutil

import networkx as nx
import pytest

from alpha2.generators.tfp import is_edge_maximal_tf


def _geng_available():
    return shutil.which("geng") is not None and shutil.which("pickg") is not None


def test_survivors_are_edge_maximal_tf():
    """Lemma 2.5: every pickg -Z2 survivor H is edge-maximal-tf (independent route)."""
    if not _geng_available():
        pytest.skip("nauty geng/pickg not on PATH")
    from alpha2.pool.cdm.generate import stream_mtf  # RED until 07-04

    seen = 0
    for _i, g6, _shard in stream_mtf(11):  # n=11 survivors (61) — fast
        H = nx.from_graph6_bytes(g6.encode())
        n = H.number_of_nodes()
        adj = [set(H.neighbors(u)) for u in range(n)]
        assert is_edge_maximal_tf(adj, n), f"pickg -Z2 survivor {g6!r} not edge-maximal-tf"
        seen += 1
    assert seen == 61, f"expected 61 MTF at n=11, got {seen}"


def test_sharding_sum_equals_single_stream():
    """Σ_res len(stream_mtf(n, res, mod)) == single-stream count (== 147 at n=12)."""
    if not _geng_available():
        pytest.skip("nauty geng/pickg not on PATH")
    from alpha2.pool.cdm.generate import stream_mtf  # RED until 07-04

    n, mod = 12, 4
    single = sum(1 for _ in stream_mtf(n))
    sharded = sum(len(list(stream_mtf(n, res, mod))) for res in range(mod))
    assert single == 147, f"single-stream n=12 count {single} != 147"
    assert sharded == single, f"Σ shards {sharded} != single-stream {single}"
