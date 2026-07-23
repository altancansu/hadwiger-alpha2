"""Sum-free generators + abelian Cayley adjacency (POOL-2, Wave 2 GREEN).

Generalizes the STRUCTURE of the frozen `generators/cayley.py` (Z_p, corpus-locked)
to an arbitrary finite abelian Γ (`pool/sumfree/group.Abelian`) WITHOUT importing or
editing the frozen module (RESEARCH Pitfall 4 — corpus byte-reproduction depends on
it staying untouched).

Three routes to a symmetric (`S = −S`) sum-free set `S ⊂ Γ \\ {0}`:

  * `random_maximal_symmetric_sumfree(group, rng)` — greedy maximal (the pseudorandom
    counterpoint; consumes the caller's injected `rng` via `rng.shuffle`);
  * `middle_interval_sumfree(group)` — the Andrásfai middle-third structured set;
  * `green_ruzsa_sumfree(group)` — the extremal max-density set keyed off the
    ARITHMETIC condition on |Γ| (smallest prime ≡2 mod3 / 3∣n / all ≡1 mod3), NEVER
    an I/II/III numeral (RESEARCH Pitfall 6, A1).

For a symmetric sum-free `S`, `H = Cay(Γ, S)` is triangle-free, so `G = H̄` is α=2.
`cayley_adj_abelian` builds `H` as `list[set[int]]` over the LOCKED
`itertools.product` element→index map (`group.elements()`); `adjacency_from_descriptor`
rebuilds it byte-identically from a stored `{invariant_factors, S}` descriptor (never
an RNG replay — cross-platform set-iteration safety).

The load-bearing net is `verify_sumfree_maximal`: EVERY generator re-checks its own
output (symmetric + sum-free + zero-free + maximal, raise-based) before returning, so
a wrong density formula can never yield a bad instance (RESEARCH Open Q1/A1/A2 made
non-fatal by this runtime re-check). stdlib only.
"""
from alpha2.pool.sumfree.group import Abelian

# Provenance tags for the descriptor `kind` field (structured vs random tracking).
KIND_MIDDLE_INTERVAL = "structured:middle_interval"
KIND_GREEN_RUZSA = "structured:green_ruzsa"
KIND_RANDOM_GREEDY = "random_greedy"


def _identity(group):
    return tuple(0 for _ in group.factors)


def can_add(S, group, a):
    """Abelian generalization of the frozen Z_p `can_add` (RESEARCH Pattern 1).

    True iff symmetrically adding `a` (and `neg(a)`) to `S` keeps it sum-free — i.e.
    introduces no sum relation `u + x = z` with all of u, x, z in `S ∪ {a, neg(a)}`.
    """
    b = group.neg(a)
    T = set(S) | {a, b}
    for u in (a, b):
        for x in T:
            if group.add(u, x) in T:            # u + x = z violation
                return False
            if group.add(u, group.neg(x)) in T:  # x + (u - x) = u violation
                return False
    return True


def verify_sumfree_maximal(group, S):
    """Raise-based re-check: S is symmetric + sum-free + zero-free + MAXIMAL.

    The mandatory guard (Pitfall 6) every generator calls before returning. Any
    violation raises ValueError, so a mis-derived structured set can never surface
    as a valid instance. Returns True on success.
    """
    Sset = set(S)
    zero = _identity(group)
    if zero in Sset:
        raise ValueError("0 (identity) must not be in a sum-free connection set")
    for a in Sset:
        if group.neg(a) not in Sset:
            raise ValueError(f"S is not symmetric: neg({a}) missing")
    for a in Sset:
        for b in Sset:
            if group.add(a, b) in Sset:
                raise ValueError(f"S is not sum-free: {a} + {b} in S")
    for a in group.elements():
        if a == zero or a in Sset:
            continue
        cand = Sset | {a, group.neg(a)}
        if all(group.add(x, y) not in cand for x in cand for y in cand):
            raise ValueError(f"S is not maximal: {a} could be added")
    return True


def random_maximal_symmetric_sumfree(group, rng):
    """Greedy maximal symmetric sum-free S over Γ (generalizes the frozen Z_p code).

    Consumes the caller's injected `rng` via `rng.shuffle` (never seeds internally),
    mirroring `generators/cayley.random_maximal_symmetric_sumfree`. Re-checked before
    return.
    """
    zero = _identity(group)
    S = set()
    elems = [e for e in group.elements() if e != zero]
    changed = True
    while changed:
        changed = False
        rng.shuffle(elems)
        for a in elems:
            if a in S:
                continue
            if can_add(S, group, a):
                S.add(a)
                S.add(group.neg(a))
                changed = True
    verify_sumfree_maximal(group, S)
    return S


