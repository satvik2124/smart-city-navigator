import React, { useState } from 'react';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';
import DijkstraVisualizer from './components/DijkstraVisualizer';
import AStarVisualizer from './components/AStarVisualizer';

const API_BASE_URL = "http://127.0.0.1:8000";

// Real-world coordinates for a subset of nodes (lat, lon)
const NODE_COORDS = {
  Sector85: { lat: 28.648, lon: 77.212 },
  Sector71: { lat: 28.648, lon: 77.232 },
  Sector50: { lat: 28.590, lon: 77.210 },
  Sector21: { lat: 28.575, lon: 77.220 },
  Chandigarh: { lat: 30.733, lon: 76.779 },
};

// Lightweight Dijkstra sample graph for the Dijkstra Visualizer tab (Sector85/71/50/21 -> Chandigarh)
const DIJKSTRA_SAMPLE_GRAPH = {
  nodes: [
    { id: 'Sector85', x: 60, y: 60 },
    { id: 'Sector71', x: 180, y: 60 },
    { id: 'Sector50', x: 120, y: 180 },
    { id: 'Sector21', x: 240, y: 180 },
    { id: 'Chandigarh', x: 430, y: 180 },
  ],
  edges: [
    { from: 'Sector85', to: 'Sector71', w: 4 },
    { from: 'Sector85', to: 'Sector50', w: 2 },
    { from: 'Sector71', to: 'Sector50', w: 1 },
    { from: 'Sector71', to: 'Sector21', w: 7 },
    { from: 'Sector50', to: 'Sector21', w: 3 },
    { from: 'Sector21', to: 'Chandigarh', w: 9 },
    { from: 'Sector50', to: 'Chandigarh', w: 8 },
  ],
};

function App() {
  // Navigation tabs: map, dijkstra, astar
  const [tab, setTab] = useState('map');
  // Shared exploration data between Dijkstra visualizer and MapView
  const [explorationPath, setExplorationPath] = useState([]);
  const [explorationFrontier, setExplorationFrontier] = useState([]);
  const [finalPathLatLngs, setFinalPathLatLngs] = useState([]);
  const [algoPlaying, setAlgoPlaying] = useState(false);
  const [algoSpeed, setAlgoSpeed] = useState(600);

  // Coordinates mapping (lat/lon) for sector nodes
  const handleExplorationUpdate = ({ explorationPath: ep, frontierPath: fp, finalPathLatLngs: fpl } = {}) => {
    if (ep) setExplorationPath(ep);
    if (fp) setExplorationFrontier(fp);
    if (fpl) setFinalPathLatLngs(fpl);
  };

  const [routes, setRoutes] = useState([]);
  const [bestRouteId, setBestRouteId] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [sourceInput, setSourceInput] = useState("");
  const [destinationInput, setDestinationInput] = useState("");

  // 🔥 FINAL WORKING FUNCTION
  const handleSearch = async () => {

    if (!sourceInput || !destinationInput) {
      alert("Enter both locations");
      return;
    }

    setLoading(true);
    setError(null);
    setRoutes([]);

    try {
      const response = await fetch(`${API_BASE_URL}/calculate-route`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source: sourceInput,
          destination: destinationInput,
          mode: "drive"
        }),
      });

      if (!response.ok) {
        throw new Error("API Error");
      }

      const data = await response.json();

      console.log("API RESPONSE:", data);

      setRoutes(data.routes || []);
      setBestRouteId(data.best_route_id ?? 0);
      setSelectedRouteId(data.best_route_id ?? 0);

    } catch (err) {
      console.error(err);
      setError("Failed to get route");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex">

      {/* LEFT PANEL */}
      <div className="w-[30%] bg-white p-5 shadow-lg">

        <h1 className="text-xl font-bold mb-4">
          Smart City Navigator
        </h1>

        <input
          type="text"
          placeholder="Start location"
          value={sourceInput}
          onChange={(e) => setSourceInput(e.target.value)}
          className="w-full p-2 border mb-3 rounded"
        />

        <input
          type="text"
          placeholder="Destination"
          value={destinationInput}
          onChange={(e) => setDestinationInput(e.target.value)}
          className="w-full p-2 border mb-3 rounded"
        />

        <button
          onClick={handleSearch}
          className="w-full bg-blue-600 text-white p-2 rounded"
        >
          {loading ? "Loading..." : "Find Best Route"}
        </button>

        {error && (
          <p className="text-red-500 mt-3">{error}</p>
        )}

        <RoutePanel
          routes={routes}
          bestRouteId={bestRouteId}
          selectedRouteId={selectedRouteId}
          onRouteSelect={setSelectedRouteId}
        />

        {/* Navigation Tabs */}
        <div style={{ marginTop: 16, padding: 8, borderTop: '1px solid #eee' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontWeight: 600 }}>Navigation</div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => setTab('map')} className={`px-3 py-2 rounded ${tab==='map'?'bg-gray-200':''}`}>Map</button>
              <button onClick={() => setTab('dijkstra')} className={`px-3 py-2 rounded ${tab==='dijkstra'?'bg-gray-200':''}`}>Dijkstra Visualizer</button>
              <button onClick={() => setTab('astar')} className={`px-3 py-2 rounded ${tab==='astar'?'bg-gray-200':''}`}>A*</button>
            </div>
          </div>
        </div>
      </div>

      {/* MAP */}
      <div className="flex-1">
        {tab === 'astar' ? (
          <AStarVisualizer />
        ) : tab === 'dijkstra' ? (
          <DijkstraVisualizer
            graph={{ nodes: [
              { id: 'Sector85' }, { id: 'Sector71' }, { id: 'Sector50' }, { id: 'Sector21' }, { id: 'Chandigarh' }
            ], edges: [] }}
            startId={'Sector85'} endId={'Chandigarh'}
            nodeCoords={NODE_COORDS}
            onExplorationUpdate={handleExplorationUpdate}
            isPlaying={algoPlaying}
            onPlayToggle={()=>setAlgoPlaying(v=>!v)}
            onReset={()=>setAlgoPlaying(false)}
            speed={algoSpeed}
            onSpeedChange={setAlgoSpeed}
          />
        ) : (
          <MapView
            routes={routes}
            bestRouteId={bestRouteId}
            explorationPath={explorationPath}
            explorationFrontier={explorationFrontier}
            finalPathLatLngs={finalPathLatLngs}
            onRouteClick={setSelectedRouteId}
          />
        )}
      </div>

    </div>
  );
}

export default App;
