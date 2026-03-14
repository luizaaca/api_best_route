from src.application.route_optimization_service import RouteOptimizationService
from src.infrastructure.caching import (
    CachedAdjacencyMatrixBuilder,
    CachedGeocodingResolver,
    PhotonGeocodingResolver,
    SQLiteAdjacencySegmentCache,
    SQLiteGeocodingCache,
)
from src.infrastructure.genetic_algorithm import (
    AdjacencyCostPopulationDistanceStrategy,
    AdjacencyEtaPopulationDistanceStrategy,
    AdjacencyLengthPopulationDistanceStrategy,
    EuclideanPopulationDistanceStrategy,
    HeuristicPopulationGenerator,
    HybridPopulationGenerator,
    OrderCrossoverStrategy,
    RandomPopulationGenerator,
    RoulleteSelectionStrategy,
    SwapAndRedistributeMutationStrategy,
)
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.matplotlib_plotter import MatplotlibPlotter


def _build_population_distance_strategy(adjacency_matrix, weight_type, cost_type):
    """Select the default heuristic distance strategy for population seeding."""
    if cost_type not in (None, "", "none"):
        return AdjacencyCostPopulationDistanceStrategy(adjacency_matrix)
    if weight_type == "length":
        return AdjacencyLengthPopulationDistanceStrategy(adjacency_matrix)
    if weight_type == "eta":
        return AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    return EuclideanPopulationDistanceStrategy()


def _build_default_optimizer(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    plotter,
    population_size,
) -> TSPGeneticAlgorithm:
    """Create a GA optimizer with the default console collaborators."""
    adjacency_matrix = CachedAdjacencyMatrixBuilder(
        SQLiteAdjacencySegmentCache("cache/adjacency_segments.db")
    ).build(
        route_calculator=calc,
        route_nodes=route_nodes,
        weight_type=weight_type,
        cost_type=cost_type,
    )
    heuristic_generator = HeuristicPopulationGenerator(
        _build_population_distance_strategy(adjacency_matrix, weight_type, cost_type)
    )
    return TSPGeneticAlgorithm(
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
    service = RouteOptimizationService(
        graph_generator=OSMnxGraphGenerator(
            geocoder=CachedGeocodingResolver(
                cache=SQLiteGeocodingCache("cache/geocoding.db"),
                fallback_resolver=PhotonGeocodingResolver(),
            )
        ),
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


if __name__ == "__main__":
    run_console_example()
