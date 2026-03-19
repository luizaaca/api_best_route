"""Cycle crossover operator for permutation-based multi-vehicle routes.

This module provides a cycle crossover implementation that alternates genetic
material between parents by following position cycles in the flattened
destination permutation.
"""

from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.models import RouteNode

from .base_permutation_crossover_strategy import BasePermutationCrossoverStrategy


class CycleCrossoverStrategy(BasePermutationCrossoverStrategy, ICrossoverStrategy):
    """Create a child by alternating cycles from two parent permutations."""

    def _build_child_destinations(
        self,
        parent1_destinations: list[RouteNode],
        parent2_destinations: list[RouteNode],
    ) -> list[RouteNode]:
        """Build the child destination permutation using cycle crossover.

        Args:
            parent1_destinations: Flattened destination permutation of parent 1.
            parent2_destinations: Flattened destination permutation of parent 2.

        Returns:
            A child permutation containing each destination exactly once.
        """
        length = len(parent1_destinations)
        if length < 2:
            return parent1_destinations[:]

        parent1_ids = [node.node_id for node in parent1_destinations]
        parent2_ids = [node.node_id for node in parent2_destinations]
        node_by_id = {
            node.node_id: node for node in parent1_destinations + parent2_destinations
        }
        child_ids: list[int | None] = [None] * length
        unassigned_indexes = set(range(length))
        use_parent1_cycle = True

        while unassigned_indexes:
            start_index = min(unassigned_indexes)
            cycle_indexes: list[int] = []
            current_index = start_index

            while current_index not in cycle_indexes:
                cycle_indexes.append(current_index)
                next_id = parent2_ids[current_index]
                current_index = parent1_ids.index(next_id)

            selected_ids = parent1_ids if use_parent1_cycle else parent2_ids
            for cycle_index in cycle_indexes:
                child_ids[cycle_index] = selected_ids[cycle_index]
                unassigned_indexes.discard(cycle_index)

            use_parent1_cycle = not use_parent1_cycle

        return [node_by_id[node_id] for node_id in child_ids if node_id is not None]
