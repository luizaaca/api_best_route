"""Raw file-driven session configuration model for the console lab mode."""

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field, model_validator

from .lab_output_config import LabOutputConfig
from .lab_random_search_config import LabRandomSearchConfig


class LabSessionConfig(BaseModel):
    """Represent the JSON configuration file consumed by the lab runner.

    Attributes:
        mode: Experiment mode (`explicit`, `grid`, or `random`).
        problem: Raw problem definition shared by all runs in the session.
        output: Session-level output and report-rendering configuration.
        defaults: Numeric run parameters applied before mode-specific overrides
            are expanded in `explicit` and `grid` modes.
        experiments: Explicit experiment list used when `mode=explicit`.
        search_space: Search-space definition used by `grid`.
        random_search: Policy-only random-search configuration used by `random`.
    """

    mode: Literal["explicit", "grid", "random"]
    problem: dict[str, Any]
    output: LabOutputConfig = Field(default_factory=LabOutputConfig)
    defaults: dict[str, Any] = Field(default_factory=dict)
    experiments: list[dict[str, Any]] = Field(default_factory=list)
    search_space: dict[str, Any] = Field(default_factory=dict)
    random_search: LabRandomSearchConfig | None = None
    _UNSUPPORTED_TOP_LEVEL_OPERATOR_KEYS: ClassVar[set[str]] = {
        "population_generator",
        "selection",
        "crossover",
        "mutation",
    }
    _NUMERIC_DEFAULT_KEYS: ClassVar[set[str]] = {
        "vehicle_count",
        "population_size",
        "max_generation",
        "max_processing_time",
        "seed",
    }

    @model_validator(mode="after")
    def validate_mode_sections(self) -> "LabSessionConfig":
        """Validate that the required top-level section exists for the mode.

        Returns:
            The validated session configuration.

        Raises:
            ValueError: If the configuration omits required mode-specific data.
        """
        if self._UNSUPPORTED_TOP_LEVEL_OPERATOR_KEYS & set(self.problem):
            raise ValueError(
                "lab config requires operators inside state_config; unsupported top-level operator keys in problem"
            )
        if self._UNSUPPORTED_TOP_LEVEL_OPERATOR_KEYS & set(self.defaults):
            raise ValueError(
                "lab config requires operators inside state_config; unsupported top-level operator keys in defaults"
            )
        if "state_config" in self.defaults:
            raise ValueError(
                "lab config defaults accepts only numeric run parameters; declare state_config inside each explicit experiment"
            )
        unsupported_default_keys = sorted(
            set(self.defaults) - self._NUMERIC_DEFAULT_KEYS
        )
        if unsupported_default_keys:
            raise ValueError(
                "lab config defaults accepts only numeric run parameters: "
                f"{unsupported_default_keys}"
            )
        if self.mode == "explicit" and not self.experiments:
            raise ValueError("explicit mode requires a non-empty experiments list")
        if self.mode == "explicit":
            for index, experiment in enumerate(self.experiments):
                if "state_config" not in experiment:
                    raise ValueError(
                        "explicit experiments must define state_config; "
                        f"missing in experiments[{index}]"
                    )
        if self.mode == "grid" and not self.search_space:
            raise ValueError("grid mode requires a non-empty search_space")
        if self.mode == "random":
            if self.search_space:
                raise ValueError("random mode does not accept top-level search_space")
            if self.defaults:
                raise ValueError(
                    "random mode does not accept defaults; define tunable fields in random_search"
                )
            if self.random_search is None:
                raise ValueError("random mode requires random_search")
        return self
