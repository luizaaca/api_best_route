"""Route node model used by graph generation and optimization flows."""

from dataclasses import dataclass


@dataclass
class RouteNode:
    """Represents a resolved point of interest within the graph.

    Attributes:
        name: A human-readable identifier for the location.
        node_id: The underlying graph node identifier.
        coords: The projected graph coordinates (x, y) in the graph CRS.
    """

    name: str
    node_id: int
    coords: tuple[float, float]
