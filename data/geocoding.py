"""
Geoapify Integration Module
Smart City Navigator - AI-Based Smart City Navigation System

Provides geocoding and routing functionality using Geoapify APIs.
"""

import os
import httpx
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass
class Coordinates:
    """Geographic coordinates"""
    lat: float
    lon: float
    
    def __str__(self):
        return f"{self.lat},{self.lon}"
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.lat, self.lon)


@dataclass
class GeocodingResult:
    """Geocoding search result"""
    place_id: str
    name: str
    full_address: str
    coordinates: Coordinates
    country: str
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None


@dataclass
class RouteWaypoint:
    """Route waypoint"""
    coordinates: Coordinates
    name: Optional[str] = None


@dataclass
class RouteSegment:
    """Single segment of a route"""
    waypoints: List[Coordinates]
    distance: float  # meters
    time: float  # seconds
    road_name: Optional[str] = None
    road_type: Optional[str] = None


@dataclass
class Route:
    """Complete route from Geoapify"""
    route_id: str
    waypoints: List[Coordinates]
    distance: float  # meters
    distance_km: float
    time: float  # seconds
    time_minutes: float
    geometry: List[Coordinates]
    segments: List[RouteSegment]
    mode: str
    source: Coordinates
    destination: Coordinates
    
    @property
    def polyline(self) -> List[Tuple[float, float]]:
        """Return route as list of (lat, lon) tuples for map display"""
        return [(c.lat, c.lon) for c in self.geometry]


