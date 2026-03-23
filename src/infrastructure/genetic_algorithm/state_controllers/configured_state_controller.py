"""Configured adaptive GA state controller."""

from __future__ import annotations

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
from src.domain.models.genetic_algorithm.engine.configured_state import ConfiguredState
from src.domain.models.genetic_algorithm.engine.generation_context import (
    GenerationContext,
)
from src.domain.models.genetic_algorithm.engine.state_resolution import (
    GenerationStateResolution,
)

TSolution = TypeVar("TSolution", bound=IGeneticSolution)
TEvaluated = TypeVar("TEvaluated", bound=IEvaluatedGeneticSolution)
TSeedData = TypeVar("TSeedData", bound=IGeneticSeedData)


class ConfiguredGeneticStateController(
    IGeneticStateController[TSolution, TEvaluated, TSeedData],
    Generic[TSolution, TEvaluated, TSeedData],
):
    """Resolve states and transitions from configured runtime state graphs.

    The controller keeps one active state and evaluates its transition rules in
    order. The first matching rule wins and activates its target state.
    """

    def __init__(
        self,
        initial_state: str,
        states: list[ConfiguredState[TSolution, TEvaluated, TSeedData]],
    ) -> None:
        """Initialize the configured controller.

        Args:
            initial_state: Name of the state active before generation 1.
            states: Available states in the adaptive graph.

        Raises:
            ValueError: If the initial state does not exist or state names are
                duplicated.
        """
        if not states:
            raise ValueError(
                "ConfiguredGeneticStateController requires at least one state"
            )
        state_map = {state.name: state for state in states}
        if len(state_map) != len(states):
            raise ValueError(
                "ConfiguredGeneticStateController requires unique state names"
            )
        if initial_state not in state_map:
            raise ValueError(f"Unknown initial state: {initial_state}")
        self._states = state_map
        self._current_state_name = initial_state

    @property
    def current_state_name(self) -> str:
        """Return the currently active state name."""
        return self._current_state_name

    def get_initial_resolution(
        self,
    ) -> GenerationStateResolution[TSolution, TEvaluated, TSeedData]:
        """Return the initial state resolution used before the first generation."""
        state = self._states[self._current_state_name]
        return GenerationStateResolution(
            source_state_name=state.name,
            target_state_name=state.name,
            operators=state.operators,
        )

    def resolve(
        self,
        context: GenerationContext,
    ) -> GenerationStateResolution[TSolution, TEvaluated, TSeedData]:
        """Resolve the active state and any transition for one generation.

        Args:
            context: Runtime context for the current generation.

        Returns:
            The current state resolution, including any transition label.

        Raises:
            ValueError: If a transition points to an unknown target state.
        """
        current_state = self._states[self._current_state_name]
        matching_rule = current_state.resolve_transition(context)
        if matching_rule is None:
            return GenerationStateResolution(
                source_state_name=current_state.name,
                target_state_name=current_state.name,
                operators=current_state.operators,
            )

        if matching_rule.target_state not in self._states:
            raise ValueError(
                f"Unknown target state '{matching_rule.target_state}' in transition '{matching_rule.label}'"
            )

        next_state = self._states[matching_rule.target_state]
        self._current_state_name = next_state.name
        return GenerationStateResolution(
            source_state_name=current_state.name,
            target_state_name=next_state.name,
            operators=next_state.operators,
            transition_label=matching_rule.label,
        )
