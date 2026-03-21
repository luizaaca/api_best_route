"""Shared builder helpers for composing genetic algorithm collaborators.

This package centralizes small composition utilities that are reused by the
API, console, and lab entrypoints while preserving the existing public
configuration shapes.
"""

from .adaptive_state_controller_builder import (
    build_route_adaptive_state_controller,
    build_route_generation_operators,
    build_route_transition_rule,
)
from .component_builders import (
    IgnoredParamsReporter,
    build_crossover_strategy,
    build_mutation_strategy,
    build_population_generator,
    build_selection_strategy,
    build_specification,
)
from .distance_strategy_builder import build_population_distance_strategy

__all__ = [
    "IgnoredParamsReporter",
    "build_crossover_strategy",
    "build_mutation_strategy",
    "build_population_generator",
    "build_selection_strategy",
    "build_route_adaptive_state_controller",
    "build_route_generation_operators",
    "build_route_transition_rule",
    "build_population_distance_strategy",
    "build_specification",
]
