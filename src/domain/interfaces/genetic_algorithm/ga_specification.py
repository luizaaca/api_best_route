"""Domain protocol for concrete adaptive GA specifications."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models.ga_generation_context import GenerationContext


@runtime_checkable
class IGeneticSpecification(Protocol):
    """Evaluate one runtime condition against a generation context.

    Concrete specification classes implement the semantics for adaptive GA
    transitions, while configuration decides which specifications are composed
    into each transition rule.
    """

    @property
    def name(self) -> str:
        """Return the specification identifier."""
        ...

    def matches(self, context: GenerationContext) -> bool:
        """Return whether the runtime condition is satisfied.

        Args:
            context: Runtime context for the current generation.

        Returns:
            `True` when the condition matches the current context.
        """
        ...
