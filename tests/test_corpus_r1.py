"""R1 corpus-validity test — every stored certificate re-verifies from JSON alone.

This is the corpus falsification anchor expressed as a test: it loads the stored
corpus (`paths.CORPUS`) and routes every record's trust decision ONLY through the
raise-based `verify_certificate` (never through an `assert`), so the assert-stripping
`python -O` CI job stays meaningful (Pitfall 6 / T-3-03). The `assert`s here wrap only
post-conditions the `-O` job does not depend on for correctness (slice size, the
k >= chi bound, the D.2 byte-equality) — the verification decision itself is the
exception `verify_certificate` raises, not an assertion.

`D2_MODEL` is embedded as a literal (no cross-test import from `test_fingerprint`),
matching the "embedded literal, no cross-test import" discipline of
`test_verifier_dash_O.py`.

Scope note: the strict (284, 12) / 296 family-count assertion lands in Plan 03 after
the full corpus freeze. Here we assert only the baseline+showpiece slice (>= 14
records, >= 1 triangle-free-process record) plus the (n=31, seed=1) == Appendix D.2
byte-equality — the single-RNG-contract-v1 drift tripwire.
"""
import json

from alpha2 import paths
from alpha2.corpus.verifier import verify_certificate

# Appendix D.2 K16 model for n=31, seed=1 (embedded literal; external authority).
D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]


def _load_corpus():
    with open(paths.CORPUS) as fh:
        return json.load(fh)


def family_counts(records):
    """Helper: {family -> count} over the stored records.

    Plan 03 asserts the strict (284 TFP, 12 Cayley) split after the full freeze; the
    slice test below asserts only >= 1 triangle-free-process record.
    """
    counts = {}
    for rec in records:
        fam = rec["provenance"]["family"]
        counts[fam] = counts.get(fam, 0) + 1
    return counts


def test_r1_all_records_reverify():
    records = _load_corpus()

    # Non-trivial slice: baseline (12) + showpieces (2) = 14.
    assert len(records) >= 14, ("corpus slice too small", len(records))

    # Every stored record re-verifies FROM JSON ALONE. The trust decision is the
    # raise-based verify_certificate call itself (it raises VerificationError on any
    # violation); the assert only checks the returned had_2 bound as a post-condition.
    for i, rec in enumerate(records):
        k = verify_certificate(rec)
        assert k >= rec["invariants"]["chi_G"], ("k < chi", i, k, rec["invariants"]["chi_G"])

    # Family-count helper wired here; slice asserts only >= 1 TFP (strict -> Plan 03).
    counts = family_counts(records)
    assert counts.get("triangle_free_process_complement", 0) >= 1, ("no TFP records", counts)

    # Byte-equal-to-D.2: the (n=31, seed=1) seed-provenance record's stored model is
    # exactly the Appendix D.2 K16 model. Any single-RNG-contract-v1 drift trips this.
    d2 = [
        r for r in records
        if r["provenance"].get("kind") == "seed"
        and r["provenance"].get("n") == 31
        and r["provenance"].get("seed") == 1
    ]
    assert len(d2) == 1, ("expected exactly one (n=31, seed=1) record", len(d2))
    assert d2[0]["model_branch_sets"] == D2_MODEL, (
        "stored (31,1) model != Appendix D.2", d2[0]["model_branch_sets"]
    )
