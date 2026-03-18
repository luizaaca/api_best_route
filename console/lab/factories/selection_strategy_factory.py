"""Factory for constructing selection strategies in console lab mode.

This module keeps benchmark-specific strategy-name resolution inside the
console layer so the API-facing infrastructure package does not expose
lab-only composition helpers.
"""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces import ISelectionStrategy
from src.infrastructure.genetic_algorithm.selection import (
    RankSelectionStrategy,
    RoulleteSelectionStrategy,
    StochasticUniversalSamplingSelectionStrategy,
    TournamentSelectionStrategy,
)


class SelectionStrategyFactory:
    """Create configured selection strategy instances for lab runs."""

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
    ) -> ISelectionStrategy:
        """Create a selection strategy for the provided identifier.

        Args:
            name: Stable strategy identifier used by lab configuration.
            params: Optional strategy-specific parameter mapping.
            logger: Optional verbose logger used for runtime messages.

        Returns:
            A configured selection strategy instance.

        Raises:
            ValueError: If the strategy name is unknown or unsupported params are
                provided.
        """
        normalized_name = name.strip().lower()
        resolved_params = cls._copy_params(params)

        if normalized_name == "roulette":
            emit_ignored_params_message(
                logger,
                "selection strategy",
                normalized_name,
                resolved_params,
            )
            return RoulleteSelectionStrategy()
        if normalized_name == "rank":
            emit_ignored_params_message(
                logger,
                "selection strategy",
                normalized_name,
                resolved_params,
            )
            return RankSelectionStrategy()
        if normalized_name == "sus":
            emit_ignored_params_message(
                logger,
                "selection strategy",
                normalized_name,
                resolved_params,
            )
            return StochasticUniversalSamplingSelectionStrategy()
        if normalized_name == "tournament":
            tournament_size = int(resolved_params.pop("tournament_size", 3))
            emit_ignored_params_message(
                logger,
                "selection strategy",
                normalized_name,
                resolved_params,
            )
            return TournamentSelectionStrategy(tournament_size=tournament_size)
        raise ValueError(f"Unknown selection strategy: {name}")
