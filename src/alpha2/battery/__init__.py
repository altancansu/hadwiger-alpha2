"""The kill battery (Phase 6): the 7-step runbook per candidate + its results log.

This package owns NO new mathematics. `pipeline.run_candidate` wires the already-built
gate (`alpha2.gate`), exact chi (`alpha2.invariants`), the dual-backend had_2 solvers +
`differential_verdict` (`alpha2.solvers`), and the frozen trust root
(`alpha2.corpus.verifier`) into one deterministic-in-(n, seed) control flow; `log` is the
append-only JSONL results stream (CLI-02) — a separate, simpler contract from the
hash-chained fact corpus.

Import discipline: this `__init__` imports NOTHING from its own submodules (importing the
package must never pull in `pipeline`/`log` — solver libraries load lazily, at call time).
"""
