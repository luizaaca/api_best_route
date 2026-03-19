"""Domain interfaces for calculating and optimizing mixed-route costs.

This module declares the protocol for route calculators used by the
application to compute segment-level metrics (ETA, distance, cost) between
graph nodes and aggregate them.

Implementations are responsible for translating graph metadata into
route performance estimates and exposing a consistent set of methods for the
optimizers to consume.
"""

from typing import Any, Callable, Protocol, runtime_checkable

from src.domain.models import RouteNode, RouteSegment, RouteSegmentsInfo


@runtime_checkable
class IRouteCalculator(Protocol):
    """Protocol for computing route segments and aggregating route metrics.

    Implementations must be able to compute the best segment between two graph
    nodes given a weight function, aggregate a list of computed segments into
    high-level totals, and provide factory functions for weight and cost
    calculation.
    """

    @property
    def graph_id(self) -> str:
        """Returns a deterministic identifier for the underlying graph.

        This identifier may be used for caching or deduplication of computed
        adjacency matrices.
        """
        ...

    def compute_segment(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
        weight_function: Any = ...,
        cost_function: Any | None = ...,
    ) -> RouteSegment:
        """Compute a route segment between two nodes.

        Args:
            start_node: The graph node where the segment begins.
            end_node: The graph node where the segment ends.
            weight_function: A callable used by the underlying graph search
                algorithm to weight edges (e.g., ETA, distance).
            cost_function: Optional callable to compute a secondary cost
                (e.g., priority-adjusted ETA) for the segment.

        Returns:
            A RouteSegment containing traversal metrics, path coordinates, and
            optional cost metadata.
        """
        ...

    def compute_route_segments_info(
        self,
        segments: list[RouteSegment],
    ) -> RouteSegmentsInfo:
        """Aggregate a list of precomputed segments into fleet-level totals.

        Args:
            segments: A list of RouteSegment instances typically produced by
                compute_segment().

        Returns:
            A RouteSegmentsInfo instance containing total ETA, length, and any
            computed cost aggregate.
        """
        ...

    def get_weight_function(self, weight_type: str) -> Callable:
        """Return a weight function suitable for networkx shortest-path
        algorithms.

        The returned callable should match the signature expected by
        networkx shortest-path functions (u, v, edge_data) and return a numeric
        weight.

        Args:
            weight_type: A string key indicating the type of weight to compute.

        Returns:
            A callable to be passed as the `weight` argument into networkx's
            shortest path functions.
        """
        ...

    def get_cost_function(self, cost_type: str | None) -> Callable | None:
        """Return a cost function to adjust segment costs based on custom
        business rules.

        Args:
            cost_type: The identifier for the desired cost strategy.

        Returns:
            A callable taking (node_id, eta) and returning a cost, or None if
            no additional cost should be applied.
        """
        ...
