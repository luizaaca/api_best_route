"""Adaptive state configuration model for stateful console lab runs."""

from pydantic import BaseModel, Field

from .lab_operator_config import LabOperatorConfig
from .lab_transition_rule_config import LabTransitionRuleConfig


class LabStateConfig(BaseModel):
    """Represent one configured adaptive GA state in the lab schema.

    Attributes:
        name: Stable state identifier.
        selection: Selection strategy active in the state.
        crossover: Crossover strategy active in the state.
        mutation: Mutation strategy active in the state.
        mutation_probability: Mutation probability active in the state.
        population_generator: Optional population generator used for seeding or
            reseeding while the state is active.
        transition_rules: Ordered transition rules evaluated by the adaptive
            controller.
    """

    name: str
    selection: LabOperatorConfig
    crossover: LabOperatorConfig
    mutation: LabOperatorConfig
    mutation_probability: float = 0.5
    population_generator: LabOperatorConfig | None = None
    transition_rules: list[LabTransitionRuleConfig] = Field(default_factory=list)
