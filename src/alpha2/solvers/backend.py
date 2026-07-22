"""ExactBackend Protocol + lazy backend registry — stdlib ONLY.

Trust-boundary contract:

  * Importing this module never loads a solver library. Backend modules are
    imported LAZILY by name (`alpha2.solvers.{name}`) only when requested —
    the same confinement discipline that keeps the matching library pinned to
    its owning module, applied here at registry level.
  * A backend's `solve_had2` returns an `ExactOutcome` whose family is an
    UNTRUSTED proposal; only the frozen trust root confers truth.
  * All guards raise — no optimization-strippable statements.
"""
import importlib
from typing import Callable, Protocol

from alpha2.solvers.result import ExactOutcome, SolveParams


class ExactBackend(Protocol):
    """The status-honest exact-solver interface every backend implements."""

    name: str

    def backend_version(self) -> str:
        """Human-auditable version stamp (library pin + probed engine version)."""
        ...

    def solve_had2(
        self,
        adj: list[set[int]],
        n: int,
        *,
        mode: str,
        target_k: int | None = None,
        params: SolveParams | None = None,
    ) -> ExactOutcome:
        """Solve had_2 on H=(adj, n) in "optimize" or "decision" mode."""
        ...


_REGISTRY: dict[str, Callable[[], ExactBackend]] = {}


def register_backend(name: str, factory: Callable[[], ExactBackend]) -> None:
    """Register a backend factory under `name` (called by backend modules)."""
    if not isinstance(name, str) or not name:
        raise ValueError(f"backend name must be a non-empty str, got {name!r}")
    _REGISTRY[name] = factory


def get_backend(name: str) -> ExactBackend:
    """Return a backend instance by name, lazily importing its module.

    An unregistered name triggers `importlib.import_module("alpha2.solvers.{name}")`
    so the solver library loads only when its backend is actually requested.
    Raises ValueError if the name is still unknown after the lazy import.
    """
    if name not in _REGISTRY:
        try:
            importlib.import_module(f"alpha2.solvers.{name}")
        except ModuleNotFoundError as exc:
            raise ValueError(f"unknown exact backend {name!r}") from exc
    if name not in _REGISTRY:
        raise ValueError(
            f"module alpha2.solvers.{name} did not register a backend named {name!r}"
        )
    return _REGISTRY[name]()
