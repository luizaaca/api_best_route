"""FastAPI dependency definitions for creating optimizer components.

This module provides cached factory functions used by the API to wire up the
route optimization service with adaptive GA infrastructure implementations.
"""

import logging
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
from src.infrastructure.genetic_algorithm_execution_runner import (
    GeneticAlgorithmExecutionRunner,
)
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.tsp_optimizer_factory import TSPOptimizerFactory
from src.domain.models.route_optimization.route_ga_execution_bundle import (
    RouteGAExecutionBundle,
)


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


def _build_adaptive_execution_bundle(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    population_size,
    vehicle_count,
    adaptive_config: Mapping[str, Any] | None = None,
) -> RouteGAExecutionBundle:
    """Create one route execution bundle backed by adaptive configuration.

    Args:
        calc: The route calculator to use for segment computation.
        route_nodes: The list of route nodes to optimize.
        weight_type: Weighting strategy for segment computation.
        cost_type: Optional cost strategy for segment computation.
        population_size: The number of individuals in the genetic population.
        vehicle_count: Number of vehicles available for the current run.
        adaptive_config: Adaptive GA state-graph configuration.

    Returns:
        A configured route execution bundle.

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
    return TSPOptimizerFactory.create_execution_bundle(
        adjacency_matrix=adjacency_matrix,
        route_nodes=route_nodes,
        vehicle_count=vehicle_count,
        population_size=population_size,
        ga_family=ga_family,
    )


logger = logging.getLogger("api.route_optimization_service")


def get_route_optimization_service() -> RouteOptimizationService:
    """Return the RouteOptimizationService configured with default dependencies."""
    return RouteOptimizationService(
        graph_generator=get_graph_generator(),
        route_calculator_factory=RouteCalculator,
        execution_bundle_factory=_build_adaptive_execution_bundle,
        execution_runner=GeneticAlgorithmExecutionRunner(),
        plotter_factory=None,
        logger=logger,
    )
