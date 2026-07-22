"""Derived KILLED / SHC-CANDIDATE / RESISTANT views (VRF-03) — read-only, raises-only.

`build_status_view(corpus_records, log_events)` is a PURE function of two immutable
inputs — the hash-chained corpus records and the append-only results-log events — and
returns a per-instance keyed view::

    { "tfp:n31:s137": {status, method, certificate_ref, reason, seed, provenance}, ... }

Locked VRF-03 semantics (`.planning/phases/.../06-CONTEXT.md:53-57`):

  * Status is DERIVED on read; the store is append-only + hash-chained by construction,
    so the view ONLY reads. A RESISTANT -> KILLED transition is expressed by APPENDING a
    later kill fact, never by editing the earlier stored record (T-06-14). This module
    never mutates an input object.
  * KILLED derives from a verified corpus certificate OR a KILLED results-log event that
    carries a certificate reference (a verified K_chi model — the trust root is the sole
    authority elsewhere; here we only READ its verdict).
  * SHC-CANDIDATE derives from a differential-licensed had_2 < chi value-fact event.
  * RESISTANT derives ONLY from an EXACT-method timeout (INSUFFICIENT) event — never a
    heuristic miss, and never a RESISTANT terminal_state that fails to record an exact
    method (T-06-15, spoof guard: such an event is REFUSED).

Precedence (a later, stronger fact supersedes a weaker one by appending): a verified
KILLED beats SHC-CANDIDATE beats KILLED-BY-GATE beats RESISTANT beats QUARANTINED.

The instance key reuses the frozen A5 scheme (`corpus.manifest.manifest_key`): TFP keys
read ``tfp:n{n}:s{seed}``, Cayley keys ``cayley:p{n}:s{seed}``. Every guard RAISES (no
`assert`; survives ``python -O``).
"""
import copy
import json
import os

from alpha2 import paths
from alpha2.corpus.manifest import manifest_key

# ---- Derived status vocabulary (mirrors battery/pipeline.py terminal states) ----
KILLED = "KILLED"                    # a verified K_chi model (corpus certificate or exact/heuristic kill)
KILLED_BY_GATE = "KILLED-BY-GATE"    # a HARD gate check killed — no compute, no certificate
SHC_CANDIDATE = "SHC-CANDIDATE"      # differential-licensed had_2 < chi (SHC refutation)
RESISTANT = "RESISTANT"              # exact INSUFFICIENT (timeout) — a queue state, never a heuristic miss
QUARANTINED = "QUARANTINED"          # gate Error, or release-blocking backend disagreement

# Higher wins: a stronger fact supersedes a weaker one by APPENDING (never editing).
_PRECEDENCE = {
    KILLED: 5,
    SHC_CANDIDATE: 4,
    KILLED_BY_GATE: 3,
    RESISTANT: 2,
    QUARANTINED: 1,
}


def _is_exact_method(method):
    """True iff `method` records an EXACT method (the only license for RESISTANT)."""
    return isinstance(method, str) and "exact" in method.lower()


def _fact(status, *, method, certificate_ref, reason, seed, provenance):
    """One derived fact. Provenance is DEEP-COPIED so the view never aliases an input."""
    if status not in _PRECEDENCE:
        raise ValueError(f"unknown derived status {status!r}; expected one of {sorted(_PRECEDENCE)}")
    return {
        "status": status,
        "method": method,
        "certificate_ref": certificate_ref,
        "reason": reason,
        "seed": seed,
        "provenance": copy.deepcopy(provenance),
    }


def _key_from_provenance(provenance, n):
    """Reuse the frozen A5 key scheme by shaping a minimal record-like view (READ-ONLY)."""
    if not isinstance(provenance, dict):
        raise ValueError(f"provenance must be a dict, got {type(provenance).__name__}")
    if not (isinstance(n, int) and not isinstance(n, bool) and n >= 1):
        raise ValueError(f"n must be a positive int, got {n!r}")
    # manifest_key reads record['provenance']['family'|'seed'] + record['invariants']['n'].
    return manifest_key({"provenance": provenance, "invariants": {"n": n}})


