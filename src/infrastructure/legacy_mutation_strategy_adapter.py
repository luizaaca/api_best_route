"""Adapter from legacy route-specific mutation strategies to the generic GA contract."""

from __future__ import annotations

from src.domain.interfaces import IMutationStrategy
from src.domain.interfaces.ga_mutation_strategy import IGeneticMutationStrategy
from src.domain.models.route_genetic_solution import RouteGeneticSolution


class LegacyMutationStrategyAdapter(IGeneticMutationStrategy[RouteGeneticSolution]):
    """Adapt a legacy route-specific mutation strategy to the generic GA API."""

    def __init__(self, strategy: IMutationStrategy) -> None:
        """Store the wrapped legacy mutation strategy.

        Args:
            strategy: Legacy route-specific mutation strategy.
        """
        self._strategy = strategy

    @property
    def name(self) -> str:
        """Return the wrapped strategy name for records and logs."""
        return self._strategy.__class__.__name__

    def mutate(
        self,
        solution: RouteGeneticSolution,
        mutation_probability: float,
    ) -> RouteGeneticSolution:
        """Mutate one wrapped route solution using the legacy strategy."""
        mutated = self._strategy.mutate(solution.individual, mutation_probability)
        return RouteGeneticSolution(mutated)
