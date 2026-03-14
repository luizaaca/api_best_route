"""Domain model representing the result of a route optimization run."""

from dataclasses import dataclass

from .route import FleetRouteInfo


@dataclass
class OptimizationResult:
    """Encapsulates the results and metrics from a genetic algorithm run."""

    best_route: FleetRouteInfo
    best_fitness: float
    population_size: int
    generations_run: int
