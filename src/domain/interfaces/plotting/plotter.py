"""Domain interface for visualizing route optimization results."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo


@runtime_checkable
class IPlotter(Protocol):
    """Render a visualization of route information."""

    def plot(self, route_info: FleetRouteInfo) -> None:
        """Render a visualization of the optimized fleet route.

        Args:
            route_info: The fleet route information produced by the optimizer.
        """
        ...
