"""Domain model representing the result of a route optimization run."""

from dataclasses import dataclass, field

from .ga_generation_record import GenerationRecord

from .route import FleetRouteInfo


@dataclass
class OptimizationResult:
    """Encapsulates the results and metrics from a genetic algorithm run."""

    best_route: FleetRouteInfo
    best_fitness: float
    population_size: int
    generations_run: int
    generation_records: list[GenerationRecord] = field(default_factory=list)
