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


class TSPGeneticAlgorithm:
    """
    Genetic Algorithm for the Traveling Salesman Problem using the OSMnx graph.

    Optionally accepts an `IPlotter` which will be invoked with the current best
    route after each generation. This allows interactive or incremental
    visualization during long-running optimizations.
    """

    # --- genetic operators formerly in genetic_algorithm_utils ---
    @staticmethod
    def _generate_random_population(location_list: list, population_size: int) -> list:
        if not location_list:
            return []
        origin = location_list[0]
        destinations = location_list[1:]
        import random

        return [
            [origin] + random.sample(destinations, len(destinations))
            for _ in range(population_size)
        ]

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

        Returns:
            OptimizationResult: Contains the best route found (`RouteSegmentsInfo`),
                its fitness value (`best_fitness`), the final population size, and the
                number of generations actually executed.
        """
        weight_function = self.route_calculator.get_weight_function()
        cost_function = self.route_calculator.get_cost_function("priority")
        adjacency_matrix: dict[tuple[int, int], RouteSegment] = (
            self._generate_adjacency_matrix(route_nodes, weight_function, cost_function)
        )
        population = self._generate_random_population(route_nodes, self.population_size)
        best_fitness = float("inf")
        best_individual: Tuple[list[RouteNode], RouteSegmentsInfo] = (
            [],
            RouteSegmentsInfo(),
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
            population_calculated = [
                self.route_calculator.compute_route_segments_info(
                    [
                        adjacency_matrix[
                            (individual[i].node_id, individual[i + 1].node_id)
                        ]
                        for i in range(len(individual) - 1)
                    ]
                )
                for individual in population
            ]

            population, population_calculated = zip(
                *sorted(
                    zip(population, population_calculated),
                    key=lambda x: x[1].total_cost,
                )
            )
            population = list(population)
            population_calculated = list(population_calculated)

            current_best_fitness = population_calculated[0].total_cost
            if current_best_fitness < best_fitness:
                best_fitness = current_best_fitness
                best_individual = (population[0], population_calculated[0])

            print(f"Generation {generation}: Best fitness = {best_fitness}")
            # if a plotter was injected, show update
            if self._plotter is not None:
                self._plotter.plot(population_calculated[0])

            new_population = [population[0]]

            while len(new_population) < self.population_size:
                fitness_values = [ind.total_cost for ind in population_calculated]
                probability = 1 / np.array(fitness_values)
                parent1, parent2 = random.choices(
                    population, weights=probability.tolist(), k=2
                )
                child = self._order_crossover(parent1, parent2)
                child = self._mutate(child, self.mutation_probability)
                new_population.append(child)

            population = new_population

        best_route = best_individual[1]

        print(
            "Best route: ",
            " -> ".join([segment.name for segment in best_route.segments]),
        )

        return OptimizationResult(
            best_route=best_route,
            best_fitness=best_fitness,
            population_size=len(population),
            generations_run=generation,
        )
