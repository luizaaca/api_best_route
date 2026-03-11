from typing import Union, Optional
from pydantic import BaseModel


class Destination(BaseModel):
    location: Union[str, list[float]]
    priority: int


class RouteItem(BaseModel):
    location: Union[str, list[float]]
    coords: list[float]
    length: float
    eta: float
    cost: Optional[float] = None
    path: list[list[float]]


class RouteTotals(BaseModel):
    total_length: float
    total_eta: float
    total_cost: Optional[float] = None


class FleetTotals(BaseModel):
    total_length: float
    min_vehicle_eta: float
    max_vehicle_eta: float
    total_cost: Optional[float] = None


class OptimizeRouteRequest(BaseModel):
    origin: Union[str, list[float]]
    destinations: list[Destination]
    max_generation: int = 50
    max_processing_time: int = 10000
    population_size: int = 10
    vehicle_count: int = 1  # number of vehicles available for routing
    weight_type: str = "eta"
    cost_type: Optional[str] = "priority"


class VehicleRouteResponse(BaseModel):
    vehicle_id: int
    route: list[RouteItem]
    totals: RouteTotals


class OptimizeRouteResponse(BaseModel):
    routes_by_vehicle: list[VehicleRouteResponse]
    totals: FleetTotals
    best_fitness: float
    population_size: int
    generations_run: int
