from typing import Protocol, runtime_checkable


@runtime_checkable
class IGeocodingCache(Protocol):
    """Persist forward and reverse geocoding results across executions."""

    def get_geocode(self, location: str) -> tuple[tuple[float, float], str] | None: ...

    def set_geocode(
        self,
        location: str,
        coords: tuple[float, float],
        address: str,
    ) -> None: ...

    def get_reverse(self, coords: tuple[float, float]) -> str | None: ...

    def set_reverse(
        self,
        coords: tuple[float, float],
        address: str,
    ) -> None: ...


@runtime_checkable
class IGeocodingResolver(Protocol):
    """Resolve addresses and coordinates for route initialization."""

    def geocode(self, location: str) -> tuple[tuple[float, float], str]: ...

    def reverse_geocode(self, coords: tuple[float, float]) -> str: ...
