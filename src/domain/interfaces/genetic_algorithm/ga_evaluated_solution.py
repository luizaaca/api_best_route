"""Domain protocol for evaluated GA solutions.

This protocol defines the minimum data the engine needs after a raw solution
has been evaluated by the problem layer.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .ga_solution import IGeneticSolution


@runtime_checkable
class IEvaluatedGeneticSolution(Protocol):
    """Represent one evaluated solution used by the GA engine.

    The evaluated solution exposes comparable fitness information and optional
    metrics while keeping the evaluation semantics inside the problem domain.
    """

    @property
    def solution(self) -> IGeneticSolution:
        """Return the raw solution that produced this evaluation."""
        ...

    @property
    def fitness(self) -> float:
        """Return the scalar fitness value used for ranking.

        Returns:
            A minimization-oriented fitness score.
        """
        ...

    def metric(self, name: str, default: Any = None) -> Any:
        """Return one named metric exposed by the evaluated solution.

        Args:
            name: Metric identifier.
            default: Value returned when the metric is not available.

        Returns:
            The metric value when present, otherwise `default`.
        """
        ...
