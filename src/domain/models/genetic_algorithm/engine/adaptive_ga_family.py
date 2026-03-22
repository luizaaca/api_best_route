"""Adaptive GA family model grouping the collaborators resolved from config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from src.domain.interfaces.genetic_algorithm.engine.seed_data import (
    IGeneticSeedData,
)
from src.domain.interfaces.genetic_algorithm.engine.state_controller import (
    IGeneticStateController,
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
class AdaptiveGAFamily(Generic[TSolution, TEvaluated, TSeedData]):
    """Represent one configured adaptive family of GA collaborators.

    Attributes:
        initial_state_name: Name of the configured initial adaptive state.
        initial_operators: Operator bundle active in the initial state.
        state_controller: Adaptive controller that resolves operators over time.
    """

    initial_state_name: str
    initial_operators: GenerationOperators[TSolution, TEvaluated, TSeedData]
    state_controller: IGeneticStateController[TSolution, TEvaluated, TSeedData]
