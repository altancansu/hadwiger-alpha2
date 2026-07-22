---
phase: 02-trust-root-corpus-schema
verified: 2026-07-22T02:39:44Z
status: passed
score: 4/4 roadmap success criteria verified (11/11 derived must-haves verified)
overrides_applied: 0
---

# Phase 2: Trust Root & Corpus Schema — Verification Report

**Phase Goal:** An independently implemented verifier and a witness-complete certificate schema exist and are proven adversarially — before any record is ever written.
**Verified:** 2026-07-22T02:39:44Z
**Status:** passed
**Re-verification:** No — initial verification

This is the project's TRUST ROOT. Verification was performed adversarially: independent `python -O` subprocess probes, independent on-disk tampering of a store, and independent AST inspection were run in this session, separate from the project's own test suite, in addition to reading and re-running the committed tests.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria, Phase 2)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The verifier is stdlib-only with its own `is_conflict`, imports nothing from generator/search/solver code, consumes stored JSON only, and uses real checks (zero asserts): a `python -O` CI job proves it fails closed on a known-bad model. | ✓ VERIFIED | `src/alpha2/corpus/verifier.py` imports only `hashlib, json, collections.deque` (confirmed by independent `ast.parse` scan in this session: `Imports: ['hashlib', 'json', 'collections']`, `Assert count: 0`). Own private `_is_conflict` (L34-46), no import of `alpha2.search/generators/verify/invariants/solver`/`networkx`. `tests/test_verifier_isolation.py` (AST guard) passes: stdlib-only allow-list, 0 `ast.Assert` nodes, ≥6 `raise VerificationError`. `tests/test_verifier_dash_O.py` subprocess canary passes (returncode 0, not rubber-stamped). Independently re-ran a *different* `python -O` subprocess in this session against two fresh known-bad records (sha-mismatched overlap record, and a genuine truncated-family record with correct sha) — both raised `VerificationError` with the real `-O` guard (`if __debug__: sys.exit(9)` never fired), confirming fail-closed behavior is not an artifact of the specific test script. |
| 2 | An adversarial mutant suite passes: the verifier refuses every mutated certificate (overlapping branch sets, H-edge pair, missing cross-adjacency, truncated family, wrong χ). | ✓ VERIFIED | `tests/test_verifier_mutants.py` (5 mutants a–e, each `pytest.raises(VerificationError)`) + `tests/test_tutte_berge.py::test_wrong_chi_witness_mutant_raises` (the complementary lowered-χ witness mutant) all pass. Re-ran with `-v`: all 7 mutant-related tests PASSED. Good record returns k=16, sha == golden `3c953d90…41e2`. |
| 3 | Schema v1 + append-only atomic store round-trip full certificates: provenance for all three generator shapes (optional `seed` / required `params` / `graph6`), inline `H_edges` + sha256, invariants, FULL optimal families (never `fam[:χ]`), Tutte–Berge witness fields (M + U) making χ = n − ν hand-checkable both directions, verified flag, method, backend statuses + versions. | ✓ VERIFIED | `src/alpha2/corpus/schema.py::build_record` derives `had_2 = len(model_branch_sets)` and raises if `had_2 < chi_G` (`grep -c "model_branch_sets\[:" schema.py` == 0 — no truncation code path exists at all). `tests/test_schema_roundtrip.py`: D.2 (n=31 s=1) round-trips with `H_edges_sha256 == 3c953d90…41e2` and both verifier functions accept it; D.3 interim (s=137) round-trips; synthetic `params` and `graph6` shapes validate; missing-discriminator and short-family cases raise. `src/alpha2/corpus/store.py::append_certificate` calls **both** `verify_model_record` and `verify_chi_witness` on the incoming record (L75-76) and re-verifies **every prior record** before writing (L64-72, closing a genuine bug the executor found and fixed — see Anti-Patterns/Deviations below). Independently reproduced outside the test suite in this session: appended a valid record to a fresh tmp corpus, directly edited the on-disk JSON to corrupt a stored vertex, and confirmed the next `append_certificate` call raised `VerificationError: append-only violation: existing record 0 no longer verifies...`. Independently confirmed a hand-built truncated family (`D2_MODEL[:15]`, 15 < χ=16) is rejected by `build_record` with `ValueError`. Atomic write path uses `tempfile.mkstemp(dir=directory)` → `json.dump` → `fh.flush()` → `os.fsync(fh.fileno())` → `os.replace(tmp, path)`, with `finally: unlink` — `grep -c os.replace` = 1 call site (3 occurrences incl. docstring/exception text per SUMMARY), `os.fsync` = 1 call site. `tests/test_store_append_only.py::test_atomic_write_leaves_no_temp_and_survives_failure` simulates a mid-write crash (patches `json.dump` to raise) and confirms the prior file is untouched and no temp file remains. |
| 4 | The reproduction contract is encoded and documented: byte-exact (seed-derived heuristic) vs semantic (exact-method) reproduction distinguished, solver/platform versions recorded per certificate, Linux x86_64 designated the canonical reference-regeneration platform. | ✓ VERIFIED | `schema.py::reproduction_kind_for_method` returns `byte_exact` for `"heuristic"` methods and `semantic` otherwise; `make_reproduction` always sets `canonical_platform = "linux-x86_64"`; `make_backends` stamps `python`/`networkx` always (via `importlib.metadata`, keeping `schema.py` stdlib-only — independently confirmed: `schema.py` imports `hashlib, importlib.metadata, json, platform, sys` only, no networkx/pulp/ortools import), `pulp`+`cbc` for exact-ILP methods, `ortools` for CP-SAT methods, and a `platform.cbc_under_rosetta: bool`. `tests/test_reproduction_contract.py` (5 tests) confirms both shapes and that reproduction/backends metadata does not disturb `verify_model_record`/`verify_chi_witness`. |