def _middle_interval_residues(m):
    """The middle-third residue band of Z_m: {k : ceil((m+2)/3) ≤ k ≤ floor(2m/3)}.

    Symmetric (k and m−k both land in the band) and — for the extremal cyclic cases
    used here — sum-free (the smallest sum of two band elements exceeds the band and
    wraps below it). Callers must still verify via `verify_sumfree_maximal`.
    """
    lo, hi = (m + 2) // 3, (2 * m) // 3
    return {k % m for k in range(lo, hi + 1)}


def _cyclic_pullback(group, p, residues):
    """Pull back a Z_p residue set through φ(x) = x mod p over a cyclic Γ = Z_n.

    S = { (x,) : x ∈ Z_n, x mod p ∈ residues } \\ {0}. A pullback of a symmetric
    sum-free set is symmetric sum-free.
    """
    n = group.n
    S = {(x,) for x in range(n) if (x % p) in residues}
    S.discard((0,))
    return S


def _prime_factors(n):
    """Distinct prime divisors of n by stdlib trial division (n ≤ 500, trivial)."""
    primes = set()
    m, d = n, 2
    while d * d <= m:
        while m % d == 0:
            primes.add(d)
            m //= d
        d += 1
    if m > 1:
        primes.add(m)
    return primes


def middle_interval_sumfree(group):
    """Andrásfai middle-third structured symmetric sum-free set over cyclic Γ = Z_n."""
    if len(group.factors) != 1:
        raise ValueError("middle_interval_sumfree supports cyclic Γ = Z_n only")
    n = group.n
    S = _cyclic_pullback(group, n, _middle_interval_residues(n))
    verify_sumfree_maximal(group, S)
    return S


def green_ruzsa_sumfree(group):
    """Extremal (max-density) structured sum-free S keyed off the ARITHMETIC of |Γ|.

    Cyclic Γ = Z_n only (RESEARCH Pitfall 6 — key off the arithmetic condition, never
    an I/II/III numeral; the raise-based `verify_sumfree_maximal` is the load-bearing
    net that makes an unpinned formula non-fatal):

      * smallest prime p ∣ n with p ≡ 2 (mod 3) → pull back the Z_p middle interval
        (density 1/3 + 1/(3p));
      * every prime divisor ≡ 1 (mod 3) → the Z_n middle interval is extremal of size
        (p−1)/3 for prime n;
      * 3 ∣ n (no prime ≡ 2 mod 3) → the exact coset-membership formula is the
        RESEARCH-flagged ambiguous case (Open Q1) and is deliberately NOT constructed
        here (that Γ is served by the random-greedy route / excluded from the grid).
    """
    if len(group.factors) != 1:
        raise ValueError(
            "green_ruzsa_sumfree supports cyclic Γ = Z_n only "
            "(non-cyclic 'all primes ≡1 mod3' type excluded — RESEARCH Open Q1)"
        )
    n = group.n
    primes = _prime_factors(n)
    primes_2mod3 = sorted(p for p in primes if p % 3 == 2)
    if primes_2mod3:
        p = primes_2mod3[0]  # smallest prime ≡ 2 (mod 3)
        S = _cyclic_pullback(group, p, _middle_interval_residues(p))
    elif n % 3 == 0:
        raise NotImplementedError(
            "Green–Ruzsa 3∣n coset construction is the RESEARCH-flagged ambiguous "
            "case (Open Q1) — use the random-greedy route for such Γ"
        )
    else:
        # Every prime divisor ≡ 1 (mod 3): the Z_n middle interval is extremal.
        S = _cyclic_pullback(group, n, _middle_interval_residues(n))
    verify_sumfree_maximal(group, S)
    return S


def cayley_adj_abelian(group, S):
    """H = Cay(Γ, S) as list[set[int]] over the LOCKED group.elements() index map."""
    elems = group.elements()
    index = {e: i for i, e in enumerate(elems)}
    adj = [set() for _ in elems]
    for e in elems:
        i = index[e]
        for s in S:
            adj[i].add(index[group.add(e, tuple(s))])
    return adj


def adjacency_from_descriptor(descriptor):
    """Rebuild H adjacency byte-identically from a stored {invariant_factors, S}.

    Descriptor-driven (never an RNG replay): the same descriptor always yields the
    same `list[set[int]]`, independent of the order S was stored in (S is a set).
    """
    group = Abelian(descriptor["invariant_factors"])
    S = {tuple(s) for s in descriptor["S"]}
    return cayley_adj_abelian(group, S)


def make_descriptor(group, S, kind):
    """Emit the reproducibility descriptor {invariant_factors, S(sorted), kind}."""
    return {
        "invariant_factors": list(group.factors),
        "S": sorted(tuple(s) for s in S),
        "kind": kind,
    }
