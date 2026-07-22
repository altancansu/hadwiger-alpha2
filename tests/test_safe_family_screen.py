"""GATE-03 — the G5/G6 known-safe family->citation map + membership screen (Plan 06-04).

`SAFE_FAMILIES` is the enumerated, CITED proven-safe family list frozen from Appendix E
§2 (`.planning/reference/alpha2-program-source.md:644`) — never invented. `screen_safe_families`
runs the membership tests that are cheap/decidable now and returns, per family, either a
cited safe-member hit or a "screen not yet active" marker for deferred tests (never a
fabricated safe verdict — T-06-17). D-01 Role B: the gate consults it flag_only.

Imports of the under-test module are deferred INSIDE each test so this file COLLECTS
before Task 3 lands `alpha2.gate.safe_families`.
"""


def _empty_h_adj(n):
    """H with no edges => G = complement(H) = K_n (complete)."""
    return [set() for _ in range(n)]


def test_every_mapped_family_carries_a_nonempty_citation():
    from alpha2.gate.safe_families import SAFE_FAMILIES

    assert SAFE_FAMILIES, "the safe-family map must not be empty"
    for family, citation in SAFE_FAMILIES.items():
        assert isinstance(citation, str) and citation.strip(), \
            f"family {family!r} has an empty/invalid citation {citation!r}"


def test_pinned_section2_families_are_present_by_name():
    from alpha2.gate.safe_families import SAFE_FAMILIES

    names = list(SAFE_FAMILIES)
    # A representative slice of the §2 line-644 list (verbatim, ASCII-normalized).
    assert any("line graphs" == n for n in names)
    assert any("quasi-line graphs" == n for n in names)
    assert any("C5-free graphs" == n for n in names)
    assert any(n.startswith("inflations of any graph on <=11") for n in names)
    assert any("Higman-Sims complement" in n for n in names)
    assert any("<=87 vertices for the connected-matching" in n for n in names)
    # The frozen list is substantial (author's enumerated classes, not a paraphrase).
    assert len(SAFE_FAMILIES) >= 10


def test_section2_citations_are_faithful():
    from alpha2.gate.safe_families import SAFE_FAMILIES

    assert SAFE_FAMILIES["line graphs"] == "Reed-Seymour"
    assert SAFE_FAMILIES["quasi-line graphs"] == "Chudnovsky-Fradkin"
    assert "PST" in SAFE_FAMILIES["C5-free graphs"]
    assert "Blasiak" in SAFE_FAMILIES[
        "graphs with fractional clique cover number below 3 and even order"]
    assert "Chen-Deng" in SAFE_FAMILIES[
        "graphs on <=87 vertices for the connected-matching weakening"]


def test_implemented_screen_returns_a_cited_hit():
    from alpha2.gate.safe_families import screen_safe_families

    # G = K5 is C5-free (no induced 5-cycle) => a member of the C5-free safe family (PST).
    n = 5
    adj = _empty_h_adj(n)
    screen = screen_safe_families(adj, n, {})
    assert screen["any_hit"] is True
    hits = {h["family"] for h in screen["hits"]}
    assert "C5-free graphs" in hits
    hit = next(h for h in screen["hits"] if h["family"] == "C5-free graphs")
    assert hit["status"] == "safe-member"
    assert hit["citation"].strip()   # the hit carries its §2 citation


def test_unimplemented_family_screens_as_not_yet_active():
    from alpha2.gate.safe_families import screen_safe_families

    n = 5
    adj = _empty_h_adj(n)
    screen = screen_safe_families(adj, n, {})
    by_family = {r["family"]: r for r in screen["results"]}
    # A deferred membership test never falsely kills — it reports "screen not yet active".
    assert by_family["line graphs"]["status"] == "screen not yet active"
    assert by_family["line graphs"]["citation"].strip()


def test_c5_rich_graph_is_not_a_safe_member_of_c5_free():
    """A graph WITH an induced C5 is NOT screened as C5-free-safe (no false safe verdict)."""
    from alpha2.gate.safe_families import screen_safe_families

    # G = C5 itself (a 5-cycle): H = complement(C5) = another C5. G has an induced C5.
    n = 5
    # G adjacency of a 5-cycle 0-1-2-3-4-0:
    g_cycle = {0: {1, 4}, 1: {0, 2}, 2: {1, 3}, 3: {2, 4}, 4: {0, 3}}
    # H = complement(G): adj[u] = all v != u not adjacent in G.
    adj = [set(v for v in range(n) if v != u and v not in g_cycle[u]) for u in range(n)]
    screen = screen_safe_families(adj, n, {})
    by_family = {r["family"]: r for r in screen["results"]}
    assert by_family["C5-free graphs"]["status"] == "not-a-member"


def test_b7_free_screen_is_deferred_not_implemented():
    """The B7-free screen is DEFERRED to Plan 05 (author sign-off) — it must not be a
    membership test masquerading as active."""
    from alpha2.gate import safe_families

    # No membership test is registered under any 'B7' family key.
    assert not any("B7" in family for family in safe_families.SAFE_FAMILIES)
