---
phase: 02-trust-root-corpus-schema
reviewed: 2026-07-21T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - src/alpha2/corpus/verifier.py
  - src/alpha2/corpus/schema.py
  - src/alpha2/corpus/store.py
  - src/alpha2/invariants/witness.py
  - src/alpha2/invariants/matching.py
  - tests/test_verifier_mutants.py
  - tests/test_verifier_dash_O.py
  - tests/test_verifier_isolation.py
  - tests/test_tutte_berge.py
  - tests/test_schema_roundtrip.py
  - tests/test_store_append_only.py
  - tests/test_reproduction_contract.py
findings:
  critical: 2
  warning: 6
  info: 1
  total: 9
status: resolved
---

> **RESOLUTION (2026-07-21):** All findings addressed after review.
> - CR-01, CR-02 (Critical) — FIXED with fail-before/pass-after regression tests; both independently re-verified by the orchestrator with fresh adversarial scripts (negative-index false witness now raises; coherent record substitution — including payload-swap-with-preserved-chain-hash — now raises).
> - WR-01/02/04/05/06 — FIXED with tests.
> - WR-03 (concurrency file-lock) — DEFERRED to Phase 7 (todo `store-concurrency-lock`); latent while single-threaded.
> - IN-01 (dir fsync) — DEFERRED per RESEARCH.md.
> Full suite: 48 passed. Trust-root invariants (stdlib-only, zero asserts, -O fail-closed, verbatim anchors) re-confirmed.


# Phase 2: Code Review Report — Trust Root & Corpus Schema

**Reviewed:** 2026-07-21
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

This is the program's trust root, so I hunted for any path by which `verify_model_record`/`verify_chi_witness` could **accept a false certificate**, or by which the append-only store's immutability guarantee could be **defeated**. I found two such holes, both empirically reproduced against the actual code (not merely reasoned about):

1. **`verify_chi_witness` can be made to certify a mathematically false ν(H)/χ(G) pair** via a negative-index vertex alias in `matching_M` (Python list-index wraparound). This is a direct soundness break of CHI-02's "χ pinned in both directions" guarantee — the one property the whole Tutte–Berge witness design exists to deliver.
2. **The append-only "immutability" guard does not actually detect record substitution.** It only re-verifies that whatever is currently on disk is *individually well-formed*; it never compares against any previously-observed state. A wholesale swap of a stored record for a different, self-consistent, independently-verifiable record goes completely undetected — contradicting the module's own docstring claim and the SUMMARY's assertion that "the rework is actually sound."

Both are demonstrated below with runnable reproductions (executed against `.venv/bin/python` in this repo). The `-O` fail-closed property, the AST import-boundary guard, the general (non-U=∅-hardcoded) odd-component computation, and the schema's no-truncation guarantee were all checked and are sound as implemented. `matching_number` in `matching.py` was left unreviewed per scope (verbatim Phase-1 anchor); `networkx` does not appear in `verifier.py` (confirmed via AST guard + direct read).

## Critical Issues

### CR-01: `verify_chi_witness` accepts a false ν/χ certificate via negative-index aliasing in `matching_M`

