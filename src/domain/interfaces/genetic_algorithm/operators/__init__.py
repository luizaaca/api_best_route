"""Domain protocols for GA operators and route-legacy GA adapters."""

from importlib import import_module

__all__ = [
    "ICrossoverStrategy",
    "IGeneticCrossoverStrategy",
    "IGeneticMutationStrategy",
    "IGeneticPopulationGenerator",
    "IGeneticSelectionStrategy",
    "IMutationStrategy",
    "IPopulationGenerator",
    "ISelectionStrategy",
]

_EXPORT_MAP = {
    "ICrossoverStrategy": ".crossover_strategy_legacy",
    "IGeneticCrossoverStrategy": ".ga_crossover_strategy",
    "IGeneticMutationStrategy": ".ga_mutation_strategy",
    "IGeneticPopulationGenerator": ".ga_population_generator",
    "IGeneticSelectionStrategy": ".ga_selection_strategy",
    "IMutationStrategy": ".mutation_strategy_legacy",
    "IPopulationGenerator": ".population_generator_legacy",
    "ISelectionStrategy": ".selection_strategy_legacy",
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
