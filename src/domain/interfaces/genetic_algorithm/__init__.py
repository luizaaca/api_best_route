"""Domain protocols for the generic genetic algorithm engine."""

from importlib import import_module

__all__ = [
    "IAdaptiveRouteGAFamilyFactory",
    "IEvaluatedGeneticSolution",
    "IGeneticProblem",
    "IGeneticSolution",
    "IGeneticSpecification",
    "IGeneticStateController",
]

_EXPORT_MAP = {
    "IAdaptiveRouteGAFamilyFactory": ".factories.adaptive_route_ga_family_factory",
    "IEvaluatedGeneticSolution": ".ga_evaluated_solution",
    "IGeneticProblem": ".ga_problem",
    "IGeneticSolution": ".ga_solution",
    "IGeneticSpecification": ".engine.specification",
    "IGeneticStateController": ".engine.state_controller",
}


def __getattr__(name: str):
    """Lazily resolve generic GA protocol exports."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
