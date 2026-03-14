"""FastAPI dependency definitions for creating optimizer components.

This module provides cached factory functions used by the API to wire up the
route optimization service with default infrastructure implementations.
"""

from functools import lru_cache
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


@lru_cache
def get_geocoding_cache() -> SQLiteGeocodingCache:
    """Return the default persistent geocoding cache."""
    return SQLiteGeocodingCache("cache/geocoding.db")


@lru_cache
def get_adjacency_segment_cache() -> SQLiteAdjacencySegmentCache:
    """Return the default persistent adjacency segment cache."""
    return SQLiteAdjacencySegmentCache("cache/adjacency_segments.db")


@lru_cache
def get_adjacency_matrix_builder() -> CachedAdjacencyMatrixBuilder:
    """Return the default adjacency matrix builder with segment caching."""
    return CachedAdjacencyMatrixBuilder(get_adjacency_segment_cache())


@lru_cache
def get_graph_generator() -> OSMnxGraphGenerator:
    return OSMnxGraphGenerator(
        CachedGeocodingResolver(
            cache=get_geocoding_cache(),
            fallback_resolver=PhotonGeocodingResolver(),
        )
    )


def _build_population_distance_strategy(adjacency_matrix, weight_type, cost_type):
    """Select the default heuristic distance strategy for population seeding.

    Args:
        adjacency_matrix: The adjacency matrix used for distance lookups.
        weight_type: The weight strategy (e.g., "eta", "length").
        cost_type: Optional cost strategy name.

    Returns:
        An IHeuristicDistanceStrategy implementation.
    """
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
    """Create a GA optimizer with default concrete collaborators.

    This function constructs the optimizer with a cached adjacency matrix
    builder, heuristic population generator, and default genetic operators.

    Args:
        calc: The route calculator to use for segment computation.
        route_nodes: The list of route nodes to optimize.
        weight_type: Weighting strategy for segment computation.
        cost_type: Optional cost strategy for segment computation.
        plotter: Optional plotter for visualization.
        population_size: The number of individuals in the genetic population.

    Returns:
        A configured TSPGeneticAlgorithm instance.
    """
    adjacency_matrix = get_adjacency_matrix_builder().build(
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


def get_route_optimization_service() -> RouteOptimizationService:
    """Return the RouteOptimizationService configured with default dependencies."""
    return RouteOptimizationService(
        graph_generator=get_graph_generator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=_build_default_optimizer,
        plotter_factory=None,
    )
