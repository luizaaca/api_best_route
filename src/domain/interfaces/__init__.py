"""Convenience exports for all domain interface types.

This package exposes the protocol definitions used throughout the application
so that implementations can import them from a single location.
"""

from .caching import IAdjacencySegmentCache, IGeocodingCache
from .genetic_algorithm import (
    IEvaluatedGeneticSolution,
    IGeneticProblem,
    IGeneticSolution,
    IGeneticSpecification,
    IGeneticStateController,
)
from .genetic_algorithm.operators import (
    ICrossoverStrategy,
    IGeneticCrossoverStrategy,
    IGeneticMutationStrategy,
    IGeneticPopulationGenerator,
    IGeneticSelectionStrategy,
    IMutationStrategy,
    IPopulationGenerator,
    ISelectionStrategy,
)
from .geo_graph import (
    IGeocodingResolver,
    IAdjacencyMatrixBuilder,
    IGraphGenerator,
    IHeuristicDistanceStrategy,
    IRouteCalculator,
)
from .plotting import IPlotter
from .route_optimization import IRouteOptimizer

__all__ = [
    "IAdjacencyMatrixBuilder",
    "IAdjacencySegmentCache",
    "ICrossoverStrategy",
    "IEvaluatedGeneticSolution",
    "IGeocodingCache",
    "IGeocodingResolver",
    "IGeneticCrossoverStrategy",
    "IGeneticMutationStrategy",
    "IGeneticPopulationGenerator",
    "IGeneticProblem",
    "IGeneticSpecification",
    "IGeneticStateController",
    "IGeneticSelectionStrategy",
    "IGeneticSolution",
    "IGraphGenerator",
    "IHeuristicDistanceStrategy",
    "IMutationStrategy",
    "IPlotter",
    "IPopulationGenerator",
    "IRouteCalculator",
    "IRouteOptimizer",
    "ISelectionStrategy",
]
