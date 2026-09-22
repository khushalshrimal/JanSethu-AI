import os
import math
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LocationProvider(ABC):
    """Abstract interface for Location and Geocoding operations."""

    @abstractmethod
    def geocode(self, location_query: str) -> Dict[str, Any]:
        """
        Converts a location query string (e.g. 'Baramati', 'Baramati ke paas', 'Near Pune')
        into normalized location details and coordinates.
        Returns dict: {"formatted_name": str, "district": str, "state": str, "latitude": float, "longitude": float, "is_mock": bool}
        """
        pass

    @abstractmethod
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Converts latitude and longitude into normalized district/state location info."""
        pass

    @abstractmethod
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates distance between two coordinate pairs in kilometers using Haversine formula."""
        pass


class MockLocationProvider(LocationProvider):
    """
    Zero-cost development/local Location & Geocoding Provider.
    Supports rural & semi-urban Maharashtra/India regional locations with privacy-conscious normalization.
    """

    KNOWN_LOCATIONS: Dict[str, Dict[str, Any]] = {
        "baramati": {"formatted_name": "Baramati", "district": "Pune", "state": "Maharashtra", "latitude": 18.1506, "longitude": 74.5772},
        "indapur": {"formatted_name": "Indapur", "district": "Pune", "state": "Maharashtra", "latitude": 18.1147, "longitude": 75.0326},
        "malegaon": {"formatted_name": "Malegaon", "district": "Pune", "state": "Maharashtra", "latitude": 18.1345, "longitude": 74.5211},
        "pune": {"formatted_name": "Pune City", "district": "Pune", "state": "Maharashtra", "latitude": 18.5204, "longitude": 73.8567},
        "satara": {"formatted_name": "Satara", "district": "Satara", "state": "Maharashtra", "latitude": 17.6805, "longitude": 74.0183},
        "solapur": {"formatted_name": "Solapur", "district": "Solapur", "state": "Maharashtra", "latitude": 17.6599, "longitude": 75.9064},
        "nashik": {"formatted_name": "Nashik", "district": "Nashik", "state": "Maharashtra", "latitude": 19.9975, "longitude": 73.7898},
        "kolhapur": {"formatted_name": "Kolhapur", "district": "Kolhapur", "state": "Maharashtra", "latitude": 16.7050, "longitude": 74.2433},
        "jaipur": {"formatted_name": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873},
        "mumbai": {"formatted_name": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777},
        "delhi": {"formatted_name": "Delhi", "district": "Central Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    }

    def geocode(self, location_query: str) -> Dict[str, Any]:
        if not location_query or not location_query.strip():
            return {
                "formatted_name": "Baramati",
                "district": "Pune",
                "state": "Maharashtra",
                "latitude": 18.1506,
                "longitude": 74.5772,
                "is_mock": True
            }

        query_clean = location_query.lower().strip()
        for key, info in self.KNOWN_LOCATIONS.items():
            if key in query_clean:
                res = info.copy()
                res["is_mock"] = True
                return res

        # Default fallback if unmapped location string provided
        return {
            "formatted_name": location_query.strip().title(),
            "district": "Pune",
            "state": "Maharashtra",
            "latitude": 18.1506,
            "longitude": 74.5772,
            "is_mock": True
        }

    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        # Find nearest known location in dictionary
        closest = None
        min_dist = float("inf")

        for key, info in self.KNOWN_LOCATIONS.items():
            dist = self.calculate_distance(latitude, longitude, info["latitude"], info["longitude"])
            if dist < min_dist:
                min_dist = dist
                closest = info

        if closest:
            res = closest.copy()
            res["is_mock"] = True
            res["distance_km"] = round(min_dist, 2)
            return res

        return {
            "formatted_name": "Baramati",
            "district": "Pune",
            "state": "Maharashtra",
            "latitude": latitude,
            "longitude": longitude,
            "is_mock": True
        }

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance calculation in kilometers."""
        r = 6371.0  # Earth radius in KM
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 2)


class ConfiguredLocationProvider(LocationProvider):
    """
    Environment-configurable Location Provider wrapper.
    Reads LOCATION_PROVIDER env variable.
    Falls back safely to MockLocationProvider when external credentials are missing or unconfigured.
    """

    def __init__(self, provider_type: Optional[str] = None):
        self.provider_type = (provider_type or os.getenv("LOCATION_PROVIDER", "mock")).lower()
        self._provider = MockLocationProvider()

    def geocode(self, location_query: str) -> Dict[str, Any]:
        try:
            return self._provider.geocode(location_query)
        except Exception:
            return MockLocationProvider().geocode(location_query)

    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        try:
            return self._provider.reverse_geocode(latitude, longitude)
        except Exception:
            return MockLocationProvider().reverse_geocode(latitude, longitude)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return self._provider.calculate_distance(lat1, lon1, lat2, lon2)


def get_location_provider() -> LocationProvider:
    return ConfiguredLocationProvider()
