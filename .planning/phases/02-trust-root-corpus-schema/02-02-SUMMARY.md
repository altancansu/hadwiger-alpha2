---
phase: 02-trust-root-corpus-schema
plan: 02
subsystem: corpus-schema-store
tags: [schema-v1, append-only, atomic-store, os-replace, tagged-union-provenance, reproduction-contract, byte-exact, semantic, full-family, stdlib-only, vrf-02, env-05]

# Dependency graph
requires:
  - src/alpha2/corpus/verifier.py — verify_model_record + verify_chi_witness (Plan 02-01 trust root)
  - src/alpha2/invariants/witness.py — extract_witness(adj,n) -> (M,U,nu) emission helper (Plan 02-01)
  - src/alpha2/generators/tfp.py — deterministic triangle_free_process(n, Random(seed)) (Phase 1)
  - Frozen canonical H_edges sha256 convention + D.2 golden 3c953d90…41e2 (Phase 1)
  - src/alpha2/paths.py — CORPUS path + ensure_parent
provides:
  - src/alpha2/corpus/schema.py — schema v1 record builder+validator; tagged-union provenance (seed/params/graph6); canonical H_edges+sha256; FULL family (had_2 = len, refuses len < chi); reproduction+backends stamping (make_reproduction/make_backends)
  - src/alpha2/corpus/store.py — append_certificate: verify-at-append gate (BOTH verifier fns + verified=True) + append-only prefix-immutability (re-verifies each prior record vs its own frozen sha256) + tempfile→fsync→os.replace atomic write
  - Round-trip proof: D.2 heuristic + D.3 seed-137 interim K16 + synthetic params/graph6 shapes; H_edges_sha256 == golden for D.2
  - Reproduction contract: byte_exact (heuristic) vs semantic (exact ILP/CP-SAT); linux-x86_64 canonical; version/platform stamps via importlib.metadata (stdlib-only)
affects: [03-corpus-reproduction-ci, 04-exactbackend-cbc]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Schema is stdlib-only (json, hashlib, importlib.metadata, platform, sys) — version stamps read installed-dist metadata WITHOUT importing networkx/pulp/ortools, preserving the verifier trust boundary"
    - "had_2 is DERIVED as len(model_branch_sets) and the builder RAISES on len < chi — the FULL family is structurally impossible to truncate (no fam[:chi] anywhere)"
    - "Records are JSON-native by construction (int coercion of edges/sets) so json.dumps→json.loads is a deep field-equality round-trip (no tuples leak)"
    - "Append-only immutability is enforced by re-verifying every prior record against its OWN stored H_edges_sha256 on each append — tampering with edges/model/witness/hash makes the re-check raise; content identity is anchored by the frozen Phase-1 sha256"
    - "Atomic write = tempfile in path.parent → flush → os.fsync → os.replace; temp unlinked on any failure (crash mid-write leaves old-or-new, never torn)"
    - "reproduction.kind is byte_exact iff method contains 'heuristic', else semantic; canonical_platform is always linux-x86_64 (bundled CBC runs under Rosetta 2 on Apple Silicon)"

key-files:
  created:
    - src/alpha2/corpus/schema.py
    - src/alpha2/corpus/store.py
    - tests/test_schema_roundtrip.py
    - tests/test_store_append_only.py
    - tests/test_reproduction_contract.py
  modified: []

key-decisions:
  - "had_2 is derived (len of stored family), not passed in: for the D.3 seed-137 INTERIM record the stored family is the 16-set K16 model so had_2=16, while method='exact ILP (CBC): had_2(G)=17' documents that the true 17-set had_2 family is produced in Phase 4 (CBC). The schema SUPPORTS k≥chi — nothing caps at chi."
  - "Append-only prefix-immutability is implemented as per-prior-record re-verification (each record re-checked against its own frozen H_edges_sha256) rather than the research's literal new[:len(old)]==old byte-compare — that literal compare is a no-op when new==old+[rec]. The re-verification is the meaningful guard and actually catches on-disk tampering; the byte-prefix compare is kept as a secondary reorder/drop invariant."
  - "backends version stamps use importlib.metadata.version() (stdlib) so schema.py never imports networkx/pulp/ortools — the schema stays inside the same stdlib-only trust boundary as the verifier."
  - "backends.cbc for exact-ILP records stamps the bundled-CBC provenance ('bundled-with-pulp-3.3.2'); the exact CBC binary version is stamped at ILP-solve time on the canonical platform in Phase 4 (Phase 2 runs no solver)."
  - "reproduction/backends are auto-populated by build_record on every certificate (overridable) so no certificate can be written lacking the ENV-05 contract."

