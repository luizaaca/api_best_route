"""Abstract base support for copy-based mutation strategies.

This module provides reusable infrastructure logic for mutation operators that
follow the common pattern of cloning an individual, applying a probabilistic
in-place mutation, and returning the mutated copy.
"""

from abc import ABC, abstractmethod
import copy
import random

from src.domain.interfaces.genetic_algorithm.operators.ga_mutation_strategy import (
    IGeneticMutationStrategy,
)
from src.domain.models.genetic_algorithm.individual import Individual
from src.domain.models.genetic_algorithm.route_genetic_solution import (
    RouteGeneticSolution,
)


class BaseCopyingMutationStrategy(ABC, IGeneticMutationStrategy[RouteGeneticSolution]):
    """Provide a template method for copy-based mutation operators.

    Concrete subclasses implement only the in-place mutation logic while this
    base class handles defensive copying and probabilistic triggering.
    """

    @property
    def name(self) -> str:
        """Return the stable strategy identifier used by the GA runtime."""
        return self.__class__.__name__

    @abstractmethod
    def _mutate_in_place(self, solution: Individual) -> None:
        """Apply the concrete mutation directly to the provided solution.

        Args:
            solution: Mutable copy of the individual selected for mutation.

        Returns:
            None. The solution is mutated in place when a valid move exists.
        """

    def mutate(
        self,
        solution: RouteGeneticSolution,
        mutation_probability: float,
    ) -> RouteGeneticSolution:
        """Return a mutated copy of the provided solution.

        Args:
            solution: Individual selected for mutation.
            mutation_probability: Probability that the mutation is applied.

        Returns:
            A deep-copied individual that may contain a mutation when the
            random trigger fires.
        """
        mutated_solution = copy.deepcopy(solution.individual)
        if random.random() < mutation_probability:
            self._mutate_in_place(mutated_solution)
        return RouteGeneticSolution(mutated_solution)
