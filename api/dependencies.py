"""FastAPI dependency definitions for creating optimizer components.

This module provides cached factory functions used by the API to wire up the
route optimization service with default infrastructure implementations.
"""

from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from api.config import load_adaptive_ga_config
from src.application.route_optimization_service import RouteOptimizationService
from src.domain.interfaces.genetic_algorithm.engine.specification import (
    IGeneticSpecification,
)
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
)
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
from src.domain.models.genetic_algorithm.engine.configured_state import ConfiguredState
from src.domain.models.genetic_algorithm.engine.generation_operators import (
    GenerationOperators,
)
from src.domain.models.genetic_algorithm.engine.transition_rule import TransitionRule
from src.domain.models.genetic_algorithm.evaluated_route_solution import (
    EvaluatedRouteSolution,
)
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)
from src.domain.models.geo_graph.route_population_seed_data import (
    RoutePopulationSeedData,
)
from src.infrastructure.caching import (
    CachedAdjacencyMatrixBuilder,
    CachedGeocodingResolver,
    PhotonGeocodingResolver,
    SQLiteAdjacencySegmentCache,
    SQLiteGeocodingCache,
)
from src.infrastructure.genetic_algorithm import (
    AdjacencyCostPopulationDistanceStrategy,
    AdjacencyEtaPopulationDistanceStrategy,
    AdjacencyLengthPopulationDistanceStrategy,
    ConfiguredGeneticStateController,
    EuclideanPopulationDistanceStrategy,
    HeuristicPopulationGenerator,
    ImprovementBelowSpecification,
    HybridPopulationGenerator,
    OrderCrossoverStrategy,
    ProgressAtLeastSpecification,
    RandomPopulationGenerator,
    RoulleteSelectionStrategy,
    StaleAtLeastSpecification,
    SwapAndRedistributeMutationStrategy,
)
from src.infrastructure.genetic_algorithm.crossover import (
    CycleCrossoverStrategy,
    EdgeRecombinationCrossoverStrategy,
    PartiallyMappedCrossoverStrategy,
)
from src.infrastructure.genetic_algorithm.mutation import (
    InsertionMutationStrategy,
    InversionMutationStrategy,
    TwoOptMutationStrategy,
)
from src.infrastructure.genetic_algorithm.selection import (
    RankSelectionStrategy,
    StochasticUniversalSamplingSelectionStrategy,
    TournamentSelectionStrategy,
)
from src.infrastructure.legacy_crossover_strategy_adapter import (
    LegacyCrossoverStrategyAdapter,
)
from src.infrastructure.legacy_mutation_strategy_adapter import (
    LegacyMutationStrategyAdapter,
)
from src.infrastructure.legacy_population_generator_adapter import (
    LegacyPopulationGeneratorAdapter,
)
from src.infrastructure.legacy_selection_strategy_adapter import (
    LegacySelectionStrategyAdapter,
)
from src.infrastructure.osmnx_graph_generator import OSMnxGraphGenerator
from src.infrastructure.route_calculator import RouteCalculator
from src.infrastructure.tsp_genetic_algorithm import TSPGeneticAlgorithm


@lru_cache
def get_geocoding_cache() -> SQLiteGeocodingCache:
    """Return the default persistent geocoding cache."""
    return SQLiteGeocodingCache("cache/geocoding.db")


@lru_cache
def get_adjacency_segment_cache() -> SQLiteAdjacencySegmentCache:
    """Return the default persistent adjacency segment cache."""
    return SQLiteAdjacencySegmentCache("cache/adjacency_segments.db")


@lru_cache
def get_adjacency_matrix_builder() -> CachedAdjacencyMatrixBuilder:
    """Return the default adjacency matrix builder with segment caching."""
    return CachedAdjacencyMatrixBuilder(get_adjacency_segment_cache())


@lru_cache
def get_graph_generator() -> OSMnxGraphGenerator:
    """Return the default graph generator with cached geocoding support."""
    return OSMnxGraphGenerator(
        CachedGeocodingResolver(
            cache=get_geocoding_cache(),
            fallback_resolver=PhotonGeocodingResolver(),
        )
    )


@lru_cache
def get_adaptive_ga_config() -> dict[str, Any]:
    """Return the required API adaptive GA configuration loaded from disk.

    Returns:
        The parsed adaptive GA configuration read from the fixed repository-root
        `config.json` file.

    Raises:
        FileNotFoundError: If the required config file does not exist.
        ValueError: If the config file contents are invalid.
    """
    return load_adaptive_ga_config()


def _build_population_distance_strategy(adjacency_matrix, weight_type, cost_type):
    """Select the default heuristic distance strategy for population seeding.

    Args:
        adjacency_matrix: The adjacency matrix used for distance lookups.
        weight_type: The weight strategy (e.g., "eta", "length").
        cost_type: Optional cost strategy name.

    Returns:
        An IHeuristicDistanceStrategy implementation.
    """
    if cost_type not in (None, "", "none"):
        return AdjacencyCostPopulationDistanceStrategy(adjacency_matrix)
    if weight_type == "length":
        return AdjacencyLengthPopulationDistanceStrategy(adjacency_matrix)
    if weight_type == "eta":
        return AdjacencyEtaPopulationDistanceStrategy(adjacency_matrix)
    return EuclideanPopulationDistanceStrategy()