**File:** `src/alpha2/corpus/verifier.py:142-158`
**Issue:** The `matching_M` validation loop checks `len(e) != 2` and, for each edge `(a, b)`, checks `b not in adj[a]` and the `covered` set for repeats — but **never range-checks `a`/`b` against `0 <= v < n`**, unlike every other vertex-consuming check in this same file (`_build_adj`'s `0 <= u < v < n` for H_edges, `verify_model_record`'s `0 <= v < n` for branch-set vertices, and `verify_chi_witness`'s own `0 <= v < n` check on `tutte_berge_U` two lines later). Because `adj` is a plain Python `list`, `adj[-1]` silently resolves to `adj[n-1]` (Python negative-index wraparound) instead of raising. This lets a crafted `matching_M` entry alias a vertex already used elsewhere in `M` under a different literal value (e.g. `n-1` directly, and again as `-1`), so the `covered` set — which tracks the *raw* `a`/`b` values, not resolved vertex identities — never detects the collision. The result: a `matching_M` that is **not actually a valid vertex-disjoint matching in H** can be accepted as one, inflating `len(M)` (and therefore the certifiable `nu_H`) past the graph's true matching number. Because the Tutte–Berge upper-bound leg (`tutte_berge_U`) is *also* attacker-supplied and independently satisfiable for the same false `nu`, both legs of "pinned in both directions" can be forged simultaneously — this is not merely a crash, it is a soundness break.

**Concrete reproduction (executed, both steps pass with `verify_chi_witness` returning `True`):**
```python
# H = star at vertex 2 on n=3 vertices: edges (0,2), (1,2).
# TRUE nu(H) = 1 (both H-edges share vertex 2; no real matching of size 2 exists).
# TRUE chi(G) = n - nu = 2.
edges = [[0, 2], [1, 2]]
bad = {
    "H_edges": edges,
    "H_edges_sha256": <correct sha256 of edges>,
    "invariants": {"n": 3, "nu_H": 2, "chi_G": 1, "omega_G": None, "had_2": 1},
    "matching_M": [[0, 2], [-1, 1]],   # "-1" aliases adj[-1] == adj[2] (n=3)
    "tutte_berge_U": [0],              # crafted so the upper-bound leg ALSO yields nu=2
}
verify_chi_witness(bad)  # => True  (BUG: true nu=1, true chi=2; certified nu=2, chi=1)
```
Verified live against the repo: `verify_chi_witness` returns `True` for this record. `chi_G=1` would then also satisfy `verify_model_record`'s `k >= chi` gate trivially for almost any branch-set family, meaning a forged, arbitrarily-weak "certificate" could reach `store.append_certificate` (which calls exactly these two functions and nothing else touches `matching_M`).

**Fix:** Add the same range check already used for `H_edges` and `tutte_berge_U`, before the H-edge/repeat checks:
```python
for e in M:
    if len(e) != 2:
        raise VerificationError(f"malformed M edge {e!r}")
    a, b = e
    if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < n and 0 <= b < n):
        raise VerificationError(f"M edge {(a, b)!r} vertex out of range [0,{n})")
    if b not in adj[a]:
        raise VerificationError(f"M edge {(a, b)} is not an H-edge")
    ...
```
This closes both the negative-index silent-aliasing bypass and the (lesser, crash-only) positive-out-of-range `IndexError` case noted in WR-01. Add a regression test asserting `verify_chi_witness` raises on this exact construction.

### CR-02: Append-only "immutability" guard does not detect wholesale record substitution

**File:** `src/alpha2/corpus/store.py:62-85`
**Issue:** `append_certificate`'s prefix-immutability guard re-runs `verify_model_record`/`verify_chi_witness` on every already-stored record and treats a pass as proof the record "is still the one that was written." But these functions only check that a record is **internally self-consistent** (its `H_edges_sha256` matches its own `H_edges`, its model/witness are mathematically valid for that graph) — they have no notion of *which* record was previously stored at that position. A prior record can therefore be replaced **wholesale** with any other independently-valid certificate (different graph, different provenance, different everything) and the guard raises nothing, because the replacement record trivially re-verifies against itself. The subsequent "structural" prefix check (`store.py:84`, `json.dumps(new[:len(old)]) != json.dumps(old)`) is a tautology — `new[:len(old)]` is definitionally `old` since `new = old + [rec]` — and can never fire (this exact defect was already identified once, in the 02-02-SUMMARY, as the reason the original research's prefix guard was reworked; the rework does not actually close the gap it was meant to close). This directly contradicts the module's own docstring ("Any tampering that alters a prior record's edges, model, witness, or integrity hash makes the re-check RAISE") and VRF-03's append-only/immutability requirement.

