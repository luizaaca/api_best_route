from dataclasses import dataclass, field


@dataclass
class RouteSegment:
    """Typed representation of a single computed route segment between two graph nodes."""

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
        """Build aggregate metrics from an ordered list of route segments."""
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
        """Promote generic route metrics to a vehicle-specific route result."""
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
        """Aggregate metrics across all vehicle routes in the fleet result."""
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
