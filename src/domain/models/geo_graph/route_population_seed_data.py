"""Route-domain seed data used by population generators."""

from __future__ import annotations

from dataclasses import dataclass

from .route_node import RouteNode


@dataclass(slots=True)
class RoutePopulationSeedData:
    """Carry the route-domain seed inputs required by population generators.

    Attributes:
        route_nodes: Ordered route nodes defining the route problem.
        vehicle_count: Number of vehicles available for the optimization.
    """

    route_nodes: list[RouteNode]
    vehicle_count: int
