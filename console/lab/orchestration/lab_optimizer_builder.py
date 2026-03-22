"""Build configured `TSPGeneticAlgorithm` instances for console lab runs."""

from collections.abc import Callable

from console.lab.models.lab_run_config import LabRunConfig
from console.lab.runtime_logging import emit_runtime_message
from src.infrastructure.genetic_algorithm.factories import AdaptiveRouteGAFamilyFactory
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory


class LabOptimizerBuilder:
    """Build configured optimizer instances for resolved lab run configs."""

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
        ga_family = AdaptiveRouteGAFamilyFactory().create(
            adaptive_config=run_config.state_config.model_dump(mode="python"),
            adjacency_matrix=adjacency_matrix,
            weight_type=run_config.weight_type,
            cost_type=run_config.cost_type,
        )
        emit_runtime_message(
            logger,
            (
                f"Building adaptive optimizer for run '{run_config.label}' with "
                f"initial state '{ga_family.initial_state_name}' and "
                f"{len(run_config.state_config.states)} configured state(s)."
            ),
        )
        return TSPOptimizerFactory.create(
            adjacency_matrix=adjacency_matrix,
            plotter=plotter,
            population_size=run_config.population_size,
            ga_family=ga_family,
            logger=logger,
            optimizer_type=TSPGeneticAlgorithm,
        )
