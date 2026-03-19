"""Route-domain evaluated solution model for the generic GA engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.domain.interfaces.ga_evaluated_solution import IEvaluatedGeneticSolution

from .route import FleetRouteInfo
from .route_genetic_solution import RouteGeneticSolution


@dataclass(slots=True)
class EvaluatedRouteSolution(IEvaluatedGeneticSolution):
    """Store one evaluated route solution and its comparable metrics.

    Attributes:
        solution: Raw route solution that was evaluated.
        route_info: Route-domain metrics assembled from the raw solution.
        metrics: Optional extra metrics exposed to adaptive policies and logs.
    """

    solution: RouteGeneticSolution
    route_info: FleetRouteInfo
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def fitness(self) -> float:
        """Return the scalar fitness used by the generic GA engine.

        Returns:
            The route total cost when available, otherwise the fleet makespan.
        """
        if self.route_info.total_cost is not None:
            return self.route_info.total_cost
        return self.route_info.max_vehicle_eta

    def metric(self, name: str, default: Any = None) -> Any:
        """Return one route metric by name.

        Args:
            name: Metric identifier.
            default: Value returned when the metric is unavailable.

        Returns:
            The matching metric value or `default`.
        """
        if name in self.metrics:
            return self.metrics[name]
        route_metric_map = {
            "total_length": self.route_info.total_length,
            "total_eta": self.route_info.total_eta,
            "total_cost": self.route_info.total_cost,
            "min_vehicle_eta": self.route_info.min_vehicle_eta,
            "max_vehicle_eta": self.route_info.max_vehicle_eta,
        }
        return route_metric_map.get(name, default)
