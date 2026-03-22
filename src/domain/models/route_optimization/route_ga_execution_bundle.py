"""Route-domain execution bundle for one configured GA run."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.ga_problem import IGeneticProblem
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.domain.models.route_optimization.optimization_result import OptimizationResult


@dataclass(slots=True)
class RouteGAExecutionBundle:
    """Group the fully bound collaborators required for one route GA run.

    Attributes:
        problem: Concrete route-domain problem used by the generic GA.
        seed_data: Bound route seed payload for one optimization run.
        state_controller: Adaptive controller resolved from the active config.
        population_size: Number of individuals maintained during execution.
    """

    problem: IGeneticProblem[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        OptimizationResult,
    ]
    seed_data: RoutePopulationSeedData
    state_controller: IGeneticStateController[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        RoutePopulationSeedData,
    ]
    population_size: int
