"""Adapter from legacy route-specific selection strategies to the generic GA contract."""

from __future__ import annotations

import copy

from src.domain.interfaces import ISelectionStrategy
from src.domain.interfaces.ga_selection_strategy import IGeneticSelectionStrategy
from src.domain.models.evaluated_route_solution import EvaluatedRouteSolution
from src.domain.models.route_genetic_solution import RouteGeneticSolution


class LegacySelectionStrategyAdapter(
    IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]
):
    """Adapt a legacy route-specific selection strategy to the generic GA API."""

    def __init__(self, strategy: ISelectionStrategy) -> None:
        """Store the wrapped legacy selection strategy.

        Args:
            strategy: Legacy route-specific selection strategy.
        """
        self._strategy = strategy

    @property
    def name(self) -> str:
        """Return the wrapped strategy name for records and logs."""
        return self._strategy.__class__.__name__

    def select_parents(
        self,
        population: list[RouteGeneticSolution],
        evaluated_population: list[EvaluatedRouteSolution],
    ) -> tuple[RouteGeneticSolution, RouteGeneticSolution]:
        """Select two parent route solutions using the legacy strategy.

        Args:
            population: Current route-solution population.
            evaluated_population: Aligned evaluated route solutions.

        Returns:
            Two wrapped route solutions selected for crossover.
        """
        raw_population = [solution.individual for solution in population]
        raw_evaluated_population = [
            evaluation._route_info for evaluation in evaluated_population
        ]
        parent1, parent2 = self._strategy.select_parents(
            raw_population,
            raw_evaluated_population,
            lambda route_info: (
                route_info.total_cost
                if route_info.total_cost is not None
                else route_info.max_vehicle_eta
            ),
        )
        return (
            RouteGeneticSolution(copy.deepcopy(parent1)),
            RouteGeneticSolution(copy.deepcopy(parent2)),
        )
