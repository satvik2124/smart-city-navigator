"""
Dynamic Traffic Simulation Module
Smart City Navigator - AI-Based Smart City Navigation System

Simulates real-world traffic conditions that change each time the program runs.
"""

import random
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TimePeriod(Enum):
    """Traffic time periods"""
    NIGHT = "night"
    EARLY_MORNING = "early_morning"
    MORNING_RUSH = "morning_rush"
    LATE_MORNING = "late_morning"
    LUNCH_TIME = "lunch_time"
    AFTERNOON = "afternoon"
    EVENING_RUSH = "evening_rush"
    EVENING = "evening"
    LATE_NIGHT = "late_night"


@dataclass
class TrafficCondition:
    """Traffic condition for a road segment"""
    road_id: str
    congestion_level: float  # 0.0 to 1.0
    speed_multiplier: float  # 0.0 to 1.0 (1.0 = normal speed)
    travel_time_multiplier: float  # 1.0 = normal
    status: str  # "free", "light", "moderate", "heavy", "severe"
    confidence: float  # Prediction confidence
    
    @property
    def description(self) -> str:
        if self.congestion_level < 0.15:
            return "Free flow traffic - No delays"
        elif self.congestion_level < 0.3:
            return "Light traffic - Good conditions"
        elif self.congestion_level < 0.5:
            return "Moderate traffic - Some delays"
        elif self.congestion_level < 0.7:
            return "Heavy traffic - Significant delays"
        elif self.congestion_level < 0.85:
            return "Severe congestion - Major delays"
        else:
            return "Standstill traffic - Avoid if possible"


@dataclass
class RoadSegment:
    """Road segment with traffic info"""
    road_id: str
    road_name: str
    road_type: str  # highway, arterial, local
    base_speed: float  # km/h
    length: float  # km
    
    congestion: float = 0.3
    current_speed: float = 0
    travel_time: float = 0  # minutes
    
    def __post_init__(self):
        self.current_speed = self.base_speed * (1 - self.congestion * 0.7)
        self.travel_time = (self.length / max(self.current_speed, 0.1)) * 60


@dataclass
class TrafficSimulation:
    """Complete traffic simulation data"""
    timestamp: str
    hour: int
    day_of_week: int
    time_period: str
    overall_congestion: float
    traffic_zones: List[Dict]
    road_conditions: Dict[str, TrafficCondition]
    description: str
    patterns: Dict


