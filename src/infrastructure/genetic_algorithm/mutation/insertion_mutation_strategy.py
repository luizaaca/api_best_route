"""Insertion mutation strategy for multi-vehicle route individuals.

This module provides a mutation operator that removes one destination from its
current position and inserts it into a new position, potentially in another
vehicle route.
"""

import random

from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.models.genetic_algorithm.individual import Individual

from .base_copying_mutation_strategy import BaseCopyingMutationStrategy


class InsertionMutationStrategy(BaseCopyingMutationStrategy, IMutationStrategy):
    """Mutate an individual by relocating a destination node."""

    def _mutate_in_place(self, solution: Individual) -> None:
        """Remove one destination and insert it at a new valid position.

        Args:
            solution: Mutable copy of the multi-vehicle individual.

        Returns:
            None. The solution is mutated in place when a valid move exists.
        """
        source_indexes = [
            index for index, route in enumerate(solution) if len(route) > 1
        ]
        if not source_indexes:
            return

        source_index = random.choice(source_indexes)
        source_route = solution[source_index]
        moved_position = random.randint(1, len(source_route) - 1)
        moved_node = source_route.pop(moved_position)

        target_index = random.randrange(len(solution))
        target_route = solution[target_index]
        insert_position = random.randint(1, len(target_route))
        target_route.insert(insert_position, moved_node)
