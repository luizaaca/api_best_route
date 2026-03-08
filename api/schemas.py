from typing import List, Union, Optional
from pydantic import BaseModel


class Destination(BaseModel):
    location: Union[str, List[float]]
    priority: int


class RouteItem(BaseModel):
    location: Union[str, List[float]]
    coords: List[float]
    length: float
    eta: float
    cost: Optional[float] = None
    path: List[List[float]]


class RouteTotals(BaseModel):
    total_length: float
    total_eta: float
    total_cost: Optional[float] = None


class OptimizeRouteRequest(BaseModel):
    origin: Union[str, List[float]]
    destinations: List[Destination]
    max_generation: int = 50
    max_processing_time: int = 10000


class OptimizeRouteResponse(BaseModel):
    best_route: List[RouteItem]
    totals: RouteTotals
    best_fitness: float
    population_size: int
    generations_run: int
