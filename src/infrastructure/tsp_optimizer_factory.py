"""Shared factory for assembling route-domain genetic optimizers."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.population_generator_legacy import (
    IPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.selection_strategy_legacy import (
    ISelectionStrategy,
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
        mutation_probability: float = 0.5,
        plotter: IPlotter | None = None,
        selection_strategy: ISelectionStrategy | None = None,
        crossover_strategy: ICrossoverStrategy | None = None,
        mutation_strategy: IMutationStrategy | None = None,
        population_generator: IPopulationGenerator | None = None,
        state_controller: IGeneticStateController[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
        ]
        | None = None,
        logger: Callable[[str], None] | None = None,
        optimizer_type: Callable[..., TOptimizer] = TSPGeneticAlgorithm,
    ) -> TOptimizer:
        """Create one route-domain genetic optimizer.

        Args:
            adjacency_matrix: Precomputed adjacency matrix for route evaluation.
            population_size: Number of candidate solutions per generation.
            mutation_probability: Probability of mutating one offspring.
            plotter: Optional runtime plotter.
            selection_strategy: Parent-selection strategy.
            crossover_strategy: Parent-crossover strategy.
            mutation_strategy: Offspring-mutation strategy.
            population_generator: Initial population generator.
            state_controller: Optional adaptive state controller.
            logger: Optional runtime logger.
            optimizer_type: Concrete optimizer class used for construction.

        Returns:
            A configured `TSPGeneticAlgorithm` instance or compatible object
            built by the provided constructor.
        """
        return optimizer_type(
            adjacency_matrix=adjacency_matrix,
            plotter=plotter,
            population_size=population_size,
            mutation_probability=mutation_probability,
            selection_strategy=selection_strategy,
            crossover_strategy=crossover_strategy,
            mutation_strategy=mutation_strategy,
            population_generator=population_generator,
            state_controller=state_controller,
            logger=logger,
        )