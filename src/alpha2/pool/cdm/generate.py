"""MTF generation driver (POOL-0 SC1) — the frontier-count backbone.

`stream_mtf(n, res, mod)` shells out to the nauty C pipe

    geng -ctq n [res/mod] | pickg -Z2

and yields the graph6 lines of the **maximal-triangle-free** graphs H on n
vertices (connected + diameter-2 ⟺ edge-maximal-triangle-free; their complements
Ḡ are the edge-minimal α=2 graphs the transfer lemma reduces the frontier to).
This is the ONLY correct generation route: pynauty has no `geng` binding (verified,
STACK Blueprint 1), so generation is always a subprocess.

The exact survivor counts are the external anchor — **OEIS A216783**:

    n    | 12  | 13  | 14
    -----+-----+-----+------
    MTF  | 147 | 392 | 1,274

A wrong flag, a dropped shard, or a mis-set res/mod silently yields ≠ the true
count (RESEARCH Pitfall 3), so the tests pin the exact triple against A216783.

Discipline
----------
* The C filter (`pickg -Z2`) stays IN the pipe: Python never enumerates the
  10⁶–10⁸ triangle-free pre-images (CLAUDE.md anti-pattern — `is_edge_maximal_tf`
  over the full raw stream timed out at n=13 on 20.8M graphs). Python only ever
  sees the ~10³ survivors.
* Security (T-7-gen / T-7-08): every numeric subprocess arg (n, res, mod) is
  int-validated and bounded BEFORE any string interpolation; `subprocess.Popen`
  is called with ARG LISTS only — the shell is never invoked (no shell string).
* Determinism (07-PATTERNS.md): geng emits in a deterministic canonical order and
  this module's streaming path introduces NO set-iteration-dependent ordering, so
  generate.py stays OUT of `[tool.ruff] extend-exclude`.

stdlib + `alpha2.corpus.schema` only (no networkx / ortools import here).
"""
import functools
import subprocess
from collections.abc import Iterator

from alpha2.corpus.schema import provenance_graph6

# The pipe flags, recorded verbatim into every instance's provenance sidecar.
FLAGS = "-ctq | pickg -Z2"

# DoS bound (T-7-08): the phase budget is n≤14 with a stretch to n=17. `geng` at
# larger n is an unbounded C enumeration; we validate-and-cap rather than spawn it.
N_MIN = 1
N_MAX = 17


def geng_version():
    """First non-empty line of `geng --help` — a stable nauty-provenance stamp.

    Returns None when `geng` is not on PATH (so provenance capture degrades
    gracefully rather than raising in a non-nauty environment). Cached: the value
    is constant for a given install, so it is never re-spawned in the stream loop.
    """
    return _geng_version_cached()


