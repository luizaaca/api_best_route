"""Aggregate benchmark statistics model for the console lab final report."""

from pydantic import BaseModel


class LabAggregateStats(BaseModel):
    """Summarize metrics across all successful benchmark runs.

    Attributes:
        successful_runs: Number of successfully executed runs.
        failed_runs: Number of failed runs.
        best_fitness: Minimum fitness among successful runs.
        worst_fitness: Maximum fitness among successful runs.
        average_fitness: Mean fitness among successful runs.
        median_fitness: Median fitness among successful runs.
        average_elapsed_ms: Mean runtime among all successful runs.
    """

    successful_runs: int
    failed_runs: int
    best_fitness: float | None = None
    worst_fitness: float | None = None
    average_fitness: float | None = None
    median_fitness: float | None = None
    average_elapsed_ms: float | None = None
