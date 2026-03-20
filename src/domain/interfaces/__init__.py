"""Convenience exports for domain interface types.

The package keeps a small public surface while avoiding eager imports that can
create circular dependencies during module initialization.
"""

from importlib import import_module

__all__ = [
    "IAdjacencyMatrixBuilder",
    "IAdjacencySegmentCache",
    "ICrossoverStrategy",
    "IEvaluatedGeneticSolution",
    "IGeocodingCache",
    "IGeocodingResolver",
    "IGeneticCrossoverStrategy",
    "IGeneticMutationStrategy",
    "IGeneticPopulationGenerator",
    "IGeneticProblem",
    "IGeneticSpecification",
    "IGeneticStateController",
    "IGeneticSelectionStrategy",
    "IGeneticSolution",
    "IGraphGenerator",
    "IHeuristicDistanceStrategy",
    "IMutationStrategy",
    "IPlotter",
    "IPopulationGenerator",
    "IRouteCalculator",
    "IRouteOptimizer",
    "ISelectionStrategy",
]

_EXPORT_MAP = {
    "IAdjacencyMatrixBuilder": ".route_optimization.adjacency_matrix_builder",
    "IAdjacencySegmentCache": ".caching.adjacency_segment_cache",
    "ICrossoverStrategy": ".genetic_algorithm.operators.crossover_strategy_legacy",
    "IEvaluatedGeneticSolution": ".genetic_algorithm.ga_evaluated_solution",
    "IGeocodingCache": ".caching.geocoding_cache",
    "IGeocodingResolver": ".geo_graph.geocoding_resolver",
    "IGeneticCrossoverStrategy": ".genetic_algorithm.operators.ga_crossover_strategy",
    "IGeneticMutationStrategy": ".genetic_algorithm.operators.ga_mutation_strategy",
    "IGeneticPopulationGenerator": ".genetic_algorithm.operators.ga_population_generator",
    "IGeneticProblem": ".genetic_algorithm.ga_problem",
    "IGeneticSpecification": ".genetic_algorithm.engine.specification",
    "IGeneticStateController": ".genetic_algorithm.engine.state_controller",
    "IGeneticSelectionStrategy": ".genetic_algorithm.operators.ga_selection_strategy",
    "IGeneticSolution": ".genetic_algorithm.ga_solution",
    "IGraphGenerator": ".geo_graph.graph_generator",
    "IHeuristicDistanceStrategy": ".geo_graph.heuristic_distance",
    "IMutationStrategy": ".genetic_algorithm.operators.mutation_strategy_legacy",
    "IPlotter": ".plotting.plotter",
    "IPopulationGenerator": ".genetic_algorithm.operators.population_generator_legacy",
    "IRouteCalculator": ".geo_graph.route_calculator",
    "IRouteOptimizer": ".route_optimization.route_optimizer",
    "ISelectionStrategy": ".genetic_algorithm.operators.selection_strategy_legacy",
}


def __getattr__(name: str):
    """Lazily resolve interface exports on first access."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
