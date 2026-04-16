"""
Smart City Navigator - Main FastAPI Application
AI-Based Smart City Navigation System with Geoapify Integration
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

API_KEY = os.getenv("GEOAPIFY_API_KEY", "")

try:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
except:
    pass

try:
    from geocoding import GeoapifyClient, Coordinates
    from simulation import TrafficSimulator
    from ai_model import TrafficPredictor
    from routing import Router
    from database import Database
except ImportError:
    from backend.geocoding import GeoapifyClient, Coordinates
    from backend.simulation import TrafficSimulator
    from backend.ai_model import TrafficPredictor
    from backend.routing import Router
    from backend.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    app.state.geoapify = None
    app.state.traffic_sim = TrafficSimulator()
    app.state.ai_model = TrafficPredictor()
    app.state.router = Router()
    app.state.database = Database()
    
    if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
        app.state.geoapify = GeoapifyClient(API_KEY)
        print("Geoapify client initialized!")
    else:
        print("WARNING: GEOAPIFY_API_KEY not set. Using fallback routing.")
    
    yield
    
    if app.state.geoapify:
        await app.state.geoapify.close()


app = FastAPI(
    title="Smart City Navigator API",
    description="AI-Powered Navigation with Geoapify Routing",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GeocodeRequest(BaseModel):
    query: str = Field(..., description="Place name to geocode")


class RouteRequest(BaseModel):
    source: str = Field(..., description="Source place name")
    destination: str = Field(..., description="Destination place name")
    mode: str = Field(default="drive", description="Travel mode: drive, walk, bicycle")


class RouteResponse(BaseModel):
    routes: List[Dict]
    optimal_route: Dict
    source: Dict
    destination: Dict
    traffic: Dict
    timestamp: str


PREDEFINED_LOCATIONS = {
    "delhi": {"lat": 28.6139, "lon": 77.2090, "name": "Delhi"},
    "new delhi": {"lat": 28.6139, "lon": 77.2090, "name": "New Delhi"},
    "connaught place": {"lat": 28.6318, "lon": 77.2165, "name": "Connaught Place"},
    "karol bagh": {"lat": 28.6519, "lon": 77.1908, "name": "Karol Bagh"},
    "dwarka": {"lat": 28.5703, "lon": 77.0710, "name": "Dwarka"},
    "lajpat nagar": {"lat": 28.5677, "lon": 77.2433, "name": "Lajpat Nagar"},
    "saket": {"lat": 28.5245, "lon": 77.2066, "name": "Saket"},
    "nehru place": {"lat": 28.5503, "lon": 77.2510, "name": "Nehru Place"},
    "sector 21": {"lat": 28.6189, "lon": 77.2150, "name": "Sector 21"},
    "sector 25": {"lat": 28.6259, "lon": 77.2200, "name": "Sector 25"},
    "noida": {"lat": 28.5355, "lon": 77.3910, "name": "Noida"},
    "gurgaon": {"lat": 28.4595, "lon": 77.0264, "name": "Gurgaon"},
    "airport": {"lat": 28.5562, "lon": 77.1000, "name": "IGI Airport"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "name": "Bangalore"},
}


@app.get("/")
async def root():
    return {
        "name": "Smart City Navigator API",
        "version": "2.0.0",
        "geoapify_enabled": bool(API_KEY and API_KEY != "YOUR_API_KEY_HERE"),
        "endpoints": {
            "health": "/health",
            "geocode": "/geocode",
            "calculate_route": "/calculate-route",
            "simulate_traffic": "/simulate-traffic",
            "routes_history": "/routes-history"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "operational",
            "geoapify": "connected" if API_KEY else "disabled",
            "ai_model": "loaded",
            "traffic_simulation": "active",
            "database": "connected"
        }
    }


@app.post("/geocode")
async def geocode(request: GeocodeRequest):
    if not app.state.geoapify:
        return {"error": "Geoapify not configured", "results": []}
    
    try:
        results = await app.state.geoapify.geocode(request.query)
        return {
            "status": "success",
            "count": len(results),
            "results": [
                {
                    "name": r.name,
                    "address": r.full_address,
                    "lat": r.coordinates.lat,
                    "lon": r.coordinates.lon
                }
                for r in results[:5]
            ]
        }
    except Exception as e:
        return {"error": str(e), "results": []}


@app.post("/calculate-route")
async def calculate_route(request: RouteRequest):
    now = datetime.now()
    route_id = str(uuid.uuid4())[:8]
    
    source_data = _find_location(request.source)
    dest_data = _find_location(request.destination)
    
    if not source_data:
        raise HTTPException(status_code=404, detail=f"Source '{request.source}' not found")
    if not dest_data:
        raise HTTPException(status_code=404, detail=f"Destination '{request.destination}' not found")
    
    source_coords = Coordinates(lat=source_data["lat"], lon=source_data["lon"])
    dest_coords = Coordinates(lat=dest_data["lat"], lon=dest_data["lon"])
    
    traffic = app.state.traffic_sim.simulate()
    
    routes = []
    
    try:
        if app.state.geoapify and API_KEY and API_KEY != "YOUR_API_KEY_HERE":
            geoapify_routes = await app.state.geoapify.calculate_route(
                source_coords, dest_coords, mode=request.mode
            )
            
            for i, route in enumerate(geoapify_routes):
                adjusted = app.state.traffic_sim.get_adjusted_travel_time(
                    route.time_minutes, now.hour, now.weekday()
                )
                
                routes.append({
                    "route_id": route.route_id,
                    "route_index": i + 1,
                    "distance_km": round(route.distance_km, 2),
                    "distance_text": _format_distance(route.distance_km),
                    "duration_minutes": round(adjusted["adjusted_time"], 1),
                    "duration_text": _format_duration(adjusted["adjusted_time"]),
                    "geometry": [{"lat": c.lat, "lon": c.lon} for c in route.geometry],
                    "polyline": route.polyline,
                    "traffic_delay": round(adjusted["delay_minutes"], 1),
                    "congestion_level": adjusted["congestion_level"],
                    "traffic_status": adjusted["traffic_status"],
                    "is_optimal": False,
                    "color": _get_route_color(i)
                })
        else:
            routes = _generate_fallback_routes(source_coords, dest_coords, app.state.traffic_sim, traffic, now)
    except Exception as e:
        print(f"Route error: {e}")
        import traceback
        traceback.print_exc()
        routes = _generate_fallback_routes(source_coords, dest_coords, app.state.traffic_sim, traffic, now)
    
    if routes:
        optimal = min(routes, key=lambda x: x["duration_minutes"])
        for r in routes:
            r["is_optimal"] = r["route_id"] == optimal["route_id"]
    
    try:
        await app.state.database.save_route(
            route_id,
            (source_coords.lat, source_coords.lon),
            (dest_coords.lat, dest_coords.lon),
            {"routes": routes, "optimal": optimal if routes else {}}
        )
    except Exception as e:
        print(f"Database error: {e}")
    
    return {
        "routes": routes,
        "optimal_route": optimal if routes else {},
        "source": {
            "name": source_data["name"],
            "coordinates": {"lat": source_coords.lat, "lon": source_coords.lon}
        },
        "destination": {
            "name": dest_data["name"],
            "coordinates": {"lat": dest_coords.lat, "lon": dest_coords.lon}
        },
        "traffic": traffic.to_dict(),
        "timestamp": now.isoformat()
    }


@app.get("/simulate-traffic")
async def simulate_traffic():
    traffic = app.state.traffic_sim.simulate()
    return {"status": "success", **traffic.to_dict()}


@app.get("/routes-history")
async def get_routes_history(limit: int = Query(default=10, le=50)):
    routes = await app.state.database.get_route_history(limit)
    return {"status": "success", "count": len(routes), "routes": routes}


def _find_location(query: str):
    """Find location by name or return None"""
    query_lower = query.lower().strip()
    
    for key, val in PREDEFINED_LOCATIONS.items():
        if key in query_lower or query_lower in key:
            return val
    
    if app.state.geoapify and API_KEY and API_KEY != "YOUR_API_KEY_HERE":
        try:
            import asyncio
            results = asyncio.run(app.state.geoapify.geocode(query))
            if results:
                return {
                    "lat": results[0].coordinates.lat,
                    "lon": results[0].coordinates.lon,
                    "name": results[0].name
                }
        except:
            pass
    
    return None


def _generate_fallback_routes(source, dest, traffic_sim, traffic_data, now):
    """Generate fallback routes"""
    import math
    
    R = 6371
    lat1, lon1 = math.radians(source.lat), math.radians(source.lon)
    lat2, lon2 = math.radians(dest.lat), math.radians(dest.lon)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = R * c
    
    variations = [
        {"name": "Fastest Route", "factor": 1.0, "offset": 0},
        {"name": "Shortest Path", "factor": 0.95, "offset": 0.3},
        {"name": "Via Highway", "factor": 1.05, "offset": 0.2},
    ]
    
    congestion = traffic_data.overall_congestion
    
    routes = []
    for i, var in enumerate(variations):
        adjusted_time = (distance_km / 40) * 60 * var["factor"]
        final_time = adjusted_time * (1 + congestion * 0.5)
        
        points = _generate_points(source, dest, 15, var["offset"])
        
        routes.append({
            "route_id": f"route_{i+1}",
            "route_index": i + 1,
            "distance_km": round(distance_km * var["factor"], 2),
            "distance_text": _format_distance(distance_km * var["factor"]),
            "duration_minutes": round(final_time, 1),
            "duration_text": _format_duration(final_time),
            "geometry": [{"lat": p[0], "lon": p[1]} for p in points],
            "polyline": points,
            "traffic_delay": round(final_time - adjusted_time, 1),
            "congestion_level": round(congestion, 3),
            "traffic_status": "light" if congestion < 0.3 else "moderate" if congestion < 0.6 else "heavy",
            "is_optimal": i == 0,
            "color": _get_route_color(i)
        })
    
    return routes


def _generate_points(source, dest, num_points, offset):
    import random
    random.seed(42)
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = source.lat + (dest.lat - source.lat) * t
        lon = source.lon + (dest.lon - source.lon) * t
        if i > 0 and i < num_points and offset > 0:
            lat += random.uniform(-offset, offset) * 0.01
            lon += random.uniform(-offset, offset) * 0.01
        points.append((lat, lon))
    return points


def _format_distance(km: float) -> str:
    if km < 1:
        return f"{int(km * 1000)} m"
    return f"{km:.1f} km"


def _format_duration(minutes: float) -> str:
    if minutes < 1:
        return "Less than 1 min"
    if minutes < 60:
        return f"{int(minutes)} min"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"


def _get_route_color(index: int) -> str:
    colors = ["#22c55e", "#3b82f6", "#f97316", "#a855f7", "#ec4899"]
    return colors[index % len(colors)]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
