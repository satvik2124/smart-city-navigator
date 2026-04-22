"""
Smart City Navigator - Main FastAPI Application
AI-Based Smart City Navigation System with Geoapify Integration
"""

import os
import uuid
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from pydantic.functional_validators import model_validator

from routing import RoutingClient, HTTPException as RoutingHTTPException


API_KEY = os.getenv("GEOAPIFY_API_KEY", "")

try:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("GEOAPIFY_API_KEY", "")
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Initialize routing client if API key is available
    app.state.routing_client = None
    if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
        app.state.routing_client = RoutingClient(API_KEY)
        print("Geoapify Routing client initialized")
    else:
        print("WARNING: GEOAPIFY_API_KEY not set")
    
    # Initialize database on startup
    init_database()
    print("Database initialized")
    
    yield
    
    # Cleanup on shutdown (if needed)
    print("Application shutting down")


# Create FastAPI application instance
app = FastAPI(
    title="Smart City Navigator API",
    description="AI-Powered Navigation with Multi-Route Optimization",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Pydantic Models for Request/Response Validation
# =============================================================================

class RouteRequest(BaseModel):
    """Request model for route calculation endpoint."""
    source: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Source location name or address"
    )
    destination: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Destination location name or address"
    )
    mode: str = Field(
        default="drive",
        description="Travel mode: drive, walk, or bike"
    )
    
    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Ensure mode is one of the allowed values."""
        valid_modes = ["drive", "walk", "bike"]
        if v.lower() not in valid_modes:
            raise ValueError(f"mode must be one of: {', '.join(valid_modes)}")
        return v.lower()
    
    @model_validator(mode="after")
    def validate_locations_different(self) -> "RouteRequest":
        """Ensure source and destination are different."""
        if self.source.lower().strip() == self.destination.lower().strip():
            raise ValueError("source and destination cannot be the same")
        return self


class GeocodeResult(BaseModel):
    """Result of geocoding a location."""
    name: str
    lat: float
    lon: float
    full_address: Optional[str] = None


class RouteResponse(BaseModel):
    """Response model for route calculation."""
    routes: List[dict]
    best_route_id: int
    total_routes: int
    calculation_timestamp: str
    source: dict
    destination: dict


# =============================================================================
# Database Functions
# =============================================================================

DATABASE_PATH = "smart_city_navigator.db"


def init_database():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create route_history table for storing route calculations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_history (
            id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            destination_name TEXT NOT NULL,
            source_lat REAL NOT NULL,
            source_lon REAL NOT NULL,
            destination_lat REAL NOT NULL,
            destination_lon REAL NOT NULL,
            total_routes INTEGER NOT NULL,
            best_route_id INTEGER NOT NULL,
            best_route_cost REAL NOT NULL,
            best_route_distance REAL NOT NULL,
            best_route_time REAL NOT NULL,
            calculation_timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def save_route_to_history(
    route_id: str,
    source_name: str,
    destination_name: str,
    source_coords: Tuple[float, float],
    dest_coords: Tuple[float, float],
    result: dict
):
    """
    Save route calculation to database history.
    
    Args:
        route_id: Unique identifier for this route calculation
        source_name: Name of source location
        destination_name: Name of destination location
        source_coords: Tuple of (lat, lon) for source
        dest_coords: Tuple of (lat, lon) for destination
        result: Full routing result dictionary
    """
    # Find best route info
    best_route = next(
        (r for r in result["routes"] if r["id"] == result["best_route_id"]),
        result["routes"][0] if result["routes"] else {}
    )
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO route_history (
            id, source_name, destination_name,
            source_lat, source_lon, destination_lat, destination_lon,
            total_routes, best_route_id, best_route_cost,
            best_route_distance, best_route_time, calculation_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        route_id,
        source_name,
        destination_name,
        source_coords[0],
        source_coords[1],
        dest_coords[0],
        dest_coords[1],
        result["total_routes"],
        result["best_route_id"],
        best_route.get("cost", 0),
        best_route.get("distance_km", 0),
        best_route.get("estimated_time_minutes", 0),
        result["calculation_timestamp"]
    ))
    
    conn.commit()
    conn.close()


# =============================================================================
# Geocoding Functions (using httpx directly)
# =============================================================================

async def geocode_location(location: str, api_key: str) -> Optional[GeocodeResult]:
    """
    Geocode a location string to coordinates using Geoapify Geocoding API.
    
    Args:
        location: Location name or address to geocode
        api_key: Geoapify API key
        
    Returns:
        GeocodeResult with coordinates or None if not found
    """
    import httpx
    
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": location,
        "apiKey": api_key,
        "limit": 1
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            features = data.get("features", [])
            
            if not features:
                return None
            
            result = features[0]
            props = result.get("properties", {})
            return GeocodeResult(
                name=props.get("name", location),
                lat=props.get("lat", 0),
                lon=props.get("lon", 0),
                full_address=props.get("formatted", None)
            )
    
    except (httpx.TimeoutException, httpx.RequestError):
        return None


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint - returns API information."""
    return {
        "name": "Smart City Navigator API",
        "version": "3.0.0",
        "description": "AI-Powered Multi-Route Navigation System",
        "geoapify_enabled": bool(API_KEY and API_KEY != "YOUR_API_KEY_HERE"),
        "endpoints": {
            "GET /health": "Health check",
            "POST /calculate-route": "Calculate optimal routes between two locations",
            "GET /routes-history": "Get recent route calculations",
            "GET /routes-history/{id}": "Get specific route by ID"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - returns service status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "operational",
            "geoapify": "connected" if API_KEY else "disabled",
            "database": "connected"
        }
    }


