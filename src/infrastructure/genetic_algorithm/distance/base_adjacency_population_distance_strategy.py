from src.domain.interfaces import IHeuristicDistanceStrategy
from src.domain.models import RouteNode, RouteSegment
from src.infrastructure.route_calculator import AdjacencyMatrix


class BaseAdjacencyPopulationDistanceStrategy(IHeuristicDistanceStrategy):
    """Read heuristic distances from a precomputed adjacency matrix."""

    def __init__(self, adjacency_matrix: AdjacencyMatrix):
        """Store the adjacency matrix used during heuristic ordering."""
        self._adjacency_matrix = adjacency_matrix

    def _get_segment(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> RouteSegment:
        """Return the precomputed segment between two route nodes."""
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
