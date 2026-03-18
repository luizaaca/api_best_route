"""Destination configuration model used by the console lab mode."""

from typing import Union

from pydantic import BaseModel


class LabDestinationConfig(BaseModel):
    """Describe one destination item used in a lab run configuration.

    Attributes:
        location: Address string or `[lat, lon]` coordinate pair.
        priority: Priority level associated with the destination.
    """

    location: Union[str, list[float]]
    priority: int