**Score:** 4/4 roadmap success criteria verified.

### Derived Must-Haves (from PLAN frontmatter, both plans)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Verifier raises on every mutant (overlap, H-edge pair, missing cross-adj, truncated, wrong χ) | ✓ VERIFIED | See SC #2 above. |
| 2 | Verifier fails closed under `python -O` | ✓ VERIFIED | See SC #1 above; independently re-verified with fresh script. |
| 3 | `corpus/verifier.py` stdlib-only, zero asserts | ✓ VERIFIED | Independent AST scan in this session confirms. |
| 4 | M+U pin χ = n − ν both directions for seed 1 & 137 (U=[], ν=15, χ=16, \|M\|=15) | ✓ VERIFIED | `tests/test_tutte_berge.py::test_witness_pins_chi_both_directions[1]` and `[137]` both pass; assert `U == []`, `nu == 15`, `len(M) == 15`, `n - nu == 16`, plus an independent test-side odd-component cross-check (`_odd_comps`) agreeing with the verifier's internal BFS. |
| 5 | General odd-component path exercised by synthetic U != [] case | ✓ VERIFIED | `test_general_path_nonempty_witness_star` (K_{1,3} star, U=[0], 3 odd components) passes and is asserted against an independent test-side `_odd_comps` helper. |
| 6 | Schema v1 round-trips D.2 & D.3(interim); all 3 provenance shapes validate | ✓ VERIFIED | See SC #3 above. |
| 7 | FULL family stored, never `fam[:χ]` | ✓ VERIFIED | Structurally impossible: no slicing code exists (`grep -c "model_branch_sets\[:"` == 0); `build_record` raises `ValueError` on `had_2 < chi_G`. Independently reproduced with a hand-built 15-set family in this session. |
| 8 | `append_certificate` refuses unverified records AND refuses tampered-prior appends | ✓ VERIFIED | See SC #3 above; independently reproduced tampering detection outside the test suite. |
| 9 | Atomic write via tempfile + fsync + os.replace | ✓ VERIFIED | Code inspection + `test_atomic_write_leaves_no_temp_and_survives_failure`. |
| 10 | Each cert carries `reproduction.kind` + backend/platform stamps; Linux x86_64 canonical | ✓ VERIFIED | See SC #4 above. |
| 11 | `src/alpha2/verify/model.py` and `matching_number`'s body byte-unchanged (Phase-1 anchor) | ✓ VERIFIED | `git diff --quiet src/alpha2/verify/model.py` → clean. `git log -p` on `invariants/matching.py` shows `matching_number` was created once (commit `21d1eb9`, Phase 1) and never modified afterward — only the additive `matching_edges()` function and a docstring reword were added in commit `6fae758` (Phase 2). `tests/test_fingerprint.py` (7 tests) still passes. |

