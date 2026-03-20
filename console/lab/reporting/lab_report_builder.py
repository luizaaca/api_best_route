"""Build report models for completed console lab benchmark sessions."""

from datetime import datetime
from statistics import mean, median
from typing import Iterable

from console.lab.models.lab_aggregate_stats import LabAggregateStats
from console.lab.models.lab_benchmark_report import LabBenchmarkReport
from console.lab.models.lab_fleet_route_summary import LabFleetRouteSummary
from console.lab.models.lab_output_config import LabOutputConfig
from console.lab.models.lab_problem_summary import LabProblemSummary
from console.lab.models.lab_run_config import LabRunConfig
from console.lab.models.lab_run_result import LabRunResult
from console.lab.models.lab_search_summary import LabSearchSummary
from console.lab.models.lab_vehicle_route_summary import LabVehicleRouteSummary
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo
from src.domain.models.route_optimization.optimization_result import OptimizationResult
from src.domain.models.route_optimization.vehicle_route_info import VehicleRouteInfo


class LabReportBuilder:
    """Translate benchmark execution data into final report models."""

    @staticmethod
    def _build_vehicle_summary(
        vehicle_route: VehicleRouteInfo,
    ) -> LabVehicleRouteSummary:
        """Build one per-vehicle summary from a route result.

        Args:
            vehicle_route: Vehicle route information returned by the optimizer.

        Returns:
            A compact per-vehicle summary model.
        """
        ordered_stops = [segment.name for segment in vehicle_route.segments]
        return LabVehicleRouteSummary(
            vehicle_id=vehicle_route.vehicle_id,
            stop_count=max(0, len(vehicle_route.segments) - 1),
            total_length=vehicle_route.total_length,
            total_eta=vehicle_route.total_eta,
            total_cost=vehicle_route.total_cost,
            ordered_stops=ordered_stops,
        )

    @staticmethod
    def _build_fleet_summary(fleet_route: FleetRouteInfo) -> LabFleetRouteSummary:
        """Build a fleet-level summary from optimizer output.

        Args:
            fleet_route: Fleet route information returned by the optimizer.

        Returns:
            A fleet-level summary model.
        """
        return LabFleetRouteSummary(
            total_length=fleet_route.total_length,
            min_vehicle_eta=fleet_route.min_vehicle_eta,
            max_vehicle_eta=fleet_route.max_vehicle_eta,
            total_cost=fleet_route.total_cost,
        )

    def build_run_result(
        self,
        run_config: LabRunConfig,
        run_id: str,
        elapsed_ms: float,
        result: OptimizationResult | None = None,
        error_message: str | None = None,
        warnings: list[str] | None = None,
    ) -> LabRunResult:
        """Build one run result model from execution data.

        Args:
            run_config: Resolved run configuration.
            run_id: Stable run identifier.
            elapsed_ms: Measured execution time in milliseconds.
            result: Optional optimizer output when execution succeeds.
            error_message: Optional error message when execution fails.
            warnings: Optional per-run warnings.

        Returns:
            A complete per-run result model.
        """
        if result is None:
            return LabRunResult(
                run_id=run_id,
                run_index=run_config.source_index,
                label=run_config.label,
                status="failed",
                error_message=error_message,
                elapsed_ms=elapsed_ms,
                resolved_config=run_config,
                warnings=warnings or [],
            )

        vehicle_summaries = [
            self._build_vehicle_summary(vehicle_route)
            for vehicle_route in result.best_route.routes_by_vehicle
        ]
        return LabRunResult(
            run_id=run_id,
            run_index=run_config.source_index,
            label=run_config.label,
            status="success",
            elapsed_ms=elapsed_ms,
            best_fitness=result.best_fitness,
            population_size=result.population_size,
            generations_run=result.generations_run,
            resolved_config=run_config,
            fleet_summary=self._build_fleet_summary(result.best_route),
            vehicle_summaries=vehicle_summaries,
            warnings=warnings or [],
        )

    @staticmethod
    def _sort_runs(runs: Iterable[LabRunResult]) -> list[LabRunResult]:
        """Return run results sorted for ranking and final reporting.

        Args:
            runs: Run results collected during the benchmark session.

        Returns:
            A list ordered by success, fitness, and elapsed time.
        """
        return sorted(
            runs,
            key=lambda run: (
                run.status != "success",
                float("inf") if run.best_fitness is None else run.best_fitness,
                run.elapsed_ms,
                run.run_index,
            ),
        )

    @staticmethod
    def _build_problem_summary(run_config: LabRunConfig) -> LabProblemSummary:
        """Build the shared problem summary from one resolved run config.

        Args:
            run_config: Resolved run configuration representative of the session.

        Returns:
            A compact session-level problem summary.
        """
        return LabProblemSummary(
            origin=str(run_config.origin),
            destination_count=len(run_config.destinations),
            vehicle_count=run_config.vehicle_count,
            weight_type=run_config.weight_type,
            cost_type=run_config.cost_type,
            destination_priority_summary=[
                destination.priority for destination in run_config.destinations
            ],
        )

    @staticmethod
    def _build_budget_summary(
        runs: list[LabRunResult],
    ) -> dict[str, int | str | None]:
        """Build a compact budget summary across resolved runs.

        Args:
            runs: Sorted run results for the benchmark session.

        Returns:
            A dictionary describing the requested generation and time budgets.
        """
        generations = [run.resolved_config.max_generation for run in runs]
        times = [run.resolved_config.max_processing_time for run in runs]
        return {
            "max_generation_min": min(generations, default=None),
            "max_generation_max": max(generations, default=None),
            "max_processing_time_min": min(times, default=None),
            "max_processing_time_max": max(times, default=None),
        }

    @staticmethod
    def _build_aggregate_stats(runs: list[LabRunResult]) -> LabAggregateStats:
        """Build aggregate benchmark statistics across successful runs.

        Args:
            runs: Sorted run results for the benchmark session.

        Returns:
            Aggregate benchmark statistics.
        """
        successful_runs = [run for run in runs if run.status == "success"]
        failed_runs = [run for run in runs if run.status != "success"]
        fitness_values = [
            run.best_fitness for run in successful_runs if run.best_fitness is not None
        ]
        elapsed_values = [run.elapsed_ms for run in successful_runs]
        return LabAggregateStats(
            successful_runs=len(successful_runs),
            failed_runs=len(failed_runs),
            best_fitness=min(fitness_values) if fitness_values else None,
            worst_fitness=max(fitness_values) if fitness_values else None,
            average_fitness=mean(fitness_values) if fitness_values else None,
            median_fitness=median(fitness_values) if fitness_values else None,
            average_elapsed_ms=mean(elapsed_values) if elapsed_values else None,
        )

    def build_report(
        self,
        config_file: str,
        output_config: LabOutputConfig,
        search_summary: LabSearchSummary,
        started_at: datetime,
        finished_at: datetime,
        runs: list[LabRunResult],
        session_warnings: list[str] | None = None,
    ) -> LabBenchmarkReport:
        """Build the root benchmark report for one completed session.

        Args:
            config_file: Source config file path.
            search_summary: Search summary produced by the config expander.
            started_at: Session start timestamp.
            finished_at: Session completion timestamp.
            runs: Collected run results.
            session_warnings: Optional session-level warnings.

        Returns:
            A complete benchmark report model.
        """
        sorted_runs = self._sort_runs(runs)
        representative_run = sorted_runs[0].resolved_config
        best_run = next((run for run in sorted_runs if run.status == "success"), None)
        return LabBenchmarkReport(
            session_id=f"lab-session-{started_at.strftime('%Y%m%d%H%M%S')}",
            config_file=config_file,
            mode=search_summary.mode,
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            elapsed_ms=(finished_at - started_at).total_seconds() * 1000,
            problem_summary=self._build_problem_summary(representative_run),
            output_config=output_config,
            search_summary=search_summary,
            ranking_metric="best_fitness",
            budget_summary=self._build_budget_summary(sorted_runs),
            aggregate_stats=self._build_aggregate_stats(sorted_runs),
            runs=sorted_runs,
            best_run_id=best_run.run_id if best_run else None,
            warnings=session_warnings or [],
        )
