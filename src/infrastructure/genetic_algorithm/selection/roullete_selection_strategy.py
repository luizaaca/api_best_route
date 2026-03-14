"""Roulette selection strategy for choosing parent solutions.

This implementation performs inverse-fitness sampling, meaning lower fitness values
are considered more desirable (since the problem is a minimization task).
"""

import random
from collections.abc import Callable

import numpy as np

from src.domain.interfaces import ISelectionStrategy
from src.domain.models import FleetRouteInfo, Individual, Population


class RoulleteSelectionStrategy(ISelectionStrategy):
    """Select parents using a roulette-wheel approach based on fitness."""

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Sample two parents from the population based on fitness.

        Args:
            population: The current population of candidate solutions.
            evaluated_population: The population evaluated with fitness values.
            fitness_function: Callable returning a fitness score for each individual.

        Returns:
            A pair of selected individuals to be used as parents.
        """
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
