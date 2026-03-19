"""Domain protocols for GA operators and route-legacy GA adapters."""

from .crossover_strategy_legacy import ICrossoverStrategy
from .ga_crossover_strategy import IGeneticCrossoverStrategy
from .ga_mutation_strategy import IGeneticMutationStrategy
from .ga_population_generator import IGeneticPopulationGenerator
from .ga_selection_strategy import IGeneticSelectionStrategy
from .mutation_strategy_legacy import IMutationStrategy
from .population_generator_legacy import IPopulationGenerator
from .selection_strategy_legacy import ISelectionStrategy

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
