"""Domain protocol for generic GA mutation strategies."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from ..ga_solution import IGeneticSolution

TSolution = TypeVar("TSolution", bound=IGeneticSolution)


@runtime_checkable
class IGeneticMutationStrategy(Protocol[TSolution]):
    """Apply mutation to one raw GA solution."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        ...

    def mutate(self, solution: TSolution, mutation_probability: float) -> TSolution:
        """Mutate one solution using the provided probability.

        Args:
            solution: Raw solution to mutate.
            mutation_probability: Active mutation probability for the generation.

        Returns:
            The resulting solution after mutation logic is applied.
        """
        ...
