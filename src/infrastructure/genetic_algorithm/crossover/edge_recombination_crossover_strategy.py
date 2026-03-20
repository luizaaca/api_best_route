"""Edge recombination crossover for permutation-based multi-vehicle routes.

This module provides an edge-preserving crossover operator that attempts to
keep useful adjacency relationships from both parents when constructing the
child destination permutation.
"""

import random

from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.models.geo_graph.route_node import RouteNode

from .base_permutation_crossover_strategy import BasePermutationCrossoverStrategy


class EdgeRecombinationCrossoverStrategy(
    BasePermutationCrossoverStrategy,
    ICrossoverStrategy,
):
    """Create a child by preserving parent adjacency information when possible."""

    @staticmethod
    def _build_edge_map(parent_ids: list[int]) -> dict[int, set[int]]:
        """Build adjacency relationships for a flattened parent permutation.

        Args:
            parent_ids: Parent destination permutation represented by node IDs.

        Returns:
            A map from each node ID to the neighboring node IDs seen in the
            parent permutation.
        """
        edge_map: dict[int, set[int]] = {node_id: set() for node_id in parent_ids}
        for index, node_id in enumerate(parent_ids):
            if index > 0:
                edge_map[node_id].add(parent_ids[index - 1])
            if index < len(parent_ids) - 1:
                edge_map[node_id].add(parent_ids[index + 1])
        return edge_map

    @staticmethod
    def _merge_edge_maps(
        parent1_ids: list[int],
        parent2_ids: list[int],
    ) -> dict[int, set[int]]:
        """Merge adjacency relationships from both parents.

        Args:
            parent1_ids: Parent 1 destination permutation represented by node IDs.
            parent2_ids: Parent 2 destination permutation represented by node IDs.

        Returns:
            A merged edge map containing neighbors from both parents.
        """
        merged_edge_map = EdgeRecombinationCrossoverStrategy._build_edge_map(
            parent1_ids
        )
        second_edge_map = EdgeRecombinationCrossoverStrategy._build_edge_map(
            parent2_ids
        )
        for node_id, neighbors in second_edge_map.items():
            merged_edge_map.setdefault(node_id, set()).update(neighbors)
        return merged_edge_map

    @staticmethod
    def _remove_node_from_edges(
        edge_map: dict[int, set[int]],
        node_id: int,
    ) -> None:
        """Remove a selected node from every neighbor set in the edge map.

        Args:
            edge_map: Mutable adjacency map used during child construction.
            node_id: Node that has just been selected into the child.

        Returns:
            None. The map is updated in place.
        """
        for neighbors in edge_map.values():
            neighbors.discard(node_id)

    def _choose_next_node(
        self,
        current_node_id: int,
        edge_map: dict[int, set[int]],
        remaining_node_ids: set[int],
    ) -> int:
        """Choose the next node using adjacency preservation or safe fallback.

        Args:
            current_node_id: Node most recently appended to the child.
            edge_map: Mutable adjacency map used during child construction.
            remaining_node_ids: Destination node IDs not yet selected.

        Returns:
            The next node ID to append to the child permutation.
        """
        candidate_neighbors = [
            neighbor_id
            for neighbor_id in edge_map.get(current_node_id, set())
            if neighbor_id in remaining_node_ids
        ]
        if candidate_neighbors:
            minimum_degree = min(
                len(edge_map.get(neighbor_id, set()) & remaining_node_ids)
                for neighbor_id in candidate_neighbors
            )
            best_candidates = [
                neighbor_id
                for neighbor_id in candidate_neighbors
                if len(edge_map.get(neighbor_id, set()) & remaining_node_ids)
                == minimum_degree
            ]
            return random.choice(best_candidates)
        return random.choice(sorted(remaining_node_ids))

    def _build_child_destinations(
        self,
        parent1_destinations: list[RouteNode],
        parent2_destinations: list[RouteNode],
    ) -> list[RouteNode]:
        """Build the child destination permutation using edge recombination.

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
        edge_map = self._merge_edge_maps(parent1_ids, parent2_ids)
        remaining_node_ids = set(parent1_ids)
        current_node_id = random.choice(parent1_ids)
        child_ids: list[int] = []

        while remaining_node_ids:
            child_ids.append(current_node_id)
            remaining_node_ids.discard(current_node_id)
            self._remove_node_from_edges(edge_map, current_node_id)
            if not remaining_node_ids:
                break
            current_node_id = self._choose_next_node(
                current_node_id,
                edge_map,
                remaining_node_ids,
            )

        return [node_by_id[node_id] for node_id in child_ids]
