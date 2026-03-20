"""Domain protocols for the generic genetic algorithm engine."""

from importlib import import_module

__all__ = [
    "IGeneticSpecification",
    "IGeneticStateController",
]

_EXPORT_MAP = {
    "IGeneticSpecification": ".specification",
    "IGeneticStateController": ".state_controller",
}


def __getattr__(name: str):
    """Lazily resolve generic GA engine protocol exports."""
    module_path = _EXPORT_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
