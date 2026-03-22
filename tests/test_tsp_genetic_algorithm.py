import os
import random
import sys
import copy
import networkx as nx

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.domain.models.geo_graph.route_node import RouteNode
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.domain.models.route_optimization.route_segment import RouteSegment
from src.domain.models.route_optimization.route_segments_info import RouteSegmentsInfo
from src.domain.models.genetic_algorithm.engine.configured_state import ConfiguredState
from src.domain.models.genetic_algorithm.engine.generation_operators import (
    GenerationOperators,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_crossover_strategy import (
    IGeneticCrossoverStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_mutation_strategy import (
    IGeneticMutationStrategy,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_population_generator import (
    IGeneticPopulationGenerator,
)
from src.domain.interfaces.genetic_algorithm.operators.ga_selection_strategy import (
    IGeneticSelectionStrategy,
)
from src.domain.interfaces.geo_graph.route_calculator import IRouteCalculator
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.infrastructure.genetic_algorithm import (
    AdjacencyEtaPopulationDistanceStrategy,
    CycleCrossoverStrategy,
    ConfiguredGeneticStateController,
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
from src.infrastructure.tsp_genetic_problem import TSPGeneticProblem


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


class StubSelectionStrategy(
    IGeneticSelectionStrategy[RouteGeneticSolution, EvaluatedRouteSolution]
):
    def __init__(self):
        self.called = False

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def select_parents(self, population, evaluated_population):
        self.called = True
        return population[0].clone(), population[-1].clone()


class StubCrossoverStrategy(IGeneticCrossoverStrategy[RouteGeneticSolution]):
    def __init__(self):
        self.called = False

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def crossover(self, parent1, parent2):
        self.called = True
        return parent1.clone()


class StubMutationStrategy(IGeneticMutationStrategy[RouteGeneticSolution]):
    def __init__(self):
        self.called = False

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def mutate(self, solution, mutation_probability):
        self.called = True
        return solution.clone()


class StubPopulationGenerator(
    IGeneticPopulationGenerator[RoutePopulationSeedData, RouteGeneticSolution]
):
    def __init__(self):
        self.called = False

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def generate(self, seed_data, population_size):
        self.called = True
        origin = seed_data.route_nodes[0]
        destinations = seed_data.route_nodes[1:]
        vehicle_slots = max(1, seed_data.vehicle_count)
        base_routes = [[origin] for _ in range(vehicle_slots)]
        for index, destination in enumerate(destinations):
            base_routes[index % vehicle_slots].append(destination)
        return [
            RouteGeneticSolution(copy.deepcopy(base_routes))
            for _ in range(population_size)
        ]

    def inject(self, population, seed_data, injection_size, context=None):
        _ = population
        _ = context
        return self.generate(seed_data, injection_size)


def make_nodes(destination_count):
    nodes = [RouteNode("Origin", 1, (0.0, 0.0))]
    for index in range(destination_count):
        node_id = index + 2
        nodes.append(
            RouteNode(f"Node {node_id}", node_id, (float(node_id), float(node_id)))
        )
    return nodes


def flatten_destination_ids(individual):
    if hasattr(individual, "individual"):
        individual = individual.individual
    return [node.node_id for route in individual for node in route[1:]]


def route_signature(individual):
    if hasattr(individual, "individual"):
        individual = individual.individual
    return tuple(tuple(node.node_id for node in route) for route in individual)


def build_single_state_adaptive_optimizer(adjacency_matrix, population_size=10):
    """Create one optimizer using a single-state adaptive controller."""
    heuristic_generator = HeuristicPopulationGenerator(
        AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    )
    state_controller = ConfiguredGeneticStateController(
        initial_state="baseline",
        states=[
            ConfiguredState(
                name="baseline",
                operators=GenerationOperators(
                    selection=RoulleteSelectionStrategy(),
                    crossover=OrderCrossoverStrategy(),
                    mutation=SwapAndRedistributeMutationStrategy(),
                    mutation_probability=0.5,
                    population_generator=HybridPopulationGenerator(
                        RandomPopulationGenerator(),
                        heuristic_generator,
                    ),
                ),
            )
        ],
    )
    return TSPGeneticAlgorithm(
        adjacency_matrix,
        population_size=population_size,
        state_controller=state_controller,
    )


def build_stub_state_controller(
    selection_strategy,
    crossover_strategy,
    mutation_strategy,
    population_generator,
    mutation_probability=0.5,
):
    """Build one single-state adaptive controller for test doubles."""
    return ConfiguredGeneticStateController(
        initial_state="baseline",
        states=[
            ConfiguredState(
                name="baseline",
                operators=GenerationOperators(
                    selection=selection_strategy,
                    crossover=crossover_strategy,
                    mutation=mutation_strategy,
                    mutation_probability=mutation_probability,
                    population_generator=population_generator,
                ),
            )
        ],
    )


def test_generate_random_population_allows_empty_vehicles():
    random.seed(0)
    nodes = make_nodes(2)

    population = RandomPopulationGenerator().generate(
        RoutePopulationSeedData(route_nodes=nodes, vehicle_count=5),
        population_size=1,
    )

    assert len(population) == 1
    assert len(population[0].individual) == 5
    assert sum(1 for route in population[0].individual if len(route) == 1) >= 3
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
        RoutePopulationSeedData(route_nodes=nodes, vehicle_count=2),
        population_size=5,
    )

    assert len(population) == 5
    assert all(len(individual.individual) == 2 for individual in population)
    assert all(
        sorted(flatten_destination_ids(individual)) == [2, 3, 4, 5]
        for individual in population
    )
    assert len({route_signature(individual) for individual in population}) >= 2


def test_order_crossover_preserves_all_destinations_and_origins():
    random.seed(1)
    origin, n2, n3, n4, n5 = make_nodes(4)
    parent1 = [[origin, n2, n3], [origin, n4, n5]]
    parent2 = [[origin, n5], [origin, n3, n2, n4]]

    child = OrderCrossoverStrategy().crossover(
        RouteGeneticSolution(parent1),
        RouteGeneticSolution(parent2),
    )

    assert len(child.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in child.individual)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_partially_mapped_crossover_preserves_all_destinations_and_origins():
    random.seed(11)
    origin, n2, n3, n4, n5, n6 = make_nodes(5)
    parent1 = [[origin, n2, n3, n4], [origin, n5, n6]]
    parent2 = [[origin, n6, n4], [origin, n5, n2, n3]]

    child = PartiallyMappedCrossoverStrategy().crossover(
        RouteGeneticSolution(parent1),
        RouteGeneticSolution(parent2),
    )

    assert len(child.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in child.individual)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id, n6.node_id]
    )


def test_cycle_crossover_preserves_all_destinations_and_origins():
    random.seed(23)
    origin, n2, n3, n4, n5, n6 = make_nodes(5)
    parent1 = [[origin, n2, n3, n4], [origin, n5, n6]]
    parent2 = [[origin, n4, n6], [origin, n2, n5, n3]]

    child = CycleCrossoverStrategy().crossover(
        RouteGeneticSolution(parent1),
        RouteGeneticSolution(parent2),
    )

    assert len(child.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in child.individual)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id, n6.node_id]
    )


