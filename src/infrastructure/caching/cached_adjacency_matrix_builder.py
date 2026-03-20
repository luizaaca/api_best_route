"""Adjacency matrix builder that caches computed route segments.

This implementation checks a persistent segment cache before computing a
segment and stores newly computed segments for future reuse.
"""

from src.domain.interfaces.caching.adjacency_segment_cache import IAdjacencySegmentCache
from src.domain.interfaces.geo_graph.route_calculator import IRouteCalculator
from src.domain.interfaces.route_optimization.adjacency_matrix_builder import (
    IAdjacencyMatrixBuilder,
)
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.route_segment import RouteSegment


class CachedAdjacencyMatrixBuilder(IAdjacencyMatrixBuilder):
    """Build adjacency matrices while reusing cached segments when available."""

    def __init__(self, segment_cache: IAdjacencySegmentCache):
        """Store the segment cache used across matrix builds."""
        self._segment_cache = segment_cache

    def build(
        self,
        route_calculator: IRouteCalculator,
        route_nodes: list[RouteNode],
        weight_type: str = "eta",
        cost_type: str | None = "priority",
    ) -> dict[tuple[int, int], RouteSegment]:
        """Build an adjacency matrix while filling and reading the segment cache.

        Each computed segment is cached so subsequent runs can reuse previously
        computed results for the same graph and parameters.

        Args:
            route_calculator: The route calculator used to compute missing segments.
            route_nodes: The nodes to include in the adjacency matrix.
            weight_type: Weighting strategy for path computation.
            cost_type: Optional cost strategy for segment cost adjustments.

        Returns:
            A mapping from (start_node_id, end_node_id) to RouteSegment.
        """
        weight_function = route_calculator.get_weight_function(weight_type)
        cost_function = route_calculator.get_cost_function(cost_type)
        graph_key = route_calculator.graph_id
        matrix: dict[tuple[int, int], RouteSegment] = {}

        for i, from_node in enumerate(route_nodes):
            for j, to_node in enumerate(route_nodes):
                if i == j:
                    continue
                cached_segment = self._segment_cache.get_segment(
                    graph_key,
                    from_node.node_id,
                    to_node.node_id,
                    weight_type,
                    cost_type,
                )
                if cached_segment is not None:
                    matrix[(from_node.node_id, to_node.node_id)] = cached_segment
                    continue

                segment = route_calculator.compute_segment(
                    start_node=from_node,
                    end_node=to_node,
                    weight_function=weight_function,
                    cost_function=cost_function,
                )
                self._segment_cache.set_segment(
                    graph_key,
                    from_node.node_id,
                    to_node.node_id,
                    weight_type,
                    cost_type,
                    segment,
                )
                matrix[(from_node.node_id, to_node.node_id)] = segment

        return matrix
