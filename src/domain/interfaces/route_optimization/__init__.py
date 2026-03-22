"""Domain protocols for route-optimization orchestration."""

from importlib import import_module

__all__ = ["IAdjacencyMatrixBuilder"]

_EXPORT_MAP = {
    "IAdjacencyMatrixBuilder": ".adjacency_matrix_builder",
}


def __getattr__(name: str):
    """Lazily resolve route-optimization protocol exports."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
