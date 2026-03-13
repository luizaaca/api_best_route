from math import dist

from src.domain.interfaces import IHeuristicDistanceStrategy
from src.domain.models import RouteNode


class EuclideanPopulationDistanceStrategy(IHeuristicDistanceStrategy):
    """Measure heuristic distances using projected Euclidean coordinates."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float:
        """Return the Euclidean distance between two projected nodes."""
        return float(dist(start_node.coords, end_node.coords))
