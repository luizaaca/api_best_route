"""Factory for constructing mutation strategies in console lab mode."""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces.genetic_algorithm.operators.ga_mutation_strategy import (
    IGeneticMutationStrategy,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.infrastructure.genetic_algorithm.builders.component_builders import (
    build_mutation_strategy,
)


class MutationStrategyFactory:
    """Create configured mutation strategy instances for lab runs."""

    @classmethod
    def create(
        cls,
        name: str,
        params: Mapping[str, Any] | None = None,
        logger: RuntimeLogger | None = None,
    ) -> IGeneticMutationStrategy[RouteGeneticSolution]:
        """Create a mutation strategy for the provided identifier.

        Args:
            name: Stable strategy identifier used by lab configuration.
            params: Optional strategy-specific parameter mapping.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured mutation strategy instance.

        Raises:
            ValueError: If the strategy name is unknown or unsupported params are
                provided.
        """
        return build_mutation_strategy(
            name=name,
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
