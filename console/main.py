from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.matplotlib_plotter import MatplotlibPlotter
from src.application.route_optimization_service import RouteOptimizationService


def run_console_example():
    service = RouteOptimizationService(
        graph_generator=OSMnxGraphGenerator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=lambda calc, plotter, population_size: TSPGeneticAlgorithm(
            route_calculator=calc,
            plotter=plotter,
            population_size=population_size,
        ),
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

    result = service.optimize(
        origin=origin,
        destinations=destinations,
        max_generation=max_generation,
        max_processing_time=max_processing_time,
        vehicle_count=2,  # example value
        population_size=10,
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
    print(f"Tempo total estimado: {result.best_route.total_eta/60:.1f} min")
    print(f"Custo total: {(result.best_route.total_cost or 0.0):.2f}")
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    run_console_example()
