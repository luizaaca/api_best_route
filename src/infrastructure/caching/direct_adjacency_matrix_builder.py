"""Adjacency matrix builder that computes segments on-demand without caching."""

from src.domain.interfaces import IAdjacencyMatrixBuilder, IRouteCalculator
from src.domain.models import RouteNode, RouteSegment
from src.infrastructure.route_calculator import build_adjacency_matrix


class DirectAdjacencyMatrixBuilder(IAdjacencyMatrixBuilder):
    """Build an adjacency matrix without persistent caching."""

    def build(
        self,
        route_calculator: IRouteCalculator,
        route_nodes: list[RouteNode],
        weight_type: str = "eta",
        cost_type: str | None = "priority",
    ) -> dict[tuple[int, int], RouteSegment]:
        """Build an adjacency matrix by computing every segment.

        Args:
            route_calculator: Calculator used to compute segments.
            route_nodes: The nodes to include in the adjacency matrix.
            weight_type: The weight strategy for pathfinding.
            cost_type: Optional cost strategy to apply.

        Returns:
            A full adjacency matrix mapping node pairs to RouteSegment objects.
        """
        return build_adjacency_matrix(
            route_calculator=route_calculator,
            route_nodes=route_nodes,
            weight_type=weight_type,
            cost_type=cost_type,
        )
