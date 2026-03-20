"""Inversion mutation strategy for multi-vehicle route individuals.

This module provides a mutation operator that reverses a contiguous subsequence
inside a randomly chosen eligible vehicle route.
"""

import random

from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.models.genetic_algorithm.individual import Individual

from .base_copying_mutation_strategy import BaseCopyingMutationStrategy


class InversionMutationStrategy(BaseCopyingMutationStrategy, IMutationStrategy):
    """Mutate an individual by inverting a destination subsequence."""

    def _mutate_in_place(self, solution: Individual) -> None:
        """Reverse a contiguous destination subsequence in one route.

        Args:
            solution: Mutable copy of the multi-vehicle individual.

        Returns:
            None. The solution is mutated in place when a valid route exists.
        """
        candidate_routes = [route for route in solution if len(route) > 2]
        if not candidate_routes:
            return
        route = random.choice(candidate_routes)
        start_index, end_index = sorted(random.sample(range(1, len(route)), 2))
        route[start_index : end_index + 1] = list(
            reversed(route[start_index : end_index + 1])
        )
