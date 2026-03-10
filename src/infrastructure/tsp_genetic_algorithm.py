import random
import time
import numpy as np
from typing import Tuple
from src.domain.interfaces import IRouteCalculator, IPlotter
from src.domain.models import (
    OptimizationResult,
    RouteNode,
    RouteSegmentsInfo,
    RouteSegment,
)

# type aliases to clarify multi-vehicle data structures
VehicleRoute = list[RouteNode]  # single vehicle sequence
Individual = list[VehicleRoute]  # one solution containing all vehicle routes
Population = list[Individual]


class TSPGeneticAlgorithm:
    """
    Genetic Algorithm for the Traveling Salesman Problem using the OSMnx graph.

    Optionally accepts an `IPlotter` which will be invoked with the current best
    route after each generation. This allows interactive or incremental
    visualization during long-running optimizations.
    """

    # --- genetic operators formerly in genetic_algorithm_utils ---
    @staticmethod
    def _generate_random_population(
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Create a population of candidate solutions.

        Each individual is a list of `vehicle_count` routes; every route is itself a
        list of ``RouteNode`` objects that begins with the common origin. The
        destinations (location_list[1:]) are shuffled and partitioned randomly
        so that each vehicle has at least one destination. If ``vehicle_count``
        exceeds the number of destinations we fall back to one-destination-per-
        vehicle until the list is exhausted.
        """
        if not location_list:
            return []
        origin = location_list[0]
        destinations = location_list[1:]
        n_dest = len(destinations)
        # clamp vehicle_count to at most n_dest (each group must have >=1 item)
        vc = min(vehicle_count, n_dest) if n_dest > 0 else 1

        pop: list[list[list[RouteNode]]] = []
        for _ in range(population_size):
            shuffled = random.sample(destinations, n_dest)
            if vc <= 1:
                groups = [shuffled]
            else:
                # choose vc-1 cut points in range 1..n_dest-1
                cuts = sorted(random.sample(range(1, n_dest), vc - 1))
                groups = []
                prev = 0
                for c in cuts:
                    groups.append(shuffled[prev:c])
                    prev = c
                groups.append(shuffled[prev:])
            # prepend origin to each vehicle's route
            groups = [[origin] + g for g in groups]
            pop.append(groups)
        return pop

    @staticmethod
    def _order_crossover(
        parent1: list[RouteNode],
        parent2: list[RouteNode],
    ) -> list[RouteNode]:
        first = parent1[0]
        p1 = parent1[1:]
        p2 = parent2[1:]
        length = len(p1)
        import random

        start_index = random.randint(0, length - 1)
        end_index = random.randint(start_index + 1, length)
        child = p1[start_index:end_index]
        remaining_positions = [
            i for i in range(length) if i < start_index or i >= end_index
        ]
        remaining_genes = [gene for gene in p2 if gene not in child]
        for position, gene in zip(remaining_positions, remaining_genes):
            child.insert(position, gene)
        return [first] + child

    @staticmethod
    def _mutate(
        solution: list[RouteNode],
        mutation_probability: float,
    ) -> list[RouteNode]:
        if len(solution) < 2:
            return solution
        first = solution[0]
        rest = solution[1:]
        import copy, random

        mutated_rest = copy.deepcopy(rest)
        if random.random() < mutation_probability:
            if len(mutated_rest) < 2:
                return [first] + mutated_rest
            index = random.randint(0, len(mutated_rest) - 2)
            mutated_rest[index], mutated_rest[index + 1] = (
                mutated_rest[index + 1],
                mutated_rest[index],
            )
        return [first] + mutated_rest

    def _generate_adjacency_matrix(
        self, route_nodes: list[RouteNode], weight_function, cost_function
    ) -> dict[tuple[int, int], RouteSegment]:
        """
        Generate an adjacency mapping of travel calculations between every pair of nodes.

        Parameters:
        - route_nodes (list[RouteNode]): Resolved graph nodes.
        - weight_function: Callable to compute the weight (e.g., distance) of a segment.
        - cost_function: Callable to compute the cost of a segment based on its eta and node priority.

        Returns:
        dict[tuple[int, int], RouteSegment]: Mapping of (start_node_id, end_node_id) -> RouteSegment.
        """
        matrix: dict[tuple[int, int], RouteSegment] = {}
        for i, from_node in enumerate(route_nodes):
            for j, to_node in enumerate(route_nodes):
                if i == j:
                    continue
                seg = self.route_calculator.compute_segment(
                    start_node=from_node,
                    end_node=to_node,
                    weight_function=weight_function,
                    cost_function=cost_function,
                )
                matrix[(from_node.node_id, to_node.node_id)] = seg
        return matrix

    # helper for evaluating an individual comprised of multiple vehicle routes
    def _evaluate_individual(
        self,
        individual: Individual,
        adjacency_matrix: dict[tuple[int, int], RouteSegment],
    ) -> list[RouteSegmentsInfo]:
        """Return a list of RouteSegmentsInfo, one per vehicle route."""
        infos: list[RouteSegmentsInfo] = []
        for route in individual:
            if len(route) < 2:
                infos.append(
                    RouteSegmentsInfo(
                        segments=[
                            RouteSegment(
                                route[0].node_id,
                                route[0].node_id,
                                0,
                                0,
                                [],
                                [route[0].node_id],
                                route[0].name,
                                route[0].coords,
                                0,
                            )
                        ]
                    )
                )
                continue
            segments = [
                adjacency_matrix[(route[i].node_id, route[i + 1].node_id)]
                for i in range(len(route) - 1)
            ]
            infos.append(self.route_calculator.compute_route_segments_info(segments))
        return infos

    def _aggregate_cost(self, infos: list[RouteSegmentsInfo]) -> float:
        """Return sum of total_cost from a list of RouteSegmentsInfo.

        This helper is used by the genetic loop to compute fitness. It does not
        merge or alter the original objects.
        """
        cost = 0.0
        for info in infos:
            if info.total_cost is not None:
                cost += info.total_cost
        return cost

    # ----------------------------------------------------------

    def __init__(
        self,
        route_calculator: IRouteCalculator,
        population_size=10,
        mutation_probability=0.5,
        plotter: IPlotter | None = None,
    ):
        self.route_calculator = route_calculator
        self.population_size = population_size
        self.mutation_probability = mutation_probability
        self._plotter = plotter

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
        # vehicle_count currently unused internally; log for traceability
        print(f"Running optimizer with vehicle_count={vehicle_count}")
        weight_function = self.route_calculator.get_weight_function()
        cost_function = self.route_calculator.get_cost_function("priority")
        adjacency_matrix: dict[tuple[int, int], RouteSegment] = (
            self._generate_adjacency_matrix(route_nodes, weight_function, cost_function)
        )
        population = self._generate_random_population(
            route_nodes, self.population_size, vehicle_count
        )
        best_fitness = float("inf")
        # store the individual itself along with its per-vehicle infos
        best_individual: Tuple[Individual, list[RouteSegmentsInfo]] = (
            [],
            [],
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
            # evaluate each individual per vehicle
            population_calculated: list[list[RouteSegmentsInfo]] = [
                self._evaluate_individual(ind, adjacency_matrix) for ind in population
            ]

            # sort by aggregated cost across vehicles
            population, population_calculated = zip(
                *sorted(
                    zip(population, population_calculated),
                    key=lambda x: self._aggregate_cost(x[1]),
                )
            )
            population = list(population)
            population_calculated = list(population_calculated)

            current_best_fitness = self._aggregate_cost(population_calculated[0])
            if current_best_fitness < best_fitness:
                best_fitness = current_best_fitness
                # keep raw per-vehicle infos in best_individual
                best_individual = (
                    population[0],
                    population_calculated[0],
                )

            print(
                f"Generation {generation}: Best fitness = {best_fitness} - Elapsed time: {current_time - start_time:.2f} ms"
            )
            # if a plotter was injected, show update
            if self._plotter is not None:
                self._plotter.plot(population_calculated[0])

            new_population = [population[0]]

            while len(new_population) < self.population_size:
                fitness_values = [
                    self._aggregate_cost(infos) for infos in population_calculated
                ]
                probability = 1 / np.array(fitness_values)
                parent1, parent2 = random.choices(
                    population, weights=probability.tolist(), k=2
                )
                # when multiple vehicles are present we simply mutate each
                # route independently instead of crossing between parents
                if vehicle_count > 1:
                    child = [
                        self._mutate(route, self.mutation_probability)
                        for route in parent1
                    ]
                else:
                    child = self._order_crossover(parent1, parent2)
                    child = self._mutate(child, self.mutation_probability)
                new_population.append(child)

            population = new_population

        # best_individual[1] is a list of RouteSegmentsInfo, one per vehicle
        best_route = best_individual[1]
        print("Best routes by vehicle:")
        total_cost = 0.0
        for vidx, info in enumerate(best_route, start=1):
            nodes = " -> ".join([seg.name for seg in info.segments])
            print(f"  Vehicle {vidx}: {nodes}")
            if info.total_cost is not None:
                total_cost += info.total_cost
        print(f"Total aggregated cost: {total_cost}")

        return OptimizationResult(
            best_route=best_route,
            best_fitness=best_fitness,
            population_size=len(population),
            generations_run=generation,
        )
