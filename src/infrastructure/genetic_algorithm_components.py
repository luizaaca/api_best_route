"""Convenience exports for genetic algorithm components used by the optimizer.

This module re-exports commonly used genetic operator implementations and the
core domain type aliases used throughout the genetic algorithm.
"""

from src.domain.models import Individual, Population, VehicleRoute
from src.infrastructure.genetic_algorithm import (
    HybridPopulationGenerator,
    OrderCrossoverStrategy,
    RandomPopulationGenerator,
    RoulleteSelectionStrategy,
    SwapAndRedistributeMutationStrategy,
)

__all__ = [
    "HybridPopulationGenerator",
    "Individual",
    "OrderCrossoverStrategy",
    "Population",
    "RandomPopulationGenerator",
    "RoulleteSelectionStrategy",
    "SwapAndRedistributeMutationStrategy",
    "VehicleRoute",
]