requirements-completed: [VRF-02, ENV-05]

# Metrics
duration: ~14min
completed: 2026-07-22
---

# Phase 02 Plan 02: Schema v1 + Append-Only Atomic Store + Reproduction Contract Summary

**The corpus is now a tamper-evident falsification anchor: `schema.py` builds witness-complete schema-v1 certificates (tagged-union seed/params/graph6 provenance, canonical H_edges+golden sha256, the FULL had₂ family that cannot be truncated, M+U witness, and the byte-exact-vs-semantic reproduction contract), and `store.py` refuses to write anything the Plan-01 trust root rejects, re-proves every prior record's integrity on each append, and swaps the file atomically via os.replace — so nothing enters unverified, existing records are immutable, and a crash mid-write cannot corrupt the anchor.**

## Performance
- **Duration:** ~14 min
- **Tasks:** 3 (each RED→GREEN, 6 commits)
- **Files:** 5 created, 0 modified; full suite 42 tests green (23 Phase-1 + 19 new)

## Accomplishments
- **VRF-02 schema v1** (`src/alpha2/corpus/schema.py`): `build_record` assembles a `schema_version=1` dict with tagged-union `provenance` (`provenance_seed`/`provenance_params`/`provenance_graph6` + `validate_provenance` raising on a missing discriminator), canonical `H_edges` + frozen-convention `H_edges_sha256`, `invariants {n, num_H_edges, nu_H, chi_G, omega_G|null, had_2}`, the FULL `model_branch_sets`, `matching_M`, `tutte_berge_U`, `verified`, `method`. **had₂ is derived as `len(model_branch_sets)` and a family shorter than χ RAISES** — truncation is structurally impossible (`grep -c "model_branch_sets\[:"` == 0). stdlib-only.
- **VRF-02 append-only atomic store** (`src/alpha2/corpus/store.py`): `append_certificate` (a) re-verifies **every** prior record (`verify_model_record` + `verify_chi_witness`) → tampering with any stored record refuses the append; (b) gates the incoming record on **BOTH** verifier functions **and** `verified is True` → nothing enters unverified; (c) writes atomically `tempfile(dir=path.parent) → flush → os.fsync → os.replace`, unlinking the temp on any failure. Accepts a `path` override so tests never touch the repo corpus.
- **ENV-05 reproduction contract** (`schema.py`): `reproduction_kind_for_method` (heuristic→`byte_exact`, exact ILP/CP-SAT→`semantic`), `make_reproduction` (`canonical_platform` always `"linux-x86_64"`, `seed` recorded for byte-exact), `make_backends` (python+networkx always; `pulp`+`cbc` for exact ILP, `ortools` for CP-SAT; `platform.cbc_under_rosetta` bool). Versions come from `importlib.metadata` so **schema.py imports no third-party package**. `build_record` auto-attaches both blocks to every certificate.
- **Round-trip + adversarial proof (3 test files, 19 tests):** D.2 heuristic record round-trips with field-equality, `H_edges_sha256 == 3c953d90…41e2`, verifier accepts, `len == had_2 == 16`; D.3 seed-137 interim K16 record round-trips (had_2=16 interim, method notes 17, omega_G=14); synthetic `params` (Cayley Z_p) + `graph6` shapes validate and verify; missing-discriminator and short-family cases raise. Store: valid appends, prefix preserved, unverified/mutant refused with file byte-unchanged, tampered-prior refused, atomic write leaves no temp and survives a simulated mid-write crash.
- **Anchors preserved:** `git diff --quiet src/alpha2/corpus/verifier.py src/alpha2/verify/model.py` both clean (byte-unchanged); `data/corpus/` still `.gitkeep`-only (tests use `tmp_path`).

