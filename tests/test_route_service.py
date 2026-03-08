import sys
import os

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.application.route_optimization_service import RouteOptimizationService
from src.domain.models import OptimizationResult, RouteNode, RouteSegmentsInfo


class DummyGraphGenerator:
    def initialize(self, origin, destinations):
        # return a simple dummy graph object and nodes list
        return type("G", (), {"graph": {"crs": "EPSG:3857"}})(), [
            RouteNode("A", 1, (0, 0))
        ]


class DummyRouteCalculator:
    def __init__(self, graph):
        pass

    def get_weight_function(self):
        return lambda u, v, d: 1

    def compute_route_segments_info(self, route, weight_function, cost_type=None):
        return RouteSegmentsInfo(segments=[], total_eta=0, total_length=0, total_cost=0)


class DummyOptimizer:
    def __init__(self, calc):
        self.calc = calc

    def solve(self, route_nodes, max_generation, max_processing_time):
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
    service = RouteOptimizationService(
        graph_generator=DummyGraphGenerator(),
        route_calculator_factory=lambda g: DummyRouteCalculator(g),
        optimizer_factory=lambda calc: DummyOptimizer(calc),
        plotter=plotter,
    )
    # run once to trigger plot call
    result = service.optimize("orig", [("dest", 1)])
    assert plotter.called

    result = service.optimize("orig", [("dest", 1)])
    assert isinstance(result, OptimizationResult)
    assert result.best_fitness == 0
