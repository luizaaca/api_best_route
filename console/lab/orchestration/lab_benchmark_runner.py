"""Sequential benchmark runner for the console lab mode."""

import random
from collections.abc import Callable
from datetime import datetime
from time import perf_counter
from typing import Any

import numpy as np

from console.lab.config import LabConfigLoader, LabRunConfigExpander
from console.lab.models.lab_benchmark_report import LabBenchmarkReport
from console.lab.models.lab_run_config import LabRunConfig
from console.lab.models.lab_session_config import LabSessionConfig
from console.lab.orchestration.lab_optimizer_builder import LabOptimizerBuilder
from console.lab.reporting.lab_report_builder import LabReportBuilder
from console.lab.runtime_logging import emit_runtime_message
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.domain.models.route_optimization.optimization_result import OptimizationResult
from src.infrastructure.genetic_algorithm_execution_runner import (
    GeneticAlgorithmExecutionRunner,
)
from src.infrastructure.route_calculator import AdjacencyMatrix


class LabBenchmarkRunner:
    """Run a complete benchmark session from one lab config file."""

    def __init__(
        self,
        graph_generator,
        route_calculator_factory,
        adjacency_matrix_builder,
        plotter_factory=None,
        logger: Callable[[str], None] | None = None,
        execution_runner: GeneticAlgorithmExecutionRunner[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
            OptimizationResult,
        ]
        | None = None,
    ):
        """Initialize the benchmark runner dependencies.

        Args:
            graph_generator: Graph generator used to initialize shared route data.
            route_calculator_factory: Factory callable creating route calculators.
            adjacency_matrix_builder: Builder used to compute the shared adjacency matrix.
            plotter_factory: Optional factory for creating plotters.
            logger: Optional verbose logger used for runtime messages.
            execution_runner: Optional generic runner used to execute prepared bundles.
        """
        self._graph_generator = graph_generator
        self._route_calculator_factory = route_calculator_factory
        self._adjacency_matrix_builder = adjacency_matrix_builder
        self._plotter_factory = plotter_factory
        self._report_builder = LabReportBuilder()
        self._logger = logger
        self._execution_runner = execution_runner or GeneticAlgorithmExecutionRunner()

    def _log(self, message: str) -> None:
        """Emit one runtime message when verbose logging is enabled."""
        emit_runtime_message(self._logger, message)

    def _handle_generation(
        self,
        record: GenerationRecord,
        evaluated_solution: EvaluatedRouteSolution,
        plotter,
    ) -> None:
        """Handle one evaluated generation emitted by the generic runner."""
        if record.transition_label is not None:
            target_state_name = record.target_state_name or "unknown"
            self._log(
                (
                    f"Generation {record.generation}: transition "
                    f"'{record.transition_label}' ({record.state_name} -> {target_state_name})"
                )
            )
        self._log(
            (
                f"Generation {record.generation}: Best fitness = {record.best_fitness} "
                f"- Elapsed time: {record.elapsed_time_ms:.2f} ms"
            )
        )
        if plotter is not None:
            plotter.plot(evaluated_solution._route_info)

    @staticmethod
    def _normalize_destinations(
        run_config: LabRunConfig,
    ) -> list[tuple[str | tuple[float, ...], int]]:
        """Return destination tuples compatible with graph initialization.

        Args:
            run_config: Resolved run configuration.

        Returns:
            A list of `(location, priority)` tuples.
        """
        return [
            (
                (
                    tuple(destination.location)
                    if isinstance(destination.location, list)
                    else destination.location
                ),
                destination.priority,
            )
            for destination in run_config.destinations
        ]

    @staticmethod
    def _assert_shared_route_setup(runs: list[LabRunConfig]) -> None:
        """Validate that all runs share the same expensive route-setup inputs.

        Args:
            runs: Resolved benchmark run configurations.

        Raises:
            ValueError: If the session attempts to vary graph or adjacency inputs.
        """
        if not runs:
            raise ValueError("The benchmark session produced no resolved runs")
        first_run = runs[0]
        first_destinations = [
            destination.model_dump() for destination in first_run.destinations
        ]
        for run in runs[1:]:
            if run.origin != first_run.origin:
                raise ValueError("All lab runs must share the same origin")
            if [
                destination.model_dump() for destination in run.destinations
            ] != first_destinations:
                raise ValueError("All lab runs must share the same destinations")
            if run.weight_type != first_run.weight_type:
                raise ValueError("All lab runs must share the same weight_type")
            if run.cost_type != first_run.cost_type:
                raise ValueError("All lab runs must share the same cost_type")

    def _build_shared_adjacency_matrix(
        self,
        run_config: LabRunConfig,
    ) -> tuple[object, list, AdjacencyMatrix]:
        """Build the shared route context and adjacency matrix for the session.

        Args:
            run_config: Representative run configuration for the shared setup.

        Returns:
            A tuple containing the graph context, route nodes, and adjacency matrix.
        """
        self._log("Initializing shared graph context and route nodes...")
        context = self._graph_generator.initialize(
            run_config.origin,
            self._normalize_destinations(run_config),
        )
        self._log("Creating shared route calculator and adjacency matrix...")
        route_calculator = self._route_calculator_factory(context.graph)
        adjacency_matrix = self._adjacency_matrix_builder.build(
            route_calculator=route_calculator,
            route_nodes=context.route_nodes,
            weight_type=run_config.weight_type,
            cost_type=run_config.cost_type,
        )
        self._log("Shared route setup is ready for all resolved runs.")
        return context, context.route_nodes, adjacency_matrix

    @staticmethod
    def _apply_run_seed(run_config: LabRunConfig) -> tuple[Any, Any, bool]:
        """Apply the optional run seed and return the previous RNG states.

        Args:
            run_config: Resolved run configuration for the upcoming execution.

        Returns:
            A tuple containing the previous Python RNG state, previous NumPy RNG
            state, and a flag indicating whether a seed was applied.
        """
        previous_random_state = random.getstate()
        previous_numpy_state = np.random.get_state()
        if run_config.seed is None:
            return previous_random_state, previous_numpy_state, False
        random.seed(run_config.seed)
        np.random.seed(run_config.seed)
        return previous_random_state, previous_numpy_state, True

    @staticmethod
    def _restore_run_seed(
        previous_random_state: Any,
        previous_numpy_state: Any,
        seed_was_applied: bool,
    ) -> None:
        """Restore RNG states after one seeded run completes.

        Args:
            previous_random_state: Python RNG state captured before the run.
            previous_numpy_state: NumPy RNG state captured before the run.
            seed_was_applied: Whether the run applied an explicit seed.
        """
        if not seed_was_applied:
            return
        random.setstate(previous_random_state)
        np.random.set_state(previous_numpy_state)

    def run(
        self,
        config_file: str,
        session_config: LabSessionConfig | None = None,
    ) -> LabBenchmarkReport:
        """Execute one benchmark session from a JSON configuration file.

        Args:
            config_file: Path to the lab JSON configuration file.
            session_config: Optional preloaded session configuration model.

        Returns:
            The final benchmark report for the session.
        """
        started_at = datetime.now()
        if session_config is None:
            self._log(f"Loading lab config from '{config_file}'...")
            session_config = LabConfigLoader.load(config_file)
        else:
            self._log(f"Using preloaded lab config from '{config_file}'.")
        resolved_runs, search_summary = LabRunConfigExpander.expand(session_config)
        self._log(
            f"Resolved {len(resolved_runs)} run(s) for mode '{search_summary.mode}'."
        )
        self._assert_shared_route_setup(resolved_runs)

        context, route_nodes, adjacency_matrix = self._build_shared_adjacency_matrix(
            resolved_runs[0]
        )
        session_warnings: list[str] = []
        if len(resolved_runs) > 1 and session_config.output.plot:
            session_warnings.append(
                "Plotting is enabled in a multi-run sequential benchmark and may distort elapsed-time comparisons."
            )

        run_results = []
        for index, run_config in enumerate(resolved_runs, start=1):
            self._log(
                (
                    f"Starting run {index}/{len(resolved_runs)}: '{run_config.label}' "
                    f"(population_size={run_config.population_size}, "
                    f"initial_state={run_config.state_config.initial_state}, "
                    f"max_generation={run_config.max_generation})."
                )
            )
            plotter = None
            if session_config.output.plot and self._plotter_factory is not None:
                self._log(f"Creating plotter for run '{run_config.label}'.")
                plotter = self._plotter_factory(context)
            previous_random_state, previous_numpy_state, seed_was_applied = (
                self._apply_run_seed(run_config)
            )
            self._log(f"Building execution bundle for run '{run_config.label}'.")
            execution_bundle = LabOptimizerBuilder.build(
                run_config=run_config,
                adjacency_matrix=adjacency_matrix,
                route_nodes=route_nodes,
                logger=self._logger,
            )
            started_run = perf_counter()
            try:
                self._log(
                    f"Running optimizer with vehicle_count={run_config.vehicle_count}"
                )
                generation_records: list[GenerationRecord] = []
                optimization_result = self._execution_runner.run(
                    problem=execution_bundle.problem,
                    seed_data=execution_bundle.seed_data,
                    state_controller=execution_bundle.state_controller,
                    population_size=execution_bundle.population_size,
                    max_generations=run_config.max_generation,
                    max_processing_time=run_config.max_processing_time,
                    logger=self._logger,
                    on_generation=generation_records.append,
                    on_generation_evaluated=lambda record, evaluated_solution: self._handle_generation(
                        record,
                        evaluated_solution,
                        plotter,
                    ),
                )
                optimization_result.generation_records = generation_records
                elapsed_ms = (perf_counter() - started_run) * 1000
                self._log(
                    (
                        f"Run '{run_config.label}' finished successfully in "
                        f"{elapsed_ms:.2f} ms with best fitness "
                        f"{optimization_result.best_fitness:.2f}."
                    )
                )
                run_results.append(
                    self._report_builder.build_run_result(
                        run_config=run_config,
                        run_id=f"run-{index:03d}",
                        elapsed_ms=elapsed_ms,
                        result=optimization_result,
                    )
                )
            except Exception as error:
                elapsed_ms = (perf_counter() - started_run) * 1000
                self._log(
                    (
                        f"Run '{run_config.label}' failed after {elapsed_ms:.2f} ms: "
                        f"{error}"
                    )
                )
                run_results.append(
                    self._report_builder.build_run_result(
                        run_config=run_config,
                        run_id=f"run-{index:03d}",
                        elapsed_ms=elapsed_ms,
                        error_message=str(error),
                    )
                )
            finally:
                self._restore_run_seed(
                    previous_random_state,
                    previous_numpy_state,
                    seed_was_applied,
                )

        finished_at = datetime.now()
        self._log("Benchmark session finished; building final report.")
        return self._report_builder.build_report(
            config_file=config_file,
            output_config=session_config.output,
            search_summary=search_summary,
            started_at=started_at,
            finished_at=finished_at,
            runs=run_results,
            session_warnings=session_warnings,
        )
