---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 05-05-PLAN.md — solve_had3 on CBC+CP-SAT, size-3-forced dual-backend escalation (had_2=4<had_3=5) verified through widened trust root; CBC==CP-SAT on had_3 (EXACT-05/EXACT-03)
last_updated: "2026-07-22T09:49:08.206Z"
last_activity: 2026-07-22
progress:
  total_phases: 12
  completed_phases: 4
  total_plans: 19
  completed_plans: 18
  percent: 33
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-21)

**Core value:** Reconstruct the *attempt* under discipline — build the adversary so that anything surviving it is a correct road to a disproof, and anything dying leaves a machine-verified result; never invent the missing hour. Epistemic integrity (verified existence, radioactive impossibility) wins over speed, coverage, or narrative.
**Current focus:** Phase 05 — cp-sat-differential-gate-had

## Current Position

Phase: 05 (cp-sat-differential-gate-had) — EXECUTING
Plan: 7 of 7
Status: Ready to execute
Last activity: 2026-07-22

Progress: [██████████] 95%

## Performance Metrics

**Velocity:**

- Total plans completed: 14
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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
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

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 6] GATE-02 needs author input: pin the exact original G1–G6 definitions (§2) and reconcile reconstructed labels; also confirm what B₇ denotes in the PST citation. Gather early (any time from Phase 1) — required before the gate is trusted.
- [Phase 3] Linux x86_64 is the canonical reference-regeneration platform for ILP-method certificates (macOS bundled CBC is x86_64-only, Rosetta on Apple Silicon) — CI must provide it.
- [Phase 10] P4 requires pinning CLWY Theorem 3.12's exact parameter window before declaring any cell open; P5 is gated on the ETT (arXiv 2508.19646) construction study — instance sizes may exceed exact-ILP range.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-22T09:48:44.433Z
Stopped at: Completed 05-05-PLAN.md — solve_had3 on CBC+CP-SAT, size-3-forced dual-backend escalation (had_2=4<had_3=5) verified through widened trust root; CBC==CP-SAT on had_3 (EXACT-05/EXACT-03)
Resume file: None
