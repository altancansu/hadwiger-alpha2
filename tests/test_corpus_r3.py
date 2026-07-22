"""R3 pinned-interpreter replay gate — full driver replay, byte-identical stored JSON.

R3 is the strongest (and most fragile) reproduction notion: it re-runs the actual
`repro/` drivers under the single-RNG contract v1 — generation THEN heuristic search
on one `random.Random(seed)` — into a throwaway `tmp_path` corpus, then asserts the
produced record's load-bearing fields are byte-identical to the committed record in
`paths.CORPUS`. Because the heuristic model depends on CPython set-iteration order and
`rng` consumption, byte-equality only holds on the PINNED interpreter (3.12.13).

Version gate (Pitfall 4 — R3 must not be the only reproduction notion): strict
byte-equality is asserted ONLY on CPython 3.12.13. On any other interpreter the test
downgrades to "a verifying model is produced" (routes through raise-based
`verify_certificate`), so the newer-Python CI canary fails for a genuine hash reason,
not R3 fragility. R1 (witness re-verify) and R2 (generator determinism) remain the
version-proof primary checks.

Marked `slow`: a release/nightly gate only (the `slow` marker is registered in
pyproject from Plan 01 — nothing new is registered here). It replays into `tmp_path`
and NEVER touches the repo corpus.
"""
import json
import sys

import pytest

from alpha2 import paths
from alpha2.corpus.verifier import verify_certificate
from alpha2.repro import baseline, cayley_run

PINNED_INTERPRETER = "3.12.13"

# The fields the verifier and the reproduction contract are pinned to. reproduction/
# backends (environment stamps) and chain_sha256 (corpus-position dependent) are
# deliberately EXCLUDED — they are not part of the byte-replay claim.
LOAD_BEARING = ("H_edges", "model_branch_sets", "matching_M", "tutte_berge_U", "invariants")


def _committed_records():
    with open(paths.CORPUS) as fh:
        return json.load(fh)


def _last_stored(path):
    with open(path) as fh:
        return json.load(fh)[-1]


def _find_seed(records, n, seed):
    hits = [
        r for r in records
        if r["provenance"].get("kind") == "seed"
        and r["provenance"].get("n") == n
        and r["provenance"].get("seed") == seed
    ]
    assert len(hits) == 1, (f"expected one committed (n={n}, seed={seed})", len(hits))
    return hits[0]


def _find_cayley(records, p, seed):
    hits = [
        r for r in records
        if r["provenance"]["family"] == "cayley_maximal_sumfree_Zp"
        and r["provenance"].get("n") == p
        and r["provenance"].get("seed") == seed
    ]
    assert len(hits) == 1, (f"expected one committed Cayley (p={p}, seed={seed})", len(hits))
    return hits[0]


def _assert_replay(replay, target, label):
    """Version-gated R3 check: byte-identical on the pinned interpreter, else verifying."""
    if sys.version.split()[0] == PINNED_INTERPRETER:
        for field in LOAD_BEARING:
            assert replay[field] == target[field], (
                label, field, "R3 byte drift on the pinned interpreter"
            )
    else:
        # Newer interpreter: do not assert byte-equality (Pitfall 4). Require only that
        # the replayed record verifies — a genuine hash mismatch surfaces via R2/canary.
        k = verify_certificate(replay)
        assert k >= replay["invariants"]["chi_G"], (label, "replayed record fails to verify")


@pytest.mark.slow
def test_r3_replay_tfp_pinned(tmp_path):
    """Replay the baseline (31,1) instance into tmp_path; byte-identical to committed."""
    target = _find_seed(_committed_records(), 31, 1)
    corpus = tmp_path / "tfp_replay.json"
    baseline.run_instance(31, 1, str(corpus))
    assert str(corpus) != str(paths.CORPUS), "R3 must never touch the repo corpus"
    _assert_replay(_last_stored(corpus), target, "tfp(31,1)")


@pytest.mark.slow
def test_r3_replay_cayley_pinned(tmp_path):
    """Replay the Cayley (p=31, s=5310) instance into tmp_path; byte-identical to committed."""
    target = _find_cayley(_committed_records(), 31, 5310)
    corpus = tmp_path / "cayley_replay.json"
    cayley_run.run_instance(31, 5310, str(corpus))
    assert str(corpus) != str(paths.CORPUS), "R3 must never touch the repo corpus"
    _assert_replay(_last_stored(corpus), target, "cayley(31,5310)")
