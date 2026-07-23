"""Single source of repo-relative paths (replaces the sandbox /mnt/... path).

Every absolute/output path in the toolkit resolves through this module; no other
module in src/alpha2 may embed a filesystem path. The repo root is discovered
from this file's location (src/alpha2/paths.py -> repo root is three parents up).
"""
from pathlib import Path

# src/alpha2/paths.py -> parents[0]=alpha2, [1]=src, [2]=repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

CORPUS = REPO_ROOT / "data" / "corpus" / "hadwiger_alpha2_certificates.json"

# Dedicated append-only CDM corpus (POOL-0, Phase 7). A SEPARATE file from the
# frozen 296-instance had_2 CORPUS above, which stays byte-untouched: CDM
# certificates carry a different record shape (a connected dominating matching
# witness, not a K_chi branch-set family) and their own stdlib-only verifier leg.
# Same REPO_ROOT / "data" / "corpus" / ... shape; `ensure_parent` generalizes over
# any path. Sole path authority — no other module embeds this literal.
CDM_CORPUS = REPO_ROOT / "data" / "corpus" / "cdm_certificates.json"

# Append-only battery results log (CLI-02) — a SEPARATE contract from the corpus:
# the corpus is the hash-chained FACT authority; this is the event stream (every
# terminal state + method + reason). Same REPO_ROOT / "data" / ... shape as CORPUS;
# `ensure_parent` already generalizes over any path. Sole path authority — no other
# module embeds this literal.
RESULTS_LOG = REPO_ROOT / "data" / "results" / "battery_results.jsonl"

# --- Phase 8 (P1 & P2) additive paths — beside CDM_CORPUS, NOT touching the frozen
# 296-instance CORPUS above (which stays byte-untouched: a different record shape and
# its own stdlib-only verifier leg). Each is the SOLE authority for its literal. ---

# Append-only g(G) = (chi - had_k)/chi certificate corpus for the sum-free Cayley
# break-hunt (POOL-2). A SEPARATE file from CORPUS/CDM_CORPUS: its records carry a
# g(G)-screen shape (invariant_factors + S provenance, chi/had_k, computed g,
# terminal_state, certificate_statement) and their own verify-at-append leg.
SUMFREE_CORPUS = REPO_ROOT / "data" / "corpus" / "sumfree_gscreen_certificates.json"

# Append-only P1 large-n showpiece existence-certificate corpus (POOL-1): heuristic
# HIT -> trust-root-verified K_chi models at n≈1001–2001 (existence-only, never exact).
P1_SHOWPIECE_CORPUS = REPO_ROOT / "data" / "corpus" / "p1_showpiece_certificates.json"

# Append-only aggregate sweep event stream (the g-vs-|Gamma| plot data): one row per
# adjudicated instance (|Gamma|, structured/random tag, g, terminal_state). A SEPARATE
# contract from SUMFREE_CORPUS — an event stream, not the hash-chained FACT authority.
SUMFREE_SWEEP = REPO_ROOT / "data" / "results" / "sumfree_sweep.jsonl"

# Phase 8 (P2) — the empirical ILP optimality-proof frontier (RESEARCH open-Q A4). Two
# SEPARATE data/results/ artifacts (measured/derived data, NEVER the hash-chained corpus):
#   * SUMFREE_FRONTIER_TABLE  — append-only per-(n, kind) PROVED/UNPROVED measurement rows
#     under a deterministic (det_time, det_nodes) budget on BOTH co-equal backends.
#   * SUMFREE_FRONTIER_REPORT — the compact DERIVED report (per-n booleans + the frontier_n
#     boundary + the det budgets + solver versions) the 08-06 grid sweep reads via
#     `exact_window_max` to route a non-packing instance to an exact g>0 verdict (n ≤ window)
#     or the RESISTANT E3 queue (n > window). The authoritative report is regenerated on the
#     shared box (08-06), never on a dev machine — the frontier is a function of (n, budget).
SUMFREE_FRONTIER_TABLE = REPO_ROOT / "data" / "results" / "sumfree_frontier_table.jsonl"
SUMFREE_FRONTIER_REPORT = REPO_ROOT / "data" / "results" / "sumfree_frontier.json"


def ensure_parent(path=CORPUS):
    """Ensure the parent directory of ``path`` exists; return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
