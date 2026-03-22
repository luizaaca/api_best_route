import os
import sys
from typing import cast
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.genetic_algorithm.builders import (
    build_crossover_strategy,
    build_mutation_strategy,
    build_population_generator,
    build_population_distance_strategy,
    build_route_adaptive_state_controller,
    build_selection_strategy,
    build_specification,
)
from src.infrastructure.genetic_algorithm.factories import AdaptiveRouteGAFamilyFactory
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)
from src.infrastructure.genetic_algorithm.crossover import (
    OrderCrossoverStrategy,
)
from src.infrastructure.genetic_algorithm.distance import (
    AdjacencyCostPopulationDistanceStrategy,
    AdjacencyEtaPopulationDistanceStrategy,
    AdjacencyLengthPopulationDistanceStrategy,
    EuclideanPopulationDistanceStrategy,
)
from src.infrastructure.genetic_algorithm.mutation import InversionMutationStrategy
from src.infrastructure.genetic_algorithm.population import HybridPopulationGenerator
from src.infrastructure.genetic_algorithm.selection import TournamentSelectionStrategy
from src.infrastructure.genetic_algorithm.specifications import (
    ImprovementBelowSpecification,
)
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory
from src.domain.models.geo_graph.route_node import RouteNode


class DummyHeuristicDistanceStrategy:
    """Provide one minimal heuristic distance strategy for builder tests."""

    def distance(self, start_node, end_node):
        """Return one deterministic heuristic distance for any nodes."""
        _ = start_node
        _ = end_node
        return 1.0


def test_build_population_distance_strategy_prefers_cost_type():
    adjacency_matrix = {}

    strategy = build_population_distance_strategy(
        adjacency_matrix,
        weight_type="eta",
        cost_type="priority",
    )

    assert isinstance(strategy, AdjacencyCostPopulationDistanceStrategy)


def test_build_population_distance_strategy_supports_length_eta_and_fallback():
    adjacency_matrix = {}

    assert isinstance(
        build_population_distance_strategy(adjacency_matrix, "length", None),
        AdjacencyLengthPopulationDistanceStrategy,
    )
    assert isinstance(
        build_population_distance_strategy(adjacency_matrix, "eta", None),
        AdjacencyEtaPopulationDistanceStrategy,
    )
    assert isinstance(
        build_population_distance_strategy(adjacency_matrix, "custom", None),
        EuclideanPopulationDistanceStrategy,
    )


def test_shared_component_builders_resolve_expected_types():
    selection = build_selection_strategy(
        "tournament",
        params={"tournament_size": 5},
    )
    crossover = build_crossover_strategy("order")
    mutation = build_mutation_strategy("inversion")
    generator = build_population_generator(
        "hybrid",
        distance_strategy=DummyHeuristicDistanceStrategy(),
        params={"heuristic_ratio": 0.7},
    )
    specification = build_specification(
        {"name": "improvement_below", "params": {"threshold": 0.02}}
    )

    assert isinstance(selection, TournamentSelectionStrategy)
    assert cast(TournamentSelectionStrategy, selection)._tournament_size == 5
    assert isinstance(crossover, OrderCrossoverStrategy)
    assert isinstance(mutation, InversionMutationStrategy)
    assert isinstance(generator, HybridPopulationGenerator)
    assert isinstance(specification, ImprovementBelowSpecification)


def test_shared_builders_report_ignored_params_when_requested():
    ignored_params_reports: list[tuple[str, str, dict[str, object]]] = []

    build_selection_strategy(
        "roulette",
        params={"unused": 1},
        ignored_params_reporter=lambda kind, name, params: ignored_params_reports.append(
            (kind, name, dict(params))
        ),
    )

    assert ignored_params_reports == [("selection strategy", "roulette", {"unused": 1})]


