"""Factory for constructing crossover strategies in console lab mode."""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.infrastructure.genetic_algorithm.crossover import (
    CycleCrossoverStrategy,
    EdgeRecombinationCrossoverStrategy,
    OrderCrossoverStrategy,
    PartiallyMappedCrossoverStrategy,
)


class CrossoverStrategyFactory:
    """Create configured crossover strategy instances for lab runs."""

    @staticmethod
    def _copy_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
        """Return a shallow mutable copy of the provided parameter mapping.

        Args:
            params: Optional parameter mapping supplied by the caller.

        Returns:
            A mutable dictionary containing the provided parameters.
        """
        return dict(params or {})

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
        normalized_name = name.strip().lower()
        resolved_params = cls._copy_params(params)
        emit_ignored_params_message(
            logger,
            "crossover strategy",
            normalized_name,
            resolved_params,
        )
        if normalized_name == "order":
            return OrderCrossoverStrategy()
        if normalized_name == "pmx":
            return PartiallyMappedCrossoverStrategy()
        if normalized_name == "cycle":
            return CycleCrossoverStrategy()
        if normalized_name == "edge_recombination":
            return EdgeRecombinationCrossoverStrategy()
        raise ValueError(f"Unknown crossover strategy: {name}")
