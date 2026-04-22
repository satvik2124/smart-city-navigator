/**
 * MapView Component
 * Renders interactive map with multiple route polylines, markers, and animations.
 * Uses React-Leaflet for map rendering and animation.
 */

import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Custom marker icons using DivIcon for "A" and "B" labels
const createMarkerIcon = (label, color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      color: white;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 14px;
      border: 2px solid white;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    ">${label}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14]
  });
};

// Static marker icons for start (A) and end (B)
const startIcon = createMarkerIcon('A', '#22c55e'); // Green for start
const endIcon = createMarkerIcon('B', '#ef4444');   // Red for end

// Route colors by index - distinct colors for visual differentiation
const ROUTE_COLORS = [
  '#3b82f6', // Blue - index 0
  '#f97316', // Orange - index 1
  '#a855f7', // Purple - index 2
  '#ec4899', // Pink - index 3
];

// Animation configuration
const ANIMATION_INTERVAL_MS = 30;  // Update interval in milliseconds
const POINTS_PER_TICK = 5;         // Number of points to reveal per tick

/**
 * MapView Component
 * @param {Object} props - Component props
 * @param {Array} props.routes - Array of route objects with path coordinates
 * @param {number|null} props.bestRouteId - ID of the optimal route
 * @param {Function} props.onRouteClick - Callback when a route is clicked
 * @param {number|null} props.selectedRouteId - ID of currently selected route
 */
function MapView({ routes = [], bestRouteId = null, onRouteClick, selectedRouteId = null }) {
  // State for animated route progress
  const [animatedPaths, setAnimatedPaths] = useState({});
  const mapRef = useRef(null);
  const animationIntervals = useRef({});

  /**
   * Calculate bounds to fit all routes in the map view
   * Returns a Leaflet LatLngBounds object
   */
  const getRouteBounds = () => {
    if (!routes || routes.length === 0) {
      // Default to a central location if no routes
      return [[28.6139, 77.2090], [28.6320, 77.2200]]; // Delhi area
    }

    const allCoords = [];
    routes.forEach(route => {
      if (route.path && route.path.length > 0) {
        allCoords.push(...route.path);
      }
    });

    if (allCoords.length === 0) {
      return [[28.6139, 77.2090], [28.6320, 77.2200]];
    }

    // Calculate bounding box
    const lats = allCoords.map(coord => coord[0]);
    const lngs = allCoords.map(coord => coord[1]);
    
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    // Add padding to bounds
    const latPadding = (maxLat - minLat) * 0.1 || 0.01;
    const lngPadding = (maxLng - minLng) * 0.1 || 0.01;

    return [
      [minLat - latPadding, minLng - lngPadding],
      [maxLat + latPadding, maxLng + lngPadding]
    ];
  };

  /**
   * Start animation for a specific route
   * Progressively reveals coordinates over time
   */
  const startRouteAnimation = (routeId) => {
    // Clear any existing animation for this route
    if (animationIntervals.current[routeId]) {
      clearInterval(animationIntervals.current[routeId]);
    }

    const route = routes.find(r => r.id === routeId);
    if (!route || !route.path) return;

    const totalPoints = route.path.length;
    let currentProgress = 0;

    // Initialize with first point
    setAnimatedPaths(prev => ({
      ...prev,
      [routeId]: [route.path[0]]
    }));

    // Create interval to progressively add points
    animationIntervals.current[routeId] = setInterval(() => {
      currentProgress += POINTS_PER_TICK;
      
      if (currentProgress >= totalPoints) {
        // Animation complete - show full path
        setAnimatedPaths(prev => ({
          ...prev,
          [routeId]: route.path
        }));
        clearInterval(animationIntervals.current[routeId]);
      } else {
        // Show partial path
        setAnimatedPaths(prev => ({
          ...prev,
          [routeId]: route.path.slice(0, currentProgress)
        }));
      }
    }, ANIMATION_INTERVAL_MS);
  };

  /**
   * Effect to start animations when routes change
   */
  useEffect(() => {
    // Start animations for all routes
    routes.forEach(route => {
      startRouteAnimation(route.id);
    });

    // Cleanup intervals on unmount
    return () => {
      Object.values(animationIntervals.current).forEach(interval => {
        clearInterval(interval);
      });
    };
  }, [routes]);

  /**
   * Effect to fit map bounds when routes change
   */
  useEffect(() => {
    if (mapRef.current && routes.length > 0) {
      const bounds = getRouteBounds();
      mapRef.current.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [routes]);

  /**
   * Get polyline styling based on route properties
   * @param {number} index - Route index in the routes array
   * @param {number} routeId - Route ID
   * @returns {Object} Styling object for the polyline
   */
  const getPolylineStyle = (index, routeId) => {
    const isBest = routeId === bestRouteId;
    const isSelected = routeId === selectedRouteId;

    if (isBest) {
      return {
        weight: 6,
        opacity: 1.0,
        color: '#22c55e', // Green for best route
        smoothFactor: 1,
        noClip: false
      };
    }

    return {
      weight: 3,
      opacity: 0.6,
      color: ROUTE_COLORS[index % ROUTE_COLORS.length],
      dashArray: "8,4", // Dashed line for non-best routes
      smoothFactor: 1,
      noClip: false
    };
  };

  /**
   * Handle route click event
   */
  const handleRouteClick = (routeId) => {
    if (onRouteClick) {
      onRouteClick(routeId);
    }
  };

  // Get start and end coordinates from the best route (first route as fallback)
  const primaryRoute = routes.find(r => r.id === bestRouteId) || routes[0];
  const startCoords = primaryRoute?.path?.[0] || [28.6139, 77.2090];
  const endCoords = primaryRoute?.path?.[primaryRoute.path.length - 1] || [28.6320, 77.2200];

  return (
    <div className="w-full h-full relative">
      <MapContainer
        center={[28.6139, 77.2090]} // Default center (Delhi)
        zoom={12}
        className="w-full h-full"
        ref={mapRef}
        scrollWheelZoom={true}
      >
        {/* OpenStreetMap tile layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Render glow effect for best route (underneath the main line) */}
        {bestRouteId && animatedPaths[bestRouteId] && animatedPaths[bestRouteId].length > 1 && (
          <Polyline
            positions={animatedPaths[bestRouteId]}
            pathOptions={{
              weight: 12,
              opacity: 0.2,
              color: '#22c55e',
              smoothFactor: 1
            }}
          />
        )}

        {/* Render all route polylines */}
        {routes.map((route, index) => {
          const animatedPath = animatedPaths[route.id] || [];
          
          // Skip if path is not available
          if (animatedPath.length < 2) return null;

          return (
            <Polyline
              key={`route-${route.id}`}
              positions={animatedPath}
              pathOptions={getPolylineStyle(index, route.id)}
              eventHandlers={{
                click: () => handleRouteClick(route.id)
              }}
            />
          );
        })}

        {/* Start marker (A) */}
        {startCoords && (
          <Marker position={startCoords} icon={startIcon} />
        )}

        {/* End marker (B) */}
        {endCoords && (
          <Marker position={endCoords} icon={endIcon} />
        )}
      </MapContainer>

      {/* Map legend */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-[1000]">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Route Legend</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-green-500 rounded"></div>
            <span className="text-xs text-gray-600">Best Route</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-blue-500 rounded" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-xs text-gray-600">Alternative</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapView;
