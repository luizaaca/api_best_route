from typing import Callable
from src.domain.interfaces import (
    IGraphGenerator,
    IRouteCalculator,
    IRouteOptimizer,
    IPlotter,
)
from src.domain.models import OptimizationResult


class RouteOptimizationService:
    def __init__(
        self,
        graph_generator: IGraphGenerator,
        route_calculator_factory: Callable[..., IRouteCalculator],
        optimizer_factory: Callable[
            [IRouteCalculator, IPlotter | None], IRouteOptimizer
        ],
        plotter_factory: Callable[..., IPlotter] | None = None,
    ):
        self._graph_generator: IGraphGenerator = graph_generator
        self._route_calculator_factory: Callable[..., IRouteCalculator] = (
            route_calculator_factory
        )
        self._optimizer_factory: Callable[
            [IRouteCalculator, IPlotter | None], IRouteOptimizer
        ] = optimizer_factory
        self._plotter_factory: Callable[..., IPlotter] | None = plotter_factory

    def optimize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
        max_generation: int = 50,
        max_processing_time: int = 10000,
        vehicle_count: int = 1,
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
        optimizer = self._optimizer_factory(route_calculator, plotter)

        print("Running optimization...")
        result = optimizer.solve(
            route_nodes=context.route_nodes,
            max_generation=max_generation,
            max_processing_time=max_processing_time,
            vehicle_count=vehicle_count,
        )

        print("Converting optimized route segments back to lat/lon...")
        converted_route = self._graph_generator.convert_segments_to_lat_lon(
            context, result.best_route
        )
        result = OptimizationResult(
            best_route=converted_route,
            best_fitness=result.best_fitness,
            population_size=result.population_size,
            generations_run=result.generations_run,
        )

        return result
