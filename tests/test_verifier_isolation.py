"""Import-boundary + zero-assert AST guard for the trust root (VRF-01).

The verifier is the trust root: it must share NO logic with any proposer and must
be correct under `python -O`. This guard tests the MECHANISM (AST nodes), not prose:

  1. Every import in corpus/verifier.py targets a stdlib allow-list module.
  2. No import mentions alpha2.search / generators / verify / invariants / solver /
     networkx (the trust-boundary leak, Pitfall 2).
  3. ZERO ast.Assert nodes (asserts vanish under -O -> rubber stamp, Pitfall 1).
  4. At least 6 `raise VerificationError(...)` statements (real checks, not asserts).

Follows the Phase-1 CHI-01 AST-guard pattern (test_chi_no_estimate.py).
"""
import ast
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[1] / "src" / "alpha2" / "corpus" / "verifier.py"

STDLIB_ALLOW = {
    "json", "hashlib", "os", "sys", "collections", "itertools", "dataclasses", "platform",
}
FORBIDDEN_SUBSTRINGS = (
    "alpha2.search", "alpha2.generators", "alpha2.verify", "alpha2.invariants",
    "solver", "networkx",
)


def _tree():
    return ast.parse(VERIFIER.read_text(), filename=str(VERIFIER))


def test_verifier_imports_stdlib_only():
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                assert top in STDLIB_ALLOW, f"non-stdlib import {a.name!r}"
                assert not any(s in a.name for s in FORBIDDEN_SUBSTRINGS), \
                    f"trust-boundary leak: {a.name!r}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            top = mod.split(".")[0]
            assert top in STDLIB_ALLOW, f"non-stdlib from-import {mod!r}"
            assert not any(s in mod for s in FORBIDDEN_SUBSTRINGS), \
                f"trust-boundary leak: from {mod!r}"
            for a in node.names:
                assert not any(s in a.name for s in FORBIDDEN_SUBSTRINGS), \
                    f"trust-boundary leak: {a.name!r}"


def test_verifier_has_zero_asserts():
    tree = _tree()
    asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    assert not asserts, f"verifier must contain ZERO assert statements, found {len(asserts)}"


def test_verifier_raises_verification_error_at_least_6():
    tree = _tree()
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            fn = exc.func if isinstance(exc, ast.Call) else exc
            name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
            if name == "VerificationError":
                count += 1
    assert count >= 6, f"expected >=6 raise VerificationError, found {count}"
