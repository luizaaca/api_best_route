"""Domain protocols for graph generation, routing, and geocoding resolution."""

from importlib import import_module

__all__ = [
    "IGeocodingResolver",
    "IGraphGenerator",
    "IHeuristicDistanceStrategy",
    "IRouteCalculator",
]

_EXPORT_MAP = {
    "IGeocodingResolver": ".geocoding_resolver",
    "IGraphGenerator": ".graph_generator",
    "IHeuristicDistanceStrategy": ".heuristic_distance",
    "IRouteCalculator": ".route_calculator",
}


def __getattr__(name: str):
    """Lazily resolve geo-graph protocol exports."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
