"""Tournament-based selection strategy for the genetic algorithm.

This module provides a configurable tournament selection operator that can be
used as an alternative to roulette-based parent selection.
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


class TournamentSelectionStrategy(
    IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]
):
    """Select parents using tournament selection.

    The strategy samples a subset of individuals from the population and picks
    the best one according to the provided fitness function. The process is
    repeated independently for each parent.

    Args:
        tournament_size: Number of competitors sampled for each tournament.

    Raises:
        ValueError: If ``tournament_size`` is smaller than ``2``.
    """

    def __init__(self, tournament_size: int = 3):
        """Initialize the selection strategy.

        Args:
            tournament_size: Number of candidates to compare in each tournament.

        Raises:
            ValueError: If ``tournament_size`` is smaller than ``2``.
        """
        if tournament_size < 2:
            raise ValueError("tournament_size must be at least 2")
        self._tournament_size = tournament_size

    @property
    def name(self) -> str:
        """Return the stable strategy identifier used by the GA runtime."""
        return self.__class__.__name__

    def _select_one_parent(
        self,
        population: Sequence[RouteGeneticSolution],
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> RouteGeneticSolution:
        """Return one parent chosen from a tournament.

        Args:
            population: Current genetic algorithm population.
            evaluated_population: Fitness metadata aligned with ``population``.

        Returns:
            The winning individual from the sampled tournament.
        """
        competitor_count = min(self._tournament_size, len(population))
        competitor_indexes = random.sample(range(len(population)), k=competitor_count)
        best_index = min(
            competitor_indexes,
            key=lambda index: evaluated_population[index].fitness,
        )
        return population[best_index].clone()

    def select_parents(
        self,
        population: Sequence[RouteGeneticSolution],
        evaluated_population: Sequence[EvaluatedRouteSolution],
    ) -> tuple[RouteGeneticSolution, RouteGeneticSolution]:
        """Return two parents selected via independent tournaments.

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
        parent1 = self._select_one_parent(
            population,
            evaluated_population,
        )
        parent2 = self._select_one_parent(
            population,
            evaluated_population,
        )
        return parent1, parent2
