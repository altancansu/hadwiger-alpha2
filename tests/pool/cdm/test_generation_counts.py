"""Exact MTF frontier counts (POOL-0) — 147 / 392 / 1,274 at n = 12 / 13 / 14.

`geng -ctq n | pickg -Z2` generates the maximal-triangle-free (connected,
diameter-2) graphs on n vertices; their complements are the edge-minimal α=2
graphs the transfer lemma reduces the whole frontier to. The counts are the
external anchor (OEIS A216783): a wrong flag, a dropped shard, or a mis-set res/mod
silently yields ≠ the true count (RESEARCH Pitfall 3), so we pin the exact triple.

n=14 (1,274 over 467M triangle-free pre-images) is marked `@pytest.mark.slow` for
CI fan-out. All cases skip cleanly when nauty is not on PATH.

RED until 07-04 lands `alpha2.pool.cdm.generate.stream_mtf` — the import is
function-local so `--collect-only` stays clean.
"""
import shutil

import pytest


@pytest.mark.parametrize(
    "n,expected",
    [
        (12, 147),
        (13, 392),
        pytest.param(14, 1274, marks=pytest.mark.slow),
    ],
)
def test_mtf_generation_counts(n, expected):
    """sum(1 for _ in stream_mtf(n)) == the exact OEIS A216783 count."""
    if shutil.which("geng") is None or shutil.which("pickg") is None:
        pytest.skip("nauty geng/pickg not on PATH")
    from alpha2.pool.cdm.generate import stream_mtf  # RED until 07-04

    count = sum(1 for _ in stream_mtf(n))
    assert count == expected, f"n={n}: generated {count}, expected {expected}"
