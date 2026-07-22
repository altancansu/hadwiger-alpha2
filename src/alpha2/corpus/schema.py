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
import importlib.metadata as _md
import json
import platform as _platform
import sys as _sys

SCHEMA_VERSION = 1

_VALID_KINDS = ("seed", "params", "graph6")

# ENV-05: Linux x86_64 is the canonical reference-regeneration platform. PuLP's
# bundled CBC ships no osx/arm64 binary, so on Apple Silicon it runs under Rosetta 2
# (x86_64 emulation); to make semantic (exact-method) reproduction deterministic,
# ILP-method certificates are regenerated on Linux x86_64.
CANONICAL_PLATFORM = "linux-x86_64"


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


CHAIN_FIELD = "chain_sha256"


def canonical_record_json(record):
    """Compact, key-sorted JSON of a record EXCLUDING its chain field.

    This is the exact byte-string the store's per-record hash chain hashes. Keys
    are sorted so an in-memory record and its json.load'd copy canonicalize
    identically (records are JSON-native by construction -- see the int coercions
    in build_record and canonical_edges).
    """
    body = {k: v for k, v in record.items() if k != CHAIN_FIELD}
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def chain_hash(prev_chain, record):
    """chain_sha256 = sha256(prev_chain || canonical_record_json(record)).

    Genesis (record 0) uses prev_chain == "". Because each record's chain folds in
    the previous record's chain, any change to an earlier record's body (or a
    wholesale substitution) makes its recomputed chain diverge from the stored one
    and cascades to break every subsequent record's stored chain.
    """
    return hashlib.sha256((prev_chain + canonical_record_json(record)).encode()).hexdigest()


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
    # WR-04: the documented seed shape is {kind, family, n, seed, process}. Enforce
    # `process` so validate_provenance is a faithful source of truth for the shape.
    if kind == "seed" and prov.get("process") is None:
        raise ValueError("seed-kind provenance requires a `process`")
    if kind == "params" and prov.get("params") is None:
        raise ValueError("params-kind provenance requires `params`")
    if kind == "graph6" and prov.get("graph6") is None:
        raise ValueError("graph6-kind provenance requires `graph6`")
    return True


# --------------------------------------------------------------------------- #
# Reproduction contract (ENV-05)
# --------------------------------------------------------------------------- #
def reproduction_kind_for_method(method):
    """byte_exact for heuristic/seed-derived models; semantic for exact methods.

    Heuristic models are byte-reproducible from (n, seed) on the pinned interpreter
    (single-RNG contract). Exact-method models (CBC ILP / CP-SAT) are only
    SEMANTICALLY reproducible — the claim (had_2 value, optimality) reproduces, but
    the model bytes depend on solver threading/platform (CBC-under-Rosetta).
    """
    return "byte_exact" if "heuristic" in method.lower() else "semantic"


def make_reproduction(method, seed=None):
    """Build the `reproduction` block: kind + canonical_platform (+ seed if exact-byte)."""
    kind = reproduction_kind_for_method(method)
    repro = {"kind": kind, "canonical_platform": CANONICAL_PLATFORM}
    if kind == "byte_exact" and seed is not None:
        repro["seed"] = seed
    return repro


def _pkg_version(name):
    """Package version from installed metadata WITHOUT importing the package.

    importlib.metadata is stdlib and reads dist metadata only — so the schema stays
    stdlib-only (it never imports networkx / pulp / ortools).
    """
    try:
        return _md.version(name)
    except _md.PackageNotFoundError:
        return None


def _cbc_under_rosetta():
    """True when the bundled CBC would run under Rosetta 2 (Apple Silicon).

    PuLP ships no osx/arm64 CBC binary, so on darwin+arm64 CBC executes emulated
    (x86_64). This is exactly why Linux x86_64 is the canonical platform.
    """
    return _sys.platform == "darwin" and _platform.machine() == "arm64"


def make_backends(method):
    """Stamp the current environment's backend versions for a given method.

    Always records python + networkx + the platform block. Solver stamps are null
    for heuristic (byte_exact) records; for exact methods they carry the relevant
    solver: `pulp`+`cbc` for exact ILP (CBC), `ortools` for exact CP-SAT.

    The `cbc` field records the bundled-CBC provenance; the exact CBC binary version
    is stamped at ILP-solve time on the canonical platform (Phase 4).
    """
    m = method.lower()
    semantic = reproduction_kind_for_method(method) == "semantic"
    is_ilp = semantic and ("ilp" in m or "cbc" in m)
    is_cpsat = semantic and ("cp-sat" in m or "cp_sat" in m or "cpsat" in m)

    pulp_ver = _pkg_version("pulp") if is_ilp else None
    return {
        "python": _platform.python_version(),
        "networkx": _pkg_version("networkx"),
        "pulp": pulp_ver,
        "cbc": (f"bundled-with-pulp-{pulp_ver}" if is_ilp else None),
        "ortools": (_pkg_version("ortools") if is_cpsat else None),
        "platform": {
            "system": _platform.system(),
            "machine": _platform.machine(),
            "cbc_under_rosetta": _cbc_under_rosetta(),
        },
    }


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
        # ENV-05 reproduction contract — every certificate carries it. Callers may
        # override; otherwise it is derived from the method (+ provenance seed).
        "reproduction": (
            reproduction
            if reproduction is not None
            else make_reproduction(method, seed=provenance.get("seed"))
        ),
        "backends": (backends if backends is not None else make_backends(method)),
    }
    return record
