"""Convenience exports for domain models.

The root package resolves model symbols lazily so importing one lightweight model does not initialize unrelated GA orchestration modules.
"""

from importlib import import_module

__all__ = [
    "FleetRouteInfo",
    "AdjacencyMatrixMap",
    "EvaluatedRouteSolution",
    "GenerationContext",
    "GenerationOperators",
    "GenerationRecord",
    "GenerationStateResolution",
    "GraphContext",
    "Individual",
    "OptimizationResult",
    "Population",
    "RouteGeneticSolution",
    "RouteMetrics",
    "RouteNode",
    "RoutePopulationSeedData",
    "RouteSegment",
    "RouteSegmentsInfo",
    "TransitionRule",
    "VehicleRoute",
    "VehicleRouteInfo",
]

_EXPORT_MAP = {
    "AdjacencyMatrixMap": ".route_optimization.adjacency_matrix_map",
    "EvaluatedRouteSolution": ".genetic_algorithm.evaluated_route_solution",
    "FleetRouteInfo": ".route_optimization.fleet_route_info",
    "GenerationContext": ".genetic_algorithm.engine.generation_context",
    "GenerationOperators": ".genetic_algorithm.engine.generation_operators",
    "GenerationRecord": ".genetic_algorithm.engine.generation_record",
    "GenerationStateResolution": ".genetic_algorithm.engine.state_resolution",
    "GraphContext": ".geo_graph.graph_context",
    "Individual": ".genetic_algorithm.individual",
    "OptimizationResult": ".route_optimization.optimization_result",
    "Population": ".genetic_algorithm.population",
    "RouteGeneticSolution": ".genetic_algorithm.route_genetic_solution",
    "RouteMetrics": ".route_optimization.route_metrics",
    "RouteNode": ".geo_graph.route_node",
    "RoutePopulationSeedData": ".geo_graph.route_population_seed_data",
    "RouteSegment": ".route_optimization.route_segment",
    "RouteSegmentsInfo": ".route_optimization.route_segments_info",
    "TransitionRule": ".genetic_algorithm.engine.transition_rule",
    "VehicleRoute": ".genetic_algorithm.vehicle_route",
    "VehicleRouteInfo": ".route_optimization.vehicle_route_info",
}


def __getattr__(name: str):
    """Lazily resolve model exports on first access."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