**Concrete reproduction (executed against the real `store.append_certificate` API):**
```python
rec1 = full_record(seed=1, D2_MODEL)          # the REAL, original record 0
append_certificate(rec1, path=path)

rec137 = full_record(seed=137, D3_MODEL, method="exact ILP (CBC): had_2(G)=17")
with open(path, "w") as f:
    json.dump([rec137], f)                    # wholesale swap of record 0 on disk

append_certificate(full_record(seed=1, D2_MODEL), path=path)   # a fresh, valid record
# -> SUCCEEDS, no exception.
# Final corpus: [seed=137's cert masquerading as record 0, seed=1's cert as record 1]
# The ORIGINAL record 0 (seed=1's real certificate, as first appended) is GONE,
# and nothing in append_certificate detected the substitution.
```
Executed live: `Step3: append of a fresh valid record SUCCEEDED — no exception raised.` The test suite (`tests/test_store_append_only.py::test_prefix_immutability_refuses_tampered_prior_record`) only exercises a *self-inconsistent* tamper (corrupting `H_edges_sha256` to a hash that doesn't match the record's own edges) — it never tests a coherent full-record substitution, which is exactly the gap this exploits.

**Fix:** Immutability of *history* cannot be proven by re-checking self-consistency alone; it requires comparing against an independently-anchored reference to the previously-known-good state. Concrete options: (a) maintain a separate, append-only manifest/ledger file (or a running hash chain — e.g. `record_hash[i] = sha256(record_hash[i-1] + content_hash(record_i))`) that is itself checked before trusting `old`; (b) rely on the git history of the committed corpus file as the actual immutability anchor and make `append_certificate` diff against `git show HEAD:<path>` rather than the working-tree file; (c) at minimum, store a running "last known length + hash-of-hashes" value in a location the append path cannot also freely rewrite. Whichever is chosen, add a test that swaps a prior record for a *different but individually valid* record and asserts the next append raises — the current test suite does not cover this case.

## Warnings

### WR-01: `verify_chi_witness` lacks type/None validation before arithmetic and indexing, unlike `verify_model_record`

**File:** `src/alpha2/corpus/verifier.py:135-158`
**Issue:** `verify_model_record` carefully validates `n`/`chi` are `int`s before using them (`verifier.py:86-87`) and validates every branch-set vertex's type/range before use. `verify_chi_witness`, by contrast, does `n - nu != chi` (`line 139`) with no `isinstance` check on `nu` (`inv["nu_H"]`) at all — a record with `nu_H: null` (or any non-numeric type) raises an **uncaught `TypeError`**, not `VerificationError`. Confirmed live: `verify_chi_witness({..., "nu_H": None, ...})` raises `TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'`. `verify_chi_witness` is a documented standalone public entry point (it has its own direct-call tests in `test_tutte_berge.py`), so callers that only `except VerificationError` (as `store.py`'s prior-record re-verification loop does) will let this specific malformed-input case propagate uncaught, contradicting the module's stated "every check is `if not cond: raise VerificationError(...)`" discipline.
**Fix:** Validate `nu`, and revalidate `n`/`chi`, as `int`s at the top of `verify_chi_witness`, mirroring `verify_model_record`'s pattern:
```python
if not (isinstance(n, int) and isinstance(nu, int) and isinstance(chi, int)):
    raise VerificationError(f"bad n/nu/chi types (n={n!r}, nu={nu!r}, chi={chi!r})")
