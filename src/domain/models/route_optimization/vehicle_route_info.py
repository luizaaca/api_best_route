"""Vehicle-specific route result model."""

from dataclasses import dataclass

from .route_segments_info import RouteSegmentsInfo


@dataclass
class VehicleRouteInfo(RouteSegmentsInfo):
    """Represent route results assigned to a specific vehicle."""

    vehicle_id: int = 0

    @classmethod
    def from_route_segments_info(
        cls,
        vehicle_id: int,
        route_info: RouteSegmentsInfo,
    ) -> "VehicleRouteInfo":
        """Create a vehicle route result from generic route metrics."""
        return cls(
            vehicle_id=vehicle_id,
            segments=route_info.segments,
            total_eta=route_info.total_eta,
            total_length=route_info.total_length,
            total_cost=route_info.total_cost,
        )
