"""Problem summary model for the console lab final report."""

from pydantic import BaseModel, Field


class LabProblemSummary(BaseModel):
    """Summarize the shared route-optimization problem for a lab session.

    Attributes:
        origin: Shared origin definition for the session.
        destination_count: Number of destinations compared in the session.
        vehicle_count: Number of vehicles available in the problem.
        weight_type: Weight strategy used by route calculation.
        cost_type: Optional cost strategy used by route calculation.
        destination_priority_summary: Compact list of destination priorities.
    """

    origin: str
    destination_count: int
    vehicle_count: int
    weight_type: str
    cost_type: str | None
    destination_priority_summary: list[int] = Field(default_factory=list)
