"""VRF-03 — derived statuses are READ-ONLY views over immutable facts (Plan 06-04).

`build_status_view(corpus_records, log_events)` is a PURE function of the immutable
corpus records + append-only results-log events. It derives, per instance:

  * KILLED         — a verified K_chi model exists (a stored corpus certificate, or a
                     KILLED results-log event carrying a certificate reference);
  * SHC-CANDIDATE  — a differential-licensed had_2 < chi value-fact;
  * RESISTANT      — an EXACT-method timeout (INSUFFICIENT) event ONLY — never a
                     heuristic miss.

The load-bearing invariants under test (mirroring the threat register):
  * T-06-14: a RESISTANT -> KILLED transition recomputes to KILLED by APPENDING a new
    fact; the earlier stored event object is byte-unchanged (the view never edits input).
  * T-06-15: a heuristic-miss event does NOT by itself produce RESISTANT; a RESISTANT
    terminal_state that does not record an exact-method timeout is refused.

Imports of the under-test module are deferred INSIDE each test so this file COLLECTS
before Task 2 lands `alpha2.status.views` (mirrors the Plan 06-02 Wave-0 convention).
"""
import copy

import pytest


# --------------------------------------------------------------------------- #
# Synthetic fixtures (in-memory; no disk, no solvers).
# --------------------------------------------------------------------------- #
def _tfp_prov(n, seed):
    return {
        "kind": "seed",
        "family": "triangle_free_process_complement",
        "n": n,
        "seed": seed,
        "process": "Bohman uniform triangle-free process",
    }


def _corpus_record(n, seed, *, verified=True):
    """A minimal schema-v1-shaped corpus record (only the fields the view reads)."""
    prov = _tfp_prov(n, seed)
    nu = n // 2
    return {
        "schema_version": "v1",
        "provenance": prov,
        "H_edges": [[0, 1]],
        "H_edges_sha256": "ab" * 32,
        "invariants": {
            "n": n, "num_H_edges": 1, "nu_H": nu, "chi_G": n - nu,
            "omega_G": None, "had_2": n - nu,
        },
        "model_branch_sets": [[0, 1]],
        "matching_M": [[0, 1]],
        "tutte_berge_U": [],
        "verified": verified,
        "method": "heuristic",
    }


def _event(n, seed, terminal_state, method, *, terminal=True,
           certificate_ref=None, reason="", family="tfp"):
    return {
        "family": family, "n": n, "seed": seed, "step": "had2",
        "terminal": terminal, "terminal_state": terminal_state,
        "method": method, "certificate_ref": certificate_ref, "reason": reason,
        "provenance": _tfp_prov(n, seed), "budgets": {},
        "invariants": {"n": n}, "flags": [],
    }


# --------------------------------------------------------------------------- #
# Derivations
# --------------------------------------------------------------------------- #
def test_verified_corpus_record_derives_killed():
    from alpha2.status.views import build_status_view

    rec = _corpus_record(31, 137)
    view = build_status_view([rec], [])
    assert len(view) == 1
    (key, fact), = view.items()
    assert key == "tfp:n31:s137"
    assert fact["status"] == "KILLED"
    assert fact["seed"] == 137
    assert fact["provenance"]["family"] == "triangle_free_process_complement"


def test_shc_candidate_from_differential_value_fact():
    from alpha2.status.views import build_status_view

    ev = _event(45, 9, "SHC-CANDIDATE", "exact-had2",
                reason="had_2=21 < chi=23: differential-licensed")
    view = build_status_view([], [ev])
    assert view["tfp:n45:s9"]["status"] == "SHC-CANDIDATE"


def test_resistant_only_from_exact_timeout_event():
    from alpha2.status.views import build_status_view

    ev = _event(51, 4, "RESISTANT", "exact-had2",
                reason="exact had_2 INSUFFICIENT (timeout on a backend) -> RESISTANT queue")
    view = build_status_view([], [ev])
    assert view["tfp:n51:s4"]["status"] == "RESISTANT"


def test_heuristic_miss_never_resistant():
    """T-06-15: a heuristic-miss (non-terminal) event yields NO status at all — never RESISTANT."""
    from alpha2.status.views import build_status_view

    miss = _event(51, 4, "HEURISTIC-MISS", "heuristic", terminal=False,
                  reason="heuristic miss -> routing to exact had_2")
    view = build_status_view([], [miss])
    # A heuristic miss is not a terminal fact: the instance simply has no derived status.
    assert "tfp:n51:s4" not in view
    assert all(f["status"] != "RESISTANT" for f in view.values())


def test_resistant_terminal_state_without_exact_method_is_refused():
    """T-06-15 (spoof guard): RESISTANT is derivable ONLY from an exact-method timeout."""
    from alpha2.status.views import build_status_view

    spoof = _event(51, 4, "RESISTANT", "heuristic", reason="not an exact timeout")
    with pytest.raises(ValueError):
        build_status_view([], [spoof])


def test_resistant_to_killed_transition_never_mutates_stored_record():
    """T-06-14: a later KILL event supersedes RESISTANT by APPENDING — the earlier stored
    event is byte-unchanged (the derivation only READS)."""
    from alpha2.status.views import build_status_view

    resistant = _event(51, 4, "RESISTANT", "exact-had2",
                       reason="exact had_2 INSUFFICIENT (timeout) -> RESISTANT queue")
    later_kill = _event(51, 4, "KILLED", "exact-had2",
                        certificate_ref="in-memory exact had_2=25 h_sha256=abcdef012345",
                        reason="dual-backend AGREED_KILL had_2=25 (longer budget)")

    frozen = copy.deepcopy(resistant)          # snapshot BEFORE derivation
    events = [resistant, later_kill]           # append-only order: RESISTANT then KILLED

    view = build_status_view([], events)

    # The recomputed status is KILLED (the later verified fact supersedes RESISTANT)...
    assert view["tfp:n51:s4"]["status"] == "KILLED"
    # ...and the earlier stored RESISTANT event object was NEVER edited (byte-identical).
    assert resistant == frozen


def test_view_is_read_only_corpus_records_unchanged():
    """A verified corpus record + a superseding event leave the input record untouched."""
    from alpha2.status.views import build_status_view

    rec = _corpus_record(31, 137)
    frozen = copy.deepcopy(rec)
    build_status_view([rec], [_event(31, 137, "KILLED", "exact-had2",
                                     certificate_ref="corpus:tfp:n31:s137")])
    assert rec == frozen
