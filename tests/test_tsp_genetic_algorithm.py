import os
import random
import sys
import copy
import networkx as nx

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.route_segments_info import RouteSegmentsInfo
from src.domain.interfaces.genetic_algorithm.operators.crossover_strategy_legacy import (
    ICrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.mutation_strategy_legacy import (
    IMutationStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.population_generator_legacy import (
    IPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.selection_strategy_legacy import (
    ISelectionStrategy,
)
from src.domain.interfaces.geo_graph.route_calculator import IRouteCalculator
from src.infrastructure.genetic_algorithm import (
    AdjacencyEtaPopulationDistanceStrategy,
    CycleCrossoverStrategy,
    EdgeRecombinationCrossoverStrategy,
    HeuristicPopulationGenerator,
    HybridPopulationGenerator,
    InsertionMutationStrategy,
    InversionMutationStrategy,
    OrderCrossoverStrategy,
    PartiallyMappedCrossoverStrategy,
    RankSelectionStrategy,
    RandomPopulationGenerator,
    RoulleteSelectionStrategy,
    StochasticUniversalSamplingSelectionStrategy,
    SwapAndRedistributeMutationStrategy,
    TournamentSelectionStrategy,
    TwoOptMutationStrategy,
)
from src.infrastructure.route_calculator import build_adjacency_matrix
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm


class FakeRouteCalculator(IRouteCalculator):
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.graph.graph["graph_id"] = "fake-graph"

    @property
    def graph_id(self) -> str:
        return str(self.graph.graph.get("graph_id", "fake-graph"))

    def compute_segment(
        self,
        start_node,
        end_node,
        weight_function=None,
        cost_function=None,
    ):
        eta = abs(end_node.node_id - start_node.node_id) + 1
        cost = cost_function(end_node.node_id, eta) if cost_function else None
        return RouteSegment(
            start=start_node.node_id,
            end=end_node.node_id,
            eta=float(eta),
            length=float(eta * 10),
            path=[start_node.coords, end_node.coords],
            segment=[start_node.node_id, end_node.node_id],
            name=end_node.name,
            coords=end_node.coords,
            cost=float(cost) if cost is not None else None,
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

    def get_weight_function(self, weight_type="eta"):
        if weight_type != "eta":
            raise ValueError(f"Unknown weight type: {weight_type}")
        return lambda *_args, **_kwargs: 1.0

    def get_cost_function(self, cost_type):
        if cost_type in (None, "", "none"):
            return None
        return lambda node_id, eta: float(node_id + eta)


class StubSelectionStrategy(ISelectionStrategy):
    def __init__(self):
        self.called = False

    def select_parents(self, population, evaluated_population, fitness_function):
        self.called = True
        return population[0], population[-1]


class StubCrossoverStrategy(ICrossoverStrategy):
    def __init__(self):
        self.called = False

    def crossover(self, parent1, parent2):
        self.called = True
        return copy.deepcopy(parent1)


class StubMutationStrategy(IMutationStrategy):
    def __init__(self):
        self.called = False

    def mutate(self, solution, mutation_probability):
        self.called = True
        return copy.deepcopy(solution)


class StubPopulationGenerator(IPopulationGenerator):
    def __init__(self):
        self.called = False

    def generate(self, location_list, population_size, vehicle_count):
        self.called = True
        origin = location_list[0]
        destinations = location_list[1:]
        vehicle_slots = max(1, vehicle_count)
        base_routes = [[origin] for _ in range(vehicle_slots)]
        for index, destination in enumerate(destinations):
            base_routes[index % vehicle_slots].append(destination)
        return [copy.deepcopy(base_routes) for _ in range(population_size)]


def make_nodes(destination_count):
    nodes = [RouteNode("Origin", 1, (0.0, 0.0))]
    for index in range(destination_count):
        node_id = index + 2
        nodes.append(RouteNode(f"Node {node_id}", node_id, (float(node_id), float(node_id))))
    return nodes


def flatten_destination_ids(individual):
    return [node.node_id for route in individual for node in route[1:]]


def route_signature(individual):
    return tuple(tuple(node.node_id for node in route) for route in individual)


def build_default_optimizer(adjacency_matrix, population_size=10):
    heuristic_generator = HeuristicPopulationGenerator(
        AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    )
    return TSPGeneticAlgorithm(
        adjacency_matrix,
        population_size=population_size,
        selection_strategy=RoulleteSelectionStrategy(),
        crossover_strategy=OrderCrossoverStrategy(),
        mutation_strategy=SwapAndRedistributeMutationStrategy(),
        population_generator=HybridPopulationGenerator(
            RandomPopulationGenerator(),
            heuristic_generator,
        ),
    )


def test_generate_random_population_allows_empty_vehicles():
    random.seed(0)
    nodes = make_nodes(2)

    population = RandomPopulationGenerator().generate(
        nodes,
        population_size=1,
        vehicle_count=5,
    )

    assert len(population) == 1
    assert len(population[0]) == 5
    assert sum(1 for route in population[0] if len(route) == 1) >= 3
    assert sorted(flatten_destination_ids(population[0])) == [2, 3]


def test_generate_initial_population_returns_hybrid_diverse_population():
    random.seed(7)
    nodes = [
        RouteNode("Origin", 1, (0.0, 0.0)),
        RouteNode("Node 2", 2, (0.0, 1.0)),
        RouteNode("Node 3", 3, (0.0, 2.0)),
        RouteNode("Node 4", 4, (100.0, 100.0)),
        RouteNode("Node 5", 5, (101.0, 100.0)),
    ]

    adjacency_matrix = build_adjacency_matrix(FakeRouteCalculator(), nodes)
    heuristic_generator = HeuristicPopulationGenerator(
        AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    )
    population = HybridPopulationGenerator(
        RandomPopulationGenerator(),
        heuristic_generator,
    ).generate(
        nodes,
        population_size=5,
        vehicle_count=2,
    )

    assert len(population) == 5
    assert all(len(individual) == 2 for individual in population)
    assert all(
        sorted(flatten_destination_ids(individual)) == [2, 3, 4, 5]
        for individual in population
    )
    assert len({route_signature(individual) for individual in population}) >= 2


def test_evaluate_individual_returns_fleet_aggregate_with_empty_vehicle():
    calculator = FakeRouteCalculator()
    optimizer = build_default_optimizer({})
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
    assert fleet_route.min_vehicle_eta == 0
    assert fleet_route.max_vehicle_eta == fleet_route.routes_by_vehicle[0].total_eta


def test_order_crossover_preserves_all_destinations_and_origins():
    random.seed(1)
    origin, n2, n3, n4, n5 = make_nodes(4)
    parent1 = [[origin, n2, n3], [origin, n4, n5]]
    parent2 = [[origin, n5], [origin, n3, n2, n4]]

    child = OrderCrossoverStrategy().crossover(parent1, parent2)

    assert len(child) == 2
    assert all(route[0].node_id == origin.node_id for route in child)
    assert sorted(flatten_destination_ids(child)) == sorted([n2.node_id, n3.node_id, n4.node_id, n5.node_id])


def test_partially_mapped_crossover_preserves_all_destinations_and_origins():
    random.seed(11)
    origin, n2, n3, n4, n5, n6 = make_nodes(5)
    parent1 = [[origin, n2, n3, n4], [origin, n5, n6]]
    parent2 = [[origin, n6, n4], [origin, n5, n2, n3]]

    child = PartiallyMappedCrossoverStrategy().crossover(parent1, parent2)

    assert len(child) == 2
    assert all(route[0].node_id == origin.node_id for route in child)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id, n6.node_id]
    )


def test_cycle_crossover_preserves_all_destinations_and_origins():
    random.seed(23)
    origin, n2, n3, n4, n5, n6 = make_nodes(5)
    parent1 = [[origin, n2, n3, n4], [origin, n5, n6]]
    parent2 = [[origin, n4, n6], [origin, n2, n5, n3]]

    child = CycleCrossoverStrategy().crossover(parent1, parent2)

    assert len(child) == 2
    assert all(route[0].node_id == origin.node_id for route in child)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id, n6.node_id]
    )


