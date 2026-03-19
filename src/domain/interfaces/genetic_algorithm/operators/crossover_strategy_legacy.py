"""Legacy route-domain protocol for creating one child from two parents."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import Individual


@runtime_checkable
class ICrossoverStrategy(Protocol):
    """Create one child route individual from two parent individuals."""

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        """Combine two parent individuals into a new offspring.

        Args:
            parent1: The first parent individual.
            parent2: The second parent individual.

        Returns:
            A new individual representing the crossover result.
        """
        ...
