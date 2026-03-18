"""Per-run result model for the console lab final report."""

from pydantic import BaseModel, Field

from .lab_fleet_route_summary import LabFleetRouteSummary
from .lab_run_config import LabRunConfig
from .lab_vehicle_route_summary import LabVehicleRouteSummary


class LabRunResult(BaseModel):
    """Represent the outcome of one resolved benchmark execution.

    Attributes:
        run_id: Stable identifier for the run inside the session.
        run_index: Zero-based execution index.
        label: Human-friendly run label.
        status: Execution status (`success`, `failed`, or `skipped`).
        error_message: Optional failure details.
        elapsed_ms: Total execution time in milliseconds.
        best_fitness: Best fitness returned by the optimizer.
        population_size: Final population size reported by the optimizer.
        generations_run: Number of executed generations.
        resolved_config: Full resolved execution configuration.
        fleet_summary: Fleet-level route metrics when available.
        vehicle_summaries: Per-vehicle route metrics when available.
        warnings: Optional per-run warning messages.
    """

    run_id: str
    run_index: int
    label: str
    status: str
    error_message: str | None = None
    elapsed_ms: float
    best_fitness: float | None = None
    population_size: int | None = None
    generations_run: int | None = None
    resolved_config: LabRunConfig
    fleet_summary: LabFleetRouteSummary | None = None
    vehicle_summaries: list[LabVehicleRouteSummary] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
