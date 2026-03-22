"""Concrete abstract-factory implementation for adaptive route GA families."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.domain.interfaces.genetic_algorithm.factories.adaptive_route_ga_family_factory import (
    IAdaptiveRouteGAFamilyFactory,
)
from src.domain.models.genetic_algorithm.engine.adaptive_ga_family import (
    AdaptiveGAFamily,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.infrastructure.genetic_algorithm.builders import (
    build_route_adaptive_state_controller,
)
from src.infrastructure.route_calculator import AdjacencyMatrix


class AdaptiveRouteGAFamilyFactory(IAdaptiveRouteGAFamilyFactory):
    """Build adaptive route-domain GA families from state-graph config."""

    def create(
        self,
        adaptive_config: Mapping[str, Any],
        adjacency_matrix: AdjacencyMatrix,
        weight_type: str,
        cost_type: str | None,
    ) -> AdaptiveGAFamily[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        RoutePopulationSeedData,
    ]:
        """Build one adaptive family for route optimization.

        Args:
            adaptive_config: Validated adaptive GA state graph.
            adjacency_matrix: Shared adjacency matrix for route evaluation.
            weight_type: Requested route weight strategy.
            cost_type: Optional route cost strategy.

        Returns:
            The resolved adaptive route GA family.

        Raises:
            ValueError: If the adaptive configuration is empty.
        """
        if not adaptive_config:
            raise ValueError("adaptive_config is required to build the GA family")

        state_controller = build_route_adaptive_state_controller(
            adaptive_config=adaptive_config,
            adjacency_matrix=adjacency_matrix,
            weight_type=weight_type,
            cost_type=cost_type,
        )
        initial_resolution = state_controller.get_initial_resolution()
        return AdaptiveGAFamily[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
        ](
            initial_state_name=initial_resolution.state_name,
            initial_operators=initial_resolution.operators,
            state_controller=state_controller,
        )
