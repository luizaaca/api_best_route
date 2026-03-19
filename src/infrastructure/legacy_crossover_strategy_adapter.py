"""Adapter from legacy route-specific crossover strategies to the generic GA contract."""

from __future__ import annotations

from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_crossover_strategy import (
    IGeneticCrossoverStrategy,
)
from src.domain.models.route_genetic_solution import RouteGeneticSolution


class LegacyCrossoverStrategyAdapter(IGeneticCrossoverStrategy[RouteGeneticSolution]):
    """Adapt a legacy route-specific crossover strategy to the generic GA API."""

    def __init__(self, strategy: ICrossoverStrategy) -> None:
        """Store the wrapped legacy crossover strategy.

        Args:
            strategy: Legacy route-specific crossover strategy.
        """
        self._strategy = strategy

    @property
    def name(self) -> str:
        """Return the wrapped strategy name for records and logs."""
        return self._strategy.__class__.__name__

    def crossover(
        self,
        parent1: RouteGeneticSolution,
        parent2: RouteGeneticSolution,
    ) -> RouteGeneticSolution:
        """Cross two wrapped route solutions using the legacy strategy."""
        child = self._strategy.crossover(parent1.individual, parent2.individual)
        return RouteGeneticSolution(child)
