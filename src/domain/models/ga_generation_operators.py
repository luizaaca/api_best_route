"""Operator bundle model resolved for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from src.domain.interfaces.ga_crossover_strategy import IGeneticCrossoverStrategy
from src.domain.interfaces.ga_evaluated_solution import IEvaluatedGeneticSolution
from src.domain.interfaces.ga_mutation_strategy import IGeneticMutationStrategy
from src.domain.interfaces.ga_population_generator import IGeneticPopulationGenerator
from src.domain.interfaces.ga_selection_strategy import IGeneticSelectionStrategy
from src.domain.interfaces.ga_solution import IGeneticSolution

OperatorMetadataValue = str | int | float | bool | None

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData")


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
