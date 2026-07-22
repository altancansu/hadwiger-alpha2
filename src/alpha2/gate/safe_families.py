"""GATE-03 — the G5/G6 proven-safe family->citation map + membership screen (stdlib ONLY).

`SAFE_FAMILIES` is the enumerated, CITED proven-safe family list frozen VERBATIM from the
author's Appendix E §2 (`.planning/reference/alpha2-program-source.md:644`) — the classes
are NOT invented here; the map is data so it can grow as pools/literature settle (stub-and-
grow). Family names are ASCII-normalized transcriptions of §2; each carries the §2
parenthetical citation where the source gives an explicit author, and the §2 provenance
(the December-2025 verification / PST) where it does not — never a fabricated author.

`screen_safe_families(adj, n, inv)` runs the membership tests that are cheap/decidable now
and returns, per family, either a CITED safe-member hit or a "screen not yet active" marker
for the families whose membership test is deferred. A deferred family NEVER produces a
(false) safe verdict (T-06-17) — it logs "screen not yet active" instead.

Role B (D-01, LOCKED): the gate consults this screen FLAG-ONLY (`gate/checks.py:g6`), so a
safe-family hit is RECORDED on the record as a flag — it never HARD-kills a studied pool
instance (seed-137 keeps passing the hard-gate). networkx is NOT imported here (it stays
confined to `invariants/`); the C5-free membership test works directly over `adj`. Every
guard RAISES (no `assert`; survives ``python -O``).

DEFERRED (do NOT implement here): the B7-free screen is deferred to Plan 05 — it needs the
author sign-off on what B7 denotes in the PST citation (06-CONTEXT.md deferred checkpoint).
"""
from collections import OrderedDict
from itertools import combinations

# §2 provenance for classes the source verified without naming a single explicit author.
_S2 = "Costa-Luu-Wood-Yip 2025 (Dec 2025 verification); PST 2003 (Appendix E §2 line 644)"

# The proven-safe family -> citation map, frozen VERBATIM from §2 line 644 (ASCII-normalized).
# Order follows the source list. Membership here is (in the strict §2 gate) an instant kill;
# under D-01 Role B the gate records it as a flag only.
SAFE_FAMILIES = OrderedDict([
    ("line graphs", "Reed-Seymour"),
    ("quasi-line graphs", "Chudnovsky-Fradkin"),
    ("C5-free graphs", "PST (Plummer-Stiebitz-Toft)"),
    ("inflations of any graph on <=11 vertices", "PST (Plummer-Stiebitz-Toft)"),
    ("inflations of complements of girth->=5 graphs (5-cycle, Petersen, Hoffman-Singleton)", _S2),
    ("inflations of complements of triangle-free Kneser graphs", _S2),
    ("Clebsch, Mesner, and Gewirtz complements and their inflations", _S2),
    ("Higman-Sims complement (explicit K50 model)", _S2),
    ("Andrasfai and odd-anticycle inflations", _S2),
    ("Eberhard Cayley complements", "Eberhard"),
    ("graphs with fractional clique cover number below 3 and even order", "Blasiak"),
    ("graphs on <=87 vertices for the connected-matching weakening",
     "Furedi-Gyarfas-Simonyi; Chen-Deng"),
])


# --------------------------------------------------------------------------- #
# Cheap/decidable-now membership tests (stdlib over `adj`; no networkx).
# --------------------------------------------------------------------------- #
def _g_adjacency(adj, n):
    """G = complement(H) adjacency (sets), built directly from H's `adj` (no networkx)."""
    if not (isinstance(n, int) and not isinstance(n, bool) and n >= 0):
        raise ValueError(f"n must be a non-negative int, got {n!r}")
    if len(adj) != n:
        raise ValueError(f"adj has {len(adj)} rows, expected n={n}")
    g = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(n):
            if v != u and v not in row:
                g[u].add(v)
    return g


def _has_induced_c5(g, n):
    """True iff G (adjacency `g`) contains an induced 5-cycle.

    A 5-subset induces a C5 iff it spans exactly 5 induced edges with every vertex at
    induced-degree exactly 2 (5 vertices, all degree 2, 5 edges => a single 5-cycle, since
    the only 2-regular simple graph on 5 vertices is C5). O(C(n,5)) — cheap in the studied
    pool range (n ~ 31: ~1.7e5 subsets; a C5-rich candidate short-circuits on the first).
    """
    for combo in combinations(range(n), 5):
        s = set(combo)
        edges2 = 0
        degree_ok = True
        for u in combo:
            d = len(g[u] & s)
            if d != 2:
                degree_ok = False
                break
            edges2 += d
        if degree_ok and edges2 // 2 == 5:
            return True
    return False


def _is_c5_free(adj, n, inv):
    """C5-free graphs (PST): G = complement(H) contains NO induced C5."""
    g = _g_adjacency(adj, n)
    return not _has_induced_c5(g, n)


# Family -> membership predicate for the tests that are implemented for MVP. Families
# absent from this map screen as "screen not yet active" (their test is deferred, never a
# fabricated safe verdict). The map GROWS as classes settle (stub-and-grow).
_MEMBERSHIP_TESTS = {
    "C5-free graphs": _is_c5_free,
}

# Per-family verdicts.
SAFE_MEMBER = "safe-member"
NOT_A_MEMBER = "not-a-member"
NOT_YET_ACTIVE = "screen not yet active"


def screen_safe_families(adj, n, inv):
    """Screen a candidate against the proven-safe family map.

    Returns ``{"results": [...], "hits": [...], "any_hit": bool}`` where each result is
    ``{family, citation, status}``. `status` is one of `safe-member` (a cheap membership
    test fired), `not-a-member`, or `screen not yet active` (the test is deferred). A
    deferred family NEVER reports a safe verdict — it reports `screen not yet active`.
    """
    results = []
    for family, citation in SAFE_FAMILIES.items():
        test = _MEMBERSHIP_TESTS.get(family)
        if test is None:
            status = NOT_YET_ACTIVE
        else:
            status = SAFE_MEMBER if test(adj, n, inv) else NOT_A_MEMBER
        results.append({"family": family, "citation": citation, "status": status})
    hits = [r for r in results if r["status"] == SAFE_MEMBER]
    return {"results": results, "hits": hits, "any_hit": bool(hits)}
