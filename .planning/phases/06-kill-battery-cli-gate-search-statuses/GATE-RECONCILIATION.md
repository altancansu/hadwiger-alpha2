# Gate Reconciliation Record (GATE-02)

**Phase:** 6 — Kill Battery CLI (Gate, Search, Statuses)
**Plan:** 06-05 (the deferred gate-trust author sign-off)
**Written:** 2026-07-22
**Status:** ⏳ DRAFT — awaiting author sign-off on 2 items (item 3, Role A/B, is RESOLVED)

> Per 06-CONTEXT.md D-01 and the ROADMAP research flag, the G1–G6 gate must not be
> declared **"trusted" for production** until the author reconciles the labels and
> confirms the open literature item. This record does that reconciliation and then
> PAUSES for the author. It does **not** block the shipped SC1 slice (Plans 01–04),
> which already runs under D-01 Role B and is fully test-verified (239 fast tests green).

---

## 1. The core finding — two different G1–G6 decompositions share the same labels

The author's original **§2** (`reference/alpha2-program-source.md:635–644`) and the
research team's **FEATURES.md reconstruction** (`research/FEATURES.md:48–55`) BOTH use
the symbols G1–G6, but for **different checks in a different order**. This is the label
collision the "reconcile with author" flag anticipated.

| Label | Author's §2 (AUTHORITATIVE) | FEATURES.md "reconstruction" |
|-------|-----------------------------|------------------------------|
| G1 | n ≥ 31, **criticality** (n odd, n = 2χ−1) | H triangle-free & ≥1 edge (α=2 regime) |
| G2 | H triangle-free, **diameter 2** | G & H **connected** |
| G3 | χ≥7, **κ≥χ, δ≥χ+1**, Hamiltonian, vertex-critical, H−v perfect matching | H edge-maximal (⇔ diam 2) |
| G4 | **8 ≤ ω ≤ χ−3, ω/n ≲ ¼** | dominating-edge check |
| G5 | induced C₅; W₅, K₈, all 33 Carter graphs | **known-safe family screens** (incl. "B₇-free per PST") |
| G6 | outside every **proven-safe family** | cheap-invariant wins (χ≤6 RST; ω≥χ) |

**Implementation decision (recorded, needs author confirmation):** Phase 6 followed the
**author's §2 numbering** (frozen source of truth), NOT the FEATURES reconstruction —
i.e. G1 = criticality, G4 = ω-window, G6 = proven-safe families. This is why
`gate/checks.py` implements `g1_criticality`, `g4_omega_window`, etc. The FEATURES
decomposition is treated as subordinate/superseded.

> **AUTHOR CONFIRM (item 2a):** Is the §2 numbering the canonical one, with the FEATURES
> reconstruction superseded? Or should any FEATURES check (e.g. its G4 dominating-edge
> test, or G6 χ≤6 RST fast-kill) be folded in under a §2 label?

---

## 2. Implementation → §2 tier map (D-01 Role B)

Under LOCKED decision D-01 (Role B, author-confirmed 2026-07-22), only the minimal
hard-gate may KILL a studied-pool instance; the deep §2 checks run **flag-only**.

| §2 check | Implemented as | Tier | seed-137 |
|----------|----------------|------|----------|
| G1 criticality | `g1_criticality` — `ν == n//2` | **HARD** (kill) | PASS (ν=15, n=31) |
| G2 triangle-free diam-2 | `g2_triangle_free_diam2` | **HARD** (kill) | PASS |
| G3 connectivity (subset) | `g_connectivity` | **HARD** (kill) | PASS (connected) |
| G3 deep (κ≥χ, δ≥χ+1) | `g3_deep` | flag-only | FLAG (κ=11<16, δ=16<17) |
| G4 ω-window | `g4_omega_window` | flag-only | FLAG (ω=14, ω/n=0.45) |
| G5 induced-C₅ / unavoidables | screen | flag-only | (flag) |
| G6 proven-safe families | `gate/safe_families.py` | flag-only | (flag) |

**Consequence:** seed-137 PASSES the hard-gate and reaches the had₂=17 verified kill
(SC1) — the corpus reality that forces Role B (a strict §2 gate would kill seed-137 at
G3-deep before had₂, contradicting the 296-certificate corpus).

