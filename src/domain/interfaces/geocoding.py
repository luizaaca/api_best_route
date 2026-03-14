from typing import Protocol, runtime_checkable


@runtime_checkable
class IGeocodingCache(Protocol):
    """Protocol for caching geocoding results to avoid repeated external calls."""

    def get_geocode(self, location: str) -> tuple[tuple[float, float], str] | None: ...

    """Retrieve a cached geocoding result for a location string.

    Args:
        location: The address or query string used to look up coordinates.

    Returns:
        A tuple ((latitude, longitude), normalized_address) if cached,
        or None if no cached entry exists.
    """

    def set_geocode(
        self,
        location: str,
        coords: tuple[float, float],
        address: str,
    ) -> None: ...

    """Store a forward geocoding result.

    Args:
        location: The original query string.
        coords: The resolved (latitude, longitude).
        address: The normalized address returned by the geocoding service.
    """

    def get_reverse(self, coords: tuple[float, float]) -> str | None: ...

    """Lookup a cached reverse geocoding address.

    Args:
        coords: A (latitude, longitude) tuple.

    Returns:
        The cached address if available, otherwise None.
    """

    def set_reverse(
        self,
        coords: tuple[float, float],
        address: str,
    ) -> None: ...

    """Store a reverse geocoding mapping.

    Args:
        coords: A (latitude, longitude) tuple.
        address: The resolved address string.
    """


@runtime_checkable
class IGeocodingResolver(Protocol):
    """Protocol for resolving location strings to coordinates and back."""

    def geocode(self, location: str) -> tuple[tuple[float, float], str]: ...

    """Resolve an address or location string to coordinates.

    Args:
        location: The address or place name to geocode.

    Returns:
        A tuple containing the (latitude, longitude) and the normalized
        address string.
    """

    def reverse_geocode(self, coords: tuple[float, float]) -> str: ...

    """Resolve coordinates to a human-readable address.

    Args:
        coords: A (latitude, longitude) pair.

    Returns:
        The resolved address string.
    """
