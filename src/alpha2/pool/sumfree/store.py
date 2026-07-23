"""Append-only, crash-safe, verify-at-append g(G)-screen certificate writer (POOL-2).

The DEDICATED sum-free g(G) corpus (`paths.SUMFREE_CORPUS`) is strictly isolated from
the frozen 296-instance had_2 corpus AND from the CDM corpus: a SEPARATE file, a
SEPARATE stdlib verifier leg (`verify_gscreen`), and its own per-record hash chain.
This module imports and touches NOTHING of the frozen 296-instance writer/verifier
legs, the CDM store, or their default paths.

`append_gscreen_certificate` enforces three guarantees (cloning the CDM store's
mechanics, swapping in the sum-free leg + default path):

  1. Verify-at-append gate — EVERY append re-checks the incoming record through the
     stdlib sum-free trust root (`verify_gscreen`) AND requires `verified is True`.
     A record that does not pass the leg never reaches the filesystem.

  2. Append-only prefix-immutability — before writing, every already-stored record is
     re-verified via `verify_gscreen` (recomputes + compares its H_edges_sha256,
     re-derives chi and the K_chi model) AND against a per-record HASH CHAIN
     recomputed from record 0. A tampered or substituted prior record makes the
     append fail closed. A byte-compare of the new array's prefix guards accidental
     reorder/drop in the append itself.

  3. Atomic write — the array is serialized to a tempfile in the SAME directory,
     flushed + os.fsync'd, then os.replace'd over the target (an atomic
     same-filesystem swap). A reader or a crash sees the old or new file, never a
     torn one; the temp file is unlinked on any failure.

stdlib ONLY (json, os, tempfile) + the sum-free verifier/schema legs and the path
module.
"""
import json
import os
import tempfile

from alpha2 import paths
from alpha2.pool.sumfree.schema import CHAIN_FIELD, chain_hash
from alpha2.pool.sumfree.verifier import VerificationError, verify_gscreen


def _verify_chain(old):
    """Recompute the per-record hash chain from record 0 and RAISE on any mismatch.

    A stored record missing its chain field, or whose stored chain disagrees with the
    recomputation, indicates out-of-band tamper (a record written or swapped outside
    this writer) and makes the append fail closed.
    """
    prev = ""
    for i, prior in enumerate(old):
        stored = prior.get(CHAIN_FIELD)
        if stored is None:
            raise VerificationError(
                f"append-only violation: existing record {i} is missing its "
                f"{CHAIN_FIELD} (hash-chain link absent -- tamper or out-of-band write)"
            )
        expected = chain_hash(prev, prior)
        if stored != expected:
            raise VerificationError(
                f"append-only violation: existing record {i} hash-chain mismatch "
                f"(stored {stored} != recomputed {expected}) -- prior records are immutable"
            )
        prev = stored
    return prev


def _load(path):
    """Load the current sum-free corpus array, or [] if the file is absent/empty."""
    if os.path.exists(path) and os.path.getsize(path):
        with open(path) as fh:
            return json.load(fh)
    return []


def append_gscreen_certificate(rec, path=None):
    """Append a verified g(G)-screen certificate to the append-only corpus (atomic).

    Default target is `paths.SUMFREE_CORPUS`. Raises VerificationError if the incoming
    record does not pass the sum-free trust leg or is not marked verified, or if any
    already-stored record has been tampered with (append-only prefix-immutability).
    On any write failure the prior file is left intact and no temp file remains.
    """
    if path is None:
        path = paths.ensure_parent(paths.SUMFREE_CORPUS)
    path = os.fspath(path)

    old = _load(path)

    # (2) Append-only prefix-immutability: every prior record must STILL verify
    #     against its own stored integrity. A tampered record fails the re-check.
    for i, prior in enumerate(old):
        try:
            verify_gscreen(prior)
        except VerificationError as exc:
            raise VerificationError(
                f"append-only violation: existing record {i} no longer verifies "
                f"(prior records are immutable): {exc}"
            ) from exc

    # (2a) Hash-chain immutability: recompute the per-record chain from record 0.
    #      Catches a self-consistent record SUBSTITUTION the re-verification cannot.
    prev_chain = _verify_chain(old)

    # (1) Verify-at-append gate: nothing enters unverified (sum-free leg, always).
    verify_gscreen(rec)
    if not rec.get("verified"):
        raise VerificationError("record is not marked verified=True; refusing to append")

    # Stamp the incoming record's chain link (folds in the last stored chain) and
    # append the stamped copy (never mutate the caller's dict).
    stamped = dict(rec)
    stamped[CHAIN_FIELD] = chain_hash(prev_chain, rec)
    new = old + [stamped]

    # (2b) Structural invariant: the new prefix must be byte-identical to the old
    #      array (guards an accidental reorder/drop in the append itself).
    if json.dumps(new[: len(old)], sort_keys=True) != json.dumps(old, sort_keys=True):
        raise VerificationError("append-only violation: existing records changed")

    # (3) Atomic write: tempfile in the same dir -> fsync -> os.replace.
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(new, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
