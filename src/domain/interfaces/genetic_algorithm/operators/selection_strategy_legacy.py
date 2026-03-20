"""Legacy route-domain protocol for selecting parent solutions from a population."""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from src.domain.models.genetic_algorithm.individual import Individual
from src.domain.models.genetic_algorithm.population import Population
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo


@runtime_checkable
class ISelectionStrategy(Protocol):
    """Select parent solutions from a route-optimization population."""

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Choose two individuals from the current population to act as parents.

        Args:
            population: The current population of candidate solutions.
            evaluated_population: The population evaluated with fitness scores.
            fitness_function: A callable that returns a fitness score for a given
                FleetRouteInfo.

        Returns:
            A pair of individuals selected to be parents for the next generation.
        """
        ...
