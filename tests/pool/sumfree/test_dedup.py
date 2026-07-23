"""RED contract — canonical isomorph dedup, WL-hash forbidden (POOL-2, Wave 2).

Pins `alpha2.pool.sumfree.dedup.dedup(descriptors)`: distinct (Γ, S) descriptors
whose Cayley graphs H are ISOMORPHIC collapse to one canonical class (keeping the
first descriptor as provenance); non-isomorphic H stay separate. The canonical key
MUST be a nauty canonical form (`pynauty.certificate` / `shortg`) — NEVER the
networkx Weisfeiler–Lehman hash (CLAUDE.md "What NOT to Use": WL-hash is not
canonical, silent collisions violate the exactness discipline).

Hand example: over Z_5, S = {1, 4} = ±1 and S = {2, 3} = ±2 both give a 5-cycle
(C_5) — distinct connection sets, isomorphic H -> one class. C_7 (Z_7, ±1) is a
different graph -> a second class.

Imports of the module-under-test are FUNCTION-LOCAL; bodies RED until Wave 2.
"""

_D_C5_pm1 = {"invariant_factors": [5], "S": [[1], [4]]}   # Cay(Z_5, ±1) == C_5
_D_C5_pm2 = {"invariant_factors": [5], "S": [[2], [3]]}   # Cay(Z_5, ±2) == C_5 (iso)
_D_C7_pm1 = {"invariant_factors": [7], "S": [[1], [6]]}   # Cay(Z_7, ±1) == C_7


def test_isomorphic_descriptors_collapse_to_one_class():
    from alpha2.pool.sumfree.dedup import dedup

    classes = dedup([_D_C5_pm1, _D_C5_pm2])
    assert len(classes) == 1, "isomorphic H (both C_5) must collapse to one class"


def test_non_isomorphic_descriptors_stay_separate():
    from alpha2.pool.sumfree.dedup import dedup

    classes = dedup([_D_C5_pm1, _D_C7_pm1])
    assert len(classes) == 2, "C_5 and C_7 are non-isomorphic -> two classes"


def test_first_descriptor_kept_as_provenance():
    from alpha2.pool.sumfree.dedup import dedup

    classes = dedup([_D_C5_pm1, _D_C5_pm2])
    # The single surviving class keeps the FIRST (Γ, S) descriptor as provenance.
    (only_class,) = classes
    rep = only_class["representative"] if isinstance(only_class, dict) else only_class
    assert rep == _D_C5_pm1 or rep.get("S") == [[1], [4]]


def test_dedup_uses_canonical_certificate_never_wl_hash():
    # Mechanism guard (mirrors the CHI-01 source-inspection discipline): the dedup
    # key must be a nauty canonical form, and the networkx WL-hash must never appear.
    import inspect

    from alpha2.pool.sumfree import dedup as dedup_mod

    src = inspect.getsource(dedup_mod).lower()
    assert ("certificate" in src) or ("shortg" in src), (
        "dedup must key off pynauty.certificate / shortg (canonical)"
    )
    assert "weisfeiler" not in src, "WL-hash is forbidden as a dedup key (CLAUDE.md)"
    assert "wl_hash" not in src
    assert "graph_hash" not in src
