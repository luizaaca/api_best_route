"""Domain protocol for building adjacency matrices of route segments."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import AdjacencyMatrixMap, RouteNode
from src.domain.interfaces.geo_graph.route_calculator import IRouteCalculator


@runtime_checkable
class IAdjacencyMatrixBuilder(Protocol):
    """Build or load an adjacency matrix of route segments."""

    def build(
        self,
        route_calculator: IRouteCalculator,
        route_nodes: list[RouteNode],
        weight_type: str = "eta",
        cost_type: str | None = "priority",
    ) -> AdjacencyMatrixMap:
        """Build an adjacency matrix for a set of route nodes.

        Implementations may reuse previously cached adjacency segments to avoid
        expensive recomputation.

        Args:
            route_calculator: The calculator used to compute individual segments.
            route_nodes: The list of nodes for which to compute adjacency.
            weight_type: The type of weight to use when computing distances.
            cost_type: Optional cost strategy for segment cost adjustments.

        Returns:
            An adjacency matrix mapping node pairs to computed route segments.
        """
        ...
