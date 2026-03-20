"""Domain model representing the result of a route optimization run."""

from dataclasses import dataclass, field

from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)

from .fleet_route_info import FleetRouteInfo


@dataclass
class OptimizationResult:
    """Encapsulate the results and metrics from a genetic algorithm run."""

    best_route: FleetRouteInfo
    best_fitness: float
    population_size: int
    generations_run: int
    generation_records: list[GenerationRecord] = field(default_factory=list)
