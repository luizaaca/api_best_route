"""Rank-based selection strategy for the genetic algorithm.

This module provides a parent selection operator that assigns selection weight
based on the ranking of each individual instead of raw fitness magnitude.
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


class RankSelectionStrategy(
    IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]
):
    """Select parents using rank-based probabilities.

    Better-ranked individuals receive higher selection probability, while the
    probability gaps remain smoother than in raw fitness-proportional methods.
    """

    @property
    def name(self) -> str:
        """Return the stable strategy identifier used by the GA runtime."""
        return self.__class__.__name__

    @staticmethod
    def _build_rank_weights(
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> list[int]:
        """Build per-individual rank weights for the current population.

        Args:
            evaluated_population: Evaluated population aligned with the current
                population order.

        Returns:
            A list of integer weights aligned with the population order.
        """
        ranked_indexes = sorted(
            range(len(evaluated_population)),
            key=lambda index: evaluated_population[index].fitness,
        )
        weights = [0] * len(evaluated_population)
        population_size = len(evaluated_population)
        for rank, index in enumerate(ranked_indexes):
            weights[index] = population_size - rank
        return weights

    def select_parents(
        self,
        population: Sequence[RouteGeneticSolution],
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> tuple[RouteGeneticSolution, RouteGeneticSolution]:
        """Return two parents selected with rank-based probabilities.

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
        weights = self._build_rank_weights(evaluated_population)
        parent1, parent2 = random.choices(population, weights=weights, k=2)
        return parent1.clone(), parent2.clone()
