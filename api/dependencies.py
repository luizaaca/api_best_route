"""FastAPI dependency definitions for creating optimizer components.

This module provides cached factory functions used by the API to wire up the
route optimization service with adaptive GA infrastructure implementations.
"""

from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from api.config import load_adaptive_ga_config
from src.application.route_optimization_service import RouteOptimizationService
from src.infrastructure.caching import (
    CachedAdjacencyMatrixBuilder,
    CachedGeocodingResolver,
    PhotonGeocodingResolver,
    SQLiteAdjacencySegmentCache,
    SQLiteGeocodingCache,
)
from src.infrastructure.genetic_algorithm.factories import AdaptiveRouteGAFamilyFactory
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory


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
    """Return the default graph generator with cached geocoding support."""
    return OSMnxGraphGenerator(
        CachedGeocodingResolver(
            cache=get_geocoding_cache(),
            fallback_resolver=PhotonGeocodingResolver(),
        )
    )


@lru_cache
def get_adaptive_ga_config() -> dict[str, Any]:
    """Return the required API adaptive GA configuration loaded from disk.

    Returns:
        The parsed adaptive GA configuration read from the fixed repository-root
        `config.json` file.

    Raises:
        FileNotFoundError: If the required config file does not exist.
        ValueError: If the config file contents are invalid.
    """
    return load_adaptive_ga_config()


def _build_adaptive_optimizer(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    plotter,
    population_size,
    adaptive_config: Mapping[str, Any] | None = None,
) -> TSPGeneticAlgorithm:
    """Create a GA optimizer backed by adaptive configuration.

    Args:
        calc: The route calculator to use for segment computation.
        route_nodes: The list of route nodes to optimize.
        weight_type: Weighting strategy for segment computation.
        cost_type: Optional cost strategy for segment computation.
        plotter: Optional plotter for visualization.
        population_size: The number of individuals in the genetic population.
        adaptive_config: Adaptive GA state-graph configuration.

    Returns:
        A configured TSPGeneticAlgorithm instance.

    Raises:
        ValueError: If the adaptive configuration is not provided.
    """
    if adaptive_config is None:
        raise ValueError("adaptive_config is required")
    adjacency_matrix = get_adjacency_matrix_builder().build(
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
    return TSPOptimizerFactory.create(
        adjacency_matrix=adjacency_matrix,
        plotter=plotter,
        population_size=population_size,
        ga_family=ga_family,
    )


def get_route_optimization_service() -> RouteOptimizationService:
    """Return the RouteOptimizationService configured with default dependencies."""
    api_adaptive_config = get_adaptive_ga_config()

    def optimizer_factory(
        calc,
        route_nodes,
        weight_type,
        cost_type,
        plotter,
        population_size,
        adaptive_config=None,
    ) -> TSPGeneticAlgorithm:
        """Build one optimizer using the API's required adaptive configuration.

        Args:
            calc: Route calculator used to evaluate route segments.
            route_nodes: Nodes that define the optimization problem.
            weight_type: Requested route-weight strategy.
            cost_type: Optional cost strategy.
            plotter: Optional plotter used for visualization.
            population_size: Population size for the optimization run.
            adaptive_config: Optional config supplied by callers that still use
                the service's adaptive-config parameter path.

        Returns:
            A configured `TSPGeneticAlgorithm` instance.
        """
        resolved_adaptive_config = (
            adaptive_config if adaptive_config is not None else api_adaptive_config
        )

        return _build_adaptive_optimizer(
            calc=calc,
            route_nodes=route_nodes,
            weight_type=weight_type,
            cost_type=cost_type,
            plotter=plotter,
            population_size=population_size,
            adaptive_config=resolved_adaptive_config,
        )

    return RouteOptimizationService(
        graph_generator=get_graph_generator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=optimizer_factory,
        plotter_factory=None,
    )
