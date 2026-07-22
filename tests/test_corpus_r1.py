"""R1 corpus-validity test — every stored certificate re-verifies from JSON alone.

This is the corpus falsification anchor expressed as a test: it loads the stored
corpus (`paths.CORPUS`) and routes every record's trust decision ONLY through the
raise-based `verify_certificate` (never through an `assert`), so the assert-stripping
`python -O` CI job stays meaningful (Pitfall 6 / T-3-03). The `assert`s here wrap only
post-conditions the `-O` job does not depend on for correctness (slice size, the
k >= chi bound, the D.2 byte-equality) — the verification decision itself is the
exception `verify_certificate` raises, not an assertion.

`D2_MODEL` / `D3_MODEL` are embedded as literals (no cross-test import from
`test_fingerprint`), matching the "embedded literal, no cross-test import" discipline
of `test_verifier_dash_O.py`.

Hard count gate (Plan 03, after the full corpus freeze): the corpus is EXACTLY 296
records with per-family counts (284 triangle-free-process + 12 Cayley), and the
seed-137 record's stored model is byte-equal to the Appendix D.3 K16 literal. The
(n=31, seed=1) == Appendix D.2 byte-equality remains the single-RNG-contract-v1
drift tripwire.
"""
import json

from alpha2 import paths
from alpha2.corpus.verifier import verify_certificate

# Appendix D.2 K16 model for n=31, seed=1 (embedded literal; external authority).
D2_MODEL = [
    [16, 20], [14, 3], [11, 4], [10, 19], [26, 9], [6, 29], [18, 25], [13, 24],
    [30, 8], [15, 28], [27, 12], [23, 7], [17, 2], [0], [21, 22], [1, 5],
]

# Appendix D.3 K16 model for n=31, seed=137 (embedded literal; external authority).
# 9 pairs + 7 singletons; carried solver-free (Phase 3). Any RNG-contract-v1 or
# literal-carry drift trips the byte-equality below.
D3_MODEL = [
    [2, 20], [4, 7], [8, 18], [9, 13], [12, 27], [16, 22], [17, 24],
    [19, 29], [26, 28], [0], [1], [3], [10], [11], [21], [23],
]


def _load_corpus():
    with open(paths.CORPUS) as fh:
        return json.load(fh)


def family_counts(records):
    """Helper: {family -> count} over the stored records."""
    counts = {}
    for rec in records:
        fam = rec["provenance"]["family"]
        counts[fam] = counts.get(fam, 0) + 1
    return counts


def _find_seed_record(records, n, seed):
    """The single seed-kind (n, seed) record, or raise on a miscount."""
    hits = [
        r for r in records
        if r["provenance"].get("kind") == "seed"
        and r["provenance"].get("n") == n
        and r["provenance"].get("seed") == seed
    ]
    assert len(hits) == 1, (f"expected exactly one (n={n}, seed={seed}) record", len(hits))
    return hits[0]


def test_r1_all_records_reverify():
    records = _load_corpus()

    # HARD count gate (post-freeze): exactly 296 records, split (284 TFP, 12 Cayley).
    assert len(records) == 296, ("corpus is not exactly 296", len(records))
    counts = family_counts(records)
    tfp = counts.get("triangle_free_process_complement", 0)
    cay = counts.get("cayley_maximal_sumfree_Zp", 0)
    assert (tfp, cay) == (284, 12), ("family counts != (284, 12)", counts)

    # Every stored record re-verifies FROM JSON ALONE. The trust decision is the
    # raise-based verify_certificate call itself (it raises VerificationError on any
    # violation); the assert only checks the returned had_2 bound as a post-condition.
    for i, rec in enumerate(records):
        k = verify_certificate(rec)
        assert k >= rec["invariants"]["chi_G"], ("k < chi", i, k, rec["invariants"]["chi_G"])

    # Byte-equal-to-D.2: the (n=31, seed=1) seed record's stored model is exactly the
    # Appendix D.2 K16 model. Any single-RNG-contract-v1 drift trips this.
    d2 = _find_seed_record(records, 31, 1)
    assert d2["model_branch_sets"] == D2_MODEL, (
        "stored (31,1) model != Appendix D.2", d2["model_branch_sets"]
    )

    # Byte-equal-to-D.3: the (n=31, seed=137) exact-study record's stored model is
    # exactly the Appendix D.3 K16 literal (carried solver-free). Drift trips this.
    d3 = _find_seed_record(records, 31, 137)
    assert d3["model_branch_sets"] == D3_MODEL, (
        "stored (31,137) model != Appendix D.3", d3["model_branch_sets"]
    )
