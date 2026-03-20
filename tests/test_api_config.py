import os
import sys
from pathlib import Path

import pytest

# ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.config import get_adaptive_ga_config_path, load_adaptive_ga_config


def test_get_adaptive_ga_config_path_points_to_api_root() -> None:
    expected = Path(__file__).resolve().parent.parent / "api" / "config.json"

    assert get_adaptive_ga_config_path() == expected


def test_load_adaptive_ga_config_reads_valid_file(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        """
        {
          "initial_state": "baseline",
          "states": [
            {
              "name": "baseline",
              "selection": {"name": "roulette"},
              "crossover": {"name": "order"},
              "mutation": {"name": "swap_redistribute"}
            }
          ]
        }
        """.strip(),
        encoding="utf-8",
    )

    config = load_adaptive_ga_config(config_file)

    assert config["initial_state"] == "baseline"
    assert len(config["states"]) == 1
    assert config["states"][0]["name"] == "baseline"


def test_load_adaptive_ga_config_raises_for_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "config.json"

    with pytest.raises(FileNotFoundError, match="configuration file not found"):
        load_adaptive_ga_config(missing_file)


def test_load_adaptive_ga_config_raises_for_invalid_json(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid adaptive GA configuration JSON"):
        load_adaptive_ga_config(config_file)


def test_load_adaptive_ga_config_raises_for_missing_states(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"initial_state": "baseline"}', encoding="utf-8")

    with pytest.raises(ValueError, match="must define 'states'"):
        load_adaptive_ga_config(config_file)