def _normalize_component_name(name: str) -> str:
    """Normalize one configured component identifier for internal matching."""
    return name.strip().lower()


def _build_selection_strategy(
    config: Mapping[str, Any],
) -> ISelectionStrategy:
    """Build one legacy selection strategy from adaptive configuration."""
    name = _normalize_component_name(str(config["name"]))
    params = dict(config.get("params", {}))

    if name == "roulette":
        return RoulleteSelectionStrategy()
    if name == "rank":
        return RankSelectionStrategy()
    if name == "sus":
        return StochasticUniversalSamplingSelectionStrategy()
    if name == "tournament":
        return TournamentSelectionStrategy(
            tournament_size=int(params.get("tournament_size", 3))
        )
    raise ValueError(f"Unknown selection strategy: {config['name']}")


def _build_crossover_strategy(
    config: Mapping[str, Any],
) -> ICrossoverStrategy:
    """Build one legacy crossover strategy from adaptive configuration."""
    name = _normalize_component_name(str(config["name"]))

    if name == "order":
        return OrderCrossoverStrategy()
    if name == "pmx":
        return PartiallyMappedCrossoverStrategy()
    if name == "cycle":
        return CycleCrossoverStrategy()
    if name == "edge_recombination":
        return EdgeRecombinationCrossoverStrategy()
    raise ValueError(f"Unknown crossover strategy: {config['name']}")


def _build_mutation_strategy(
    config: Mapping[str, Any],
) -> IMutationStrategy:
    """Build one legacy mutation strategy from adaptive configuration."""
    name = _normalize_component_name(str(config["name"]))

    if name == "swap_redistribute":
        return SwapAndRedistributeMutationStrategy()
    if name == "inversion":
        return InversionMutationStrategy()
    if name == "insertion":
        return InsertionMutationStrategy()
    if name == "two_opt":
        return TwoOptMutationStrategy()
    raise ValueError(f"Unknown mutation strategy: {config['name']}")


def _build_population_generator(
    config: Mapping[str, Any],
    adjacency_matrix,
    weight_type: str,
    cost_type: str | None,
) -> IPopulationGenerator:
    """Build one legacy population generator from adaptive configuration."""
    name = _normalize_component_name(str(config["name"]))
    params = dict(config.get("params", {}))
    distance_strategy = _build_population_distance_strategy(
        adjacency_matrix,
        weight_type,
        cost_type,
    )

    if name == "random":
        return RandomPopulationGenerator()
    if name == "heuristic":
        return HeuristicPopulationGenerator(distance_strategy)
    if name == "hybrid":
        return HybridPopulationGenerator(
            random_population_generator=RandomPopulationGenerator(),
            heuristic_population_generator=HeuristicPopulationGenerator(
                distance_strategy
            ),
            heuristic_ratio=float(params.get("heuristic_ratio", 0.4)),
        )
    raise ValueError(f"Unknown population generator: {config['name']}")


def _build_specification(
    config: Mapping[str, Any],
) -> IGeneticSpecification:
    """Build one concrete adaptive transition specification from configuration."""
    name = _normalize_component_name(str(config["name"]))
    params = dict(config.get("params", {}))

    if name == "progress_at_least":
        return ProgressAtLeastSpecification(threshold=float(params["threshold"]))
    if name == "stale_at_least":
        return StaleAtLeastSpecification(threshold=int(params["threshold"]))
    if name == "improvement_below":
        return ImprovementBelowSpecification(threshold=float(params["threshold"]))
    raise ValueError(f"Unknown adaptive specification: {config['name']}")


def _build_transition_rule(config: Mapping[str, Any]) -> TransitionRule:
    """Build one configured transition rule from API configuration."""
    return TransitionRule(
        label=str(config["label"]),
        target_state=str(config["target_state"]),
        specifications=[
            _build_specification(specification)
            for specification in config.get("specifications", [])
        ],
    )


def _build_generation_operators(
    state_config: Mapping[str, Any],
    adjacency_matrix,
    weight_type: str,
    cost_type: str | None,
) -> GenerationOperators[
    RouteGeneticSolution,
    EvaluatedRouteSolution,
    RoutePopulationSeedData,
]:
    """Build one adaptive generation-operator bundle for a configured state."""
    population_generator_config = state_config.get("population_generator")
    resolved_population_generator = (
        _build_population_generator(
            population_generator_config,
            adjacency_matrix,
            weight_type,
            cost_type,
        )
        if population_generator_config is not None
        else HybridPopulationGenerator(
            RandomPopulationGenerator(),
            HeuristicPopulationGenerator(
                _build_population_distance_strategy(
                    adjacency_matrix,
                    weight_type,
                    cost_type,
                )
            ),
        )
    )

    return GenerationOperators(
        selection=LegacySelectionStrategyAdapter(
            _build_selection_strategy(state_config["selection"])
        ),
        crossover=LegacyCrossoverStrategyAdapter(
            _build_crossover_strategy(state_config["crossover"])
        ),
        mutation=LegacyMutationStrategyAdapter(
            _build_mutation_strategy(state_config["mutation"])
        ),
        mutation_probability=float(state_config.get("mutation_probability", 0.5)),
        population_generator=LegacyPopulationGeneratorAdapter(
            resolved_population_generator
        ),
    )


