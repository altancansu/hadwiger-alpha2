# 08-06 Sweep — Observable Bank (novelty-surface addendum)

**Agreed:** 2026-07-23 (author + Claude), during Phase 8 execution.
**Purpose:** Maximize the sweep's chance of surfacing a *novel* structural signal — without
p-hacking. All observables are cheap (derived from the already-stored group descriptor + quantities
already computed per instance) and are **recorded + verified**, never trusted from a heuristic.

## Honesty protocol (non-negotiable — extends the E3 discipline)
- **PRIMARY (pre-registered):** the LOCKED prediction only — `g(G) = (χ − had₃)/χ` and RESISTANT-rate,
  **structured vs random**, vs `|Γ|`. This is *the* hypothesis test. Timestamped pre-data.
- **SECONDARY (exploratory):** every other cross-section below. Mine freely — but a hit here is
  **hypothesis-generating, not a result**.
- **Confirmation rule:** any exploratory signal must be re-tested as a *new pre-registered prediction*
  on **fresh instances (seed change)** before it is reported as real. Multiple-comparison honesty:
  record how many cross-sections were examined alongside any claimed effect.
- Only exact `g>0` points **within the measured `exact_window_max`** (08-05) are candidates; beyond it
  → RESISTANT → E3 queue. This addendum changes *what we record*, never *what counts as a break*.

## Per-instance observables to record (in the sweep row)
Beyond the existing `{kind, |Γ|, gate_survived, g, verdict}`:
- `chi`, `nu_H` (matching number), `had2`, `had3` — raw, not just the normalized `g`.
- **`had3_minus_had2`** — does the size-3 branch set actually help? (had₃ ≈ had₂ ⇒ stronger candidate.)
- **`abs_gap = chi − had3`** — the raw (un-normalized) shortfall.
- `S_density = |S| / |Γ|` — sum-free set density vs the theoretical extremal for that family.
- `det_work_had3` — deterministic work consumed to settle had₃ (a *difficulty* signal; a difficulty
  knee may itself be novel, independent of `g`).

## Group-structure cross-sections (group-by axes for the exploratory bank)
All from the stored abelian descriptor — zero solver cost:
- **rank(Γ)** = # invariant factors (cyclic=1 vs Z_3^4=4 vs Z_9×Z_9=2 …).
- **exponent(Γ)** = largest element order.
- **# distinct prime divisors**; **# primes ≡ 1 (mod 3)**; **# primes ≡ 2 (mod 3)**
  (the residue class governing sum-free density formulas).
- **cyclic vs non-cyclic** (boolean).
- **|Aut(Γ)| / symmetry proxy** — directly probes the adversarial counter: does higher symmetry make
  minors *easier* to pack (automorphic branch-set copies), killing the break? If structured stays
  clean exactly where `|Aut|` is large, that is a novel, publishable structural explanation.

## The novel question this enables
Not just *"does it break?"* but *"which algebraic feature obstructs minor-packing?"* — order, rank,
exponent, prime-residue signature, or symmetry. A correlation with a *specific invariant* (rather than
sheer `|Γ|`) is a genuine structural finding that survives **even if no counterexample appears**.
