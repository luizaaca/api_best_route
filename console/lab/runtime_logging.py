"""Helpers for verbose runtime messages in console lab flows."""

from collections.abc import Callable

RuntimeLogger = Callable[[str], None]


def build_runtime_logger(verbose: bool) -> RuntimeLogger | None:
    """Return a console logger when verbose mode is enabled.

    Args:
        verbose: Whether runtime messages should be emitted.

    Returns:
        The standard ``print`` callable when verbose mode is enabled;
        otherwise ``None``.
    """
    if verbose:
        return print
    return None


def emit_runtime_message(logger: RuntimeLogger | None, message: str) -> None:
    """Emit one runtime message if a logger is configured.

    Args:
        logger: Optional callable used to write runtime messages.
        message: The message to emit.
    """
    if logger is not None:
        logger(message)


def emit_ignored_params_message(
    logger: RuntimeLogger | None,
    component_type: str,
    component_name: str,
    params: dict[str, object],
) -> None:
    """Emit a verbose-only message describing ignored operator params.

    Args:
        logger: Optional callable used to write runtime messages.
        component_type: Human-readable operator category.
        component_name: Stable operator identifier.
        params: Mapping of params that will not be used.
    """
    if not params:
        return
    emit_runtime_message(
        logger,
        (
            f"Ignoring unsupported params for {component_type} "
            f"'{component_name}': {sorted(params)}"
        ),
    )
