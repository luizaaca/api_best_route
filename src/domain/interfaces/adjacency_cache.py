from typing import Protocol, runtime_checkable

from .route_calculator import IRouteCalculator
from src.domain.models import RouteNode, RouteSegment


AdjacencyMatrixMap = dict[tuple[int, int], RouteSegment]


@runtime_checkable
class IAdjacencySegmentCache(Protocol):
    """Persist route segments keyed by graph identity and segment parameters."""

    def get_segment(
        self,
        graph_key: str,
        start_node_id: int,
        end_node_id: int,
        weight_type: str,
        cost_type: str | None,
    ) -> RouteSegment | None: ...

    def set_segment(
        self,
        graph_key: str,
        start_node_id: int,
        end_node_id: int,
        weight_type: str,
        cost_type: str | None,
        segment: RouteSegment,
    ) -> None: ...


@runtime_checkable
class IAdjacencyMatrixBuilder(Protocol):
    """Build an adjacency matrix, optionally reusing cached segments."""

    def build(
        self,
        route_calculator: IRouteCalculator,
        route_nodes: list[RouteNode],
        weight_type: str = "eta",
        cost_type: str | None = "priority",
    ) -> AdjacencyMatrixMap: ...