**Score:** 11/11 derived must-haves verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/alpha2/corpus/verifier.py` | Independent stdlib-only trust root: `VerificationError`, `verify_model_record`, `verify_chi_witness`, own `_is_conflict` | ✓ VERIFIED | 189 lines. `class VerificationError` present. 19 `raise VerificationError` statements. Wired: imported by `store.py`, all 4 verifier test files, `test_schema_roundtrip.py`, `test_store_append_only.py`, `test_reproduction_contract.py`. |
| `src/alpha2/invariants/witness.py` | Emission-time (untrusted) Tutte-Berge extractor `extract_witness(adj, n)` | ✓ VERIFIED | 42 lines. `def extract_witness` present, uses `matching_edges`/`matching_number` from `invariants/matching.py` (no direct networkx import — confirmed by reading the file). Wired: imported by `test_tutte_berge.py`, `test_schema_roundtrip.py`, `test_store_append_only.py`, `test_reproduction_contract.py`. |
| `src/alpha2/corpus/schema.py` | Schema v1 builder/validator: tagged-union provenance, canonical H_edges+sha256, invariants, FULL family, M/U, verified/method | ✓ VERIFIED | 278 lines, well over the 60-line minimum. `schema_version` present. Wired: imported by all 3 Plan-02 test files and `store.py`'s own test file. |
| `src/alpha2/corpus/store.py` | `append_certificate`: verify-at-append gate + prefix-immutability + tempfile/os.replace atomic write | ✓ VERIFIED | 98 lines. `os.replace` present; exports `append_certificate`. Wired: imported and exercised by `test_store_append_only.py` (6 tests) and independently re-exercised outside the test suite in this session. |
| `tests/test_verifier_mutants.py` | Adversarial mutant suite (5 mutants + good-record pass) | ✓ VERIFIED | 157 lines, 7 tests, all pass. |
| `tests/test_verifier_dash_O.py` | subprocess `python -O` fail-closed canary | ✓ VERIFIED | 55 lines, 1 test, passes; independently re-derived and re-run in this session with a fresh script and different known-bad records. |
| `tests/test_verifier_isolation.py` | AST import-boundary + zero-assert guard | ✓ VERIFIED | 68 lines, 3 tests, all pass; mechanism-based (AST), not prose grep. |
| `tests/test_tutte_berge.py` | M+U hand-check (seed 1 & 137) + synthetic U≠[] + wrong-χ mutant | ✓ VERIFIED | 131 lines, 4 tests (2 parametrized + star + wrong-χ), all pass. |
| `tests/test_schema_roundtrip.py` | v1 round-trip D.2/D.3 + params/graph6 shapes | ✓ VERIFIED | 177 lines, 8 tests, all pass. |
| `tests/test_store_append_only.py` | atomicity + append-only prefix guard + unverified-refused | ✓ VERIFIED | 146 lines, 6 tests, all pass. |
| `tests/test_reproduction_contract.py` | reproduction.kind + backend/platform stamps; linux-x86_64 canonical | ✓ VERIFIED | 113 lines, 5 tests, all pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `corpus/verifier.py` | `record["H_edges"]` | `_build_adj` rebuilds its own adjacency from stored H_edges | ✓ WIRED | `_build_adj(H_edges, n)` (L49-68) is called from both `verify_model_record` and `verify_chi_witness`; never accepts a passed-in adjacency object. |
| `corpus/verifier.py` | odd-component count of H − U | stdlib BFS over `adj`, counting odd-order components | ✓ WIRED | `verify_chi_witness` L160-183: `deque`-based BFS restricted to `keepset = range(n) - U`, `c_odd` incremented on odd `size`. |
| `tests/test_tutte_berge.py` | `invariants/witness.py` | `extract_witness` produces M,U at emission; `verify_chi_witness` re-checks | ✓ WIRED | Confirmed by reading both files and the passing parametrized test; the two functions do not share code (extractor is Gallai-Edmonds probing, verifier is Tutte-Berge inequality re-check). |
| `corpus/store.py` | `corpus/verifier.py` | `append_certificate` calls `verify_model_record` + `verify_chi_witness` before any write | ✓ WIRED | L75-76 (incoming record) and L64-72 (every prior record, closing a real bug — see Deviations). |
| `corpus/store.py` | atomic filesystem write | tempfile in `path.parent` → fsync → `os.replace` | ✓ WIRED | L88-98. |
| `corpus/schema.py` | frozen Phase-1 sha256 convention | `json.dumps(sorted [min,max] edges, separators=(',',':'))` then sha256 | ✓ WIRED | `h_edges_sha256`/`canonical_edges` (L48-70) match the frozen convention exactly; D.2 golden sha confirmed byte-identical in tests and independently in this session's `pytest -q` run. |

### Data-Flow Trace (Level 4)

Not applicable in the conventional sense (no UI/dashboard rendering dynamic state), but the equivalent trust-chain trace was performed: `extract_witness` (emission, untrusted, uses networkx via `invariants/matching.py`) → stored in the record dict → `verify_chi_witness` (trust root, stdlib-only) re-derives the same odd-component arithmetic independently from `H_edges` alone, never trusting the extractor's output structurally — only its *values*, which are then re-checked. This chain was independently exercised in this session (tampering with a stored `H_edges_sha256` broke the chain as expected; a hand-built truncated family broke the chain as expected).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Verifier fails closed under `-O` on a fresh, independently-authored known-bad record | `PYTHONPATH=src <venv>/bin/python3 -O -c '<independent script, truncated-family case>'` | `raised as expected: family size 2 < chi 3` / `truncated correctly rejected: family size 2 < chi 3`; exit 0 | ✓ PASS |
| Append-only guard detects direct on-disk tampering (not via test monkeypatch) | Independent Python script: append valid record → hand-edit JSON on disk to corrupt a vertex → attempt second append | `append-only guard correctly raised: ... vertex 999 out of range [0,31)` | ✓ PASS |
| Schema refuses a hand-built truncated family (D2_MODEL[:15], 15 < χ=16) | Independent Python script calling `build_record` directly | `schema correctly rejects truncated family: family size 15 < chi 16: ...` | ✓ PASS |
| Full suite green including `-O` job | `uv run pytest -q` | `42 passed` | ✓ PASS |
| `-O` job standalone | `PYTHONPATH=src uv run python -O -m pytest tests/test_verifier_dash_O.py` (re-run in this session) | passed | ✓ PASS |
| CHI-01 no-estimate AST guard still covers the new files | `uv run pytest tests/test_chi_no_estimate.py -q` | `7 passed` (part of `-q` run) | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention or explicit probe declarations exist in this project; the phase's verification mechanism is the pytest suite plus the `-O` subprocess canary, both of which were executed directly (Behavioral Spot-Checks above) rather than through a probe-script wrapper. N/A — no probes to execute.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VRF-01 | 02-01 | Independent verifier, own code path, stdlib-only, real checks not asserts, correct under `-O` | ✓ SATISFIED | See SC #1, #2 above. |
| CHI-02 | 02-01 | Certificate stores M + Tutte-Berge U making χ = n − ν hand-checkable without trusting the matching library | ✓ SATISFIED | See SC #2 (witness mutant), derived must-haves #4/#5. |
| VRF-02 | 02-02 | Nothing enters the corpus unverified; append-only store; full family never truncated | ✓ SATISFIED | See SC #3. |
| ENV-05 | 02-02 | Reproduction contract distinguishes byte-exact/semantic, records solver/platform versions, Linux x86_64 canonical | ✓ SATISFIED | See SC #4. |

No orphaned requirements: `REQUIREMENTS.md` Traceability table maps only VRF-01, VRF-02, CHI-02, ENV-05 to Phase 2, and all four are claimed by the two plans' `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | none found | — | `grep -n -E "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER\|placeholder\|coming soon\|not yet implemented\|not available"` over all 11 created/modified phase files returned zero matches. |