def test_tsp_optimizer_factory_builds_route_execution_bundle() -> None:
    ga_family = AdaptiveRouteGAFamilyFactory().create(
        adaptive_config={
            "initial_state": "baseline",
            "states": [
                {
                    "name": "baseline",
                    "selection": {"name": "roulette"},
                    "crossover": {"name": "order"},
                    "mutation": {"name": "inversion"},
                    "population_generator": {"name": "random"},
                    "mutation_probability": 0.33,
                }
            ],
        },
        adjacency_matrix={},
        weight_type="eta",
        cost_type=None,
    )

    nodes = [
        RouteNode("Origin", 1, (0.0, 0.0)),
        RouteNode("Node 2", 2, (1.0, 1.0)),
    ]
    bundle = TSPOptimizerFactory.create_execution_bundle(
        adjacency_matrix={},
        route_nodes=nodes,
        vehicle_count=3,
        population_size=12,
        ga_family=ga_family,
    )

    assert bundle.problem is not None
    assert bundle.seed_data.route_nodes == nodes
    assert bundle.seed_data.vehicle_count == 3
    assert bundle.population_size == 12
    assert bundle.state_controller is ga_family.state_controller


def test_tsp_optimizer_factory_requires_adaptive_family() -> None:
    with pytest.raises(ValueError, match="ga_family is required"):
        TSPOptimizerFactory.create_execution_bundle(
            adjacency_matrix={},
            route_nodes=[RouteNode("Origin", 1, (0.0, 0.0))],
            vehicle_count=1,
            population_size=10,
            ga_family=None,
        )


def test_adaptive_route_ga_family_factory_builds_initial_family_from_config():
    """Ensure the adaptive family factory exposes the initial state collaborators."""
    family = AdaptiveRouteGAFamilyFactory().create(
        adaptive_config={
            "initial_state": "baseline",
            "states": [
                {
                    "name": "baseline",
                    "selection": {
                        "name": "tournament",
                        "params": {"tournament_size": 4},
                    },
                    "crossover": {"name": "order"},
                    "mutation": {"name": "two_opt"},
                    "population_generator": {
                        "name": "hybrid",
                        "params": {"heuristic_ratio": 0.6},
                    },
                    "mutation_probability": 0.21,
                }
            ],
        },
        adjacency_matrix={},
        weight_type="eta",
        cost_type=None,
    )

    assert family.initial_state_name == "baseline"
    assert family.initial_operators.selection.name == "TournamentSelectionStrategy"
    assert family.initial_operators.crossover.name == "OrderCrossoverStrategy"
    assert family.initial_operators.mutation.name == "TwoOptMutationStrategy"
    assert family.initial_operators.population_generator is not None
    assert (
        family.initial_operators.population_generator.name
        == "HybridPopulationGenerator"
    )
    assert family.initial_operators.mutation_probability == 0.21


def test_route_adaptive_state_controller_builder_applies_transition_rules():
    controller = build_route_adaptive_state_controller(
        adaptive_config={
            "initial_state": "baseline",
            "states": [
                {
                    "name": "baseline",
                    "selection": {"name": "roulette"},
                    "crossover": {"name": "order"},
                    "mutation": {"name": "inversion"},
                    "transition_rules": [
                        {
                            "label": "late-search",
                            "target_state": "intensify",
                            "specifications": [
                                {
                                    "name": "progress_at_least",
                                    "params": {"threshold": 0.5},
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "intensify",
                    "selection": {
                        "name": "tournament",
                        "params": {"tournament_size": 4},
                    },
                    "crossover": {"name": "order"},
                    "mutation": {"name": "two_opt"},
                },
            ],
        },
        adjacency_matrix={},
        weight_type="eta",
        cost_type=None,
    )

    initial_resolution = controller.get_initial_resolution()
    assert initial_resolution.state_name == "baseline"
    assert initial_resolution.operators.selection.name == "RoulleteSelectionStrategy"

    transitioned = controller.resolve(
        GenerationContext(
            generation=5,
            max_generations=10,
            best_fitness=10.0,
            previous_best_fitness=12.0,
            stale_generations=0,
            elapsed_generations=5,
            elapsed_time_ms=100.0,
            state_name="baseline",
        )
    )

    assert transitioned.state_name == "intensify"
    assert transitioned.transition_label == "late-search"
    assert transitioned.operators.selection.name == "TournamentSelectionStrategy"
