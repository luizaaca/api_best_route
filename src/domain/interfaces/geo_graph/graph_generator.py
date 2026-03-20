"""Domain interface for generating and preparing graph contexts.

Graph generators are responsible for translating user-provided origins and
Destinations into a graph suitable for route optimization, and for providing
coordinate conversion utilities used by downstream components.
"""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from src.domain.models.geo_graph.graph_context import GraphContext


@runtime_checkable
class IGraphGenerator(Protocol):
    """Construct graph contexts used by route optimizers."""

    def initialize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
    ) -> GraphContext:
        """Initialize and return the graph context for optimization."""
        ...

    def build_coordinate_converter(
        self,
        context: GraphContext,
    ) -> Callable[[float, float], tuple[float, float]]:
        """Return a converter from projected graph coordinates to lat/lon."""
        ...
