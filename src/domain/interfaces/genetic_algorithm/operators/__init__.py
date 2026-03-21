"""Domain protocols for generic GA operators."""

from importlib import import_module

__all__ = [
    "IGeneticCrossoverStrategy",
    "IGeneticMutationStrategy",
    "IGeneticPopulationGenerator",
    "IGeneticSelectionStrategy",
]

_EXPORT_MAP = {
    "IGeneticCrossoverStrategy": ".ga_crossover_strategy",
    "IGeneticMutationStrategy": ".ga_mutation_strategy",
    "IGeneticPopulationGenerator": ".ga_population_generator",
    "IGeneticSelectionStrategy": ".ga_selection_strategy",
}


def __getattr__(name: str):
    """Lazily resolve GA operator protocol exports."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
