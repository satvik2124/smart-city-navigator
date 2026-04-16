"""
Smart City Navigator Backend
AI-Based Smart City Navigation System for Real-Time Traffic Prediction and Dynamic Route Optimization
"""

__version__ = "1.0.0"
__author__ = "Smart City Navigator Team"

from .main import app
from .routing import Router
from .ai_model import TrafficPredictor
from .graph_builder import GraphBuilder
from .database import Database

__all__ = ["app", "Router", "TrafficPredictor", "GraphBuilder", "Database"]
