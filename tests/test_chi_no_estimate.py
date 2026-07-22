"""CHI-01 static guard: chi is computed ONLY as n - matching_number, never estimated.

This guard tests the MECHANISM, not merely prose. Wave 1 already reworded docstrings to
remove trigger tokens, so a bare word-grep would be weak/circular. Instead we parse every
`src/alpha2/**/*.py` with `ast` (which discards comments and lets us skip docstrings) and
assert the real invariant on ACTUAL call/import nodes:

  1. No chromatic-estimate call is ever invoked in src/ control flow (no greedy_color /
     coloring / chromatic / *estimate* Call target anywhere).
  2. No coloring/approximation/chromatic module is imported.
  3. The networkx API surface in src/ is confined to a matching-only allow-list; the only
     matching call is `max_weight_matching(..., maxcardinality=True)`.
  4. Positively: invariants/matching.py is the SOLE chi path and it uses
     max_weight_matching(maxcardinality=True) with no coloring import.

Because the scan is over AST Call/Import nodes (not source text), comment prose such as
"# ---------- exact chromatic number ..." cannot trip OR mask the gate (T-01-06 / T-01-07).
"""
import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "alpha2"

# Substrings that, if they appear in an actually-CALLED function name, indicate a chromatic
# estimate/coloring mechanism. Matched against Call targets only (never comments/docstrings).
BANNED_CALL_SUBSTRINGS = ("color", "chromatic", "estimate")

# Module path fragments whose import would pull in a coloring/approximation estimator.
BANNED_IMPORT_SUBSTRINGS = ("color", "chromatic", "approximation")

# The only networkx attribute calls permitted anywhere in src/ (matching-confined surface).
ALLOWED_NX_ATTRS = {"Graph", "add_nodes_from", "add_edges_from", "max_weight_matching"}


def _src_files():
    files = sorted(SRC_ROOT.rglob("*.py"))
    assert files, f"no source files under {SRC_ROOT}"
    return files


def _call_target_name(node):
    """Return the called function's simple name (Name.id or Attribute.attr), else None."""
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _networkx_aliases(tree):
    """Names bound to the networkx module in this file (e.g. `import networkx as nx`)."""
    aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "networkx" or a.name.startswith("networkx."):
                    aliases.add(a.asname or a.name.split(".")[0])
    return aliases


def test_chi_no_estimate():
    matching_has_blossom = False

    for path in _src_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        nx_aliases = _networkx_aliases(tree)

        # (2) No coloring/approximation/chromatic import anywhere.
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                assert not any(b in mod for b in BANNED_IMPORT_SUBSTRINGS), \
                    f"{path}: forbidden import from {node.module}"
                for a in node.names:
                    assert not any(b in a.name.lower() for b in BANNED_IMPORT_SUBSTRINGS), \
                        f"{path}: forbidden import name {a.name}"
            elif isinstance(node, ast.Import):
                for a in node.names:
                    assert not any(b in a.name.lower() for b in BANNED_IMPORT_SUBSTRINGS), \
                        f"{path}: forbidden import module {a.name}"

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_target_name(node)
            if name is None:
                continue
            lname = name.lower()

            # (1) No chromatic-estimate call is ever invoked.
            assert not any(sub in lname for sub in BANNED_CALL_SUBSTRINGS), \
                f"{path}: forbidden chromatic-estimate call `{name}`"

            # (3) networkx API surface confinement: any nx.<attr>(...) call must be allow-listed.
            f = node.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) \
                    and f.value.id in nx_aliases:
                assert f.value.id + "." + f.attr in {f.value.id + "." + a for a in ALLOWED_NX_ATTRS}, \
                    f"{path}: networkx call `{f.value.id}.{f.attr}` outside the matching allow-list"

            # (4) Positive: confirm the exact blossom matching call with maxcardinality=True.
            if name == "max_weight_matching":
                # matching must be confined to invariants/matching.py
                assert path.name == "matching.py" and path.parent.name == "invariants", \
                    f"{path}: max_weight_matching must live only in invariants/matching.py"
                kws = {k.arg: k.value for k in node.keywords}
                assert "maxcardinality" in kws, f"{path}: max_weight_matching missing maxcardinality"
                mc = kws["maxcardinality"]
                assert isinstance(mc, ast.Constant) and mc.value is True, \
                    f"{path}: maxcardinality must be the literal True (exact maximum matching)"
                matching_has_blossom = True

    # The sole chi path (n - nu via Edmonds blossom) must actually exist.
    assert matching_has_blossom, \
        "no max_weight_matching(maxcardinality=True) found — the exact chi path is missing"
