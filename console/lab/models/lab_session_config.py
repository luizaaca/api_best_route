"""Raw file-driven session configuration model for the console lab mode."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .lab_output_config import LabOutputConfig
from .lab_random_search_config import LabRandomSearchConfig


class LabSessionConfig(BaseModel):
    """Represent the JSON configuration file consumed by the lab runner.

    Attributes:
        mode: Experiment mode (`explicit`, `grid`, or `random`).
        problem: Raw problem definition shared by all runs in the session.
        output: Session-level output and report-rendering configuration.
        defaults: Default run configuration values applied before mode-specific
            overrides are expanded in `explicit` and `grid` modes.
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

    @model_validator(mode="after")
    def validate_mode_sections(self) -> "LabSessionConfig":
        """Validate that the required top-level section exists for the mode.

        Returns:
            The validated session configuration.

        Raises:
            ValueError: If the configuration omits required mode-specific data.
        """
        if self.mode == "explicit" and not self.experiments:
            raise ValueError("explicit mode requires a non-empty experiments list")
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
