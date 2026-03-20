"""Helpers for loading the API adaptive GA configuration from a fixed file."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


def get_adaptive_ga_config_path() -> Path:
    """Return the fixed API-root path for the API adaptive config.

    Returns:
        The absolute path to the required `config.json` file used by the API.
    """
    return Path(__file__).resolve().parent / "config.json"


def load_adaptive_ga_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the API adaptive GA configuration.

    Args:
        config_path: Optional explicit path. When omitted,
            the function reads the API-root `config.json` file.

    Returns:
        The parsed adaptive GA configuration payload.

    Raises:
        FileNotFoundError: If the required config file does not exist.
        ValueError: If the file contents are invalid JSON or do not contain the minimum required adaptive GA structure.
    """
    resolved_path = config_path or get_adaptive_ga_config_path()
    if not resolved_path.is_file():
        raise FileNotFoundError(
            f"API adaptive GA configuration file not found: {resolved_path}"
        )

    try:
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ValueError(
            f"Invalid adaptive GA configuration JSON in '{resolved_path}': {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "Adaptive GA configuration must be a JSON object at the top level"
        )
    if "initial_state" not in payload:
        raise ValueError("Adaptive GA configuration must define 'initial_state'")
    if "states" not in payload:
        raise ValueError("Adaptive GA configuration must define 'states'")
    if not isinstance(payload["states"], list) or not payload["states"]:
        raise ValueError(
            "Adaptive GA configuration must define a non-empty 'states' list"
        )
    return payload
