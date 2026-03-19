"""Domain protocol for generic GA crossover strategies."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from ..ga_solution import IGeneticSolution

TSolution = TypeVar("TSolution", bound=IGeneticSolution)


@runtime_checkable
class IGeneticCrossoverStrategy(Protocol[TSolution]):
    """Combine two parent solutions into one offspring solution."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        ...

    def crossover(self, parent1: TSolution, parent2: TSolution) -> TSolution:
        """Build one offspring solution from two parent solutions.

        Args:
            parent1: First parent solution.
            parent2: Second parent solution.

        Returns:
            One offspring solution.
        """
        ...
