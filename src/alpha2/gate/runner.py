"""Gate outcome vocabulary + cost-ordered chain runner (GATE-01, D-01 Role B) — stdlib ONLY.

The outcome types (`Pass` / `Fail` / `Error` / `GateKill` / `GateResult`) mirror the frozen
validated-dataclass discipline of `solvers/result.py`: every `__post_init__` guard RAISES
(never `assert`, so `python -O` cannot strip it). `checks.py` imports the per-check outcome
types from here; the chain-walking `run_gate` / `default_chain` (Task 3) are appended below.
"""
from dataclasses import dataclass, field
from enum import Enum, auto


class Verdict(Enum):
    """Overall gate verdict for one candidate."""

    PASS = auto()      # cleared the hard-gate (flags may still travel on the result)
    KILLED = auto()    # a HARD check FAILed — dead on arrival, no compute spent
    ERROR = auto()     # a check quarantined (malformed input / recompute failure) — NEVER a kill


# The two tiers a check may occupy (D-01 Role B, LOCKED).
TIERS = ("hard", "flag_only")


@dataclass(frozen=True)
class Pass:
    """A check passed. `witness` records the evidence (invariant values inspected)."""

    witness: dict = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.witness, dict):
            raise ValueError(f"Pass witness must be a dict, got {type(self.witness).__name__}")


@dataclass(frozen=True)
class Fail:
    """A check failed. `reason` quotes the §2 requirement; `witness` carries the values."""

    reason: str
    witness: dict = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("Fail requires a non-empty reason string")
        if not isinstance(self.witness, dict):
            raise ValueError(f"Fail witness must be a dict, got {type(self.witness).__name__}")


@dataclass(frozen=True)
class Error:
    """A check could not be evaluated (malformed input / recompute failure). Quarantine."""

    trace: str

    def __post_init__(self):
        if not isinstance(self.trace, str) or not self.trace:
            raise ValueError("Error requires a non-empty trace string")


@dataclass(frozen=True)
class GateKill:
    """The terminal kill record: the name of the hard check that killed + its witness."""

    reason: str
    witness: dict = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("GateKill requires a non-empty killing-check name")
        if not isinstance(self.witness, dict):
            raise ValueError(f"GateKill witness must be a dict, got {type(self.witness).__name__}")


@dataclass(frozen=True)
class GateResult:
    """Aggregate gate outcome: overall verdict + killing check (if any) + ordered flags."""

    verdict: Verdict
    killing: str | None = None
    witness: dict = field(default_factory=dict)   # the killing check's witness (KILLED only)
    flags: tuple = ()                             # ordered ((name, Fail), ...) from flag_only checks
    passed: tuple = ()                            # names of checks that passed
    error: "Error | None" = None                  # the quarantining Error (ERROR only)

    def __post_init__(self):
        if not isinstance(self.verdict, Verdict):
            raise ValueError(f"verdict must be a Verdict, got {self.verdict!r}")
        if self.verdict is Verdict.KILLED and not self.killing:
            raise ValueError("a KILLED verdict requires the killing check name")
        if self.verdict is not Verdict.KILLED and self.killing is not None:
            raise ValueError("only a KILLED verdict may name a killing check")
        if self.verdict is Verdict.ERROR and self.error is None:
            raise ValueError("an ERROR verdict requires an Error record")
        if self.verdict is not Verdict.ERROR and self.error is not None:
            raise ValueError("only an ERROR verdict may carry an Error record")

    @property
    def flag_names(self):
        return tuple(name for name, _ in self.flags)


# ---------- cost-ordered chain (D-01 Role B: hard vs flag_only tiers, LOCKED) ----------
def default_chain():
    """The canonical cost-ordered chain `((name, tier, check_fn), ...)`.

    Resolved lazily (checks imported inside) so `checks.py` -> `runner.py` (for the outcome
    types) is a clean one-directional import; the chain never forms an import cycle.

    Hard set (the ONLY checks that may KILL) = {g1_criticality, g2_triangle_free_diam2,
    g_connectivity}. Everything deeper (g3_deep, g4_omega_window, g5, g6) is flag_only:
    it records regime + reason + witness but never terminates the runbook (Role B). Order
    is cost-increasing — cheap criticality/connectivity before expensive kappa/omega.
    """
    from alpha2.gate import checks
    return (
        ("g1_criticality",         "hard",      checks.g1_criticality),
        ("g2_triangle_free_diam2", "hard",      checks.g2_triangle_free_diam2),
        ("g_connectivity",         "hard",      checks.g_connectivity),
        ("g3_deep",                "flag_only", checks.g3_deep),
        ("g4_omega_window",        "flag_only", checks.g4_omega_window),
        ("g5_unavoidables",        "flag_only", checks.g5_unavoidables),
        ("g6_safe_families",       "flag_only", checks.g6_safe_families),
    )


def __getattr__(name):
    # PEP 562 lazy attribute: `runner.DEFAULT_CHAIN` (and `from ... import DEFAULT_CHAIN`)
    # resolve the chain on demand, keeping module import strictly one-directional.
    if name == "DEFAULT_CHAIN":
        return default_chain()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def run_gate(adj, n, inv, chain=None):
    """Walk `chain` in cost order; return a `GateResult` (D-01 Role B).

    - a HARD `Fail` stops immediately -> KILLED (no later check runs);
    - a FLAG_ONLY `Fail` is appended to `flags` and execution CONTINUES;
    - an `Error` quarantines -> ERROR (NEVER a kill), stopping the chain;
    - all checks passing (modulo flags) -> PASS.

    Guards RAISE (malformed tier / non-outcome return); no `assert` (python -O safe).
    """
    if chain is None:
        chain = default_chain()
    flags = []
    passed = []
    for entry in chain:
        if len(entry) != 3:
            raise ValueError(f"chain entry must be (name, tier, check_fn), got {entry!r}")
        name, tier, check_fn = entry
        if tier not in TIERS:
            raise ValueError(f"check {name!r} has unknown tier {tier!r}; expected {TIERS}")
        outcome = check_fn(adj, n, inv)
        if isinstance(outcome, Error):
            return GateResult(
                verdict=Verdict.ERROR, error=outcome,
                flags=tuple(flags), passed=tuple(passed),
            )
        if isinstance(outcome, Pass):
            passed.append(name)
            continue
        if isinstance(outcome, Fail):
            if tier == "hard":
                return GateResult(
                    verdict=Verdict.KILLED, killing=name, witness=outcome.witness,
                    flags=tuple(flags), passed=tuple(passed),
                )
            flags.append((name, outcome))
            continue
        raise TypeError(
            f"check {name!r} returned a non-outcome {type(outcome).__name__}; "
            "expected Pass | Fail | Error"
        )
    return GateResult(verdict=Verdict.PASS, flags=tuple(flags), passed=tuple(passed))
