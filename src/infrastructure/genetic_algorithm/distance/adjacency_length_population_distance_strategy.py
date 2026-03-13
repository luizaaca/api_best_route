from src.domain.models import RouteNode

from .base_adjacency_population_distance_strategy import (
    BaseAdjacencyPopulationDistanceStrategy,
)


class AdjacencyLengthPopulationDistanceStrategy(
    BaseAdjacencyPopulationDistanceStrategy
):
    """Measure heuristic distances using adjacency-matrix segment length."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float:
        """Return the precomputed segment length between two nodes."""
        return self._get_segment(start_node, end_node).length
