from typing import Protocol, runtime_checkable

from src.domain.models import RouteNode


@runtime_checkable
class IHeuristicDistanceStrategy(Protocol):
    """Resolve heuristic population distances between two route nodes."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float: ...
