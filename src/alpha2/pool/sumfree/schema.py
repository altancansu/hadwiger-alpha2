"""g(G)-screen certificate schema — the record shape for a sum-free Cayley screen.

`build_gscreen_record` assembles a plain JSON dict (round-trips through
json.dumps/json.loads with field-equality) that the stdlib-only sum-free trust root
(`pool/sumfree/verifier.py`) re-derives and re-checks the g(G) claim from — it trusts
no emission artifact. A g(G) record states ONLY what a proven `had_3 < chi`
establishes ("no K_chi minor with branch sets of size <=3"); it NEVER claims
"counterexample" or "had(G) < chi". The screen gap is

    g(G) = (chi - had_k) / chi ,  had_k the deepest proved bound (had_3, else had_2),

with the interpretation g <= 0  =>  the K_chi minor already packs (KILLED, Hadwiger
holds on that instance, by construction); g > 0  =>  an SHC_CANDIDATE (necessary, not
sufficient — small branch sets cannot reach chi), queued for the E3 survivor
protocol; RESISTANT  =>  no exact bound was proved in the deterministic budget
(had_k None, g None) — never a g>0 point.

The record carries:

  * `provenance`   — a descriptor identity {kind:"descriptor", family, tag, n,
        invariant_factors, S}; the instance rebuilds FROM this descriptor (never an
        RNG replay). NOTE: the frozen tagged-union `validate_provenance`
        (seed|params|graph6) does NOT admit this `descriptor` kind, so this schema
        validates the descriptor shape itself — it never smuggles a descriptor
        through the frozen graph6/params provenance validator.
  * `H_edges`         — canonical sorted [min,max] pairs of H (Phase-1 convention);
  * `H_edges_sha256`  — sha256 of the compact canonical serialization;
  * `chi`, `had_2`, `had_3`  — chi = n - nu(H); had_k the exact minor lower bounds
        (had_3 / had_2 are null when RESISTANT — no exact bound proved in budget);
  * `g`               — the DERIVED screen gap (null when had_k is None); the schema
        computes it, it is never trusted from the caller;
  * `model_branch_sets` — for a KILLED (g<=0) record, the trust-root-verified K_chi
        family (branch sets of size <=3) — a sound per-instance Hadwiger result;
        None for a g>0 SHC_CANDIDATE (no such family exists at branch sets <=3);
  * `terminal_state`  — KILLED | SHC_CANDIDATE | RESISTANT;
  * `certificate_statement` — the HONEST g(G) claim; the radioactive guard
        (Pitfall 1) RAISES if it carries "counterexample" or "had(G) <";
  * `verified`, `method` — provenance of the claim;
  * `reproduction`    — a PLATFORM-AGNOSTIC block for verified-existence (g<=0)
        records; g>0 ILP-method records carry the solver/platform stamp (ENV-05).

stdlib ONLY (json/hashlib/platform). REUSES the frozen `corpus/schema` helpers
(`canonical_edges`, `h_edges_sha256`, `chain_hash`, `CHAIN_FIELD`,
`canonical_record_json`, `_as_int_pairs`) — those live behind a stdlib-only boundary
(corpus/schema imports no networkx/ortools), so this schema stays stdlib-only too.
"""
import platform as _platform

from alpha2.corpus.schema import (  # noqa: F401 (re-exported for the sumfree store)
    CHAIN_FIELD,
    canonical_edges,
    canonical_record_json,
    chain_hash,
    h_edges_sha256,
)

# The two radioactive substrings a g(G) record may NEVER contain (RESEARCH Pitfall 1).
# "counterexample" is matched case-insensitively; "had(G) <" is the exact claim
# "had(G) < chi" a screen may never make (branch sets of size >=4 are not excluded).
RADIOACTIVE_SUBSTRINGS = ("counterexample", "had(G) <")

# The exact honest wording for a g>0 SHC_CANDIDATE (RESEARCH "Certificate honesty
# rule"). Says ONLY what a proved had_3 < chi establishes; contains NEITHER radioactive
# substring (note: "had(G) drops below chi", never "had(G) < chi").
HONEST_G_POSITIVE_STATEMENT = (
    "had_3 = {had_3} < chi = {chi} (both backends PROVED_OPTIMAL); establishes only "
    "that there is no K_chi minor with branch sets <=3; this does not prove had(G) "
    "drops below chi (size->=4 branch sets are not excluded); queued for E3."
)

_VALID_TERMINAL_STATES = ("KILLED", "SHC_CANDIDATE", "RESISTANT")


def _assert_honest(statement):
    """RAISE ValueError if `statement` carries a radioactive claim (Pitfall 1 guard).

    This is the schema-side half of the honesty gate (the verifier carries the
    trust-root half). A g(G) record physically cannot be assembled with a
    "counterexample" / "had(G) <" claim.
    """
    if not isinstance(statement, str):
        raise ValueError(f"certificate_statement must be a str, got {type(statement).__name__}")
    low = statement.lower()
    if "counterexample" in low:
        raise ValueError(
            "radioactive certificate_statement: a g(G) record may never say "
            "'counterexample' (the screen is necessary-not-sufficient; Pitfall 1)"
        )
    if "had(G) <" in statement:
        raise ValueError(
            "radioactive certificate_statement: a g(G) record may never claim "
            "'had(G) < chi' (branch sets of size >=4 are not excluded; Pitfall 1)"
        )


