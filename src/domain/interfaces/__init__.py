"""Convenience exports for all domain interface types.

This package exposes the protocol definitions used throughout the application so that implementations can import them from a single location.
"""

from .adjacency_cache import IAdjacencyMatrixBuilder, IAdjacencySegmentCache
from .ga_crossover_strategy import IGeneticCrossoverStrategy
from .ga_evaluated_solution import IEvaluatedGeneticSolution
from .ga_mutation_strategy import IGeneticMutationStrategy
from .ga_population_generator import IGeneticPopulationGenerator
from .ga_problem import IGeneticProblem
from .ga_specification import IGeneticSpecification
from .ga_state_controller import IGeneticStateController
from .ga_selection_strategy import IGeneticSelectionStrategy
from .ga_solution import IGeneticSolution
from .geocoding import IGeocodingCache, IGeocodingResolver
from .genetic_algorithm import (
    ICrossoverStrategy,
    IHeuristicDistanceStrategy,
    IMutationStrategy,
    IPopulationGenerator,
    ISelectionStrategy,
)
from .graph_generator import IGraphGenerator
from .plotter import IPlotter
from .route_calculator import IRouteCalculator
from .route_optimizer import IRouteOptimizer

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
