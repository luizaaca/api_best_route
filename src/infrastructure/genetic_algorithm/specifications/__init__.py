"""Concrete adaptive GA specifications."""

from .improvement_below import ImprovementBelowSpecification
from .progress_at_least import ProgressAtLeastSpecification
from .stale_at_least import StaleAtLeastSpecification

__all__ = [
    "ImprovementBelowSpecification",
    "ProgressAtLeastSpecification",
    "StaleAtLeastSpecification",
]
