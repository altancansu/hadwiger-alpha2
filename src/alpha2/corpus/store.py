"""Append-only, crash-safe, verify-at-append corpus store (VRF-02).

The corpus is the program's falsification anchor: it must be impossible to corrupt
(crash mid-write) or to silently mutate (edit/reorder a prior record), and NOTHING
may enter it unverified. `append_certificate` enforces all three:

  1. Verify-at-append gate — EVERY append calls BOTH `verify_model_record` and
     `verify_chi_witness` on the incoming record and requires `verified is True`.
     There is no `has_witness` opt-out: a record that does not pass the stdlib-only
     trust root never reaches the filesystem.

  2. Append-only prefix-immutability — before writing, every already-stored record
     is re-verified against its OWN frozen H_edges_sha256 (verify_model_record
     recomputes and compares it). Any tampering that alters a prior record's edges,
     model, witness, or integrity hash makes the re-check RAISE, so the append is
     refused. A structural byte-compare of the new array's prefix against the loaded
     prefix additionally guards accidental reorder/drop. Existing records are
     IMMUTABLE — instance status (KILLED/RESISTANT) is a DERIVED view (VRF-03,
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
from alpha2.corpus.verifier import (
    VerificationError,
    verify_chi_witness,
    verify_model_record,
)


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
            verify_model_record(prior)
            verify_chi_witness(prior)
        except VerificationError as exc:
            raise VerificationError(
                f"append-only violation: existing record {i} no longer verifies "
                f"(prior records are immutable): {exc}"
            ) from exc

    # (1) Verify-at-append gate: nothing enters unverified.
    verify_model_record(rec)
    verify_chi_witness(rec)
    if not rec.get("verified"):
        raise VerificationError("record is not marked verified=True; refusing to append")

    new = old + [rec]

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
