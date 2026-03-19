"""Legacy route-domain protocol for mutating one route individual."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import Individual


@runtime_checkable
class IMutationStrategy(Protocol):
    """Introduce random variation into one route-domain solution."""

    def mutate(
        self,
        solution: Individual,
        mutation_probability: float,
    ) -> Individual:
        """Mutate a candidate solution based on a given probability.

        Args:
            solution: The individual to mutate.
            mutation_probability: The probability of applying a mutation.

        Returns:
            A potentially modified individual.
        """
        ...
