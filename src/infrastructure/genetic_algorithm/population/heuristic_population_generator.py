import copy
import random

import numpy as np
from shapely.geometry import MultiPoint, Polygon
from sklearn.cluster import KMeans

from src.domain.interfaces import IHeuristicDistanceStrategy, IPopulationGenerator
from src.domain.models import Individual, Population, RouteNode, VehicleRoute


class HeuristicPopulationGenerator(IPopulationGenerator):
    """Generate seed populations using clustering and ordering heuristics."""

    _HULL_MIN_CLUSTER_SIZE = 6

    def __init__(self, distance_strategy: IHeuristicDistanceStrategy):
        """Initialize the generator with a heuristic distance strategy.

        Args:
            distance_strategy: Used to estimate distances between route nodes
                when ordering and clustering destinations.
        """
        self._distance_strategy = distance_strategy

    def _require_distance(self, start_node: RouteNode, end_node: RouteNode) -> float:
        """Return a distance value or raise if the metric cannot be computed.

        Args:
            start_node: The source route node.
            end_node: The destination route node.

        Returns:
            The heuristic distance value between the nodes.

        Raises:
            ValueError: If the configured distance strategy returns None.
        """
        distance = self._distance_strategy.distance(start_node, end_node)
        if distance is None:
            raise ValueError(
                "Heuristic distance strategy returned no distance for "
                f"segment {start_node.node_id}->{end_node.node_id}."
            )
        return distance

    def _resolve_mixed_strategy(
        self,
        cluster_nodes: list[RouteNode],
        rng: random.Random,
    ) -> str:
        """Pick a reproducible ordering strategy for mixed heuristic mode.

        If the cluster is large enough to benefit from convex hull ordering, this
        method randomly chooses between nearest-neighbor and hull-guided strategies.

        Args:
            cluster_nodes: Nodes belonging to a cluster.
            rng: A random number generator for reproducibility.

        Returns:
            A string identifying the chosen ordering strategy.
        """
        if not self.should_use_convex_hull(cluster_nodes):
            return "nearest_neighbor"
        return rng.choice(["nearest_neighbor", "hull_guided"])

    def route_distance(self, origin: RouteNode, nodes: list[RouteNode]) -> float:
        """Measure the cumulative heuristic distance of an ordered node path.

        Args:
            origin: The route origin node.
            nodes: An ordered list of subsequent nodes to visit.

        Returns:
            The total heuristic distance across the ordered path.
        """
        total_distance = 0.0
        current = origin
        for node in nodes:
            total_distance += self._require_distance(current, node)
            current = node
        return total_distance

    @staticmethod
    def rotate_nodes(nodes: list[RouteNode], start_node: RouteNode) -> list[RouteNode]:
        """Rotate a cyclic node sequence so it begins at a specific node.

        Args:
            nodes: The cyclic list of nodes.
            start_node: The node to place at the beginning of the sequence.

        Returns:
            A rotated list of nodes starting at start_node.
        """
        start_index = nodes.index(start_node)
        return nodes[start_index:] + nodes[:start_index]

    @staticmethod
    def cluster_destinations(
        destinations: list[RouteNode],
        vehicle_count: int,
        random_state: int | None = None,
    ) -> list[list[RouteNode]]:
        """Split destinations into clusters for each vehicle.

        Clustering is performed using K-Means based on projected coordinates.
        If there are more vehicles than destinations, each destination is assigned
        to its own cluster.

        Args:
            destinations: The list of destination nodes to cluster.
            vehicle_count: The number of vehicles (clusters) to create.
            random_state: Optional random seed for reproducible clustering.

        Returns:
            A list of clusters where each cluster is a list of RouteNode instances.
        """
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

    def order_by_nearest_neighbor(
        self,
        origin: RouteNode,
        nodes: list[RouteNode],
    ) -> list[RouteNode]:
        """Order cluster nodes greedily using the current distance strategy.

        Starting from the origin, each step selects the closest remaining node.

        Args:
            origin: The starting node for the route.
            nodes: The nodes to order.

        Returns:
            An ordered list of nodes following a nearest-neighbor heuristic.
        """
        remaining_nodes = nodes[:]
        ordered_nodes: list[RouteNode] = []
        current_node = origin
        while remaining_nodes:
            next_node = min(
                remaining_nodes,
                key=lambda node: self._require_distance(current_node, node),
            )
            ordered_nodes.append(next_node)
            remaining_nodes.remove(next_node)
            current_node = next_node
        return ordered_nodes

    @staticmethod
    def extract_hull_nodes(nodes: list[RouteNode]) -> list[RouteNode]:
        """Return the destination nodes that lie on the convex hull boundary.

        Args:
            nodes: A list of route nodes.

        Returns:
            A list of nodes whose coordinates lie on the convex hull boundary,
            ordered according to the hull exterior.
        """
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
    def should_use_convex_hull(cls, nodes: list[RouteNode]) -> bool:
        """Determine if convex hull ordering should be applied.

        Args:
            nodes: A list of nodes in a cluster.

        Returns:
            True if the cluster is large enough and the hull covers a sufficient
            fraction of nodes to make hull-guided ordering beneficial.
        """
        if len(nodes) < cls._HULL_MIN_CLUSTER_SIZE:
            return False
        hull_nodes = cls.extract_hull_nodes(nodes)
        if len(hull_nodes) < 3:
            return False
        hull_ratio = len(hull_nodes) / len(nodes)
        return hull_ratio >= 0.5

    def best_insertion_index(
        self,
        origin: RouteNode,
        ordered_nodes: list[RouteNode],
        candidate: RouteNode,
    ) -> int:
        """Return the insertion index that minimally increases route length.

        Args:
            origin: The origin node for the route.
            ordered_nodes: The current ordered list of nodes.
            candidate: The node to insert.

        Returns:
            The index at which inserting the candidate yields the minimal total
            route length increase.
        """
        best_index = 0
        best_delta = float("inf")
        for index in range(len(ordered_nodes) + 1):
            previous_node = origin if index == 0 else ordered_nodes[index - 1]
            next_node = ordered_nodes[index] if index < len(ordered_nodes) else None
            added_distance = self._require_distance(previous_node, candidate)
            removed_distance = 0.0
            if next_node is not None:
                added_distance += self._require_distance(candidate, next_node)
                removed_distance = self._require_distance(
                    previous_node,
                    next_node,
                )
            delta = added_distance - removed_distance
            if delta < best_delta:
                best_delta = delta
                best_index = index
        return best_index

    def order_with_convex_hull(
        self,
        origin: RouteNode,
        nodes: list[RouteNode],
    ) -> list[RouteNode]:
        """Order nodes by hull traversal plus best-position insertion.

        This strategy first orders the convex hull nodes in the direction that
        minimizes the heuristic route length, then inserts interior nodes at the
        position that causes the least additional distance.

        Args:
            origin: The starting node.
            nodes: The nodes to order.

        Returns:
            An ordered list of nodes representing the hull-guided route.
        """
        hull_nodes = self.extract_hull_nodes(nodes)
        if len(hull_nodes) < 3:
            return self.order_by_nearest_neighbor(origin, nodes)

        entry_node = min(
            hull_nodes,
            key=lambda node: self._require_distance(origin, node),
        )
        clockwise = self.rotate_nodes(hull_nodes, entry_node)
        counterclockwise = self.rotate_nodes(list(reversed(hull_nodes)), entry_node)
        ordered_nodes = min(
            (clockwise, counterclockwise),
            key=lambda candidate: self.route_distance(origin, candidate),
        )

        hull_node_ids = {node.node_id for node in hull_nodes}
        interior_nodes = [node for node in nodes if node.node_id not in hull_node_ids]
        for node in interior_nodes:
            insertion_index = self.best_insertion_index(origin, ordered_nodes, node)
            ordered_nodes.insert(insertion_index, node)
        return ordered_nodes

    def order_cluster_destinations(
        self,
        origin: RouteNode,
        cluster_nodes: list[RouteNode],
        strategy: str = "nearest_neighbor",
    ) -> list[RouteNode]:
        """Order the destinations in a cluster using a chosen heuristic.

        Args:
            origin: The route origin node.
            cluster_nodes: The nodes to order.
            strategy: The ordering strategy to use ("nearest_neighbor" or "hull_guided").

        Returns:
            An ordered list of cluster nodes.
        """
        if len(cluster_nodes) < 2:
            return cluster_nodes[:]
        if strategy == "hull_guided" and self.should_use_convex_hull(cluster_nodes):
            return self.order_with_convex_hull(origin, cluster_nodes)
        return self.order_by_nearest_neighbor(origin, cluster_nodes)

    def build_clustered_individual(
        self,
        origin: RouteNode,
        clustered_destinations: list[list[RouteNode]],
        ordering_strategy: str = "mixed",
        rng: random.Random | None = None,
    ) -> Individual:
        """Build one valid individual from already-clustered destinations.

        Args:
            origin: The route origin node.
            clustered_destinations: A list of destination clusters (one per vehicle).
            ordering_strategy: Ordering heuristic to apply per cluster.
            rng: Optional random number generator for reproducibility.

        Returns:
            An Individual containing one route per vehicle.
        """
        strategy_rng = rng or random.Random()
        individual: Individual = []
        for cluster in clustered_destinations:
            strategy = ordering_strategy
            if ordering_strategy == "mixed":
                strategy = self._resolve_mixed_strategy(cluster, strategy_rng)
            ordered_cluster = self.order_cluster_destinations(origin, cluster, strategy)
            individual.append([origin, *ordered_cluster])
        return individual

    @staticmethod
    def perturb_clustered_individual(
        individual: Individual,
        intensity: int = 1,
        rng: random.Random | None = None,
    ) -> Individual:
        """Apply small local perturbations to diversify heuristic seeds.

        The method randomly chooses route segments and applies swap / insert /
        reverse mutations to introduce variation.

        Args:
            individual: The base individual to perturb.
            intensity: Controls the number of perturbation operations applied.
            rng: Optional random generator for reproducibility.

        Returns:
            A new Individual with perturbations applied.
        """
        strategy_rng = rng or random.Random()
        perturbed = copy.deepcopy(individual)
        for _ in range(max(1, intensity)):
            candidate_routes = [route for route in perturbed if len(route) > 2]
            if not candidate_routes:
                break
            route = strategy_rng.choice(candidate_routes)
            positions = list(range(1, len(route)))
            if len(positions) < 2:
                continue
            mutation_type = strategy_rng.choice(("swap", "insert", "reverse"))
            first_index, second_index = sorted(strategy_rng.sample(positions, 2))
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

    def generate(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Return a heuristic-only initial population.

        This generator creates seed solutions by clustering destinations per vehicle
        and ordering within each cluster based on heuristic distance strategies.

        Args:
            location_list: A vehicle route list where the first node is the origin.
            population_size: Number of individuals to generate.
            vehicle_count: Number of vehicles (clusters) to distribute destinations across.

        Returns:
            A Population of heuristic seed individuals.
        """
        if not location_list or population_size <= 0:
            return []

        origin = location_list[0]
        destinations = location_list[1:]
        vehicle_slots = max(1, vehicle_count)
        heuristic_population: Population = []
        for seed_index in range(population_size):
            strategy_rng = random.Random(seed_index)
            clustered_destinations = self.cluster_destinations(
                destinations,
                vehicle_slots,
                random_state=seed_index,
            )
            individual = self.build_clustered_individual(
                origin,
                clustered_destinations,
                ordering_strategy="mixed",
                rng=strategy_rng,
            )
            if seed_index > 0:
                individual = self.perturb_clustered_individual(
                    individual,
                    intensity=seed_index,
                    rng=strategy_rng,
                )
            heuristic_population.append(individual)
        return heuristic_population
