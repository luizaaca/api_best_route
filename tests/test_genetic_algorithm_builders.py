import os
import sys
from typing import cast

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


def test_tsp_optimizer_factory_forwards_resolved_collaborators():
    captured_kwargs: dict[str, object] = {}

    class CapturingOptimizer:
        """Capture constructor kwargs passed through the shared TSP factory."""

        def __init__(self, **kwargs):
            """Store the received constructor kwargs for assertions."""
            captured_kwargs.update(kwargs)

    selection = build_selection_strategy("roulette")
    crossover = build_crossover_strategy("order")
    mutation = build_mutation_strategy("inversion")
    generator = build_population_generator(
        "random",
        distance_strategy=DummyHeuristicDistanceStrategy(),
    )

    optimizer = TSPOptimizerFactory.create(
        adjacency_matrix={},
        population_size=14,
        mutation_probability=0.33,
        plotter=None,
        selection_strategy=selection,
        crossover_strategy=crossover,
        mutation_strategy=mutation,
        population_generator=generator,
        logger=None,
        optimizer_type=CapturingOptimizer,
    )

    assert optimizer is not None
    assert captured_kwargs["population_size"] == 14
    assert captured_kwargs["mutation_probability"] == 0.33
    assert captured_kwargs["selection_strategy"] is selection
    assert captured_kwargs["crossover_strategy"] is crossover
    assert captured_kwargs["mutation_strategy"] is mutation
    assert captured_kwargs["population_generator"] is generator


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
                    "selection": {"name": "tournament", "params": {"tournament_size": 4}},
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
