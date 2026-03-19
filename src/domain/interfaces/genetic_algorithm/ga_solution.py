"""Domain protocol for raw GA-compatible solutions.

This protocol defines the minimum behavioral contract for a raw solution object
that can participate in GA operations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IGeneticSolution(Protocol):
    """Represent one raw solution handled by the generic GA engine.

    A raw solution is the structure manipulated by population generation,
    crossover, mutation, cloning, and elitism. The GA engine treats it as an
    opaque entity, while the problem domain defines its semantics and
    evaluation.
    """

    def clone(self) -> "IGeneticSolution":
        """Return a detached copy of the solution.

        Returns:
            A logically equivalent copy safe for mutation and elitism.
        """
        ...
