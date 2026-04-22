 import React from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Renders up to three routes simultaneously: fastest (blue), medium (yellow), congested (red)
function MapView({ routes = [], bestRouteId = null, explorationPath = null }) {
  // Node exploration animation on the Leaflet map (optional)
  const [exploredIndex, setExploredIndex] = React.useState(-1);
  React.useEffect(() => {
    if (!explorationPath || explorationPath.length === 0) {
      setExploredIndex(-1);
      return;
    }
    let i = -1;
    setExploredIndex(-1);
    const timer = setInterval(() => {
      i += 1;
      setExploredIndex(i);
      if (i >= explorationPath.length - 1) {
        clearInterval(timer);
      }
    }, 600);
    return () => clearInterval(timer);
  }, [explorationPath]);

  // Helper: extract [lat, lon] path from geometry.coordinates (assuming [lon, lat] input)
  const extractPath = (geometry) => {
    if (!geometry?.coordinates) return [];
    return geometry.coordinates
      .filter((c) => Array.isArray(c) && c.length >= 2)
      .map((c) => [c[1], c[0]]);
  };

  // Heuristic selectors: fastest (min time), medium (middle by time), congested (max traffic_level or time)
  const center = [28.6139, 77.2090];

  const timeOf = (r) => (typeof r.time === 'number' ? r.time : Number.POSITIVE_INFINITY);
  const trafficRank = (r) => {
    // rank by traffic_level if present: high > medium > low
    const t = r.traffic_level;
    if (t === 'high') return 3;
    if (t === 'medium') return 2;
    if (t === 'low') return 1;
    return 0;
  };

  // Sort by time to determine fastest and median
  const sortedByTime = [...routes].sort((a, b) => timeOf(a) - timeOf(b));
  const fastestRoute = sortedByTime[0] ?? null;
  const mediumRoute = sortedByTime.length >= 3
    ? sortedByTime[Math.floor((sortedByTime.length - 1) / 2)]
    : sortedByTime[1] ?? null;

  // Congested: highest traffic level; fallback to highest time if necessary
  const congestedRoute = [...routes]
    .sort((a, b) => {
      const ra = trafficRank(b) - trafficRank(a); // descending by traffic rank
      if (ra !== 0) return ra;
      // tie-breaker: higher time
      return timeOf(b) - timeOf(a);
    })[0] ?? null;

  // Normalize: ensure we only render up to three routes
  const toRender = [
    { route: fastestRoute, color: 'blue' },
    { route: mediumRoute, color: 'yellow' },
    { route: congestedRoute, color: 'red' },
  ].filter((r) => r.route && (r.route.geometry?.coordinates?.length ?? 0) > 0);

  // If a route is missing, fall back to existing rendering (older behavior) if any
  const showLegacy = routes.length > 0 && toRender.length === 0;

  // If requested, also respect an external bestRouteId for emphasis (override to fastest if available)
  const emphasizedId = fastestRoute?.id ?? bestRouteId ?? null;

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {toRender.map(({ route, color }) => {
          const path = extractPath(route.geometry);
          if (path.length < 2) return null;
          return (
            <Polyline
              key={route.id}
              positions={path}
              pathOptions={{
                color: color,
                weight: route.id === emphasizedId ? 6 : 4,
              }}
            />
          );
        })}

        {showLegacy && routes.map((route) => {
          const path = extractPath(route.geometry);
          if (path.length < 2) return null;
          // Fallback: render in gray if legacy data exists but not matched by the new three-route logic
          return (
            <Polyline
              key={route.id}
              positions={path}
              pathOptions={{ color: 'gray', weight: 2 }}
            />
          );
        })}
        {/* Animated exploration markers (optional) */}
        {explorationPath && explorationPath.length > 0 && explorationPath.slice(0, exploredIndex + 1).map((p, idx) => {
          const lat = p.lat ?? p[0] ?? null;
          const lon = p.lon ?? p[1] ?? null;
          if (typeof lat === 'number' && typeof lon === 'number') {
            return (
              <CircleMarker 
                key={`expl-${idx}`} 
                center={[lat, lon]} 
                pathOptions={{ color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.5 }} 
                radius={6} 
              />
            );
          }
          return null;
        })}
      </MapContainer>
    </div>
  );
}

export default MapView;
