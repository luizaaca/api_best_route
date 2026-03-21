"""Adaptive state-graph configuration model for stateful console lab runs."""

from pydantic import BaseModel, model_validator

from .lab_state_config import LabStateConfig


class LabStateGraphConfig(BaseModel):
    """Represent the complete adaptive GA state graph for one lab run.

    Attributes:
        initial_state: Name of the state active before generation 1.
        states: Available configured states for the run.
    """

    initial_state: str
    states: list[LabStateConfig]

    @model_validator(mode="after")
    def validate_graph(self) -> "LabStateGraphConfig":
        """Validate graph consistency after model parsing.

        Returns:
            The validated state graph.

        Raises:
            ValueError: If the graph is empty, duplicates state names, or the
                declared initial state does not exist.
        """
        if not self.states:
            raise ValueError("state_config.states must be a non-empty list")
        state_names = [state.name for state in self.states]
        if len(set(state_names)) != len(state_names):
            raise ValueError("state_config.states must use unique state names")
        if self.initial_state not in state_names:
            raise ValueError(
                "state_config.initial_state must match one configured state name"
            )
        return self
