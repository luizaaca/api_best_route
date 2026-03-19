"""Domain protocol for caching forward and reverse geocoding results."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IGeocodingCache(Protocol):
    """Cache geocoding results to avoid repeated external calls."""

    def get_geocode(self, location: str) -> tuple[tuple[float, float], str] | None:
        """Retrieve a cached geocoding result for a location string."""
        ...

    def set_geocode(
        self,
        location: str,
        coords: tuple[float, float],
        address: str,
    ) -> None:
        """Store a forward geocoding result."""
        ...

    def get_reverse(self, coords: tuple[float, float]) -> str | None:
        """Lookup a cached reverse geocoding address."""
        ...

    def set_reverse(
        self,
        coords: tuple[float, float],
        address: str,
    ) -> None:
        """Store a reverse geocoding mapping."""
        ...
