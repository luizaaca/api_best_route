"""Shared builder for heuristic distance strategies used by GA composition."""

from __future__ import annotations

from src.domain.interfaces.geo_graph.heuristic_distance import (
    IHeuristicDistanceStrategy,
)
from src.infrastructure.genetic_algorithm.distance import (
    AdjacencyCostPopulationDistanceStrategy,
    AdjacencyEtaPopulationDistanceStrategy,
    AdjacencyLengthPopulationDistanceStrategy,
    EuclideanPopulationDistanceStrategy,
)
from src.infrastructure.route_calculator import AdjacencyMatrix


def build_population_distance_strategy(
    adjacency_matrix: AdjacencyMatrix,
    weight_type: str,
    cost_type: str | None,
) -> IHeuristicDistanceStrategy:
    """Build the heuristic distance strategy used by population generators.

    Args:
        adjacency_matrix: Shared adjacency matrix used by adjacency-based
            distance strategies.
        weight_type: Preferred graph edge weight identifier.
        cost_type: Optional cost metric identifier.

    Returns:
        The concrete heuristic distance strategy for the requested routing
        configuration.
    """
    if cost_type not in (None, "", "none"):
        return AdjacencyCostPopulationDistanceStrategy(adjacency_matrix)
    if weight_type == "length":
        return AdjacencyLengthPopulationDistanceStrategy(adjacency_matrix)
    if weight_type == "eta":
        return AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    return EuclideanPopulationDistanceStrategy()
