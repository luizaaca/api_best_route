"""Abstract factory contract for adaptive route GA families."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from src.domain.models.genetic_algorithm.engine.adaptive_ga_family import (
    AdaptiveGAFamily,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.route_optimization.adjacency_matrix_map import AdjacencyMatrixMap
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)


@runtime_checkable
class IAdaptiveRouteGAFamilyFactory(Protocol):
    """Build adaptive route-domain GA families from validated configuration."""

    def create(
        self,
        adaptive_config: Mapping[str, Any],
        adjacency_matrix: AdjacencyMatrixMap,
        weight_type: str,
        cost_type: str | None,
    ) -> AdaptiveGAFamily[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        RoutePopulationSeedData,
    ]:
        """Build one adaptive route GA family.

        Args:
            adaptive_config: Validated adaptive state-graph configuration.
            adjacency_matrix: Shared adjacency matrix for route evaluation.
            weight_type: Requested route weight strategy.
            cost_type: Optional route cost strategy.

        Returns:
            The resolved adaptive GA family for the route domain.
        """
        ...
