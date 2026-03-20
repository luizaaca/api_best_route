"""Domain interfaces for calculating and aggregating route costs."""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable

from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.route_segments_info import RouteSegmentsInfo


@runtime_checkable
class IRouteCalculator(Protocol):
    """Compute route segments and aggregate route metrics."""

    @property
    def graph_id(self) -> str:
        """Return a deterministic identifier for the underlying graph."""
        ...

    def compute_segment(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
        weight_function: Any = ...,
        cost_function: Any | None = ...,
    ) -> RouteSegment:
        """Compute a route segment between two nodes."""
        ...

    def compute_route_segments_info(
        self,
        segments: list[RouteSegment],
    ) -> RouteSegmentsInfo:
        """Aggregate a list of precomputed segments into route totals."""
        ...

    def get_weight_function(self, weight_type: str) -> Callable:
        """Return a weight function suitable for shortest-path algorithms."""
        ...

    def get_cost_function(self, cost_type: str | None) -> Callable | None:
        """Return a cost function to adjust segment costs."""
        ...
