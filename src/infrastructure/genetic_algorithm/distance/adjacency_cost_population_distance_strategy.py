"""Heuristic distance strategy using precomputed adjacency segment cost."""

from src.domain.models import RouteNode

from .base_adjacency_population_distance_strategy import (
    BaseAdjacencyPopulationDistanceStrategy,
)


class AdjacencyCostPopulationDistanceStrategy(BaseAdjacencyPopulationDistanceStrategy):
    """Strategy that returns the stored cost value from the adjacency matrix."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float | None:
        """Return the precomputed segment cost between two nodes.

        Args:
            start_node: The start node.
            end_node: The end node.

        Returns:
            The cost value for the segment, or None if no cost is defined.
        """
        segment = self._get_segment(start_node, end_node)
        return float(segment.cost) if segment.cost is not None else None
