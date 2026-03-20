"""Operator bundle model resolved for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from src.domain.interfaces.genetic_algorithm.engine.seed_data import (
    IGeneticSeedData,
)
from src.domain.interfaces.genetic_algorithm.ga_evaluated_solution import (
    IEvaluatedGeneticSolution,
)
from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution
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

OperatorMetadataValue = str | int | float | bool | None

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData", bound=IGeneticSeedData)


@dataclass(slots=True)
class GenerationOperators(Generic[TSolution, TEvaluated, TSeedData]):
    """Group the active operators and tunables for one generation."""

    selection: IGeneticSelectionStrategy[TSolution, TEvaluated]
    crossover: IGeneticCrossoverStrategy[TSolution]
    mutation: IGeneticMutationStrategy[TSolution]
    mutation_probability: float
    population_generator: IGeneticPopulationGenerator[TSeedData, TSolution] | None = (
        None
    )
    metadata: dict[str, OperatorMetadataValue] = field(default_factory=dict)
