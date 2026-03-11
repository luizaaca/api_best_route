from typing import Callable
from src.domain.interfaces import (
    IGraphGenerator,
    IRouteCalculator,
    IRouteOptimizer,
    IPlotter,
)
from src.domain.models import (
    FleetRouteInfo,
    OptimizationResult,
    RouteNode,
    RouteSegment,
    VehicleRouteInfo,
)


class RouteOptimizationService:
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
        )

        return result

    def _convert_fleet_route_coordinates(
        self,
        fleet_route: FleetRouteInfo,
        coordinate_converter: Callable[[float, float], tuple[float, float]],
    ) -> FleetRouteInfo:
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
