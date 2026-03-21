"""Roulette selection strategy for choosing parent solutions.

This implementation performs inverse-fitness sampling, meaning lower fitness values
are considered more desirable (since the problem is a minimization task).
"""

import random
from collections.abc import Sequence

import numpy as np

from src.domain.interfaces.genetic_algorithm.operators.ga_selection_strategy import (
    IGeneticSelectionStrategy,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)


class RoulleteSelectionStrategy(
    IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]
):
    """Select parents using a roulette-wheel approach based on fitness."""

    @property
    def name(self) -> str:
        """Return the stable strategy identifier used by the GA runtime."""
        return self.__class__.__name__

    def select_parents(
        self,
        population: Sequence[RouteGeneticSolution],
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> tuple[RouteGeneticSolution, RouteGeneticSolution]:
        """Sample two parents from the population based on fitness.

        Args:
            population: The current population of candidate solutions.
            evaluated_population: The population evaluated with fitness values.

        Returns:
            A pair of selected individuals to be used as parents.
        """
        if not population:
            empty_solution = RouteGeneticSolution([])
            return empty_solution, empty_solution.clone()
        fitness_values = [evaluation.fitness for evaluation in evaluated_population]
        probability = np.array([1 / max(fitness, 1e-9) for fitness in fitness_values])
        parent1, parent2 = random.choices(
            population,
            weights=probability.tolist(),
            k=2,
        )
        return parent1.clone(), parent2.clone()
