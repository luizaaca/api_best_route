"""Resolved adaptive state information for one GA generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from src.domain.interfaces.genetic_algorithm.engine.seed_data import (
    IGeneticSeedData,
)
from src.domain.interfaces.genetic_algorithm.ga_evaluated_solution import (
    IEvaluatedGeneticSolution,
)
from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution
from .generation_operators import GenerationOperators

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData", bound=IGeneticSeedData)


@dataclass(slots=True)
class GenerationStateResolution(Generic[TSolution, TEvaluated, TSeedData]):
    """Bundle explicit transition resolution data for one generation.

    Attributes:
        source_state_name: State evaluated when resolving the current generation.
        target_state_name: State activated after resolution for the next operator set.
        operators: Operator bundle to apply after resolution.
        transition_label: Transition label selected for the generation, when one exists.
    """

    source_state_name: str
    target_state_name: str
    operators: GenerationOperators[TSolution, TEvaluated, TSeedData]
    transition_label: str | None = None
