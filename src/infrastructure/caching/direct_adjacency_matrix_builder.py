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
        """Delegate to the existing in-memory adjacency builder."""
        return build_adjacency_matrix(
            route_calculator=route_calculator,
            route_nodes=route_nodes,
            weight_type=weight_type,
            cost_type=cost_type,
        )
