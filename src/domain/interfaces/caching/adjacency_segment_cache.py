"""Domain protocol for caching computed adjacency segments."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models.route_optimization.route_segment import RouteSegment


@runtime_checkable
class IAdjacencySegmentCache(Protocol):
    """Cache computed adjacency segments to reduce recomputation."""

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
            graph_key: Identifier for the graph instance.
            start_node_id: The starting node identifier.
            end_node_id: The ending node identifier.
            weight_type: The type of weight used to compute the segment.
            cost_type: Optional cost adjustment strategy name.

        Returns:
            A cached route segment if present, or None otherwise.
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
            segment: The computed route segment to cache.
        """
        ...
