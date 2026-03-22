import sys
import os
from types import SimpleNamespace
from typing import Any

import pytest

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models.geo_graph.graph_context import GraphContext
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)
from src.domain.models.route_optimization.optimization_result import OptimizationResult
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.route_segments_info import RouteSegmentsInfo
from src.domain.models.route_optimization.vehicle_route_info import VehicleRouteInfo
from src.application.route_optimization_service import RouteOptimizationService
import networkx as nx


class DummyGraphGenerator:
    def initialize(self, origin, destinations):
        # return a GraphContext with dummy graph and nodes
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:3857"
        return GraphContext(graph=graph, route_nodes=[RouteNode("A", 1, (0, 0))])

    def build_coordinate_converter(self, context):
        self.converter_built = True
        return lambda x, y: (x + 100.0, y + 200.0)


class DummyRouteCalculator:
    def __init__(self, graph):
        pass

    def get_weight_function(self, weight_type="eta"):
        return lambda u, v, d: 1

    def get_cost_function(self, cost_type="priority"):
        return None

    def compute_route_segments_info(self, route, weight_function, cost_type=None):
        return RouteSegmentsInfo(segments=[], total_eta=0, total_length=0, total_cost=0)


class DummyExecutionRunner:
    def __init__(self):
        self.problem = None
        self.seed_data = None
        self.state_controller = None
        self.population_size = None
        self.max_generations = None
        self.max_processing_time = None

    def run(
        self,
        problem,
        seed_data,
        state_controller,
        population_size,
        max_generations,
        max_processing_time,
        logger=None,
        on_generation=None,
        on_generation_evaluated=None,
    ):
        self.problem = problem
        self.seed_data = seed_data
        self.state_controller = state_controller
        self.population_size = population_size
        self.max_generations = max_generations
        self.max_processing_time = max_processing_time

        route_info = VehicleRouteInfo(
            vehicle_id=1,
            segments=[
                RouteSegment(
                    start=1,
                    end=1,
                    eta=0,
                    length=0,
                    path=[],
                    segment=[1],
                    name="A",
                    coords=(0.0, 0.0),
                    cost=0,
                ),
                RouteSegment(
                    start=1,
                    end=1,
                    eta=5,
                    length=10,
                    path=[(1.0, 2.0), (3.0, 4.0)],
                    segment=[1],
                    name="A",
                    coords=(5.0, 6.0),
                    cost=7,
                ),
            ],
            total_eta=5,
            total_length=10,
            total_cost=7,
        )
        fleet_route = FleetRouteInfo.from_vehicle_routes([route_info])
        if on_generation is not None:
            on_generation(
                GenerationRecord(
                    generation=1,
                    state_name="warmup",
                    transition_label=None,
                    best_fitness=0.0,
                    stale_generations=0,
                    improvement_ratio=0.0,
                    elapsed_time_ms=1.0,
                    selection_name="roulette",
                    crossover_name="order",
                    mutation_name="swap_redistribute",
                    mutation_probability=0.5,
                    reseed_applied=False,
                )
            )
        if on_generation_evaluated is not None:
            on_generation_evaluated(
                GenerationRecord(
                    generation=1,
                    state_name="warmup",
                    transition_label=None,
                    best_fitness=0.0,
                    stale_generations=0,
                    improvement_ratio=0.0,
                    elapsed_time_ms=1.0,
                    selection_name="roulette",
                    crossover_name="order",
                    mutation_name="swap_redistribute",
                    mutation_probability=0.5,
                    reseed_applied=False,
                ),
                SimpleNamespace(_route_info=fleet_route),
            )
        return OptimizationResult(
            best_route=fleet_route,
            best_fitness=0,
            population_size=population_size,
            generations_run=1,
        )


class DummyPlotter:
    def __init__(self):
        self.called = False

    def plot(self, route_info):
        self.called = True


