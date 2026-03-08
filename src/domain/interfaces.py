from typing import Protocol, Callable, Any, runtime_checkable
from .models import RouteSegmentsInfo, OptimizationResult, GraphContext


@runtime_checkable
class IGraphGenerator(Protocol):
    def initialize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
    ) -> GraphContext: ...


@runtime_checkable
class IRouteCalculator(Protocol):
    def compute_route_segments_info(
        self,
        route: list,
        weight_function: Any = ...,
        cost_type: str | None = ...,
    ) -> RouteSegmentsInfo: ...

    def get_weight_function(self) -> Callable: ...


@runtime_checkable
class IRouteOptimizer(Protocol):
    def solve(
        self,
        route_nodes: list,
        max_generation: int = ...,
        max_processing_time: int = ...,
    ) -> OptimizationResult: ...


@runtime_checkable
class IPlotter(Protocol):
    def plot(self, route_info: RouteSegmentsInfo) -> None: ...
