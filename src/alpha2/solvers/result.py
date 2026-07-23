"""Status-honest exact-solve outcome types (EXACT-01) — stdlib ONLY.

Trust-boundary contract:

  * This module is importable by battery/verify/corpus code WITHOUT loading any
    solver library — it depends on `dataclasses` and `enum` alone.
  * `ExactOutcome.exact_value()` is the ONLY battery-facing exact accessor. It
    RAISES `NotProvedOptimal` for every status except PROVED_OPTIMAL, so a
    timed-out incumbent (or any weaker outcome) is structurally unable to read
    as an exact had_2 — the soundness hole of the legacy Appendix-C reader is
    unrepresentable at the type level.
  * `__post_init__` refuses inconsistent construction (04-REVIEW WR-02):
    PROVED_OPTIMAL / INCUMBENT_ONLY / MODEL_FOUND REQUIRE a genuine int value
    (bool and float rejected); PROVED_INFEASIBLE / UNKNOWN / ERROR carry no
    value (their solver-side numbers are garbage — or, for an
    impossibility-flavored status, radioactive — and must never surface);
    PROVED_OPTIMAL additionally requires value == bound by definition AND a
    non-None family (the model that proves the value is attainable), while
    PROVED_INFEASIBLE / UNKNOWN / ERROR must carry family=None. A constructed
    PROVED_OPTIMAL therefore cannot yield None (or a float) from
    `exact_value()` — the invariants hold at construction, structurally.
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
    """Solver invocation parameters, recorded verbatim in every outcome.

    `det_time` / `det_nodes` are ADDITIVE deterministic-budget fields (Phase 8): on
    the shared 64–250-core box a recorded verdict must be a function of (n, seed), not
    machine speed, so any reported impossibility/RESISTANT run is bounded by a
    work-count (CP-SAT `max_deterministic_time`) or node-count (CBC `maxNodes`) budget
    — NEVER wall-clock. Both default None → unbounded → the frozen 296-corpus
    reproduction path is byte-unchanged. `time_limit_s` (wall-clock) and `threads`
    are unchanged; wall-clock is forbidden for any path feeding a reported verdict.
    """

    time_limit_s: float | None = None
    threads: int = 1
    det_time: float | None = None   # CP-SAT deterministic work-count budget
    det_nodes: int | None = None    # CBC deterministic node-count cap (maxNodes)


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
    # WR-01 (05-REVIEW): the had_3 Tier-1 model OMITS triple-triple conflicts, so
    # its feasible region is a SUPERSET of the true size-3 model — solve_had3's
    # proven optimum is an UPPER BOUND on the true had_3, never the exact size-3
    # Hadwiger number. This flag travels with the outcome so a Tier-1 value can
    # NEVER be silently read as an exact had_3 optimum. Sound in the impossibility
    # direction (value < chi => true had_3 <= value < chi); UNSOUND as a kill
    # (value >= chi does NOT prove a K_chi minor — the winning family may hold two
    # mutually non-adjacent triples). had_2 outcomes leave it False.
    value_is_upper_bound: bool = False

    # Statuses that carry a value (04-RESEARCH: value is populated ONLY for
    # these three) vs statuses whose solver-side numbers are garbage or
    # radioactive and must never surface. Class-level, not per-instance.
    _VALUED = (Status.PROVED_OPTIMAL, Status.INCUMBENT_ONLY, Status.MODEL_FOUND)
    _BOUND_SOURCES = ("definition", "cbc_log", "trivial_n", "none")

    def __post_init__(self):
        if self.status in self._VALUED:
            # bool subclasses int: True would silently read as value 1.
            if not isinstance(self.value, int) or isinstance(self.value, bool):
                raise ValueError(
                    f"status={self.status.name} requires a genuine int value "
                    f"(bool/float/None rejected), got {self.value!r}"
                )
        elif self.value is not None:
            # PROVED_INFEASIBLE joins UNKNOWN/ERROR: no value ever surfaces.
            raise ValueError(
                f"status={self.status.name} must carry value=None: solver-side "
                "numbers outside the status gate are garbage and never surface"
            )
        if self.status is Status.PROVED_OPTIMAL:
            if self.value != self.bound:
                raise ValueError(
                    f"PROVED_OPTIMAL requires value == bound, got "
                    f"value={self.value!r} bound={self.bound!r}"
                )
            if self.family is None:
                raise ValueError(
                    "PROVED_OPTIMAL requires a non-None family: the exact "
                    "value is only honest alongside the model attaining it"
                )
        elif self.status not in self._VALUED and self.family is not None:
            # PROVED_INFEASIBLE / UNKNOWN / ERROR: no family may surface.
            raise ValueError(
                f"status={self.status.name} must carry family=None"
            )
        if self.bound_source not in self._BOUND_SOURCES:
            raise ValueError(
                f"unknown bound_source {self.bound_source!r}; expected one "
                f"of {self._BOUND_SOURCES}"
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
