---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: "08-06 code authored (box run pending) — pool/sumfree/sweep.py: grid_descriptors (odd |Γ|=31–500 cyclic + curated non-cyclic; non-cyclic all-primes-≡1-mod3 type-II EXCLUDED with a logged reason) + canonical merged-stream dedup (pynauty; collisions logged) + group_observables (rank/exponent/prime-residue/cyclic?/exact |Aut|) + run_sweep (adjudicate_grid_point under a deterministic budget on BOTH backends; breadth-only instance parallelism; exact-window routing g>0-only-≤-window; observable bank folded in) + aggregate_sweep (structured-vs-random g / resistant-rate series) + box CLI. Dev-scale sweep/grid/dedup/aggregate tests GREEN; 332 non-slow pass (323 pre-existing unchanged); frozen trust root byte-untouched. The CANONICAL --order-max 500 box sweep + Task-3 human-verify checkpoint + POOL-2 completion are the orchestrator's box job (NOT run this Mac session)."
last_updated: "2026-07-23T12:00:00.000Z"
last_activity: 2026-07-23
progress:
  total_phases: 12
  completed_phases: 7
  total_plans: 37
  completed_plans: 36
  percent: 60
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-21)

**Core value:** Reconstruct the *attempt* under discipline — build the adversary so that anything surviving it is a correct road to a disproof, and anything dying leaves a machine-verified result; never invent the missing hour. Epistemic integrity (verified existence, radioactive impossibility) wins over speed, coverage, or narrative.
**Current focus:** Phase 08 — p1-p2-seeded-families-at-scale

## Current Position

Phase: 08 (p1-p2-seeded-families-at-scale) — EXECUTING
Plan: 08-06 CODE AUTHORED, box run pending (08-01..08-05, 08-07 done)
Status: 08-06 sweep.py authored + dev-scale tests GREEN; canonical --order-max 500 box sweep + Task-3 checkpoint + POOL-2 completion pending (orchestrator/box)
Last activity: 2026-07-23

Progress: [██████████] 97%

## Performance Metrics

**Velocity:**

- Total plans completed: 32
- Average duration: ~8 min
- Total execution time: ~0.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 2 | ~18 min | ~9 min |
| 1 | 2 | - | - |
| 2 | 2 | - | - |
| 03 | 4 | - | - |
| 04 | 4 | - | - |
| 5 | 7 | - | - |
| 6 | 5 | - | - |
| 07 | 6 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 02 P01 | 12min | 3 tasks | 8 files |
| Phase 02 P02 | 14min | 3 tasks | 5 files |
| Phase 05 P01 | 12min | 3 tasks | 2 files |
| Phase 05 P02 | 18min | 2 tasks | 2 files |
| Phase 05 P03 | 10min | 2 tasks | 3 files |
| Phase 05 P04 | 10min | 2 tasks | 3 files |
| Phase 05 P05 | 14min | 2 tasks | 3 files |
| Phase 05 P06 | 10 | 2 tasks | 2 files |
| Phase 05 P07 | 12min | 2 tasks | 1 files |
| Phase 06 P01 | 16min | 3 tasks | 8 files |
| Phase 06 P02 | 20min | 3 tasks | 9 files |
| Phase 06 P03 | 30min | 2 tasks | 3 files |
| Phase 06 P04 | 16min | 3 tasks | 7 files |
| Phase 07 P07-01 | 22min | 3 tasks | 15 files |
| Phase 07 P07-02 | 11min | 2 tasks | 3 files |
| Phase 07 P07-03 | 14min | 3 tasks | 3 files |
| Phase 07 P07-04 | 31min | 3 tasks | 1 files |
| Phase 07 P07-06 | 32min | 2 tasks | 4 files |
| Phase 08 P01 | 25min | 3 tasks | 12 files |
| Phase 08 P02 | 20min | 3 tasks | 7 files |
| Phase 08 P03 | ~18min | 3 tasks | 3 files |
| Phase 08 P05 | ~25min | 2 tasks | 2 files |
| Phase 08 P07 | ~45min | 2 tasks | 1 files |
| Phase 08 P04 | ~35min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- 08-03: the g(G) verifier re-derives χ = n − ν(H) via its OWN self-contained stdlib Edmonds blossom (the g-screen record carries no Tutte–Berge witness field), keeping the trust root independent of the networkx blossom the toolkit uses; n is re-derived from `invariant_factors` (true |Γ|), never the placeholder `provenance.n`.
- 08-03: the certificate-honesty gate is enforced INDEPENDENTLY in BOTH legs (schema `_assert_honest` + verifier `_assert_honest`, each carrying its own private radioactive literals) — a g(G) record can never be assembled OR verified with a "counterexample"/"had(G) <" claim (Pitfall 1, T-8-01).
- 08-03: POOL-2 NOT marked complete — still shared across waves 08-04..08-07 (adjudicate/frontier/sweep); this plan lands the certificate persistence backbone only, same discipline as 08-01/08-02.