def test_edge_recombination_crossover_preserves_all_destinations_and_origins():
    random.seed(29)
    origin, n2, n3, n4, n5, n6 = make_nodes(5)
    parent1 = [[origin, n2, n3, n4], [origin, n5, n6]]
    parent2 = [[origin, n6, n4], [origin, n3, n5, n2]]

    child = EdgeRecombinationCrossoverStrategy().crossover(parent1, parent2)

    assert len(child) == 2
    assert all(route[0].node_id == origin.node_id for route in child)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id, n6.node_id]
    )


def test_mutate_preserves_all_destinations_and_origins():
    random.seed(2)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3], [origin], [origin, n4, n5]]

    mutated = SwapAndRedistributeMutationStrategy().mutate(
        individual,
        mutation_probability=1.0,
    )

    assert len(mutated) == 3
    assert all(route[0].node_id == origin.node_id for route in mutated)
    assert sorted(flatten_destination_ids(mutated)) == sorted([n2.node_id, n3.node_id, n4.node_id, n5.node_id])


def test_two_opt_mutation_preserves_all_destinations_and_origins():
    random.seed(17)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3, n4, n5], [origin]]

    mutated = TwoOptMutationStrategy().mutate(
        individual,
        mutation_probability=1.0,
    )

    assert len(mutated) == 2
    assert all(route[0].node_id == origin.node_id for route in mutated)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_inversion_mutation_preserves_all_destinations_and_origins():
    random.seed(31)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3, n4, n5], [origin]]

    mutated = InversionMutationStrategy().mutate(
        individual,
        mutation_probability=1.0,
    )

    assert len(mutated) == 2
    assert all(route[0].node_id == origin.node_id for route in mutated)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_inversion_mutation_respects_zero_probability():
    random.seed(37)
    origin, n2, n3, n4 = make_nodes(3)
    individual = [[origin, n2, n3, n4], [origin]]

    mutated = InversionMutationStrategy().mutate(
        individual,
        mutation_probability=0.0,
    )

    assert route_signature(mutated) == route_signature(individual)


