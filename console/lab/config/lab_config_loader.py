"""Load console lab configuration files from disk."""

import json
from pathlib import Path

from console.lab.models.lab_session_config import LabSessionConfig


class LabConfigLoader:
    """Load and validate JSON configuration files for the lab runner."""

    @staticmethod
    def load(config_file: str) -> LabSessionConfig:
        """Load a JSON session configuration file from disk.

        Args:
            config_file: Path to the JSON config file.

        Returns:
            A validated `LabSessionConfig` instance.

        Raises:
            ValueError: If the file extension is unsupported.
        """
        path = Path(config_file)
        if path.suffix.lower() != ".json":
            raise ValueError("Only JSON config files are supported in lab mode")
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return LabSessionConfig.model_validate(payload)
