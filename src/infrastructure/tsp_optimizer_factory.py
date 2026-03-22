"""Shared factory for assembling route-domain genetic optimizers."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from src.domain.models.genetic_algorithm.engine.adaptive_ga_family import (
    AdaptiveGAFamily,
)
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.interfaces.plotting.plotter import IPlotter
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm

TOptimizer = TypeVar("TOptimizer")


class TSPOptimizerFactory:
    """Assemble `TSPGeneticAlgorithm` instances from resolved collaborators.

    This factory centralizes route-optimizer construction so API, console, and
    lab entrypoints can share the same composition seam while still resolving
    their own collaborators independently.
    """

    @staticmethod
    def create(
        adjacency_matrix: AdjacencyMatrix,
        population_size: int = 10,
        ga_family: AdaptiveGAFamily[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
        ]
        | None = None,
        plotter: IPlotter | None = None,
        logger: Callable[[str], None] | None = None,
        optimizer_type: Callable[..., TOptimizer] = TSPGeneticAlgorithm,
    ) -> TOptimizer:
        """Create one route-domain genetic optimizer.

        Args:
            adjacency_matrix: Precomputed adjacency matrix for route evaluation.
            population_size: Number of candidate solutions per generation.
            ga_family: Adaptive route GA family resolved from configuration.
            plotter: Optional runtime plotter.
            logger: Optional runtime logger.
            optimizer_type: Concrete optimizer class used for construction.

        Returns:
            A configured `TSPGeneticAlgorithm` instance or compatible object
            built by the provided constructor.
        """
        if ga_family is None:
            raise ValueError("ga_family is required")
        return optimizer_type(
            adjacency_matrix=adjacency_matrix,
            plotter=plotter,
            population_size=population_size,
            state_controller=ga_family.state_controller,
            logger=logger,
        )