def test_insertion_mutation_preserves_all_destinations_and_origins():
    random.seed(41)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2], [origin, n3, n4, n5]]

    mutated = InsertionMutationStrategy().mutate(
        individual,
        mutation_probability=1.0,
    )

    assert len(mutated) == 2
    assert all(route[0].node_id == origin.node_id for route in mutated)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_insertion_mutation_respects_zero_probability():
    random.seed(43)
    origin, n2, n3, n4 = make_nodes(3)
    individual = [[origin, n2], [origin, n3, n4]]

    mutated = InsertionMutationStrategy().mutate(
        individual,
        mutation_probability=0.0,
    )

    assert route_signature(mutated) == route_signature(individual)


def test_tournament_selection_returns_population_members():
    random.seed(19)
    nodes = make_nodes(4)
    adjacency_matrix = build_adjacency_matrix(FakeRouteCalculator(), nodes)
    optimizer = build_default_optimizer(adjacency_matrix, population_size=4)
    population = optimizer._population_generator.generate(
        nodes,
        population_size=4,
        vehicle_count=2,
    )
    evaluated_population = [
        optimizer._evaluate_individual(individual, adjacency_matrix)
        for individual in population
    ]

    parent1, parent2 = TournamentSelectionStrategy(tournament_size=2).select_parents(
        population,
        evaluated_population,
        optimizer._fitness,
    )

    assert parent1 in population
    assert parent2 in population


def test_rank_selection_returns_population_members():
    random.seed(47)
    nodes = make_nodes(4)
    adjacency_matrix = build_adjacency_matrix(FakeRouteCalculator(), nodes)
    optimizer = build_default_optimizer(adjacency_matrix, population_size=4)
    population = optimizer._population_generator.generate(
        nodes,
        population_size=4,
        vehicle_count=2,
    )
    evaluated_population = [
        optimizer._evaluate_individual(individual, adjacency_matrix)
        for individual in population
    ]

    parent1, parent2 = RankSelectionStrategy().select_parents(
        population,
        evaluated_population,
        optimizer._fitness,
    )

    assert parent1 in population
    assert parent2 in population


def test_sus_selection_returns_population_members():
    random.seed(53)
    nodes = make_nodes(4)
    adjacency_matrix = build_adjacency_matrix(FakeRouteCalculator(), nodes)
    optimizer = build_default_optimizer(adjacency_matrix, population_size=4)
    population = optimizer._population_generator.generate(
        nodes,
        population_size=4,
        vehicle_count=2,
    )
    evaluated_population = [
        optimizer._evaluate_individual(individual, adjacency_matrix)
        for individual in population
    ]

    parent1, parent2 = StochasticUniversalSamplingSelectionStrategy().select_parents(
        population,
        evaluated_population,
        optimizer._fitness,
    )

    assert parent1 in population
    assert parent2 in population


def test_sus_selection_handles_identical_fitness_values():
    random.seed(59)
    nodes = make_nodes(2)
    origin, n2, n3 = nodes
    individual = [[origin, n2], [origin, n3]]
    population = [copy.deepcopy(individual) for _ in range(4)]
    evaluated_population = [
        RouteSegmentsInfo(
            segments=[],
            total_eta=10.0,
            total_length=100.0,
            total_cost=5.0,
        )
        for _ in range(4)
    ]

    parent1, parent2 = StochasticUniversalSamplingSelectionStrategy().select_parents(
        population,
        evaluated_population,
        lambda info: info.total_eta,
    )

    assert parent1 in population
    assert parent2 in population


def test_solve_keeps_requested_vehicle_count_even_with_empty_routes():
    random.seed(3)
    calculator = FakeRouteCalculator()
    nodes = make_nodes(2)
    adjacency_matrix = build_adjacency_matrix(calculator, nodes)
    optimizer = build_default_optimizer(adjacency_matrix, population_size=4)

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
    assert result.best_route.min_vehicle_eta == 0
    assert result.best_route.max_vehicle_eta >= 0


def test_solve_uses_injected_ga_components():
    random.seed(5)
    calculator = FakeRouteCalculator()
    nodes = make_nodes(2)
    adjacency_matrix = build_adjacency_matrix(calculator, nodes)
    selection_strategy = StubSelectionStrategy()
    crossover_strategy = StubCrossoverStrategy()
    mutation_strategy = StubMutationStrategy()
    population_generator = StubPopulationGenerator()
    optimizer = TSPGeneticAlgorithm(
        adjacency_matrix,
        population_size=2,
        selection_strategy=selection_strategy,
        crossover_strategy=crossover_strategy,
        mutation_strategy=mutation_strategy,
        population_generator=population_generator,
    )

    result = optimizer.solve(
        route_nodes=nodes,
        max_generation=1,
        max_processing_time=1000,
        vehicle_count=2,
    )

    assert population_generator.called is True
    assert selection_strategy.called is True
    assert crossover_strategy.called is True
    assert mutation_strategy.called is True
    assert len(result.best_route.routes_by_vehicle) == 2
