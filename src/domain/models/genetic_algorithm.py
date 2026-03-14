"""Domain type aliases used by the genetic algorithm components.

This module defines the core type aliases used by selection, crossover,
mutation, and population generation components.
"""

from .graph import RouteNode


VehicleRoute = list[RouteNode]
Individual = list[VehicleRoute]
Population = list[Individual]
