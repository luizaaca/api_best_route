"""Concrete adaptive specification configuration for console lab runs."""

from typing import Any

from pydantic import BaseModel, Field


class LabSpecificationConfig(BaseModel):
    """Represent one configured adaptive specification.

    Attributes:
        name: Stable specification identifier understood by the shared adaptive
            builder.
        params: Optional constructor parameters for the selected specification.
    """

    name: str
    params: dict[str, Any] = Field(default_factory=dict)