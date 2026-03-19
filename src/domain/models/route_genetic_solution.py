"""Route-domain raw solution model for the generic GA engine."""

from __future__ import annotations

import copy
from dataclasses import dataclass

from src.domain.interfaces.ga_solution import IGeneticSolution

from .genetic_algorithm import Individual


@dataclass(slots=True)
class RouteGeneticSolution(IGeneticSolution):
    """Wrap one route-domain individual as a raw GA solution.

    Attributes:
        individual: Multi-vehicle route representation used by the existing TSP
            operators.
    """

    individual: Individual

    def clone(self) -> "RouteGeneticSolution":
        """Return a detached copy of the wrapped route solution.

        Returns:
            A deep-copied route solution safe for elitism and mutation.
        """
        return RouteGeneticSolution(copy.deepcopy(self.individual))
