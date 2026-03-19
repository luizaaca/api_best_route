"""2-opt-style mutation strategy for route-order improvement.

This module provides a mutation operator that reverses a subsequence inside a
single vehicle route, approximating a 2-opt local-search move while preserving
the multi-vehicle representation.
"""

import random

from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.models import Individual

from .base_copying_mutation_strategy import BaseCopyingMutationStrategy


class TwoOptMutationStrategy(BaseCopyingMutationStrategy, IMutationStrategy):
    """Mutate an individual with a 2-opt-style subsequence reversal.

    The strategy selects one candidate vehicle route and reverses a contiguous
    subsequence of destinations while keeping the origin fixed at the first
    position.
    """

    def _mutate_in_place(self, solution: Individual) -> None:
        """Reverse a destination subsequence inside one eligible route.

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
        route[start_index : end_index + 1] = reversed(
            route[start_index : end_index + 1]
        )
