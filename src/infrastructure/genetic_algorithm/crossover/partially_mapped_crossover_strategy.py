"""Partially mapped crossover implementation for permutation-based routes.

This module provides a PMX crossover operator adapted to the multi-vehicle
representation used by the route optimization genetic algorithm.
"""

import random
from src.domain.models.geo_graph.route_node import RouteNode

from .base_permutation_crossover_strategy import BasePermutationCrossoverStrategy


class PartiallyMappedCrossoverStrategy(BasePermutationCrossoverStrategy):
    """Create a child by applying PMX to the flattened destination sequence.

    The operator preserves the repeated origin convention of each vehicle route
    by flattening only destinations, applying PMX over that permutation, and
    then rebuilding the multi-vehicle structure.
    """

    def _build_child_destinations(
        self,
        parent1_destinations: list[RouteNode],
        parent2_destinations: list[RouteNode],
    ) -> list[RouteNode]:
        """Apply PMX to two destination permutations.

        Args:
            parent1_destinations: First parent permutation.
            parent2_destinations: Second parent permutation.

        Returns:
            A child permutation containing every destination exactly once.
        """
        length = len(parent1_destinations)
        if length < 2:
            return parent1_destinations[:]

        start_index, end_index = sorted(random.sample(range(length), 2))
        child_ids: list[int | None] = [None] * length
        parent1_ids = [node.node_id for node in parent1_destinations]
        parent2_ids = [node.node_id for node in parent2_destinations]
        node_by_id = {
            node.node_id: node for node in parent1_destinations + parent2_destinations
        }

        for index in range(start_index, end_index + 1):
            child_ids[index] = parent1_ids[index]

        for index in range(start_index, end_index + 1):
            candidate_id = parent2_ids[index]
            if candidate_id in child_ids:
                continue
            target_index = index
            while True:
                mapped_id = parent1_ids[target_index]
                target_index = parent2_ids.index(mapped_id)
                if child_ids[target_index] is None:
                    child_ids[target_index] = candidate_id
                    break

        for index, candidate_id in enumerate(parent2_ids):
            if child_ids[index] is None:
                child_ids[index] = candidate_id

        return [node_by_id[node_id] for node_id in child_ids if node_id is not None]
