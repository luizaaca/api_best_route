"""Rank-based selection strategy for the genetic algorithm.

This module provides a parent selection operator that assigns selection weight
based on the ranking of each individual instead of raw fitness magnitude.
"""

import random
from collections.abc import Callable

from src.domain.interfaces.genetic_algorithm.operators.selection_strategy_legacy import (
    ISelectionStrategy,
)
from src.domain.models.genetic_algorithm.individual import Individual
from src.domain.models.genetic_algorithm.population import Population
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo


class RankSelectionStrategy(ISelectionStrategy):
    """Select parents using rank-based probabilities.

    Better-ranked individuals receive higher selection probability, while the
    probability gaps remain smoother than in raw fitness-proportional methods.
    """

    @staticmethod
    def _build_rank_weights(
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> list[int]:
        """Build per-individual rank weights for the current population.

        Args:
            evaluated_population: Evaluated population aligned with the current
                population order.
            fitness_function: Function used to score evaluated individuals.

        Returns:
            A list of integer weights aligned with the population order.
        """
        ranked_indexes = sorted(
            range(len(evaluated_population)),
            key=lambda index: fitness_function(evaluated_population[index]),
        )
        weights = [0] * len(evaluated_population)
        population_size = len(evaluated_population)
        for rank, index in enumerate(ranked_indexes):
            weights[index] = population_size - rank
        return weights

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Return two parents selected with rank-based probabilities.

        Args:
            population: Current genetic algorithm population.
            evaluated_population: Fitness metadata aligned with ``population``.
            fitness_function: Function used to score evaluated individuals.

        Returns:
            A tuple with two selected parents. When the population is empty,
            returns two empty individuals.
        """
        if not population:
            return [], []
        weights = self._build_rank_weights(evaluated_population, fitness_function)
        parent1, parent2 = random.choices(population, weights=weights, k=2)
        return parent1, parent2
