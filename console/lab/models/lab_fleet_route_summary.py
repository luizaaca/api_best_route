"""Fleet-level route summary model for the console lab final report."""

from pydantic import BaseModel


class LabFleetRouteSummary(BaseModel):
    """Capture fleet-level metrics for one benchmark run.

    Attributes:
        total_length: Total fleet route length in meters.
        min_vehicle_eta: Minimum per-vehicle ETA in seconds.
        max_vehicle_eta: Maximum per-vehicle ETA in seconds.
        total_cost: Optional aggregated cost metric across the fleet.
    """

    total_length: float
    min_vehicle_eta: float
    max_vehicle_eta: float
    total_cost: float | None
