"""Expand file-driven lab session configs into resolved benchmark runs."""

import copy
import itertools
import random
from typing import Any

from console.lab.models.lab_float_range_policy import LabFloatRangePolicy
from console.lab.models.lab_int_range_policy import LabIntRangePolicy
from console.lab.models.lab_run_config import LabRunConfig
from console.lab.models.lab_search_summary import LabSearchSummary
from console.lab.models.lab_session_config import LabSessionConfig


class LabRunConfigExpander:
    """Expand explicit, grid, and random config modes into resolved runs."""

    _REPLACE_WHOLE_KEYS = {"state_config"}
    _LEGACY_OPERATOR_QUARTET_KEYS = {
        "population_generator",
        "selection",
        "crossover",
        "mutation",
    }

    @classmethod
    def expand(
        cls,
        session_config: LabSessionConfig,
    ) -> tuple[list[LabRunConfig], LabSearchSummary]:
        """Expand a validated session config into resolved benchmark runs.

        Args:
            session_config: The validated session configuration model.

        Returns:
            A tuple with the resolved run list and a search summary.
        """
        if session_config.mode == "explicit":
            runs = cls._expand_explicit(session_config)
        elif session_config.mode == "grid":
            runs = cls._expand_grid(session_config)
        else:
            runs = cls._expand_random(session_config)
        search_summary = cls._build_search_summary(session_config, runs)
        return runs, search_summary

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge two dictionaries into a new mapping.

        Args:
            base: Base mapping that provides default values.
            override: Override mapping whose values take precedence.

        Returns:
            A merged dictionary.
        """
        merged = copy.deepcopy(base)
        for key, value in override.items():
            if (
                key not in LabRunConfigExpander._REPLACE_WHOLE_KEYS
                and key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = LabRunConfigExpander._deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged

    @classmethod
    def _build_base_run_dict(cls, session_config: LabSessionConfig) -> dict[str, Any]:
        """Return the merged base dictionary shared by all resolved runs.

        Args:
            session_config: The validated session configuration model.

        Returns:
            A dictionary containing merged problem and default fields.
        """
        return cls._deep_merge(session_config.problem, session_config.defaults)

    @staticmethod
    def _sample_int_policy(
        rng: random.Random,
        policy: LabIntRangePolicy,
    ) -> int:
        """Sample one integer value from an inclusive integer policy.

        Args:
            rng: Random generator used for reproducible sampling.
            policy: Integer sampling policy.

        Returns:
            One sampled integer value.
        """
        return rng.randint(policy.min, policy.max)

    @staticmethod
    def _sample_float_policy(
        rng: random.Random,
        policy: LabFloatRangePolicy,
    ) -> float:
        """Sample one float value from an inclusive float policy.

        Args:
            rng: Random generator used for reproducible sampling.
            policy: Float sampling policy.

        Returns:
            One sampled float value.
        """
        sampled_value = rng.uniform(policy.min, policy.max)
        if policy.round is not None:
            return round(sampled_value, policy.round)
        return sampled_value

    @staticmethod
    def _set_nested_value(payload: dict[str, Any], dotted_key: str, value: Any) -> None:
        """Assign a value inside a nested dictionary using dot notation.

        Args:
            payload: Mutable target dictionary.
            dotted_key: Dot-separated path to assign.
            value: Value to write at the target path.
        """
        parts = dotted_key.split(".")
        cursor = payload
        for part in parts[:-1]:
            next_value = cursor.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                cursor[part] = next_value
            cursor = next_value
        cursor[parts[-1]] = copy.deepcopy(value)

    @classmethod
    def _build_run_config(
        cls,
        resolved_dict: dict[str, Any],
        mode: str,
        index: int,
        default_label_prefix: str,
    ) -> LabRunConfig:
        """Convert a merged dictionary into a validated resolved run config.

        Args:
            resolved_dict: Raw merged run payload.
            mode: Source mode that produced the run.
            index: Zero-based resolved run index.
            default_label_prefix: Label prefix used when no label is supplied.

        Returns:
            A validated `LabRunConfig` instance.
        """
        payload = copy.deepcopy(resolved_dict)
        legacy_keys = sorted(cls._LEGACY_OPERATOR_QUARTET_KEYS & set(payload))
        if legacy_keys:
            raise ValueError(
                "lab config no longer supports legacy operator quartet keys: "
                f"{legacy_keys}"
            )
        payload.setdefault("label", f"{default_label_prefix}-{index + 1:03d}")
        payload["source_mode"] = mode
        payload["source_index"] = index
        return LabRunConfig.model_validate(payload)

    @classmethod
    def _expand_explicit(cls, session_config: LabSessionConfig) -> list[LabRunConfig]:
        """Resolve explicit experiments into validated run configs.

        Args:
            session_config: The validated session configuration model.

        Returns:
            A list of resolved run configs.
        """
        base_run = cls._build_base_run_dict(session_config)
        return [
            cls._build_run_config(
                cls._deep_merge(base_run, experiment),
                session_config.mode,
                index,
                "explicit",
            )
            for index, experiment in enumerate(session_config.experiments)
        ]

    @classmethod
    def _expand_grid(cls, session_config: LabSessionConfig) -> list[LabRunConfig]:
        """Resolve a Cartesian product of grid search values into run configs.

        Args:
            session_config: The validated session configuration model.

        Returns:
            A list of resolved run configs.
        """
        base_run = cls._build_base_run_dict(session_config)
        grid_items = list(session_config.search_space.items())
        combinations = itertools.product(*(values for _, values in grid_items))

        resolved_runs: list[LabRunConfig] = []
        for index, combination in enumerate(combinations):
            payload = copy.deepcopy(base_run)
            for (path, _), value in zip(grid_items, combination):
                cls._set_nested_value(payload, path, value)
            resolved_runs.append(
                cls._build_run_config(payload, session_config.mode, index, "grid")
            )
        return resolved_runs

    @classmethod
    def _expand_random(cls, session_config: LabSessionConfig) -> list[LabRunConfig]:
        """Resolve randomly sampled search-space values into run configs.

        Args:
            session_config: The validated session configuration model.

        Returns:
            A list of resolved run configs.
        """
        if session_config.random_search is None:
            raise ValueError("random mode requires random_search")

        base_run = copy.deepcopy(session_config.problem)
        sample_count = session_config.random_search.n
        seed = session_config.random_search.seed
        rng = random.Random(seed)

        resolved_runs: list[LabRunConfig] = []
        for index in range(sample_count):
            payload = copy.deepcopy(base_run)
            payload["state_config"] = copy.deepcopy(
                rng.choice(
                    session_config.random_search.allowed_state_configs
                ).model_dump(mode="python")
            )
            for field_name, policy in session_config.random_search.ranges.items():
                if isinstance(policy, LabIntRangePolicy):
                    payload[field_name] = cls._sample_int_policy(rng, policy)
                else:
                    payload[field_name] = cls._sample_float_policy(rng, policy)
            if seed is not None:
                payload["seed"] = int(seed) + index
            resolved_runs.append(
                cls._build_run_config(payload, session_config.mode, index, "random")
            )
        return resolved_runs

    @classmethod
    def _build_search_summary(
        cls,
        session_config: LabSessionConfig,
        runs: list[LabRunConfig],
    ) -> LabSearchSummary:
        """Build a report-friendly summary of the resolved search session.

        Args:
            session_config: Original validated session configuration.
            runs: Resolved run list produced from the session config.

        Returns:
            A search summary suitable for the final benchmark report.
        """
        if session_config.mode == "explicit":
            details = {"labels": [run.label for run in runs]}
        elif session_config.mode == "grid":
            details = {
                "dimensions": {
                    key: len(value)
                    for key, value in session_config.search_space.items()
                }
            }
        else:
            details = {
                "n": session_config.random_search.n,
                "seed": session_config.random_search.seed,
                "allowed_state_config_count": len(
                    session_config.random_search.allowed_state_configs
                ),
                "ranges": sorted(session_config.random_search.ranges.keys()),
            }
        return LabSearchSummary(
            mode=session_config.mode,
            resolved_run_count=len(runs),
            details=details,
        )
