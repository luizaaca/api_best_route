from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.matplotlib_plotter import MatplotlibPlotter
from src.application.route_optimization_service import RouteOptimizationService


def run_console_example():
    service = RouteOptimizationService(
        graph_generator=OSMnxGraphGenerator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=lambda calc: TSPGeneticAlgorithm(route_calculator=calc),
        plotter=MatplotlibPlotter(),
    )

    # example usage (coordinates or addresses needed to actually run):
    origin = "Praça da Sé, São Paulo"
    destinations = [("Avenida Paulista, São Paulo", 1)]
    result = service.optimize(origin=origin, destinations=destinations)
    print(result)


if __name__ == "__main__":
    run_console_example()
