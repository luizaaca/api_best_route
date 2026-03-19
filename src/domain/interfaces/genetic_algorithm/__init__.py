"""Domain protocols for the generic genetic algorithm engine."""

from .ga_evaluated_solution import IEvaluatedGeneticSolution
from .ga_problem import IGeneticProblem
from .ga_solution import IGeneticSolution
from .ga_specification import IGeneticSpecification
from .ga_state_controller import IGeneticStateController

__all__ = [
    "IEvaluatedGeneticSolution",
    "IGeneticProblem",
    "IGeneticSolution",
    "IGeneticSpecification",
    "IGeneticStateController",
]
