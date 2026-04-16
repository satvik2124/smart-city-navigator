"""
Routing Module - Implements Dijkstra and A* algorithms for pathfinding
Smart City Navigator - AI-Based Smart City Navigation System
"""

import heapq
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime

try:
    from .graph_builder import GraphBuilder
    from .ai_model import TrafficPredictor
except ImportError:
    from graph_builder import GraphBuilder
    from ai_model import TrafficPredictor


@dataclass
class Node:
    """Represents a node in the routing graph"""
    id: str
    lat: float
    lon: float
    name: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


@dataclass
class Edge:
    """Represents an edge (road) between two nodes"""
    source: str
    target: str
    distance: float
    road_type: str = "local"
    traffic_level: float = 0.0
    
    @property
    def travel_time(self) -> float:
        """Calculate travel time based on distance and traffic"""
        base_speed = {
            "highway": 100,
            "arterial": 60,
            "local": 40
        }
        speed = base_speed.get(self.road_type, 40)
        congestion_multiplier = 1 + (self.traffic_level * 1.5)
        return (self.distance / speed) * 60


class PriorityQueue:
    """Min-heap priority queue implementation"""
    
    def __init__(self):
        self.heap: List[Tuple[float, str]] = []
        self.entries: Dict[str, float] = {}
        self.removed: Set[str] = set()
    
    def add(self, priority: float, item: str):
        if item in self.entries:
            if priority < self.entries[item]:
                self._remove(item)
        else:
            self.entries[item] = priority
            heapq.heappush(self.heap, (priority, item))
    
    def pop(self) -> Optional[str]:
        while self.heap:
            priority, item = heapq.heappop(self.heap)
            if item not in self.removed:
                del self.entries[item]
                return item
        return None
    
    def _remove(self, item: str):
        self.removed.add(item)
    
    def __len__(self) -> int:
        return len(self.entries)
    
    def __contains__(self, item: str) -> bool:
        return item in self.entries and item not in self.removed


