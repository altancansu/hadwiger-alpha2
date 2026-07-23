"""RNG contract v2 — sha256 per-stage subseeds (POOL-1/2, stdlib ONLY).

ROADMAP SC3 / RESEARCH Pattern 2: derive an independent subseed per pipeline stage
from a single master seed, so changing one stage's stream never shifts another's.

    subseed(master, stage) = int.from_bytes(sha256(f"{master}:{stage}")[:8], "big")

Each stage is hashed independently from the master, so the "sumfree-generate" and
"heuristic-search" subseeds are stage-independent (re-deriving one cannot move the
other) and stable across runs/platforms (sha256 is not set-iteration dependent).

`gen_rng` / `search_rng` are thin `random.Random` factories over the two canonical
stages. Reproducibility rests on the STORED descriptor (invariant_factors, S), never
on replaying these RNG streams (cross-platform set-iteration safety) — the streams
only drive the initial random-greedy construction.

No new dependency — stdlib `hashlib` + `random` only.
"""
import hashlib
import random

# The two canonical pipeline stages (LOCKED stage labels — changing a label
# re-buckets its subseed, so these strings are part of the reproducibility contract).
_STAGE_GENERATE = "sumfree-generate"
_STAGE_SEARCH = "heuristic-search"


def subseed(master: int, stage: str) -> int:
    """Per-stage subseed: first 8 bytes of sha256(f"{master}:{stage}"), big-endian.

    Stable and stage-independent (RESEARCH Pattern 2). sha256 is used purely as a
    deterministic seed derivation here — NOT as a security control (V6 n/a).
    """
    digest = hashlib.sha256(f"{master}:{stage}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def gen_rng(seed: int) -> random.Random:
    """`random.Random` seeded on the 'sumfree-generate' subseed (random-greedy S)."""
    return random.Random(subseed(seed, _STAGE_GENERATE))


def search_rng(seed: int) -> random.Random:
    """`random.Random` seeded on the 'heuristic-search' subseed (heuristic solve)."""
    return random.Random(subseed(seed, _STAGE_SEARCH))
