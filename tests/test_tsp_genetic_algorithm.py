import os
import random
import sys

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models import RouteNode, RouteSegment, RouteSegmentsInfo
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm


class FakeRouteCalculator:
    def compute_segment(
        self,
        start_node,
        end_node,
        weight_function=None,
        cost_function=None,
    ):
        eta = abs(end_node.node_id - start_node.node_id) + 1
        cost = cost_function(end_node.node_id, eta) if cost_function else float(eta)
        return RouteSegment(
            start=start_node.node_id,
            end=end_node.node_id,
            eta=float(eta),
            length=float(eta * 10),
            path=[start_node.coords, end_node.coords],
            segment=[start_node.node_id, end_node.node_id],
            name=end_node.name,
            coords=end_node.coords,
            cost=float(cost),
        )

    def compute_route_segments_info(self, segments):
        total_eta = sum(seg.eta for seg in segments)
        total_length = sum(seg.length for seg in segments)
        total_cost = sum(seg.cost or 0.0 for seg in segments)
        return RouteSegmentsInfo(
            segments=segments,
            total_eta=total_eta,
            total_length=total_length,
            total_cost=total_cost,
        )

    def get_weight_function(self):
        return lambda *_args, **_kwargs: 1.0

    def get_cost_function(self, cost_type):
        return lambda node_id, eta: float(node_id + eta)


def make_nodes(destination_count):
    nodes = [RouteNode("Origin", 1, (0.0, 0.0))]
    for index in range(destination_count):
        node_id = index + 2
        nodes.append(RouteNode(f"Node {node_id}", node_id, (float(node_id), float(node_id))))
    return nodes


def flatten_destination_ids(individual):
    return [node.node_id for route in individual for node in route[1:]]


def test_generate_random_population_allows_empty_vehicles():
    random.seed(0)
    nodes = make_nodes(2)

    population = TSPGeneticAlgorithm._generate_random_population(
        nodes,
        population_size=1,
        vehicle_count=5,
    )

    assert len(population) == 1
    assert len(population[0]) == 5
    assert sum(1 for route in population[0] if len(route) == 1) >= 3
    assert sorted(flatten_destination_ids(population[0])) == [2, 3]


def test_evaluate_individual_returns_fleet_aggregate_with_empty_vehicle():
    calculator = FakeRouteCalculator()
    optimizer = TSPGeneticAlgorithm(calculator)
    origin, destination = make_nodes(1)
    cost_function = calculator.get_cost_function("priority")

    adjacency_matrix = {
        (origin.node_id, destination.node_id): calculator.compute_segment(
            origin,
            destination,
            cost_function=cost_function,
        )
    }
    individual = [[origin, destination], [origin]]

    fleet_route = optimizer._evaluate_individual(individual, adjacency_matrix)

    assert len(fleet_route.routes_by_vehicle) == 2
    assert fleet_route.routes_by_vehicle[0].vehicle_id == 1
    assert fleet_route.routes_by_vehicle[1].vehicle_id == 2
    assert fleet_route.routes_by_vehicle[0].segments[0].start == origin.node_id
    assert fleet_route.routes_by_vehicle[0].segments[0].end == origin.node_id
    assert fleet_route.routes_by_vehicle[0].segments[0].name == origin.name
    assert fleet_route.routes_by_vehicle[1].total_eta == 0
    assert fleet_route.routes_by_vehicle[1].total_length == 0
    assert fleet_route.routes_by_vehicle[1].total_cost == 0
    assert fleet_route.routes_by_vehicle[1].segments[0].start == origin.node_id
    assert fleet_route.routes_by_vehicle[1].segments[0].end == origin.node_id
    assert fleet_route.total_cost == fleet_route.routes_by_vehicle[0].total_cost


def test_order_crossover_preserves_all_destinations_and_origins():
    random.seed(1)
    optimizer = TSPGeneticAlgorithm(FakeRouteCalculator())
    origin, n2, n3, n4, n5 = make_nodes(4)
    parent1 = [[origin, n2, n3], [origin, n4, n5]]
    parent2 = [[origin, n5], [origin, n3, n2, n4]]

    child = optimizer._order_crossover(parent1, parent2)

    assert len(child) == 2
    assert all(route[0].node_id == origin.node_id for route in child)
    assert sorted(flatten_destination_ids(child)) == sorted([n2.node_id, n3.node_id, n4.node_id, n5.node_id])


def test_mutate_preserves_all_destinations_and_origins():
    random.seed(2)
    optimizer = TSPGeneticAlgorithm(FakeRouteCalculator())
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3], [origin], [origin, n4, n5]]

    mutated = optimizer._mutate(individual, mutation_probability=1.0)

    assert len(mutated) == 3
    assert all(route[0].node_id == origin.node_id for route in mutated)
    assert sorted(flatten_destination_ids(mutated)) == sorted([n2.node_id, n3.node_id, n4.node_id, n5.node_id])


def test_solve_keeps_requested_vehicle_count_even_with_empty_routes():
    random.seed(3)
    optimizer = TSPGeneticAlgorithm(FakeRouteCalculator(), population_size=4)
    nodes = make_nodes(2)

    result = optimizer.solve(
        route_nodes=nodes,
        max_generation=1,
        max_processing_time=1000,
        vehicle_count=5,
    )

    assert len(result.best_route.routes_by_vehicle) == 5
    assert sorted(
        route.vehicle_id for route in result.best_route.routes_by_vehicle
    ) == [1, 2, 3, 4, 5]
    assert sorted(
        segment.end
        for route in result.best_route.routes_by_vehicle
        for segment in route.segments
        if segment.start != segment.end
    ) == [2, 3]
    assert all(route.segments[0].start == 1 for route in result.best_route.routes_by_vehicle)
    assert all(route.segments[0].end == 1 for route in result.best_route.routes_by_vehicle)
