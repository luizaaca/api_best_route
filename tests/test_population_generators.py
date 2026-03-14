import os
import random
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models import RouteNode
from src.infrastructure.genetic_algorithm import (
    AdjacencyCostPopulationDistanceStrategy,
    AdjacencyEtaPopulationDistanceStrategy,
    EuclideanPopulationDistanceStrategy,
    HeuristicPopulationGenerator,
)
from src.infrastructure.route_calculator import build_adjacency_matrix

from tests.test_tsp_genetic_algorithm import FakeRouteCalculator


def make_nodes(destination_count):
    nodes = [RouteNode("Origin", 1, (0.0, 0.0))]
    for index in range(destination_count):
        node_id = index + 2
        nodes.append(
            RouteNode(f"Node {node_id}", node_id, (float(node_id), float(node_id)))
        )
    return nodes


def flatten_destination_ids(individual):
    return [node.node_id for route in individual for node in route[1:]]


def test_cluster_destinations_groups_spatially_close_nodes():
    generator = HeuristicPopulationGenerator(EuclideanPopulationDistanceStrategy())
    n2 = RouteNode("Node 2", 2, (0.0, 1.0))
    n3 = RouteNode("Node 3", 3, (0.0, 2.0))
    n4 = RouteNode("Node 4", 4, (100.0, 100.0))
    n5 = RouteNode("Node 5", 5, (101.0, 100.0))

    clusters = generator.cluster_destinations(
        [n2, n3, n4, n5],
        vehicle_count=2,
        random_state=0,
    )

    cluster_sets = {frozenset(node.node_id for node in cluster) for cluster in clusters}
    assert cluster_sets == {frozenset({2, 3}), frozenset({4, 5})}


def test_cluster_destinations_handles_more_vehicles_than_destinations():
    generator = HeuristicPopulationGenerator(EuclideanPopulationDistanceStrategy())
    nodes = make_nodes(2)[1:]

    clusters = generator.cluster_destinations(
        nodes,
        vehicle_count=5,
        random_state=0,
    )

    assert len(clusters) == 5
    assert sum(1 for cluster in clusters if not cluster) == 3
    assert sorted(node.node_id for cluster in clusters for node in cluster) == [2, 3]


def test_build_clustered_individual_preserves_origin_and_uniqueness():
    generator = HeuristicPopulationGenerator(EuclideanPopulationDistanceStrategy())
    origin, n2, n3, n4, n5 = make_nodes(4)

    individual = generator.build_clustered_individual(
        origin,
        [[n2, n3], [n4, n5], []],
    )

    assert len(individual) == 3
    assert all(route[0].node_id == origin.node_id for route in individual)
    assert sorted(flatten_destination_ids(individual)) == [2, 3, 4, 5]


def test_adjacency_eta_distance_strategy_reads_precomputed_segments():
    calculator = FakeRouteCalculator()
    origin, destination = make_nodes(1)
    adjacency_matrix = build_adjacency_matrix(calculator, [origin, destination])
    strategy = AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)

    assert strategy.distance(origin, destination) == adjacency_matrix[(1, 2)].eta


def test_heuristic_population_generator_uses_distance_strategy():
    random.seed(5)
    nodes = make_nodes(4)
    adjacency_matrix = build_adjacency_matrix(FakeRouteCalculator(), nodes)
    generator = HeuristicPopulationGenerator(
        AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    )

    population = generator.generate(nodes, population_size=3, vehicle_count=2)

    assert len(population) == 3
    assert all(len(individual) == 2 for individual in population)
    assert all(
        sorted(flatten_destination_ids(individual)) == [2, 3, 4, 5]
        for individual in population
    )


def test_adjacency_cost_distance_strategy_returns_none_without_cost():
    calculator = FakeRouteCalculator()
    origin, destination = make_nodes(1)
    adjacency_matrix = build_adjacency_matrix(
        calculator,
        [origin, destination],
        cost_type=None,
    )
    strategy = AdjacencyCostPopulationDistanceStrategy(adjacency_matrix)

    assert strategy.distance(origin, destination) is None


def test_heuristic_population_generator_fails_clearly_when_distance_missing():
    calculator = FakeRouteCalculator()
    nodes = make_nodes(2)
    adjacency_matrix = build_adjacency_matrix(calculator, nodes, cost_type=None)
    generator = HeuristicPopulationGenerator(
        AdjacencyCostPopulationDistanceStrategy(adjacency_matrix)
    )

    with pytest.raises(ValueError, match="returned no distance"):
        generator.generate(nodes, population_size=1, vehicle_count=1)


def test_mixed_ordering_diversifies_heuristic_population_when_hull_is_eligible():
    origin = RouteNode("Origin", 1, (0.0, 0.0))
    destinations = [
        RouteNode("Node 2", 2, (0.0, 10.0)),
        RouteNode("Node 3", 3, (10.0, 10.0)),
        RouteNode("Node 4", 4, (10.0, 0.0)),
        RouteNode("Node 5", 5, (5.0, -5.0)),
        RouteNode("Node 6", 6, (4.0, 4.0)),
        RouteNode("Node 7", 7, (6.0, 5.0)),
    ]
    generator = HeuristicPopulationGenerator(EuclideanPopulationDistanceStrategy())

    individuals = [
        generator.build_clustered_individual(
            origin,
            [destinations],
            ordering_strategy="mixed",
            rng=random.Random(seed),
        )
        for seed in range(6)
    ]

    assert len({tuple(flatten_destination_ids(individual)) for individual in individuals}) >= 2
