"""Route-domain problem adapter for the generic GA engine."""

from __future__ import annotations

from typing import Sequence

from src.domain.interfaces.genetic_algorithm.ga_problem import IGeneticProblem
from src.domain.models.evaluated_route_solution import EvaluatedRouteSolution
from src.domain.models.genetic_algorithm import VehicleRoute
from src.domain.models.optimization import OptimizationResult
from src.domain.models.route import (
    FleetRouteInfo,
    RouteSegment,
    RouteSegmentsInfo,
    VehicleRouteInfo,
)
from src.domain.models.route_genetic_solution import RouteGeneticSolution
from src.infrastructure.route_calculator import AdjacencyMatrix


class TSPGeneticProblem(
    IGeneticProblem[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        OptimizationResult,
    ]
):
    """Adapt the multi-vehicle routing problem to the generic GA engine."""

    def __init__(self, adjacency_matrix: AdjacencyMatrix) -> None:
        """Store the adjacency matrix used for route evaluation.

        Args:
            adjacency_matrix: Precomputed route-segment adjacency matrix.
        """
        self._adjacency_matrix = adjacency_matrix

    @staticmethod
    def _build_origin_route_segment(origin) -> RouteSegment:
        """Create a zero-length route segment representing the route origin."""
        return RouteSegment(
            start=origin.node_id,
            end=origin.node_id,
            eta=0,
            length=0,
            path=[],
            segment=[origin.node_id],
            name=origin.name,
            coords=origin.coords,
            cost=0,
        )

    @classmethod
    def _prepend_origin_segment(
        cls,
        origin,
        route_info: RouteSegmentsInfo,
    ) -> RouteSegmentsInfo:
        """Ensure the origin segment appears at the beginning of a route."""
        return RouteSegmentsInfo(
            segments=[cls._build_origin_route_segment(origin), *route_info.segments],
            total_eta=route_info.total_eta,
            total_length=route_info.total_length,
            total_cost=route_info.total_cost,
        )

    @classmethod
    def _build_empty_vehicle_route_info(
        cls,
        route: VehicleRoute,
        vehicle_id: int,
    ) -> VehicleRouteInfo:
        """Produce vehicle route info for an empty route."""
        origin = route[0]
        route_info = cls._prepend_origin_segment(
            origin,
            RouteSegmentsInfo(
                total_eta=0,
                total_length=0,
                total_cost=0,
            ),
        )
        return VehicleRouteInfo.from_route_segments_info(vehicle_id, route_info)

    def _evaluate_individual(self, solution: RouteGeneticSolution) -> FleetRouteInfo:
        """Evaluate one wrapped route solution into fleet route metrics.

        Args:
            solution: Wrapped raw route solution.

        Returns:
            Fleet-level route metrics for the evaluated individual.
        """
        infos: list[VehicleRouteInfo] = []
        for vehicle_id, route in enumerate(solution.individual, start=1):
            origin = route[0]
            if len(route) < 2:
                infos.append(self._build_empty_vehicle_route_info(route, vehicle_id))
                continue
            segments = [
                self._adjacency_matrix[(route[index].node_id, route[index + 1].node_id)]
                for index in range(len(route) - 1)
            ]
            route_info = self._prepend_origin_segment(
                origin,
                RouteSegmentsInfo.from_segments(segments),
            )
            infos.append(
                VehicleRouteInfo.from_route_segments_info(vehicle_id, route_info)
            )
        return FleetRouteInfo.from_vehicle_routes(infos)

    def evaluate_solution(
        self,
        solution: RouteGeneticSolution,
    ) -> EvaluatedRouteSolution:
        """Evaluate one wrapped route solution for the generic engine."""
        route_info = self._evaluate_individual(solution)
        return EvaluatedRouteSolution(solution=solution, route_info=route_info)

    def evaluate_population(
        self,
        population: Sequence[RouteGeneticSolution],
    ) -> list[EvaluatedRouteSolution]:
        """Evaluate an entire population of wrapped route solutions."""
        return [self.evaluate_solution(solution) for solution in population]

    def build_empty_result(self) -> OptimizationResult:
        """Return the empty optimization result for an empty population."""
        return OptimizationResult(
            best_route=FleetRouteInfo(),
            best_fitness=0,
            population_size=0,
            generations_run=0,
        )

    def build_result(
        self,
        best_evaluated_solution: EvaluatedRouteSolution,
        population_size: int,
        generations_run: int,
    ) -> OptimizationResult:
        """Build the route-domain optimization result returned to callers."""
        return OptimizationResult(
            best_route=best_evaluated_solution._route_info,
            best_fitness=best_evaluated_solution.fitness,
            population_size=population_size,
            generations_run=generations_run,
        )
