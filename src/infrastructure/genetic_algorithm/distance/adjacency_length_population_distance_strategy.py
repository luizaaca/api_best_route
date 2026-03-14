"""Heuristic distance strategy using precomputed adjacency segment length."""

from src.domain.models import RouteNode

from .base_adjacency_population_distance_strategy import (
    BaseAdjacencyPopulationDistanceStrategy,
)


class AdjacencyLengthPopulationDistanceStrategy(
    BaseAdjacencyPopulationDistanceStrategy
):
    """Strategy that returns the stored segment length from the adjacency matrix."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float:
        """Return the precomputed segment length between two nodes.

        Args:
            start_node: The start node.
            end_node: The end node.

        Returns:
            The length (in meters) of the precomputed segment.
        """
        return self._get_segment(start_node, end_node).length
