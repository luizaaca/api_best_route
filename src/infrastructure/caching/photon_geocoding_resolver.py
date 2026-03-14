from typing import Protocol, cast

from geopy.geocoders import Photon

from src.domain.interfaces import IGeocodingResolver


class _PhotonLocationLike(Protocol):
    """Describe the minimal location attributes used from Photon results."""

    latitude: float
    longitude: float
    address: str


class PhotonGeocodingResolver(IGeocodingResolver):
    """Resolve locations using the Photon geocoding service."""

    def __init__(self, user_agent: str = "geo_app"):
        """Create the Photon client used for external geocoding calls."""
        self._geolocator = Photon(user_agent=user_agent)

    def geocode(self, location: str) -> tuple[tuple[float, float], str]:
        """Resolve a location name into coordinates and formatted address."""
        geoloc = self._geolocator.geocode(location)
        if geoloc is None:
            raise ValueError(f"Unable to geocode location: {location}")
        typed_geoloc = cast(_PhotonLocationLike, geoloc)
        return (
            (float(typed_geoloc.latitude), float(typed_geoloc.longitude)),
            str(typed_geoloc.address),
        )

    def reverse_geocode(self, coords: tuple[float, float]) -> str:
        """Resolve coordinates into a formatted address string."""
        geoloc = self._geolocator.reverse(coords)
        if geoloc is None:
            raise ValueError(f"Unable to reverse geocode coordinates: {coords}")
        typed_geoloc = cast(_PhotonLocationLike, geoloc)
        return str(typed_geoloc.address)
