"""Per-vehicle route summary model for the console lab final report."""

from pydantic import BaseModel, Field


class LabVehicleRouteSummary(BaseModel):
    """Capture compact per-vehicle metrics for one benchmark run.

    Attributes:
        vehicle_id: Vehicle identifier used in the optimization output.
        stop_count: Number of visited stops in the route, excluding the origin.
        total_length: Total route length in meters.
        total_eta: Total route ETA in seconds.
        total_cost: Optional route cost metric.
        ordered_stops: Ordered stop names included in the route output.
    """

    vehicle_id: int
    stop_count: int
    total_length: float
    total_eta: float
    total_cost: float | None
    ordered_stops: list[str] = Field(default_factory=list)
