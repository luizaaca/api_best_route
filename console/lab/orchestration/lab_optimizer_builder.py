"""Build configured `TSPGeneticAlgorithm` instances for console lab runs."""

from collections.abc import Callable

from console.lab.factories import (
    CrossoverStrategyFactory,
    MutationStrategyFactory,
    PopulationGeneratorFactory,
    SelectionStrategyFactory,
)
from console.lab.models.lab_run_config import LabRunConfig
from console.lab.runtime_logging import emit_runtime_message
from src.infrastructure.genetic_algorithm import (
    AdjacencyCostPopulationDistanceStrategy,
    AdjacencyEtaPopulationDistanceStrategy,
    AdjacencyLengthPopulationDistanceStrategy,
    EuclideanPopulationDistanceStrategy,
)
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm


class LabOptimizerBuilder:
    """Build configured optimizer instances for resolved lab run configs."""

    @staticmethod
    def _build_population_distance_strategy(
        adjacency_matrix: AdjacencyMatrix,
        weight_type: str,
        cost_type: str | None,
    ):
        """Return the heuristic distance strategy required by population seeding.

        Args:
            adjacency_matrix: Shared adjacency matrix for the session.
            weight_type: Weight metric used by the route calculator.
            cost_type: Optional cost metric used by the route calculator.

        Returns:
            A heuristic distance strategy instance.
        """
        if cost_type not in (None, "", "none"):
            return AdjacencyCostPopulationDistanceStrategy(adjacency_matrix)
        if weight_type == "length":
            return AdjacencyLengthPopulationDistanceStrategy(adjacency_matrix)
        if weight_type == "eta":
            return AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
        return EuclideanPopulationDistanceStrategy()

    @classmethod
    def build(
        cls,
        run_config: LabRunConfig,
        adjacency_matrix: AdjacencyMatrix,
        plotter=None,
        logger: Callable[[str], None] | None = None,
    ) -> TSPGeneticAlgorithm:
        """Build one optimizer instance for a resolved lab run.

        Args:
            run_config: Fully resolved lab run configuration.
            adjacency_matrix: Shared adjacency matrix for the benchmark session.
            plotter: Optional plotter used when plotting is enabled.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured `TSPGeneticAlgorithm` instance.
        """
        distance_strategy = cls._build_population_distance_strategy(
            adjacency_matrix,
            run_config.weight_type,
            run_config.cost_type,
        )
        emit_runtime_message(
            logger,
            (
                f"Building optimizer for run '{run_config.label}' with "
                f"population generator '{run_config.population_generator.name}', "
                f"selection '{run_config.selection.name}', crossover "
                f"'{run_config.crossover.name}', and mutation "
                f"'{run_config.mutation.name}'."
            ),
        )
        population_generator = PopulationGeneratorFactory.create(
            run_config.population_generator.name,
            distance_strategy=distance_strategy,
            params=run_config.population_generator.params,
            logger=logger,
        )
        selection_strategy = SelectionStrategyFactory.create(
            run_config.selection.name,
            params=run_config.selection.params,
            logger=logger,
        )
        crossover_strategy = CrossoverStrategyFactory.create(
            run_config.crossover.name,
            params=run_config.crossover.params,
            logger=logger,
        )
        mutation_strategy = MutationStrategyFactory.create(
            run_config.mutation.name,
            params=run_config.mutation.params,
            logger=logger,
        )
        return TSPGeneticAlgorithm(
            adjacency_matrix=adjacency_matrix,
            plotter=plotter,
            population_size=run_config.population_size,
            mutation_probability=run_config.mutation_probability,
            selection_strategy=selection_strategy,
            crossover_strategy=crossover_strategy,
            mutation_strategy=mutation_strategy,
            population_generator=population_generator,
            logger=logger,
        )
