"""Certificate schema v1 — the witness-complete record every cert is written in (VRF-02).

A schema-v1 record is a plain JSON dict (round-trips through json.dumps/json.loads
with field-equality) carrying everything the stdlib-only trust root
(`corpus/verifier.py`) needs to re-derive and re-check the K_k-minor claim from
scratch — it trusts no emission artifact:

  * `provenance`   — a TAGGED UNION discriminated by `kind`:
        seed   {kind, family, n, seed, process}        (deterministic in (n, seed))
        params {kind, family, n, params, [seed]}        (structured, e.g. Cayley Z_p)
        graph6 {kind, family, n, graph6}                (external/ingested identity)
  * `H_edges`         — canonical sorted [min,max] pairs (Phase-1 convention);
  * `H_edges_sha256`  — sha256 of the compact canonical serialization;
  * `invariants`      — {n, num_H_edges, nu_H, chi_G, omega_G|null, had_2};
  * `model_branch_sets` — the FULL had_2-optimal family (len == had_2 >= chi).
        NEVER `fam[:chi]`: a family shorter than chi is a REJECTED input, never a
        storage shortcut. The schema SUPPORTS k >= chi (seed-137's true 17-set
        had_2 family arrives in Phase 4 via CBC; Phase 2 round-trips the 16-set
        interim K16 model of Appendix D.3).
  * `matching_M`, `tutte_berge_U` — the Tutte-Berge witness pinning chi = n - nu;
  * `verified`, `method` — provenance of the claim;
  * `reproduction`, `backends` — the ENV-05 reproduction contract (added by the
        reproduction helpers; the verifier ignores these structurally).

stdlib ONLY (json, hashlib). No networkx, no search/generators imports — the
schema assembles plain data the trust root consumes.
"""
import hashlib
import json

SCHEMA_VERSION = 1

_VALID_KINDS = ("seed", "params", "graph6")


# --------------------------------------------------------------------------- #
# Canonical H_edges + sha256 (frozen Phase-1 convention)
# --------------------------------------------------------------------------- #
def canonical_edges(H_edges):
    """Canonicalize edges to sorted [min,max] pairs (globally sorted).

    Mirrors the frozen Phase-1 convention exactly so the recomputed sha256 matches
    the golden manifest byte-for-byte.
    """
    out = []
    for e in H_edges:
        if len(e) != 2:
            raise ValueError(f"malformed H_edge {e!r} (len != 2)")
        a, b = e
        out.append([min(a, b), max(a, b)])
    return sorted(out)


def h_edges_sha256(H_edges):
    """sha256 hexdigest of the compact canonical H_edges serialization.

    json.dumps(canonical_edges, separators=(",",":")) then sha256 — the frozen
    Phase-1 identity convention (WL-hash is forbidden; this is canonical).
    """
    canon = json.dumps(canonical_edges(H_edges), separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Tagged-union provenance
# --------------------------------------------------------------------------- #
def provenance_seed(family, n, seed, process):
    """Deterministic-in-(n, seed) provenance (triangle-free-process complements)."""
    return {"kind": "seed", "family": family, "n": n, "seed": seed, "process": process}


def provenance_params(family, n, params, seed=None):
    """Structured-parameter provenance (sum-free Cayley Z_p, Kneser, inflation).

    `params` is required; `seed` is optional (some param families also seed an RNG).
    """
    prov = {"kind": "params", "family": family, "n": n, "params": params}
    if seed is not None:
        prov["seed"] = seed
    return prov


def provenance_graph6(family, n, graph6):
    """External/ingested-identity provenance (nauty geng, Ramsey datasets)."""
    return {"kind": "graph6", "family": family, "n": n, "graph6": graph6}


def validate_provenance(prov):
    """Raise ValueError unless `prov` is a well-formed tagged-union provenance.

    Each shape MUST carry its discriminator field: seed needs `seed`, params needs
    `params`, graph6 needs `graph6`. A missing discriminator is a rejected input.
    """
    if not isinstance(prov, dict):
        raise ValueError(f"provenance must be a dict, got {type(prov).__name__}")
    kind = prov.get("kind")
    if kind not in _VALID_KINDS:
        raise ValueError(f"provenance kind {kind!r} not in {_VALID_KINDS}")
    for req in ("family", "n"):
        if req not in prov:
            raise ValueError(f"provenance missing required field {req!r}")
    if kind == "seed" and prov.get("seed") is None:
        raise ValueError("seed-kind provenance requires a `seed`")
    if kind == "params" and prov.get("params") is None:
        raise ValueError("params-kind provenance requires `params`")
    if kind == "graph6" and prov.get("graph6") is None:
        raise ValueError("graph6-kind provenance requires `graph6`")
    return True


# --------------------------------------------------------------------------- #
# Record builder
# --------------------------------------------------------------------------- #
def _as_int_pairs(edges):
    """Coerce an iterable of 2-element edges to plain [int,int] lists (JSON-native).

    Guarantees json round-trip equality (no tuples/np-ints leak into the record).
    """
    out = []
    for e in edges:
        a, b = e
        out.append([int(a), int(b)])
    return out


def _as_branch_sets(sets):
    """Coerce branch sets to plain list[list[int]] (preserving order, JSON-native)."""
    return [[int(v) for v in s] for s in sets]


def build_record(
    *,
    provenance,
    H_edges,
    nu_H,
    chi_G,
    model_branch_sets,
    matching_M,
    tutte_berge_U,
    method,
    omega_G=None,
    verified=True,
    reproduction=None,
    backends=None,
):
    """Assemble a schema-v1 record. Returns a plain JSON-serializable dict.

    Derives `had_2 = len(model_branch_sets)` and REFUSES a family shorter than chi
    (no `fam[:chi]` truncation is ever produced). `n` is taken from provenance and
    must equal len-consistency of the edges. `reproduction`/`backends` are optional
    metadata (populated by the ENV-05 helpers); when present they are stored as-is.
    """
    validate_provenance(provenance)
    n = provenance["n"]
    if not (isinstance(n, int) and n >= 1):
        raise ValueError(f"provenance n must be a positive int, got {n!r}")
    if not (isinstance(chi_G, int) and chi_G >= 1):
        raise ValueError(f"chi_G must be a positive int, got {chi_G!r}")

    had_2 = len(model_branch_sets)
    if had_2 < chi_G:
        raise ValueError(
            f"family size {had_2} < chi {chi_G}: the FULL had_2 family (len >= chi) "
            "must be stored; a truncated family is a rejected input, never a shortcut"
        )

    canon_edges = canonical_edges(H_edges)
    record = {
        "schema_version": SCHEMA_VERSION,
        "provenance": provenance,
        "H_edges": canon_edges,
        "H_edges_sha256": h_edges_sha256(canon_edges),
        "invariants": {
            "n": n,
            "num_H_edges": len(canon_edges),
            "nu_H": int(nu_H),
            "chi_G": int(chi_G),
            "omega_G": (int(omega_G) if omega_G is not None else None),
            "had_2": had_2,
        },
        "model_branch_sets": _as_branch_sets(model_branch_sets),
        "matching_M": _as_int_pairs(matching_M),
        "tutte_berge_U": [int(v) for v in tutte_berge_U],
        "verified": bool(verified),
        "method": method,
    }
    if reproduction is not None:
        record["reproduction"] = reproduction
    if backends is not None:
        record["backends"] = backends
    return record