def honest_statement_for(terminal_state, had_3, chi):
    """Assemble the honest g(G) statement for a terminal state; RAISE on abuse.

    For SHC_CANDIDATE (g>0) it returns the exact `HONEST_G_POSITIVE_STATEMENT` with
    had_3/chi filled in. The returned string is run through `_assert_honest`, so this
    helper can never emit a radioactive claim.
    """
    if terminal_state == "SHC_CANDIDATE":
        stmt = HONEST_G_POSITIVE_STATEMENT.format(had_3=had_3, chi=chi)
    elif terminal_state == "KILLED":
        stmt = (
            f"had_3 = {had_3} >= chi = {chi}; verified K_chi minor (branch sets <=3); "
            "Hadwiger holds on this instance (packs); g <= 0."
        )
    elif terminal_state == "RESISTANT":
        stmt = (
            "no exact bound was proved in the deterministic budget; queued for E3; "
            "NOT a result."
        )
    else:
        raise ValueError(f"unknown terminal_state {terminal_state!r}")
    _assert_honest(stmt)
    return stmt


def _validate_descriptor_provenance(prov):
    """RAISE ValueError unless `prov` is a well-formed sum-free descriptor provenance.

    Shape: {kind:"descriptor", family:"sumfree_cayley", tag: structured|random, n,
    invariant_factors:[int,...], S:[element-tuple,...]}. The instance rebuilds from
    invariant_factors + S; the frozen tagged-union validator is deliberately NOT used
    (it rejects the `descriptor` kind).
    """
    if not isinstance(prov, dict):
        raise ValueError(f"provenance must be a dict, got {type(prov).__name__}")
    if prov.get("kind") != "descriptor":
        raise ValueError(f"provenance kind must be 'descriptor', got {prov.get('kind')!r}")
    if prov.get("family") != "sumfree_cayley":
        raise ValueError(f"provenance family must be 'sumfree_cayley', got {prov.get('family')!r}")
    if prov.get("tag") not in ("structured", "random"):
        raise ValueError(f"provenance tag must be structured|random, got {prov.get('tag')!r}")
    if "invariant_factors" not in prov or not prov["invariant_factors"]:
        raise ValueError("descriptor provenance requires non-empty invariant_factors")
    if "S" not in prov:
        raise ValueError("descriptor provenance requires S (the sum-free set)")
    return True


def _normalize_provenance(prov):
    """Return a JSON-native copy of the descriptor provenance (int/list coercion)."""
    return {
        "kind": "descriptor",
        "family": prov["family"],
        "tag": prov["tag"],
        "n": (int(prov["n"]) if prov.get("n") is not None else None),
        "invariant_factors": [int(d) for d in prov["invariant_factors"]],
        "S": [[int(x) for x in s] for s in prov["S"]],
    }


def _screen_reproduction(terminal_state, method):
    """Reproduction block: platform-agnostic for verified-existence (g<=0) records.

    A KILLED record carries a hand-checkable K_chi family re-derived from the stored
    descriptor + H_edges — solver-independent, byte_exact on ANY interpreter (no
    platform stamp). A g>0 SHC_CANDIDATE rests on an exact ILP/CP-SAT had_3 < chi
    proof, so it carries the solver/platform stamp (ENV-05 semantic reproduction).
    """
    if terminal_state == "SHC_CANDIDATE":
        return {
            "kind": "semantic",
            "canonical_platform": "linux-x86_64",
            "tools": {"python": _platform.python_version()},
        }
    return {
        "kind": "byte_exact",
        "tools": {"python": _platform.python_version()},
    }


def _compute_g(chi, had_2, had_3):
    """Derive the screen gap g = (chi - had_k)/chi; None when no bound was proved.

    had_k is the deepest proved bound: had_3 if present, else had_2. RESISTANT
    records (both None) yield g None — a RESISTANT instance is never a g>0 point.
    """
    had_k = had_3 if had_3 is not None else had_2
    if had_k is None:
        return None
    return (chi - had_k) / chi


def build_gscreen_record(
    *,
    provenance,
    H_edges,
    chi,
    had_2,
    had_3,
    terminal_state,
    certificate_statement,
    method,
    model_branch_sets=None,
    verified=True,
):
    """Assemble a g(G)-screen certificate. Returns a plain JSON-serializable dict.

    `provenance` is a sum-free descriptor (validated by `_validate_descriptor_provenance`,
    NOT the frozen tagged-union validator). `H_edges` are canonicalized; `g` is DERIVED
    (never trusted from the caller). `certificate_statement` is run through the
    radioactive guard (`_assert_honest`), so a "counterexample"/"had(G) <" claim can
    never be assembled. `terminal_state` must be KILLED | SHC_CANDIDATE | RESISTANT.
    """
    _validate_descriptor_provenance(provenance)
    if terminal_state not in _VALID_TERMINAL_STATES:
        raise ValueError(f"terminal_state {terminal_state!r} not in {_VALID_TERMINAL_STATES}")
    if not (isinstance(chi, int) and chi >= 1):
        raise ValueError(f"chi must be a positive int, got {chi!r}")
    _assert_honest(certificate_statement)

    canon_edges = canonical_edges(H_edges)
    g = _compute_g(chi, had_2, had_3)

    record = {
        "provenance": _normalize_provenance(provenance),
        "H_edges": canon_edges,
        "H_edges_sha256": h_edges_sha256(canon_edges),
        "chi": int(chi),
        "had_2": (int(had_2) if had_2 is not None else None),
        "had_3": (int(had_3) if had_3 is not None else None),
        "g": g,
        "model_branch_sets": (
            [[int(v) for v in b] for b in model_branch_sets]
            if model_branch_sets is not None
            else None
        ),
        "terminal_state": terminal_state,
        "certificate_statement": certificate_statement,
        "verified": bool(verified),
        "method": method,
        "reproduction": _screen_reproduction(terminal_state, method),
    }
    return record
