"""Finite abelian group Γ over invariant factors (POOL-2, stdlib ONLY).

`Abelian(factors)` represents `Γ = Z_{d₁} × … × Z_{d_k}` by its invariant-factor
tuple `(d₁,…,d_k)`. Elements are integer tuples; `add` is component-wise mod the
factors, `neg` is component-wise negation (`neg(neg(a)) == a`). Enumeration is the
deterministic `itertools.product` order — identity first, last coordinate varies
fastest — so vertex `i` of `Cay(Γ, S)` is the `i`-th enumerated tuple (vertex 0 is
the identity). This ordering is the LOCKED adjacency convention the whole
`pool/sumfree` package (generate / dedup / descriptor rebuild) depends on.

Input validation (V5, T-8-05) runs in `__init__` BEFORE anything is enumerated:
factors must be genuine positive ints (`bool` rejected — it is an int subclass), and
the group order `n = ∏ dᵢ` is capped at `N_MAX = 500` so an oversized Γ can never
trigger an unbounded `itertools.product` enumeration or a downstream subprocess DoS.
Mirrors the `pool/cdm/generate._validate` int-and-bound pattern.

No new dependency — stdlib `itertools` only.
"""
from itertools import product

# DoS bound (T-8-05): the P2 grid is odd |Γ| = 31–~500. A Γ larger than this is
# validated-and-rejected rather than enumerated (the enumeration + every downstream
# nauty/solver step is O(n)–O(n²) in the group order).
N_MAX = 500


def _validate_factors(factors):
    """Int-validate + bound the invariant factors BEFORE constructing the group.

    Raises ValueError on any non-int / bool / non-positive factor, or when the
    product order exceeds N_MAX. `bool` is rejected explicitly (it is an int
    subclass) so `Abelian((True,))` cannot slip a `1` past the type gate.
    """
    factors = tuple(factors)
    if not factors:
        raise ValueError("invariant factors must be a non-empty sequence")
    n = 1
    for d in factors:
        if isinstance(d, bool) or not isinstance(d, int):
            raise ValueError(
                f"each invariant factor must be an int, got {type(d).__name__}"
            )
        if d < 1:
            raise ValueError(f"each invariant factor must be positive, got {d}")
        n *= d
    if n > N_MAX:
        raise ValueError(
            f"group order n={n} exceeds the DoS cap N_MAX={N_MAX} (T-8-05); "
            "validate-and-reject before any enumeration"
        )
    return factors, n


class Abelian:
    """Finite abelian Γ = Z_{d₁} × … × Z_{d_k} by invariant factors (validated)."""

    def __init__(self, factors):
        self.factors, self.n = _validate_factors(factors)

    def elements(self):
        """Deterministic enumeration (itertools.product order): identity first."""
        return list(product(*(range(d) for d in self.factors)))

    def add(self, a, b):
        """Component-wise addition mod the invariant factors."""
        return tuple((x + y) % d for x, y, d in zip(a, b, self.factors))

    def neg(self, a):
        """Component-wise negation; neg(neg(a)) == a and a + neg(a) == 0."""
        return tuple((-x) % d for x, d in zip(a, self.factors))
