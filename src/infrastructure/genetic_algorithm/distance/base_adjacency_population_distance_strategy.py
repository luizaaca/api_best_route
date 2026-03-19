"""Heuristic distance strategies that rely on a precomputed adjacency matrix.

These strategies are used to compute heuristic distances for seeding or
ordering the genetic algorithm's initial population.
"""

from src.domain.interfaces.geo_graph.heuristic_distance import (
    IHeuristicDistanceStrategy,
)
from src.domain.models import RouteNode, RouteSegment
from src.infrastructure.route_calculator import AdjacencyMatrix


class BaseAdjacencyPopulationDistanceStrategy(IHeuristicDistanceStrategy):
    """Base class implementing common adjacency matrix lookup behavior."""

    def __init__(self, adjacency_matrix: AdjacencyMatrix):
        """Initialize with a precomputed adjacency matrix.

        Args:
            adjacency_matrix: Mapping of node pairs to RouteSegment objects.
        """
        self._adjacency_matrix = adjacency_matrix

    def _get_segment(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> RouteSegment:
        """Return the precomputed segment between two route nodes.

        Args:
            start_node: The starting node.
            end_node: The ending node.

        Returns:
            A RouteSegment representing the cached route between the two nodes.
        """
        if start_node.node_id == end_node.node_id:
            return RouteSegment(
                start=start_node.node_id,
                end=end_node.node_id,
                eta=0.0,
                length=0.0,
                path=[],
                segment=[start_node.node_id],
                name=end_node.name,
                coords=end_node.coords,
                cost=0.0,
            )
        return self._adjacency_matrix[(start_node.node_id, end_node.node_id)]
