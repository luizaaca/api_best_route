from src.domain.models import RouteNode

from .base_adjacency_population_distance_strategy import (
    BaseAdjacencyPopulationDistanceStrategy,
)


class AdjacencyCostPopulationDistanceStrategy(BaseAdjacencyPopulationDistanceStrategy):
    """Measure heuristic distances using adjacency-matrix segment cost."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float | None:
        """Return the precomputed segment cost between two nodes."""
        segment = self._get_segment(start_node, end_node)
        return float(segment.cost) if segment.cost is not None else None