```

### WR-02: No combined "verify a full certificate" API — the χ-gate is only sound when both functions are called together

**File:** `src/alpha2/corpus/verifier.py` (module-level)
**Issue:** `verify_model_record`'s `k >= chi` check is only meaningful because `chi_G` is independently pinned by `verify_chi_witness`'s M+U check. Called alone, `verify_model_record` trusts `inv["chi_G"]` as given — an attacker (or a future bug) could set `chi_G` arbitrarily low and trivially satisfy `k >= chi`. `store.py` gets this right (it always calls both), but nothing in the public API prevents a future call site — a new emission script, a CLI tool, a Phase-6 status view — from treating `verify_model_record`'s return value alone as a complete proof.
**Fix:** Add a single `verify_certificate(rec)` that calls both and is the only function documented/exported as "the" verification entry point; keep the two functions available for the existing fine-grained tests but steer all production call sites (current and future) through the combined one.

### WR-03: `append_certificate` has no concurrency guard (read-modify-write race)

**File:** `src/alpha2/corpus/store.py:48-98`
**Issue:** `_load` → verify → `os.replace` has no file locking. Two concurrent `append_certificate` calls against the same path will both read the same `old`, both succeed independently, and the second `os.replace` silently discards the first append (last-writer-wins lost update) — with **no exception raised on either side**. This is not a hypothetical: the project's own STACK.md calls out `pytest-xdist` "parallel test/instance fan-out" for "Sweeps (270-seed) and P0 batch runs," which is exactly the workload pattern that would trigger this.
**Fix:** Take an `fcntl`/`msvcrt` advisory lock (or a lockfile) around the load-verify-write critical section, or document explicitly that concurrent writers to the same corpus path are unsupported and must be serialized by the caller.

### WR-04: `schema.validate_provenance` doesn't enforce the documented `process` field for `kind="seed"`

**File:** `src/alpha2/corpus/schema.py:97-117`
**Issue:** The module docstring and `provenance_seed`'s own signature (`schema.py:76-78`) document the seed-provenance shape as `{kind, family, n, seed, process}` with `process` implied required, but `validate_provenance` only requires `family`, `n`, and `seed` — a hand-built `{"kind":"seed","family":"f","n":5,"seed":1}` (no `process`) passes validation. Not exploitable against the verifier (which never reads `provenance` at all), but it is a spec/implementation mismatch that will surprise a future caller relying on `validate_provenance` as the source of truth for the documented shape.
**Fix:** Add `if kind == "seed" and "process" not in prov: raise ValueError(...)`, or update the docstring to mark `process` as recommended-not-required.

### WR-05: `canonical_edges` does not `int()`-coerce edge endpoints, unlike the rest of `build_record`

**File:** `src/alpha2/corpus/schema.py:48-60`, `214-278`
**Issue:** `_as_int_pairs` (for `matching_M`) and `_as_branch_sets` (for `model_branch_sets`) explicitly coerce every value with `int(...)` so the record is guaranteed JSON-native and round-trips by field-equality. `canonical_edges` does the same sort/min/max reshaping for `H_edges` but never calls `int(...)` on `a`/`b` — if a future caller passes edges containing non-native-`int` numeric types (e.g. `numpy.int64`, common if a future generator or nauty-adapter uses numpy), `json.dumps` would either raise `TypeError` at build time or (depending on type) silently serialize inconsistently, breaking the "no tuples/np-ints leak" round-trip guarantee the module's docstring promises for the rest of the record.
**Fix:** `out.append([int(min(a, b)), int(max(a, b))])` in `canonical_edges` for consistency with the rest of `build_record`.

### WR-06: `matching_M`/`tutte_berge_U` are read via bare dict access with no defensive `KeyError` handling anywhere in the trust root

**File:** `src/alpha2/corpus/verifier.py:145`, `161`
**Issue:** `rec["matching_M"]` and `rec["tutte_berge_U"]` are accessed directly; a record missing either key raises an uncaught `KeyError` rather than `VerificationError`. Same class of issue as WR-01 (inconsistent with the "every check raises VerificationError" discipline) — low severity on its own (it still fails closed, nothing gets written), but worth fixing in the same pass as WR-01 since the fix is identical in shape (`rec.get(...)` + explicit raise with a clear message instead of a bare KeyError/TypeError leaking out).
**Fix:** `if "matching_M" not in rec: raise VerificationError("record missing matching_M")` (and similarly for `tutte_berge_U`), before use.

## Info

### IN-01: No directory-fsync after `os.replace` in the atomic write path

**File:** `src/alpha2/corpus/store.py:87-98`
**Issue:** The write path does `tempfile → flush → os.fsync(file) → os.replace`, but never `os.fsync`s the containing directory's file descriptor afterward. On some filesystems, a power loss immediately after `os.replace` returns but before the directory entry's metadata update is durable could theoretically lose the rename. The RESEARCH doc explicitly flags this as "optionally... for durability" (i.e. acknowledged and deliberately deferred), so this is informational only, not a defect relative to the phase's own design intent.
**Fix (optional, future hardening):** `dir_fd = os.open(directory, os.O_RDONLY); os.fsync(dir_fd); os.close(dir_fd)` after `os.replace`.

---

_Reviewed: 2026-07-21_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