Roadmap-creation decisions affecting current work:

- Roadmap: 296-reproduction and test-suite/CI merged into one "first blood" phase (Phase 3); Phases 1→2→3 are strictly sequential and gate everything downstream.
- Roadmap: had₃ (EXACT-05) built in Phase 5 with CP-SAT + the differential gate — before the battery goes live — so any future had₂ < χ event can be escalated same-day; the battery (Phase 6) wires it into runbook step 5.
- Roadmap: pools bundled only where genuinely related — P1+P2 (legacy seeded families at scale), P3+P6 (shared inflation operator), P4+P5 (2025-literature named open cells); P0 and P7 standalone; P7 deliberately last (needs battery-as-library + E3).
- Roadmap: LEAN-01/02 and deferred pool depth (POOL-0+/POOL-5+) are milestone 2 — excluded from this roadmap.

Execution decisions (Phase 01 Plan 01):

- Interpreter pin: `requires-python = ">=3.12,<3.13"` in pyproject + exact `3.12.13` in `.python-version` (research A3 granularity).
- pynauty stays an optional `[nauty]` extra so a compiler-less `uv sync` passes; dev tools via `uv sync --extra dev`. hatchling is the src-layout build backend.
- Verbatim port confirmed byte-exact: n=31 seed=1 `H_edges` sha256 == research golden `3c953d90…41e2`; fingerprint invariants (131/15/16) GREEN.

Execution decisions (Phase 01 Plan 02):

- Gated golden freeze: doc-derived Appendix-D invariants (131/15/16/tf/maxTF; seed-137 m=177) asserted FIRST; the self-generated sha256 is trusted and frozen into `data/manifests/fingerprint.json` only after the gate — a porting bug cannot self-certify.
- Tests load `h_edges_sha256` FROM the manifest (never a duplicated literal), so the manifest is the authority the byte-exact tripwire guards. seed-137 hash = `c3e7540f…cb13` (H-only; no model/ILP until Phase 4).
- Exact-match heuristic tier uses the single-RNG contract v1 (one `random.Random(1)` feeds `triangle_free_process` THEN `solve`) — the only path reproducing Appendix D.2 byte-exactly; the plan's literal fresh-`Random(1)` snippet was superseded.
- CHI-01 guard is AST/mechanism-based (Call/Import inspection), not a prose grep — verified non-vacuous by an injected `greedy_color` that trips it; `invariants/matching.py` confirmed the sole chi path via `max_weight_matching(maxcardinality=True)`.
- [Phase ?]: Phase 2 Plan 1: trust root corpus/verifier.py is stdlib-only, zero asserts, own _is_conflict, rebuilds adjacency from stored H_edges; verify/model.py stays byte-verbatim
- [Phase ?]: matching_edges() added to invariants/matching.py so witness.py obtains M without calling max_weight_matching outside matching.py (CHI-01 guard); extract_witness lives only in invariants/witness.py
- [Phase ?]: Wrong-chi proven at two boundaries: chi_G=17 trips verify_model_record k<chi; chi_G=15 trips verify_chi_witness n-nu!=chi (not catchable by family-size check)

Execution decisions (Phase 02 Plan 02):

