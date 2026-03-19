"""Domain interface for generating and preparing graph contexts.

Graph generators are responsible for translating user-provided origins and
destinations into a graph suitable for route optimization, and for providing
coordinate conversion utilities used by downstream components.
"""

from typing import Callable, Protocol, runtime_checkable

from src.domain.models import GraphContext


@runtime_checkable
class IGraphGenerator(Protocol):
    """Protocol for constructing graph contexts used by route optimizers."""

    def initialize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
    ) -> GraphContext:
        """Initialize and return the graph context for optimization.

        This method should perform any necessary geocoding, graph extraction,
        and preprocessing to create the data structures needed by route
        optimization.

        Args:
            origin: The starting location, either as an address string or a
                (latitude, longitude) tuple.
            destinations: A list of destination entries, each being a tuple
                (location, priority) where location is an address string or a
                (latitude, longitude) tuple.

        Returns:
            A GraphContext containing the prepared graph and route nodes.
        """
        ...

    def build_coordinate_converter(
        self,
        context: GraphContext,
    ) -> Callable[[float, float], tuple[float, float]]:
        """Return a function that converts projected graph coordinates back to
        geographic latitude/longitude.

        Args:
            context: The GraphContext created during initialization.

        Returns:
            A callable accepting (x, y) coordinates in the graph's CRS and
            returning (latitude, longitude).
        """
        ...