---

## 3. G1 even-n generalization (recorded, ROADMAP-sanctioned)

- **§2 G1 (literal):** n odd, `n = 2χ(G) − 1`.
- **Implementation:** `ν == n // 2` — accepts **even** n (the n=32 corpus row passes),
  as required by ROADMAP Phase-6 Success Criterion 2 ("the criticality predicate accepts
  even n"). The forbidden literal `n == 2*chi − 1` form is grep-asserted absent.

> **AUTHOR CONFIRM (item 2b, part of the label map):** the even-n generalization of G1
> criticality (`ν == n//2`) is the intended production form, superseding the odd-only §2
> literal for the studied pools. (Believed correct — sanctioned by ROADMAP SC2 — flagged
> only for completeness.)

---

## 4. The three open items

| # | Item | Status |
|---|------|--------|
| 1 | **Role A vs Role B** for TFP/Cayley studied pools | ✅ **RESOLVED — Role B** (author, 2026-07-22). Recorded in 06-CONTEXT.md D-01. |
| 2 | **§2 ↔ FEATURES.md label map** (§1 above) + even-n G1 (§3) | ⏳ Awaiting author confirmation. Draft complete; believed correct. |
| 3 | **B₇ meaning** in the PST citation | ⏳ Awaiting author confirmation. **Sourced proposal below.** |

### B₇ — sourced proposal (do not treat as confirmed)

- **Where it appears:** ONLY in the FEATURES.md G5 known-safe screen ("B₇-free per PST",
  `FEATURES.md:54,297`) and the theorem citation "B₇-free ⟹ had ≥ n/2". It is **absent
  from the author's §2** — so it is a FEATURES-reconstruction addition, not part of the
  frozen gate. It is **not on the SC1 path** (seed-137 never touches the B₇ screen).
- **Proposed meaning (web-sourced, needs author confirmation):** In Plummer–Stiebitz–Toft
  (2003), *On a special case of Hadwiger's conjecture*, Discuss. Math. Graph Theory
  23(2):333–363, they prove h(G) ≥ χ(G) for H-free graphs with α(G) ≤ 2 where H is any
  4-vertex graph with α(H) ≤ 2, **or C₅, or a particular graph on seven vertices**. That
  7-vertex graph is **B₇** — characterized as containing every 4-vertex α≤2 graph as an
  induced subgraph. So "B₇-free (with α≤2) ⟹ Hadwiger holds" is the PST result the G5
  screen invokes.

> **AUTHOR CONFIRM (item 3):** Is B₇ the specific 7-vertex graph from PST 2003 as above?
> If so, provide (or point to) its edge set / adjacency so the G5 screen can test
> "B₇-free" exactly. Until confirmed, the G5 B₇-free screen stays **inactive** (reports
> "screen not yet active"); nothing downstream depends on it under Role B.

---

## 5. Sign-off

The gate is **NOT declared "trusted" for production** until the author signs items 2 and 3.
Until then:
- The SC1 slice and all Phase-6 machinery are shipped and test-verified (Role B, hard-gate).
- The deep §2 checks run flag-only (never kill studied pools).
- The G5 B₇-free screen is inactive.

**Author sign-off:**
- [ ] Item 2 — §2 numbering canonical (FEATURES superseded) + even-n G1 confirmed
- [ ] Item 3 — B₇ = PST 7-vertex graph confirmed + adjacency provided
- [ ] Gate declared TRUSTED for production — signed: __________ date: __________

*Sources for the B₇ proposal:*
- [Plummer–Stiebitz–Toft, *On a special case of Hadwiger's conjecture* (EUDML)](https://eudml.org/doc/270755)
- [Semantic Scholar record](https://www.semanticscholar.org/paper/On-a-special-case-of-Hadwiger's-conjecture-Plummer-Stiebitz/312103e6fca99c76bcae9031fd86f41fd0b87763)
- [Costa–Luu–Wood–Yip 2025 (CLWY), arXiv:2512.17114](https://www.arxiv.org/pdf/2512.17114)
