"""Search-space summary model for the console lab final report."""

from typing import Any

from pydantic import BaseModel, Field


class LabSearchSummary(BaseModel):
    """Summarize how the benchmark session produced its resolved runs.

    Attributes:
        mode: Experiment mode (`explicit`, `grid`, or `random`).
        resolved_run_count: Number of runs after expansion.
        details: Mode-specific descriptive metadata for the search process.
    """

    mode: str
    resolved_run_count: int
    details: dict[str, Any] = Field(default_factory=dict)
