"""Render final benchmark reports as human-readable console output."""

from console.lab.models.lab_benchmark_report import LabBenchmarkReport
from console.lab.models.lab_run_result import LabRunResult


class LabConsoleReportRenderer:
    """Render a benchmark report into a structured multi-section string."""

    @staticmethod
    def _format_operator_combo(run: LabRunResult) -> str:
        """Return a compact operator-combination string for ranking output.

        Args:
            run: Run result to summarize.

        Returns:
            A compact operator-combination string.
        """
        config = run.resolved_config
        return (
            f"{config.population_generator.name} | {config.selection.name} | "
            f"{config.crossover.name} | {config.mutation.name}"
        )

    @staticmethod
    def render(report: LabBenchmarkReport) -> str:
        """Render the final benchmark report as a console-friendly string.

        Args:
            report: Benchmark report to render.

        Returns:
            A formatted multiline string ready for console output.
        """
        lines: list[str] = []
        lines.append("=== Session summary ===")
        lines.append(f"Config file: {report.config_file}")
        lines.append(f"Mode: {report.mode}")
        lines.append(f"Elapsed: {report.elapsed_ms:.2f} ms")
        lines.append(
            "Runs: "
            f"{len(report.runs)} total | "
            f"{report.aggregate_stats.successful_runs} success | "
            f"{report.aggregate_stats.failed_runs} failed"
        )
        lines.append(f"Ranking metric: {report.ranking_metric}")
        lines.append(f"Budget summary: {report.budget_summary}")
        lines.append(
            "Output: "
            f"plot={report.output_config.plot}, "
            f"verbose={report.output_config.verbose}, "
            f"show_best_run_details={report.output_config.show_best_run_details}"
        )
        lines.append("")

        lines.append("=== Problem summary ===")
        lines.append(f"Origin: {report.problem_summary.origin}")
        lines.append(f"Destinations: {report.problem_summary.destination_count}")
        lines.append(f"Vehicles: {report.problem_summary.vehicle_count}")
        lines.append(f"Weight type: {report.problem_summary.weight_type}")
        lines.append(f"Cost type: {report.problem_summary.cost_type}")
        lines.append("")

        lines.append("=== Search summary ===")
        lines.append(f"Resolved runs: {report.search_summary.resolved_run_count}")
        for key, value in report.search_summary.details.items():
            lines.append(f"{key}: {value}")
        lines.append("")

        lines.append("=== Aggregate stats ===")
        lines.append(f"Best fitness: {report.aggregate_stats.best_fitness}")
        lines.append(f"Worst fitness: {report.aggregate_stats.worst_fitness}")
        lines.append(f"Average fitness: {report.aggregate_stats.average_fitness}")
        lines.append(f"Median fitness: {report.aggregate_stats.median_fitness}")
        lines.append(f"Average elapsed: {report.aggregate_stats.average_elapsed_ms} ms")
        lines.append("")

        lines.append("=== Ranking ===")
        for index, run in enumerate(report.runs, start=1):
            lines.append(
                f"{index:02d}. {run.label} | {LabConsoleReportRenderer._format_operator_combo(run)} | "
                f"fitness={run.best_fitness} | generations={run.generations_run} | "
                f"elapsed={run.elapsed_ms:.2f} ms | status={run.status}"
            )
        lines.append("")

        best_run = next(
            (run for run in report.runs if run.run_id == report.best_run_id),
            None,
        )
        if best_run is not None and report.output_config.show_best_run_details:
            lines.append("=== Best run details ===")
            lines.append(f"Run: {best_run.label} ({best_run.run_id})")
            lines.append(f"Resolved config: {best_run.resolved_config.model_dump()}")
            if best_run.fleet_summary is not None:
                lines.append(
                    "Fleet summary: "
                    f"length={best_run.fleet_summary.total_length:.2f} | "
                    f"min_eta={best_run.fleet_summary.min_vehicle_eta:.2f} | "
                    f"max_eta={best_run.fleet_summary.max_vehicle_eta:.2f} | "
                    f"cost={best_run.fleet_summary.total_cost}"
                )
            for vehicle_summary in best_run.vehicle_summaries:
                lines.append(
                    f"Vehicle {vehicle_summary.vehicle_id}: "
                    f"stops={vehicle_summary.stop_count} | "
                    f"length={vehicle_summary.total_length:.2f} | "
                    f"eta={vehicle_summary.total_eta:.2f} | "
                    f"cost={vehicle_summary.total_cost} | "
                    f"route={vehicle_summary.ordered_stops}"
                )
            lines.append("")

        lines.append("=== Run details ===")
        for run in report.runs:
            lines.append(
                f"- {run.label} ({run.run_id}) => status={run.status}, "
                f"fitness={run.best_fitness}, elapsed={run.elapsed_ms:.2f} ms"
            )
            if run.error_message:
                lines.append(f"  error: {run.error_message}")
            if run.warnings:
                lines.append(f"  warnings: {run.warnings}")
        lines.append("")

        if report.warnings:
            lines.append("=== Warnings ===")
            for warning in report.warnings:
                lines.append(f"- {warning}")

        return "\n".join(lines).strip()
