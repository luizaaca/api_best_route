"""Domain interface for heuristic distance strategies used during
population seeding.

Heuristic strategies provide an estimate of the distance between two route
nodes to guide genetic algorithm population initialization and diversity.
"""

from typing import Protocol, runtime_checkable

from src.domain.models import RouteNode


@runtime_checkable
class IHeuristicDistanceStrategy(Protocol):
    """Protocol for computing an estimated distance between two route nodes."""

    def distance(
        self,
        start_node: RouteNode,
        end_node: RouteNode,
    ) -> float | None: ...
    """Estimate a heuristic distance value between two route points.

    Args:
        start_node: The starting route node.
        end_node: The ending route node.

    Returns:
        A float representing the heuristic distance, or None if the
        strategy cannot compute a meaningful value.
    """
