/**
 * Smart City Navigator - Main Application Component
 * React 18 + React-Leaflet + Tailwind CSS
 */

import React, { useState } from 'react';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';

// API configuration - reads from .env (VITE_API_URL) or falls back to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * SearchForm Component
 * Handles location input and search submission.
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onSearch - Callback with {source, destination, mode}
 * @param {boolean} props.loading - Whether search is in progress
 */
function SearchForm({ onSearch, loading }) {
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [mode, setMode] = useState('drive');

  /**
   * Handle form submission
   * @param {React.FormEvent} e - Form event
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate inputs
    if (!source.trim() || !destination.trim()) {
      return;
    }
    
    if (source.trim().toLowerCase() === destination.trim().toLowerCase()) {
      alert('Source and destination cannot be the same');
      return;
    }
    
    // Trigger search callback
    onSearch({
      source: source.trim(),
      destination: destination.trim(),
      mode
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Source Input */}
      <div>
        <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-1">
          Start Location
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
          </div>
          <input
            type="text"
            id="source"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="e.g., Sector 85, Mohali"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                       placeholder-gray-400 text-gray-900"
            disabled={loading}
            required
            minLength={3}
            maxLength={150}
          />
        </div>
      </div>

      {/* Destination Input */}
      <div>
        <label htmlFor="destination" className="block text-sm font-medium text-gray-700 mb-1">
          End Location
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
          </div>
          <input
            type="text"
            id="destination"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="e.g., Sector 21, Chandigarh"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                       placeholder-gray-400 text-gray-900"
            disabled={loading}
            required
            minLength={3}
            maxLength={150}
          />
        </div>
      </div>

      {/* Travel Mode Selection */}
      <div>
        <label htmlFor="mode" className="block text-sm font-medium text-gray-700 mb-1">
          Travel Mode
        </label>
        <select
          id="mode"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          disabled={loading}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg 
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                     bg-white text-gray-900"
        >
          <option value="drive">Drive</option>
          <option value="walk">Walk</option>
          <option value="bike">Bike</option>
        </select>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || !source.trim() || !destination.trim()}
        className={`
          w-full py-3 px-4 rounded-lg font-semibold text-white
          transition-all duration-200
          ${loading || !source.trim() || !destination.trim()
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 shadow-lg hover:shadow-xl'
          }
        `}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Calculating...
          </span>
        ) : (
          'Find Best Route'
        )}
      </button>
    </form>
  );
}

/**
 * ErrorAlert Component
 * Displays dismissible error messages.
 * 
 * @param {Object} props - Component props
 * @param {string|null} props.message - Error message to display
 * @param {Function} props.onDismiss - Callback to dismiss the alert
 */
function ErrorAlert({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[9999] w-full max-w-md px-4">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm text-red-800 font-medium">{message}</p>
          </div>
          <button
            onClick={onDismiss}
            className="ml-3 text-red-400 hover:text-red-600 transition-colors"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * LoadingOverlay Component
 * Full-screen loading indicator with message.
 * 
 * @param {string} message - Message to display during loading
 */
function LoadingOverlay({ message = 'Calculating optimal routes...' }) {
  return (
    <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-[9998] flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <svg className="animate-spin h-16 w-16 text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
        <p className="text-gray-700 font-medium">{message}</p>
      </div>
    </div>
  );
}

/**
 * Main App Component
 * Root component managing application state and layout.
 */
function App() {
  // Application state
  const [routes, setRoutes] = useState([]);
  const [bestRouteId, setBestRouteId] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(null);
  const [destination, setDestination] = useState(null);

  /**
   * Handle search submission
   * Calls backend API to calculate routes.
   * 
   * @param {Object} searchParams - Search parameters
   * @param {string} searchParams.source - Source location
   * @param {string} searchParams.destination - Destination location
   * @param {string} searchParams.mode - Travel mode
   */
  const handleSearch = async ({ source, destination, mode }) => {
    // Reset state
    setLoading(true);
    setError(null);
    setRoutes([]);
    setBestRouteId(null);
    setSelectedRouteId(null);

    try {
      // Make API request
      const response = await fetch(`${API_BASE_URL}/calculate-route`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source,
          destination,
          mode
        }),
      });

      // Parse response
      const data = await response.json();

      // Handle HTTP errors
      if (!response.ok) {
        throw new Error(data.detail || `HTTP error ${response.status}`);
      }

      // Update state with successful response
      setRoutes(data.routes || []);
      setBestRouteId(data.best_route_id);
      setSelectedRouteId(data.best_route_id);
      setSource(data.source);
      setDestination(data.destination);

    } catch (err) {
      // Handle errors gracefully
      console.error('Route calculation error:', err);
      setError(err.message || 'Failed to calculate routes. Please try again.');
    } finally {
      // Ensure loading state is cleared
      setLoading(false);
    }
  };

  /**
   * Handle route selection from panel
   * @param {number} routeId - ID of selected route
   */
  const handleRouteSelect = (routeId) => {
    setSelectedRouteId(routeId);
  };

  /**
   * Dismiss error alert
   */
  const handleDismissError = () => {
    setError(null);
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-gray-100">
      {/* Left Panel - Search and Route Selection (30%) */}
      <div className="w-[30%] min-w-[320px] max-w-[400px] bg-white shadow-xl flex flex-col z-10">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-blue-600 to-blue-700">
          <h1 className="text-2xl font-bold text-white">
            Smart City Navigator
          </h1>
          <p className="text-blue-100 text-sm mt-1">
            AI-Powered Multi-Route Optimization
          </p>
        </div>

        {/* Search Form */}
        <div className="p-6 border-b border-gray-200">
          <SearchForm onSearch={handleSearch} loading={loading} />
        </div>

        {/* Route Panel */}
        <RoutePanel
          routes={routes}
          bestRouteId={bestRouteId}
          selectedRouteId={selectedRouteId}
          onRouteSelect={handleRouteSelect}
        />
      </div>

      {/* Right Panel - Map View (70%) */}
      <div className="flex-1 relative">
        {/* Map Component */}
        <MapView
          routes={routes}
          bestRouteId={bestRouteId}
          selectedRouteId={selectedRouteId}
          onRouteClick={handleRouteSelect}
        />

        {/* Loading Overlay */}
        {loading && <LoadingOverlay />}

        {/* Error Alert */}
        <ErrorAlert message={error} onDismiss={handleDismissError} />
      </div>
    </div>
  );
}

export default App;
