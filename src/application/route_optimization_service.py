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
        plotter: IPlotter | None = None,
    ):
        self._graph_generator = graph_generator
        self._route_calculator_factory = route_calculator_factory
        self._optimizer_factory = optimizer_factory
        self._plotter = plotter

    def optimize(
        self,
        origin: str | tuple[float, float],
        destinations: list[tuple[str | tuple[float, float], int]],
        max_generation: int = 50,
        max_processing_time: int = 10000,
    ) -> OptimizationResult:
        context = self._graph_generator.initialize(origin, destinations)

        route_calculator = self._route_calculator_factory(context.graph)
        optimizer = self._optimizer_factory(route_calculator, self._plotter)

        result = optimizer.solve(
            route_nodes=context.route_nodes,
            max_generation=max_generation,
            max_processing_time=max_processing_time,
        )

        return result
