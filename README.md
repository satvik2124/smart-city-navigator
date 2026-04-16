# Smart City Navigator - AI-Powered Navigation System

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

> **"I developed an AI-based Smart City Navigation System that predicts traffic conditions using machine learning and dynamically computes optimal routes using Dijkstra and A* algorithms. The system integrates Geoapify APIs, OpenStreetMap, GPS-based geolocation, and real-time traffic simulation. It also displays multiple alternative routes and selects the most efficient one using AI-driven optimization."**

## 🎯 Features

### Core Features
- **Geoapify Integration** - Real-world routing using Geoapify Routing & Geocoding APIs
- **Multiple Routes** - Display all possible routes between two locations
- **AI-Optimized Selection** - Automatically selects the best route using AI traffic prediction
- **Dynamic Traffic** - Traffic conditions change each time you search
- **Multi-Modal** - Support for driving, walking, and cycling routes

### AI & Routing
- **Dijkstra Algorithm** - Classic shortest path algorithm
- **A* Algorithm** - Heuristic-based optimal pathfinding
- **Random Forest Prediction** - ML-based traffic and ETA prediction
- **Real-time Simulation** - Time-based traffic patterns (rush hour, etc.)

### Frontend Features
- **Interactive Map** - Leaflet.js with OpenStreetMap tiles
- **Multiple Route Display** - Different colors for each route
- **Route Selection** - Click to highlight different routes
- **Traffic Visualization** - Congestion bars and traffic zones
- **Search History** - Quick access to recent searches

## 🚀 Quick Start

### 1. Get Geoapify API Key (Free)

1. Go to [Geoapify](https://www.geoapify.com/)
2. Sign up for free account
3. Get your API key from dashboard

### 2. Setup Environment

```bash
# Clone the repository
cd SmartCityNavigator

# Create .env file
cp .env.example .env

# Edit .env and add your API key
GEOAPIFY_API_KEY=your_api_key_here
```

### 3. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 4. Run the Application

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Open in Browser

```
http://localhost:3000
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/geocode` | POST | Convert place name to coordinates |
| `/calculate-route` | POST | Calculate multiple routes with AI optimization |
| `/simulate-traffic` | GET | Get dynamic traffic simulation |
| `/routes-history` | GET | Get route calculation history |
| `/compare-algorithms` | GET | Compare Dijkstra vs A* algorithms |

### Example: Calculate Route

```bash
curl -X POST http://localhost:8000/calculate-route \
  -H "Content-Type: application/json" \
  -d '{"source": "Connaught Place", "destination": "Sector 21", "mode": "drive"}'
```

## 🗺️ Route Color Scheme

| Route Type | Color | Description |
|------------|-------|-------------|
| Best Route | Green (#22c55e) | AI-optimized optimal route |
| Alternative 1 | Blue (#3b82f6) | First alternative |
| Alternative 2 | Orange (#f97316) | Second alternative |
| Alternative 3 | Purple (#a855f7) | Third alternative |
| Alternative 4 | Pink (#ec4899) | Fourth alternative |

## 🤖 AI Traffic Prediction

The system uses Random Forest Regression to predict:

- **Congestion Level** (0-100%)
- **Travel Time** considering traffic
- **Traffic Delay** compared to free-flow conditions

Traffic patterns simulated:
- **Morning Rush** (7-9 AM): High congestion
- **Lunch Time** (12-2 PM): Medium congestion
- **Evening Rush** (5-8 PM): Highest congestion
- **Night** (10 PM - 6 AM): Low congestion

## 🏗️ Project Structure

```
SmartCityNavigator/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── geocoding.py         # Geoapify API integration
│   ├── routing.py           # Dijkstra & A* algorithms
│   ├── simulation.py         # Dynamic traffic simulation
│   ├── ai_model.py          # ML traffic prediction
│   ├── database.py           # SQLite operations
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Component styles
│   │   └── index.css        # Global styles
│   └── package.json
│
├── data/                     # Database & datasets
├── models/                   # Trained ML models
├── docker/                   # Docker configuration
├── .env.example              # Environment template
└── README.md
```

## 🔧 Configuration

### Environment Variables

```env
# Geoapify API (required for real routing)
GEOAPIFY_API_KEY=your_api_key_here

# Backend
PORT=8000
HOST=0.0.0.0

# Database
DATABASE_URL=sqlite:///./data/smartcity.db
```

### Fallback Mode

If no Geoapify API key is provided, the system uses:
- Pre-defined location database
- Calculated routes between coordinates
- Multiple route variations

## 📊 Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | React 18, Tailwind CSS, Framer Motion |
| **Maps** | Leaflet.js, OpenStreetMap |
| **Backend** | Python, FastAPI |
| **Routing** | Geoapify API, NetworkX |
| **ML** | Scikit-learn, Random Forest |
| **Database** | SQLite |
| **HTTP** | httpx |

## 🎨 UI Features

### Search Panel
- Source & destination inputs with suggestions
- Travel mode selector (Drive/Walk/Bike)
- Route list with clickable items
- Traffic delay indicators
- Congestion progress bars

### Map Display
- All routes displayed in different colors
- Best route highlighted with solid line
- Alternative routes with dashed lines
- Source (green) and destination (red) markers
- Auto-fit bounds to show all routes

### Traffic Visualization
- Zone-based congestion display
- Real-time traffic patterns
- Color-coded congestion levels
- Delay predictions

## 🚢 Deployment

### Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d
```

### Manual Deployment

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run build
# Serve from dist/ folder
```

## 📝 API Response Example

```json
{
  "routes": [
    {
      "route_id": "route_1",
      "route_index": 1,
      "distance_km": 8.5,
      "distance_text": "8.5 km",
      "duration_minutes": 18.2,
      "duration_text": "18 min",
      "traffic_delay": 5.5,
      "congestion_level": 0.35,
      "traffic_status": "light",
      "is_optimal": true,
      "color": "#22c55e"
    }
  ],
  "optimal_route": {...},
  "source": {
    "name": "Connaught Place",
    "coordinates": {"lat": 28.6318, "lon": 77.2165}
  },
  "destination": {...},
  "traffic": {
    "congestion_level": 0.45,
    "description": "Moderate traffic - Some delays possible",
    "time_period": "evening_rush"
  }
}
```

## 🔮 Future Improvements

- [ ] Real-time traffic data integration
- [ ] Turn-by-turn navigation
- [ ] Weather impact on routes
- [ ] Mobile app (React Native)
- [ ] WebSocket for live updates
- [ ] Advanced ML model with real data

## 👤 Author

Satvik Sharma - [GitHub](https://github.com/)

## 📄 License

MIT License - see LICENSE file for details.

---

⭐ If this project helps you, please give it a star!

Built with ❤️ using FastAPI, React, Geoapify, and AI
