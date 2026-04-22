import React, { useEffect, useMemo, useState, useRef } from 'react';

// Dijkstra Visualizer: interactive visualization of Dijkstra algorithm
// Graph: intersections (nodes) and roads (weighted edges)
// Features: Play, Pause, Next, Reset, Speed, current node, visited, PQ, dist table, final path

// Sample graph (Sector85, Sector71, Sector50, Sector21, Sector17, Chandigarh)
const DEFAULT_GRAPH = {
  nodes: [
    { id: 'Sector85', x: 60, y: 60 },
    { id: 'Sector71', x: 180, y: 60 },
    { id: 'Sector50', x: 120, y: 180 },
    { id: 'Sector21', x: 240, y: 180 },
    { id: 'Sector17', x: 330, y: 130 },
    { id: 'Chandigarh', x: 430, y: 180 },
  ],
  edges: [
    { from: 'Sector85', to: 'Sector71', w: 4 },
    { from: 'Sector85', to: 'Sector50', w: 2 },
    { from: 'Sector71', to: 'Sector50', w: 1 },
    { from: 'Sector71', to: 'Sector21', w: 7 },
    { from: 'Sector50', to: 'Sector21', w: 3 },
    { from: 'Sector21', to: 'Sector17', w: 2 },
    { from: 'Sector17', to: 'Chandigarh', w: 6 },
    { from: 'Sector21', to: 'Chandigarh', w: 9 },
    { from: 'Sector50', to: 'Chandigarh', w: 8 },
  ],
};

function buildAdjacency(graph){
  const adj = {};
  graph.nodes.forEach(n => adj[n.id] = []);
  graph.edges.forEach(e => {
    adj[e.from].push({ to: e.to, w: e.w });
    adj[e.to].push({ to: e.from, w: e.w }); // undirected
  });
  return adj;
}

function reconstructPath(end, start, prev){
  const path = [];
  let at = end;
  while (at && at !== start) {
    path.unshift(at);
    at = prev[at];
  }
  if (start) path.unshift(start);
  return path;
}

function runDijkstra(graph, startId = 'Sector85', endId = 'Chandigarh'){
  const adj = buildAdjacency(graph);
  const dist = {};
  const prev = {};
  const visited = new Set();
  const pq = [];
  graph.nodes.forEach(n => dist[n.id] = Number.POSITIVE_INFINITY);
  dist[startId] = 0;
  pq.push({ node: startId, dist: 0 });
  const steps = [];
  let endReached = false;

  const popMin = () => {
    pq.sort((a,b)=> a.dist - b.dist);
    return pq.shift();
  };

  while(pq.length > 0){
    const { node: u } = popMin();
    if (!u) break;
    if (visited.has(u)) continue;
    visited.add(u);
    steps.push({ current: u, dist: { ...dist }, visited: new Set(visited), pq: pq.map(p => ({ node: p.node, dist: p.dist })), prev: { ...prev } });
    if (u === endId){ endReached = true; break; }
    const neighbors = adj[u] || [];
    for (const nb of neighbors){
      const v = nb.to;
      if (visited.has(v)) continue;
      const alt = (dist[u] ?? Number.POSITIVE_INFINITY) + nb.w;
      if (alt < (dist[v] ?? Number.POSITIVE_INFINITY)){
        dist[v] = alt;
        prev[v] = u;
        pq.push({ node: v, dist: alt});
      }
    }
  }

  const finalPath = endReached ? reconstructPath(endId, startId, prev) : reconstructPath(endId, startId, prev);
  const runtimeMs = 0; // approximate runtime displayed via timer in UI if needed
  const explored = visited.size;
  return { steps, dist, prev, finalPath, runtimeMs, explored };
}

