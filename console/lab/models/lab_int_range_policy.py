"""Integer range policy used by random lab-search configuration."""

from typing import Literal

from pydantic import BaseModel, model_validator


class LabIntRangePolicy(BaseModel):
    """Represent an inclusive integer sampling range.

    Attributes:
        type: Discriminator used during config validation.
        min: Inclusive lower bound.
        max: Inclusive upper bound.
    """

    type: Literal["int"]
    min: int
    max: int

    @model_validator(mode="after")
    def validate_bounds(self) -> "LabIntRangePolicy":
        """Validate the integer bounds.

        Returns:
            The validated integer range policy.

        Raises:
            ValueError: If the lower bound exceeds the upper bound.
        """
        if self.min > self.max:
            raise ValueError("int range policy requires min <= max")
        return self
