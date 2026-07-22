"""Append-only JSONL results log (CLI-02) — stdlib ONLY, atomic, path from paths.py.

The results log is the battery's EVENT stream: one JSON object per line, one line per
runbook step outcome (terminal state + method + certificate ref + reason + seed/provenance
+ per-step budgets). It is a deliberately SIMPLER contract than the corpus
(`corpus/store.py`): no hash-chain, no verifier gate — the hash-chained corpus remains the
sole FACT authority (RESEARCH Pattern 4). What it shares with the store is the discipline
that matters here: the path comes ONLY from `paths.RESULTS_LOG` (never a filesystem literal),
and each append is atomic (read → append one line → tempfile → flush → fsync → os.replace),
so a reader or a crash sees the old file or the new file, never a torn line.

Append-only by construction: `append_event` only ever REWRITES the file as
`existing_bytes + json.dumps(event) + "\\n"`; it never truncates, edits, or reorders a prior
line. Every guard RAISES (no `assert`; survives ``python -O``).
"""
import json
import os
import tempfile

from alpha2 import paths


def append_event(event, path=None):
    """Append one JSON event as a new JSONL line (atomic; append-only).

    `event` must be a JSON-serializable dict. When `path` is None it resolves from
    `paths.ensure_parent(paths.RESULTS_LOG)` (the sole path authority); a caller-supplied
    path (e.g. a test tempfile) is honored end-to-end. Returns the resolved path.
    """
    if not isinstance(event, dict):
        raise TypeError(f"event must be a dict, got {type(event).__name__}")
    if path is None:
        path = paths.ensure_parent(paths.RESULTS_LOG)
    path = os.fspath(path)

    # json.dumps here (before any file write) so a non-serializable event fails BEFORE
    # the file is touched — a bad event never produces a torn or partial line.
    line = json.dumps(event, sort_keys=True) + "\n"

    existing = b""
    if os.path.exists(path) and os.path.getsize(path):
        with open(path, "rb") as fh:
            existing = fh.read()

    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(existing)
            fh.write(line.encode())
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path