def _build_adaptive_state_controller(
    adaptive_config: Mapping[str, Any],
    adjacency_matrix,
    weight_type: str,
    cost_type: str | None,
) -> IGeneticStateController[
    RouteGeneticSolution,
    EvaluatedRouteSolution,
    RoutePopulationSeedData,
]:
    """Build one configured adaptive state controller for route optimization."""
    states = [
        ConfiguredState[
            RouteGeneticSolution,
            EvaluatedRouteSolution,
            RoutePopulationSeedData,
        ](
            name=str(state["name"]),
            operators=_build_generation_operators(
                state,
                adjacency_matrix,
                weight_type,
                cost_type,
            ),
            transition_rules=[
                _build_transition_rule(rule)
                for rule in state.get("transition_rules", [])
            ],
        )
        for state in adaptive_config.get("states", [])
    ]

    return ConfiguredGeneticStateController[
        RouteGeneticSolution,
        EvaluatedRouteSolution,
        RoutePopulationSeedData,
    ](
        initial_state=str(adaptive_config["initial_state"]),
        states=states,
    )


def _build_default_optimizer(
    calc,
    route_nodes,
    weight_type,
    cost_type,
    plotter,
    population_size,
    adaptive_config: Mapping[str, Any] | None = None,
) -> TSPGeneticAlgorithm:
    """Create a GA optimizer with default concrete collaborators.

    This function constructs the optimizer with a cached adjacency matrix
    builder, heuristic population generator, and default genetic operators.

    Args:
        calc: The route calculator to use for segment computation.
        route_nodes: The list of route nodes to optimize.
        weight_type: Weighting strategy for segment computation.
        cost_type: Optional cost strategy for segment computation.
        plotter: Optional plotter for visualization.
        population_size: The number of individuals in the genetic population.
        adaptive_config: Optional adaptive GA state-graph configuration.

    Returns:
        A configured TSPGeneticAlgorithm instance.
    """
    adjacency_matrix = get_adjacency_matrix_builder().build(
        route_calculator=calc,
        route_nodes=route_nodes,
        weight_type=weight_type,
        cost_type=cost_type,
    )
    heuristic_generator = HeuristicPopulationGenerator(
        _build_population_distance_strategy(adjacency_matrix, weight_type, cost_type)
    )
    return TSPGeneticAlgorithm(
        adjacency_matrix=adjacency_matrix,
        plotter=plotter,
        population_size=population_size,
        selection_strategy=RoulleteSelectionStrategy(),
        crossover_strategy=OrderCrossoverStrategy(),
        mutation_strategy=SwapAndRedistributeMutationStrategy(),
        population_generator=HybridPopulationGenerator(
            RandomPopulationGenerator(),
            heuristic_generator,
        ),
        state_controller=(
            _build_adaptive_state_controller(
                adaptive_config,
                adjacency_matrix,
                weight_type,
                cost_type,
            )
            if adaptive_config is not None
            else None
        ),
    )


def get_route_optimization_service() -> RouteOptimizationService:
    """Return the RouteOptimizationService configured with default dependencies."""
    api_adaptive_config = get_adaptive_ga_config()

    def optimizer_factory(
        calc,
        route_nodes,
        weight_type,
        cost_type,
        plotter,
        population_size,
        adaptive_config=None,
    ) -> TSPGeneticAlgorithm:
        """Build one optimizer using the API's required adaptive configuration.

        Args:
            calc: Route calculator used to evaluate route segments.
            route_nodes: Nodes that define the optimization problem.
            weight_type: Requested route-weight strategy.
            cost_type: Optional cost strategy.
            plotter: Optional plotter used for visualization.
            population_size: Population size for the optimization run.
            adaptive_config: Optional config supplied by callers that still use
                the service's adaptive-config parameter path.

        Returns:
            A configured `TSPGeneticAlgorithm` instance.
        """
        resolved_adaptive_config = (
            adaptive_config if adaptive_config is not None else api_adaptive_config
        )

        return _build_default_optimizer(
            calc=calc,
            route_nodes=route_nodes,
            weight_type=weight_type,
            cost_type=cost_type,
            plotter=plotter,
            population_size=population_size,
            adaptive_config=resolved_adaptive_config,
        )

    return RouteOptimizationService(
        graph_generator=get_graph_generator(),
        route_calculator_factory=RouteCalculator,
        optimizer_factory=optimizer_factory,
        plotter_factory=None,
    )
