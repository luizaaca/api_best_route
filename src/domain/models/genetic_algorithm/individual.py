"""Type alias for one genetic individual composed of vehicle routes."""

from .vehicle_route import VehicleRoute


Individual = list[VehicleRoute]