- Schema v1: had_2 is DERIVED as len(model_branch_sets); build_record RAISES on len < chi — truncation (fam[:chi]) is structurally impossible; schema SUPPORTS k≥chi so Phase 4 drops in seed-137's true 17-set family with no schema change.
- Append-only immutability = per-prior-record re-verification against each record's own frozen H_edges_sha256 (the research's literal new[:len(old)]==old byte-compare is a no-op when new==old+[rec]); tampering with any stored record refuses the next append.
- Atomic write = tempfile(dir=path.parent)→flush→os.fsync→os.replace, temp unlinked on failure; append_certificate gates on BOTH verify_model_record AND verify_chi_witness AND verified=True (no has_witness opt-out).
- backends version stamps use importlib.metadata.version() (stdlib) so schema.py imports no networkx/pulp/ortools — same stdlib-only trust boundary as the verifier; reproduction.kind=byte_exact iff method mentions 'heuristic', canonical_platform always linux-x86_64.
- D.3 seed-137 stored as the 16-set K16 INTERIM (had_2=16); backends.cbc = bundled-with-pulp provenance — exact CBC binary version stamped at ILP-solve time in Phase 4.
- [Phase ?]: Phase 05 Plan 01: CP-SAT recorded-mode determinism is num_workers=1 + a pinned module-constant random_seed (137), resolving RESEARCH Open-Q4; interleave_search deliberately NOT used.
- [Phase ?]: Phase 05 Plan 01: cpsat.py is the ONLY ortools importer; reuses the frozen build_had2_problem (no re-enumeration), mirrors cbc.py swapping pulp->cp_model.
- [Phase ?]: Phase 05 Plan 01: CP-SAT non-optimal optimize bound = round(best_objective_bound) if finite else n, always bound_source='trivial_n' (no cbc_log analog invented).
- [Phase ?]: Phase 05 Plan 02: had3.py checksum is a closed-form degree/codegree recompute independent of the enumeration (n_triples=C(n,3)-sum C(deg,2); n_conflicts=sum C(deg,3)+sum C(codeg,3)); reuses had2.ChecksumError; conflict scope = seagull/Tier-1 (triple-single+triple-pair from W(T)), Tier-2 triple-triple deferred
- [Phase ?]: Phase 05 Plan 02: size-3-forced test uses a genuine had_2<had_3 (4<5) instance, NOT had_2<chi — no triangle-free H with had_2<chi is known (would be a Hadwiger counterexample); had_2<had_3 is the honest escalation signal
- [Phase 05]: Plan 05-03: trust root widened to size gate {1,2,3} with an explicit >=2-G-edges size-3 connectivity check; size-<=2 legs + _is_conflict byte-unchanged, raises-only under -O
- [Phase 05]: Plan 05-03: no schema.py / had_3 invariant change (RESEARCH Open-Q1/A6) — size-3 escalation proven at trust-root level only; had_3 corpus-field naming deferred to first real escalation-certificate consumer (Phase 6/11)
- [Phase 05]: Plan 05-04: differential.py is stdlib-only (imports only Status), raises-only (0 asserts); differential_verdict licenses SHC_CANDIDATE ONLY on two equal PROVED_OPTIMAL below chi, unequal proven optima raise CriticalDisagreement (quarantine+halt), single proof -> INSUFFICIENT (EXACT-04)
- [Phase 05]: Plan 05-04: metamorphic guard assert_not_below_verified(outcome, verified_k) raises CriticalDisagreement when a PROVED_OPTIMAL value < a trust-root-verified family size (verifier trumps solver); verified_k must come from verify_certificate, never a solver flag; new solver paths (CP-SAT + differential) fail closed under -O via test_solver_paths_dash_O.py
- [Phase ?]: Plan 05-05: had_3 escalation proven on the honest had_2<had_3 size-3-forced instance (n=7, had_2=4=chi < had_3=5); no triangle-free had_2<chi is known (296/296 killed at had_2; ~55k-trial small-graph search finds none), so the escalation signal is had_2<had_3, not had_2<chi (matches Plan 02)
- [Phase ?]: Plan 05-05: solve_had3 on BOTH backends behind its own method, translating the SAME frozen Had3Problem (seagull Tier-1); solve_had2 + _guarded_extract byte-unchanged; new _guarded_extract3 extends guards over triple vars; ortools confined to cpsat.py, pulp to cbc.py
- [Phase ?]: Plan 05-06: assume-and-verify SB discipline lands as stdlib-only solvers/symmetry.py (imports ONLY Status; 0 asserts); any impossibility-flavored (< chi) SB-on outcome reruns WITHOUT SB or raises SBContaminationError; C5 vertex-0-unused invalid hand constraint fabricates had_2=2<3=chi and is a passing regression (discipline restores 3); sound path = CP-SAT symmetry_level, pynauty DEFERRED (Open-Q2), no EXACT-06 criterion descoped
- [Phase ?]: [Phase 06] Plan 06-01: G1 criticality encoded as nu==n//2 (even-n fix, LOCKED); n=32/nu=16 passes as n=31/nu=15; forbidden n=2·chi−1 form grep-asserted absent.
- [Phase ?]: [Phase 06] Plan 06-01: D-01 Role B — hard-gate {g1,g2,connectivity} may KILL; g3_deep/g4/g5/g6 flag_only (record reason+witness, never terminate); seed-137 PASSES with g3/g4 as flags.
- [Phase ?]: [Phase 06] Plan 06-01: omega/kappa/connectivity networkx-confined to invariants/cliques.py (CHI-01 guard extended cliques.py-scoped); omega via max_weight_clique(weight=None).
- [Phase ?]: [Phase 06] Plan 06-01: runner.default_chain() resolves checks lazily so DEFAULT_CHAIN (PEP 562 __getattr__) never forms a checks<->runner import cycle.
- [Phase ?]: [Phase 06] Plan 06-03: profile-general solve() iterates (p',s') with p'+s'=chi & 2p'+s'<=n, round-robin restarts, NO assert (bounded enumeration); new initial_state_profile holds non-spanning states (unused verts) — finds seed-137 K16 the spanning profile missed
- [Phase ?]: [Phase 06] Plan 06-03: spanning profile (2p+s==n) stays byte-exact via untouched initial_state so D.2 (seed=1) reproduces verbatim; PER_RESTART_ITERS=1000 cap cycles restarts (deterministic, above the 3-iter D.2 solve); determinism idiom preserved byte-for-byte
- [Phase ?]: [Phase 06] Plan 06-03: heuristic miss stays sets=None (never RESISTANT); SC1 e2e preserved — starved 0.0s budget still misses -> exact had_2=17; explicit fast SC1-routing guard added
- [Phase ?]: [Phase 07] Plan 07-01: n≤11 MTF definition oracle embedded as 134 graph6 literals in conftest (self-contained, no geng-at-fixture-build) so the A1 CDM definition-regression gate can never silently skip
- [Phase ?]: [Phase 07] Plan 07-01: Lemma 2.5 equivalence leg GREEN now (embedded oracle + tfp.is_edge_maximal_tf + nx.diameter, no CDM module) as a live transfer-lemma regression; monotonicity + other bodies RED via function-local imports
- [Phase ?]: [Phase 07] Plan 07-01: CDM record shape = H_edges (MTF H) + matching_M of G-edges (complement) + invariants{n,complement_connected,cdm}; verifier rebuilds H-adjacency; paths.CDM_CORPUS additive, frozen 296-corpus byte-untouched
- [Phase 07]: Plan 07-04: Q3 ratified v1 — OEIS A216783 counts + is_edge_maximal_tf second-FILTER + shortg canonical dedup ARE the independent cross-check; independent MTF generator deferred to milestone-2/n~16
- [Phase 07]: Plan 07-04: stream_mtf = geng -ctq n [res/mod] | pickg -Z2 via Popen arg lists (no shell); int-validated + DoS-bounded n<=17 before interpolation; yields 147/392/1274 at n=12/13/14 (OEIS A216783)
- [Phase ?]: [Phase 07] Plan 07-06: adjudicate.py wires the CDM subsystem — decode(V5 n-assert)->has_cdm≡cdm_cpsat gate(CDMCriticalDisagreement, release-blocking)->CDM-HOLDS verify+append; CDM-FAILS is_connected carve-out (K_a⊔K_b out-of-scope) vs connected-complement battery escalation hook
- [Phase ?]: [Phase 07] Plan 07-06: full n=12-14 batch — 1813 total, DFS≡CP-SAT everywhere (0 disagreements), 1794 CDM-HOLDS certificated (141/386/1267), 19 K_a⊔K_b carve-outs, 0 connected-complement fails; verified CDM frontier extends past n≤11
- [Phase ?]: [Phase 07] Plan 07-06: CDM corpus is gitignored runtime output; CHI-01 guard extended with pool/cdm/adjudicate.py-scoped networkx allow-list {from_graph6_bytes,complement,is_connected}
- [Phase 08]: POOL-1/POOL-2 RED contract landed (12 test modules + conftest); certificate-honesty gate executable — requirements deferred to implementation waves 08-03..08-07, not marked complete on the RED scaffold (reporting discipline)
- [Phase 08 P02]: POOL-2 generation foundation GREEN — Abelian(factors) Γ arithmetic (V5-validated, n≤500 cap), sha256 stage-independent RNG v2 subseeds, structured (Andrásfai middle-interval, Green–Ruzsa) + random-greedy sum-free generators with a raise-based verify_sumfree_maximal net inside every generator, pynauty-canonical dedup (WL/graph-hash forbidden). Frozen generators/cayley.py byte-untouched.
- [Phase 08 P02]: green_ruzsa_sumfree keys off the ARITHMETIC of |Γ| (smallest prime ≡2 mod3 pullback / all ≡1 mod3 middle interval), never an I/II/III numeral (Pitfall 6); the raise-based re-check makes an unpinned coset-membership formula non-fatal (RESEARCH Open Q1). 3∣n cyclic case deliberately NotImplemented (ambiguous — served by random-greedy).
- [Phase 08 P02]: deterministic solver budgets are ADDITIVE — SolveParams.det_time → CP-SAT max_deterministic_time, SolveParams.det_nodes → CBC PULP_CBC_CMD(maxNodes=…); both default None → unbounded → 296-corpus reproduction byte-unchanged (273 pre-existing tests still green); map_status untouched (node-limit stop already maps to INCUMBENT_ONLY). Wall-clock forbidden for any recorded verdict (Pitfall 2).
- [Phase 08 P02]: POOL-2 NOT marked complete — shared across waves 08-02..08-07; this plan lands the generation foundation only. Completed when the g-screen/store/verifier/adjudicate waves make the full contract green (same discipline as 08-01).
- [Phase 08 P05]: ILP optimality-proof frontier MEASURED, not assumed (RESEARCH A4). measure_ilp_frontier walks a group-order grid, hard-gates each structured/random sum-free Cayley instance, and times ONLY survivors on BOTH co-equal backends under a FIXED deterministic budget — CP-SAT det_time (num_workers=1), CBC det_nodes (maxNodes, threads=1) — with NO wall-clock time_limit_s on any timed call (T-8-07; the exact failure this closes). proved iff BOTH PROVED_OPTIMAL; had_2<chi escalates to Tier-1 had_3 the same bounded way. num_workers!=1 raises.
- [Phase 08 P05]: run_frontier_probe persists the compact frontier_report (per-n bools + conservative contiguous-from-bottom frontier_n + budgets + solver versions) atomically; exact_window_max is the boundary 08-06 reads to route a non-packing instance to exact g>0 (n≤window) or the RESISTANT E3 queue (n>window) — 0 when nothing proved (conservative → E3). Signature follows the RED contract (det_budget/num_workers) with det_time/det_nodes additive; authoritative data/results/sumfree_frontier.json regenerated on the box at 08-06, not this Mac session. POOL-2 still NOT complete.
- [Phase 08 P07]: POOL-1 COMPLETE — the P1/TFP-complement track is delivered solely by this plan (POOL-2 stays open, shared across 08-02..08-07). pool/sumfree/p1.py: run_p1_tfp/critical_sweep (n=31-32 EXACT-had_2 dual-backend sweep under differential_verdict + trust root; DECIDED vs RESISTANT; verdict a deterministic function of (n,seed,det_budget) via CP-SAT det_time + CBC det_nodes=det_budget·5000, never wall-clock; num_workers!=1 raises) and the RESISTANT set IS the derived E3 queue (SC1).
- [Phase 08 P07]: run_showpiece is EXISTENCE-ONLY above the ILP frontier (n≈1001-2001) — heuristic proposes, verify_certificate (SOLE trust root) disposes: HIT→VERIFIED cert appended to a NEW dedicated paths.P1_SHOWPIECE_CORPUS (gitignored runtime output); MISS→RESISTANT with had_2=None (heuristic resistance is never a result, never an impossibility claim; T-8-11/SRCH-02). RNG v2 gen/search subseeds + byte-exact descriptor rebuild; frozen 296-corpus + generators/{tfp,cayley}.py byte-untouched.
- [Phase 08 P07]: run_p1_tfp reimplements the exact-had_2 slice directly (NOT battery.run_candidate, which is RNG-v1 + wall-clock and ignores its params arg — incompatible with the RNG-v2 + deterministic-budget must-haves and the (n,seed) determinism test); reuses the SAME differential_verdict + verify_certificate + build_record + extract_witness machinery, in-memory, files_modified scope = p1.py only (Deviation Rule 3).
- [Phase 08 P04]: the per-instance g(G) runbook SPINE is complete. screen.py: compute_g / classify_screen_outcome (pure metric + radioactive labels — heuristic hit→KILLED g≤0, had_k<χ→SHC_CANDIDATE g>0, miss/unproved→RESISTANT g None) + screen_gap (had_2 dual-backend optimize → differential_verdict → Tier-1 had_3 seagull; a proved U<χ is a SOUND g>0 from the upper bound, U≥χ raises UnverifiedKill → Tier-2 extract + trust_root_verify_family). adjudicate.py: adjudicate_sumfree replicates the runbook legs on the descriptor-built adj (NOT run_candidate) — build→gate→χ=n−ν→heuristic(HIT→verify_certificate→KILLED store)/screen→honest certificate; HARD gate fail is first-class KILLED-BY-GATE (log only, no g, no cert); g>0 carries HONEST_G_POSITIVE_STATEMENT; RESISTANT→E3 queue log.
- [Phase 08 P04]: every recorded verdict is deterministically bounded on BOTH co-equal backends — CP-SAT det_time (max_deterministic_time, num_workers=1), CBC det_nodes (maxNodes) — screen_gap RAISES if either budget is absent; adjudicate_gscreen rejects wall-clock knobs (wallclock_budget/time_limit_s) and num_workers≠1 (T-8-07, CP-SAT #3590/#3842/#4839). verify_certificate is the SOLE family authority, called OUTSIDE any truth-expression; an unverifiable ≥χ upper-bound family routes conservatively to RESISTANT (never an unverified kill or a false g>0).
- [Phase 08 P04]: DEVIATION (Rule 3, conservative) — the backends expose only the Tier-1 seagull solve_had3 (an UPPER bound), so a rigorous Tier-2 exact had_3 is unavailable; a proved U≥χ whose extracted family does NOT certify a K_χ minor is routed to RESISTANT (E3 / Tier-2 exact obligation) rather than emitting an unproven g>0 — errs toward the radioactive-impossibility discipline. At dev ns all odd-|Γ| structured/random instances are hard-gate-KILLED at g1_criticality (documented in 08-05); the KILLED-BY-GATE + heuristic-verify+store legs were validated directly (trust_root_verify_family returns k=3 on the Z_5 C_5 K_3 minor, None on a bogus family). POOL-2 NOT marked complete — the slow grid sweep (08-06) remains; requirements-completed: [].
- [Phase 08 P06]: CODE AUTHORED, BOX RUN PENDING. pool/sumfree/sweep.py: grid_descriptors (odd cyclic 31–500 + curated non-cyclic; the non-cyclic "all primes ≡1 mod3" GR type-II case EXCLUDED with logged reason "unresolved GR non-cyclic type-II", T-8-17) merges structured (green_ruzsa/middle_interval) + random-greedy streams and dedups canonically (pynauty; WL-hash forbidden; first descriptor kept, collapsed dups + structured-vs-random collisions LOGGED not dropped); group_observables adds the zero-cost cross-sections (rank, exponent, #primes≡1/≡2 mod3, cyclic?, exact |Aut| via Hillar–Rhea). run_sweep drives adjudicate_grid_point per descriptor under a DETERMINISTIC budget on BOTH backends (RAISES without det_time+det_nodes), breadth-only instance parallelism with parent-serial event-stream writes (per-verdict determinism preserved, T-8-07), exact-window routing (g>0 candidate ONLY ≤ window; above → RESISTANT via effective_state), observable bank folded onto every row (had₃−had₂, abs_gap, S_density, det_work budget); aggregate_sweep emits per-(kind,order) gate-survival / verified-g≤0 / exact-g>0 / RESISTANT-rate + structured-vs-random series to paths.SUMFREE_SWEEP. Honesty protocol: PRIMARY (LOCKED g(G)+RESISTANT-rate) vs SECONDARY exploratory bank, multiple-comparison count recorded. Dev-scale sweep/grid/dedup/aggregate/resistant tests GREEN; 332 non-slow pass (323 pre-existing unchanged); frozen 296-corpus + generators/cayley.py byte-untouched. NOT run this session: the canonical --order-max 500 box sweep + Task-3 human-verify checkpoint — the orchestrator finalizes those + POOL-2 completion + the authoritative SUMMARY after the box run. requirements-completed: [].

### Pending Todos

- **⏳ AUTHOR READ PENDING (non-blocking): transfer-lemma A3.** Phase 7 execution was run with both
  author checkpoints delegated to Claude (07-04 Q3 → ratified v1: OEIS + second-filter + shortg;
  07-05 Q1 → carve-out self-reviewed). The transfer-lemma proof (`docs/proofs/transfer-lemma.md`)
  Assumption A3 (disconnected complement is the ONLY carve-out obstruction) is a first-new-science
  claim that still wants the author's final read before any external frontier claim is published.
  Correctness backstop: the empirical n≤11 definition gate (all 134 connected MTF-complements vs
  CLWY's published all-CDM result).

### Blockers/Concerns

- [Phase 6] GATE-02 needs author input: pin the exact original G1–G6 definitions (§2) and reconcile reconstructed labels; also confirm what B₇ denotes in the PST citation. Gather early (any time from Phase 1) — required before the gate is trusted.
- [Phase 3] Linux x86_64 is the canonical reference-regeneration platform for ILP-method certificates (macOS bundled CBC is x86_64-only, Rosetta on Apple Silicon) — CI must provide it.
- [Phase 10] P4 requires pinning CLWY Theorem 3.12's exact parameter window before declaring any cell open; P5 is gated on the ETT (arXiv 2508.19646) construction study — instance sizes may exceed exact-ILP range.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260722-r57 | ruff lint cleanup (Phase 1-6): 6 errors → 0, lint-only | 2026-07-22 | 30fbd73 | [260722-r57-ruff-lint-phase-1-6](./quick/260722-r57-ruff-lint-phase-1-6/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-23T12:00:00.000Z
Stopped at: 08-06 code authored (box run pending). pool/sumfree/sweep.py + tests/pool/sumfree/test_sweep.py authored: grid_descriptors (odd |Γ|=31–500 cyclic + curated non-cyclic; non-cyclic all-primes-≡1-mod3 type-II EXCLUDED with logged reason) + canonical merged-stream dedup (collisions logged) + group_observables (rank/exponent/prime-residue/cyclic?/exact |Aut|) + run_sweep (adjudicate_grid_point under deterministic budget on BOTH backends; breadth-only parallelism; exact-window routing; observable bank) + aggregate_sweep (structured-vs-random g / resistant-rate series) + box CLI. Dev-scale sweep/grid/dedup/aggregate tests GREEN; 332 non-slow pass (323 pre-existing unchanged); frozen trust root byte-untouched. The CANONICAL --order-max 500 box sweep, the Task-3 human-verify checkpoint, and POOL-2 completion + the authoritative SUMMARY are the orchestrator's box job — NOT run this Mac session (no claim the sweep ran).
Resume file: .planning/phases/08-p1-p2-seeded-families-at-scale/08-06-SUMMARY.md (status: code-authored, box-run-pending)
