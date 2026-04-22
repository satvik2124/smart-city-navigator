"""
Database Module - SQLite database for route history and logs
Smart City Navigator - AI-Based Smart City Navigation System

Provides database operations for storing routes, logs, and simulation data.
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class RouteRecord:
    """Route calculation record"""
    route_id: str
    source_lat: float
    source_lon: float
    dest_lat: float
    dest_lon: float
    algorithm: str
    distance_km: float
    duration_min: float
    traffic_level: str
    path_json: str
    created_at: str


@dataclass
class TrafficLog:
    """Traffic simulation log entry"""
    id: int
    timestamp: str
    hour: int
    day_of_week: int
    avg_congestion: float
    zone_data: str


@dataclass
class PredictionLog:
    """Traffic prediction log entry"""
    id: int
    timestamp: str
    input_params: str
    predicted_time: float
    actual_time: Optional[float]
    error: Optional[float]


class Database:
    """
    SQLite database manager for Smart City Navigator.
    
    Handles:
    - Route history storage
    - Traffic logs
    - Prediction logs
    - User preferences
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "smartcity.db"
            )
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._initialize_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT UNIQUE NOT NULL,
                    source_lat REAL NOT NULL,
                    source_lon REAL NOT NULL,
                    dest_lat REAL NOT NULL,
                    dest_lon REAL NOT NULL,
                    algorithm TEXT NOT NULL,
                    distance_km REAL NOT NULL,
                    duration_min REAL NOT NULL,
                    traffic_level TEXT,
                    path_json TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    avg_congestion REAL NOT NULL,
                    zone_data TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    input_params TEXT NOT NULL,
                    predicted_time REAL NOT NULL,
                    actual_time REAL,
                    error REAL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    simulation_type TEXT NOT NULL,
                    parameters TEXT,
                    results TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_key TEXT UNIQUE NOT NULL,
                    preference_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_routes_created 
                ON routes(created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_traffic_timestamp 
                ON traffic_logs(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prediction_timestamp 
                ON prediction_logs(timestamp)
            """)
            
            conn.commit()
            
            print(f"Database initialized at {self.db_path}")
    
    async def save_route(
        self,
        route_id: str,
        source: tuple,
        destination: tuple,
        route_data: Dict
    ) -> bool:
        """Save a route calculation to history"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO routes (
                        route_id, source_lat, source_lon, dest_lat, dest_lon,
                        algorithm, distance_km, duration_min, traffic_level,
                        path_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    route_id,
                    source[0], source[1],
                    destination[0], destination[1],
                    route_data.get('algorithm_used', 'dijkstra'),
                    route_data.get('distance_km', 0),
                    route_data.get('duration_minutes', 0),
                    route_data.get('traffic_level', 'unknown'),
                    json.dumps(route_data.get('path', [])),
                    datetime.now().isoformat()
                ))
                
                return True
        except Exception as e:
            print(f"Error saving route: {e}")
            return False
    
    async def get_route_history(self, limit: int = 10) -> List[Dict]:
        """Get recent route history"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM routes 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        "route_id": row["route_id"],
                        "source": {
                            "lat": row["source_lat"],
                            "lon": row["source_lon"]
                        },
                        "destination": {
                            "lat": row["dest_lat"],
                            "lon": row["dest_lon"]
                        },
                        "algorithm": row["algorithm"],
                        "distance_km": row["distance_km"],
                        "duration_min": row["duration_min"],
                        "traffic_level": row["traffic_level"],
                        "created_at": row["created_at"]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting route history: {e}")
            return []
    
    async def get_route_by_id(self, route_id: str) -> Optional[Dict]:
        """Get a specific route by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM routes WHERE route_id = ?
                """, (route_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        "route_id": row["route_id"],
                        "source": {
                            "lat": row["source_lat"],
                            "lon": row["source_lon"]
                        },
                        "destination": {
                            "lat": row["dest_lat"],
                            "lon": row["dest_lon"]
                        },
                        "algorithm": row["algorithm"],
                        "distance_km": row["distance_km"],
                        "duration_min": row["duration_min"],
                        "traffic_level": row["traffic_level"],
                        "path": json.loads(row["path_json"]) if row["path_json"] else [],
                        "created_at": row["created_at"]
                    }
                return None
        except Exception as e:
            print(f"Error getting route: {e}")
            return None
    
    async def log_traffic(self, traffic_data: Dict) -> bool:
        """Log traffic simulation data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO traffic_logs (
                        timestamp, hour, day_of_week, avg_congestion, zone_data
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    traffic_data.get('hour', 0),
                    traffic_data.get('day_of_week', 0),
                    traffic_data.get('congestion_level', 0),
                    json.dumps(traffic_data.get('zones', []))
                ))
                
                return True
        except Exception as e:
            print(f"Error logging traffic: {e}")
            return False
    
    async def get_traffic_history(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent traffic history"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM traffic_logs 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (cutoff_time.isoformat(), limit))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "hour": row["hour"],
                        "day_of_week": row["day_of_week"],
                        "avg_congestion": row["avg_congestion"],
                        "zones": json.loads(row["zone_data"]) if row["zone_data"] else []
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting traffic history: {e}")
            return []
    
    async def log_prediction(
        self,
        input_params: Dict,
        predicted_time: float,
        actual_time: Optional[float] = None
    ) -> bool:
        """Log a traffic prediction"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                error = None
                if actual_time is not None:
                    error = abs(predicted_time - actual_time) / actual_time * 100
                
                cursor.execute("""
                    INSERT INTO prediction_logs (
                        timestamp, input_params, predicted_time,
                        actual_time, error
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    json.dumps(input_params),
                    predicted_time,
                    actual_time,
                    error
                ))
                
                return True
        except Exception as e:
            print(f"Error logging prediction: {e}")
            return False
    
    async def get_prediction_accuracy(self, days: int = 7) -> Dict:
        """Calculate prediction accuracy over time"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_predictions,
                        AVG(error) as avg_error,
                        MAX(error) as max_error,
                        MIN(error) as min_error,
                        AVG(CASE WHEN error < 10 THEN 1 ELSE 0 END) * 100 as accuracy_below_10
                    FROM prediction_logs 
                    WHERE timestamp >= ? AND error IS NOT NULL
                """, (cutoff_time.isoformat(),))
                
                row = cursor.fetchone()
                
                return {
                    "total_predictions": row["total_predictions"] or 0,
                    "avg_error_percent": round(row["avg_error"] or 0, 2),
                    "max_error_percent": round(row["max_error"] or 0, 2),
                    "min_error_percent": round(row["min_error"] or 0, 2),
                    "accuracy_below_10_percent": round(row["accuracy_below_10"] or 0, 2)
                }
        except Exception as e:
            print(f"Error getting prediction accuracy: {e}")
            return {}
    
    async def save_preference(self, key: str, value: Any) -> bool:
        """Save a user preference"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                value_str = json.dumps(value) if not isinstance(value, str) else value
                
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences (
                        preference_key, preference_value, updated_at
                    ) VALUES (?, ?, ?)
                """, (key, value_str, datetime.now().isoformat()))
                
                return True
        except Exception as e:
            print(f"Error saving preference: {e}")
            return False
    
    async def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT preference_value FROM user_preferences 
                    WHERE preference_key = ?
                """, (key,))
                
                row = cursor.fetchone()
                
                if row:
                    try:
                        return json.loads(row["preference_value"])
                    except json.JSONDecodeError:
                        return row["preference_value"]
                return default
        except Exception as e:
            print(f"Error getting preference: {e}")
            return default
    
    async def get_statistics(self) -> Dict:
        """Get overall system statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                cursor.execute("SELECT COUNT(*) as count FROM routes")
                stats["total_routes"] = cursor.fetchone()["count"]
                
                cursor.execute("SELECT COUNT(*) as count FROM traffic_logs")
                stats["total_traffic_logs"] = cursor.fetchone()["count"]
                
                cursor.execute("SELECT COUNT(*) as count FROM prediction_logs")
                stats["total_predictions"] = cursor.fetchone()["count"]
                
                cursor.execute("""
                    SELECT AVG(distance_km) as avg_dist, 
                           AVG(duration_min) as avg_duration
                    FROM routes
                """)
                row = cursor.fetchone()
                stats["avg_route_distance"] = round(row["avg_dist"] or 0, 2)
                stats["avg_route_duration"] = round(row["avg_duration"] or 0, 2)
                
                return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    async def clear_old_data(self, days: int = 30) -> Dict:
        """Clear old data from tables"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM routes WHERE created_at < ?", (cutoff_time.isoformat(),))
                routes_deleted = cursor.rowcount
                
                cursor.execute("DELETE FROM traffic_logs WHERE timestamp < ?", (cutoff_time.isoformat(),))
                traffic_deleted = cursor.rowcount
                
                cursor.execute("DELETE FROM prediction_logs WHERE timestamp < ?", (cutoff_time.isoformat(),))
                predictions_deleted = cursor.rowcount
                
                return {
                    "routes_deleted": routes_deleted,
                    "traffic_logs_deleted": traffic_deleted,
                    "predictions_deleted": predictions_deleted
                }
        except Exception as e:
            print(f"Error clearing old data: {e}")
            return {}
