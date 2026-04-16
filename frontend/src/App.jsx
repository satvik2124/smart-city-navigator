import React, { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Navigation, MapPin, Clock, Gauge, Route, RefreshCw,
  Loader2, AlertCircle, CheckCircle, X, Search, MapPinned,
  ArrowRight, Car, Timer, Signpost, History, Cpu, Layers
} from 'lucide-react'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

const API_BASE = 'http://localhost:8000'

const POPULAR_PLACES = [
  "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata",
  "Hyderabad", "Pune", "Gurgaon", "Noida", "Connaught Place",
  "Karol Bagh", "Dwarka", "Lajpat Nagar", "Saket", "Nehru Place",
  "Airport", "Railway Station", "Sector 21", "Sector 25"
]

const ROUTE_COLORS = {
  optimal: '#22c55e',
  alternative: ['#3b82f6', '#f97316', '#a855f7', '#ec4899']
}

function App() {
  const [sourceText, setSourceText] = useState('')
  const [destText, setDestText] = useState('')
  const [sourceLocation, setSourceLocation] = useState(null)
  const [destLocation, setDestLocation] = useState(null)
  const [routes, setRoutes] = useState([])
  const [selectedRoute, setSelectedRoute] = useState(null)
  const [optimalRoute, setOptimalRoute] = useState(null)
  const [trafficData, setTrafficData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [routeHistory, setRouteHistory] = useState([])
  const [showRoutes, setShowRoutes] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [activeInput, setActiveInput] = useState(null)
  const [routeMode, setRouteMode] = useState('drive')
  const mapRef = useRef(null)

  useEffect(() => {
    fetchTraffic()
    fetchHistory()
  }, [])

  useEffect(() => {
    const query = activeInput === 'source' ? sourceText : destText
    if (query.length > 1) {
      const filtered = POPULAR_PLACES.filter(p =>
        p.toLowerCase().includes(query.toLowerCase())
      )
      setSuggestions(filtered.slice(0, 6))
      setShowSuggestions(filtered.length > 0)
    } else {
      setShowSuggestions(false)
    }
  }, [sourceText, destText, activeInput])

  const fetchTraffic = async () => {
    try {
      const res = await axios.get(`${API_BASE}/simulate-traffic`)
      setTrafficData(res.data)
    } catch (err) {
      console.error('Traffic fetch error:', err)
    }
  }

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/routes-history?limit=5`)
      if (res.data.routes) {
        setRouteHistory(res.data.routes)
      }
    } catch (err) {
      console.error('History fetch error:', err)
    }
  }

  const handleSearch = async () => {
    if (!sourceText || !destText) {
      setError('Please enter both source and destination')
      return
    }

    setLoading(true)
    setError(null)
    setShowRoutes(false)

    try {
      const res = await axios.post(`${API_BASE}/calculate-route`, {
        source: sourceText,
        destination: destText,
        mode: routeMode
      })

      const data = res.data

      setSourceLocation(data.source)
      setDestLocation(data.destination)
      setRoutes(data.routes)
      setOptimalRoute(data.optimal_route)
      setSelectedRoute(data.optimal_route)
      setShowRoutes(true)

      if (mapRef.current) {
        const map = mapRef.current
        const bounds = L.latLngBounds([
          [data.source.coordinates.lat, data.source.coordinates.lon],
          [data.destination.coordinates.lat, data.destination.coordinates.lon]
        ])
        map.fitBounds(bounds, { padding: [80, 80], maxZoom: 13 })
      }

      fetchHistory()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to calculate route')
    } finally {
      setLoading(false)
    }
  }

  const handleRouteSelect = (route) => {
    setSelectedRoute(route)
  }

  const selectSuggestion = (place) => {
    if (activeInput === 'source') {
      setSourceText(place)
    } else {
      setDestText(place)
    }
    setShowSuggestions(false)
  }

  const handleHistoryClick = (history) => {
    setSourceText(history.source.name || 'Previous Location')
    setDestText(history.destination.name || 'Previous Destination')
    handleSearch()
  }

  const resetMap = () => {
    setSourceLocation(null)
    setDestLocation(null)
    setRoutes([])
    setSelectedRoute(null)
    setOptimalRoute(null)
    setSourceText('')
    setDestText('')
    setError(null)
    setShowRoutes(false)
  }

  const getCongestionColor = (level) => {
    if (level < 0.3) return '#22c55e'
    if (level < 0.6) return '#eab308'
    return '#ef4444'
  }

  const sourceIcon = L.divIcon({
    className: 'custom-marker',
    html: '<div class="marker-source">A</div>',
    iconSize: [36, 36],
    iconAnchor: [18, 18]
  })

  const destIcon = L.divIcon({
    className: 'custom-marker',
    html: '<div class="marker-dest">B</div>',
    iconSize: [36, 36],
    iconAnchor: [18, 18]
  })

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <Navigation size={28} />
            </div>
            <div className="logo-text">
              <h1>Smart City Navigator</h1>
              <p>AI-Powered Route Optimization</p>
            </div>
          </div>
          <div className="header-actions">
            {trafficData && (
              <div className="traffic-badge" style={{
                background: getCongestionColor(trafficData.congestion_level) + '22',
                color: getCongestionColor(trafficData.congestion_level)
              }}>
                <Gauge size={18} />
                <span>{trafficData.description}</span>
              </div>
            )}
            <button className="icon-btn" onClick={fetchTraffic} title="Refresh Traffic">
              <RefreshCw size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="main-content">
        {/* Search Panel */}
        <div className="search-panel">
          {/* Search Card */}
          <div className="search-card">
            <div className="search-header">
              <Search size={20} />
              <span>Find Route</span>
            </div>

            <div className="input-group">
              <label><MapPin className="source-icon" /> From</label>
              <div className="input-wrapper">
                <input
                  type="text"
                  placeholder="Enter starting point..."
                  value={sourceText}
                  onChange={(e) => { setSourceText(e.target.value); setActiveInput('source') }}
                  onFocus={() => setActiveInput('source')}
                />
                {showSuggestions && activeInput === 'source' && (
                  <div className="suggestions-dropdown">
                    {suggestions.map(s => (
                      <div key={s} onClick={() => selectSuggestion(s)}>
                        <MapPinned size={14} /> {s}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="input-group">
              <label><MapPin className="dest-icon" /> To</label>
              <div className="input-wrapper">
                <input
                  type="text"
                  placeholder="Enter destination..."
                  value={destText}
                  onChange={(e) => { setDestText(e.target.value); setActiveInput('dest') }}
                  onFocus={() => setActiveInput('dest')}
                />
                {showSuggestions && activeInput === 'dest' && (
                  <div className="suggestions-dropdown">
                    {suggestions.map(s => (
                      <div key={s} onClick={() => selectSuggestion(s)}>
                        <MapPinned size={14} /> {s}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="mode-selector">
              <button
                className={`mode-btn ${routeMode === 'drive' ? 'active' : ''}`}
                onClick={() => setRouteMode('drive')}
              >
                <Car size={16} /> Drive
              </button>
              <button
                className={`mode-btn ${routeMode === 'walk' ? 'active' : ''}`}
                onClick={() => setRouteMode('walk')}
              >
                <Navigation size={16} /> Walk
              </button>
              <button
                className={`mode-btn ${routeMode === 'bicycle' ? 'active' : ''}`}
                onClick={() => setRouteMode('bicycle')}
              >
                <Route size={16} /> Bike
              </button>
            </div>

            <button
              className="search-btn"
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? (
                <><Loader2 className="spin" size={20} /> Finding routes...</>
              ) : (
                <><Search size={20} /> Find Best Route</>
              )}
            </button>

            {error && (
              <div className="error-toast">
                <AlertCircle size={16} />
                <span>{error}</span>
                <button onClick={() => setError(null)}><X size={14} /></button>
              </div>
            )}
          </div>

          {/* Routes List */}
          <AnimatePresence>
            {showRoutes && routes.length > 0 && (
              <motion.div
                className="routes-panel"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="routes-header">
                  <h3><Layers size={18} /> {routes.length} Routes Found</h3>
                  <span className="optimal-badge">
                    <CheckCircle size={14} /> Best Route Highlighted
                  </span>
                </div>

                <div className="routes-list">
                  {routes.map((route) => (
                    <div
                      key={route.route_id}
                      className={`route-item ${selectedRoute?.route_id === route.route_id ? 'selected' : ''} ${route.is_optimal ? 'optimal' : ''}`}
                      onClick={() => handleRouteSelect(route)}
                      style={{ borderLeftColor: route.color }}
                    >
                      <div className="route-info">
                        <div className="route-time">{route.duration_text}</div>
                        <div className="route-name">
                          {route.is_optimal ? '⭐ ' : ''}Route {route.route_index}
                        </div>
                      </div>
                      <div className="route-stats">
                        <div className="route-dist">{route.distance_text}</div>
                        <div
                          className="route-traffic"
                          style={{ color: getCongestionColor(route.congestion_level) }}
                        >
                          {route.traffic_status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Selected Route Details */}
                {selectedRoute && (
                  <div className="route-details">
                    <h4><Signpost size={16} /> Route Details</h4>

                    <div className="detail-row">
                      <span>Distance</span>
                      <strong>{selectedRoute.distance_text}</strong>
                    </div>
                    <div className="detail-row">
                      <span>Duration</span>
                      <strong>{selectedRoute.duration_text}</strong>
                    </div>
                    <div className="detail-row">
                      <span>Traffic Delay</span>
                      <strong style={{ color: getCongestionColor(selectedRoute.congestion_level) }}>
                        +{selectedRoute.traffic_delay} min
                      </strong>
                    </div>
                    <div className="detail-row">
                      <span>Congestion</span>
                      <div className="congestion-bar">
                        <div
                          className="congestion-fill"
                          style={{
                            width: `${selectedRoute.congestion_level * 100}%`,
                            background: getCongestionColor(selectedRoute.congestion_level)
                          }}
                        />
                      </div>
                      <span>{(selectedRoute.congestion_level * 100).toFixed(0)}%</span>
                    </div>

                    <div className="location-names">
                      <div><MapPin size={14} /> {sourceLocation?.name || sourceText}</div>
                      <ArrowRight size={14} />
                      <div><MapPin size={14} /> {destLocation?.name || destText}</div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Traffic Info */}
          {trafficData && (
            <div className="traffic-info-card">
              <h3><Gauge size={18} /> Traffic Conditions</h3>
              <div className="traffic-period">{trafficData.time_period?.replace('_', ' ')}</div>
              <div className="traffic-zones">
                {trafficData.traffic_zones?.slice(0, 4).map((zone, i) => (
                  <div key={i} className="zone-item">
                    <span>{zone.name}</span>
                    <div className="zone-bar">
                      <div
                        className="zone-fill"
                        style={{
                          width: `${zone.level * 100}%`,
                          background: getCongestionColor(zone.level)
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* History */}
          {routeHistory.length > 0 && !showRoutes && (
            <div className="history-section">
              <h3><History size={18} /> Recent Searches</h3>
              {routeHistory.map((h, i) => (
                <div key={i} className="history-item" onClick={() => handleHistoryClick(h)}>
                  <MapPin size={14} />
                  <span>{h.source?.name || 'Start'} → {h.destination?.name || 'End'}</span>
                </div>
              ))}
            </div>
          )}

          {/* Popular Places */}
          <div className="popular-section">
            <h3>Popular Places</h3>
            <div className="popular-chips">
              {POPULAR_PLACES.slice(0, 12).map(place => (
                <button
                  key={place}
                  className="popular-chip"
                  onClick={() => setDestText(place)}
                >
                  {place}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Map */}
        <div className="map-wrapper">
          <MapContainer
            center={[28.6139, 77.2090]}
            zoom={12}
            className="leaflet-map"
            ref={mapRef}
          >
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {sourceLocation && (
              <Marker
                position={[sourceLocation.coordinates.lat, sourceLocation.coordinates.lon]}
                icon={sourceIcon}
              >
                <Popup>
                  <strong>A:</strong> {sourceLocation.name}
                </Popup>
              </Marker>
            )}

            {destLocation && (
              <Marker
                position={[destLocation.coordinates.lat, destLocation.coordinates.lon]}
                icon={destIcon}
              >
                <Popup>
                  <strong>B:</strong> {destLocation.name}
                </Popup>
              </Marker>
            )}

            {/* Render all routes */}
            {routes.map((route, index) => {
              const positions = route.polyline || route.geometry?.map(g => [g.lat, g.lon]) || []
              const isSelected = selectedRoute?.route_id === route.route_id
              const isOptimal = route.is_optimal

              return positions.length > 1 && (
                <Polyline
                  key={route.route_id}
                  positions={positions}
                  pathOptions={{
                    color: route.color,
                    weight: isSelected ? 6 : 3,
                    opacity: isSelected ? 0.9 : 0.5,
                    dashArray: isOptimal ? null : "10, 10"
                  }}
                />
              )
            })}
          </MapContainer>

          {/* Map Controls */}
          <div className="map-controls">
            <button className="control-btn" onClick={resetMap}>
              <X size={18} /> Clear
            </button>
            <button className="control-btn" onClick={fetchTraffic}>
              <RefreshCw size={18} /> Traffic
            </button>
          </div>

          {/* Legend */}
          <div className="map-legend">
            <div className="legend-item">
              <span className="dot green"></span> Start
            </div>
            <div className="legend-item">
              <span className="dot red"></span> End
            </div>
            <div className="legend-item">
              <span className="line solid green"></span> Best Route
            </div>
            <div className="legend-item">
              <span className="line dashed blue"></span> Alternatives
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
