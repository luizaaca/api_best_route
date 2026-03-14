"""Heuristic distance strategy using Euclidean distance in projected space."""

from math import dist

from src.domain.interfaces import IHeuristicDistanceStrategy
from src.domain.models import RouteNode


class EuclideanPopulationDistanceStrategy(IHeuristicDistanceStrategy):
    """Strategy that computes distance using straight-line Euclidean metric."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float:
        """Return the Euclidean distance between two projected nodes.

        Args:
            start_node: The start node.
            end_node: The end node.

        Returns:
            The straight-line distance in the projected CRS.
        """
        return float(dist(start_node.coords, end_node.coords))
