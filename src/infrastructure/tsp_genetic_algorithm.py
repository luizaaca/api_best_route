import random
import time
import numpy as np
import copy
from math import dist, floor
from typing import Tuple
from shapely.geometry import MultiPoint, Polygon
from sklearn.cluster import KMeans
from src.domain.interfaces import IRouteCalculator, IPlotter
from src.domain.models import (
    FleetRouteInfo,
    OptimizationResult,
    RouteNode,
    RouteSegmentsInfo,
    RouteSegment,
    VehicleRouteInfo,
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

    _DEFAULT_HEURISTIC_RATIO = 0.4
    _HULL_MIN_CLUSTER_SIZE = 6

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
        destinations (location_list[1:]) are shuffled and distributed randomly,
        allowing vehicles to remain with only the origin when that distribution
        is generated.
        """
        if not location_list:
            return []
        origin = location_list[0]
        destinations = location_list[1:]
        n_dest = len(destinations)
        vc = max(1, vehicle_count)

        pop: list[list[list[RouteNode]]] = []
        for _ in range(population_size):
            shuffled = random.sample(destinations, n_dest)
            groups: list[list[RouteNode]] = [[] for _ in range(vc)]
            for destination in shuffled:
                groups[random.randrange(vc)].append(destination)
            for group in groups:
                random.shuffle(group)
            # prepend origin to each vehicle's route
            groups = [[origin] + g for g in groups]
            pop.append(groups)
        return pop

    @staticmethod
    def _euclidean_distance(left: RouteNode, right: RouteNode) -> float:
        return float(dist(left.coords, right.coords))

    @staticmethod
    def _route_distance(origin: RouteNode, nodes: list[RouteNode]) -> float:
        total_distance = 0.0
        current = origin
        for node in nodes:
            total_distance += TSPGeneticAlgorithm._euclidean_distance(current, node)
            current = node
        return total_distance

    @staticmethod
    def _rotate_nodes(nodes: list[RouteNode], start_node: RouteNode) -> list[RouteNode]:
        start_index = nodes.index(start_node)
        return nodes[start_index:] + nodes[:start_index]

    @staticmethod
    def _cluster_destinations(
        destinations: list[RouteNode],
        vehicle_count: int,
        random_state: int | None = None,
    ) -> list[list[RouteNode]]:
        vehicle_slots = max(1, vehicle_count)
        if not destinations:
            return [[] for _ in range(vehicle_slots)]
        if vehicle_slots == 1:
            return [destinations[:]]

        shuffled_destinations = destinations[:]
        if vehicle_slots >= len(destinations):
            random.Random(random_state).shuffle(shuffled_destinations)
            clusters = [[destination] for destination in shuffled_destinations]
            clusters.extend([[] for _ in range(vehicle_slots - len(destinations))])
            return clusters

        coordinates = np.array([node.coords for node in destinations], dtype=float)
        labels = KMeans(
            n_clusters=vehicle_slots,
            n_init=10,
            random_state=random_state,
        ).fit_predict(coordinates)
        clusters: list[list[RouteNode]] = [[] for _ in range(vehicle_slots)]
        for node, label in zip(destinations, labels):
            clusters[int(label)].append(node)
        return clusters

    @staticmethod
    def _order_by_nearest_neighbor(
        origin: RouteNode,
        nodes: list[RouteNode],
    ) -> list[RouteNode]:
        remaining_nodes = nodes[:]
        ordered_nodes: list[RouteNode] = []
        current_node = origin
        while remaining_nodes:
            next_node = min(
                remaining_nodes,
                key=lambda node: TSPGeneticAlgorithm._euclidean_distance(
                    current_node,
                    node,
                ),
            )
            ordered_nodes.append(next_node)
            remaining_nodes.remove(next_node)
            current_node = next_node
        return ordered_nodes

    @staticmethod
    def _extract_hull_nodes(nodes: list[RouteNode]) -> list[RouteNode]:
        if len(nodes) < 3:
            return []

        hull = MultiPoint([node.coords for node in nodes]).convex_hull
        if not isinstance(hull, Polygon):
            return []

        ordered_coords = list(hull.exterior.coords)[:-1]
        remaining_by_coord: dict[tuple[float, float], list[RouteNode]] = {}
        for node in nodes:
            remaining_by_coord.setdefault(node.coords, []).append(node)

        hull_nodes: list[RouteNode] = []
        for coord in ordered_coords:
            matched_nodes = remaining_by_coord.get((float(coord[0]), float(coord[1])))
            if matched_nodes:
                hull_nodes.append(matched_nodes.pop(0))
        return hull_nodes

    @classmethod
    def _should_use_convex_hull(cls, nodes: list[RouteNode]) -> bool:
        if len(nodes) < cls._HULL_MIN_CLUSTER_SIZE:
            return False
        hull_nodes = cls._extract_hull_nodes(nodes)
        if len(hull_nodes) < 3:
            return False
        hull_ratio = len(hull_nodes) / len(nodes)
        return hull_ratio >= 0.5

    @classmethod
    def _best_insertion_index(
        cls,
        origin: RouteNode,
        ordered_nodes: list[RouteNode],
        candidate: RouteNode,
    ) -> int:
        best_index = 0
        best_delta = float("inf")
        for index in range(len(ordered_nodes) + 1):
            previous_node = origin if index == 0 else ordered_nodes[index - 1]
            next_node = ordered_nodes[index] if index < len(ordered_nodes) else None
            added_distance = cls._euclidean_distance(previous_node, candidate)
            removed_distance = 0.0
            if next_node is not None:
                added_distance += cls._euclidean_distance(candidate, next_node)
                removed_distance = cls._euclidean_distance(previous_node, next_node)
            delta = added_distance - removed_distance
            if delta < best_delta:
                best_delta = delta
                best_index = index
        return best_index

    @classmethod
    def _order_with_convex_hull(
        cls,
        origin: RouteNode,
        nodes: list[RouteNode],
    ) -> list[RouteNode]:
        hull_nodes = cls._extract_hull_nodes(nodes)
        if len(hull_nodes) < 3:
            return cls._order_by_nearest_neighbor(origin, nodes)

        entry_node = min(
            hull_nodes,
            key=lambda node: cls._euclidean_distance(origin, node),
        )
        clockwise = cls._rotate_nodes(hull_nodes, entry_node)
        counterclockwise = cls._rotate_nodes(list(reversed(hull_nodes)), entry_node)
        ordered_nodes = min(
            (clockwise, counterclockwise),
            key=lambda candidate: cls._route_distance(origin, candidate),
        )

        hull_node_ids = {node.node_id for node in hull_nodes}
        interior_nodes = [node for node in nodes if node.node_id not in hull_node_ids]
        for node in interior_nodes:
            insertion_index = cls._best_insertion_index(origin, ordered_nodes, node)
            ordered_nodes.insert(insertion_index, node)
        return ordered_nodes

    @classmethod
    def _order_cluster_destinations(
        cls,
        origin: RouteNode,
        cluster_nodes: list[RouteNode],
        strategy: str = "nearest_neighbor",
    ) -> list[RouteNode]:
        if len(cluster_nodes) < 2:
            return cluster_nodes[:]
        if strategy == "hull_guided" and cls._should_use_convex_hull(cluster_nodes):
            return cls._order_with_convex_hull(origin, cluster_nodes)
        return cls._order_by_nearest_neighbor(origin, cluster_nodes)

    @classmethod
    def _build_clustered_individual(
        cls,
        origin: RouteNode,
        clustered_destinations: list[list[RouteNode]],
        ordering_strategy: str = "mixed",
    ) -> Individual:
        individual: Individual = []
        for cluster in clustered_destinations:
            strategy = ordering_strategy
            if ordering_strategy == "mixed":
                strategy = (
                    "hull_guided"
                    if cls._should_use_convex_hull(cluster)
                    else "nearest_neighbor"
                )
            ordered_cluster = cls._order_cluster_destinations(
                origin,
                cluster,
                strategy,
            )
            individual.append([origin, *ordered_cluster])
        return individual

    @staticmethod
    def _perturb_clustered_individual(
        individual: Individual,
        intensity: int = 1,
    ) -> Individual:
        perturbed = copy.deepcopy(individual)
        for _ in range(max(1, intensity)):
            candidate_routes = [route for route in perturbed if len(route) > 2]
            if not candidate_routes:
                break
            route = random.choice(candidate_routes)
            positions = list(range(1, len(route)))
            if len(positions) < 2:
                continue
            mutation_type = random.choice(("swap", "insert", "reverse"))
            first_index, second_index = sorted(random.sample(positions, 2))
            if mutation_type == "swap":
                route[first_index], route[second_index] = (
                    route[second_index],
                    route[first_index],
                )
            elif mutation_type == "insert":
                node = route.pop(second_index)
                route.insert(first_index, node)
            else:
                route[first_index : second_index + 1] = reversed(
                    route[first_index : second_index + 1]
                )
        return perturbed

    def _generate_initial_population(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        if not location_list or population_size <= 0:
            return []

        origin = location_list[0]
        destinations = location_list[1:]
        vehicle_slots = max(1, vehicle_count)
        heuristic_count = min(
            population_size,
            max(1, int(round(population_size * self._DEFAULT_HEURISTIC_RATIO))),
        )
        heuristic_population: Population = []
        for seed_index in range(heuristic_count):
            clustered_destinations = self._cluster_destinations(
                destinations,
                vehicle_slots,
                random_state=seed_index,
            )
            individual = self._build_clustered_individual(
                origin,
                clustered_destinations,
                ordering_strategy="mixed",
            )
            if seed_index > 0:
                individual = self._perturb_clustered_individual(
                    individual,
                    intensity=seed_index,
                )
            heuristic_population.append(individual)

        random_population = self._generate_random_population(
            location_list,
            population_size - len(heuristic_population),
            vehicle_slots,
        )
        return [*heuristic_population, *random_population][:population_size]

    @staticmethod
    def _order_crossover_sequence(
        parent1: list[RouteNode],
        parent2: list[RouteNode],
    ) -> list[RouteNode]:
        length = len(parent1)
        if length < 2:
            return parent1[:]
        start_index = random.randint(0, length - 1)
        end_index = random.randint(start_index + 1, length)
        child = parent1[start_index:end_index]
        remaining_positions = [
            i for i in range(length) if i < start_index or i >= end_index
        ]
        remaining_genes = [gene for gene in parent2 if gene not in child]
        for position, gene in zip(remaining_positions, remaining_genes):
            child.insert(position, gene)
        return child

    def _choose_child_distribution(
        self,
        parent1: Individual,
        parent2: Individual,
        total_destinations: int,
    ) -> list[int]:
        distribution1 = self._extract_distribution(parent1)
        distribution2 = self._extract_distribution(parent2)
        strategy = random.choice(("parent1", "parent2", "average"))
        if strategy == "parent1":
            return distribution1
        if strategy == "parent2":
            return distribution2
        return self._average_distribution(
            distribution1,
            distribution2,
            total_destinations,
        )

    @staticmethod
    def _extract_distribution(individual: Individual) -> list[int]:
        return [max(0, len(route) - 1) for route in individual]

    @staticmethod
    def _average_distribution(
        distribution1: list[int],
        distribution2: list[int],
        total_destinations: int,
    ) -> list[int]:
        raw_distribution = [
            (left + right) / 2 for left, right in zip(distribution1, distribution2)
        ]
        averaged = [floor(value) for value in raw_distribution]
        remainder = total_destinations - sum(averaged)
        if remainder > 0:
            ranked_indexes = sorted(
                range(len(raw_distribution)),
                key=lambda index: raw_distribution[index] - averaged[index],
                reverse=True,
            )
            for index in ranked_indexes[:remainder]:
                averaged[index] += 1
        return averaged

    @staticmethod
    def _flatten_destinations(individual: Individual) -> list[RouteNode]:
        return [node for route in individual for node in route[1:]]

    @staticmethod
    def _rebuild_individual(
        origin: RouteNode,
        destinations: list[RouteNode],
        distribution: list[int],
    ) -> Individual:
        routes: Individual = []
        offset = 0
        for route_size in distribution:
            vehicle_destinations = destinations[offset : offset + route_size]
            routes.append([origin] + vehicle_destinations)
            offset += route_size
        return routes

    def _order_crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Individual:
        origin = parent1[0][0]
        parent1_destinations = self._flatten_destinations(parent1)
        parent2_destinations = self._flatten_destinations(parent2)
        total_destinations = len(parent1_destinations)
        distribution = self._choose_child_distribution(
            parent1,
            parent2,
            total_destinations,
        )
        if total_destinations == 0:
            return self._rebuild_individual(origin, [], distribution)
        child_destinations = self._order_crossover_sequence(
            parent1_destinations,
            parent2_destinations,
        )
        return self._rebuild_individual(origin, child_destinations, distribution)

    def _mutate(
        self,
        solution: Individual,
        mutation_probability: float,
    ) -> Individual:
        mutated_solution = copy.deepcopy(solution)
        if random.random() < mutation_probability:
            mutation_actions = [self._mutate_distribution, self._mutate_vehicle_order]
            random.shuffle(mutation_actions)
            for mutation_action in mutation_actions[
                : random.randint(1, len(mutation_actions))
            ]:
                mutation_action(mutated_solution)
        return mutated_solution

    @staticmethod
    def _mutate_distribution(solution: Individual) -> None:
        source_indexes = [
            index for index, route in enumerate(solution) if len(route) > 1
        ]
        if not source_indexes:
            return
        source_index = random.choice(source_indexes)
        target_indexes = [
            index for index in range(len(solution)) if index != source_index
        ]
        if not target_indexes:
            return
        target_index = random.choice(target_indexes)
        source_route = solution[source_index]
        target_route = solution[target_index]
        moved_position = random.randint(1, len(source_route) - 1)
        moved_node = source_route.pop(moved_position)
        insert_position = random.randint(1, len(target_route))
        target_route.insert(insert_position, moved_node)

    @staticmethod
    def _mutate_vehicle_order(solution: Individual) -> None:
        candidate_routes = [route for route in solution if len(route) > 2]
        if not candidate_routes:
            return
        route = random.choice(candidate_routes)
        first_index = random.randint(1, len(route) - 1)
        second_index = random.randint(1, len(route) - 1)
        while second_index == first_index and len(route) > 2:
            second_index = random.randint(1, len(route) - 1)
        route[first_index], route[second_index] = (
            route[second_index],
            route[first_index],
        )

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
        return route_info.total_eta

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
        print(f"Running optimizer with vehicle_count={vehicle_count}")
        weight_function = self.route_calculator.get_weight_function()
        cost_function = self.route_calculator.get_cost_function("priority")
        adjacency_matrix: dict[tuple[int, int], RouteSegment] = (
            self._generate_adjacency_matrix(route_nodes, weight_function, cost_function)
        )
        population = self._generate_initial_population(
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
                self._evaluate_individual(individual, adjacency_matrix)
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
                fitness_values = [self._fitness(info) for info in population_calculated]
                probability = np.array(
                    [1 / max(fitness, 1e-9) for fitness in fitness_values]
                )
                parent1, parent2 = random.choices(
                    population, weights=probability.tolist(), k=2
                )
                child = self._order_crossover(parent1, parent2)
                child = self._mutate(child, self.mutation_probability)
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
