"""Factory for constructing selection strategies in console lab mode.

This module keeps benchmark-specific strategy-name resolution inside the
console layer so the API-facing infrastructure package does not expose
lab-only composition helpers.
"""

from collections.abc import Mapping
from typing import Any

from console.lab.runtime_logging import RuntimeLogger, emit_ignored_params_message
from src.domain.interfaces.genetic_algorithm.operators.ga_selection_strategy import (
    IGeneticSelectionStrategy,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.infrastructure.genetic_algorithm.builders.component_builders import (
    build_selection_strategy,
)


class SelectionStrategyFactory:
    """Create configured selection strategy instances for lab runs."""

    @classmethod
    def create(
        cls,
        name: str,
        params: Mapping[str, Any] | None = None,
        logger: RuntimeLogger | None = None,
    ) -> IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]:
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
        return build_selection_strategy(
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
