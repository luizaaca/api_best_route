"""Application service that orchestrates route optimization workflows."""

from typing import Callable

from src.domain.interfaces.geo_graph.graph_generator import IGraphGenerator
from src.domain.interfaces.geo_graph.route_calculator import IRouteCalculator
from src.domain.interfaces.plotting.plotter import IPlotter
from src.domain.interfaces.route_optimization.route_optimizer import IRouteOptimizer
from src.domain.models import (
    FleetRouteInfo,
    OptimizationResult,
    RouteNode,
    RouteSegment,
    VehicleRouteInfo,
)


class RouteOptimizationService:
    """High-level service coordinating graph generation, optimization, and post-processing."""

    def __init__(
        self,
        graph_generator: IGraphGenerator,
        route_calculator_factory: Callable[..., IRouteCalculator],
        optimizer_factory: Callable[
            [
                IRouteCalculator,
                list[RouteNode],
                str,
                str | None,
                IPlotter | None,
                int,
            ],
            IRouteOptimizer,
        ],
        plotter_factory: Callable[..., IPlotter] | None = None,
    ):
        """Initialize the service with its dependencies.

        Args:
            graph_generator: Responsible for building the graph and route nodes.
            route_calculator_factory: Factory callable for route calculators.
            optimizer_factory: Factory callable for route optimizers.
            plotter_factory: Optional factory for creating a plotter.
        """
        self._graph_generator: IGraphGenerator = graph_generator
        self._route_calculator_factory: Callable[..., IRouteCalculator] = (
            route_calculator_factory
        )
        self._optimizer_factory: Callable[
            [
                IRouteCalculator,
                list[RouteNode],
                str,
                str | None,
                IPlotter | None,
                int,
            ],
            IRouteOptimizer,
        ] = optimizer_factory
        self._plotter_factory: Callable[..., IPlotter] | None = plotter_factory

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

        Returns:
            An OptimizationResult containing the best found routes and metrics.
        """
        print("Initializing graph and route nodes...")
        context = self._graph_generator.initialize(origin, destinations)

        print("Creating route calculator...")
        route_calculator = self._route_calculator_factory(context.graph)

        plotter = None
        if self._plotter_factory:
            print("Creating plotter...")
            plotter = self._plotter_factory(context)

        print("Creating optimizer with route calculator...")
        optimizer = self._optimizer_factory(
            route_calculator,
            context.route_nodes,
            weight_type,
            cost_type,
            plotter,
            population_size,
        )

        print("Creating coordinate converter...")
        coordinate_converter = self._graph_generator.build_coordinate_converter(context)

        print("Running optimization...")
        result = optimizer.solve(
            route_nodes=context.route_nodes,
            max_generation=max_generation,
            max_processing_time=max_processing_time,
            vehicle_count=vehicle_count,
        )

        print("Converting optimized route coordinates back to lat/lon...")
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
