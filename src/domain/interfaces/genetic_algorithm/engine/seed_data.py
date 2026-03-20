"""Domain protocol for GA seed-data payloads."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IGeneticSeedData(Protocol):
    """Mark one payload as seed data for a GA problem family.

    Concrete problem families can define richer seed payloads that extend this protocol, allowing the generic GA runtime to depend on this explicit seed-data abstraction.
    """

    ...
