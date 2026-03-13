import random
from collections.abc import Callable

import numpy as np

from src.domain.interfaces import ISelectionStrategy
from src.domain.models import FleetRouteInfo, Individual, Population


class RoulleteSelectionStrategy(ISelectionStrategy):
    """Select parents with inverse-fitness roulette sampling."""

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Return two sampled parents from the current population."""
        if not population:
            return [], []
        fitness_values = [fitness_function(info) for info in evaluated_population]
        probability = np.array([1 / max(fitness, 1e-9) for fitness in fitness_values])
        parent1, parent2 = random.choices(
            population,
            weights=probability.tolist(),
            k=2,
        )
        return parent1, parent2
