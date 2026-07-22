"""Golden-hash manifest builder for the frozen 296-instance corpus (R2 anchor).

Reads the frozen schema-v1 corpus (`paths.CORPUS`) and freezes a compact
golden-hash manifest keyed by the A5 scheme:

  * triangle-free-process complements -> ``tfp:n{n}:s{seed}``
  * sum-free Cayley Z_p complements    -> ``cayley:p{n}:s{seed}``

Each value is ``{"m", "nu", "chi", "h_edges_sha256"}`` where ``m`` is
``num_H_edges`` and the hash is produced by the FROZEN verifier convention
``schema.h_edges_sha256`` (json.dumps of sorted [min,max] pairs, then sha256) — the
exact bytes ``verifier.verify_model_record`` recomputes. NO hand-rolled sha256: a
second hashing routine would be a common-mode integrity gap (T-3-01).

The manifest is the R2 determinism anchor: R2 regenerates H from the seed, hashes it
via the same convention, and compares to the frozen value here. It is additive — the
2-entry ``data/manifests/fingerprint.json`` (ENV-03 exemplar) stays untouched.

Run:  python -m alpha2.corpus.manifest   (freezes data/manifests/corpus-v1.manifest.json)

stdlib ONLY (json) + schema (stdlib-only). No networkx / generators imports.
"""
import json

from alpha2 import paths
from alpha2.corpus import schema

# The full golden manifest lives beside the ENV-03 fingerprint exemplar (additive).
MANIFEST_PATH = paths.REPO_ROOT / "data" / "manifests" / "corpus-v1.manifest.json"

# Family -> A5 key prefix + node-dimension letter. TFP keys read tfp:n{n}:s{seed};
# Cayley keys read cayley:p{n}:s{seed} (n == p for Cayley Z_p).
_FAMILY_KEY = {
    "triangle_free_process_complement": ("tfp", "n"),
    "cayley_maximal_sumfree_Zp": ("cayley", "p"),
}


def manifest_key(record):
    """A5 manifest key for a stored record: tfp:n{n}:s{seed} / cayley:p{n}:s{seed}."""
    fam = record["provenance"]["family"]
    if fam not in _FAMILY_KEY:
        raise ValueError(f"no manifest key scheme for family {fam!r}")
    prefix, dim = _FAMILY_KEY[fam]
    n = record["invariants"]["n"]
    seed = record["provenance"]["seed"]
    return f"{prefix}:{dim}{n}:s{seed}"


def build_manifest(records):
    """Build the golden-hash manifest dict from stored schema-v1 records.

    Hashes each record's stored ``H_edges`` via the frozen ``schema.h_edges_sha256``
    convention and asserts it AGREES with the record's own ``H_edges_sha256`` field
    (same frozen convention — divergence is a tamper/drift signal, T-3-01). Refuses a
    duplicate key so the 296 accounting cannot silently collapse two instances.
    """
    manifest = {}
    for rec in records:
        key = manifest_key(rec)
        if key in manifest:
            raise ValueError(f"duplicate manifest key {key!r} — corpus accounting broken")
        inv = rec["invariants"]
        h = schema.h_edges_sha256(rec["H_edges"])
        stored = rec["H_edges_sha256"]
        if h != stored:
            raise ValueError(
                f"{key}: recomputed h_edges_sha256 {h} != stored {stored} "
                "(hashing convention divergence — T-3-01)"
            )
        manifest[key] = {
            "m": inv["num_H_edges"],
            "nu": inv["nu_H"],
            "chi": inv["chi_G"],
            "h_edges_sha256": h,
        }
    return manifest


def freeze(path=None, corpus_path=None):
    """Load the corpus, build the manifest, assert 296 entries, write the frozen file.

    Writes stable (sort_keys) pretty JSON mirroring ``fingerprint.json`` so the
    committed golden manifest is diff-friendly and byte-stable across regenerations.
    """
    if path is None:
        path = MANIFEST_PATH
    if corpus_path is None:
        corpus_path = paths.CORPUS
    with open(corpus_path) as fh:
        records = json.load(fh)
    manifest = build_manifest(records)
    if len(manifest) != 296:
        raise ValueError(f"manifest has {len(manifest)} entries, expected 296")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


def main():
    manifest = freeze()
    prefixes = {}
    for k in manifest:
        p = k.split(":", 1)[0]
        prefixes[p] = prefixes.get(p, 0) + 1
    print(f"FROZEN: {len(manifest)} golden-hash entries -> {MANIFEST_PATH}")
    print(f"        by prefix: {prefixes}")


if __name__ == "__main__":
    main()
