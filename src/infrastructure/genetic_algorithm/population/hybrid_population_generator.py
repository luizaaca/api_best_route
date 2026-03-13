import copy
import random
from math import dist

import numpy as np
from shapely.geometry import MultiPoint, Polygon
from sklearn.cluster import KMeans

from src.domain.interfaces import IPopulationGenerator
from src.domain.models import Individual, Population, RouteNode, VehicleRoute


class HybridPopulationGenerator(IPopulationGenerator):
    """Bootstrap the GA population with heuristic and random individuals."""

    _DEFAULT_HEURISTIC_RATIO = 0.4
    _HULL_MIN_CLUSTER_SIZE = 6

    def __init__(
        self,
        random_population_generator: IPopulationGenerator,
    ):
        """Create a generator that mixes heuristic and random seeds."""
        self._random_population_generator = random_population_generator

    @staticmethod
    def euclidean_distance(left: RouteNode, right: RouteNode) -> float:
        """Compute the Euclidean distance between two projected route nodes."""
        return float(dist(left.coords, right.coords))

    @classmethod
    def route_distance(cls, origin: RouteNode, nodes: list[RouteNode]) -> float:
        """Measure the path length of a tentative ordered cluster."""
        total_distance = 0.0
        current = origin
        for node in nodes:
            total_distance += cls.euclidean_distance(current, node)
            current = node
        return total_distance

    @staticmethod
    def rotate_nodes(nodes: list[RouteNode], start_node: RouteNode) -> list[RouteNode]:
        """Rotate a cyclic node sequence so it starts at the chosen node."""
        start_index = nodes.index(start_node)
        return nodes[start_index:] + nodes[:start_index]

    @staticmethod
    def cluster_destinations(
        destinations: list[RouteNode],
        vehicle_count: int,
        random_state: int | None = None,
    ) -> list[list[RouteNode]]:
        """Split destinations into one cluster per vehicle slot."""
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

    @classmethod
    def order_by_nearest_neighbor(
        cls,
        origin: RouteNode,
        nodes: list[RouteNode],
    ) -> list[RouteNode]:
        """Order cluster nodes greedily using the nearest-neighbor heuristic."""
        remaining_nodes = nodes[:]
        ordered_nodes: list[RouteNode] = []
        current_node = origin
        while remaining_nodes:
            next_node = min(
                remaining_nodes,
                key=lambda node: cls.euclidean_distance(current_node, node),
            )
            ordered_nodes.append(next_node)
            remaining_nodes.remove(next_node)
            current_node = next_node
        return ordered_nodes

    @staticmethod
    def extract_hull_nodes(nodes: list[RouteNode]) -> list[RouteNode]:
        """Return the destination nodes that lie on the convex hull boundary."""
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
        """Decide whether hull-guided ordering is worthwhile for the cluster."""
        if len(nodes) < cls._HULL_MIN_CLUSTER_SIZE:
            return False
        hull_nodes = cls.extract_hull_nodes(nodes)
        if len(hull_nodes) < 3:
            return False
        hull_ratio = len(hull_nodes) / len(nodes)
        return hull_ratio >= 0.5

    @classmethod
    def best_insertion_index(
        cls,
        origin: RouteNode,
        ordered_nodes: list[RouteNode],
        candidate: RouteNode,
    ) -> int:
        """Return the insertion index that minimally increases route length."""
        best_index = 0
        best_delta = float("inf")
        for index in range(len(ordered_nodes) + 1):
            previous_node = origin if index == 0 else ordered_nodes[index - 1]
            next_node = ordered_nodes[index] if index < len(ordered_nodes) else None
            added_distance = cls.euclidean_distance(previous_node, candidate)
            removed_distance = 0.0
            if next_node is not None:
                added_distance += cls.euclidean_distance(candidate, next_node)
                removed_distance = cls.euclidean_distance(previous_node, next_node)
            delta = added_distance - removed_distance
            if delta < best_delta:
                best_delta = delta
                best_index = index
        return best_index

    @classmethod
    def order_with_convex_hull(
        cls,
        origin: RouteNode,
        nodes: list[RouteNode],
    ) -> list[RouteNode]:
        """Order nodes by hull traversal plus best-position insertion for inner nodes."""
        hull_nodes = cls.extract_hull_nodes(nodes)
        if len(hull_nodes) < 3:
            return cls.order_by_nearest_neighbor(origin, nodes)

        entry_node = min(
            hull_nodes,
            key=lambda node: cls.euclidean_distance(origin, node),
        )
        clockwise = cls.rotate_nodes(hull_nodes, entry_node)
        counterclockwise = cls.rotate_nodes(list(reversed(hull_nodes)), entry_node)
        ordered_nodes = min(
            (clockwise, counterclockwise),
            key=lambda candidate: cls.route_distance(origin, candidate),
        )

        hull_node_ids = {node.node_id for node in hull_nodes}
        interior_nodes = [node for node in nodes if node.node_id not in hull_node_ids]
        for node in interior_nodes:
            insertion_index = cls.best_insertion_index(origin, ordered_nodes, node)
            ordered_nodes.insert(insertion_index, node)
        return ordered_nodes

    @classmethod
    def order_cluster_destinations(
        cls,
        origin: RouteNode,
        cluster_nodes: list[RouteNode],
        strategy: str = "nearest_neighbor",
    ) -> list[RouteNode]:
        """Order the destinations in a cluster with the requested heuristic."""
        if len(cluster_nodes) < 2:
            return cluster_nodes[:]
        if strategy == "hull_guided" and cls.should_use_convex_hull(cluster_nodes):
            return cls.order_with_convex_hull(origin, cluster_nodes)
        return cls.order_by_nearest_neighbor(origin, cluster_nodes)

    @classmethod
    def build_clustered_individual(
        cls,
        origin: RouteNode,
        clustered_destinations: list[list[RouteNode]],
        ordering_strategy: str = "mixed",
    ) -> Individual:
        """Build one valid individual from already-clustered destinations."""
        individual: Individual = []
        for cluster in clustered_destinations:
            strategy = ordering_strategy
            if ordering_strategy == "mixed":
                strategy = (
                    "hull_guided"
                    if cls.should_use_convex_hull(cluster)
                    else "nearest_neighbor"
                )
            ordered_cluster = cls.order_cluster_destinations(origin, cluster, strategy)
            individual.append([origin, *ordered_cluster])
        return individual

    @staticmethod
    def perturb_clustered_individual(
        individual: Individual,
        intensity: int = 1,
    ) -> Individual:
        """Apply small local perturbations to diversify heuristic seeds."""
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

    def generate(
        self,
        location_list: VehicleRoute,
        population_size: int,
        vehicle_count: int,
    ) -> Population:
        """Return a mixed initial population with heuristic and random seeds."""
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
            clustered_destinations = self.cluster_destinations(
                destinations,
                vehicle_slots,
                random_state=seed_index,
            )
            individual = self.build_clustered_individual(
                origin,
                clustered_destinations,
                ordering_strategy="mixed",
            )
            if seed_index > 0:
                individual = self.perturb_clustered_individual(
                    individual,
                    intensity=seed_index,
                )
            heuristic_population.append(individual)

        random_population = self._random_population_generator.generate(
            location_list,
            population_size - len(heuristic_population),
            vehicle_slots,
        )
        return [*heuristic_population, *random_population][:population_size]
