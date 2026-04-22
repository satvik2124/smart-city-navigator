"""
Graph Builder Module - Creates city graph from map data
Smart City Navigator - AI-Based Smart City Navigation System

Builds a weighted graph representation of the city road network
using NetworkX-style data structures.
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GraphNode:
    """Represents a node (intersection) in the city graph"""
    id: str
    lat: float
    lon: float
    name: Optional[str] = None
    node_type: str = "intersection"
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, GraphNode) and self.id == other.id


@dataclass
class GraphEdge:
    """Represents an edge (road segment) in the city graph"""
    source: str
    target: str
    distance: float
    road_type: str = "local"
    name: Optional[str] = None
    max_speed: int = 60
    lanes: int = 2
    traffic_level: float = 0.0
    bidirectional: bool = True
    
    @property
    def travel_time(self) -> float:
        """Calculate travel time in minutes"""
        base_speed = self.max_speed if self.max_speed else 60
        congestion = 1 + (self.traffic_level * 1.5)
        return (self.distance / base_speed) * 60
    
    @property
    def weight(self) -> float:
        """Edge weight for routing algorithms"""
        return self.distance * (1 + self.traffic_level)


class GraphBuilder:
    """
    Builds and manages the city road network graph.
    
    Features:
    - Creates graph from coordinates or loads from data
    - Simulates city road network
    - Provides neighbor queries for routing
    - Manages edge weights based on traffic
    """
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Tuple[str, str, Dict]] = []
        self._adjacency: Dict[str, List[Tuple[str, Dict]]] = {}
        self._edges_dict: Dict[Tuple[str, str], Dict] = {}
        
        self._build_city_graph()
    
    def _build_city_graph(self):
        """Build the city road network graph"""
        print("Building city road network graph...")
        
        self._create_sample_city()
        
        print(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
    
    def _create_sample_city(self):
        """Create a sample city graph for demonstration"""
        
        city_center_lat = 28.6139
        city_center_lon = 77.2090
        
        landmarks = [
            ("N0", "City Center", city_center_lat, city_center_lon),
            ("N1", "North Station", city_center_lat + 0.02, city_center_lon),
            ("N2", "East Market", city_center_lat, city_center_lon + 0.02),
            ("N3", "South Plaza", city_center_lat - 0.02, city_center_lon),
            ("N4", "West Terminal", city_center_lat, city_center_lon - 0.02),
            ("N5", "Tech Park", city_center_lat + 0.015, city_center_lon + 0.015),
            ("N6", "University", city_center_lat - 0.015, city_center_lon + 0.015),
            ("N7", "Airport", city_center_lat + 0.04, city_center_lon),
            ("N8", "Train Station", city_center_lat - 0.015, city_center_lon - 0.015),
            ("N9", "Shopping Mall", city_center_lat + 0.01, city_center_lon - 0.01),
            ("N10", "Business District", city_center_lat - 0.01, city_center_lon - 0.01),
            ("N11", "Sector 21", city_center_lat + 0.025, city_center_lon - 0.01),
            ("N12", "Sector 25", city_center_lat - 0.02, city_center_lon + 0.025),
            ("N13", "Sector 15", city_center_lat - 0.035, city_center_lon - 0.01),
            ("N14", "Hospital", city_center_lat + 0.005, city_center_lon + 0.025),
            ("N15", "Sector 62", city_center_lat + 0.02, city_center_lon + 0.025),
            ("N16", "Connaught Place", city_center_lat + 0.018, city_center_lon + 0.008),
            ("N17", "Rajiv Chowk", city_center_lat + 0.018, city_center_lon + 0.009),
            ("N18", "Nehru Place", city_center_lat - 0.05, city_center_lon + 0.04),
            ("N19", "Saket", city_center_lat - 0.07, city_center_lon + 0.0),
            ("N20", "Dwarka", city_center_lat - 0.04, city_center_lon - 0.12),
            ("N21", "Lajpat Nagar", city_center_lat - 0.04, city_center_lon + 0.035),
            ("N22", "Karol Bagh", city_center_lat + 0.02, city_center_lon - 0.02),
            ("N23", "Chandni Chowk", city_center_lat + 0.04, city_center_lon + 0.02),
            ("N24", "M.G. Road", city_center_lat + 0.015, city_center_lon + 0.005),
            ("N25", "Aerocity", city_center_lat - 0.06, city_center_lon - 0.12),
            ("N26", "Huda City Centre", city_center_lat - 0.15, city_center_lon - 0.14),
            ("N27", "Cyber Hub", city_center_lat - 0.14, city_center_lon - 0.14),
            ("N28", "Botanical Garden", city_center_lat - 0.04, city_center_lon + 0.12),
            ("N29", "Noida Metro", city_center_lat + 0.004, city_center_lon + 0.0),
            ("N30", "IFFCO Chowk", city_center_lat - 0.15, city_center_lon - 0.18),
        ]
        
        for node_id, name, lat, lon in landmarks:
            self.add_node(node_id, lat, lon, name)
        
        roads = [
            # Core city connections
            ("N0", "N1", 2.5, "arterial", "Ring Road"),
            ("N0", "N2", 2.0, "arterial", "Mathura Road"),
            ("N0", "N3", 2.3, "arterial", "Ring Road"),
            ("N0", "N4", 2.1, "arterial", "Ring Road"),
            ("N0", "N29", 0.5, "arterial", "Atta Market Road"),
            ("N0", "N16", 1.8, "arterial", "Barakhamba Road"),
            ("N0", "N17", 1.9, "arterial", "Barakhamba Road"),
            # North connections
            ("N1", "N5", 1.8, "arterial", "DND Flyover"),
            ("N1", "N11", 2.5, "highway", "NH-24"),
            ("N1", "N15", 2.0, "arterial", "Sector Road"),
            # East connections
            ("N2", "N5", 1.5, "arterial", "Vikas Marg"),
            ("N2", "N14", 2.2, "arterial", "Loknayak Marg"),
            ("N2", "N18", 3.5, "highway", " Nehru Place Road"),
            ("N2", "N28", 4.0, "arterial", "Botanical Garden Road"),
            # South connections
            ("N3", "N6", 2.0, "arterial", "Maharaja Ranjit Singh Marg"),
            ("N3", "N8", 1.6, "local", " Sardar Patel Road"),
            ("N3", "N19", 5.0, "highway", "MG Road Connector"),
            ("N3", "N21", 3.5, "arterial", "Amar Ujjala Chowk"),
            # West connections
            ("N4", "N9", 1.4, "arterial", " Pusa Road"),
            ("N4", "N10", 1.7, "arterial", " Linking Road"),
            ("N4", "N22", 2.0, "arterial", " Ajmeri Gate Road"),
            ("N4", "N24", 1.5, "local", " Baba Kharak Singh Marg"),
            # Special zones
            ("N5", "N14", 1.3, "arterial", "Max Hospital Road"),
            ("N6", "N21", 2.5, "arterial", " South Campus Road"),
            ("N6", "N19", 3.0, "arterial", "Mandi House Road"),
            # Outer areas
            ("N7", "N25", 2.0, "highway", "NH-8"),
            ("N7", "N1", 4.5, "highway", "Airport Road"),
            ("N10", "N20", 5.0, "highway", "Dwarka Expressway"),
            ("N11", "N15", 1.0, "local", "Sector Internal Road"),
            ("N12", "N28", 2.0, "arterial", "Botanical Garden Link"),
            ("N16", "N17", 0.3, "local", "Connaught Place Inner Circle"),
            ("N16", "N23", 2.5, "arterial", "Netaji Subhash Marg"),
            ("N18", "N21", 1.5, "local", "Nehru Place Road"),
            ("N19", "N18", 2.0, "arterial", "M仿e Road"),
            ("N20", "N25", 3.0, "highway", "NH-48"),
            ("N21", "N18", 1.5, "local", "Garhi Cul De Sac"),
            ("N22", "N23", 1.8, "arterial", " Dayanand Road"),
            ("N25", "N26", 3.5, "highway", "MG Road"),
            ("N26", "N27", 0.8, "local", "Ambience Mall Road"),
            ("N26", "N30", 1.5, "arterial", "Sohna Road"),
            ("N28", "N29", 2.5, "arterial", "Noida Expressway"),
            ("N30", "N27", 2.0, "local", "Golf Course Road"),
        ]
        
        for source, target, distance, road_type, name in roads:
            self.add_edge(source, target, distance, road_type, name)
        
        self._add_secondary_nodes()
    
    def _add_secondary_nodes(self):
        """Add secondary nodes to make the graph denser"""
        
        main_nodes = list(self.nodes.keys())
        
        for i in range(15):
            node_id = f"S{i}"
            base_node = random.choice(main_nodes)
            base_data = self.nodes[base_node]
            
            lat_offset = random.uniform(-0.008, 0.008)
            lon_offset = random.uniform(-0.008, 0.008)
            
            new_lat = base_data["lat"] + lat_offset
            new_lon = base_data["lon"] + lon_offset
            
            self.add_node(
                node_id,
                new_lat,
                new_lon,
                f"Secondary Point {i+1}"
            )
            
            target = random.choice(main_nodes)
            distance = self._calculate_distance(
                new_lat, new_lon,
                self.nodes[target]["lat"],
                self.nodes[target]["lon"]
            )
            
            self.add_edge(
                node_id,
                target,
                distance,
                random.choice(["local", "arterial"]),
                f"Connector {i}"
            )
    
    def add_node(self, node_id: str, lat: float, lon: float, name: Optional[str] = None):
        """Add a node to the graph"""
        self.nodes[node_id] = {
            "id": node_id,
            "lat": lat,
            "lon": lon,
            "name": name or f"Node {node_id}"
        }
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
    
    def add_edge(
        self,
        source: str,
        target: str,
        distance: float,
        road_type: str = "local",
        name: Optional[str] = None
    ):
        """Add an edge to the graph"""
        if source not in self.nodes or target not in self.nodes:
            return
        
        max_speed_map = {
            "highway": 100,
            "arterial": 60,
            "local": 40
        }
        
        edge_data = {
            "source": source,
            "target": target,
            "distance": distance,
            "road_type": road_type,
            "name": name,
            "max_speed": max_speed_map.get(road_type, 60),
            "lanes": 2 if road_type == "local" else (4 if road_type == "highway" else 3),
            "traffic_level": 0.3,
            "bidirectional": True
        }
        
        self.edges.append((source, target, edge_data.copy()))
        
        if edge_data.get("bidirectional", True):
            reverse_data = edge_data.copy()
            reverse_data["source"] = target
            reverse_data["target"] = source
            self.edges.append((target, source, reverse_data))
        
        edge_key = tuple(sorted([source, target]))
        self._edges_dict[edge_key] = edge_data
        
        self._adjacency[source].append((target, edge_data))
        if edge_data.get("bidirectional", True):
            self._adjacency[target].append((source, edge_data))
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def find_nearest_node(self, coordinates: Tuple[float, float]) -> str:
        """Find the nearest node to given coordinates"""
        lat, lon = coordinates
        
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, node_data in self.nodes.items():
            distance = self._calculate_distance(
                lat, lon,
                node_data["lat"],
                node_data["lon"]
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node or list(self.nodes.keys())[0]
    
    def get_neighbors(self, node_id: str) -> List[Tuple[str, Dict]]:
        """Get all neighbors of a node"""
        return self._adjacency.get(node_id, [])
    
    def get_edge_data(self, edge_key: Tuple[str, str]) -> Optional[Dict]:
        """Get edge data for a given edge key"""
        normalized_key = tuple(sorted(edge_key))
        return self._edges_dict.get(normalized_key)
    
    def get_edges_dict(self) -> Dict[Tuple[str, str], Dict]:
        """Get all edges as dictionary"""
        return self._edges_dict.copy()
    
    def get_bounds(self) -> Dict:
        """Get geographical bounds of the graph"""
        if not self.nodes:
            return {}
        
        lats = [n["lat"] for n in self.nodes.values()]
        lons = [n["lon"] for n in self.nodes.values()]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
            "center_lat": sum(lats) / len(lats),
            "center_lon": sum(lons) / len(lons)
        }
    
    def update_traffic(self, source: str, target: str, traffic_level: float):
        """Update traffic level for an edge"""
        edge_key = tuple(sorted([source, target]))
        
        if edge_key in self._edges_dict:
            self._edges_dict[edge_key]["traffic_level"] = traffic_level
        
        for i, (s, t, data) in enumerate(self.edges):
            if tuple(sorted([s, t])) == edge_key:
                self.edges[i] = (s, t, {**data, "traffic_level": traffic_level})
        
        if source in self._adjacency:
            for i, (neighbor, data) in enumerate(self._adjacency[source]):
                if neighbor == target:
                    self._adjacency[source][i] = (neighbor, {**data, "traffic_level": traffic_level})
        
        if target in self._adjacency:
            for i, (neighbor, data) in enumerate(self._adjacency[target]):
                if neighbor == source:
                    self._adjacency[target][i] = (neighbor, {**data, "traffic_level": traffic_level})
    
    def get_path_distance(self, path: List[str]) -> float:
        """Calculate total distance of a path"""
        total_distance = 0.0
        
        for i in range(len(path) - 1):
            edge_data = self.get_edge_data((path[i], path[i + 1]))
            if edge_data:
                total_distance += edge_data["distance"]
        
        return total_distance
    
    def get_path_travel_time(self, path: List[str]) -> float:
        """Calculate total travel time of a path"""
        total_time = 0.0
        
        for i in range(len(path) - 1):
            edge_data = self.get_edge_data((path[i], path[i + 1]))
            if edge_data:
                total_time += edge_data.get("travel_time", edge_data["distance"] / 60 * 60)
        
        return total_time
    
    def visualize_graph(self) -> Dict:
        """Get graph visualization data"""
        return {
            "nodes": [
                {
                    "id": node_id,
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "name": data.get("name", f"Node {node_id}"),
                    "connections": len(self._adjacency.get(node_id, []))
                }
                for node_id, data in self.nodes.items()
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "distance": data["distance"],
                    "road_type": data["road_type"],
                    "traffic_level": data.get("traffic_level", 0)
                }
                for source, target, data in self.edges[::2]
            ],
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges) // 2,
                "avg_connections": sum(len(n) for n in self._adjacency.values()) / len(self._adjacency) if self._adjacency else 0
            }
        }
    
    def export_to_dict(self) -> Dict:
        """Export graph to dictionary format"""
        return {
            "nodes": self.nodes,
            "edges": [
                {
                    "source": source,
                    "target": target,
                    **data
                }
                for source, target, data in self.edges
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "node_count": len(self.nodes),
                "edge_count": len(self.edges) // 2
            }
        }