export default function DijkstraVisualizer({ graph = DEFAULT_GRAPH, startId = 'Sector85', endId = 'Chandigarh', nodeCoords = {}, onExplorationUpdate, isPlaying, onPlayToggle, speed, onSpeedChange }) {
  // Controlled playback (from parent) if provided
  const [localPlaying, setLocalPlaying] = useState(false);
  const playing = typeof isPlaying === 'boolean' ? isPlaying : localPlaying;
  const [stepIndex, setStepIndex] = useState(0);
  const [speedMs, setSpeedMs] = useState(600);
  const [internal, setInternal] = useState(() => runDijkstra(graph, startId, endId));
  const timerRef = useRef(null);

  // Recompute on graph/start/end change
  useEffect(() => {
    const res = runDijkstra(graph, startId, endId);
    setInternal(res);
    setStepIndex(0);
    setLocalPlaying(false);
  }, [graph.nodes.length, graph.edges.length, startId, endId]);

  // Playback loop (controlled by parent when provided)
  useEffect(() => {
    const s = speed ?? 600;
    if (!playing) { if (timerRef.current) window.clearInterval(timerRef.current); timerRef.current = null; return; }
    timerRef.current = window.setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, (internal.steps?.length ?? 0) - 1));
    }, s);
    return () => { if (timerRef.current) window.clearInterval(timerRef.current); timerRef.current = null; };
  }, [playing, speed, internal.steps?.length]);

  const currentStep = internal.steps[stepIndex] ?? null;
  const currentNode = currentStep?.current ?? null;
  const visited = currentStep?.visited ?? new Set();
  const dist = currentStep?.dist ?? {};
  const finalPath = internal.finalPath ?? [];
  // Notify parent about exploration progress (lat/lon via nodeCoords)
  useEffect(() => {
    if (!onExplorationUpdate || !nodeCoords) return;
    const step = internal.steps[stepIndex] ?? null;
    if (!step) return;
    const visitedIds = Array.from(step.visited || []);
    const explorationPath = visitedIds
      .map((id) => {
        const c = nodeCoords[id];
        if (!c) return null;
        return { id, lat: c.lat, lon: c.lon };
      })
      .filter((x) => x && typeof x.lat === 'number' && typeof x.lon === 'number');
    const frontierIds = ((step.pq || []).map(p => p.node));
    const frontierPath = frontierIds
      .map((id) => {
        const c = nodeCoords[id];
        if (!c) return null;
        return { id, lat: c.lat, lon: c.lon };
      })
      .filter((x) => x && typeof x.lat === 'number' && typeof x.lon === 'number');
    const finalPathLatLngs = (internal.finalPath || []).map((id) => {
      const c = nodeCoords[id];
      return c ? { id, lat: c.lat, lon: c.lon } : null;
    }).filter(Boolean);
    onExplorationUpdate({ explorationPath, frontierPath, finalPathLatLngs });
  }, [stepIndex, internal, nodeCoords, onExplorationUpdate]);
  // Build path edges for highlighting
  const pathEdges = useMemo(() => {
    const edges = [];
    if (!finalPath || finalPath.length < 2) return edges;
    for (let i = 0; i < finalPath.length - 1; i++) edges.push([finalPath[i], finalPath[i+1]]);
    return edges;
  }, [finalPath]);
  const pathEdgeSet = useMemo(() => new Set(pathEdges.map(([a,b]) => `${a}-${b}` < `${b}-${a}` ? `${a}-${b}` : `${b}-${a}`)), [pathEdges]);

  // Graph positions for nodes: map by id
  const nodeMap = useMemo(() => {
    const m = new Map();
    graph.nodes.forEach(n => m.set(n.id, n));
    return m;
  }, [graph.nodes]);

  // Distance table entries
  const distancesForDisplay = useMemo(() => graph.nodes.reduce((acc, n) => {
    acc[n.id] = dist[n.id] ?? Number.POSITIVE_INFINITY;
    return acc;
  }, {}), [graph.nodes, dist]);

  // Simple methods
  const handleNext = () => setStepIndex((i) => Math.min(i + 1, (internal.steps?.length ?? 0) - 1));
  const handleReset = () => { setStepIndex(0); setLocalPlaying(false); };

  // UI helpers
  const width = 700;
  const height = 260;

  // Build node rendering state: current -> color, visited -> color
  const nodeColor = (id) => {
    if (id === currentNode) return '#f59e0b'; // current
    if (visited.has(id)) return '#86efac'; // visited
    return '#ffffff';
  };

  // Edge rendering: path edges blue
  const edgeStroke = (a,b) => pathEdgeSet.has(`${a}-${b}`) || pathEdgeSet.has(`${b}-${a}`) ? '#3b82f6' : '#cbd5e1';

  // Pseudo code text
  const pseudocode = [
    'while pq not empty',
    '  extract-min',
    '  for each neighbor, relax if better',
  ];
  const complexity = 'O((V+E) log V)';

  // Build color-coded path nodes for blue highlight after completion
  return (
    <div style={{ display: 'flex', gap: 16, padding: 12, height: '100%' }}>
      {/* Graph visualization */}
      <div style={{ flex: 1, border: '1px solid #e5e7eb', borderRadius: 8, padding: 12, background: '#fff' }}>
        <svg width={width} height={height} style={{ display: 'block' }}>
          {/* Edges */}
          {graph.edges.map((e, idx) => {
            const a = nodeMap.get(e.from);
            const b = nodeMap.get(e.to);
            if (!a || !b) return null;
            const onPath = pathEdgeSet.has(`${e.from}-${e.to}`) || pathEdgeSet.has(`${e.to}-${e.from}`);
            return (
              <line key={`e-${idx}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={onPath ? '#3b82f6' : '#cbd5e1'} strokeWidth={onPath ? 3 : 2} />
            );
          })}
          {/* Weights */}
          {graph.edges.map((e, idx) => {
            const a = nodeMap.get(e.from);
            const b = nodeMap.get(e.to);
            if (!a || !b) return null;
            const mx = (a.x + b.x) / 2;
            const my = (a.y + b.y) / 2;
            return (
              <text key={`w-${idx}`} x={mx} y={my - 6} textAnchor="middle" fontSize="12" fill="#374151">{e.w}</text>
            );
          })}
          {/* Nodes */}
          {graph.nodes.map((n) => {
            const isVisited = visited.has(n.id);
            const isCurrent = currentNode === n.id;
            const fill = isCurrent ? '#f59e0b' : isVisited ? '#86efac' : '#fff';
            return (
              <g key={`n-${n.id}`}>
                <circle cx={n.x} cy={n.y} r={14} fill={fill} stroke="#374151" />
                <text x={n.x} y={n.y + 4} textAnchor="middle" fontSize="12" fill="#111">{n.id}</text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* RIGHT PANEL: Metrics */}
          <div style={{ width: 360 }}>
        <div style={{ padding: 12, border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff', height: '100%' }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Dijkstra Metrics</h3>
          <div style={{ height: 12 }} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <strong>Current</strong>
              <div style={{ height: 4 }} />
              <span>{currentNode ?? '–'}</span>
            </div>
            <div>
              <strong>Visited</strong>
              <div style={{ height: 4 }} />
              <span>{visited.size}</span>
            </div>
          </div>
          <div style={{ height: 12 }} />
          <div>
            <strong>Distance Table</strong>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 6 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', fontSize: 12, padding: 6 }}>Node</th>
                  <th style={{ textAlign: 'right', fontSize: 12, padding: 6 }}>Dist</th>
                </tr>
              </thead>
              <tbody>
                {graph.nodes.map((n) => (
                  <tr key={`td-${n.id}`}>
                    <td style={{ padding: 6 }}>{n.id}</td>
                    <td style={{ padding: 6, textAlign: 'right' }}>{dist[n.id] !== undefined ? dist[n.id] === Number.POSITIVE_INFINITY ? '∞' : dist[n.id] : '–'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ height: 12 }} />
          <div>
            <strong>Priority Queue</strong>
            <div style={{ height: 6 }} />
            <div style={{ maxHeight: 120, overflowY: 'auto', border: '1px solid #e5e7eb', borderRadius: 6, padding: 6 }}>
              {internalPQtoList(internal, stepIndex)}
            </div>
          </div>
          <div style={{ height: 12 }} />
          <div>
            <strong>Path</strong>
            <div style={{ height: 6 }} />
            <div style={{ fontSize: 12, color: '#555' }}>{finalPath.length > 0 ? finalPath.join(' → ') : 'No path found'}</div>
          </div>
          <div style={{ height: 12 }} />
          <div>
            <strong>Pseudocode</strong>
            <pre style={{ background: '#f8fafc', padding: 8, borderRadius: 6, border: '1px solid #e2e8f0' }}>
{`while pq not empty:
  extract-min
  for each neighbor v of u:
    if dist[u] + w(u,v) < dist[v]:
      dist[v] = dist[u] + w(u,v)`}
            </pre>
            <div style={{ fontSize: 12 }}>Complexity: {complexity}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper: convert internal PQ snapshot to readable list
function internalPQtoList(state, stepIndex){
  const steps = state?.steps || [];
  const snap = steps[stepIndex] || null;
  const pq = snap?.pq ?? [];
  if (!pq.length) return <div style={{ color: '#888' }}>Empty</div>;
  return (
    <ul style={{ margin: 0, paddingLeft: 16 }}>
      {pq.map((p, i) => (
        <li key={`pq-${i}`}>{p.node}: {p.dist}</li>
      ))}
    </ul>
  );
}
