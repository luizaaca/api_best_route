from src.domain.models import RouteNode

from .base_adjacency_population_distance_strategy import (
    BaseAdjacencyPopulationDistanceStrategy,
)


class AdjacencyEtaPopulationDistanceStrategy(BaseAdjacencyPopulationDistanceStrategy):
    """Measure heuristic distances using adjacency-matrix ETA."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float:
        """Return the precomputed segment ETA between two nodes."""
        return self._get_segment(start_node, end_node).eta
