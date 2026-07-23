"""Dev-scale unit tests for the structured-vs-random g(G) grid sweep (POOL-2, 08-06).

These are the FAST ("not slow") tests: they exercise grid enumeration, the non-cyclic
Green–Ruzsa type-II exclusion guard, canonical dedup of the merged streams, the
observable bank, the exact-window routing, and the aggregation — all at a tiny order_max
or over a handful of hand-built gate-KILLED descriptors, so NO heavy ILP solve runs. The
authoritative |Γ|=31–500 grid is the box job (docs/COMPUTE.md), NOT this session.

Adjacency / dedup conventions match conftest: Γ by invariant factors, S a symmetric
sum-free set of element tuples, H = Cay(Γ, S). Cay(Z_5, ±1) = C_5 and Cay(Z_7, ±1) = C_7
are the small gate-KILLED instances used for the sweep-run tests.
"""
import json

from alpha2.pool.sumfree.generate import (
    KIND_GREEN_RUZSA,
    KIND_MIDDLE_INTERVAL,
    KIND_RANDOM_GREEDY,
)
from alpha2.pool.sumfree.sweep import (
    grid_descriptors,
    group_observables,
)


def _read_events(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --------------------------------------------------------------------------- #
# grid enumeration + dedup
# --------------------------------------------------------------------------- #
def test_grid_descriptors_deduped_with_kinds_preserved(tmp_path):
    log = tmp_path / "grid.jsonl"
    descriptors = grid_descriptors(order_max=37, non_cyclic=(), log_path=str(log))

    assert descriptors, "the odd 31..37 cyclic grid must yield descriptors"
    # Every descriptor carries dedup/adjudicate-ready provenance with its family kind.
    for d in descriptors:
        assert "invariant_factors" in d and "S" in d
        assert d["kind"] in (KIND_GREEN_RUZSA, KIND_MIDDLE_INTERVAL, KIND_RANDOM_GREEDY)
        assert d["tag"] in ("structured", "random")
    # Deduped: no two representatives share a canonical certificate (isomorphic H).
    from alpha2.pool.sumfree.dedup import canonical_key
    from alpha2.pool.sumfree.generate import adjacency_from_descriptor
    keys = []
    for d in descriptors:
        adj = adjacency_from_descriptor(d)
        keys.append(canonical_key(adj, len(adj)))
    assert len(keys) == len(set(keys)), "dedup must leave one representative per iso class"


def test_grid_excludes_noncyclic_all_primes_1mod3(tmp_path):
    # Z_7 x Z_7 = (7,7): non-cyclic, every prime divisor (7) is ≡ 1 (mod 3) -> EXCLUDED
    # with a logged reason (RESEARCH Open Q1 / T-8-17). Z_7 (cyclic) is NOT excluded.
    log = tmp_path / "grid.jsonl"
    descriptors = grid_descriptors(order_max=49, non_cyclic=((7, 7),), log_path=str(log))

    assert all(d["invariant_factors"] != [7, 7] for d in descriptors), (
        "the unresolved non-cyclic all-primes-≡1-mod3 case must be absent from the grid"
    )
    events = _read_events(log)
    skips = [e for e in events if e.get("event") == "grid_skip_gamma"]
    assert any(
        e["gamma"] == [7, 7] and "type-II" in e["reason"] for e in skips
    ), "the excluded Γ must be logged with the unresolved-type-II reason (not silent)"


def test_grid_includes_curated_noncyclic_not_excluded(tmp_path):
    # Z_3^2 x Z_5 = (3,3,5), order 45: non-cyclic but primes 3,5 are ≢ 1 mod 3 -> INCLUDED
    # (random-greedy at least; the structured generators serve cyclic Γ only).
    descriptors = grid_descriptors(order_max=45, non_cyclic=((3, 3, 5),), log_path=str(tmp_path / "l"))
    assert any(d["invariant_factors"] == [3, 3, 5] for d in descriptors), (
        "a curated non-cyclic Γ whose primes are ≢ 1 mod 3 must appear in the grid"
    )


def test_grid_dedup_collapses_isomorphic_and_logs_not_drops(tmp_path):
    # At n=31 (prime ≡1 mod3) Green–Ruzsa falls back to the middle interval, so the two
    # structured generators produce the SAME S -> isomorphic H. dedup collapses them to one
    # representative and LOGS the collapse (never a silent drop); the first kind is kept.
    log = tmp_path / "grid.jsonl"
    descriptors = grid_descriptors(order_max=31, non_cyclic=(), log_path=str(log))

    z31 = [d for d in descriptors if d["invariant_factors"] == [31]]
    kinds = {d["kind"] for d in z31}
    assert KIND_MIDDLE_INTERVAL not in kinds or KIND_GREEN_RUZSA not in kinds, (
        "the isomorphic structured pair on Z_31 must collapse to a single representative"
    )
    events = _read_events(log)
    dedup_events = [e for e in events if e.get("event") in ("dedup_duplicate", "dedup_collision")]
    assert dedup_events, "an isomorphic collapse on Z_31 must be logged, never silently dropped"
    for e in dedup_events:
        assert e["reason"], "every collapsed duplicate must carry a non-silent reason"


# --------------------------------------------------------------------------- #
# observable bank (zero solver cost, group-structure cross-sections)
# --------------------------------------------------------------------------- #
def test_group_observables_cross_sections():
    z31 = group_observables((31,))
    assert z31["order"] == 31 and z31["rank"] == 1 and z31["cyclic"] is True
    assert z31["exponent"] == 31 and z31["n_primes_1mod3"] == 1 and z31["aut_order"] == 30

    z3_4 = group_observables((3, 3, 3, 3))       # Z_3^4, elementary abelian, |GL(4,3)|
    assert z3_4["order"] == 81 and z3_4["rank"] == 4 and z3_4["cyclic"] is False
    assert z3_4["elementary_abelian"] is True

    z9x9 = group_observables((9, 9))
    assert z9x9["order"] == 81 and z9x9["rank"] == 2 and z9x9["exponent"] == 9

    z3x5 = group_observables((3, 3, 5))          # Z_3^2 x Z_5, |Aut| = 48 * 4
    assert z3x5["order"] == 45 and z3x5["aut_order"] == 48 * 4
    assert z3x5["n_primes_1mod3"] == 0 and z3x5["n_primes_2mod3"] == 1
