"""Domain interface for visualizing route optimization results."""

from typing import Protocol, runtime_checkable

from src.domain.models import FleetRouteInfo


@runtime_checkable
class IPlotter(Protocol):
    """Protocol for plotting route information."""

    def plot(self, route_info: FleetRouteInfo) -> None: ...

    """Render a visualization of the optimized fleet route.

    Args:
        route_info: The fleet route information produced by the optimizer.

    Returns:
        None. 
    """
