"""Policy-only random-search configuration for the console lab mode."""

from typing import TypeAlias

from pydantic import BaseModel, Field, model_validator

from .lab_float_range_policy import LabFloatRangePolicy
from .lab_int_range_policy import LabIntRangePolicy

LabRangePolicy: TypeAlias = LabIntRangePolicy | LabFloatRangePolicy

_ALLOWED_GENERATORS = {"random", "heuristic", "hybrid"}
_ALLOWED_SELECTION = {"roulette", "rank", "sus", "tournament"}
_ALLOWED_CROSSOVER = {"order", "pmx", "cycle", "edge_recombination"}
_ALLOWED_MUTATION = {"swap_redistribute", "inversion", "insertion", "two_opt"}
_REQUIRED_RANGE_KEYS = {
    "population_size",
    "mutation_probability",
    "max_generation",
    "max_processing_time",
    "vehicle_count",
}
_RANGE_TYPE_BY_FIELD = {
    "population_size": "int",
    "mutation_probability": "float",
    "max_generation": "int",
    "max_processing_time": "int",
    "vehicle_count": "int",
}


class LabRandomSearchConfig(BaseModel):
    """Represent policy-only random-search settings for one session.

    Attributes:
        n: Number of randomly generated runs.
        seed: Optional session seed used to derive reproducible samples.
        allowed_generators: Allowed population-generator identifiers.
        allowed_selection: Allowed selection-strategy identifiers.
        allowed_crossover: Allowed crossover-strategy identifiers.
        allowed_mutation: Allowed mutation-strategy identifiers.
        ranges: Required scalar policies used to build each resolved run.
    """

    n: int
    seed: int | None = None
    allowed_generators: list[str] = Field(default_factory=list)
    allowed_selection: list[str] = Field(default_factory=list)
    allowed_crossover: list[str] = Field(default_factory=list)
    allowed_mutation: list[str] = Field(default_factory=list)
    ranges: dict[str, LabRangePolicy] = Field(default_factory=dict)

    @staticmethod
    def _validate_allowed_values(
        values: list[str],
        field_name: str,
        allowed_values: set[str],
    ) -> None:
        """Validate one operator allow-list.

        Args:
            values: Values declared in the configuration.
            field_name: Field name used in validation messages.
            allowed_values: Set of supported stable identifiers.

        Raises:
            ValueError: If the list is empty, duplicated, or contains unknown values.
        """
        if not values:
            raise ValueError(f"random_search.{field_name} must be a non-empty list")
        if len(set(values)) != len(values):
            raise ValueError(
                f"random_search.{field_name} must not contain duplicate values"
            )
        unknown_values = sorted(set(values) - allowed_values)
        if unknown_values:
            raise ValueError(
                f"random_search.{field_name} contains unsupported values: {unknown_values}"
            )

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

        self._validate_allowed_values(
            self.allowed_generators,
            "allowed_generators",
            _ALLOWED_GENERATORS,
        )
        self._validate_allowed_values(
            self.allowed_selection,
            "allowed_selection",
            _ALLOWED_SELECTION,
        )
        self._validate_allowed_values(
            self.allowed_crossover,
            "allowed_crossover",
            _ALLOWED_CROSSOVER,
        )
        self._validate_allowed_values(
            self.allowed_mutation,
            "allowed_mutation",
            _ALLOWED_MUTATION,
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
            if key == "mutation_probability":
                if policy.min < 0 or policy.max > 1:
                    raise ValueError(
                        "random_search.ranges.mutation_probability must stay within [0, 1]"
                    )
        return self
