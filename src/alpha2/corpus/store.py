"""Append-only, crash-safe, verify-at-append corpus store (VRF-02).

The corpus is the program's falsification anchor: it must be impossible to corrupt
(crash mid-write) or to silently mutate (edit/reorder a prior record), and NOTHING
may enter it unverified. `append_certificate` enforces all three:

  1. Verify-at-append gate — EVERY append calls the combined `verify_certificate`
     (BOTH `verify_model_record` AND `verify_chi_witness`) on the incoming record
     and requires `verified is True`. There is no `has_witness` opt-out: a record
     that does not pass the stdlib-only trust root never reaches the filesystem.

  2. Append-only prefix-immutability — before writing, every already-stored record
     is re-verified against its OWN frozen H_edges_sha256 (verify_model_record
     recomputes and compares it) AND against a per-record HASH CHAIN. Each stored
     record carries `chain_sha256 = sha256(prev_chain_sha256 || canonical_json(
     record_without_chain_field))` (genesis prev = ""). On append the chain is
     recomputed from record 0; if any stored chain disagrees the append is refused.
     This makes a self-consistent record SUBSTITUTION detectable: swapping a prior
     record for a different-but-individually-valid cert changes its body, so its
     recomputed chain diverges and cascades to break every later record's chain.

     Honest guarantee (do NOT overclaim): the chain detects PARTIAL / out-of-band
     tamper (editing, reordering, dropping, or substituting a subset of records)
     because such a change is not reflected forward through the rest of the chain.
     It does NOT by itself defeat a fully-recomputed rewrite of the ENTIRE corpus
     file (an attacker who rewrites every record and every chain link produces an
     internally-consistent chain). That worst case is bounded EXTERNALLY by the
     git-committed corpus history, which is the actual immutability anchor for a
     wholesale rewrite. A structural byte-compare of the new array's prefix against
     the loaded prefix additionally guards accidental reorder/drop. Existing records
     are IMMUTABLE — instance status (KILLED/RESISTANT) is a DERIVED view (VRF-03,
     Phase 6), never a stored-record edit.

  3. Atomic write — the array is serialized to a tempfile in the SAME directory,
     flushed + os.fsync'd, then os.replace'd over the target (an atomic
     same-filesystem swap). A reader or a crash sees the old file or the new file,
     never a torn one; the temp file is unlinked on any failure.

stdlib ONLY (json, os, tempfile) + the trust root and the path module.
"""
import json
import os
import tempfile

from alpha2 import paths
from alpha2.corpus.schema import CHAIN_FIELD, chain_hash
from alpha2.corpus.verifier import (
    VerificationError,
    verify_certificate,
)


def _verify_chain(old):
    """Recompute the per-record hash chain from record 0 and RAISE on any mismatch.

    A stored record missing its chain field, or whose stored chain disagrees with
    the recomputation, indicates out-of-band tamper (a record written or swapped
    outside append_certificate) and makes the append fail closed.
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
    """Load the current corpus array, or [] if the file is absent/empty."""
    if os.path.exists(path) and os.path.getsize(path):
        with open(path) as fh:
            return json.load(fh)
    return []


def append_certificate(rec, path=None):
    """Append a verified certificate to the append-only corpus (atomic write).

    Raises VerificationError if the incoming record does not pass the trust root
    or is not marked verified, or if any already-stored record has been tampered
    with (append-only prefix-immutability). On any write failure the prior file is
    left intact and no temp file remains.
    """
    if path is None:
        path = paths.ensure_parent(paths.CORPUS)
    path = os.fspath(path)

    old = _load(path)

    # (2) Append-only prefix-immutability: every prior record must STILL verify
    #     against its own stored integrity. A tampered record fails the re-check.
    for i, prior in enumerate(old):
        try:
            verify_certificate(prior)
        except VerificationError as exc:
            raise VerificationError(
                f"append-only violation: existing record {i} no longer verifies "
                f"(prior records are immutable): {exc}"
            ) from exc

    # (2a) Hash-chain immutability: recompute the per-record chain from record 0.
    #      This catches a self-consistent record SUBSTITUTION that the per-record
    #      re-verification above cannot (a swapped cert verifies against itself).
    prev_chain = _verify_chain(old)

    # (1) Verify-at-append gate: nothing enters unverified (BOTH legs, always).
    verify_certificate(rec)
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
