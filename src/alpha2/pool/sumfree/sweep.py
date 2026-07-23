"""Structured-vs-random g(G) grid sweep + aggregation (POOL-2, the P2 break-hunt).

This is the driver the whole phase exists to feed: it enumerates the odd |Γ| = 31–~500
grid (all cyclic n plus a curated non-cyclic set), builds structured (Green–Ruzsa /
Andrásfai middle-interval) and random-greedy sum-free Cayley instances, canonically
dedups the MERGED streams (`dedup.dedup` — a nauty canonical certificate; WL-hash
FORBIDDEN), adjudicates each survivor through `adjudicate_grid_point` under a
DETERMINISTIC budget on BOTH co-equal backends, and aggregates the falsifiable plot
data: `g` vs group order, structured vs random, gate-survival rate, and RESISTANT-rate
by family.

Honesty discipline threaded end to end (never relaxed here — this module changes only
WHAT WE RECORD, never what counts as a break):

  * PRIMARY (pre-registered): the LOCKED prediction — `g(G) = (χ − had_k)/χ` and the
    RESISTANT-rate, structured vs random, vs |Γ|. That is THE hypothesis test.
  * SECONDARY (exploratory): every other cross-section recorded in the observable bank
    (rank, exponent, prime-residue signature, cyclic?, |Aut| proxy; per-instance
    had₃−had₂, abs_gap, S_density, det_work). A hit here is HYPOTHESIS-GENERATING, not a
    result — it must be re-tested as a fresh pre-registered prediction on new seeds
    before it is reported. The aggregate records how many cross-sections were examined.
  * The exact-window boundary (08-05 `exact_window_max`) is load-bearing: a non-packing
    outcome at order ≤ window is an exact `g>0` candidate; ABOVE the window it is
    RESISTANT (E3 queue), NEVER a reported `g>0` (RESEARCH §"Consequence").

Determinism (T-8-07): every recorded verdict is a deterministic function of (n, seed) —
the adjudicator bounds BOTH backends deterministically (CP-SAT det_time, CBC det_nodes)
and runs single-worker. Parallelism here is INSTANCE-LEVEL BREADTH ONLY; the sweep event
stream is written by the parent in descriptor order, so contention can never reorder or
flip a recorded verdict. A wall-clock cutoff on any recorded-verdict path is forbidden.

The unresolved Green–Ruzsa non-cyclic "all primes ≡ 1 (mod 3)" type-II case (RESEARCH
Open Q1) is EXCLUDED from the grid with a logged reason; the `verify_sumfree_maximal`
net still runs on every generated S, so a wrong density formula can never surface a bad
instance regardless.
"""
import math

from alpha2.battery.log import append_event
from alpha2.pool.sumfree.dedup import dedup
from alpha2.pool.sumfree.generate import (
    KIND_GREEN_RUZSA,
    KIND_MIDDLE_INTERVAL,
    KIND_RANDOM_GREEDY,
    green_ruzsa_sumfree,
    make_descriptor,
    middle_interval_sumfree,
    random_maximal_symmetric_sumfree,
)
from alpha2.pool.sumfree.group import N_MAX, Abelian
from alpha2.pool.sumfree.rng import gen_rng

_SUBSYSTEM = "pool/sumfree"

# The odd |Γ| grid floor (RESEARCH / Locked Decision 1: the break-hunt starts at 31).
ORDER_MIN = 31

# The curated NON-CYCLIC set (RESEARCH Open Q2, RESOLVED): each involves the primes 3
# and/or 5 (both ≢ 1 mod 3), so none is caught by the type-II exclusion guard below —
# but the guard is applied regardless so the exclusion is explicit and future-proof.
#   Z_3^4 = 81, Z_3×Z_27 = 81, Z_5^3 = 125, Z_3^2×Z_5 = 45, Z_9×Z_9 = 81.
DEFAULT_NONCYCLIC = (
    (3, 3, 3, 3),   # Z_3^4  = 81
    (3, 27),        # Z_3×Z_27 = 81
    (5, 5, 5),      # Z_5^3  = 125
    (3, 3, 5),      # Z_3^2×Z_5 = 45
    (9, 9),         # Z_9×Z_9 = 81
)

# The three families the sweep contrasts (structured × 2 + random).
STRUCTURED_KINDS = (KIND_GREEN_RUZSA, KIND_MIDDLE_INTERVAL)
ALL_KINDS = STRUCTURED_KINDS + (KIND_RANDOM_GREEDY,)

_STRUCTURED_GENERATORS = {
    KIND_GREEN_RUZSA: green_ruzsa_sumfree,
    KIND_MIDDLE_INTERVAL: middle_interval_sumfree,
}


