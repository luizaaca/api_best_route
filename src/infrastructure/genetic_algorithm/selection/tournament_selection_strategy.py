"""Tournament-based selection strategy for the genetic algorithm.

This module provides a configurable tournament selection operator that can be
used as an alternative to roulette-based parent selection.
"""

import random
from collections.abc import Callable

from src.domain.interfaces.genetic_algorithm.operators.selection_strategy_legacy import (
    ISelectionStrategy,
)
from src.domain.models import FleetRouteInfo, Individual, Population


class TournamentSelectionStrategy(ISelectionStrategy):
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

    def _select_one_parent(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> Individual:
        """Return one parent chosen from a tournament.

        Args:
            population: Current genetic algorithm population.
            evaluated_population: Fitness metadata aligned with ``population``.
            fitness_function: Function used to score evaluated individuals.

        Returns:
            The winning individual from the sampled tournament.
        """
        competitor_count = min(self._tournament_size, len(population))
        competitor_indexes = random.sample(range(len(population)), k=competitor_count)
        best_index = min(
            competitor_indexes,
            key=lambda index: fitness_function(evaluated_population[index]),
        )
        return population[best_index]

    def select_parents(
        self,
        population: Population,
        evaluated_population: list[FleetRouteInfo],
        fitness_function: Callable[[FleetRouteInfo], float],
    ) -> tuple[Individual, Individual]:
        """Return two parents selected via independent tournaments.

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
        parent1 = self._select_one_parent(
            population,
            evaluated_population,
            fitness_function,
        )
        parent2 = self._select_one_parent(
            population,
            evaluated_population,
            fitness_function,
        )
        return parent1, parent2
