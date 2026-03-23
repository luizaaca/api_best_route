"""Console entrypoint for the route optimization example.

This module is intended for local experimentation and demonstrates how to
construct the application services and run the genetic algorithm from a
standalone script.
"""

import argparse
from pathlib import Path
from typing import Any

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
from src.infrastructure.genetic_algorithm.factories import AdaptiveRouteGAFamilyFactory
from src.infrastructure.config import (
    get_sibling_config_path,
    load_adaptive_ga_config,
)
from src.infrastructure.genetic_algorithm_execution_runner import (
    GeneticAlgorithmExecutionRunner,
)
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.matplotlib_plotter import MatplotlibPlotter
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory
from src.domain.models.route_optimization.route_ga_execution_bundle import (
    RouteGAExecutionBundle,
)


def get_console_adaptive_ga_config_path() -> Path:
    """Return the fixed adaptive GA config path used by the console example.

    Returns:
        The absolute path to the console-owned adaptive GA config file.
    """
    return get_sibling_config_path(__file__, "example.config.json")


def _build_graph_generator(logger=None) -> OSMnxGraphGenerator:
    """Create the shared graph generator used by console flows.

    Returns:
        A configured graph generator with persistent geocoding cache.
    """
    return OSMnxGraphGenerator(
        geocoder=CachedGeocodingResolver(
            cache=SQLiteGeocodingCache("cache/geocoding.db"),
            fallback_resolver=PhotonGeocodingResolver(),
            logger=logger,
        ),
        logger=logger,
    )


def _build_adjacency_matrix_builder(logger=None) -> CachedAdjacencyMatrixBuilder:
    """Create the shared adjacency-matrix builder used by console flows.

    Returns:
        A configured adjacency-matrix builder with persistent SQLite cache.
    """
    return CachedAdjacencyMatrixBuilder(
        SQLiteAdjacencySegmentCache("cache/adjacency_segments.db"),
        logger=logger,
    )


def _build_adaptive_execution_bundle(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    population_size,
    vehicle_count,
    adaptive_config: dict[str, Any] | None = None,
) -> RouteGAExecutionBundle:
    """Create one route execution bundle configured from adaptive config.

    Args:
        calc: The route calculator to use.
        route_nodes: The list of route nodes for optimization.
        weight_type: Weighting strategy for segment evaluation.
        cost_type: Optional cost strategy.
        population_size: Number of individuals in the population.
        vehicle_count: Number of vehicles available for the current run.
        adaptive_config: Adaptive GA state-graph configuration.

    Returns:
        A configured route execution bundle.

    Raises:
        ValueError: If the adaptive configuration is not provided.
    """
    if adaptive_config is None:
        raise ValueError("adaptive_config is required")
    adjacency_matrix = _build_adjacency_matrix_builder().build(
        route_calculator=calc,
        route_nodes=route_nodes,
        weight_type=weight_type,
        cost_type=cost_type,
    )
    ga_family = AdaptiveRouteGAFamilyFactory().create(
        adaptive_config=adaptive_config,
        adjacency_matrix=adjacency_matrix,
        weight_type=weight_type,
        cost_type=cost_type,
    )
    return TSPOptimizerFactory.create_execution_bundle(
        adjacency_matrix=adjacency_matrix,
        route_nodes=route_nodes,
        vehicle_count=vehicle_count,
        population_size=population_size,
        ga_family=ga_family,
    )


def run_console_example(
    verbose: bool = False,
    max_generation: int = 500,
    max_processing_time: int = 300000,
):
    """Run a console example optimization and print the results."""
    adaptive_config = load_adaptive_ga_config(get_console_adaptive_ga_config_path())
    logger = build_runtime_logger(verbose)

    service = RouteOptimizationService(
        graph_generator=_build_graph_generator(logger=logger),
        route_calculator_factory=RouteCalculator,
        execution_bundle_factory=_build_adaptive_execution_bundle,
        execution_runner=GeneticAlgorithmExecutionRunner(),
        plotter_factory=MatplotlibPlotter,
        logger=logger,
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
        adaptive_config=adaptive_config,
    )
    # Format the result for console display.
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
        adjacency_matrix_builder=_build_adjacency_matrix_builder(logger=logger),
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
            "Console entrypoint for route optimization. Run the adaptive "
            "interactive example or execute lab-mode benchmark sessions "
            "from JSON configuration files."
        )
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose console output for the interactive example.",
    )
    parser.add_argument(
        "--max-generation",
        type=int,
        default=500,
        help="Maximum number of generations for the interactive example.",
    )
    parser.add_argument(
        "--max-processing-time",
        type=int,
        default=300000,
        help="Maximum processing time in milliseconds for the interactive example.",
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

    When no subcommand is provided, the adaptive console example is executed.
    """
    parser = _build_argument_parser()
    args = parser.parse_args()
    if args.command == "lab":
        run_lab_benchmark(args.config)
        return
    run_console_example(
        verbose=args.verbose,
        max_generation=args.max_generation,
        max_processing_time=args.max_processing_time,
    )


if __name__ == "__main__":
    main()
