"""Domain protocol for forward and reverse geocoding resolution."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IGeocodingResolver(Protocol):
    """Resolve location strings to coordinates and back."""

    def geocode(self, location: str) -> tuple[tuple[float, float], str]:
        """Resolve an address or location string to coordinates."""
        ...

    def reverse_geocode(self, coords: tuple[float, float]) -> str:
        """Resolve coordinates to a human-readable address."""
        ...
