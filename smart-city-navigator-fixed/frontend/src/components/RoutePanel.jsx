/**
 * RoutePanel Component
 * Displays sidebar panel with route cards, summaries, and selection functionality.
 */

import React from 'react';

/**
 * RoutePanel Component
 * @param {Object} props - Component props
 * @param {Array} props.routes - Array of route objects
 * @param {number|null} props.bestRouteId - ID of the optimal route
 * @param {Function} props.onRouteSelect - Callback when a route is selected
 * @param {number|null} props.selectedRouteId - ID of currently selected route
 */
function RoutePanel({ routes = [], bestRouteId = null, onRouteSelect, selectedRouteId = null }) {
  
  /**
   * Get badge styling based on traffic level
   * @param {string} traffic - Traffic level: "Low", "Medium", or "High"
   * @returns {Object} Tailwind classes for the badge
   */
  const getTrafficBadgeClasses = (traffic) => {
    switch (traffic) {
      case 'Low':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'High':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  /**
   * Get route color based on route ID
   * @param {number} routeId - Route ID
   * @returns {string} Hex color code
   */
  const getRouteColor = (routeId) => {
    const colors = ['#3b82f6', '#f97316', '#a855f7', '#ec4899'];
    return colors[(routeId - 1) % colors.length];
  };

  /**
   * Format distance for display
   * @param {number} km - Distance in kilometers
   * @returns {string} Formatted distance string
   */
  const formatDistance = (km) => {
    if (km < 1) {
      return `${Math.round(km * 1000)} m`;
    }
    return `${km.toFixed(1)} km`;
  };

  /**
   * Format time for display
   * @param {number} minutes - Time in minutes
   * @returns {string} Formatted time string
   */
  const formatTime = (minutes) => {
    if (minutes < 1) {
      return 'Less than 1 min';
    }
    if (minutes < 60) {
      return `${Math.round(minutes)} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  /**
   * Calculate time savings between best and worst routes
   * @returns {number|null} Time difference in minutes
   */
  const getTimeSavings = () => {
    if (routes.length < 2) return null;
    
    const times = routes.map(r => r.estimated_time_minutes);
    const maxTime = Math.max(...times);
    const minTime = Math.min(...times);
    
    return Math.round(maxTime - minTime);
  };

  const timeSavings = getTimeSavings();

  /**
   * Handle route card click
   * @param {number} routeId - ID of clicked route
   */
  const handleRouteClick = (routeId) => {
    if (onRouteSelect) {
      onRouteSelect(routeId);
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Panel Header */}
      <div className="p-4 bg-white border-b border-gray-200 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900">Route Options</h2>
        
        {/* Summary statistics */}
        {routes.length > 0 && (
          <p className="text-sm text-gray-600 mt-1">
            Analyzing {routes.length} route{routes.length !== 1 ? 's' : ''}
            {timeSavings !== null && (
              <span className="text-green-600 font-medium">
                {' '}• Best saves ~{timeSavings} min vs worst
              </span>
            )}
          </p>
        )}
      </div>

      {/* Route Cards List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {routes.length === 0 ? (
          // Empty state when no routes available
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm">
              Enter locations above to see available routes
            </p>
          </div>
        ) : (
          // Render route cards
          routes.map((route, index) => {
            const isBest = route.id === bestRouteId;
            const isSelected = route.id === selectedRouteId;
            const routeColor = getRouteColor(route.id);

            return (
              <div
                key={route.id}
                onClick={() => handleRouteClick(route.id)}
                className={`
                  relative bg-white rounded-xl p-4 shadow-sm border-2 cursor-pointer
                  transition-all duration-200 hover:shadow-md hover:scale-[1.02]
                  ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-transparent'}
                  ${isBest ? 'ring-2 ring-green-100' : ''}
                `}
              >
                {/* Best Route Badge */}
                {isBest && (
                  <div className="absolute -top-2 -right-2">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-green-500 text-white shadow-sm">
                      Best Route
                    </span>
                  </div>
                )}

                {/* Route Header with Color Dot */}
                <div className="flex items-center gap-2 mb-3">
                  <div 
                    className="w-3 h-3 rounded-full shadow-sm" 
                    style={{ backgroundColor: routeColor }}
                  />
                  <h3 className="font-semibold text-gray-900">
                    Route {route.id}
                  </h3>
                </div>

                {/* Route Details Grid */}
                <div className="grid grid-cols-2 gap-3">
                  {/* Distance */}
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Distance</span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatDistance(route.distance_km)}
                    </span>
                  </div>

                  {/* Traffic Level */}
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Traffic</span>
                    <span className={`
                      inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-medium border
                      ${getTrafficBadgeClasses(route.traffic)}
                    `}>
                      {route.traffic}
                    </span>
                  </div>

                  {/* Estimated Time */}
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Est. Time</span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatTime(route.estimated_time_minutes)}
                    </span>
                  </div>

                  {/* Cost Score */}
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Score</span>
                    <span className={`text-sm font-medium ${isBest ? 'text-green-600' : 'text-gray-900'}`}>
                      {route.cost.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Traffic Factor Indicator (subtle) */}
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Traffic Factor</span>
                    <span className="font-mono">{route.traffic_factor.toFixed(2)}x</span>
                  </div>
                  {/* Traffic factor progress bar */}
                  <div className="mt-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className={`
                        h-full rounded-full transition-all duration-500
                        ${route.traffic === 'Low' ? 'bg-green-500' : route.traffic === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'}
                      `}
                      style={{ 
                        width: `${Math.min(route.traffic_factor * 40, 100)}%` 
                      }}
                    />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Panel Footer */}
      {routes.length > 0 && (
        <div className="p-4 bg-white border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            Routes calculated at {new Date().toLocaleTimeString()}
          </p>
        </div>
      )}
    </div>
  );
}

export default RoutePanel;
