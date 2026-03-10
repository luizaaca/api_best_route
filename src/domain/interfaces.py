from typing import Protocol, Callable, Any, runtime_checkable
from .models import (
    RouteSegment,
    RouteSegmentsInfo,
    OptimizationResult,
    GraphContext,
    RouteNode,
)


@runtime_checkable
class IGraphGenerator(Protocol):
    def initialize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
    ) -> GraphContext: ...

    def convert_segments_to_lat_lon(
        self, context: GraphContext, route_segments: RouteSegmentsInfo
    ) -> RouteSegmentsInfo: ...


@runtime_checkable
class IRouteCalculator(Protocol):
    def compute_segment(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
        weight_function: Any = ...,
        cost_function: Any | None = ...,
    ) -> RouteSegment: ...

    def compute_route_segments_info(
        self,
        segments: list[RouteSegment],
    ) -> RouteSegmentsInfo: ...

    def get_weight_function(self) -> Callable: ...

    def get_cost_function(self, cost_type: str) -> Callable: ...


@runtime_checkable
class IRouteOptimizer(Protocol):
    def solve(
        self,
        route_nodes: list,
        max_generation: int = ...,
        max_processing_time: int = ...,
        vehicle_count: int = ...,
    ) -> OptimizationResult: ...


@runtime_checkable
class IPlotter(Protocol):
    def plot(self, route_info: RouteSegmentsInfo) -> None: ...
