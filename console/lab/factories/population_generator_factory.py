"""Factory for constructing population generators in console lab mode."""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.interfaces.geo_graph.heuristic_distance import (
    IHeuristicDistanceStrategy,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.infrastructure.genetic_algorithm.builders.component_builders import (
    build_population_generator,
)


class PopulationGeneratorFactory:
    """Create configured population generators for lab runs."""

    @classmethod
    def create(
        cls,
        name: str,
        distance_strategy: IHeuristicDistanceStrategy,
        params: Mapping[str, Any] | None = None,
        logger: RuntimeLogger | None = None,
    ) -> IGeneticPopulationGenerator[RoutePopulationSeedData, RouteGeneticSolution]:
        """Create a population generator for the provided identifier.

        Args:
            name: Stable generator identifier used by lab configuration.
            distance_strategy: Heuristic distance strategy used by heuristic-based
                generators.
            params: Optional generator-specific parameter mapping.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured population generator instance.

        Raises:
            ValueError: If the generator name is unknown or unsupported params are
                provided.
        """
        return build_population_generator(
            name=name,
            distance_strategy=distance_strategy,
            params=params,
            ignored_params_reporter=lambda kind, normalized_name, ignored_params: (
                emit_ignored_params_message(
                    logger,
                    kind,
                    normalized_name,
                    ignored_params,
                )
            ),
        )
