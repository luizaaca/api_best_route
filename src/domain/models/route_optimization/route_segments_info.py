"""Aggregate information for an ordered sequence of route segments."""

from dataclasses import dataclass, field

from .route_metrics import RouteMetrics
from .route_segment import RouteSegment


@dataclass
class RouteSegmentsInfo(RouteMetrics):
    """Store computed metrics for an ordered sequence of route segments."""

    segments: list[RouteSegment] = field(default_factory=list)

    @classmethod
    def from_segments(cls, segments: list[RouteSegment]) -> "RouteSegmentsInfo":
        """Create an aggregated route info object from a segment list."""
        total_eta = 0.0
        total_length = 0.0
        total_cost = 0.0
        has_cost = False

        for seg in segments:
            total_eta += seg.eta
            total_length += seg.length
            if seg.cost is not None:
                has_cost = True
                total_cost += seg.cost

        return cls(
            segments=segments,
            total_eta=total_eta,
            total_length=total_length,
            total_cost=total_cost if has_cost else None,
        )
