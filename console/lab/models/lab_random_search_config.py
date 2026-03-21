"""Policy-only random-search configuration for the console lab mode."""

from typing import TypeAlias

from pydantic import BaseModel, Field, model_validator

from .lab_float_range_policy import LabFloatRangePolicy
from .lab_int_range_policy import LabIntRangePolicy
from .lab_state_graph_config import LabStateGraphConfig

LabRangePolicy: TypeAlias = LabIntRangePolicy | LabFloatRangePolicy

_REQUIRED_RANGE_KEYS = {
    "population_size",
    "max_generation",
    "max_processing_time",
    "vehicle_count",
}
_RANGE_TYPE_BY_FIELD = {
    "population_size": "int",
    "max_generation": "int",
    "max_processing_time": "int",
    "vehicle_count": "int",
}


class LabRandomSearchConfig(BaseModel):
    """Represent policy-only random-search settings for one session.

    Attributes:
        n: Number of randomly generated runs.
        seed: Optional session seed used to derive reproducible samples.
        allowed_state_configs: Allowed adaptive state graphs that random search
            can sample for each generated run.
        ranges: Required scalar policies used to build each resolved run.
    """

    n: int
    seed: int | None = None
    allowed_state_configs: list[LabStateGraphConfig] = Field(default_factory=list)
    ranges: dict[str, LabRangePolicy] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schema(self) -> "LabRandomSearchConfig":
        """Validate the random-search contract.

        Returns:
            The validated random-search configuration.

        Raises:
            ValueError: If the random-search contract is incomplete or inconsistent.
        """
        if self.n < 1:
            raise ValueError("random_search.n must be >= 1")
        if not self.allowed_state_configs:
            raise ValueError(
                "random_search.allowed_state_configs must be a non-empty list"
            )

        range_keys = set(self.ranges)
        missing_keys = sorted(_REQUIRED_RANGE_KEYS - range_keys)
        if missing_keys:
            raise ValueError(
                f"random_search.ranges is missing required keys: {missing_keys}"
            )
        unknown_keys = sorted(range_keys - set(_RANGE_TYPE_BY_FIELD))
        if unknown_keys:
            raise ValueError(
                f"random_search.ranges contains unsupported keys: {unknown_keys}"
            )

        for key, policy in self.ranges.items():
            expected_type = _RANGE_TYPE_BY_FIELD[key]
            if policy.type != expected_type:
                raise ValueError(
                    f"random_search.ranges.{key} must use type '{expected_type}'"
                )
            if (
                key
                in {
                    "population_size",
                    "max_generation",
                    "max_processing_time",
                    "vehicle_count",
                }
                and policy.min < 1
            ):
                raise ValueError(f"random_search.ranges.{key}.min must be >= 1")
        return self
