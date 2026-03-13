import copy
import time
from typing import Tuple

from src.domain.interfaces import (
    ICrossoverStrategy,
    IMutationStrategy,
    IPlotter,
    IPopulationGenerator,
    IRouteOptimizer,
    ISelectionStrategy,
)
from src.domain.models import (
    FleetRouteInfo,
    Individual,
    OptimizationResult,
    RouteNode,
    RouteSegment,
    RouteSegmentsInfo,
    VehicleRoute,
    VehicleRouteInfo,
)
from src.infrastructure.route_calculator import AdjacencyMatrix


class TSPGeneticAlgorithm(IRouteOptimizer):
    """Genetic Algorithm for multi-vehicle TSP optimization over a fixed adjacency matrix."""

    @staticmethod
    def _build_origin_route_segment(origin: RouteNode) -> RouteSegment:
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
        origin: RouteNode,
        route_info: RouteSegmentsInfo,
    ) -> RouteSegmentsInfo:
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

    @staticmethod
    def _fitness(route_info: FleetRouteInfo) -> float:
        if route_info.total_cost is not None:
            return route_info.total_cost
        return route_info.max_vehicle_eta

    # helper for evaluating an individual comprised of multiple vehicle routes
    def _evaluate_individual(
        self,
        individual: Individual,
        adjacency_matrix: dict[tuple[int, int], RouteSegment],
    ) -> FleetRouteInfo:
        """Return a fleet aggregate containing one route result per vehicle."""
        infos: list[VehicleRouteInfo] = []
        for vehicle_id, route in enumerate(individual, start=1):
            origin = route[0]
            if len(route) < 2:
                infos.append(self._build_empty_vehicle_route_info(route, vehicle_id))
                continue
            segments = [
                adjacency_matrix[(route[i].node_id, route[i + 1].node_id)]
                for i in range(len(route) - 1)
            ]
            route_info = self._prepend_origin_segment(
                origin,
                RouteSegmentsInfo.from_segments(segments),
            )
            infos.append(
                VehicleRouteInfo.from_route_segments_info(vehicle_id, route_info)
            )
        return FleetRouteInfo.from_vehicle_routes(infos)

    # ----------------------------------------------------------

    def __init__(
        self,
        adjacency_matrix: AdjacencyMatrix,
        population_size=10,
        mutation_probability=0.5,
        plotter: IPlotter | None = None,
        selection_strategy: ISelectionStrategy | None = None,
        crossover_strategy: ICrossoverStrategy | None = None,
        mutation_strategy: IMutationStrategy | None = None,
        population_generator: IPopulationGenerator | None = None,
    ):
        """Create an optimizer that delegates GA operations to injected collaborators."""
        if selection_strategy is None:
            raise ValueError("selection_strategy is required")
        if crossover_strategy is None:
            raise ValueError("crossover_strategy is required")
        if mutation_strategy is None:
            raise ValueError("mutation_strategy is required")
        if population_generator is None:
            raise ValueError("population_generator is required")
        self._adjacency_matrix = adjacency_matrix
        self.population_size = population_size
        self.mutation_probability = mutation_probability
        self._plotter = plotter
        self._selection_strategy = selection_strategy
        self._crossover_strategy = crossover_strategy
        self._mutation_strategy = mutation_strategy
        self._population_generator = population_generator

    def solve(
        self,
        route_nodes: list[RouteNode],
        max_generation=50,
        max_processing_time=10000,
        vehicle_count: int = 1,
    ) -> OptimizationResult:
        """
        Solve the Traveling Salesman Problem using a genetic algorithm.

        Pre-computes a full adjacency matrix of `RouteSegment` objects for every ordered
        pair of nodes, then runs a generational loop that evaluates, selects, crosses over,
        and mutates candidate routes. Each generation's fitness is derived from
        `RouteSegmentsInfo.total_cost`, which aggregates the priority-weighted ETA across
        all segments in a route. The best individual found across all generations is returned.

        Args:
            route_nodes (list[RouteNode]): Ordered list of resolved graph nodes that define
                the set of locations to visit. The first node is treated as the fixed origin.
            max_generation (int, optional): Maximum number of generations to run before
                stopping, regardless of convergence. Defaults to 50.
            max_processing_time (int, optional): Wall-clock time limit in milliseconds.
                The loop exits early if this threshold is reached. Defaults to 10000.
            vehicle_count (int, optional): Number of vehicles available for routing.
                Currently this parameter is accepted and passed through but does not
                alter the algorithm's single-vehicle behaviour. Defaults to 1.

        Returns:
            OptimizationResult: Contains the best route found (`RouteSegmentsInfo`),
                its fitness value (`best_fitness`), the final population size, and the
                number of generations actually executed.
        """
        print(f"Running optimizer with vehicle_count={vehicle_count}")
        population = self._population_generator.generate(
            route_nodes, self.population_size, vehicle_count
        )
        if not population:
            return OptimizationResult(
                best_route=FleetRouteInfo(),
                best_fitness=0,
                population_size=0,
                generations_run=0,
            )
        best_fitness = float("inf")
        best_individual: Tuple[Individual, FleetRouteInfo] = (
            [],
            FleetRouteInfo(),
        )
        generation = 0
        start_time = time.time() * 1000

        while generation < max_generation:
            current_time = time.time() * 1000
            if current_time - start_time > max_processing_time:
                print(
                    f"Time limit of {max_processing_time} ms reached. Stopping the algorithm."
                )
                break

            print(f"Processing generation {generation}...")
            generation += 1
            population_calculated: list[FleetRouteInfo] = [
                self._evaluate_individual(individual, self._adjacency_matrix)
                for individual in population
            ]

            population_tuple, population_calculated_tuple = zip(
                *sorted(
                    zip(population, population_calculated),
                    key=lambda x: self._fitness(x[1]),
                )
            )
            population = list(population_tuple)
            population_calculated = list(population_calculated_tuple)

            current_best_fitness = self._fitness(population_calculated[0])
            if current_best_fitness < best_fitness:
                best_fitness = current_best_fitness
                best_individual = (
                    population[0],
                    population_calculated[0],
                )

            print(
                f"Generation {generation}: Best fitness = {best_fitness} - Elapsed time: {current_time - start_time:.2f} ms"
            )
            if self._plotter is not None:
                self._plotter.plot(population_calculated[0])

            new_population = [copy.deepcopy(population[0])]

            while len(new_population) < self.population_size:
                parent1, parent2 = self._selection_strategy.select_parents(
                    population,
                    population_calculated,
                    self._fitness,
                )
                child = self._crossover_strategy.crossover(parent1, parent2)
                child = self._mutation_strategy.mutate(
                    child,
                    self.mutation_probability,
                )
                new_population.append(child)

            population = new_population

        best_route = best_individual[1]
        print("Best routes by vehicle:")
        for info in best_route.routes_by_vehicle:
            nodes = " -> ".join([seg.name for seg in info.segments])
            print(f"  Vehicle {info.vehicle_id}: {nodes}")
        print(f"Total aggregated cost: {best_route.total_cost or 0.0}")

        return OptimizationResult(
            best_route=best_route,
            best_fitness=best_fitness,
            population_size=len(population),
            generations_run=generation,
        )
