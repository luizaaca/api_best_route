"""Heuristic distance strategy using precomputed adjacency segment ETA."""

from src.domain.models import RouteNode

from .base_adjacency_population_distance_strategy import (
    BaseAdjacencyPopulationDistanceStrategy,
)


class AdjacencyEtaPopulationDistanceStrategy(BaseAdjacencyPopulationDistanceStrategy):
    """Strategy that returns the stored ETA value from the adjacency matrix."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float:
        """Return the precomputed segment ETA between two nodes.

        Args:
            start_node: The start node.
            end_node: The end node.

        Returns:
            The estimated time of arrival in seconds for the segment.
        """
        return self._get_segment(start_node, end_node).eta
