"""Build configured route execution bundles for console lab runs."""

from collections.abc import Callable

from console.lab.models.lab_run_config import LabRunConfig
from console.lab.runtime_logging import emit_runtime_message
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.route_ga_execution_bundle import (
    RouteGAExecutionBundle,
)
from src.infrastructure.genetic_algorithm.factories import AdaptiveRouteGAFamilyFactory
from src.infrastructure.route_calculator import AdjacencyMatrix
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory


class LabOptimizerBuilder:
    """Build configured execution bundles for resolved lab run configs."""

    @classmethod
    def build(
        cls,
        run_config: LabRunConfig,
        adjacency_matrix: AdjacencyMatrix,
        route_nodes: list[RouteNode],
        logger: Callable[[str], None] | None = None,
    ) -> RouteGAExecutionBundle:
        """Build one execution bundle for a resolved lab run.

        Args:
            run_config: Fully resolved lab run configuration.
            adjacency_matrix: Shared adjacency matrix for the benchmark session.
            route_nodes: Shared route nodes resolved for the benchmark session.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured route execution bundle.
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
                f"Building adaptive execution bundle for run '{run_config.label}' with "
                f"initial state '{ga_family.initial_state_name}' and "
                f"{len(run_config.state_config.states)} configured state(s)."
            ),
        )
        return TSPOptimizerFactory.create_execution_bundle(
            adjacency_matrix=adjacency_matrix,
            route_nodes=route_nodes,
            vehicle_count=run_config.vehicle_count,
            population_size=run_config.population_size,
            ga_family=ga_family,
        )
