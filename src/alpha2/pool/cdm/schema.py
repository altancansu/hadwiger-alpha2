"""CDM certificate schema — the record shape for a connected dominating matching.

`build_cdm_record` assembles a plain JSON dict (round-trips through
json.dumps/json.loads with field-equality) that the stdlib-only CDM trust root
(`pool/cdm/verifier.py`) re-derives and re-checks a CDM claim from — it trusts no
emission artifact. The record carries:

  * `provenance`   — graph6 tagged-union identity of H (the MTF triangle-free
        graph), family "mtf_complement"; validated by the reused
        `validate_provenance`.
  * `H_edges`         — canonical sorted [min,max] pairs of H (Phase-1 convention);
  * `H_edges_sha256`  — sha256 of the compact canonical serialization;
  * `matching_M`      — the connected dominating matching as int pairs of G-edges
        (G = complement(H)); NOT a K_chi branch-set family;
  * `invariants`      — {n, complement_connected: bool, cdm: true};
  * `generation`      — SC1 per-instance provenance {geng_version, flags, shard,
        index} (a dedicated-CDM-schema field, NOT smuggled through the frozen
        graph6 provenance shape);
  * `reproduction`    — a CDM-specific PLATFORM-AGNOSTIC block {kind: "byte_exact",
        tools}. CDM certificates are solver-independent (RESEARCH Pitfall 5): they
        carry NO platform / emulation stamp — the ENV-05 Rosetta block is
        exclusively for the CBC ILP-method certificates, never for CDM.

stdlib ONLY (json/hashlib/platform). REUSES the frozen `corpus/schema` helpers
(`provenance_graph6`, `canonical_edges`, `h_edges_sha256`, `chain_hash`,
`CHAIN_FIELD`, `canonical_record_json`, `validate_provenance`, `_as_int_pairs`) —
those live behind a stdlib-only boundary (corpus/schema imports no
networkx/ortools), so the CDM schema stays stdlib-only too.
"""
import platform as _platform

from alpha2.corpus.schema import (  # noqa: F401 (re-exported for the CDM store)
    CHAIN_FIELD,
    _as_int_pairs,
    canonical_edges,
    canonical_record_json,
    chain_hash,
    h_edges_sha256,
    provenance_graph6,
    validate_provenance,
)

# Default generation flags: the exact nauty pipeline that emits the MTF-complement
# frontier (geng exhaustive triangle-free + pickg maximal-triangle-free by diameter).
_DEFAULT_GENG_FLAGS = "geng -ctq | pickg -Z2"


def _generation_block(generation):
    """Normalize the SC1 per-instance generation provenance to a JSON-native dict.

    Every stored int is `int()`-coerced (no numpy-int / tuple leak); `shard` and
    `index` may legitimately be None (unsharded / not-yet-indexed).
    """
    g = generation or {}
    shard = g.get("shard")
    index = g.get("index")
    return {
        "geng_version": g.get("geng_version"),
        "flags": g.get("flags", _DEFAULT_GENG_FLAGS),
        "shard": (int(shard) if shard is not None else None),
        "index": (int(index) if index is not None else None),
    }


def _cdm_reproduction():
    """CDM reproduction block: byte_exact + PLATFORM-AGNOSTIC (RESEARCH Pitfall 5).

    A CDM certificate is a tiny hand-checkable matching witness re-derived from the
    stored graph6 + H_edges — solver-independent, so it is byte_exact on ANY
    interpreter. It deliberately carries NO platform / emulation stamp (the ENV-05
    Rosetta block is only for the CBC ILP-method certs, never for CDM).
    """
    return {
        "kind": "byte_exact",
        "tools": {
            "python": _platform.python_version(),
            "nauty": "2.9.3",
        },
    }


def build_cdm_record(
    *,
    provenance,
    H_edges,
    matching_M,
    complement_connected,
    method,
    generation=None,
    verified=True,
):
    """Assemble a CDM certificate record. Returns a plain JSON-serializable dict.

    `provenance` is a graph6 tagged-union (validated by the reused
    `validate_provenance`); `n` is taken from it. `H_edges` are canonicalized;
    `matching_M` is coerced to plain [int,int] G-edge pairs. `invariants` carries
    `{n, complement_connected, cdm}`; the top-level `generation` field stores the
    SC1 per-instance provenance. The `reproduction` block is platform-agnostic.
    """
    validate_provenance(provenance)
    n = provenance["n"]
    if not (isinstance(n, int) and n >= 1):
        raise ValueError(f"provenance n must be a positive int, got {n!r}")

    canon_edges = canonical_edges(H_edges)
    record = {
        "provenance": provenance,
        "H_edges": canon_edges,
        "H_edges_sha256": h_edges_sha256(canon_edges),
        "matching_M": _as_int_pairs(matching_M),
        "invariants": {
            "n": int(n),
            "complement_connected": bool(complement_connected),
            "cdm": True,
        },
        "verified": bool(verified),
        "method": method,
        "generation": _generation_block(generation),
        "reproduction": _cdm_reproduction(),
    }
    return record
