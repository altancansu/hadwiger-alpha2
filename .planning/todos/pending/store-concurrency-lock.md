---
id: store-concurrency-lock
created: 2026-07-21
resolves_phase: 7
source: phase-2 code-review WR-03
severity: warning
---

# append_certificate has no concurrency guard

`src/alpha2/corpus/store.py::append_certificate` does read-modify-write with no file lock.
Two concurrent appends can lose a record (last-writer-wins on os.replace). Phase 2 runs
single-threaded so this is latent, but the project's own plans use pytest-xdist parallel
sweeps (P1 270-seed, P0 batch) in Phases 7/9 which WILL append concurrently.

**Fix in the batch/sweep phase (7 or 9):** add an advisory file lock (fcntl.flock on a
sidecar .lock, or atomic O_EXCL lockfile) around the load→append→os.replace critical section,
OR shard per-worker corpora + merge through `shortg`/canonical dedup at the end.

Ref: 02-REVIEW.md WR-03.
