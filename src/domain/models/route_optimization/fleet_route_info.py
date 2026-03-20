"""Fleet-wide aggregated route result model."""

from dataclasses import dataclass, field

from .route_metrics import RouteMetrics
from .vehicle_route_info import VehicleRouteInfo


@dataclass
class FleetRouteInfo(RouteMetrics):
    """Aggregate optimization results across all vehicles."""

    routes_by_vehicle: list[VehicleRouteInfo] = field(default_factory=list)
    min_vehicle_eta: float = 0.0
    max_vehicle_eta: float = 0.0

    @classmethod
    def from_vehicle_routes(
        cls,
        routes_by_vehicle: list[VehicleRouteInfo],
    ) -> "FleetRouteInfo":
        """Create a fleet result by aggregating all vehicle routes."""
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
