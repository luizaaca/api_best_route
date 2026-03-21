"""Build configured `TSPGeneticAlgorithm` instances for console lab runs."""

from collections.abc import Callable

from console.lab.models.lab_run_config import LabRunConfig
from console.lab.runtime_logging import emit_runtime_message
from src.infrastructure.genetic_algorithm.builders import (
    build_crossover_strategy,
    build_mutation_strategy,
    build_population_generator,
    build_route_adaptive_state_controller,
    build_selection_strategy,
)
from src.infrastructure.genetic_algorithm.builders.distance_strategy_builder import (
    build_population_distance_strategy,
)
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory


class LabOptimizerBuilder:
    """Build configured optimizer instances for resolved lab run configs."""

    @staticmethod
    def _find_initial_state(run_config: LabRunConfig):
        """Return the configured initial state declared for the run."""
        for state in run_config.state_config.states:
            if state.name == run_config.state_config.initial_state:
                return state
        raise ValueError(
            f"Unknown initial state '{run_config.state_config.initial_state}'"
        )

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
        return build_population_distance_strategy(
            adjacency_matrix,
            weight_type,
            cost_type,
        )

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
        initial_state = cls._find_initial_state(run_config)
        emit_runtime_message(
            logger,
            (
                f"Building stateful optimizer for run '{run_config.label}' with "
                f"initial state '{run_config.state_config.initial_state}' and "
                f"{len(run_config.state_config.states)} configured state(s)."
            ),
        )
        population_generator = build_population_generator(
            (
                initial_state.population_generator.name
                if initial_state.population_generator is not None
                else "hybrid"
            ),
            distance_strategy=distance_strategy,
            params=(
                initial_state.population_generator.params
                if initial_state.population_generator is not None
                else None
            ),
        )
        selection_strategy = build_selection_strategy(
            initial_state.selection.name,
            params=initial_state.selection.params,
        )
        crossover_strategy = build_crossover_strategy(
            initial_state.crossover.name,
            params=initial_state.crossover.params,
        )
        mutation_strategy = build_mutation_strategy(
            initial_state.mutation.name,
            params=initial_state.mutation.params,
        )
        state_controller = build_route_adaptive_state_controller(
            adaptive_config=run_config.state_config.model_dump(mode="python"),
            adjacency_matrix=adjacency_matrix,
            weight_type=run_config.weight_type,
            cost_type=run_config.cost_type,
        )
        return TSPOptimizerFactory.create(
            adjacency_matrix=adjacency_matrix,
            plotter=plotter,
            population_size=run_config.population_size,
            mutation_probability=initial_state.mutation_probability,
            selection_strategy=selection_strategy,
            crossover_strategy=crossover_strategy,
            mutation_strategy=mutation_strategy,
            population_generator=population_generator,
            state_controller=state_controller,
            logger=logger,
            optimizer_type=TSPGeneticAlgorithm,
        )
