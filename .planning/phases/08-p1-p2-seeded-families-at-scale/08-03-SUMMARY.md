---
phase: 08-p1-p2-seeded-families-at-scale
plan: 03
subsystem: pool-sumfree
tags: [pool-2, g-screen, certificate-honesty, radioactive-impossibility, trust-root, blossom, append-only, hash-chain, fail-closed]

# Dependency graph
requires:
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 01
    provides: "RED contract (test_schema/test_store/test_screen) + valid_gscreen_record/honesty_canary_record fixtures + paths.SUMFREE_CORPUS this plan makes GREEN"
  - phase: 08-p1-p2-seeded-families-at-scale
    plan: 02
    provides: "the descriptor/{invariant_factors,S} generation foundation whose instances this certificate layer persists"
provides:
  - "alpha2.pool.sumfree.schema.build_gscreen_record — g(G) certificate; derives g=(chi-had_k)/chi; HONEST_G_POSITIVE_STATEMENT + honest_statement_for + _assert_honest radioactive guard"
  - "alpha2.pool.sumfree.verifier.verify_gscreen_record (alias verify_gscreen) — stdlib-only trust root: rebuilds H, re-derives chi=n-nu(H) via its own Edmonds blossom, re-checks g + K_chi minor model + honesty gate; fails closed under python -O"
  - "alpha2.pool.sumfree.store.append_gscreen_certificate — append-only verify-at-append writer to paths.SUMFREE_CORPUS, per-record hash chain, prefix immutability, atomic write; isolated from frozen 296-corpus + CDM corpus"
