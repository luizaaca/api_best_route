"""Domain interface for route optimization solvers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.optimization_result import OptimizationResult


@runtime_checkable
class IRouteOptimizer(Protocol):
    """Optimize routes using a search-based strategy."""

    def solve(
        self,
        route_nodes: list[RouteNode],
        max_generation: int = ...,
        max_processing_time: int = ...,
        vehicle_count: int = ...,
    ) -> OptimizationResult:
        """Find the best routes for the given waypoints.

        Args:
            route_nodes: The list of route nodes that must be visited.
            max_generation: The maximum number of algorithm generations to run.
            max_processing_time: Maximum time in milliseconds to allow for optimization.
            vehicle_count: The number of vehicles to split the route across.

        Returns:
            An optimization result containing the best found route and metrics.
        """
        ...
