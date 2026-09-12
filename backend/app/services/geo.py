"""Geospatial helpers. Distance is computed with the Haversine formula.

The backend is the FINAL authority on location validation; clients may
show an approximate distance for UX only.
"""

import math
from dataclasses import dataclass

EARTH_RADIUS_M = 6_371_000.0


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/long points, in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def coordinates_valid(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


@dataclass
class LocationCheck:
    distance_meters: float
    allowed_radius_meters: int
    accuracy: float
    max_accuracy_meters: float
    within_radius: bool
    accuracy_ok: bool

    @property
    def valid(self) -> bool:
        return self.within_radius and self.accuracy_ok


def check_location(
    lat: float,
    lon: float,
    accuracy: float,
    target_lat: float,
    target_lon: float,
    allowed_radius_meters: int,
    max_accuracy_meters: float,
) -> LocationCheck:
    distance = haversine_meters(lat, lon, target_lat, target_lon)
    return LocationCheck(
        distance_meters=round(distance, 2),
        allowed_radius_meters=allowed_radius_meters,
        accuracy=accuracy,
        max_accuracy_meters=max_accuracy_meters,
        within_radius=distance <= allowed_radius_meters,
        accuracy_ok=accuracy <= max_accuracy_meters,
    )