def test_edge_recombination_crossover_preserves_all_destinations_and_origins():
    random.seed(29)
    origin, n2, n3, n4, n5, n6 = make_nodes(5)
    parent1 = [[origin, n2, n3, n4], [origin, n5, n6]]
    parent2 = [[origin, n6, n4], [origin, n3, n5, n2]]

    child = EdgeRecombinationCrossoverStrategy().crossover(
        RouteGeneticSolution(parent1),
        RouteGeneticSolution(parent2),
    )

    assert len(child.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in child.individual)
    assert sorted(flatten_destination_ids(child)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id, n6.node_id]
    )


def test_mutate_preserves_all_destinations_and_origins():
    random.seed(2)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3], [origin], [origin, n4, n5]]

    mutated = SwapAndRedistributeMutationStrategy().mutate(
        RouteGeneticSolution(individual),
        mutation_probability=1.0,
    )

    assert len(mutated.individual) == 3
    assert all(route[0].node_id == origin.node_id for route in mutated.individual)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_two_opt_mutation_preserves_all_destinations_and_origins():
    random.seed(17)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3, n4, n5], [origin]]

    mutated = TwoOptMutationStrategy().mutate(
        RouteGeneticSolution(individual),
        mutation_probability=1.0,
    )

    assert len(mutated.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in mutated.individual)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_inversion_mutation_preserves_all_destinations_and_origins():
    random.seed(31)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2, n3, n4, n5], [origin]]

    mutated = InversionMutationStrategy().mutate(
        RouteGeneticSolution(individual),
        mutation_probability=1.0,
    )

    assert len(mutated.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in mutated.individual)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_inversion_mutation_respects_zero_probability():
    random.seed(37)
    origin, n2, n3, n4 = make_nodes(3)
    individual = [[origin, n2, n3, n4], [origin]]

    mutated = InversionMutationStrategy().mutate(
        RouteGeneticSolution(individual),
        mutation_probability=0.0,
    )

    assert route_signature(mutated) == route_signature(individual)


