"""Single ordered-freeze entry point: empty corpus -> exactly 296 records.

This is the ONE command that deterministically rebuilds the full certificate
corpus. It deletes/recreates `paths.CORPUS` as an empty JSON array, then invokes
the four reproduction drivers in a fixed order, appending every record through the
store's verify-at-append trust root:

    baseline   ->  14  (12 baseline instances + showpieces n=301, n=501)   TFP
    sweep      -> 269  (n=31 s100..299 excl 137, n=51 s100..149, n=101 s100..119)  TFP
    cayley_run ->  12  (p in {31,53,101,151}, seed 5000+10p+k, k in 0..2)   Cayley
    seed137    ->   1  (Appendix D.3 K16 literal, solver-free)              TFP
    ------------------------------------------------------------------------------
    total      -> 296  (284 triangle_free_process_complement + 12 cayley_maximal_sumfree_Zp)

After the run, freeze asserts len == 296 and the exact family counts (284, 12).
These asserts govern the count/accounting invariant, NOT a verification decision —
every record's correctness is already enforced (raise-based) by
`store.append_certificate` -> `verify_certificate` at append time (Pitfall 6).

SLOW-FREEZE NOTE (W5 / Pitfall 5 / A3): sequential `append_certificate` re-verifies
the whole prior prefix on every append (O(N^2), tens of thousands of verify calls,
plus n=501 witness extraction), which can run for minutes — an accepted MVP tradeoff.
Run this in the background (or with a raised tool timeout) if needed. Do NOT weaken
verify-at-append or add a batch path here.

Run:  python -m alpha2.repro.freeze
"""
import collections
import json
import os

from alpha2 import paths
from alpha2.repro import baseline, sweep, cayley_run, seed137


def freeze(path=None):
    """Rebuild the corpus from empty; return the 296-record list."""
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    path = os.fspath(path)

    # Delete/recreate as an empty JSON array — the store is append-only and refuses a
    # reorder, so a freeze MUST begin from empty (never double-append onto a prior run).
    if os.path.exists(path):
        os.remove(path)
    with open(path, "w") as fh:
        json.dump([], fh)

    print("=== FREEZE: rebuilding the 296-record corpus from empty ===\n", flush=True)
    baseline.main()                 # 14 TFP (baseline.main empties+writes to paths.CORPUS)
    sweep.main(path=path)           # +269 TFP
    cayley_run.main(path=path)      # +12 Cayley
    seed137.main(path=path)         # +1 TFP (D.3 literal, solver-free)

    with open(path) as fh:
        corpus = json.load(fh)

    counts = collections.Counter(r["provenance"]["family"] for r in corpus)
    assert len(corpus) == 296, f"expected 296 records, got {len(corpus)}"
    assert counts["triangle_free_process_complement"] == 284, dict(counts)
    assert counts["cayley_maximal_sumfree_Zp"] == 12, dict(counts)
    print(f"\n=== FROZEN: {len(corpus)} records ({dict(counts)}) at {path} ===", flush=True)
    return corpus


def main():
    freeze()


if __name__ == "__main__":
    main()
