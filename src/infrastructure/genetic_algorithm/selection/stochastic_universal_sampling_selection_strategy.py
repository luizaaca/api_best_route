"""Stochastic universal sampling selection strategy.

This module provides a lower-variance alternative to roulette-wheel parent
selection using evenly spaced sampling pointers across the cumulative weight
distribution.
"""

import random
from collections.abc import Callable

from src.domain.interfaces.genetic_algorithm.operators.selection_strategy_legacy import (
    ISelectionStrategy,
)
from src.domain.models.genetic_algorithm.individual import Individual
from src.domain.models.genetic_algorithm.population import Population
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo


class StochasticUniversalSamplingSelectionStrategy(ISelectionStrategy):
    """Select parents using stochastic universal sampling.

    The strategy converts fitness values into inverse-fitness weights and then
    samples two parents using evenly spaced pointers over the cumulative weight
    distribution.
    """

    @staticmethod
    def _build_weights(
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> list[float]:
        """Build inverse-fitness weights for the evaluated population.

        Args:
            evaluated_population: Evaluated population aligned with the current
                population order.
            fitness_function: Function used to score evaluated individuals.

        Returns:
            A list of positive weights aligned with the population order.
        """
        return [
            1 / max(fitness_function(individual_info), 1e-9)
            for individual_info in evaluated_population
        ]

    @staticmethod
    def _select_index(cumulative_weights: list[float], pointer: float) -> int:
        """Return the first cumulative slot that covers the given pointer.

        Args:
            cumulative_weights: Ascending cumulative weight distribution.
            pointer: Pointer position to resolve.

        Returns:
            The selected population index.
        """
        for index, cumulative_weight in enumerate(cumulative_weights):
            if pointer <= cumulative_weight:
                return index
        return len(cumulative_weights) - 1

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Return two parents sampled through stochastic universal sampling.

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

        weights = self._build_weights(evaluated_population, fitness_function)
        total_weight = sum(weights)
        step = total_weight / 2
        start_pointer = random.uniform(0, step)

        cumulative_weights: list[float] = []
        running_total = 0.0
        for weight in weights:
            running_total += weight
            cumulative_weights.append(running_total)

        parent_indexes = [
            self._select_index(
                cumulative_weights, start_pointer + pointer_offset * step
            )
            for pointer_offset in range(2)
        ]
        return population[parent_indexes[0]], population[parent_indexes[1]]
