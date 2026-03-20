"""Route-domain raw solution model for the generic GA engine."""

from __future__ import annotations

import copy
from dataclasses import dataclass

from src.domain.interfaces.genetic_algorithm.ga_solution import IGeneticSolution

from .individual import Individual


@dataclass(slots=True)
class RouteGeneticSolution(IGeneticSolution):
    """Wrap one route-domain individual as a raw GA solution.

    Attributes:
        individual: Multi-vehicle route representation used by the existing TSP
            operators.
    """

    individual: Individual

    def clone(self) -> "RouteGeneticSolution":
        """Return a detached copy of the wrapped route solution."""
        return RouteGeneticSolution(copy.deepcopy(self.individual))