## Task Commits
1. **Task 1 — Schema v1 (VRF-02):** RED `617695f` (test) → GREEN `cbd1a1e` (feat) — tagged-union provenance, canonical sha256, FULL family, no-truncation guard.
2. **Task 2 — Append-only atomic store (VRF-02):** RED `cd3b598` (test) → GREEN `98d36b2` (feat) — verify-at-append gate + prefix-immutability + os.replace atomic write.
3. **Task 3 — Reproduction contract (ENV-05):** RED `e62d908` (test) → GREEN `4bc9bd8` (feat) — byte_exact vs semantic + version/platform stamps; linux-x86_64 canonical.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prefix-immutability guard reworked from a no-op byte-compare to per-record re-verification**
- **Found during:** Task 2.
- **Issue:** The research's literal prefix guard `json.dumps(new[:len(old)]) != json.dumps(old)` is a tautology when `new = old + [rec]` (`new[:len(old)]` IS `old`) — it can never fire, so it would NOT detect an edited on-disk record, defeating the append-only mitigation (threat T-02-04) and the plan's test (d).
- **Fix:** `append_certificate` now re-verifies every already-stored record (`verify_model_record` + `verify_chi_witness`) before appending; because `verify_model_record` recomputes and compares each record's `H_edges_sha256`, any tampering with a prior record's edges/model/witness/hash makes the re-check raise. The literal byte-prefix compare is retained as a cheap secondary reorder/drop invariant.
- **Files modified:** `src/alpha2/corpus/store.py`.
- **Verification:** `test_prefix_immutability_refuses_tampered_prior_record` (corrupts a stored `H_edges_sha256` → next append raises) passes.
- **Committed in:** `98d36b2`.

**2. [Rule 3 - Blocking] Version stamps via importlib.metadata to keep schema.py stdlib-only**
- **Found during:** Task 3.
- **Issue:** `make_backends` must record `networkx==3.6.1` / `pulp==3.3.2` / `ortools` versions, but Task-1 acceptance requires `schema.py` to import only stdlib (no networkx/search/generators) — importing those packages to read `__version__` would break the trust boundary.
- **Fix:** Used `importlib.metadata.version(name)` (stdlib), which reads installed-distribution metadata WITHOUT importing the package. `schema.py`'s real imports are `hashlib, importlib.metadata, json, platform, sys` — all stdlib.
- **Files modified:** `src/alpha2/corpus/schema.py`.
- **Verification:** all reproduction tests green (`python==3.12.13`, `networkx==3.6.1`, `pulp==3.3.2`, `ortools==9.15.6755` stamped correctly); no third-party import in schema.py.
- **Committed in:** `4bc9bd8`.

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking). No architectural changes, no scope creep, no authentication gates.

## Known Stubs
- **`backends.cbc` = `"bundled-with-pulp-3.3.2"` (provenance string, not the exact CBC binary version).** Intentional and documented: Phase 2 runs no solver; the exact CBC binary version is stamped at ILP-solve time on the canonical Linux x86_64 platform in **Phase 4** (ExactBackend & CBC). The field is non-null and honestly identifies the bundled solver. Not blocking — Phase 2's goal is the schema/store machinery, not exact-method execution.
- **D.3 seed-137 record stores the 16-set K16 INTERIM family** (`had_2=16`), not the true 17-set had₂ family. Intentional per RESEARCH Pattern 3 / Assumption A2: the 17-set family requires CBC ILP and is produced in **Phase 4**. The schema already SUPPORTS k≥χ (had_2 derived from family length), so Phase 4 drops in the 17-set family with no schema change.

## Verification Evidence
- `uv run pytest tests/test_schema_roundtrip.py tests/test_store_append_only.py tests/test_reproduction_contract.py -x` → 19 passed.
- `uv run pytest -q` → **42 passed** (no regression).
- `grep -c "model_branch_sets\[:" src/alpha2/corpus/schema.py` → 0 (no truncation).
- `grep -c "os.replace" src/alpha2/corpus/store.py` → 3; `grep -c "os.fsync" …` → 2.
- `git diff --quiet src/alpha2/corpus/verifier.py src/alpha2/verify/model.py` → clean (both byte-unchanged).
- `data/corpus/` → `.gitkeep` only (tests wrote to `tmp_path`).

## Next Plan Readiness
Plan 03 (Corpus Reproduction & CI — First Blood) can now regenerate the 296-instance corpus under schema v1 and append every record through `store.append_certificate` — every write is gated by the trust root, immutable once stored, and crash-safe. The `baseline.py` writer is updated to emit v1 in Phase 3.

## Self-Check: PASSED
All 5 created files present on disk; all 6 task commits (617695f, cbd1a1e, cd3b598, 98d36b2, e62d908, 4bc9bd8) exist in git history.
