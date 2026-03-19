"""Factory for constructing mutation strategies in console lab mode."""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.infrastructure.genetic_algorithm.mutation import (
    InsertionMutationStrategy,
    InversionMutationStrategy,
    SwapAndRedistributeMutationStrategy,
    TwoOptMutationStrategy,
)


class MutationStrategyFactory:
    """Create configured mutation strategy instances for lab runs."""

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
    ) -> IMutationStrategy:
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
        normalized_name = name.strip().lower()
        resolved_params = cls._copy_params(params)
        emit_ignored_params_message(
            logger,
            "mutation strategy",
            normalized_name,
            resolved_params,
        )
        if normalized_name == "swap_redistribute":
            return SwapAndRedistributeMutationStrategy()
        if normalized_name == "inversion":
            return InversionMutationStrategy()
        if normalized_name == "insertion":
            return InsertionMutationStrategy()
        if normalized_name == "two_opt":
            return TwoOptMutationStrategy()
        raise ValueError(f"Unknown mutation strategy: {name}")