@app.post("/calculate-route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """
    Calculate multiple optimal routes between source and destination.
    
    This endpoint geocodes both locations, calls the routing API to get
    multiple route alternatives, and returns them with traffic-aware scoring.
    """
    # Check if routing client is available
    if not app.state.routing_client:
        raise HTTPException(
            status_code=503,
            detail="Geoapify API key not configured. Please set GEOAPIFY_API_KEY."
        )
    
    # Geocode source location
    source_geo = await geocode_location(request.source, API_KEY)
    if not source_geo:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find source location: {request.source}"
        )
    
    # Geocode destination location
    dest_geo = await geocode_location(request.destination, API_KEY)
    if not dest_geo:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find destination location: {request.destination}"
        )
    
    # Calculate routes using routing client
    try:
        routing_result = await app.state.routing_client.calculate_routes(
            source=(source_geo.lat, source_geo.lon),
            destination=(dest_geo.lat, dest_geo.lon),
            mode=request.mode
        )
    except RoutingHTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    # Generate unique route ID for history tracking
    route_id = str(uuid.uuid4())[:8]
    
    # Save to database history
    try:
        save_route_to_history(
            route_id=route_id,
            source_name=request.source,
            destination_name=request.destination,
            source_coords=(source_geo.lat, source_geo.lon),
            dest_coords=(dest_geo.lat, dest_geo.lon),
            result=routing_result
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Database save error: {e}")
    
    # Build and return response
    return RouteResponse(
        routes=routing_result["routes"],
        best_route_id=routing_result["best_route_id"],
        total_routes=routing_result["total_routes"],
        calculation_timestamp=routing_result["calculation_timestamp"],
        source={
            "name": request.source,
            "lat": source_geo.lat,
            "lon": source_geo.lon,
            "formatted": source_geo.full_address
        },
        destination={
            "name": request.destination,
            "lat": dest_geo.lat,
            "lon": dest_geo.lon,
            "formatted": dest_geo.full_address
        }
    )


@app.get("/routes-history")
async def get_routes_history(limit: int = Query(default=10, ge=1, le=50)):
    """
    Get history of recent route calculations.
    
    Args:
        limit: Maximum number of routes to return (default: 10, max: 50)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM route_history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    routes = []
    for row in rows:
        routes.append({
            "id": row["id"],
            "source_name": row["source_name"],
            "destination_name": row["destination_name"],
            "source_coordinates": {
                "lat": row["source_lat"],
                "lon": row["source_lon"]
            },
            "destination_coordinates": {
                "lat": row["destination_lat"],
                "lon": row["destination_lon"]
            },
            "total_routes": row["total_routes"],
            "best_route_id": row["best_route_id"],
            "best_route": {
                "cost": row["best_route_cost"],
                "distance_km": row["best_route_distance"],
                "estimated_time_minutes": row["best_route_time"]
            },
            "calculation_timestamp": row["calculation_timestamp"],
            "created_at": row["created_at"]
        })
    
    return {"status": "success", "count": len(routes), "routes": routes}


@app.get("/routes-history/{route_id}")
async def get_route_by_id(route_id: str):
    """Get a specific route calculation by its ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM route_history WHERE id = ?",
        (route_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {
        "id": row["id"],
        "source_name": row["source_name"],
        "destination_name": row["destination_name"],
        "source_coordinates": {
            "lat": row["source_lat"],
            "lon": row["source_lon"]
        },
        "destination_coordinates": {
            "lat": row["destination_lat"],
            "lon": row["destination_lon"]
        },
        "total_routes": row["total_routes"],
        "best_route_id": row["best_route_id"],
        "best_route": {
            "cost": row["best_route_cost"],
            "distance_km": row["best_route_distance"],
            "estimated_time_minutes": row["best_route_time"]
        },
        "calculation_timestamp": row["calculation_timestamp"],
        "created_at": row["created_at"]
    }


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
