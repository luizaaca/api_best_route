from typing import Protocol, runtime_checkable

from src.domain.models import OptimizationResult, RouteNode


@runtime_checkable
class IRouteOptimizer(Protocol):
    def solve(
        self,
        route_nodes: list[RouteNode],
        max_generation: int = ...,
        max_processing_time: int = ...,
        vehicle_count: int = ...,
    ) -> OptimizationResult: ...
