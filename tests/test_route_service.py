import sys
import os
from typing import Any

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models.geo_graph.graph_context import GraphContext
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo
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


class DummyOptimizer:
    def __init__(
        self,
        route_nodes,
        weight_type,
        cost_type,
        plotter=None,
        population_size=10,
        adaptive_config: dict[str, Any] | None = None,
    ):
        self.route_nodes = route_nodes
        self.weight_type = weight_type
        self.cost_type = cost_type
        self.plotter = plotter
        self.last_vehicle_count = None
        self.last_population_size = population_size
        self.adaptive_config = adaptive_config

    def solve(self, route_nodes, max_generation, max_processing_time, vehicle_count=1):
        # record argument for verification
        self.last_vehicle_count = vehicle_count
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
        if self.plotter:
            self.plotter.plot(fleet_route)
        return OptimizationResult(
            best_route=fleet_route,
            best_fitness=0,
            population_size=self.last_population_size,
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
    # capture optimizer instance so we can inspect arguments later
    last_optimizer = None

    def optimizer_factory(
        calc,
        route_nodes,
        weight_type,
        cost_type,
        plotter,
        population_size,
        adaptive_config=None,
    ):
        nonlocal last_optimizer
        last_optimizer = DummyOptimizer(
            route_nodes,
            weight_type,
            cost_type,
            plotter,
            population_size,
            adaptive_config,
        )
        return last_optimizer

    service = RouteOptimizationService(
        graph_generator=generator,
        route_calculator_factory=lambda g: DummyRouteCalculator(g),
        optimizer_factory=optimizer_factory,
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
    assert last_optimizer is not None
    assert last_optimizer.last_vehicle_count == 3
    assert last_optimizer.last_population_size == 17
    assert last_optimizer.weight_type == "eta"
    assert last_optimizer.cost_type == "priority"
    assert last_optimizer.adaptive_config is not None
    assert last_optimizer.adaptive_config["initial_state"] == "warmup"
    assert len(last_optimizer.route_nodes) == 1
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
    result = service.optimize("orig", [("dest", 1)])
    assert isinstance(result, OptimizationResult)
    assert result.best_fitness == 0
    assert last_optimizer.last_vehicle_count == 1


if __name__ == "__main__":
    test_service_uses_generators()
    print("All tests passed!")
