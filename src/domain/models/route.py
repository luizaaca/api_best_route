"""Domain models representing computed route segments and aggregated route metrics.

This module defines the data transfer objects (DTOs) used by the optimization service
and the genetic algorithm to capture route distances, timings, costs, and the
structure of multi-vehicle fleet routes.
"""

from dataclasses import dataclass, field


@dataclass
class RouteSegment:
    """Represents a single computed segment between two graph nodes.

    Attributes:
        start: The starting graph node identifier.
        end: The ending graph node identifier.
        eta: Estimated time of arrival in seconds.
        length: The segment length in meters.
        path: A list of (latitude, longitude) points representing the route.
        segment: The sequence of graph node IDs traversed.
        name: A human-readable name for the end node (typically the destination label).
        coords: The projected graph coordinates (x, y) for the end node.
        cost: Optional computed cost (e.g., priority-adjusted ETA).
    """

    start: int
    end: int
    eta: float
    length: float
    path: list[tuple[float, float]]
    segment: list[int]
    name: str
    coords: tuple[float, float]
    cost: float | None = None


@dataclass
class RouteMetrics:
    """Shared aggregate totals for route-level and fleet-level results."""

    total_eta: float = 0.0
    total_length: float = 0.0
    total_cost: float | None = None


@dataclass
class RouteSegmentsInfo(RouteMetrics):
    """Stores computed metrics for an ordered sequence of route segments."""

    segments: list[RouteSegment] = field(default_factory=list)

    @classmethod
    def from_segments(cls, segments: list[RouteSegment]) -> "RouteSegmentsInfo":
        """Create a RouteSegmentsInfo instance from a list of segments.

        This helper computes aggregate metrics (total ETA, total length, and
        optionally total cost) across all segments.

        Args:
            segments: An ordered list of RouteSegment instances.

        Returns:
            A RouteSegmentsInfo containing the original segments and computed
            aggregate totals.
        """
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


@dataclass
class VehicleRouteInfo(RouteSegmentsInfo):
    """Route result assigned to a specific vehicle."""

    vehicle_id: int = 0

    @classmethod
    def from_route_segments_info(
        cls,
        vehicle_id: int,
        route_info: RouteSegmentsInfo,
    ) -> "VehicleRouteInfo":
        """Create a vehicle-specific route result from generic route metrics.

        Args:
            vehicle_id: The identifier of the vehicle assigned to the route.
            route_info: A RouteSegmentsInfo instance containing segment-level
                metrics for the vehicle’s route.

        Returns:
            A VehicleRouteInfo containing the same segment data and aggregated
            totals, annotated with the vehicle identifier.
        """
        return cls(
            vehicle_id=vehicle_id,
            segments=route_info.segments,
            total_eta=route_info.total_eta,
            total_length=route_info.total_length,
            total_cost=route_info.total_cost,
        )


@dataclass
class FleetRouteInfo(RouteMetrics):
    """Aggregated optimization result across all vehicles."""

    routes_by_vehicle: list[VehicleRouteInfo] = field(default_factory=list)
    min_vehicle_eta: float = 0.0
    max_vehicle_eta: float = 0.0

    @classmethod
    def from_vehicle_routes(
        cls,
        routes_by_vehicle: list[VehicleRouteInfo],
    ) -> "FleetRouteInfo":
        """Create a FleetRouteInfo by aggregating metrics across all vehicles.

        Args:
            routes_by_vehicle: A list of VehicleRouteInfo objects, one per vehicle.

        Returns:
            A FleetRouteInfo containing the combined totals, including min/max
            per-vehicle ETA and optional aggregated cost.
        """
        total_length = sum(route.total_length for route in routes_by_vehicle)
        vehicle_etas = [route.total_eta for route in routes_by_vehicle]
        total_cost_values = [
            route.total_cost
            for route in routes_by_vehicle
            if route.total_cost is not None
        ]
        total_cost = sum(total_cost_values) if total_cost_values else None
        return cls(
            routes_by_vehicle=routes_by_vehicle,
            total_length=total_length,
            total_cost=total_cost,
            min_vehicle_eta=min(vehicle_etas, default=0.0),
            max_vehicle_eta=max(vehicle_etas, default=0.0),
        )
