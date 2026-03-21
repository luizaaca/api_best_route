"""Stochastic universal sampling selection strategy.

This module provides a lower-variance alternative to roulette-wheel parent
selection using evenly spaced sampling pointers across the cumulative weight
distribution.
"""

import random
from collections.abc import Sequence

from src.domain.interfaces.genetic_algorithm.operators.ga_selection_strategy import (
    IGeneticSelectionStrategy,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)


class StochasticUniversalSamplingSelectionStrategy(
    IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]
):
    """Select parents using stochastic universal sampling.

    The strategy converts fitness values into inverse-fitness weights and then
    samples two parents using evenly spaced pointers over the cumulative weight
    distribution.
    """

    @staticmethod
    def _build_weights(
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> list[float]:
        """Build inverse-fitness weights for the evaluated population.

        Args:
            evaluated_population: Evaluated population aligned with the current
                population order.

        Returns:
            A list of positive weights aligned with the population order.
        """
        return [
            1 / max(individual_info.fitness, 1e-9)
            for individual_info in evaluated_population
        ]

    @property
    def name(self) -> str:
        """Return the stable strategy identifier used by the GA runtime."""
        return self.__class__.__name__

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
        population: Sequence[RouteGeneticSolution],
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> tuple[RouteGeneticSolution, RouteGeneticSolution]:
        """Return two parents sampled through stochastic universal sampling.

        Args:
            population: Current genetic algorithm population.
            evaluated_population: Fitness metadata aligned with ``population``.

        Returns:
            A tuple with two selected parents. When the population is empty,
            returns two empty individuals.
        """
        if not population:
            empty_solution = RouteGeneticSolution([])
            return empty_solution, empty_solution.clone()

        weights = self._build_weights(evaluated_population)
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
        return (
            population[parent_indexes[0]].clone(),
            population[parent_indexes[1]].clone(),
        )
