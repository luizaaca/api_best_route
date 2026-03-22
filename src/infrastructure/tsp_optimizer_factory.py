"""Shared factory for assembling route-domain execution bundles."""

from __future__ import annotations

from src.domain.models.genetic_algorithm.engine.adaptive_ga_family import (
    AdaptiveGAFamily,
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
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.route_ga_execution_bundle import (
    RouteGAExecutionBundle,
)
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_genetic_problem import TSPGeneticProblem


class TSPOptimizerFactory:
    """Assemble route-domain execution bundles from resolved collaborators.

    This factory centralizes route-problem composition so API, console, and lab
    entrypoints can share the same bundle-building seam while still resolving
    their own collaborators independently.
    """

    @staticmethod
    def create_execution_bundle(
        adjacency_matrix: AdjacencyMatrix,
        route_nodes: list[RouteNode],
        vehicle_count: int,
        population_size: int = 10,
        ga_family: (
            AdaptiveGAFamily[
                RouteGeneticSolution,
                EvaluatedRouteSolution,
                RoutePopulationSeedData,
            ]
            | None
        ) = None,
    ) -> RouteGAExecutionBundle:
        """Create one route execution bundle bound to concrete run inputs.

        Args:
            adjacency_matrix: Precomputed adjacency matrix for route evaluation.
            route_nodes: Ordered nodes that define the concrete route problem.
            vehicle_count: Number of vehicles available for this run.
            population_size: Number of candidate solutions per generation.
            ga_family: Adaptive route GA family resolved from configuration.

        Returns:
            A bound route-domain execution bundle ready for the generic runner.

        Raises:
            ValueError: If the adaptive family is not provided.
        """
        if ga_family is None:
            raise ValueError("ga_family is required")

        problem = TSPGeneticProblem(adjacency_matrix)
        return RouteGAExecutionBundle(
            problem=problem,
            seed_data=problem.build_seed_data(route_nodes, vehicle_count),
            state_controller=ga_family.state_controller,
            population_size=population_size,
        )
