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
