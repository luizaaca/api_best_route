"""Transition rule configuration model for stateful console lab runs."""

from pydantic import BaseModel, Field

from .lab_specification_config import LabSpecificationConfig


class LabTransitionRuleConfig(BaseModel):
    """Represent one transition rule declared in the lab state graph.

    Attributes:
        label: Human-readable rule label used in generation records.
        target_state: Name of the state activated when the rule matches.
        specifications: Specifications evaluated with AND semantics.
    """

    label: str
    target_state: str
    specifications: list[LabSpecificationConfig] = Field(default_factory=list)