# --------------------------------------------------------------------------- #
# Group arithmetic + the observable bank (all zero solver cost, from Γ alone)
# --------------------------------------------------------------------------- #
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


def _p_adic(d, p):
    """The exponent of p in d (p-adic valuation)."""
    e = 0
    while d % p == 0:
        d //= p
        e += 1
    return e


def _group_order(factors):
    return math.prod(factors)


def _exponent(factors):
    """The group exponent = largest element order = lcm of the invariant factors."""
    return math.lcm(*factors)


def _rank(factors):
    """The rank = max over primes p | n of the p-rank (# factors divisible by p).

    The p-rank is an isomorphism invariant, so this is correct for ANY direct-product
    representation of Γ (cyclic Γ has rank 1; Z_3^4 has rank 4; Z_9×Z_9 has rank 2).
    """
    n = _group_order(factors)
    if n == 1:
        return 0
    return max(sum(1 for d in factors if d % p == 0) for p in _prime_factors(n))


def _is_cyclic(factors):
    """Γ is cyclic iff its exponent equals its order (⟺ rank ≤ 1)."""
    return _exponent(factors) == _group_order(factors)


def _aut_p_group(p, part):
    """|Aut| of the abelian p-group of type `part` (Hillar–Rhea, Amer. Math. Monthly).

    `part` is the multiset of exponents e_i of the Z_{p^{e_i}} primary factors. Verified
    against |Aut(Z_p)| = p−1, |Aut(Z_p^2)| = (p²−1)(p²−p), |Aut(Z_{p²})| = p(p−1).
    """
    e = sorted(part, reverse=True)
    n = len(e)
    d = [max(l for l in range(1, n + 1) if e[l - 1] == e[k - 1]) for k in range(1, n + 1)]
    c = [min(l for l in range(1, n + 1) if e[l - 1] == e[k - 1]) for k in range(1, n + 1)]
    t1 = math.prod(p ** d[k - 1] - p ** (k - 1) for k in range(1, n + 1))
    t2 = math.prod((p ** e[j - 1]) ** (n - d[j - 1]) for j in range(1, n + 1))
    t3 = math.prod((p ** (e[i - 1] - 1)) ** (n - c[i - 1] + 1) for i in range(1, n + 1))
    return t1 * t2 * t3


def _aut_order(factors):
    """Exact |Aut(Γ)| = ∏_p |Aut(Sylow_p(Γ))| (the symmetry cross-section axis).

    Exact (not a fuzzy proxy) but SECONDARY/exploratory: it never gates a verdict, so a
    bug here can only mislabel an exploratory group-by axis, never manufacture a break.
    """
    n = _group_order(factors)
    order = 1
    for p in sorted(_prime_factors(n)):
        part = [e for d in factors if (e := _p_adic(d, p)) > 0]
        order *= _aut_p_group(p, part)
    return order


def _elementary_abelian(factors):
    """Γ ≅ Z_p^k (exponent prime) — the maximal-symmetry case the observable bank probes."""
    exp = _exponent(factors)
    return len(_prime_factors(exp)) == 1 and exp in _prime_factors(_group_order(factors))


def group_observables(factors):
    """The zero-cost group-structure cross-sections (SECONDARY/exploratory bank).

    All derived from the abelian descriptor alone — no solver touched. These are the
    group-by axes the observable bank mines for a structural obstruction to minor-packing
    (order, rank, exponent, prime-residue signature, symmetry) that would survive even if
    no counterexample ever appears.
    """
    n = _group_order(factors)
    primes = _prime_factors(n)
    return {
        "order": n,
        "rank": _rank(factors),
        "exponent": _exponent(factors),
        "n_prime_divisors": len(primes),
        "n_primes_1mod3": sum(1 for p in primes if p % 3 == 1),
        "n_primes_2mod3": sum(1 for p in primes if p % 3 == 2),
        "has_prime_3": 3 in primes,
        "cyclic": _is_cyclic(factors),
        "elementary_abelian": _elementary_abelian(factors),
        "aut_order": _aut_order(factors),
    }


def _excluded_gr_noncyclic(factors):
    """The RESEARCH Open Q1 exclusion: a NON-CYCLIC Γ whose EVERY prime divisor ≡ 1 mod 3.

    The exact coset-membership extremal formula for this "all primes ≡ 1 mod 3" non-cyclic
    type-II case is not yet pinned (T-8-17), so such Γ are skipped with a logged reason.
    Cyclic Γ (e.g. Z_31, all primes ≡ 1 mod 3 but cyclic) are NOT excluded.
    """
    n = _group_order(factors)
    primes = _prime_factors(n)
    return (not _is_cyclic(factors)) and all(p % 3 == 1 for p in primes)


