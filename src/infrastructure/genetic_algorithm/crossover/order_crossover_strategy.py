"""Order crossover operator for multi-vehicle routing individuals.

This strategy performs an order crossover over the flattened destination
sequences and then relies on the shared permutation-crossover scaffold to
rebuild the multi-vehicle solution.
"""

import random

from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.models import RouteNode

from .base_permutation_crossover_strategy import BasePermutationCrossoverStrategy


class OrderCrossoverStrategy(BasePermutationCrossoverStrategy, ICrossoverStrategy):
    """Preserve relative destination ordering through classic OX crossover."""

    def _build_child_destinations(
        self,
        parent1_destinations: list[RouteNode],
        parent2_destinations: list[RouteNode],
    ) -> list[RouteNode]:
        """Apply classic order crossover on two destination sequences.

        This method selects a random slice from the first parent and fills the
        remaining positions with destinations from the second parent in order,
        skipping duplicates.

        Args:
            parent1_destinations: The first destination sequence.
            parent2_destinations: The second destination sequence.

        Returns:
            A new list of destinations representing the crossover child.
        """
        length = len(parent1_destinations)
        if length < 2:
            return parent1_destinations[:]
        start_index = random.randint(0, length - 1)
        end_index = random.randint(start_index + 1, length)
        child = parent1_destinations[start_index:end_index]
        remaining_positions = [
            index
            for index in range(length)
            if index < start_index or index >= end_index
        ]
        remaining_genes = [
            gene for gene in parent2_destinations if gene not in child
        ]
        for position, gene in zip(remaining_positions, remaining_genes):
            child.insert(position, gene)
        return child
