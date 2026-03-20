"""Console entrypoint for the route optimization example.

This module is intended for local experimentation and demonstrates how to
construct the application services and run the genetic algorithm from a
standalone script.
"""

import argparse

from console.lab.config import LabConfigLoader
from console.lab.orchestration import LabBenchmarkRunner
from console.lab.reporting import LabConsoleReportRenderer
from console.lab.runtime_logging import build_runtime_logger
from src.application.route_optimization_service import RouteOptimizationService
from src.infrastructure.caching import (
    CachedAdjacencyMatrixBuilder,
    CachedGeocodingResolver,
    PhotonGeocodingResolver,
    SQLiteAdjacencySegmentCache,
    SQLiteGeocodingCache,
)
from src.infrastructure.genetic_algorithm import (
    HeuristicPopulationGenerator,
    HybridPopulationGenerator,
    OrderCrossoverStrategy,
    RandomPopulationGenerator,
    RoulleteSelectionStrategy,
    SwapAndRedistributeMutationStrategy,
)
from src.infrastructure.genetic_algorithm.builders.distance_strategy_builder import (
    build_population_distance_strategy,
)
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.matplotlib_plotter import MatplotlibPlotter
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory


def _build_graph_generator(logger=None) -> OSMnxGraphGenerator:
    """Create the shared graph generator used by console flows.

    Returns:
        A configured graph generator with persistent geocoding cache.
    """
    return OSMnxGraphGenerator(
        geocoder=CachedGeocodingResolver(
            cache=SQLiteGeocodingCache("cache/geocoding.db"),
            fallback_resolver=PhotonGeocodingResolver(),
        ),
        logger=logger,
    )


def _build_adjacency_matrix_builder() -> CachedAdjacencyMatrixBuilder:
    """Create the shared adjacency-matrix builder used by console flows.

    Returns:
        A configured adjacency-matrix builder with persistent SQLite cache.
    """
    return CachedAdjacencyMatrixBuilder(
        SQLiteAdjacencySegmentCache("cache/adjacency_segments.db")
    )


def _build_default_optimizer(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    plotter,
    population_size,
) -> TSPGeneticAlgorithm:
    """Create a GA optimizer configured with console defaults.

    Args:
        calc: The route calculator to use.
        route_nodes: The list of route nodes for optimization.
        weight_type: Weighting strategy for segment evaluation.
        cost_type: Optional cost strategy.
        plotter: Plotter used to visualize progress.
        population_size: Number of individuals in the population.

    Returns:
        A configured TSPGeneticAlgorithm instance.
    """
    adjacency_matrix = CachedAdjacencyMatrixBuilder(
        SQLiteAdjacencySegmentCache("cache/adjacency_segments.db")
    ).build(
        route_calculator=calc,
        route_nodes=route_nodes,
        weight_type=weight_type,
        cost_type=cost_type,
    )
    heuristic_generator = HeuristicPopulationGenerator(
        build_population_distance_strategy(adjacency_matrix, weight_type, cost_type)
    )
    return TSPOptimizerFactory.create(
        adjacency_matrix=adjacency_matrix,
        plotter=plotter,
        population_size=population_size,
        selection_strategy=RoulleteSelectionStrategy(),
        crossover_strategy=OrderCrossoverStrategy(),
        mutation_strategy=SwapAndRedistributeMutationStrategy(),
        population_generator=HybridPopulationGenerator(
            RandomPopulationGenerator(),
            heuristic_generator,
        ),
    )


def run_console_example():
    """Run a console example optimization and print the results.

    This function is intended as a quick demo for running the optimizer from the
    command line, using hard-coded locations and parameters.
    """
    service = RouteOptimizationService(
        graph_generator=_build_graph_generator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=_build_default_optimizer,
        plotter_factory=MatplotlibPlotter,
    )

    origin: str | tuple[float, float] = "Praça da Sé, São Paulo"
    destinations: list[tuple[str | tuple[float, float], int]] = [
        ("Edifício Copan, São Paulo", 1),
        ("Mercado Municipal de São Paulo", 2),
        ((-23.5465, -46.6367), 3),
        ((-23.561543, -46.656197), 2),
        ((-23.544534, -46.66503), 1),
        ((-23.534346, -46.64046), 3),
        ((-23.532278, -46.657468), 2),
        ((-23.531978, -46.634383), 1),
    ]

    max_generation = 50
    max_processing_time = 30000
    weight_type = "eta"
    cost_type = "priority"

    result = service.optimize(
        origin=origin,
        destinations=destinations,
        max_generation=max_generation,
        max_processing_time=max_processing_time,
        vehicle_count=2,  # example value
        population_size=10,
        weight_type=weight_type,
        cost_type=cost_type,
    )
    # resultado formatado para exibição no console
    print("\nResumo da otimização:")
    for vehicle_route in result.best_route.routes_by_vehicle:
        print(
            f"Veículo {vehicle_route.vehicle_id}: "
            f"{[seg.name for seg in vehicle_route.segments]}"
        )
        print(f"  Distância: {vehicle_route.total_length:.1f} m")
        print(f"  ETA: {vehicle_route.total_eta/60:.1f} min")
        print(f"  Custo: {(vehicle_route.total_cost or 0.0):.2f}")
    print(f"Distância total: {result.best_route.total_length:.1f} m")
    print(
        f"Tempo mínimo entre veículos: {result.best_route.min_vehicle_eta/60:.1f} min"
    )
    print(
        f"Tempo máximo entre veículos: {result.best_route.max_vehicle_eta/60:.1f} min"
    )
    print(f"Custo total: {(result.best_route.total_cost or 0.0):.2f}")
    input("\nPressione Enter para sair...")


def run_lab_benchmark(config_file: str) -> None:
    """Run the sequential console lab benchmark for a JSON config file.

    Args:
        config_file: Path to the lab JSON configuration file.
    """
    session_config = LabConfigLoader.load(config_file)
    logger = build_runtime_logger(session_config.output.verbose)
    runner = LabBenchmarkRunner(
        graph_generator=_build_graph_generator(logger=logger),
        route_calculator_factory=RouteCalculator,
        adjacency_matrix_builder=_build_adjacency_matrix_builder(),
        plotter_factory=MatplotlibPlotter,
        logger=logger,
    )
    report = runner.run(config_file, session_config=session_config)
    print(LabConsoleReportRenderer.render(report))


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the console argument parser.

    Returns:
        The configured top-level argument parser.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Console entrypoint for route optimization. Run the legacy "
            "interactive example or execute lab-mode benchmark sessions "
            "from JSON configuration files."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    lab_parser = subparsers.add_parser(
        "lab",
        help="Run a sequential lab-mode benchmark session from a JSON config file.",
    )
    lab_parser.add_argument(
        "--config",
        required=True,
        help=(
            "Path to a lab JSON configuration file, for example "
            "'lab/explicit.config.json', 'lab/grid.config.json', or "
            "'lab/random.config.json'."
        ),
    )
    return parser


def main() -> None:
    """Dispatch the requested console command.

    When no subcommand is provided, the legacy demo flow is executed to preserve
    backwards compatibility with the original console example.
    """
    parser = _build_argument_parser()
    args = parser.parse_args()
    if args.command == "lab":
        run_lab_benchmark(args.config)
        return
    run_console_example()


if __name__ == "__main__":
    main()
