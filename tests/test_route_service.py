import sys
import os

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models import (
    OptimizationResult,
    RouteNode,
    RouteSegmentsInfo,
    GraphContext,
)
from src.application.route_optimization_service import RouteOptimizationService
import networkx as nx


class DummyGraphGenerator:
    def initialize(self, origin, destinations):
        # return a GraphContext with dummy graph and nodes
        graph = nx.MultiDiGraph()
        graph.graph["crs"] = "EPSG:3857"
        return GraphContext(graph=graph, route_nodes=[RouteNode("A", 1, (0, 0))])

    def convert_segments_to_lat_lon(self, context, route_segments):
        self.converted = True
        return route_segments


class DummyRouteCalculator:
    def __init__(self, graph):
        pass

    def get_weight_function(self):
        return lambda u, v, d: 1

    def compute_route_segments_info(self, route, weight_function, cost_type=None):
        return RouteSegmentsInfo(segments=[], total_eta=0, total_length=0, total_cost=0)


class DummyOptimizer:
    def __init__(self, calc, plotter=None):
        self.calc = calc
        self.plotter = plotter
        self.last_vehicle_count = None

    def solve(self, route_nodes, max_generation, max_processing_time, vehicle_count=1):
        # record argument for verification
        self.last_vehicle_count = vehicle_count
        if self.plotter:
            self.plotter.plot(RouteSegmentsInfo())
        return OptimizationResult(
            best_route=RouteSegmentsInfo(),
            best_fitness=0,
            population_size=1,
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

    def optimizer_factory(calc, plt):
        nonlocal last_optimizer
        last_optimizer = DummyOptimizer(calc, plt)
        return last_optimizer

    service = RouteOptimizationService(
        graph_generator=generator,
        route_calculator_factory=lambda g: DummyRouteCalculator(g),
        optimizer_factory=optimizer_factory,
        plotter_factory=lambda context: plotter,
    )
    # run once to trigger plot call and record optimizer
    result = service.optimize("orig", [("dest", 1)], vehicle_count=3)
    assert plotter.called
    assert generator.converted  # Ensure conversion was called
    assert last_optimizer is not None
    assert last_optimizer.last_vehicle_count == 3

    # run again without specifying vehicle_count to exercise default
    result = service.optimize("orig", [("dest", 1)])
    assert isinstance(result, OptimizationResult)
    assert result.best_fitness == 0
    assert last_optimizer.last_vehicle_count == 1


if __name__ == "__main__":
    test_service_uses_generators()
    print("All tests passed!")
