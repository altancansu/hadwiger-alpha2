"""Status-honest exact-solve outcome types (EXACT-01) — stdlib ONLY.

Trust-boundary contract:

  * This module is importable by battery/verify/corpus code WITHOUT loading any
    solver library — it depends on `dataclasses` and `enum` alone.
  * `ExactOutcome.exact_value()` is the ONLY battery-facing exact accessor. It
    RAISES `NotProvedOptimal` for every status except PROVED_OPTIMAL, so a
    timed-out incumbent (or any weaker outcome) is structurally unable to read
    as an exact had_2 — the soundness hole of the legacy Appendix-C reader is
    unrepresentable at the type level.
  * `__post_init__` refuses inconsistent construction: UNKNOWN/ERROR carry no
    value (their solver-side numbers are garbage and must never surface), and
    PROVED_OPTIMAL means value == bound by definition.
  * Every guard here raises — these checks are impossibility-adjacent and must
    survive Python's optimized mode; none of them is an optimization-strippable
    statement.

`ExactOutcome.family` is an UNTRUSTED proposal: only the frozen trust root
(`corpus/verifier.verify_certificate`) ever confers truth on a family.
"""
from dataclasses import dataclass, field
from enum import Enum, auto


class Status(Enum):
    """The six-member exact-solve status vocabulary (LOCKED)."""

    MODEL_FOUND = auto()        # decision: feasible witness produced (-> verifier)
    PROVED_OPTIMAL = auto()     # optimize: value exact; bound == value
    PROVED_INFEASIBLE = auto()  # decision: target k proven unreachable (RADIOACTIVE;
                                # single-backend in Phase 4 — never battery-conclusive)
    INCUMBENT_ONLY = auto()     # stopped; value = best found, NOT exact
    UNKNOWN = auto()            # stopped; nothing usable — values are garbage
    ERROR = auto()              # integrality / recompute / encoding failure


class NotProvedOptimal(Exception):
    """Raised when an exact value is requested from a non-proven outcome."""


@dataclass(frozen=True)
class SolveParams:
    """Solver invocation parameters, recorded verbatim in every outcome."""

    time_limit_s: float | None = None
    threads: int = 1


@dataclass(frozen=True)
class ExactOutcome:
    """One exact-solve outcome: status, value/bound evidence, UNTRUSTED family.

    `bound_source` documents where `bound` came from:
      "definition" — PROVED_OPTIMAL (bound == value by definition);
      "cbc_log"    — dual bound parsed from the archived solver log;
      "trivial_n"  — fallback trivial bound n (log line absent);
      "none"       — no bound applicable (e.g. decision mode, hard failure).
    """

    problem: str
    mode: str
    status: Status
    value: int | None
    bound: int | float | None
    bound_source: str
    family: tuple[tuple[int, ...], ...] | None  # UNTRUSTED proposal
    backend: str
    backend_version: str
    params: SolveParams = field(default_factory=SolveParams)
    wall_time_s: float = 0.0

    def __post_init__(self):
        if self.status in (Status.UNKNOWN, Status.ERROR) and self.value is not None:
            raise ValueError(
                f"status={self.status.name} must carry value=None: solver-side "
                "numbers outside the status gate are garbage and never surface"
            )
        if self.status is Status.PROVED_OPTIMAL and self.value != self.bound:
            raise ValueError(
                f"PROVED_OPTIMAL requires value == bound, got value={self.value!r} "
                f"bound={self.bound!r}"
            )

    def exact_value(self) -> int:
        """The ONLY battery-facing exact accessor. Raises unless proven.

        PROVED_OPTIMAL is the sole status for which an exact had_2 exists; every
        other status raises `NotProvedOptimal` — nothing weaker is representable.
        """
        if self.status is not Status.PROVED_OPTIMAL:
            raise NotProvedOptimal(
                f"status={self.status.name}: no exact value exists"
            )
        return self.value
