"""RED contract — Green–Ruzsa / Andrásfai structured SIZES (POOL-2, Wave 2 target).

Pins the extremal structured generator `green_ruzsa_sumfree(group)` keyed off the
ARITHMETIC CONDITION on |Γ| (RESEARCH Pitfall 6 — never an I/II/III numeral):
  * Z_31: 31 ≡ 1 (mod 3)  -> max sum-free size (31 − 1)/3 = 10
  * Z_53: 53 ≡ 2 (mod 3)  -> middle-interval size 18
Each structured S is additionally re-checked sum-free + symmetric + MAXIMAL by an
in-file brute oracle (A1/A2 — never trust a density formula un-rechecked).

Imports of the module-under-test are FUNCTION-LOCAL; bodies RED until Wave 2.
"""


def _abelian(factors):
    from alpha2.pool.sumfree.group import Abelian  # RED until Wave 2

    return Abelian(factors)


def _identity(g):
    return tuple(0 for _ in g.factors)


def _is_symmetric(S, g):
    return all(g.neg(a) in S for a in S)


def _is_sumfree(S, g):
    Sset = set(S)
    return all(g.add(a, b) not in Sset for a in Sset for b in Sset)


def _is_maximal(S, g):
    """No non-zero element outside S can be added keeping symmetric sum-freeness."""
    Sset = set(S)
    zero = _identity(g)
    for a in g.elements():
        if a == zero or a in Sset:
            continue
        cand = Sset | {a, g.neg(a)}
        if all(g.add(x, y) not in cand for x in cand for y in cand):
            return False       # a could have been added -> S was NOT maximal
    return True


def test_green_ruzsa_size_Z31_is_10():
    from alpha2.pool.sumfree.generate import green_ruzsa_sumfree

    g = _abelian((31,))              # 31 ≡ 1 (mod 3)
    S = set(green_ruzsa_sumfree(g))
    assert len(S) == 10
    assert _is_symmetric(S, g)
    assert _is_sumfree(S, g)
    assert _is_maximal(S, g)


def test_green_ruzsa_size_Z53_is_18():
    from alpha2.pool.sumfree.generate import green_ruzsa_sumfree

    g = _abelian((53,))              # 53 ≡ 2 (mod 3), middle interval
    S = set(green_ruzsa_sumfree(g))
    assert len(S) == 18
    assert _is_symmetric(S, g)
    assert _is_sumfree(S, g)
    assert _is_maximal(S, g)


def test_structured_passes_same_recheck_as_random():
    # A structured S must survive the SAME brute sum-free re-check the random path
    # is held to (A2: a wrong symmetric set could silently be non-sum-free).
    from alpha2.pool.sumfree.generate import green_ruzsa_sumfree

    for factors in [(31,), (53,)]:
        g = _abelian(factors)
        S = set(green_ruzsa_sumfree(g))
        assert _identity(g) not in S
        assert _is_symmetric(S, g) and _is_sumfree(S, g)
