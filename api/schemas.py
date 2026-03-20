"""Pydantic request and response schemas for the route optimization API."""

from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class Destination(BaseModel):
    """Represents a destination waypoint in the optimization request."""

    location: Union[str, list[float]]
    priority: int


class RouteItem(BaseModel):
    """Represents a single route segment in the API response."""

    location: Union[str, list[float]]
    coords: list[float]
    length: float
    eta: float
    cost: Optional[float] = None
    path: list[list[float]]


class RouteTotals(BaseModel):
    """Aggregate metrics for a single vehicle route."""

    total_length: float
    total_eta: float
    total_cost: Optional[float] = None


class FleetTotals(BaseModel):
    """Aggregate metrics across all vehicles in the optimized fleet."""

    total_length: float
    min_vehicle_eta: float
    max_vehicle_eta: float
    total_cost: Optional[float] = None


class OptimizeRouteRequest(BaseModel):
    """Request payload for route optimization."""

    origin: Union[str, list[float]]
    destinations: list[Destination]
    max_generation: int = 50
    max_processing_time: int = 10000
    population_size: int = 10
    vehicle_count: int = 1  # number of vehicles available for routing
    weight_type: str = "eta"
    cost_type: Optional[str] = "priority"


class VehicleRouteResponse(BaseModel):
    """Response payload for a single vehicle's route."""

    vehicle_id: int
    route: list[RouteItem]
    totals: RouteTotals


class OptimizeRouteResponse(BaseModel):
    """Response payload returned from the optimize_route endpoint."""

    routes_by_vehicle: list[VehicleRouteResponse]
    totals: FleetTotals
    best_fitness: float
    population_size: int
    generations_run: int