class Router:
    """
    Router class implementing Dijkstra and A* algorithms
    for optimal pathfinding in the city navigation system.
    """
    
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.traffic_predictor = TrafficPredictor()
        self._traffic_cache: Dict[str, float] = {}
        self._last_traffic_update: Optional[datetime] = None
    
    def _update_traffic(self, hour: int, day_of_week: int):
        """Update traffic conditions with dynamic simulation"""
        current_time = datetime.now()
        
        if self._last_traffic_update is None or \
           (current_time - self._last_traffic_update).seconds > 60:
            
            for edge_key, edge_data in self.graph_builder.get_edges_dict().items():
                traffic = self._simulate_traffic(hour, day_of_week, edge_data["road_type"])
                self._traffic_cache[edge_key] = traffic
                edge_data["traffic_level"] = traffic
            
            self._last_traffic_update = current_time
    
    def _simulate_traffic(self, hour: int, day_of_week: int, road_type: str) -> float:
        """
        Simulate traffic based on time of day, day of week, and road type.
        Traffic changes each time due to stochastic variation.
        """
        base_traffic = 0.2
        
        if 7 <= hour <= 9:
            base_traffic = 0.7
        elif 12 <= hour <= 14:
            base_traffic = 0.5
        elif 17 <= hour <= 19:
            base_traffic = 0.8
        elif 22 <= hour or hour <= 5:
            base_traffic = 0.1
        
        road_factor = {
            "highway": 1.3,
            "arterial": 1.1,
            "local": 0.9
        }
        
        day_factor = 1.0
        if day_of_week >= 5:
            day_factor = 0.7
        
        random_factor = random.uniform(0.8, 1.2)
        
        traffic = base_traffic * road_factor.get(road_type, 1.0) * day_factor * random_factor
        return min(1.0, max(0.0, traffic))
    
    def get_traffic_simulation(self) -> Dict:
        """Get current traffic simulation data"""
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        self._update_traffic(hour, day_of_week)
        
        avg_traffic = sum(self._traffic_cache.values()) / len(self._traffic_cache) if self._traffic_cache else 0.5
        
        traffic_zones = []
        for edge_key, traffic in self._traffic_cache.items():
            source, target = edge_key
            traffic_zones.append({
                "edge": edge_key,
                "level": traffic,
                "status": "congested" if traffic > 0.7 else "normal" if traffic > 0.3 else "clear"
            })
        
        return {
            "congestion_level": avg_traffic,
            "zones": traffic_zones[:10],
            "hour": hour,
            "day_of_week": day_of_week,
            "traffic_pattern": self._get_traffic_pattern(hour)
        }
    
    def _get_traffic_pattern(self, hour: int) -> str:
        """Get human-readable traffic pattern description"""
        if 7 <= hour <= 9:
            return "Morning Rush Hour"
        elif 12 <= hour <= 14:
            return "Lunch Time Traffic"
        elif 17 <= hour <= 19:
            return "Evening Rush Hour"
        elif 22 <= hour or hour <= 5:
            return "Night Time - Light Traffic"
        elif 10 <= hour <= 11:
            return "Late Morning - Moderate"
        elif 15 <= hour <= 16:
            return "Afternoon - Building Up"
        else:
            return "Normal Traffic"
    
    def calculate_route(
        self,
        source: Tuple[float, float],
        destination: Tuple[float, float],
        algorithm: str = "dijkstra",
        current_hour: int = None,
        day_of_week: int = None,
        avoid_traffic: bool = False
    ) -> Dict:
        """
        Calculate optimal route using specified algorithm.
        
        Args:
            source: (latitude, longitude) tuple
            destination: (latitude, longitude) tuple
            algorithm: "dijkstra" or "astar"
            current_hour: Current hour for traffic simulation
            day_of_week: Day of week for traffic simulation
            avoid_traffic: Whether to avoid high traffic routes
        
        Returns:
            Dictionary with route information including path, distance, duration
        """
        if current_hour is None:
            current_hour = datetime.now().hour
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        
        self._update_traffic(current_hour, day_of_week)
        
        source_node = self.graph_builder.find_nearest_node(source)
        dest_node = self.graph_builder.find_nearest_node(destination)
        
        if algorithm.lower() == "astar":
            path, nodes_explored = self._astar_search(
                source_node, dest_node, avoid_traffic
            )
        else:
            path, nodes_explored = self._dijkstra_search(
                source_node, dest_node, avoid_traffic
            )
        
        total_distance = 0.0
        total_duration = 0.0
        traffic_score = 0.0
        
        path_coordinates = []
        for node_id in path:
            node_data = self.graph_builder.nodes[node_id]
            path_coordinates.append({
                "lat": node_data["lat"],
                "lon": node_data["lon"],
                "node_id": node_id
            })
        
        for i in range(len(path) - 1):
            edge_key = tuple(sorted([path[i], path[i + 1]]))
            edge_data = self.graph_builder.get_edge_data(edge_key)
            
            if edge_data:
                total_distance += edge_data["distance"]
                total_duration += edge_data.get("travel_time", total_distance / 60 * 60)
                traffic_score += edge_data.get("traffic_level", 0.5)
        
        if len(path) > 1:
            traffic_score /= (len(path) - 1)
        
        predicted_duration = self.traffic_predictor.predict(
            hour=current_hour,
            day_of_week=day_of_week,
            road_type="arterial",
            distance=total_distance,
            is_peak_hour=current_hour in [8, 9, 17, 18, 19]
        )
        
        final_duration = predicted_duration["travel_time"] * (total_distance / max(total_distance, 1))
        
        return {
            "path": path_coordinates,
            "distance": round(total_distance, 2),
            "duration": round(final_duration, 2),
            "traffic_score": round(traffic_score, 3),
            "nodes_explored": nodes_explored,
            "algorithm": algorithm,
            "source_node": source_node,
            "destination_node": dest_node
        }
    
    def _dijkstra_search(
        self,
        start: str,
        goal: str,
        avoid_traffic: bool = False
    ) -> Tuple[List[str], int]:
        """
        Dijkstra's algorithm implementation.
        Explores all possible paths to find the shortest path.
        """
        distances: Dict[str, float] = {start: 0}
        previous: Dict[str, Optional[str]] = {start: None}
        visited: Set[str] = set()
        nodes_explored = 0
        
        pq = PriorityQueue()
        pq.add(0, start)
        
        while len(pq) > 0:
            current = pq.pop()
            
            if current is None:
                break
            
            if current in visited:
                continue
            
            visited.add(current)
            nodes_explored += 1
            
            if current == goal:
                break
            
            neighbors = self.graph_builder.get_neighbors(current)
            
            for neighbor, edge_data in neighbors:
                if neighbor in visited:
                    continue
                
                edge_weight = edge_data["distance"]
                
                if avoid_traffic:
                    traffic_penalty = edge_data.get("traffic_level", 0) * 5
                    edge_weight += traffic_penalty
                
                new_dist = distances[current] + edge_weight
                
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    pq.add(new_dist, neighbor)
        
        path = self._reconstruct_path(previous, goal)
        return path, nodes_explored
    
    def _astar_search(
        self,
        start: str,
        goal: str,
        avoid_traffic: bool = False
    ) -> Tuple[List[str], int]:
        """
        A* algorithm implementation.
        Uses heuristic to guide search toward goal, making it more efficient.
        """
        def heuristic(node_id: str) -> float:
            """Euclidean distance heuristic"""
            node_data = self.graph_builder.nodes[node_id]
            goal_data = self.graph_builder.nodes[goal]
            
            lat1, lon1 = node_data["lat"], node_data["lon"]
            lat2, lon2 = goal_data["lat"], goal_data["lon"]
            
            return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111
        
        g_scores: Dict[str, float] = {start: 0}
        f_scores: Dict[str, float] = {start: heuristic(start)}
        previous: Dict[str, Optional[str]] = {start: None}
        visited: Set[str] = set()
        nodes_explored = 0
        
        pq = PriorityQueue()
        pq.add(f_scores[start], start)
        
        while len(pq) > 0:
            current = pq.pop()
            
            if current is None:
                break
            
            if current in visited:
                continue
            
            visited.add(current)
            nodes_explored += 1
            
            if current == goal:
                break
            
            neighbors = self.graph_builder.get_neighbors(current)
            
            for neighbor, edge_data in neighbors:
                if neighbor in visited:
                    continue
                
                tentative_g = g_scores[current] + edge_data["distance"]
                
                if avoid_traffic:
                    traffic_penalty = edge_data.get("traffic_level", 0) * 5
                    tentative_g += traffic_penalty
                
                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    f_scores[neighbor] = tentative_g + heuristic(neighbor)
                    previous[neighbor] = current
                    pq.add(f_scores[neighbor], neighbor)
        
        path = self._reconstruct_path(previous, goal)
        return path, nodes_explored
    
    def _reconstruct_path(
        self,
        previous: Dict[str, Optional[str]],
        goal: str
    ) -> List[str]:
        """Reconstruct path from previous node dictionary"""
        path = []
        current: Optional[str] = goal
        
        while current is not None:
            path.append(current)
            current = previous.get(current)
        
        path.reverse()
        return path
    
    def get_alternative_routes(
        self,
        source: Tuple[float, float],
        destination: Tuple[float, float],
        num_alternatives: int = 3
    ) -> List[Dict]:
        """Get multiple alternative routes"""
        routes = []
        
        for i in range(num_alternatives):
            avoid_traffic = i % 2 == 1
            algorithm = "astar" if i % 2 == 0 else "dijkstra"
            
            route = self.calculate_route(
                source=source,
                destination=destination,
                algorithm=algorithm,
                avoid_traffic=avoid_traffic
            )
            
            if route["path"]:
                routes.append({
                    **route,
                    "route_id": i + 1,
                    "description": self._get_route_description(route, i)
                })
        
        routes.sort(key=lambda x: x["duration"])
        return routes
    
    def _get_route_description(self, route: Dict, index: int) -> str:
        """Generate human-readable route description"""
        descriptions = [
            "Fastest Route",
            "Shortest Distance",
            "Avoid Traffic"
        ]
        return descriptions[index] if index < len(descriptions) else f"Alternative Route {index + 1}"
