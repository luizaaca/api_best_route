from functools import lru_cache
from src.infrastructure.genetic_algorithm import (
    HybridPopulationGenerator,
    OrderCrossoverStrategy,
    RandomPopulationGenerator,
    RoulleteSelectionStrategy,
    SwapAndRedistributeMutationStrategy,
)
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator, build_adjacency_matrix
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.application.route_optimization_service import RouteOptimizationService


@lru_cache
def get_graph_generator() -> OSMnxGraphGenerator:
    return OSMnxGraphGenerator()


def _build_default_optimizer(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    plotter,
    population_size,
) -> TSPGeneticAlgorithm:
    """Create a GA optimizer with the default concrete collaborators."""
    return TSPGeneticAlgorithm(
        adjacency_matrix=build_adjacency_matrix(
            route_calculator=calc,  # type: ignore
            route_nodes=route_nodes,
            weight_type=weight_type,
            cost_type=cost_type,
        ),
        plotter=plotter,
        population_size=population_size,
        selection_strategy=RoulleteSelectionStrategy(),
        crossover_strategy=OrderCrossoverStrategy(),
        mutation_strategy=SwapAndRedistributeMutationStrategy(),
        population_generator=HybridPopulationGenerator(RandomPopulationGenerator()),
    )


def get_route_optimization_service() -> RouteOptimizationService:
    return RouteOptimizationService(
        graph_generator=get_graph_generator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=_build_default_optimizer,
        plotter_factory=None,
    )
