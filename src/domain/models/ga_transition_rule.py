"""Concrete transition rule model for adaptive GA state graphs."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.interfaces.ga_specification import IGeneticSpecification
from .ga_generation_context import GenerationContext


@dataclass(slots=True)
class TransitionRule:
    """Describe when the adaptive controller should activate a target state.

    A transition rule uses AND semantics across its specifications. The state controller can then compose multiple rules with ordered OR semantics.
    """

    label: str
    target_state: str
    specifications: list[IGeneticSpecification] = field(default_factory=list)

    def matches(self, context: GenerationContext) -> bool:
        """Return whether all specifications match the given context.

        Args:
            context: Runtime context for the current generation.

        Returns:
            `True` when every specification matches.
        """
        return all(
            specification.matches(context) for specification in self.specifications
        )