def test_service_uses_generators():
    plotter = DummyPlotter()
    generator = DummyGraphGenerator()
    execution_runner = DummyExecutionRunner()
    captured_bundle_factory_args: dict[str, object] = {}

    def execution_bundle_factory(
        calc,
        route_nodes,
        weight_type,
        cost_type,
        population_size,
        vehicle_count,
        adaptive_config=None,
    ):
        captured_bundle_factory_args.update(
            {
                "calc": calc,
                "route_nodes": route_nodes,
                "weight_type": weight_type,
                "cost_type": cost_type,
                "population_size": population_size,
                "vehicle_count": vehicle_count,
                "adaptive_config": adaptive_config,
            }
        )
        return SimpleNamespace(
            problem="problem",
            seed_data="seed-data",
            state_controller="state-controller",
            population_size=population_size,
        )

    service = RouteOptimizationService(
        graph_generator=generator,
        route_calculator_factory=lambda g: DummyRouteCalculator(g),
        execution_bundle_factory=execution_bundle_factory,
        execution_runner=execution_runner,
        plotter_factory=lambda context: plotter,
    )
    # run once to trigger plot call and record optimizer
    result = service.optimize(
        "orig",
        [("dest", 1)],
        vehicle_count=3,
        population_size=17,
        weight_type="eta",
        cost_type="priority",
        adaptive_config={
            "initial_state": "warmup",
            "states": [
                {
                    "name": "warmup",
                    "selection": {"name": "roulette"},
                    "crossover": {"name": "order"},
                    "mutation": {"name": "swap_redistribute"},
                }
            ],
        },
    )
    assert plotter.called
    assert generator.converter_built
    assert captured_bundle_factory_args["vehicle_count"] == 3
    assert captured_bundle_factory_args["population_size"] == 17
    assert captured_bundle_factory_args["weight_type"] == "eta"
    assert captured_bundle_factory_args["cost_type"] == "priority"
    assert captured_bundle_factory_args["adaptive_config"] is not None
    assert captured_bundle_factory_args["adaptive_config"]["initial_state"] == "warmup"
    assert len(captured_bundle_factory_args["route_nodes"]) == 1
    assert execution_runner.seed_data == "seed-data"
    assert execution_runner.population_size == 17
    assert execution_runner.max_generations == 50
    assert result.best_route.routes_by_vehicle[0].vehicle_id == 1
    assert result.best_route.routes_by_vehicle[0].total_length == 10
    assert result.best_route.min_vehicle_eta == 5
    assert result.best_route.max_vehicle_eta == 5
    origin_segment = result.best_route.routes_by_vehicle[0].segments[0]
    destination_segment = result.best_route.routes_by_vehicle[0].segments[1]
    assert origin_segment.start == 1
    assert origin_segment.end == 1
    assert origin_segment.coords == (100.0, 200.0)
    assert origin_segment.length == 0
    assert destination_segment.coords == (105.0, 206.0)
    assert destination_segment.path == [(101.0, 202.0), (103.0, 204.0)]

    # run again without specifying vehicle_count to exercise default
    result = service.optimize(
        "orig",
        [("dest", 1)],
        adaptive_config={
            "initial_state": "warmup",
            "states": [
                {
                    "name": "warmup",
                    "selection": {"name": "roulette"},
                    "crossover": {"name": "order"},
                    "mutation": {"name": "swap_redistribute"},
                }
            ],
        },
    )
    assert isinstance(result, OptimizationResult)
    assert result.best_fitness == 0
    assert captured_bundle_factory_args["vehicle_count"] == 1


def test_service_requires_adaptive_config() -> None:
    service = RouteOptimizationService(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=lambda g: DummyRouteCalculator(g),
        execution_bundle_factory=lambda *args, **kwargs: SimpleNamespace(
            problem=None,
            seed_data=None,
            state_controller=None,
            population_size=10,
        ),
        execution_runner=DummyExecutionRunner(),
        plotter_factory=None,
    )

    with pytest.raises(ValueError, match="adaptive_config is required"):
        service.optimize("orig", [("dest", 1)])


if __name__ == "__main__":
    test_service_uses_generators()
    print("All tests passed!")
