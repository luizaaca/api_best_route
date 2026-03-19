"""Domain protocols for graph generation, routing, and geocoding resolution."""

from .adjacency_matrix_builder import IAdjacencyMatrixBuilder
from .geocoding_resolver import IGeocodingResolver
from .graph_generator import IGraphGenerator
from .heuristic_distance import IHeuristicDistanceStrategy
from .route_calculator import IRouteCalculator

__all__ = [
    "IAdjacencyMatrixBuilder",
    "IGeocodingResolver",
    "IGraphGenerator",
    "IHeuristicDistanceStrategy",
    "IRouteCalculator",
]
