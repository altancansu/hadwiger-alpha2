"""CR-01 regression: `freeze(path=...)` must honor the caller's path END-TO-END.

Historical bug: `baseline.main()` ignored the caller's path — it hardcoded
`paths.CORPUS` and unconditionally `os.remove()`d it, so `freeze(path=<tmp>)`
would have DESTROYED the committed 296-record corpus while leaving the caller's
path short by baseline's 14 records.

These tests stub the four drivers (no solver runs, no corpus regeneration) and
prove: (a) every driver — baseline included — receives the caller's path, and
(b) the real `paths.CORPUS` bytes are never touched when a non-default path is
passed. The frozen corpus artifact stays byte-identical throughout.
"""
import json

from alpha2 import paths
from alpha2.repro import baseline, freeze


def _fake_driver(family, count):
    """Return a stub driver main(path=...) appending `count` minimal records."""
    def main(path=None):
        assert path is not None, "freeze() must thread an explicit path to every driver"
        with open(path) as fh:
            corpus = json.load(fh)
        corpus.extend({"provenance": {"family": family}} for _ in range(count))
        with open(path, "w") as fh:
            json.dump(corpus, fh)
    return main


def test_freeze_threads_path_to_all_four_drivers(tmp_path, monkeypatch):
    """freeze(path=tmp) sends the SAME tmp path to baseline/sweep/cayley/seed137."""
    seen = []

    def record(name, inner):
        def main(path=None):
            seen.append((name, path))
            inner(path=path)
        return main

    monkeypatch.setattr(
        freeze.baseline, "main",
        record("baseline", _fake_driver("triangle_free_process_complement", 14)))
    monkeypatch.setattr(
        freeze.sweep, "main",
        record("sweep", _fake_driver("triangle_free_process_complement", 269)))
    monkeypatch.setattr(
        freeze.cayley_run, "main",
        record("cayley_run", _fake_driver("cayley_maximal_sumfree_Zp", 12)))
    monkeypatch.setattr(
        freeze.seed137, "main",
        record("seed137", _fake_driver("triangle_free_process_complement", 1)))

    real_corpus_bytes = paths.CORPUS.read_bytes()
    target = tmp_path / "scratch_corpus.json"

    corpus = freeze.freeze(path=target)

    assert [name for name, _ in seen] == ["baseline", "sweep", "cayley_run", "seed137"]
    assert all(str(p) == str(target) for _, p in seen), seen
    assert len(corpus) == 296
    # The committed trust anchor must be byte-untouched by a non-default freeze.
    assert paths.CORPUS.read_bytes() == real_corpus_bytes


def test_baseline_main_honors_caller_path(tmp_path, monkeypatch):
    """baseline.main(path=tmp) empties/writes ONLY tmp, never paths.CORPUS."""
    calls = []
    monkeypatch.setattr(
        baseline, "run_instance",
        lambda n, seed, path: calls.append((n, seed, path)))

    real_corpus_bytes = paths.CORPUS.read_bytes()
    target = tmp_path / "scratch_baseline.json"
    target.write_text("[]")  # pre-existing file: main() must remove THIS one

    baseline.main(path=target)

    assert len(calls) == 14
    assert all(str(p) == str(target) for _, _, p in calls), calls
    assert not target.exists()  # emptied (removed) the CALLER's path, not CORPUS
    assert paths.CORPUS.read_bytes() == real_corpus_bytes
