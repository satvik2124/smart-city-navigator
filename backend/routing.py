"""
Smart City Navigator - Routing Module
Handles Geoapify API calls for multi-route optimization with traffic-aware selection.
"""

import random
import httpx
from datetime import datetime
from typing import List, Dict, Any, Tuple
from math import radians, sin, cos, sqrt, atan2


class RoutingClient:
    """Client for Geoapify Routing API with intelligent traffic-aware route selection."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.geoapify.com"):
        """
        Initialize the routing client.
        
        Args:
            api_key: Geoapify API key for authentication
            base_url: Base URL for Geoapify API (default: https://api.geoapify.com)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.routing_url = f"{base_url}/v1/routing"
    
    def _get_traffic_factor(self, hour: int) -> Tuple[float, str]:
        """
        Calculate traffic factor based on time of day.
        
        Args:
            hour: Hour of day (0-23)
            
        Returns:
            Tuple of (traffic_factor, traffic_label)
        """
        # Define base traffic factors for different time periods
        if 7 <= hour < 10:
            # Morning Rush: 07:00–10:00
            base = 2.0
        elif 10 <= hour < 16:
            # Afternoon: 10:00–16:00
            base = 1.5
        elif 16 <= hour < 20:
            # Evening Rush: 16:00–20:00
            base = 2.0
        else:
            # Night: 20:00–07:00
            base = 1.0
        
        # Apply ±10% random variation for simulation
        variation = random.uniform(0.9, 1.1)
        traffic_factor = round(base * variation, 2)
        
        # Determine traffic label based on factor
        if traffic_factor < 1.2:
            traffic_label = "Low"
        elif traffic_factor < 1.7:
            traffic_label = "Medium"
        else:
            traffic_label = "High"
        
        return traffic_factor, traffic_label
    
    def _extract_coordinates(self, geometry: Dict[str, Any]) -> List[List[float]]:
        """
        Extract coordinate pairs from GeoJSON LineString geometry.
        
        Args:
            geometry: GeoJSON geometry object (LineString)
            
        Returns:
            List of [lat, lng] coordinate pairs
        """
        coordinates = geometry.get("coordinates", [])
        # GeoJSON uses [lng, lat] format, convert to [lat, lng]
        return [[coord[1], coord[0]] for coord in coordinates]
    
    def _calculate_distance_from_geometry(self, geometry: Dict[str, Any]) -> float:
        """
        Calculate total distance in km from route geometry.
        Uses Haversine formula to sum distances between consecutive points.
        
        Args:
            geometry: GeoJSON geometry object (LineString)
            
        Returns:
            Total distance in kilometers
        """
        coordinates = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            return 0.0
        
        total_distance = 0.0
        earth_radius_km = 6371.0  # Earth's radius in kilometers
        
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            
            # Convert to radians
            lat1_rad = radians(lat1)
            lat2_rad = radians(lat2)
            delta_lat = radians(lat2 - lat1)
            delta_lon = radians(lon2 - lon1)
            
            # Haversine formula
            a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            
            distance = earth_radius_km * c
            total_distance += distance
        
        return round(total_distance, 2)
    
    async def calculate_routes(
        self,
        source: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "drive"
    ) -> Dict[str, Any]:
        """
        Calculate multiple routes between source and destination using Geoapify API.
        
        Args:
            source: Tuple of (lat, lon) for starting point
            destination: Tuple of (lat, lon) for ending point
            mode: Travel mode - "drive", "walk", or "bike"
            
        Returns:
            Dictionary with routes array, best_route_id, and metadata
            
        Raises:
            HTTPException: On timeout, invalid API key, or no routes found
        """
        # Validate travel mode
        valid_modes = ["drive", "walk", "bike"]
        if mode not in valid_modes:
            mode = "drive"
        
        # Format waypoints: lat,lon|lat,lon
        waypoints = f"{source[0]},{source[1]}|{destination[0]},{destination[1]}"
        
        # Build request parameters
        params = {
            "waypoints": waypoints,
            "mode": mode,
            "alternatives": "true",  # Request multiple route alternatives
            "apiKey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.routing_url,
                    params=params
                )
                
                # Handle HTTP status codes
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid API key")
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Geoapify API error: {response.text}"
                    )
                
                data = response.json()
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=503,
                detail="Geoapify API timeout - please try again"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Network error connecting to Geoapify: {str(e)}"
            )
        
        # Extract routes from response features
        features = data.get("features", [])
        
        if not features:
            raise HTTPException(
                status_code=404,
                detail="No routes found between these locations"
            )
        
        # Get current time for traffic calculation
        now = datetime.now()
        hour = now.hour
        
        # Process each route
        routes = []
        for index, feature in enumerate(features):
            geometry = feature.get("geometry", {})
            properties = feature.get("properties", {})
            
            # Extract path coordinates
            path = self._extract_coordinates(geometry)
            
            # Get distance from properties (in meters, convert to km)
            distance_m = properties.get("distance", 0)
            distance_km = round(distance_m / 1000, 2) if distance_m else self._calculate_distance_from_geometry(geometry)
            
            # Get traffic factor based on current time
            traffic_factor, traffic_label = self._get_traffic_factor(hour)
            
            # Calculate final cost (distance weighted by traffic)
            final_cost = round(distance_km * traffic_factor, 2)
            
            # Estimate time assuming 40 km/h free-flow speed, adjusted by traffic
            estimated_time_minutes = round(
                (distance_km / 40) * traffic_factor * 60,
                1
            )
            
            route = {
                "id": index + 1,
                "path": path,
                "distance_km": distance_km,
                "traffic": traffic_label,
                "traffic_factor": traffic_factor,
                "cost": final_cost,
                "estimated_time_minutes": estimated_time_minutes
            }
            routes.append(route)
        
        # Select best route (lowest cost)
        best_route = min(routes, key=lambda x: x["cost"])
        best_route_id = best_route["id"]
        
        # Build response
        result = {
            "routes": routes,
            "best_route_id": best_route_id,
            "total_routes": len(routes),
            "calculation_timestamp": now.isoformat()
        }
        
        return result


class HTTPException(Exception):
    """Custom HTTP exception for routing errors."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