# --------------------------------------------------------------------------- #
# Grid enumeration + canonical dedup of the merged structured/random streams
# --------------------------------------------------------------------------- #
def _log(path, **event):
    append_event({"subsystem": _SUBSYSTEM, **event}, path=path)


def _tag_for(kind):
    """The coarse structured|random tag adjudicate uses for S-resolution/provenance."""
    return "structured" if kind.startswith("structured:") else "random"


def _descriptor(group, S, kind):
    """A dedup/adjudicate-ready descriptor {invariant_factors, S, kind, tag}."""
    d = make_descriptor(group, S, kind)   # {invariant_factors, S(sorted), kind}
    d["tag"] = _tag_for(kind)
    return d


def _gamma_descriptors(factors, seed, log_path):
    """Build every family's descriptor for one Γ; skip (log) a family the Γ does not serve.

    Structured generators support cyclic Γ only and raise (ValueError/NotImplementedError)
    on a Γ they cannot build — that is a recorded skip, never a crash. `verify_sumfree_maximal`
    runs INSIDE every generator, so a returned S is always symmetric + sum-free + maximal.
    """
    group = Abelian(factors)
    descriptors = []
    for kind, generator in _STRUCTURED_GENERATORS.items():
        try:
            S = generator(group)
        except (ValueError, NotImplementedError) as exc:
            _log(log_path, event="grid_skip_family", gamma=list(factors), kind=kind,
                 reason=f"generator declined this Γ: {exc}")
            continue
        descriptors.append(_descriptor(group, S, kind))
    try:
        S = random_maximal_symmetric_sumfree(group, gen_rng(seed))
        descriptors.append(_descriptor(group, S, KIND_RANDOM_GREEDY))
    except (ValueError, NotImplementedError) as exc:   # pragma: no cover - random always builds
        _log(log_path, event="grid_skip_family", gamma=list(factors), kind=KIND_RANDOM_GREEDY,
             reason=f"random-greedy declined this Γ: {exc}")
    return descriptors


def _odd_cyclic_factors(order_max):
    """The odd cyclic orders 31..order_max as invariant-factor tuples (n,)."""
    return [(n,) for n in range(ORDER_MIN, order_max + 1) if n % 2 == 1]


def grid_descriptors(order_max=500, seed=0, non_cyclic=DEFAULT_NONCYCLIC, *, log_path=None):
    """Enumerate + canonically dedup the merged structured/random grid over odd |Γ|.

    All odd cyclic orders 31..order_max plus the curated `non_cyclic` set, EXCLUDING the
    unresolved Green–Ruzsa non-cyclic "all primes ≡ 1 mod 3" type-II case (logged skip,
    RESEARCH Open Q1). For each remaining Γ the structured (Green–Ruzsa, middle-interval
    where applicable) + random-greedy descriptors are merged and passed through
    `dedup.dedup` (nauty canonical certificate; WL-hash forbidden). The FIRST descriptor
    per canonical class is KEPT as provenance; collapsed duplicates — and any
    structured-vs-random COLLISION (a structured S and a random S yielding isomorphic H) —
    are LOGGED, never silently dropped. Returns the list of representative descriptors with
    their provenance `kind` intact.
    """
    raw = []
    for factors in _odd_cyclic_factors(order_max) + [tuple(f) for f in non_cyclic]:
        n = _group_order(factors)
        if n < ORDER_MIN or n > order_max or n > N_MAX:
            continue
        if _excluded_gr_noncyclic(factors):
            _log(log_path, event="grid_skip_gamma", gamma=list(factors), order=n,
                 reason="unresolved GR non-cyclic type-II")
            continue
        raw.extend(_gamma_descriptors(factors, seed, log_path))

    classes = dedup(raw)
    representatives = []
    for cls in classes:
        rep = cls["representative"]
        dups = cls["duplicates"]
        representatives.append(rep)
        for dup in dups:
            collision = _tag_for(dup["kind"]) != _tag_for(rep["kind"])
            _log(log_path,
                 event="dedup_collision" if collision else "dedup_duplicate",
                 rep_kind=rep["kind"], rep_gamma=rep["invariant_factors"],
                 dup_kind=dup["kind"], dup_gamma=dup["invariant_factors"],
                 structured_vs_random=collision,
                 reason=("structured/random streams yielded isomorphic H (a recorded "
                         "datapoint, never a silent drop)" if collision
                         else "isomorphic duplicate collapsed to the first descriptor"))
    return representatives


__all__ = [
    "grid_descriptors",
    "group_observables",
    "DEFAULT_NONCYCLIC",
    "STRUCTURED_KINDS",
    "ALL_KINDS",
    "ORDER_MIN",
]