def test_insertion_mutation_preserves_all_destinations_and_origins():
    random.seed(41)
    origin, n2, n3, n4, n5 = make_nodes(4)
    individual = [[origin, n2], [origin, n3, n4, n5]]

    mutated = InsertionMutationStrategy().mutate(
        RouteGeneticSolution(individual),
        mutation_probability=1.0,
    )

    assert len(mutated.individual) == 2
    assert all(route[0].node_id == origin.node_id for route in mutated.individual)
    assert sorted(flatten_destination_ids(mutated)) == sorted(
        [n2.node_id, n3.node_id, n4.node_id, n5.node_id]
    )


def test_insertion_mutation_respects_zero_probability():
    random.seed(43)
    origin, n2, n3, n4 = make_nodes(3)
    individual = [[origin, n2], [origin, n3, n4]]

    mutated = InsertionMutationStrategy().mutate(
        RouteGeneticSolution(individual),
        mutation_probability=0.0,
    )

    assert route_signature(mutated) == route_signature(individual)


def test_solve_keeps_requested_vehicle_count_even_with_empty_routes():
    random.seed(3)
    calculator = FakeRouteCalculator()
    nodes = make_nodes(2)
    adjacency_matrix = build_adjacency_matrix(calculator, nodes)
    optimizer = build_single_state_adaptive_optimizer(
        adjacency_matrix,
        population_size=4,
    )

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
    assert all(
        route.segments[0].start == 1 for route in result.best_route.routes_by_vehicle
    )
    assert all(
        route.segments[0].end == 1 for route in result.best_route.routes_by_vehicle
    )
    assert result.best_route.min_vehicle_eta == 0
    assert result.best_route.max_vehicle_eta >= 0


def test_problem_build_seed_data_preserves_route_inputs():
    nodes = make_nodes(3)
    problem = TSPGeneticProblem({})

    seed_data = problem.build_seed_data(nodes, vehicle_count=4)

    assert seed_data.route_nodes == nodes
    assert seed_data.vehicle_count == 4


def test_solve_uses_injected_ga_components():
    random.seed(5)
    calculator = FakeRouteCalculator()
    nodes = make_nodes(2)
    adjacency_matrix = build_adjacency_matrix(calculator, nodes)
    selection_strategy = StubSelectionStrategy()
    crossover_strategy = StubCrossoverStrategy()
    mutation_strategy = StubMutationStrategy()
    population_generator = StubPopulationGenerator()
    state_controller = build_stub_state_controller(
        selection_strategy,
        crossover_strategy,
        mutation_strategy,
        population_generator,
    )
    optimizer = TSPGeneticAlgorithm(
        adjacency_matrix,
        population_size=2,
        state_controller=state_controller,
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


def test_optimizer_requires_adaptive_state_controller():
    """Ensure the optimizer fails fast when no adaptive controller is provided."""
    try:
        TSPGeneticAlgorithm(adjacency_matrix={})
    except ValueError as error:
        assert "state_controller is required" in str(error)
    else:
        raise AssertionError("optimizer should require an adaptive state controller")
