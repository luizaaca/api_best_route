"""Shared builders for route adaptive GA state-controller composition."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
from src.domain.models.genetic_algorithm.engine.configured_state import ConfiguredState
from src.domain.models.genetic_algorithm.engine.generation_operators import (
    GenerationOperators,
)
from src.domain.models.genetic_algorithm.engine.transition_rule import TransitionRule
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.infrastructure.genetic_algorithm.state_controllers.configured_state_controller import (
    ConfiguredGeneticStateController,
)
from src.infrastructure.genetic_algorithm.builders.distance_strategy_builder import (
    build_population_distance_strategy,
)
from src.infrastructure.genetic_algorithm.builders.legacy_component_builders import (
    build_legacy_crossover_strategy,
    build_legacy_mutation_strategy,
    build_legacy_population_generator,
    build_legacy_selection_strategy,
    build_specification,
)
from src.infrastructure.legacy_crossover_strategy_adapter import (
    LegacyCrossoverStrategyAdapter,
)
from src.infrastructure.legacy_mutation_strategy_adapter import (
    LegacyMutationStrategyAdapter,
)
from src.infrastructure.legacy_population_generator_adapter import (
    LegacyPopulationGeneratorAdapter,
)
from src.infrastructure.legacy_selection_strategy_adapter import (
    LegacySelectionStrategyAdapter,
)
from src.infrastructure.route_calculator import AdjacencyMatrix


def build_route_transition_rule(config: Mapping[str, Any]) -> TransitionRule:
    """Build one configured transition rule for route adaptive state graphs.

    Args:
        config: Transition-rule configuration mapping.

    Returns:
        The configured transition rule.
    """
    return TransitionRule(
        label=str(config["label"]),
        target_state=str(config["target_state"]),
        specifications=[
            build_specification(specification)
            for specification in config.get("specifications", [])
        ],
    )


def build_route_generation_operators(
    state_config: Mapping[str, Any],
    adjacency_matrix: AdjacencyMatrix,
    weight_type: str,
    cost_type: str | None,
) -> GenerationOperators[
    RouteGeneticSolution,
    EvaluatedRouteSolution,
    RoutePopulationSeedData,
]:
    """Build one adaptive route generation-operator bundle.

    Args:
        state_config: State configuration mapping.
        adjacency_matrix: Shared adjacency matrix for route evaluation.
        weight_type: Requested route weight strategy.
        cost_type: Optional route cost strategy.

    Returns:
        The configured generation-operator bundle for the route domain.
    """
    population_generator_config = state_config.get("population_generator")
    distance_strategy = build_population_distance_strategy(
        adjacency_matrix,
        weight_type,
        cost_type,
    )
    resolved_population_generator = (
        build_legacy_population_generator(
            name=str(population_generator_config["name"]),
            distance_strategy=distance_strategy,
            params=population_generator_config.get("params"),
        )
        if population_generator_config is not None
        else build_legacy_population_generator(
            name="hybrid",
            distance_strategy=distance_strategy,
        )
    )

    return GenerationOperators(
        selection=LegacySelectionStrategyAdapter(
            build_legacy_selection_strategy(
                name=str(state_config["selection"]["name"]),
                params=state_config["selection"].get("params"),
            )
        ),
        crossover=LegacyCrossoverStrategyAdapter(
            build_legacy_crossover_strategy(
                name=str(state_config["crossover"]["name"]),
                params=state_config["crossover"].get("params"),
            )
        ),
        mutation=LegacyMutationStrategyAdapter(
            build_legacy_mutation_strategy(
                name=str(state_config["mutation"]["name"]),
                params=state_config["mutation"].get("params"),
            )
        ),
        mutation_probability=float(state_config.get("mutation_probability", 0.5)),
        population_generator=LegacyPopulationGeneratorAdapter(
            resolved_population_generator
        ),
    )


def build_route_adaptive_state_controller(
    adaptive_config: Mapping[str, Any],
    adjacency_matrix: AdjacencyMatrix,
    weight_type: str,
    cost_type: str | None,
) -> IGeneticStateController[
    RouteGeneticSolution,
    EvaluatedRouteSolution,
    RoutePopulationSeedData,
]:
    """Build one configured adaptive state controller for route optimization.

    Args:
        adaptive_config: Adaptive state-graph configuration.
        adjacency_matrix: Shared adjacency matrix for route evaluation.
        weight_type: Requested route weight strategy.
        cost_type: Optional route cost strategy.

    Returns:
        A configured route adaptive state controller.
    """
    states = [
        ConfiguredState[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
        ](
            name=str(state["name"]),
            operators=build_route_generation_operators(
                state,
                adjacency_matrix,
                weight_type,
                cost_type,
            ),
            transition_rules=[
                build_route_transition_rule(rule)
                for rule in state.get("transition_rules", [])
            ],
        )
        for state in adaptive_config.get("states", [])
    ]

    return ConfiguredGeneticStateController[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        RoutePopulationSeedData,
    ](
        initial_state=str(adaptive_config["initial_state"]),
        states=states,
    )
