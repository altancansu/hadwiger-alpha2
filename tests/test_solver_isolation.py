"""Import-boundary + zero-assert AST guard + -O canary for the solvers package.

The status-honesty guarantee (EXACT-01) is held by raise-based guards in the
solver modules. This file pins the two erosion vectors mechanically — AST
nodes, not prose greps (the CHI-01 / VRF-01 guard pattern):

  1. stdlib boundary: solvers/result.py, solvers/backend.py and
     solvers/problems/had2.py import only allow-listed stdlib modules plus a
     pinned set of first-party targets — they stay importable without pulp.
  2. pulp confinement: across ALL of src/alpha2/, `pulp` is imported (module-
     or function-level) ONLY by solvers/cbc.py — the lazy-import precedent
     that keeps every other module solver-free.
  3. zero ast.Assert across all four solver modules (result, backend,
     problems/had2, cbc) — asserts vanish under -O -> rubber stamp.
  4. `python -O` subprocess canary: NotProvedOptimal and ChecksumError still
     raise with asserts stripped (a real __debug__ branch proves -O is live).
"""
import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOLVERS = REPO / "src" / "alpha2" / "solvers"

RESULT = SOLVERS / "result.py"
BACKEND = SOLVERS / "backend.py"
HAD2 = SOLVERS / "problems" / "had2.py"
CBC = SOLVERS / "cbc.py"

# Modules that must be importable WITHOUT any solver library.
STDLIB_BOUNDARY_MODULES = (RESULT, BACKEND, HAD2)
# All four solver modules: zero ast.Assert nodes.
ALL_SOLVER_MODULES = (RESULT, BACKEND, HAD2, CBC)

STDLIB_ALLOW = {"dataclasses", "enum", "typing", "importlib"}
# First-party imports the stdlib-boundary modules are allowed to make; each
# target is itself stdlib-only (transitively solver-free).
FIRSTPARTY_ALLOW = {
    "alpha2.solvers.result",     # backend.py -> outcome types
    "alpha2.generators.tfp",     # problems/had2.py -> is_triangle_free
}


def _tree(path):
    return ast.parse(path.read_text(), filename=str(path))


def _import_targets(tree):
    """Yield every module name targeted by an Import/ImportFrom node."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


# ---------------------------------------------------------------------------
# Guard 1: stdlib boundary for result/backend/problems.had2
# ---------------------------------------------------------------------------
def test_stdlib_boundary_modules_import_stdlib_or_pinned_firstparty_only():
    for mod in STDLIB_BOUNDARY_MODULES:
        for name in _import_targets(_tree(mod)):
            top = name.split(".")[0]
            if top == "alpha2":
                assert name in FIRSTPARTY_ALLOW, (
                    f"{mod.name}: first-party import {name!r} is not in the "
                    f"pinned allow-list {sorted(FIRSTPARTY_ALLOW)}"
                )
            else:
                assert top in STDLIB_ALLOW, (
                    f"{mod.name}: non-allow-listed import {name!r} — the "
                    "stdlib-boundary modules must stay importable without "
                    "any solver library"
                )


# ---------------------------------------------------------------------------
# Guard 2: pulp confined to solvers/cbc.py across ALL of src/alpha2/
# ---------------------------------------------------------------------------
def _imports_pulp(tree):
    for name in _import_targets(tree):
        if name.split(".")[0] == "pulp":
            return True
    return False


def test_pulp_imported_only_by_cbc_module():
    offenders = []
    for py in sorted((REPO / "src" / "alpha2").rglob("*.py")):
        if _imports_pulp(_tree(py)) and py.resolve() != CBC.resolve():
            offenders.append(str(py.relative_to(REPO)))
    assert not offenders, (
        f"pulp may be imported ONLY by solvers/cbc.py; leaked into {offenders}"
    )


def test_pulp_confinement_guard_is_not_vacuous():
    # cbc.py itself DOES import pulp — the scanner genuinely detects imports.
    assert _imports_pulp(_tree(CBC)), (
        "scanner failed to see the pulp import in cbc.py — guard is vacuous"
    )


# ---------------------------------------------------------------------------
# Guard 3: zero ast.Assert nodes in every solver module
# ---------------------------------------------------------------------------
def test_solver_modules_have_zero_asserts():
    for mod in ALL_SOLVER_MODULES:
        found = [n for n in ast.walk(_tree(mod)) if isinstance(n, ast.Assert)]
        assert not found, (
            f"{mod.relative_to(REPO)} must contain ZERO assert statements "
            f"(stripped under -O), found {len(found)}"
        )


# ---------------------------------------------------------------------------
# Guard 4: python -O subprocess canary over the solver raises.
#
# Exit codes: 3 = not actually under -O (__debug__ True, real branch);
# 4 = NotProvedOptimal did NOT raise; 5 = ChecksumError did NOT raise;
# 0 = BOTH solver guards raised with asserts stripped (correct).
# ---------------------------------------------------------------------------
SCRIPT = textwrap.dedent('''
    import sys
    if __debug__:
        sys.exit(3)   # real branch: we are NOT under -O -> parent fails

    from alpha2.solvers.result import (
        ExactOutcome, NotProvedOptimal, Status,
    )
    # Hand-built INCUMBENT_ONLY outcome (the live-reproduced treacherous case:
    # incumbent 17, true bound 20.879): exact_value() must raise under -O.
    out = ExactOutcome(
        problem="had2", mode="optimize", status=Status.INCUMBENT_ONLY,
        value=17, bound=20.879, bound_source="cbc_log", family=None,
        backend="cbc", backend_version="canary",
    )
    try:
        out.exact_value()
        sys.exit(4)   # BUG: an unproven incumbent read as exact under -O
    except NotProvedOptimal:
        pass

    import alpha2.solvers.problems.had2 as had2mod
    # Tiny triangle-free H (path 0-1-2); mutate the enumeration to drop one
    # single-single conflict after enumeration -> checksum gate must raise.
    adj = [{1}, {0, 2}, {1}]
    orig = had2mod.enumerate_had2
    def mutated(a, n):
        Gedges, ss, sp, pp = orig(a, n)
        ss = set(ss)
        ss.pop()      # deliberately drop one conflict
        return Gedges, ss, sp, pp
    had2mod.enumerate_had2 = mutated
    try:
        had2mod.build_had2_problem(adj, 3)
        sys.exit(5)   # BUG: mutated conflict set passed the checksum under -O
    except had2mod.ChecksumError:
        pass

    sys.exit(0)       # both solver raises fired with asserts stripped
''')


def test_solver_raises_survive_dash_O():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run(
        [sys.executable, "-O", "-c", SCRIPT],
        env=env, cwd=str(REPO), capture_output=True,
    )
    assert r.returncode != 3, "script did not run under -O (__debug__ was True)"
    assert r.returncode == 0, (r.returncode, r.stderr.decode())
