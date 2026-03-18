"""Root session report model for the console lab mode."""

from pydantic import BaseModel, Field

from .lab_aggregate_stats import LabAggregateStats
from .lab_problem_summary import LabProblemSummary
from .lab_output_config import LabOutputConfig
from .lab_run_result import LabRunResult
from .lab_search_summary import LabSearchSummary


class LabBenchmarkReport(BaseModel):
    """Represent the final report emitted for one benchmark session.

    Attributes:
        session_id: Stable identifier for the benchmark session.
        config_file: Source configuration file path.
        mode: Experiment mode used by the session.
        started_at: ISO timestamp marking session start.
        finished_at: ISO timestamp marking session completion.
        elapsed_ms: Total elapsed session time in milliseconds.
        problem_summary: Shared route-optimization problem summary.
        output_config: Session-level output and report-rendering configuration.
        search_summary: Summary of the experiment expansion strategy.
        ranking_metric: Metric used to order successful runs.
        budget_summary: Summary of the shared budget framing.
        aggregate_stats: Aggregate statistics across successful runs.
        runs: Ordered run results included in the final report.
        best_run_id: Identifier of the winning run when available.
        warnings: Session-level warning messages.
    """

    session_id: str
    config_file: str
    mode: str
    started_at: str
    finished_at: str
    elapsed_ms: float
    problem_summary: LabProblemSummary
    output_config: LabOutputConfig
    search_summary: LabSearchSummary
    ranking_metric: str
    budget_summary: dict[str, int | str | None]
    aggregate_stats: LabAggregateStats
    runs: list[LabRunResult] = Field(default_factory=list)
    best_run_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
