"""RED contract — g(G)-screen certificate schema (POOL-2, Wave 3 target).

Pins `alpha2.pool.sumfree.schema.build_gscreen_record(...)`: a plain
JSON-serializable dict (round-trips through json.dumps/json.loads with
field-equality) mirroring the CDM schema shape, carrying:

  * provenance — descriptor identity {invariant_factors, S, tag: structured|random},
  * H_edges + H_edges_sha256 (canonical [min,max] pairs),
  * chi, had_2, had_3 (or null when RESISTANT — no exact bound proved),
  * the computed screen gap g = (chi - had_k)/chi (or null when RESISTANT),
  * terminal_state (KILLED | SHC_CANDIDATE | RESISTANT),
  * a certificate_statement string (the honest g(G) claim; honesty enforced in
    test_screen).

Imports of the module-under-test are FUNCTION-LOCAL so `--collect-only` stays
clean; bodies are RED until Wave 3 lands `pool/sumfree/schema.py`.
"""
import json


def _provenance():
    return {
        "kind": "descriptor",
        "family": "sumfree_cayley",
        "tag": "random",
        "n": 5,
        "invariant_factors": [5],
        "S": [[1], [4]],
    }


def test_build_gscreen_record_round_trips_through_json():
    from alpha2.pool.sumfree.schema import build_gscreen_record  # RED until Wave 3

    rec = build_gscreen_record(
        provenance=_provenance(),
        H_edges=[[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]],
        chi=3,
        had_2=3,
        had_3=3,
        terminal_state="KILLED",
        certificate_statement="had_3 = 3 >= chi = 3; packs; g = 0.",
        method="heuristic K_chi HIT + trust-root verify",
    )
    assert rec == json.loads(json.dumps(rec)), "record must be pure-JSON round-trippable"


def test_gscreen_record_carries_descriptor_provenance_and_tag():
    from alpha2.pool.sumfree.schema import build_gscreen_record

    rec = build_gscreen_record(
        provenance=_provenance(),
        H_edges=[[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]],
        chi=3,
        had_2=3,
        had_3=3,
        terminal_state="KILLED",
        certificate_statement="packs",
        method="m",
    )
    prov = rec["provenance"]
    assert prov["invariant_factors"] == [5]
    assert prov["S"] == [[1], [4]]
    assert prov["tag"] in ("structured", "random")


def test_gscreen_record_carries_h_edges_sha256_and_computed_g():
    from alpha2.pool.sumfree.schema import build_gscreen_record

    rec = build_gscreen_record(
        provenance=_provenance(),
        H_edges=[[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]],
        chi=3,
        had_2=3,
        had_3=3,
        terminal_state="KILLED",
        certificate_statement="packs",
        method="m",
    )
    assert isinstance(rec["H_edges_sha256"], str) and len(rec["H_edges_sha256"]) == 64
    # g is derived by the schema, not trusted from the caller.
    assert rec["g"] == (3 - 3) / 3


def test_resistant_record_has_null_had_and_null_g():
    from alpha2.pool.sumfree.schema import build_gscreen_record

    rec = build_gscreen_record(
        provenance=_provenance(),
        H_edges=[[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]],
        chi=3,
        had_2=None,          # exact bound not proved in the deterministic budget
        had_3=None,
        terminal_state="RESISTANT",
        certificate_statement=(
            "heuristic did not find a K_chi minor and no exact bound was proved in "
            "budget; queued for E3; NOT a result."
        ),
        method="heuristic MISS above ILP frontier",
    )
    assert rec["terminal_state"] == "RESISTANT"
    assert rec["had_3"] is None
    assert rec["g"] is None, "a RESISTANT instance is never a g>0 point"
