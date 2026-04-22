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
        self.api_key = api_key
        self.base_url = base_url
        self.routing_url = f"{base_url}/v1/routing"
    
    def _get_traffic_factor(self, hour: int) -> Tuple[float, str]:
        if 7 <= hour < 10:
            base = 2.0
        elif 10 <= hour < 16:
            base = 1.5
        elif 16 <= hour < 20:
            base = 2.0
        else:
            base = 1.0
        
        variation = random.uniform(0.9, 1.1)
        traffic_factor = round(base * variation, 2)
        
        if traffic_factor < 1.2:
            traffic_label = "Low"
        elif traffic_factor < 1.7:
            traffic_label = "Medium"
        else:
            traffic_label = "High"
        
        return traffic_factor, traffic_label
    
    def _extract_coordinates(self, geometry: Dict[str, Any]) -> List[List[float]]:
        coordinates = geometry.get("coordinates", [])
        return [[coord[1], coord[0]] for coord in coordinates]
    
    def _calculate_distance_from_geometry(self, geometry: Dict[str, Any]) -> float:
        coordinates = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            return 0.0
        
        total_distance = 0.0
        earth_radius_km = 6371.0
        
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            
            lat1_rad = radians(lat1)
            lat2_rad = radians(lat2)
            delta_lat = radians(lat2 - lat1)
            delta_lon = radians(lon2 - lon1)
            
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
        valid_modes = ["drive", "walk", "bike"]
        if mode not in valid_modes:
            mode = "drive"
        
        waypoints = f"{source[0]},{source[1]}|{destination[0]},{destination[1]}"
        
        params = {
            "waypoints": waypoints,
            "mode": mode,
            "alternatives": "true",
            "apiKey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.routing_url,
                    params=params
                )
                
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
        
        features = data.get("features", [])
        
        if not features:
            raise HTTPException(
                status_code=404,
                detail="No routes found between these locations"
            )
        
        now = datetime.now()
        hour = now.hour
        
        routes = []
        for index, feature in enumerate(features):
            geometry = feature.get("geometry", {})
            properties = feature.get("properties", {})
            
            path = self._extract_coordinates(geometry)
            
            distance_m = properties.get("distance", 0)
            distance_km = round(distance_m / 1000, 2) if distance_m else self._calculate_distance_from_geometry(geometry)
            
            traffic_factor, traffic_label = self._get_traffic_factor(hour)
            
            final_cost = round(distance_km * traffic_factor, 2)
            
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
        
        best_route = min(routes, key=lambda x: x["cost"])
        best_route_id = best_route["id"]
        
        result = {
            "routes": routes,
            "best_route_id": best_route_id,
            "total_routes": len(routes),
            "calculation_timestamp": now.isoformat()
        }
        
        return result


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
