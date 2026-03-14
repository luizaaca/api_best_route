"""Domain interface for route optimization solvers.

Optimizers take a set of route waypoints and search for an efficient
assignment of destinations to vehicles under constraints like a maximum number
of generations or total computation time.
"""

from typing import Protocol, runtime_checkable

from src.domain.models import OptimizationResult, RouteNode


@runtime_checkable
class IRouteOptimizer(Protocol):
    """Protocol for optimizing routes using a search-based strategy."""

    def solve(
        self,
        route_nodes: list[RouteNode],
        max_generation: int = ...,
        max_processing_time: int = ...,
        vehicle_count: int = ...,
    ) -> OptimizationResult: ...
    """Find the best routes for the given waypoints.

    Args:
        route_nodes: The list of route nodes that must be visited.
        max_generation: The maximum number of algorithm generations to run.
        max_processing_time: Maximum time in milliseconds to allow for
            optimization.
        vehicle_count: The number of vehicles to split the route across.

    Returns:
        An OptimizationResult containing the best found route and metrics.
    """
