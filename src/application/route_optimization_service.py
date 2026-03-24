"""Application service that orchestrates route optimization workflows."""

import logging
from collections.abc import Callable
from typing import Any

from src.domain.interfaces.geo_graph.graph_generator import IGraphGenerator
from src.domain.interfaces.geo_graph.route_calculator import IRouteCalculator
from src.domain.interfaces.plotting.plotter import IPlotter
from src.domain.models.genetic_algorithm.engine.generation_record import (
    GenerationRecord,
)
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.domain.models.route_optimization.fleet_route_info import FleetRouteInfo
from src.domain.models.route_optimization.route_ga_execution_bundle import (
    RouteGAExecutionBundle,
)
from src.domain.models.route_optimization.optimization_result import OptimizationResult
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.vehicle_route_info import VehicleRouteInfo
from src.infrastructure.genetic_algorithm_execution_runner import (
    GeneticAlgorithmExecutionRunner,
)


class RouteOptimizationService:
    """High-level service coordinating graph generation, optimization, and post-processing."""

    def __init__(
        self,
        graph_generator: IGraphGenerator,
        route_calculator_factory: Callable[..., IRouteCalculator],
        execution_bundle_factory: Callable[..., RouteGAExecutionBundle],
        execution_runner: GeneticAlgorithmExecutionRunner[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
            OptimizationResult,
        ],
        plotter_factory: Callable[..., IPlotter] | None = None,
        logger: Callable[[str], None] | logging.Logger | None = None,
    ):
        """Initialize the service with its dependencies.

        Args:
            graph_generator: Responsible for building the graph and route nodes.
            route_calculator_factory: Factory callable for route calculators.
            execution_bundle_factory: Factory callable for route execution bundles.
            execution_runner: Generic runner used to execute one prepared bundle.
            plotter_factory: Optional factory for creating a plotter.
            logger: Optional runtime logger.
        """
        self._graph_generator: IGraphGenerator = graph_generator
        self._route_calculator_factory: Callable[..., IRouteCalculator] = (
            route_calculator_factory
        )
        self._execution_bundle_factory: Callable[..., RouteGAExecutionBundle] = (
            execution_bundle_factory
        )
        self._execution_runner = execution_runner
        self._plotter_factory: Callable[..., IPlotter] | None = plotter_factory
        if isinstance(logger, logging.Logger):
            self._logger = logger.debug
        else:
            self._logger = logger

    def _log(self, message: str) -> None:
        """Emit one runtime message when a logger is configured."""
        if self._logger is not None:
            self._logger(message)

    def _handle_generation(
        self,
        record: GenerationRecord,
        evaluated_solution: EvaluatedRouteSolution,
        plotter: IPlotter | None,
    ) -> None:
        """Handle one evaluated generation emitted by the generic runner.

        Args:
            record: Structured runtime record for the generation.
            evaluated_solution: Best evaluated route solution of the generation.
            plotter: Optional plotter used to visualize progress.
        """
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

    def optimize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
        max_generation: int = 50,
        max_processing_time: int = 10000,
        vehicle_count: int = 1,
        population_size: int = 10,
        weight_type: str = "eta",
        cost_type: str | None = "priority",
        adaptive_config: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        """Optimize routes for the given origin and destinations.

        This method orchestrates graph generation, route calculation, genetic
        optimization, and coordinate conversion back to latitude/longitude.

        Args:
            origin: Starting location, either as an address string or (lat, lon).
            destinations: List of (location, priority) tuples.
            max_generation: Maximum number of GA generations to run.
            max_processing_time: Maximum time in milliseconds to spend optimizing.
            vehicle_count: Number of vehicles to route.
            population_size: Size of the genetic algorithm population.
            weight_type: Weighting strategy for route calculation (e.g., "eta").
            cost_type: Optional cost adjustment strategy.
            adaptive_config: Adaptive GA state-graph configuration.

        Returns:
            An OptimizationResult containing the best found routes and metrics.

        Raises:
            ValueError: If the adaptive GA configuration is not provided.
        """
        if adaptive_config is None:
            raise ValueError("adaptive_config is required")

        self._log("Initializing graph and route nodes...")
        context = self._graph_generator.initialize(origin, destinations)

        self._log("Creating route calculator...")
        route_calculator = self._route_calculator_factory(context.graph)

        plotter = None
        if self._plotter_factory:
            self._log("Creating plotter...")
            plotter = self._plotter_factory(context)

        self._log("Creating execution bundle with route calculator...")
        execution_bundle = self._execution_bundle_factory(
            route_calculator,
            context.route_nodes,
            weight_type,
            cost_type,
            population_size,
            vehicle_count,
            adaptive_config=adaptive_config,
        )

        self._log("Creating coordinate converter...")
        coordinate_converter = self._graph_generator.build_coordinate_converter(context)

        self._log("Running optimization...")
        self._log(f"Running optimizer with vehicle_count={vehicle_count}")
        generation_records: list[GenerationRecord] = []
        result = self._execution_runner.run(
            problem=execution_bundle.problem,
            seed_data=execution_bundle.seed_data,
            state_controller=execution_bundle.state_controller,
            population_size=execution_bundle.population_size,
            max_generations=max_generation,
            max_processing_time=max_processing_time,
            logger=self._logger,
            on_generation=generation_records.append,
            on_generation_evaluated=lambda record, evaluated_solution: self._handle_generation(
                record,
                evaluated_solution,
                plotter,
            ),
        )
        result.generation_records = generation_records
        self._log("Best routes by vehicle:")
        for info in result.best_route.routes_by_vehicle:
            nodes = " -> ".join([seg.name for seg in info.segments])
            self._log(f"  Vehicle {info.vehicle_id}: {nodes}")
        self._log(f"Total aggregated cost: {result.best_route.total_cost or 0.0}")

        self._log("Converting optimized route coordinates back to lat/lon...")
        converted_route = self._convert_fleet_route_coordinates(
            result.best_route,
            coordinate_converter,
        )
        result = OptimizationResult(
            best_route=converted_route,
            best_fitness=result.best_fitness,
            population_size=result.population_size,
            generations_run=result.generations_run,
            generation_records=result.generation_records,
        )

        return result

    def _convert_fleet_route_coordinates(
        self,
        fleet_route: FleetRouteInfo,
        coordinate_converter: Callable[[float, float], tuple[float, float]],
    ) -> FleetRouteInfo:
        """Convert all route coordinates from projected CRS back to lat/lon.

        Args:
            fleet_route: The computed fleet route in projected coordinate space.
            coordinate_converter: Callable that converts (x, y) to (lat, lon).

        Returns:
            A FleetRouteInfo instance with converted coordinates.
        """
        converted_routes = [
            self._convert_vehicle_route_coordinates(route, coordinate_converter)
            for route in fleet_route.routes_by_vehicle
        ]
        return FleetRouteInfo.from_vehicle_routes(converted_routes)

    def _convert_vehicle_route_coordinates(
        self,
        route: VehicleRouteInfo,
        coordinate_converter: Callable[[float, float], tuple[float, float]],
    ) -> VehicleRouteInfo:
        """Convert a single vehicle route's segment coordinates.

        Args:
            route: The vehicle route to convert.
            coordinate_converter: Callable that converts (x, y) to (lat, lon).

        Returns:
            A VehicleRouteInfo with converted segment and path coordinates.
        """
        converted_segments = [
            self._convert_segment_coordinates(segment, coordinate_converter)
            for segment in route.segments
        ]
        return VehicleRouteInfo(
            vehicle_id=route.vehicle_id,
            segments=converted_segments,
            total_eta=route.total_eta,
            total_length=route.total_length,
            total_cost=route.total_cost,
        )

    def _convert_segment_coordinates(
        self,
        segment: RouteSegment,
        coordinate_converter: Callable[[float, float], tuple[float, float]],
    ) -> RouteSegment:
        """Convert the coordinates for a single route segment.

        Args:
            segment: The segment whose coordinates are in projected CRS.
            coordinate_converter: Callable that converts (x, y) to (lat, lon).

        Returns:
            A new RouteSegment with converted coords and path.
        """
        coords = coordinate_converter(*segment.coords)
        path = [coordinate_converter(*point) for point in segment.path]
        return RouteSegment(
            start=segment.start,
            end=segment.end,
            eta=segment.eta,
            length=segment.length,
            path=path,
            segment=segment.segment,
            name=segment.name,
            coords=coords,
            cost=segment.cost,
        )