affects: [08-04 adjudicate (emits + appends via these legs), 08-05 measure_ilp_frontier, 08-06 slow grid sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Certificate honesty enforced INDEPENDENTLY in both schema and verifier — each carries its own private radioactive literals (counterexample / 'had(G) <'); a g(G) record can never be assembled OR verified with a claim beyond a proved had_3 < chi (Pitfall 1, T-8-01)"
    - "Trust root re-derives chi = n - nu(H) via a self-contained stdlib Edmonds blossom (record carries no Tutte-Berge witness) — independent of the networkx blossom the toolkit uses (VRF-01)"
    - "n re-derived from invariant_factors (true |Gamma|), never the placeholder provenance.n — the verifier trusts no stored scalar it can recompute"
    - "Raises-only, zero assert -> fails closed under python -O (T-8-09); verify-at-append + hash chain + byte-prefix immutability clone the CDM store mechanics on a separate path/leg (T-8-08)"

key-files:
  created:
    - src/alpha2/pool/sumfree/schema.py
    - src/alpha2/pool/sumfree/verifier.py
    - src/alpha2/pool/sumfree/store.py
  modified: []

key-decisions:
  - "g(G) verifier re-derives chi via its OWN stdlib blossom (no stored matching witness in the g-screen record shape); n from invariant_factors, not provenance.n"
  - "Honesty gate lives in BOTH legs with independent private literals — the trust root refuses a radioactive statement at verify time, never merely at emit time"
  - "POOL-2 NOT marked complete — shared across waves 08-04..08-07; this plan lands only the certificate persistence backbone (same discipline as 08-01/08-02)"

requirements-completed: []

# Metrics
duration: ~18min
completed: 2026-07-23
---

# Phase 8 Plan 03: g(G)-Screen Certificate-Honesty Backbone Summary

**The radioactive-impossibility discipline is now structural: a g(G) record physically cannot be persisted unless its claim re-verifies from stored data and its statement is honest. Three stdlib-only legs — a schema that derives `g = (chi - had_k)/chi` and states ONLY what a proved `had_3 < chi` establishes ("no K_chi minor with branch sets <=3", NEVER "counterexample" / "had(G) < chi"), a verifier that rebuilds H, re-derives `chi = n - nu(H)` via its own Edmonds blossom, re-checks the K_chi minor model, and enforces the honesty gate (fails closed under `python -O`), and an append-only verify-at-append hash-chained store on `paths.SUMFREE_CORPUS` isolated from the frozen 296-corpus and the CDM corpus.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-23
- **Tasks:** 3 (all `type=auto tdd=true`)
- **Files:** 3 created, 0 modified

## Accomplishments

- **Task 1 — g(G) certificate schema (`a9719b0`):** `build_gscreen_record(*, provenance, H_edges, chi, had_2, had_3, terminal_state, certificate_statement, method, model_branch_sets=None, verified=True)` returns a pure-JSON round-trippable dict; `g` is DERIVED (`_compute_g`, had_k = had_3 else had_2; None when RESISTANT), never trusted from the caller. Descriptor provenance validated by its own shape (`_validate_descriptor_provenance` — the frozen tagged-union rejects `kind="descriptor"`). `HONEST_G_POSITIVE_STATEMENT` + `honest_statement_for` + `_assert_honest` radioactive guard (raises on "counterexample"/"had(G) <"). Platform-agnostic reproduction for g<=0; solver/platform stamp for g>0 SHC_CANDIDATE.
- **Task 2 — stdlib-only g(G) verifier (`5055590`):** `verify_gscreen_record` (alias `verify_gscreen`) rebuilds H adjacency from stored `H_edges` (CR-01 range checks), forms G=complement, re-derives `nu(H)` via a self-contained Edmonds blossom `_max_matching`, and re-checks `chi = n - nu(H)` (n from `invariant_factors`). Re-checks `g == (chi - had_k)/chi`, terminal_state<->g consistency, and — for KILLED — that `model_branch_sets` is a valid K_chi minor model (size <=3 sets, each connected in G, pairwise cross-adjacent, disjoint, len >= chi). Honesty gate re-enforced in the trust root with its own private literals. Raises-only, zero `assert`.
- **Task 3 — append-only verify-at-append store (`c197ba2`):** `append_gscreen_certificate(rec, path=None)` defaults to `paths.SUMFREE_CORPUS`; verify-at-append gate (`verify_gscreen` + `verified is True`); per-record hash chain recomputed from record 0 (`chain_hash`/`CHAIN_FIELD`); append-only prefix immutability (re-verify every prior + byte-prefix compare); atomic tempfile->flush->`os.fsync`->`os.replace` (temp unlinked on failure). Imports/touches nothing of the frozen 296-corpus or CDM store.

## Test Results

- **This plan's targets GREEN:** `test_schema` (4) + `test_store` (6) + the certificate-honesty/verifier half of `test_screen` (6, incl. `test_stdlib_verifier_rederives_and_accepts_valid_killed` — the blossom chi re-derivation) → **16 passed**.
- **No regression:** full non-slow suite → **319 passed** (= 273 pre-existing + 30 from 08-02 + 16 this plan).
- **`python -O` fail-closed canary:** a tampered-sha256 KILLED record is still rejected under `python -O` (`H_edges_sha256 mismatch`).
- **Frozen trust root untouched:** `git status` of `src/alpha2/generators/cayley.py`, `data/corpus/`, `src/alpha2/corpus/` is empty.
- **Out of scope (still RED by design):** `test_screen` screen-metric half (`compute_g`, `classify_screen_outcome` — `screen.py`, wave 08-04) and `test_frontier` (2, `measure_ilp_frontier`, wave 08-05).

## Task Commits

1. **Task 1: g(G)-screen certificate schema with honesty guard** — `a9719b0` (feat)
2. **Task 2: stdlib-only g(G) verifier re-deriving chi and the screen claim** — `5055590` (feat)
3. **Task 3: append-only verify-at-append g(G)-screen store** — `c197ba2` (feat)

## Decisions Made

- **Verifier re-derives chi via its OWN stdlib blossom.** The g-screen record shape carries no Tutte–Berge witness (unlike the frozen corpus record), so the "verify the stored witness both directions" route is unavailable; the trust root therefore carries a self-contained Edmonds blossom `_max_matching` and re-computes `nu(H)` from scratch. This keeps the trust root independent of the networkx blossom the toolkit uses (VRF-01) — a wrong `chi` (the radioactive lever a forged KILLED record would pull) is caught. n is re-derived from `invariant_factors` (true |Γ|) because `provenance.n` is a documented placeholder in the store's records.
- **Honesty gate enforced independently in BOTH legs.** Schema `_assert_honest` (emit-time) and verifier `_assert_honest` (verify-time) each carry their own private radioactive literals ("counterexample", "had(G) <") — the trust root refuses a mislabeled record at verify time, never merely at emit time (T-8-01). The verifier does NOT require the exact honest literal for g>0 (only forbidden-substring absence), to stay robust to benign wording while still failing closed on any radioactive claim.
- **POOL-2 NOT marked complete.** POOL-2 is shared across waves 08-04..08-07 (adjudicate/frontier/sweep); this plan delivers only the certificate persistence backbone. Marking it complete on the backbone would violate the reporting discipline (nothing counts as found until the full contract verifies). `requirements-completed: []`.

## Deviations from Plan

- **[Rule 3 — Blocking issue] Verifier public name is `verify_gscreen_record`, not `verify_gscreen`.** The plan's interface sketch named the function `verify_gscreen`, but the RED contract (`tests/pool/sumfree/test_screen.py`) imports `verify_gscreen_record`. Implemented `verify_gscreen_record` as canonical and aliased `verify_gscreen = verify_gscreen_record` (the store links via the `verify_gscreen` name, satisfying the plan key-link pattern). No behavioral change.
- **[Scope boundary] `screen.py` NOT created.** The plan's files_modified lists exactly schema/verifier/store, and the objective scopes this plan to "the certificate-honesty half of test_screen". `screen.compute_g` / `classify_screen_outcome` (the screen-metric half) remain RED for wave 08-04, matching the 08-02 summary's wave split. Not a deviation in behavior — an explicit scope respect.

Otherwise the plan executed as written: the signature the RED test pins takes `chi/had_2/had_3` scalars (not an `invariants` dict) and computes `g` itself, which is exactly what was built.

## Known Stubs

None — every leg is fully wired: the schema derives real data, the verifier re-derives χ and the K_χ model from stored bytes, the store gates every append. No placeholder/empty-value flows anywhere.

## Deferred / Out of Scope

- `screen.py` (`compute_g`, `classify_screen_outcome`) → wave 08-04 (adjudicate runbook).
- `measure_ilp_frontier` (`test_frontier`) → wave 08-05.
- No heavy sweeps run here (Mac authoring session per docs/COMPUTE.md); the slow grid is 08-06 on the remote box.

## TDD Gate Compliance

This plan is `type: tdd`. The RED gate (`test(...)` commits for test_schema/test_store/test_screen) landed in 08-01; this plan is the GREEN gate — three `feat(...)` commits turning the schema/verifier/store contract green. RED-before-GREEN is satisfied across the wave split; all target tests were confirmed RED at this plan's start (16 failed, 2 fixture-only passed) and GREEN after each task.

## Self-Check: PASSED

All 3 created modules exist on disk (schema 238, verifier 341, store 129 lines — each above its min_lines floor); all 3 task commits (`a9719b0`, `5055590`, `c197ba2`) present in git history; the frozen trust root (`generators/cayley.py`, `data/corpus/`, `src/alpha2/corpus/`) diff is empty.

---
*Phase: 08-p1-p2-seeded-families-at-scale*
*Completed: 2026-07-23*
