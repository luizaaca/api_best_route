"""Shared helpers for adaptive GA configuration path resolution and loading."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


def get_sibling_config_path(anchor_file: str | Path, config_name: str) -> Path:
    """Return the path to a config file stored beside an anchor module.

    Args:
        anchor_file: Module file path used as the anchor directory.
        config_name: Name of the configuration file to resolve.

    Returns:
        The absolute path to the sibling configuration file.
    """
    return Path(anchor_file).resolve().parent / config_name


def load_adaptive_ga_config(config_path: Path) -> dict[str, Any]:
    """Load and minimally validate an adaptive GA JSON configuration file.

    Args:
        config_path: Absolute or relative path to the JSON configuration file.

    Returns:
        The parsed adaptive GA configuration payload.

    Raises:
        FileNotFoundError: If the required config file does not exist.
        ValueError: If the file contents are invalid JSON or do not contain the
            minimum required adaptive GA structure.
    """
    resolved_path = Path(config_path)
    if not resolved_path.is_file():
        raise FileNotFoundError(
            f"Adaptive GA configuration file not found: {resolved_path}"
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
