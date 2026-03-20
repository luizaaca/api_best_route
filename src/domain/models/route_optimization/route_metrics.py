"""Shared aggregate metrics for route-level and fleet-level results."""

from dataclasses import dataclass


@dataclass
class RouteMetrics:
    """Store shared aggregate totals for route calculation results."""

    total_eta: float = 0.0
    total_length: float = 0.0
    total_cost: float | None = None
