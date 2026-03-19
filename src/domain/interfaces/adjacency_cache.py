from typing import Protocol, runtime_checkable

from .route_calculator import IRouteCalculator
from src.domain.models import AdjacencyMatrixMap, RouteNode, RouteSegment


@runtime_checkable
class IAdjacencySegmentCache(Protocol):
    """Protocol for caching computed adjacency segments to reduce recomputation."""

    def get_segment(
        self,
        graph_key: str,
        start_node_id: int,
        end_node_id: int,
        weight_type: str,
        cost_type: str | None,
    ) -> RouteSegment | None:
        """Attempt to retrieve a cached segment for the given parameters.

        Args:
            graph_key: Identifier for the graph instance (e.g., a hash of the
                graph structure).
            start_node_id: The starting node identifier.
            end_node_id: The ending node identifier.
            weight_type: The type of weight used to compute the segment.
            cost_type: Optional cost adjustment strategy name.

        Returns:
            A cached RouteSegment if present, or None otherwise.
        """
        ...

    def set_segment(
        self,
        graph_key: str,
        start_node_id: int,
        end_node_id: int,
        weight_type: str,
        cost_type: str | None,
        segment: RouteSegment,
    ) -> None:
        """Cache a computed segment for later reuse.

        Args:
            graph_key: Identifier for the graph instance.
            start_node_id: The starting node identifier.
            end_node_id: The ending node identifier.
            weight_type: The type of weight used to compute the segment.
            cost_type: Optional cost adjustment strategy name.
            segment: The computed RouteSegment to cache.
        """
        ...


@runtime_checkable
class IAdjacencyMatrixBuilder(Protocol):
    """Protocol for building or loading an adjacency matrix of route segments."""

    def build(
        self,
        route_calculator: IRouteCalculator,
        route_nodes: list[RouteNode],
        weight_type: str = "eta",
        cost_type: str | None = "priority",
    ) -> AdjacencyMatrixMap:
        """Build an adjacency matrix for a set of route nodes.

        Implementations may reuse previously cached adjacency segments to avoid
        expensive recomputation.

        Args:
            route_calculator: The calculator used to compute individual segments.
            route_nodes: The list of nodes for which to compute adjacency.
            weight_type: The type of weight to use when computing distances.
            cost_type: Optional cost strategy for segment cost adjustments.

        Returns:
            An AdjacencyMatrixMap mapping node pairs to computed RouteSegments.
        """
        ...
