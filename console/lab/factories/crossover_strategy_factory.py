"""Factory for constructing crossover strategies in console lab mode."""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.infrastructure.genetic_algorithm.builders.legacy_component_builders import (
    build_legacy_crossover_strategy,
)


class CrossoverStrategyFactory:
    """Create configured crossover strategy instances for lab runs."""

    @classmethod
    def create(
        cls,
        name: str,
        params: Mapping[str, Any] | None = None,
        logger: RuntimeLogger | None = None,
    ) -> ICrossoverStrategy:
        """Create a crossover strategy for the provided identifier.

        Args:
            name: Stable strategy identifier used by lab configuration.
            params: Optional strategy-specific parameter mapping.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured crossover strategy instance.

        Raises:
            ValueError: If the strategy name is unknown or unsupported params are
                provided.
        """
        return build_legacy_crossover_strategy(
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