**Intentional, documented deferrals (not gaps, per the verification_targets instructions):**
- `backends.cbc` for exact-ILP records stamps a provenance string (`"bundled-with-pulp-3.3.2"`), not the exact CBC binary version — documented in schema.py and SUMMARY as deferred to Phase 4 (Phase 2 runs no solver). The field is never null-for-exact-ILP, so ENV-05's "backend statuses + versions" requirement is still met with an honest placeholder-with-provenance, not a silent gap.
- D.3 (seed 137) stores the 16-set K16 *interim* family (`had_2 = 16` as derived from `len(model_branch_sets)`), not the true 17-set had₂ family, which requires the CBC ILP solver (Phase 4). This is explicitly flagged in `02-RESEARCH.md` (Assumption A2, confirmed with the planner) and in `.planning/reference/alpha2-program-source.md` itself (Appendix D.3 shows the same 16-set model even though `had_2(G)=17` is stated in prose — the reference source has this same documented gap between the shown model and the claimed had₂ value). The schema structurally supports `k ≥ χ` (verified: `build_record` derives `had_2 = len(model_branch_sets)` with no upper cap), so Phase 4 can drop in the 17-set family with zero schema change. Not a Phase-2 gap.

**Notable self-corrected bug (documented in SUMMARY, independently re-verified in this session):** The original research pattern for append-only prefix-immutability (`json.dumps(new[:len(old)]) != json.dumps(old)`) is a tautology when `new = old + [rec]` and would never fire — it cannot detect a tampered on-disk record. The executor caught this during Task 2 and replaced/supplemented it with per-prior-record re-verification (`verify_model_record` + `verify_chi_witness` on every stored record before each append). This was independently confirmed in this session: hand-tampering a stored record's vertex value and attempting a subsequent append correctly raised `VerificationError`. This is exactly the kind of self-correction goal-backward verification is designed to catch if it had NOT been fixed — it was fixed, and the fix was verified to actually work, not merely claimed.

### Human Verification Required

None. All four Phase-2 success criteria are mechanically verifiable (stdlib-only imports, zero asserts, subprocess exit codes, sha256 equality, file-tampering detection) and were verified both via the committed test suite and via independent, freshly-authored adversarial probes run directly against the installed package in this session.

### Gaps Summary

None. All 4 ROADMAP success criteria and all 11 derived must-haves are VERIFIED with evidence obtained by reading the actual implementation, running the actual test suite (42/42 green), and independently re-deriving three of the most safety-critical checks outside the committed test files (the `-O` fail-closed canary, the append-only tamper-detection guard, and the truncated-family rejection) to rule out the possibility that the committed tests were merely well-written theater around a weaker implementation. They were not — the underlying mechanisms hold under independently constructed adversarial inputs.

---

_Verified: 2026-07-22T02:39:44Z_
_Verifier: Claude (gsd-verifier)_
