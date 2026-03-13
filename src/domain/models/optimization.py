from dataclasses import dataclass

from .route import FleetRouteInfo


@dataclass
class OptimizationResult:
    """The output of a single optimization run."""

    best_route: FleetRouteInfo
    best_fitness: float
    population_size: int
    generations_run: int