@functools.cache
def _geng_version_cached():
    try:
        proc = subprocess.run(
            ["geng", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    for stream in (proc.stdout, proc.stderr):
        for line in stream.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return None


def _validate(n, res, mod):
    """Int-validate + bound n/res/mod BEFORE any interpolation (T-7-gen control).

    Raises ValueError on any non-int, out-of-range, or inconsistent shard spec.
    `bool` is rejected explicitly (it is an int subclass) so `stream_mtf(True)`
    cannot slip a `1` past the type gate.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"n must be an int, got {type(n).__name__}")
    if not (N_MIN <= n <= N_MAX):
        raise ValueError(f"n={n} out of bounds [{N_MIN}, {N_MAX}] (DoS cap T-7-08)")

    # Sharding is all-or-nothing: res and mod must be provided together.
    if (res is None) != (mod is None):
        raise ValueError("res and mod must be provided together (or both omitted)")
    if mod is None:
        return None

    if isinstance(mod, bool) or not isinstance(mod, int):
        raise ValueError(f"mod must be an int, got {type(mod).__name__}")
    if mod < 1:
        raise ValueError(f"mod={mod} must be a positive int")
    if isinstance(res, bool) or not isinstance(res, int):
        raise ValueError(f"res must be an int, got {type(res).__name__}")
    if not (0 <= res < mod):
        raise ValueError(f"res={res} out of range [0, {mod}) for mod={mod}")

    # Only NOW — after full validation — build the interpolated shard token.
    return f"{res}/{mod}"


def stream_mtf(n, res=None, mod=None) -> Iterator[tuple[int, str, "str | None"]]:
    """Yield (index, graph6, shard) for each MTF graph on n vertices.

    Streams `geng -ctq n [res/mod] | pickg -Z2` and yields one tuple per non-empty
    graph6 line, with a monotonically increasing 0-based `index`. `shard` is the
    "res/mod" token when sharded, else None. When res/mod is set, only the geng
    subset res-of-mod is generated (the shards partition the survivor set; their
    union over res∈0..mod-1 equals the single stream — the sharding-sum identity).

    Injection-safe (arg lists, no shell) and DoS-bounded (n≤17); inputs are fully
    int-validated before any subprocess is spawned.
    """
    shard = _validate(n, res, mod)

    geng_cmd = ["geng", "-ctq", str(n)]
    if shard is not None:
        geng_cmd.append(shard)

    p1 = subprocess.Popen(geng_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    p2 = subprocess.Popen(
        ["pickg", "-Z2"],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    # Close our copy of geng's write end so pickg sees EOF when geng exits.
    p1.stdout.close()

    index = 0
    try:
        for line in p2.stdout:
            g6 = line.strip()
            if not g6:
                continue
            yield (index, g6, shard)
            index += 1
    finally:
        p2.stdout.close()
        p1.wait()
        p2.wait()


# --------------------------------------------------------------------------- #
# Generation cross-checks (POOL-0 SC1) — the ratified v1 anti-drift surface
# (07-04 Q3 → ratify-v1): OEIS A216783 exact counts + an INDEPENDENT second-filter
# predicate (`generators.tfp.is_edge_maximal_tf`) + the sharding-sum identity. A
# fully independent MTF *generator* (triangleramsey/Goedgebeur) is DEFERRED to
# milestone-2 / n≈16; for n≤14 these three guards already catch generation drift
# (RESEARCH Pitfall 3). `shortg` is the canonical-set deduper used ONLY when a
# SECOND generator stream is merged — geng's single stream is already isomorph-free
# (McKay canonical augmentation), so NO non-canonical (hash-based) dedup is ever
# applied here; only canonical `shortg` would be, and only across merged streams.
# --------------------------------------------------------------------------- #
def count_mtf(n, res=None, mod=None):
    """Survivor count for a (possibly sharded) MTF stream.

    Used by the sharding-sum identity (Pitfall 3): for any mod,
    ``count_mtf(n) == sum(count_mtf(n, r, mod) for r in range(mod))`` — a dropped
    or duplicated shard breaks this equality. E.g. count_mtf(12) == 147.
    """
    return sum(1 for _ in stream_mtf(n, res, mod))


def _graph6_to_adj(graph6):
    """Decode a graph6 string to (adj: list[set[int]], n) — stdlib, no networkx.

    A ~15-line local decoder (STACK Blueprint 1) so the cross-check touches no
    heavyweight `nx.Graph`. Handles n≤62 (single header byte), which covers the
    whole phase budget (n≤17). Bit order is graph6's column-major upper triangle:
    (0,1),(0,2),(1,2),(0,3),… — matching `networkx.from_graph6_bytes`.
    """
    data = [ord(c) - 63 for c in graph6]
    n = data[0]
    bits = []
    for byte in data[1:]:
        for k in range(5, -1, -1):
            bits.append((byte >> k) & 1)
    adj = [set() for _ in range(n)]
    idx = 0
    for j in range(1, n):
        for i in range(j):
            if bits[idx]:
                adj[i].add(j)
                adj[j].add(i)
            idx += 1
    return adj, n


def is_survivor_edge_maximal(graph6):
    """Second-route cross-check: is this `pickg -Z2` survivor edge-maximal-tf?

    Runs the repo's INDEPENDENT Python predicate `is_edge_maximal_tf`
    (add-any-edge-closes-a-triangle ⟺ diameter 2) over the decoded survivor. nauty's
    C diameter filter and this Python edge-maximality filter must agree on the whole
    survivor set (Lemma 2.5 / OEIS A216783). This is the ratified-v1 "second route"
    — a FILTER cross-check, NOT a second generator. Never run it over the raw
    triangle-free stream (CLAUDE.md anti-pattern: timed out at n=13); apply it only
    to the ~10³ survivors `stream_mtf` yields.
    """
    from alpha2.generators.tfp import is_edge_maximal_tf

    adj, n = _graph6_to_adj(graph6)
    return is_edge_maximal_tf(adj, n)


def provenance_for(n, graph6, shard, index):
    """schema-v1 graph6 provenance for one MTF instance + a params sidecar.

    Reuses `alpha2.corpus.schema.provenance_graph6` (family="mtf_complement") and
    attaches the generation params `{geng_version, flags, shard, index}` so every
    yielded instance carries a full, replayable audit trail.
    """
    prov = provenance_graph6(family="mtf_complement", n=n, graph6=graph6)
    prov["params"] = {
        "geng_version": geng_version(),
        "flags": FLAGS,
        "shard": shard,
        "index": index,
    }
    return prov