class GeoapifyClient:
    """
    Client for Geoapify Geocoding and Routing APIs.
    
    Features:
    - Geocoding: Convert place names to coordinates
    - Reverse Geocoding: Convert coordinates to place names
    - Routing: Calculate routes between points
    - Multiple alternatives: Get alternative routes
    """
    
    BASE_URL = "https://api.geoapify.com/v1"
    
    def __init__(self, api_key: str = None):
        """
        Initialize Geoapify client.
        
        Args:
            api_key: Geoapify API key. If None, reads from environment variable.
        """
        self.api_key = api_key or os.getenv("GEOAPIFY_API_KEY")
        if not self.api_key:
            raise ValueError("Geoapify API key is required. Set GEOAPIFY_API_KEY environment variable.")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def geocode(self, query: str, limit: int = 5) -> List[GeocodingResult]:
        """
        Convert place name to coordinates using Geoapify Geocoding API.
        
        Args:
            query: Place name or address to search
            limit: Maximum number of results to return
            
        Returns:
            List of GeocodingResult objects
        """
        url = f"{self.BASE_URL}/geocode/search"
        params = {
            "text": query,
            "apiKey": self.api_key,
            "limit": limit,
            "format": "json"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                result = GeocodingResult(
                    place_id=str(item.get("place_id", "")),
                    name=item.get("name", item.get("formatted", "")),
                    full_address=item.get("formatted", ""),
                    coordinates=Coordinates(
                        lat=item.get("lat", 0),
                        lon=item.get("lon", 0)
                    ),
                    country=item.get("country", ""),
                    city=item.get("city") or item.get("town") or item.get("village"),
                    state=item.get("state"),
                    postcode=item.get("postcode")
                )
                results.append(result)
            
            return results
            
        except httpx.HTTPError as e:
            raise Exception(f"Geocoding request failed: {str(e)}")
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[GeocodingResult]:
        """
        Convert coordinates to place name using Geoapify Geocoding API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            GeocodingResult or None
        """
        url = f"{self.BASE_URL}/geocode/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "apiKey": self.api_key,
            "format": "json"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "results" in data and len(data["results"]) > 0:
                item = data["results"][0]
                return GeocodingResult(
                    place_id=str(item.get("place_id", "")),
                    name=item.get("name", item.get("formatted", "")),
                    full_address=item.get("formatted", ""),
                    coordinates=Coordinates(lat=lat, lon=lon),
                    country=item.get("country", ""),
                    city=item.get("city") or item.get("town"),
                    state=item.get("state")
                )
            return None
            
        except httpx.HTTPError as e:
            raise Exception(f"Reverse geocoding failed: {str(e)}")
    
    async def calculate_route(
        self,
        source: Coordinates,
        destination: Coordinates,
        mode: str = "drive",
        alternatives: bool = True,
        traffic: bool = False
    ) -> List[Route]:
        """
        Calculate routes between two points using Geoapify Routing API.
        
        Args:
            source: Source coordinates
            destination: Destination coordinates
            mode: Travel mode (drive, walk, bicycle, transit)
            alternatives: Whether to return alternative routes
            traffic: Whether to consider traffic (requires API key with traffic feature)
            
        Returns:
            List of Route objects
        """
        url = f"{self.BASE_URL}/routing"
        params = {
            "waypoints": f"{source}|{destination}",
            "mode": mode,
            "apiKey": self.api_key,
            "details": "road_environment,road_name,speed_info"
        }
        
        if alternatives:
            params["alternatives"] = "true"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            routes = []
            
            # Geoapify returns GeoJSON FeatureCollection
            features = data.get("features", [])
            properties = data.get("properties", {})
            waypoints_data = properties.get("waypoints", [])
            
            if features:
                # Parse routes from features
                for idx, feature in enumerate(features):
                    route_data = feature.get("properties", {})
                    geometry = feature.get("geometry", {})
                    route = self._parse_geojson_route(route_data, geometry, idx, source, destination, mode)
                    routes.append(route)
            elif waypoints_data:
                # Fallback: create direct route from waypoints
                coordinates = [source, destination]
                route = Route(
                    route_id="route_1",
                    waypoints=coordinates,
                    distance=self._haversine_distance(source, destination) * 1000,
                    distance_km=self._haversine_distance(source, destination),
                    time=self._haversine_distance(source, destination) * 120,
                    time_minutes=self._haversine_distance(source, destination) * 2,
                    geometry=coordinates,
                    segments=[],
                    mode=mode,
                    source=source,
                    destination=destination
                )
                routes.append(route)
            
            return routes
            
        except httpx.HTTPError as e:
            raise Exception(f"Routing request failed: {str(e)}")
    
    def _parse_geojson_route(
        self,
        route_properties: dict,
        geometry: dict,
        idx: int,
        source: Coordinates,
        destination: Coordinates,
        mode: str
    ) -> Route:
        """Parse GeoJSON route feature into Route object"""
        distance_m = route_properties.get("distance", 0)
        time_s = route_properties.get("time", 0)
        
        coordinates = []
        geom_type = geometry.get("type", "")
        
        if geom_type == "MultiLineString" and "coordinates" in geometry:
            # MultiLineString: coordinates = [[[lon, lat], ...], ...]
            for line_segment in geometry["coordinates"]:
                for coord_pair in line_segment:
                    if len(coord_pair) >= 2:
                        coordinates.append(Coordinates(
                            lat=coord_pair[1],
                            lon=coord_pair[0]
                        ))
        elif geom_type == "LineString" and "coordinates" in geometry:
            # LineString: coordinates = [[lon, lat], ...]
            for coord_pair in geometry["coordinates"]:
                if len(coord_pair) >= 2:
                    coordinates.append(Coordinates(
                        lat=coord_pair[1],
                        lon=coord_pair[0]
                    ))
        elif geom_type == "Point" and "coordinates" in geometry:
            # Point: coordinates = [lon, lat]
            coord = geometry["coordinates"]
            if len(coord) >= 2:
                coordinates.append(Coordinates(lat=coord[1], lon=coord[0]))
        
        return Route(
            route_id=f"route_{idx + 1}",
            waypoints=[source, destination],
            distance=distance_m,
            distance_km=distance_m / 1000,
            time=time_s,
            time_minutes=time_s / 60,
            geometry=coordinates if coordinates else [source, destination],
            segments=[],
            mode=mode,
            source=source,
            destination=destination
        )

    def _parse_route(
        self,
        route_data: dict,
        idx: int,
        source: Coordinates,
        destination: Coordinates,
        mode: str
    ) -> Route:
        """Parse Geoapify route data into Route object"""
        distance_m = route_data.get("distance", 0)
        time_s = route_data.get("time", 0)
        geometry_data = route_data.get("geometry", {})
        
        coordinates = []
        if "coordinates" in geometry_data:
            for coord_pair in geometry_data["coordinates"]:
                if len(coord_pair) >= 2:
                    coordinates.append(Coordinates(
                        lat=coord_pair[1],
                        lon=coord_pair[0]
                    ))
        
        segments = []
        if "legs" in route_data:
            for leg in route_data["legs"]:
                waypoints = [Coordinates(lat=wp[1], lon=wp[0]) 
                            for wp in leg.get("waypoints", [])]
                seg_distance = leg.get("distance", 0)
                seg_time = leg.get("time", 0)
                
                road_name = None
                road_type = None
                if "steps" in leg and leg["steps"]:
                    for step in leg["steps"]:
                        if not road_name:
                            road_name = step.get("street_name")
                        road_type = step.get("road_environment")
                
                segments.append(RouteSegment(
                    waypoints=waypoints,
                    distance=seg_distance,
                    time=seg_time,
                    road_name=road_name,
                    road_type=road_type
                ))
        
        return Route(
            route_id=f"route_{idx + 1}",
            waypoints=[source, destination],
            distance=distance_m,
            distance_km=distance_m / 1000,
            time=time_s,
            time_minutes=time_s / 60,
            geometry=coordinates if coordinates else [source, destination],
            segments=segments,
            mode=mode,
            source=source,
            destination=destination
        )
    
    def _create_direct_route(
        self,
        waypoints: List,
        source: Coordinates,
        destination: Coordinates,
        idx: int,
        mode: str
    ) -> Route:
        """Create a simple route from waypoints"""
        coordinates = []
        for wp in waypoints:
            if "lat" in wp and "lon" in wp:
                coordinates.append(Coordinates(lat=wp["lat"], lon=wp["lon"]))
        
        if len(coordinates) < 2:
            coordinates = [source, destination]
        
        distance = self._haversine_distance(source, destination)
        
        return Route(
            route_id=f"route_{idx + 1}",
            waypoints=[source, destination],
            distance=distance * 1000,
            distance_km=distance,
            time=distance * 120,
            time_minutes=distance * 2,
            geometry=coordinates,
            segments=[],
            mode=mode,
            source=source,
            destination=destination
        )
    
    @staticmethod
    def _haversine_distance(coord1: Coordinates, coord2: Coordinates) -> float:
        """Calculate distance between two coordinates in km"""
        R = 6371
        
        lat1, lon1 = math.radians(coord1.lat), math.radians(coord1.lon)
        lat2, lon2 = math.radians(coord2.lat), math.radians(coord2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


async def get_coordinates_from_place(place_name: str, api_key: str = None) -> Optional[GeocodingResult]:
    """
    Convenience function to get coordinates from a place name.
    
    Args:
        place_name: Name of the place
        api_key: Geoapify API key
        
    Returns:
        GeocodingResult with coordinates or None
    """
    client = GeoapifyClient(api_key)
    try:
        results = await client.geocode(place_name)
        await client.close()
        return results[0] if results else None
    except Exception as e:
        await client.close()
        raise e


async def get_route_between_places(
    source_name: str,
    dest_name: str,
    api_key: str = None,
    mode: str = "drive"
) -> Tuple[Optional[Route], Optional[GeocodingResult], Optional[GeocodingResult]]:
    """
    Convenience function to get a route between two place names.
    
    Args:
        source_name: Source place name
        dest_name: Destination place name
        api_key: Geoapify API key
        mode: Travel mode
        
    Returns:
        Tuple of (Route, source GeocodingResult, dest GeocodingResult)
    """
    client = GeoapifyClient(api_key)
    try:
        source_result = await client.geocode(source_name)
        dest_result = await client.geocode(dest_name)
        
        if not source_result or not dest_result:
            return None, source_result[0] if source_result else None, dest_result[0] if dest_result else None
        
        routes = await client.calculate_route(
            source_result[0].coordinates,
            dest_result[0].coordinates,
            mode=mode
        )
        
        await client.close()
        
        return routes[0] if routes else None, source_result[0], dest_result[0]
        
    except Exception as e:
        await client.close()
        raise e
