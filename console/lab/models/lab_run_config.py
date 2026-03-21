"""Resolved per-run configuration model for the console lab mode."""

from typing import Union

from pydantic import BaseModel

from .lab_destination_config import LabDestinationConfig
from .lab_state_graph_config import LabStateGraphConfig


class LabRunConfig(BaseModel):
    """Describe one fully resolved benchmark execution.

    Attributes:
        label: Human-friendly label used in reports.
        origin: Address string or `[lat, lon]` coordinate pair.
        destinations: Ordered destination definitions with priorities.
        vehicle_count: Number of vehicles available to the optimizer.
        weight_type: Weight metric used by route calculation.
        cost_type: Optional cost metric used by route calculation.
        population_size: Population size used by the genetic algorithm.
        max_generation: Maximum number of generations to execute.
        max_processing_time: Maximum processing time in milliseconds.
        state_config: Adaptive GA state graph used by the run.
        source_mode: Search mode that produced this run.
        source_index: Position of the run within the resolved batch.
        seed: Optional seed associated with the resolved run.
    """

    label: str
    origin: Union[str, list[float]]
    destinations: list[LabDestinationConfig]
    vehicle_count: int = 1
    weight_type: str = "eta"
    cost_type: str | None = "priority"
    population_size: int = 10
    max_generation: int = 50
    max_processing_time: int = 10000
    state_config: LabStateGraphConfig
    source_mode: str = "explicit"
    source_index: int = 0
    seed: int | None = None
