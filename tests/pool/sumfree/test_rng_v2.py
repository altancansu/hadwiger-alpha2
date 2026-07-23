"""RED contract — RNG contract v2 + descriptor rebuild (POOL-1/2, Wave 2 target).

Pins `alpha2.pool.sumfree.rng.subseed(master, stage)` (sha256-derived per-stage
subseeds, RESEARCH Pattern 2): stable, and STAGE-INDEPENDENT (deriving the
"generate" stage never shifts the "search" stage). Also pins the descriptor-driven
rebuild `alpha2.pool.sumfree.generate.adjacency_from_descriptor({invariant_factors,
S})` reproducing the identical adjacency byte-for-byte (cross-platform set-iteration
safety — rebuild from the STORED descriptor, never an RNG replay).

Imports of the modules-under-test are FUNCTION-LOCAL; bodies RED until Wave 2.
"""
import hashlib


def _expected_subseed(master, stage):
    h = hashlib.sha256(f"{master}:{stage}".encode()).digest()
    return int.from_bytes(h[:8], "big")


def test_subseed_is_sha256_derived_and_stable():
    from alpha2.pool.sumfree.rng import subseed

    a = subseed(12345, "sumfree-generate")
    assert isinstance(a, int)
    assert a == subseed(12345, "sumfree-generate")          # stable
    assert a == _expected_subseed(12345, "sumfree-generate")  # exact sha256 recipe


def test_subseed_is_stage_independent():
    from alpha2.pool.sumfree.rng import subseed

    gen = subseed(7, "sumfree-generate")
    search = subseed(7, "heuristic-search")
    assert gen != search, "distinct stages must yield distinct subseeds"
    # Each stage is derived independently from the master, so re-deriving one stage
    # cannot shift the other.
    assert subseed(7, "sumfree-generate") == gen
    assert subseed(7, "heuristic-search") == search


def test_subseed_master_sensitive():
    from alpha2.pool.sumfree.rng import subseed

    assert subseed(1, "sumfree-generate") != subseed(2, "sumfree-generate")


def test_descriptor_rebuild_is_byte_identical():
    from alpha2.pool.sumfree.generate import adjacency_from_descriptor

    d = {"invariant_factors": [5], "S": [[1], [4]]}
    adj1 = adjacency_from_descriptor(d)
    adj2 = adjacency_from_descriptor(d)
    assert [set(s) for s in adj1] == [set(s) for s in adj2]     # deterministic
    # Rebuild matches the hand-built Cay(Z_5, ±1) == C_5 adjacency.
    assert [set(s) for s in adj1] == [{1, 4}, {0, 2}, {1, 3}, {2, 4}, {0, 3}]


def test_descriptor_rebuild_independent_of_S_order():
    from alpha2.pool.sumfree.generate import adjacency_from_descriptor

    d1 = {"invariant_factors": [5], "S": [[1], [4]]}
    d2 = {"invariant_factors": [5], "S": [[4], [1]]}   # same set, reordered
    assert [set(s) for s in adjacency_from_descriptor(d1)] == [
        set(s) for s in adjacency_from_descriptor(d2)
    ]
