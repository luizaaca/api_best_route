from typing import Any, Callable, Protocol, runtime_checkable

from src.domain.models import RouteNode, RouteSegment, RouteSegmentsInfo


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

    def get_weight_function(self, weight_type: str) -> Callable: ...

    def get_cost_function(self, cost_type: str | None) -> Callable | None: ...