class TrafficSimulator:
    """
    Dynamic traffic simulation system.
    
    Simulates realistic traffic conditions that change based on:
    - Time of day
    - Day of week
    - Road types
    - Random fluctuations
    
    Traffic patterns:
    - Morning Rush (7-9 AM): High congestion
    - Lunch Time (12-2 PM): Medium congestion
    - Evening Rush (5-8 PM): Highest congestion
    - Night (10 PM - 6 AM): Low congestion
    """
    
    # Time period definitions
    TIME_PERIODS = {
        (0, 5): TimePeriod.NIGHT,
        (6, 6): TimePeriod.EARLY_MORNING,
        (7, 9): TimePeriod.MORNING_RUSH,
        (10, 11): TimePeriod.LATE_MORNING,
        (12, 14): TimePeriod.LUNCH_TIME,
        (15, 16): TimePeriod.AFTERNOON,
        (17, 19): TimePeriod.EVENING_RUSH,
        (20, 21): TimePeriod.EVENING,
        (22, 23): TimePeriod.LATE_NIGHT,
    }
    
    # Base congestion levels by time period
    BASE_CONGESTION = {
        TimePeriod.NIGHT: 0.08,
        TimePeriod.EARLY_MORNING: 0.15,
        TimePeriod.MORNING_RUSH: 0.65,
        TimePeriod.LATE_MORNING: 0.35,
        TimePeriod.LUNCH_TIME: 0.45,
        TimePeriod.AFTERNOON: 0.40,
        TimePeriod.EVENING_RUSH: 0.75,
        TimePeriod.EVENING: 0.30,
        TimePeriod.LATE_NIGHT: 0.12,
    }
    
    # Road type congestion modifiers
    ROAD_TYPE_MODIFIERS = {
        "highway": 0.9,  # Less affected by general traffic
        "arterial": 1.1,  # More affected
        "local": 0.85,  # Less affected
        "residential": 0.7,  # Much less affected
        "expressway": 0.95,
    }
    
    # Day of week modifiers (0 = Monday)
    DAY_MODIFIERS = {
        0: 1.0,   # Monday - normal
        1: 1.0,   # Tuesday - normal
        2: 0.95,  # Wednesday - slightly less
        3: 1.05,  # Thursday - slightly more
        4: 1.1,   # Friday - more traffic
        5: 0.8,   # Saturday - less work traffic
        6: 0.75,  # Sunday - least traffic
    }
    
    # Weather impact factors
    WEATHER_IMPACTS = {
        "clear": 1.0,
        "cloudy": 1.05,
        "rain": 1.25,
        "heavy_rain": 1.4,
        "fog": 1.2,
        "snow": 1.5,
    }
    
    def __init__(self, seed: int = None):
        """
        Initialize traffic simulator.
        
        Args:
            seed: Random seed for reproducibility (None = random each time)
        """
        if seed is not None:
            random.seed(seed)
        else:
            random.seed(datetime.now().microsecond)
        
        self.current_simulation = None
        self.simulation_count = 0
        self._road_cache: Dict[str, RoadSegment] = {}
    
    def get_time_period(self, hour: int) -> TimePeriod:
        """Get traffic time period for given hour"""
        for time_range, period in self.TIME_PERIODS.items():
            if time_range[0] <= hour <= time_range[1]:
                return period
        return TimePeriod.NIGHT
    
    def get_congestion_level(
        self,
        hour: int,
        day_of_week: int,
        road_type: str = "arterial",
        road_id: str = None,
        weather: str = "clear"
    ) -> TrafficCondition:
        """
        Calculate congestion level for given conditions.
        
        Args:
            hour: Hour of day (0-23)
            day_of_week: Day of week (0-6, 0=Monday)
            road_type: Type of road
            road_id: Unique road identifier
            weather: Weather condition
            
        Returns:
            TrafficCondition with congestion details
        """
        time_period = self.get_time_period(hour)
        
        base = self.BASE_CONGESTION[time_period]
        day_mod = self.DAY_MODIFIERS[day_of_week % 7]
        road_mod = self.ROAD_TYPE_MODIFIERS.get(road_type, 1.0)
        weather_mod = self.WEATHER_IMPACTS.get(weather, 1.0)
        
        random_factor = random.uniform(0.85, 1.15)
        
        if road_id and road_id in self._road_cache:
            road_variation = self._road_cache[road_id].congestion
            base = (base + road_variation) / 2
        
        congestion = base * day_mod * road_mod * weather_mod * random_factor
        congestion = max(0.0, min(1.0, congestion))
        
        speed_mult = 1.0 - (congestion * 0.7)
        time_mult = 1.0 + (congestion * 1.5)
        
        if congestion < 0.15:
            status = "free"
        elif congestion < 0.3:
            status = "light"
        elif congestion < 0.5:
            status = "moderate"
        elif congestion < 0.7:
            status = "heavy"
        else:
            status = "severe"
        
        confidence = 0.75 + random.uniform(0, 0.15)
        
        return TrafficCondition(
            road_id=road_id or f"road_{hour}_{day_of_week}",
            congestion_level=congestion,
            speed_multiplier=speed_mult,
            travel_time_multiplier=time_mult,
            status=status,
            confidence=min(confidence, 1.0)
        )
    
    def simulate(self, routes: List[Dict] = None) -> TrafficSimulation:
        """
        Generate complete traffic simulation.
        
        Args:
            routes: Optional list of routes to simulate
            
        Returns:
            TrafficSimulation with all traffic data
        """
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        time_period = self.get_time_period(hour)
        
        base_congestion = self.BASE_CONGESTION[time_period]
        day_mod = self.DAY_MODIFIERS[day_of_week]
        
        weather_choices = ["clear", "clear", "clear", "cloudy", "cloudy", "rain"]
        weather = random.choice(weather_choices)
        weather_mod = self.WEATHER_IMPACTS[weather]
        
        overall = base_congestion * day_mod * weather_mod * random.uniform(0.9, 1.1)
        overall = max(0.0, min(1.0, overall))
        
        traffic_zones = self._generate_traffic_zones(hour, day_of_week)
        
        road_conditions = {}
        road_types = ["highway", "arterial", "local", "residential"]
        
        if routes:
            for i, route in enumerate(routes[:5]):
                road_id = f"route_{i}_segment"
                road_type = random.choice(road_types)
                cond = self.get_congestion_level(hour, day_of_week, road_type, road_id, weather)
                road_conditions[road_id] = cond
        
        for road_type in road_types:
            for j in range(3):
                road_id = f"{road_type}_{j}"
                cond = self.get_congestion_level(hour, day_of_week, road_type, road_id, weather)
                road_conditions[road_id] = cond
        
        description = self._get_description(overall, time_period)
        
        patterns = {
            "rush_hour_multiplier": 1.5 if time_period in [TimePeriod.MORNING_RUSH, TimePeriod.EVENING_RUSH] else 1.0,
            "weekend_multiplier": 0.8 if day_of_week >= 5 else 1.0,
            "weather_impact": weather_mod,
            "predicted_delay_minutes": int(overall * 20)
        }
        
        simulation = TrafficSimulation(
            timestamp=now.isoformat(),
            hour=hour,
            day_of_week=day_of_week,
            time_period=time_period.value,
            overall_congestion=overall,
            traffic_zones=traffic_zones,
            road_conditions=road_conditions,
            description=description,
            patterns=patterns
        )
        
        self.current_simulation = simulation
        self.simulation_count += 1
        
        return simulation
    
    def _generate_traffic_zones(self, hour: int, day_of_week: int) -> List[Dict]:
        """Generate traffic data for different zones"""
        zones = [
            {"zone_id": "central", "name": "City Center", "congestion": 0, "impact": 1.2},
            {"zone_id": "north", "name": "North District", "congestion": 0, "impact": 1.0},
            {"zone_id": "south", "name": "South District", "congestion": 0, "impact": 1.0},
            {"zone_id": "east", "name": "East District", "congestion": 0, "impact": 0.95},
            {"zone_id": "west", "name": "West District", "congestion": 0, "impact": 1.05},
            {"zone_id": "highway", "name": "Highway Network", "congestion": 0, "impact": 0.8},
            {"zone_id": "suburban", "name": "Suburban Areas", "congestion": 0, "impact": 0.7},
        ]
        
        for zone in zones:
            base = self.BASE_CONGESTION[self.get_time_period(hour)]
            zone_congestion = base * zone["impact"] * random.uniform(0.85, 1.15)
            zone["congestion"] = max(0.0, min(1.0, zone_congestion))
        
        return zones
    
    def _get_description(self, congestion: float, time_period: TimePeriod) -> str:
        """Get human-readable traffic description"""
        if congestion < 0.15:
            return "Free flow traffic - No delays expected"
        elif congestion < 0.3:
            return "Light traffic - Good driving conditions"
        elif congestion < 0.5:
            return "Moderate traffic - Some delays possible"
        elif congestion < 0.7:
            return "Heavy traffic - Significant delays expected"
        else:
            return "Severe congestion - Major delays, consider alternative routes"
    
    def get_adjusted_travel_time(
        self,
        base_time_minutes: float,
        hour: int = None,
        day_of_week: int = None,
        road_type: str = "arterial"
    ) -> Dict:
        """
        Calculate adjusted travel time based on current traffic.
        
        Args:
            base_time_minutes: Base travel time without traffic
            hour: Hour of day (None = current)
            day_of_week: Day of week (None = current)
            road_type: Type of road
            
        Returns:
            Dict with original and adjusted times
        """
        if hour is None:
            hour = datetime.now().hour
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        
        cond = self.get_congestion_level(hour, day_of_week, road_type)
        
        adjusted_time = base_time_minutes * cond.travel_time_multiplier
        delay = adjusted_time - base_time_minutes
        
        return {
            "base_time": round(base_time_minutes, 1),
            "adjusted_time": round(adjusted_time, 1),
            "delay_minutes": round(delay, 1),
            "congestion_level": round(cond.congestion_level, 3),
            "traffic_status": cond.status,
            "description": cond.description
        }
    
    def predict_eta(
        self,
        distance_km: float,
        base_speed_kmh: float = 40,
        hour: int = None,
        day_of_week: int = None
    ) -> Dict:
        """
        Predict ETA considering traffic.
        
        Args:
            distance_km: Distance in kilometers
            base_speed_kmh: Base average speed
            hour: Hour of day
            day_of_week: Day of week
            
        Returns:
            Dict with ETA prediction details
        """
        base_time_hours = distance_km / base_speed_kmh
        base_time_minutes = base_time_hours * 60
        
        result = self.get_adjusted_travel_time(
            base_time_minutes,
            hour,
            day_of_week,
            "arterial"
        )
        
        now = datetime.now()
        arrival_time = now.replace(
            second=0,
            microsecond=0
        )
        arrival_minutes = int(result["adjusted_time"])
        arrival_time = arrival_time.replace(
            minute=(arrival_time.minute + arrival_minutes) % 60,
            hour=(arrival_time.hour + (arrival_time.minute + arrival_minutes) // 60) % 24
        )
        
        return {
            "distance_km": round(distance_km, 2),
            "base_time_minutes": result["base_time"],
            "predicted_time_minutes": result["adjusted_time"],
            "delay_minutes": result["delay_minutes"],
            "predicted_arrival": arrival_time.strftime("%I:%M %p"),
            "congestion_level": result["congestion_level"],
            "traffic_status": result["traffic_status"]
        }
    
    def to_dict(self) -> Dict:
        """Convert current simulation to dictionary"""
        if not self.current_simulation:
            self.simulate()
        
        sim = self.current_simulation
        
        return {
            "timestamp": sim.timestamp,
            "hour": sim.hour,
            "day_of_week": sim.day_of_week,
            "time_period": sim.time_period,
            "congestion_level": round(sim.overall_congestion, 3),
            "description": sim.description,
            "traffic_zones": [
                {
                    "zone_id": z["zone_id"],
                    "name": z["name"],
                    "level": round(z["congestion"], 3),
                    "status": "congested" if z["congestion"] > 0.6 else "normal" if z["congestion"] > 0.3 else "clear"
                }
                for z in sim.traffic_zones
            ],
            "patterns": sim.patterns
        }
