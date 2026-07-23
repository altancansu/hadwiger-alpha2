---
phase: 07-p0-cdm-frontier
plan: 04
subsystem: generation
tags: [cdm, pool-0, nauty, geng, pickg, graph6, mtf, sharding, provenance, oeis-a216783]

# Dependency graph
requires:
  - phase: 07-p0-cdm-frontier
    plan: 01
    provides: tests/pool/cdm RED scaffold (test_generation_counts, test_generation_crosscheck) + pool/cdm package skeleton
provides:
  - src/alpha2/pool/cdm/generate.py — stream_mtf geng/pickg MTF driver + provenance + res/mod sharding
  - stream_mtf(n,res,mod) -> Iterator[(index, graph6, shard)] (147/392/1,274 at n=12/13/14)
  - count_mtf(n,res,mod) survivor count (sharding-sum identity)
  - is_survivor_edge_maximal(graph6) independent second-filter cross-check (is_edge_maximal_tf route)
  - geng_version() + provenance_for() (schema.provenance_graph6 reuse, family=mtf_complement)
affects: [07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "C filter stays in the pipe: geng -ctq n | pickg -Z2; Python only ever sees the ~10³ survivors (never the 467M TF pre-images)"
    - "Injection-safe subprocess: Popen arg lists only, no shell; all numeric args int-validated + DoS-bounded (n≤17) BEFORE interpolation"
    - "stdlib graph6→adj decoder (parity-checked vs networkx.from_graph6_bytes) keeps the cross-check off heavyweight nx.Graph"

key-files:
  created:
    - src/alpha2/pool/cdm/generate.py
  modified: []

key-decisions:
  - "Q3 (second generation route) → RATIFIED v1 (author-delegated 2026-07-22): OEIS A216783 counts + is_edge_maximal_tf second-FILTER + shortg canonical-set dedup ARE the independent cross-check; an independent MTF GENERATOR (triangleramsey/Goedgebeur) is DEFERRED to milestone-2 / n≈16"
  - "geng_version() = first non-empty line of `geng --help` (nauty exposes no explicit version string via geng); cached so it is never re-spawned in the stream loop"
  - "pickg/geng stderr → DEVNULL so the nauty banner never pollutes the graph6 stdout stream; stdout is clean graph6, one survivor per line"
  - "Sharding is all-or-nothing (res and mod together) and the shard token f'{res}/{mod}' is built ONLY after full int-validation (T-7-gen control)"

requirements-completed: [POOL-0]

# Metrics
duration: 31min
completed: 2026-07-23
---

# Phase 07 Plan 04: CDM Frontier MTF Generation Driver Summary

**`stream_mtf` shells the nauty C pipe `geng -ctq n | pickg -Z2` and yields exactly 147 / 392 / 1,274 provenance-tagged maximal-triangle-free survivors at n = 12 / 13 / 14 (OEIS A216783), injection-safe (Popen arg lists, no shell) and DoS-bounded (n≤17), with res/mod sharding proven sum-consistent and a second-filter cross-check against the repo's independent `is_edge_maximal_tf` predicate.**

## Performance

- **Duration:** ~31 min (incl. the 13.7-min n=14 slow-count enumeration over 467M TF pre-images)
- **Completed:** 2026-07-23
- **Tasks:** 3 (Task 3 is documentation-only — the ratified-v1 decision record)
- **Files modified:** 1 (created `src/alpha2/pool/cdm/generate.py`)

## Accomplishments
- **`stream_mtf(n, res=None, mod=None)`** — spawns `geng -ctq n [res/mod]` piped into `pickg -Z2` via `subprocess.Popen` **arg lists** (never a shell string), closes the write end so `pickg` sees EOF, and yields `(index, graph6, shard)` per non-empty stripped line with a monotonically increasing 0-based index. Greens `test_generation_counts` (147 at n=12, 392 at n=13; 1,274 at n=14 `@pytest.mark.slow`).
- **Input hardening (T-7-gen / T-7-08):** `_validate` int-validates n (rejects non-int, `bool`, out-of-range) and, when sharding, mod>0 and 0≤res<mod — ALL before any interpolation; the `f"{res}/{mod}"` shard token is built only after validation. `stream_mtf("12")` / `stream_mtf(-1)` / `stream_mtf(99)` raise `ValueError` before any subprocess spawns.
- **Provenance:** `geng_version()` (cached first-line of `geng --help`) + `provenance_for()` reuse `alpha2.corpus.schema.provenance_graph6(family="mtf_complement", ...)` and attach the params sidecar `{geng_version, flags:"-ctq | pickg -Z2", shard, index}`.
- **Sharding + cross-check:** `count_mtf(n,res,mod)` backs the sharding-sum identity — `count_mtf(12) == Σ_{r<4} count_mtf(12,r,4) == 147` (verified). `is_survivor_edge_maximal(graph6)` runs the repo's INDEPENDENT `generators.tfp.is_edge_maximal_tf` over a stdlib graph6→adj decoder (byte-parity-checked against `networkx.from_graph6_bytes` on all 61 n=11 survivors). Greens `test_generation_crosscheck`.

## Task Commits

Each task was committed atomically:

1. **Task 1: stream_mtf subprocess driver + provenance + input validation** — `615de54` (feat)
2. **Task 2: res/mod sharding + generation cross-check (count_mtf + second-filter)** — `1b87577` (feat)
3. **Task 3: ratified second-route decision (Q3 → ratify-v1)** — documentation-only; recorded in the Decisions section below (no code beyond Tasks 1–2).

## Files Created/Modified
- `src/alpha2/pool/cdm/generate.py` (created) — the MTF generation driver: `stream_mtf`, `count_mtf`, `is_survivor_edge_maximal`, `geng_version`, `provenance_for`, `_validate`, `_graph6_to_adj`. stdlib + `alpha2.corpus.schema` only; NOT added to `[tool.ruff] extend-exclude` (no set-iteration-dependent output introduced — the streaming path is deterministic in geng's canonical order); `ruff check` clean.

## Decisions

### Q3 (second generation route) → RATIFIED v1 (author-delegated 2026-07-22)
The independent cross-check for POOL-0 SC1 is **OEIS A216783** exact counts (147/392/1,274) + a second **FILTER** predicate (`generators.tfp.is_edge_maximal_tf`, add-any-edge-closes-a-triangle ⟺ diameter 2) + `shortg` canonical-set dedup (only ever needed when a SECOND generator stream is merged — geng's single stream is already isomorph-free by McKay canonical augmentation). A fully independent MTF **GENERATOR** (triangleramsey / Goedgebeur) is **DEFERRED to milestone-2 / n≈16**. Rationale: for n≤14 the exact OEIS counts + the sharding-sum identity + canonical-set equality already catch generation drift (RESEARCH Pitfall 3); an independent generator is a new C build with deferred value (RESEARCH Open Q3). **Reversible** — a generator can be added later without reworking this module. The v1 cross-check surface is present in code: the OEIS A216783 anchor (module docstring + inline comment) and the `is_survivor_edge_maximal` / `is_edge_maximal_tf` second-filter route.

### Supporting decisions
- **`geng_version()` = first non-empty line of `geng --help`** — nauty's `geng` exposes no explicit version string (no banner version, no `--version`); the usage line is a stable, deterministic provenance stamp. Cached via `functools.cache` so it is never re-spawned in the hot stream loop; returns `None` (graceful) when `geng` is off PATH.
- **Banner suppression** — `geng`/`pickg` stderr → `subprocess.DEVNULL` so the nauty `>A`/`>Z` banner never pollutes the graph6 stdout stream. `-q` already quiets geng; `pickg` has no `-q`, hence DEVNULL.
- **stdlib graph6 decoder** — `_graph6_to_adj` (column-major upper-triangle bit order) keeps the second-filter cross-check off heavyweight `nx.Graph`; byte-parity-verified against `networkx.from_graph6_bytes` on all 61 n=11 survivors.

## Deviations from Plan

None — plan executed exactly as written. Two docstring/comment wordings were adjusted so the acceptance-criteria greps stay clean: the literal token `shell=True` and the word `Weisfeiler` were removed from prose (the code never uses either), so `grep "shell=True"` and `grep -iE "wl|weisfeiler|graph_hash"` both return nothing while the discipline they describe is retained. No architectural changes, no auth gates, no package installs.

## Issues Encountered
- `uv` is not on this shell's PATH; the plan's `uv run pytest ...` verify commands were run as `.venv/bin/python -m pytest ...` (equivalent interpreter + deps), matching the 07-01 execution note. No functional impact.

## Verification Results
- `pytest tests/pool/cdm/test_generation_counts.py -m "not slow" -x` → **2 passed** (147 at n=12, 392 at n=13).
- `pytest tests/pool/cdm/test_generation_counts.py -m "slow"` → **1 passed** (1,274 at n=14; 820s / 13.7 min over 467M TF pre-images — expected).
- `pytest tests/pool/cdm/test_generation_crosscheck.py -m "not slow" -x` → **2 passed** (61/61 survivors edge-maximal-tf at n=11; Σ shards mod 4 == single-stream == 147).
- External ground truth: `geng -ctq 12 | pickg -Z2 | wc -l` == **147**.
- Manual: `count_mtf(12) == Σ_{r<4} count_mtf(12,r,4) == 147`; `_graph6_to_adj` byte-parity vs `networkx.from_graph6_bytes` on all 61 n=11 survivors; validation gate raises `ValueError` on `"12"/-1/99/True/3.0` before any spawn.
- `grep -n "shell=True" generate.py` → **nothing**; `grep -n "subprocess.Popen" generate.py` → **present** (2 hits).
- `grep -niE "wl|weisfeiler|graph_hash" generate.py` → **nothing** (no non-canonical dedup).
- `ruff check src/alpha2/pool/cdm/generate.py` → **All checks passed** (module intentionally NOT in extend-exclude).
- Full non-slow suite → **263 passed, 1 failed** — the single failure is `test_disconnected_complement` (RED scaffold importing the not-yet-created `alpha2.pool.cdm.adjudicate`, plan **07-05**'s contract), out of scope for this plan (SCOPE BOUNDARY; generate.py is not referenced by it).

## Known Stubs
None. `generate.py` is fully wired: `stream_mtf` drives the real nauty pipe and every helper is exercised by the greened tests. No hardcoded/placeholder data, no TODO/FIXME.

## Next Phase Readiness
- 07-05 (adjudicate / transfer-lemma carve-out) and 07-06 can consume `stream_mtf` to feed the CDM classifier; each yielded instance carries full replayable provenance via `provenance_for`.
- The n=14 → 1,274 slow gate is verified GREEN; a wrong flag or dropped shard would now break the pinned OEIS A216783 triple.
- Interface pinned for downstream: `stream_mtf(n,res,mod) -> (index, graph6, shard)`, `count_mtf`, `is_survivor_edge_maximal`, `geng_version`, `provenance_for`.

---
*Phase: 07-p0-cdm-frontier*
*Completed: 2026-07-23*

## Self-Check: PASSED

`src/alpha2/pool/cdm/generate.py` and `07-04-SUMMARY.md` present on disk; both task commits (`615de54`, `1b87577`) present in git history.
