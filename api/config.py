"""Helpers for loading the API adaptive GA configuration from a fixed file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.infrastructure.config import (
    get_sibling_config_path,
    load_adaptive_ga_config as load_shared_adaptive_ga_config,
)


def get_adaptive_ga_config_path() -> Path:
    """Return the fixed API-root path for the API adaptive config.

    Returns:
        The absolute path to the required `config.json` file used by the API.
    """
    return get_sibling_config_path(__file__, "config.json")


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
    return load_shared_adaptive_ga_config(resolved_path)
