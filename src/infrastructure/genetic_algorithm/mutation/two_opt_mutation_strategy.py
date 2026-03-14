"""2-opt-style mutation strategy for route-order improvement.

This module provides a mutation operator that reverses a subsequence inside a
single vehicle route, approximating a 2-opt local-search move while preserving
the multi-vehicle representation.
"""

import copy
import random

from src.domain.interfaces import IMutationStrategy
from src.domain.models import Individual


class TwoOptMutationStrategy(IMutationStrategy):
    """Mutate an individual with a 2-opt-style subsequence reversal.

    The strategy selects one candidate vehicle route and reverses a contiguous
    subsequence of destinations while keeping the origin fixed at the first
    position.
    """

    @staticmethod
    def _apply_two_opt(solution: Individual) -> None:
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

    def mutate(
        self,
        solution: Individual,
        mutation_probability: float,
    ) -> Individual:
        """Return a mutated copy of the provided solution.

        Args:
            solution: Individual selected for mutation.
            mutation_probability: Probability that the mutation is applied.

        Returns:
            A deep-copied individual that may contain a 2-opt-style local
            improvement move when the mutation is triggered.
        """
        mutated_solution = copy.deepcopy(solution)
        if random.random() < mutation_probability:
            self._apply_two_opt(mutated_solution)
        return mutated_solution
