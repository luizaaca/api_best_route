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
from .distance_strategy_builder import build_population_distance_strategy
from .legacy_component_builders import (
    IgnoredParamsReporter,
    build_legacy_crossover_strategy,
    build_legacy_mutation_strategy,
    build_legacy_population_generator,
    build_legacy_selection_strategy,
    build_specification,
)

__all__ = [
    "IgnoredParamsReporter",
    "build_route_adaptive_state_controller",
    "build_route_generation_operators",
    "build_route_transition_rule",
    "build_population_distance_strategy",
    "build_legacy_crossover_strategy",
    "build_legacy_mutation_strategy",
    "build_legacy_population_generator",
    "build_legacy_selection_strategy",
    "build_specification",
]
