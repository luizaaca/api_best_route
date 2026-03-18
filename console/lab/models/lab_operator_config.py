"""Operator selection configuration model for the console lab mode."""

from typing import Any

from pydantic import BaseModel, Field


class LabOperatorConfig(BaseModel):
    """Represent a named GA operator plus its optional parameters.

    Attributes:
        name: Stable operator identifier understood by the lab factories.
        params: Optional mapping with operator-specific parameters.
    """

    name: str
    params: dict[str, Any] = Field(default_factory=dict)
