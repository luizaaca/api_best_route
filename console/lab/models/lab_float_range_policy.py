"""Float range policy used by random lab-search configuration."""

from typing import Literal

from pydantic import BaseModel, model_validator


class LabFloatRangePolicy(BaseModel):
    """Represent an inclusive float sampling range.

    Attributes:
        type: Discriminator used during config validation.
        min: Inclusive lower bound.
        max: Inclusive upper bound.
        round: Optional decimal precision applied after sampling.
    """

    type: Literal["float"]
    min: float
    max: float
    round: int | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> "LabFloatRangePolicy":
        """Validate the float bounds and optional precision.

        Returns:
            The validated float range policy.

        Raises:
            ValueError: If bounds or rounding precision are invalid.
        """
        if self.min > self.max:
            raise ValueError("float range policy requires min <= max")
        if self.round is not None and self.round < 0:
            raise ValueError("float range policy requires round >= 0")
        return self
