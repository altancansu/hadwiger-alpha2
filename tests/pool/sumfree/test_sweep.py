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

import pytest

from alpha2.pool.sumfree.generate import (
    KIND_GREEN_RUZSA,
    KIND_MIDDLE_INTERVAL,
    KIND_RANDOM_GREEDY,
)
from alpha2.pool.sumfree.sweep import (
    aggregate_sweep,
    grid_descriptors,
    group_observables,
    run_sweep,
)

# Small hand-built gate-KILLED descriptors (fast: no exact solve fires on these).
_D_C5 = {"invariant_factors": [5], "S": [[1], [4]], "kind": KIND_RANDOM_GREEDY, "tag": "random"}
_D_C7 = {"invariant_factors": [7], "S": [[1], [6]], "kind": KIND_MIDDLE_INTERVAL, "tag": "structured"}

_DET = dict(det_time=0.05, det_nodes=200)


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


# --------------------------------------------------------------------------- #
# run_sweep + aggregation (small gate-KILLED descriptors, no heavy solve)
# --------------------------------------------------------------------------- #
def test_run_sweep_emits_series_and_observables(tmp_path):
    sweep = tmp_path / "sweep.jsonl"
    result = run_sweep(
        descriptors=[_D_C5, _D_C7], seed=0, exact_window=0,
        sweep_path=str(sweep), corpus_path=str(tmp_path / "corpus.json"),
        log_path=str(tmp_path / "log.jsonl"), **_DET,
    )

    assert result["n_instances"] == 2
    assert result["exact_window"] == 0
    rows = result["rows"]
    for row in rows:
        # Observable bank folded in on every row (group + per-instance signals).
        obs = row["observables"]
        for field in ("rank", "exponent", "aut_order", "cyclic",
                      "n_primes_1mod3", "n_primes_2mod3", "S_density", "det_work"):
            assert field in obs
        assert row["window_class"] in ("within_window", "above_window")
        assert "effective_state" in row

    # Structured-vs-random series present, order-sorted, with the plot traces.
    series = result["series"]
    assert set(series) == {KIND_RANDOM_GREEDY, KIND_MIDDLE_INTERVAL}
    for trace in series.values():
        assert trace["orders"] == sorted(trace["orders"])
        assert len(trace["g_mean"]) == len(trace["orders"])
        assert len(trace["resistant_rate"]) == len(trace["orders"])

    # The sweep event stream carries per-row events + one aggregate event.
    events = _read_events(sweep)
    assert sum(1 for e in events if e["event"] == "sweep_row") == 2
    assert sum(1 for e in events if e["event"] == "sweep_aggregate") == 1


def test_run_sweep_is_deterministic(tmp_path):
    kw = dict(descriptors=[_D_C5, _D_C7], seed=0, exact_window=0, **_DET)
    r1 = run_sweep(sweep_path=str(tmp_path / "a.jsonl"),
                   corpus_path=str(tmp_path / "ca.json"),
                   log_path=str(tmp_path / "la.jsonl"), **kw)
    r2 = run_sweep(sweep_path=str(tmp_path / "b.jsonl"),
                   corpus_path=str(tmp_path / "cb.json"),
                   log_path=str(tmp_path / "lb.jsonl"), **kw)
    # Every recorded verdict is a function of (n, seed) — two runs agree exactly.
    strip = lambda rows: [{k: v for k, v in r.items() if k != "observables"} for r in rows]
    assert strip(r1["rows"]) == strip(r2["rows"])


def test_run_sweep_requires_deterministic_budget(tmp_path):
    with pytest.raises(ValueError):
        run_sweep(descriptors=[_D_C5], det_time=None, det_nodes=200,
                  sweep_path=str(tmp_path / "s.jsonl"))
    with pytest.raises(ValueError):
        run_sweep(descriptors=[_D_C5], det_time=0.05, det_nodes=None,
                  sweep_path=str(tmp_path / "s.jsonl"))


def test_aggregate_routes_g_positive_above_window_to_resistant():
    # A g>0 screen ABOVE the exact window must count as RESISTANT, never a reported g>0
    # (RESEARCH §Consequence). Below/at the window it is an exact g>0 candidate.
    within = {
        "kind": "structured:green_ruzsa", "order": 41, "gate_survived": True,
        "terminal_state": "SHC_CANDIDATE", "effective_state": "SHC_CANDIDATE",
        "g": 0.25, "had_2": 3, "had_3": 3,
    }
    above = {
        "kind": "structured:green_ruzsa", "order": 400, "gate_survived": True,
        "terminal_state": "SHC_CANDIDATE", "effective_state": "RESISTANT",
        "g": 0.25, "had_2": 3, "had_3": 3,
    }
    agg = aggregate_sweep([within, above], exact_window=151)
    cells = {(c["kind"], c["order"]): c for c in agg["cells"]}
    assert cells[("structured:green_ruzsa", 41)]["exact_g_gt0"] == 1
    assert cells[("structured:green_ruzsa", 41)]["resistant"] == 0
    assert cells[("structured:green_ruzsa", 400)]["exact_g_gt0"] == 0
    assert cells[("structured:green_ruzsa", 400)]["resistant"] == 1
    # Multiple-comparison honesty: the exploratory count is recorded alongside the primary.
    assert agg["n_exploratory_cross_sections"] == len(agg["exploratory_cross_sections_examined"])
