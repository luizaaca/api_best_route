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
    """Bundle the resolved state identity and operators for one generation."""

    state_name: str
    operators: GenerationOperators[TSolution, TEvaluated, TSeedData]
    transition_label: str | None = None
