from typing import Protocol, runtime_checkable

from src.domain.models import FleetRouteInfo


@runtime_checkable
class IPlotter(Protocol):
    def plot(self, route_info: FleetRouteInfo) -> None: ...
