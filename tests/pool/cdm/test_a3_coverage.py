"""A3 coverage gate (POOL-0, ROADMAP SC3) — the EXACT statement of Assumption A3.

The transfer lemma (docs/proofs/transfer-lemma.md) reduces the connected α=2
frontier to CDM on the *edge-minimal* α=2 graphs (the MTF-complements) via §3
monotonicity. Assumption **A3** is the uncertified step: that this actually reaches
EVERY connected α=2 graph. Its witness is `P4` — a connected α=2 graph that HOLDS
CDM but whose only edge-minimal floor (`2K₂`) is disconnected, so monotonicity from
the checked MTF-complement set lifts nothing to it (§5).

This gate discharges A3 empirically-in-range by checking its exact statement head-on:
for every n in range, enumerate the FULL triangle-free superset via `geng -tq n`
(NOT just the maximal-triangle-free graphs `pickg -Z2` filters to), take the
complement G of each H with ≥1 edge (so α(G)=2), and — for every CONNECTED G —
assert `has_cdm(G, n) is not None`. This iterates the complete set of connected α=2
graphs at n, not merely the edge-minimal ones, so it certifies A3's reach directly
in range rather than assuming it.

>>> Any CONNECTED α=2 graph reported CDM-less is THE headline: either A3 is false or
>>> there is a definition bug — a major finding, reported loudly with its graph6,
>>> never silently swallowed. <<<

Achieved bound: n≤11 as the default gate (matches CLWY's arXiv:2512.17114 verified
range; ~105k triangle-free graphs at n=11, ~5s); n=12 (~1.26M graphs, ~60s) behind
the `slow` marker. Counts held CDM (connected α=2 graphs, ALL of which must hold):
n=4:4  n=5:11  n=6:34  n=7:103  n=8:405  n=9:1892  n=10:12166  n=11:105065
n=12:1262173.

Generation is a subprocess arg-list (never shell=True), mirroring
`src/alpha2/pool/cdm/generate.py`. Decode/complement/connectivity are self-contained
stdlib (bitset upper-triangle graph6, per CLAUDE.md Blueprint 1: touching millions of
graphs must not build `nx.Graph` objects); cross-checked byte-for-byte against
networkx `from_graph6_bytes`/`complement`/`is_connected` over all n≤9 during
development (2452 graphs, 0 mismatches).
"""
import shutil
import subprocess

import pytest


def _geng_triangle_free(n):
    """Yield graph6 lines of ALL triangle-free graphs on n vertices.

    `geng -tq n` — triangle-free (`-t`), quiet (`-q`); this is the SUPERSET, not the
    `pickg -Z2` maximal-triangle-free subset. Subprocess is an ARG LIST (no shell),
    mirroring `alpha2.pool.cdm.generate.stream_mtf`.
    """
    proc = subprocess.Popen(
        ["geng", "-tq", str(n)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        for line in proc.stdout:
            g6 = line.strip()
            if g6:
                yield g6
    finally:
        proc.stdout.close()
        proc.wait()


def _graph6_to_adj(g6):
    """Decode graph6 → (adj: list[set[int]], n) — stdlib, no networkx.

    Column-major upper-triangle bit order (0,1),(0,2),(1,2),(0,3),… matching
    `networkx.from_graph6_bytes` (cross-checked in development). Single header byte
    covers n≤62, well past this gate's range.
    """
    data = [ord(c) - 63 for c in g6]
    n = data[0]
    bits = []
    for byte in data[1:]:
        for k in range(5, -1, -1):
            bits.append((byte >> k) & 1)
    adj = [set() for _ in range(n)]
    idx = 0
    for j in range(1, n):
        for i in range(j):
            if bits[idx]:
                adj[i].add(j)
                adj[j].add(i)
            idx += 1
    return adj, n


def _complement_adj(h_adj, n):
    """G = complement of H — G's adjacency (the convention `has_cdm` consumes)."""
    return [set(range(n)) - {u} - h_adj[u] for u in range(n)]


def _is_connected(g_adj, n):
    """True iff G (given by g_adj) is connected — stdlib iterative DFS."""
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in g_adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == n


def _assert_all_connected_alpha2_hold_cdm(n):
    """Enumerate ALL connected α=2 graphs on n and assert each holds CDM.

    Returns the count of connected α=2 graphs checked (every one must hold CDM).
    Raises loudly, quoting the graph6 of H, on the first connected CDM failure —
    that would falsify A3 (or expose a bug), the single most important outcome.
    """
    from alpha2.pool.cdm.reference import has_cdm

    checked = 0
    for g6 in _geng_triangle_free(n):
        h_adj, nn = _graph6_to_adj(g6)
        if sum(len(s) for s in h_adj) == 0:
            # H has no edge ⇒ G = K_n, α(G)=1 (not 2): outside the α=2 frontier.
            continue
        g_adj = _complement_adj(h_adj, nn)
        if not _is_connected(g_adj, nn):
            # Disconnected G = K_a ⊔ K_b — the §4 carve-out (CLWY hypothesises
            # connected G); legitimately may fail CDM, out of A3's scope.
            continue
        M = has_cdm(g_adj, nn)
        assert M is not None, (
            f"CONNECTED α=2 graph on n={nn} (H graph6={g6!r}) reported CDM-LESS. "
            "This is the exact statement of Assumption A3 FAILING in range — either "
            "A3 is false or has_cdm/the A1 reading has a bug. This is a MAJOR "
            "finding, not a definition nit: escalate with this graph6."
        )
        checked += 1
    return checked


# Per-n expected connected-α=2 counts (all of which MUST hold CDM). Anchors the gate
# against a vacuous pass and pins the exact superset size actually adjudicated.
_EXPECTED_CONNECTED = {
    4: 4, 5: 11, 6: 34, 7: 103, 8: 405, 9: 1892, 10: 12166, 11: 105065,
}


@pytest.mark.skipif(shutil.which("geng") is None, reason="nauty `geng` not on PATH")
@pytest.mark.parametrize("n", [4, 5, 6, 7, 8, 9, 10, 11])
def test_every_connected_alpha2_graph_holds_cdm(n):
    """A3 exact-in-range: EVERY connected α=2 graph on n≤11 holds CDM (superset gate)."""
    checked = _assert_all_connected_alpha2_hold_cdm(n)
    assert checked == _EXPECTED_CONNECTED[n], (
        f"n={n}: adjudicated {checked} connected α=2 graphs, expected "
        f"{_EXPECTED_CONNECTED[n]} — the enumeration changed (nauty version drift?), "
        "so the coverage claim is no longer over the set it was verified on"
    )


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("geng") is None, reason="nauty `geng` not on PATH")
def test_every_connected_alpha2_graph_holds_cdm_n12():
    """A3 exact-in-range, stretch bound: all 1,262,173 connected α=2 graphs at n=12
    hold CDM (~1.26M triangle-free superset, ~60s)."""
    checked = _assert_all_connected_alpha2_hold_cdm(12)
    assert checked == 1262173, (
        f"n=12: adjudicated {checked} connected α=2 graphs, expected 1262173"
    )