def _fact_from_corpus_record(rec):
    """A verified corpus certificate is a KILLED fact; a non-verified record has no status."""
    if not isinstance(rec, dict):
        raise ValueError(f"corpus record must be a dict, got {type(rec).__name__}")
    if "verified" not in rec:
        raise KeyError("corpus record missing 'verified' field (schema drift)")
    if not rec["verified"]:
        return None
    prov = rec["provenance"]
    n = rec["invariants"]["n"]
    key = _key_from_provenance(prov, n)
    cert = f"corpus:{key} h_sha256={str(rec.get('H_edges_sha256', ''))[:12]}"
    return key, _fact(
        KILLED,
        method=rec.get("method"),
        certificate_ref=cert,
        reason="verified K_chi model appended to the immutable corpus",
        seed=prov.get("seed"),
        provenance=prov,
    )


def _fact_from_event(ev):
    """Derive a fact from ONE results-log event, or None for a non-terminal/ignored event.

    RESISTANT is refused unless the event records an exact-method timeout (T-06-15).
    """
    if not isinstance(ev, dict):
        raise ValueError(f"log event must be a dict, got {type(ev).__name__}")
    ts = ev.get("terminal_state")
    method = ev.get("method")
    prov = ev.get("provenance")
    n = ev.get("n")
    reason = ev.get("reason", "")
    cert = ev.get("certificate_ref")

    if ts == KILLED:
        if not cert:
            raise ValueError("a KILLED event must carry a certificate_ref (verified model)")
        status = KILLED
    elif ts == SHC_CANDIDATE:
        status = SHC_CANDIDATE
    elif ts == RESISTANT:
        # RESISTANT is derivable ONLY from an exact-method timeout — a heuristic miss or
        # any non-exact method carrying this terminal_state is a spoof and is REFUSED.
        if not _is_exact_method(method):
            raise ValueError(
                f"RESISTANT event must record an exact-method timeout (INSUFFICIENT); "
                f"got method={method!r} (a heuristic miss is NEVER RESISTANT)"
            )
        status = RESISTANT
    elif ts == KILLED_BY_GATE:
        status = KILLED_BY_GATE
    elif ts == QUARANTINED:
        status = QUARANTINED
    else:
        # GATE-PASS / HEURISTIC-MISS / any non-terminal or unrecognized event: no status.
        return None

    key = _key_from_provenance(prov, n)
    return key, _fact(
        status, method=method, certificate_ref=cert, reason=reason,
        seed=(prov.get("seed") if isinstance(prov, dict) else None), provenance=prov,
    )


def _accept(view, key, fact):
    """Keep the highest-precedence fact for `key` (a stronger fact supersedes by append)."""
    incumbent = view.get(key)
    if incumbent is None or _PRECEDENCE[fact["status"]] > _PRECEDENCE[incumbent["status"]]:
        view[key] = fact


def build_status_view(corpus_records, log_events):
    """Derive the per-instance status view from immutable corpus records + append-only events.

    READ-ONLY: never mutates an input object. Corpus records seed verified KILLED facts;
    results-log events are folded in append order, a stronger fact superseding a weaker one
    (RESISTANT -> KILLED recomputes to KILLED without editing the stored RESISTANT event).
    Returns ``{instance_key: {status, method, certificate_ref, reason, seed, provenance}}``.
    """
    if not isinstance(corpus_records, list):
        raise TypeError(f"corpus_records must be a list, got {type(corpus_records).__name__}")
    if not isinstance(log_events, list):
        raise TypeError(f"log_events must be a list, got {type(log_events).__name__}")

    view = {}
    for rec in corpus_records:
        derived = _fact_from_corpus_record(rec)
        if derived is not None:
            _accept(view, *derived)
    for ev in log_events:
        derived = _fact_from_event(ev)
        if derived is not None:
            _accept(view, *derived)
    return view


def load_status_view(corpus_path=None, log_path=None):
    """Load the immutable corpus + append-only results log (READ-ONLY) and derive the view.

    `paths.CORPUS` is `json.load`ed; `paths.RESULTS_LOG` (when present) is read line by line
    (JSONL). Neither file is written. A missing results log yields corpus-only statuses.
    """
    if corpus_path is None:
        corpus_path = paths.CORPUS
    if log_path is None:
        log_path = paths.RESULTS_LOG

    with open(corpus_path) as fh:      # READ-ONLY load; transitions never edit a stored record
        records = json.load(fh)

    events = []
    if os.path.exists(log_path):
        with open(log_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    return build_status_view(records, events)


def summarize(view):
    """A JSON-serializable summary: per-status counts + the sorted per-instance view."""
    counts = {}
    for fact in view.values():
        counts[fact["status"]] = counts.get(fact["status"], 0) + 1
    return {
        "total": len(view),
        "counts": counts,
        "instances": {key: view[key] for key in sorted(view)},
    }
