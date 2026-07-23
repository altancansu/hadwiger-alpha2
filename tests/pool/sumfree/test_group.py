"""RED contract — finite abelian Gamma arithmetic (POOL-2, Wave 2 target).

Pins `alpha2.pool.sumfree.group.Abelian(factors)`: invariant-factor representation
with deterministic `.elements()`, component-wise `.add`/`.neg` mod the factors, an
involutive negation, and V5 input validation (reject non-int / bool / oversized
factors, cap n <= ~500 before any downstream enumeration/subprocess).

Every import of the module-under-test is FUNCTION-LOCAL so `--collect-only` stays
clean; the bodies are RED until Wave 2 lands `pool/sumfree/group.py`.
"""
import pytest


def _abelian(factors):
    from alpha2.pool.sumfree.group import Abelian  # RED until Wave 2

    return Abelian(factors)


def test_order_n_is_product_of_factors():
    assert _abelian((5,)).n == 5
    assert _abelian((3, 3)).n == 9
    assert _abelian((3, 15)).n == 45


def test_elements_deterministic_distinct_and_repeatable():
    g = _abelian((3, 3))
    els = g.elements()
    assert len(els) == 9
    assert len(set(els)) == 9          # all distinct
    assert g.elements() == els         # deterministic / repeatable
    assert (0, 0) in els               # identity present


def test_elements_are_lexicographic_product_order():
    # itertools.product order: identity first, last coordinate varies fastest.
    g = _abelian((2, 3))
    assert g.elements() == [
        (0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2),
    ]


def test_add_is_componentwise_mod_invariant_factors():
    g = _abelian((3, 3))
    assert g.add((2, 2), (2, 2)) == (1, 1)     # (4, 4) mod (3, 3)
    assert g.add((0, 0), (1, 2)) == (1, 2)     # identity is neutral
    assert g.add((1, 2), (2, 1)) == (0, 0)     # inverse pair sums to identity


def test_neg_is_componentwise_and_involutive():
    g = _abelian((7,))
    zero = (0,)
    for a in g.elements():
        assert g.neg(g.neg(a)) == a            # neg(neg(a)) == a
        assert g.add(a, g.neg(a)) == zero      # a + (-a) == 0


def test_neg_involution_on_noncyclic_group():
    g = _abelian((3, 3))
    for a in g.elements():
        assert g.neg(g.neg(a)) == a
        assert g.add(a, g.neg(a)) == (0, 0)


def test_rejects_non_int_factor():
    with pytest.raises((TypeError, ValueError)):
        _abelian((5.0,))


def test_rejects_bool_factor():
    # bool is an int subclass; the V5 validator must still reject it.
    with pytest.raises((TypeError, ValueError)):
        _abelian((True,))


def test_rejects_nonpositive_factor():
    with pytest.raises((TypeError, ValueError)):
        _abelian((0,))
    with pytest.raises((TypeError, ValueError)):
        _abelian((-3,))


def test_rejects_oversized_group_v5_cap():
    # n must be bounded (cap ~500) BEFORE any enumeration / subprocess (V5, T-7-08).
    with pytest.raises(ValueError):
        _abelian((1000,))
    with pytest.raises(ValueError):
        _abelian((23, 23))   # 529 > 500 cap
