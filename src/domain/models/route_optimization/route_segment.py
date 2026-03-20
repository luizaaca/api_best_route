"""Route segment model representing a computed path between nodes."""

from dataclasses import dataclass


@dataclass
class RouteSegment:
    """Represent a single computed segment between two graph nodes."""

    start: int
    end: int
    eta: float
    length: float
    path: list[tuple[float, float]]
    segment: list[int]
    name: str
    coords: tuple[float, float]
    cost: float | None = None
