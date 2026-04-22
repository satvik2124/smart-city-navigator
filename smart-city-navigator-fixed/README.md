# Smart City Navigator — AI-Powered Navigation System

> AI-based navigation that predicts traffic using ML and computes optimal routes with Dijkstra & A* algorithms. Integrates Geoapify APIs, OpenStreetMap, and real-time traffic simulation.

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm 9+

### Step 1 — Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2 — Start the backend

```bash
# From the backend/ directory
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
✓ Geoapify Routing client initialized (key: 142250f8...)
✓ Database initialized
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Step 3 — Install & start the frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### Step 4 — Open in browser

```
http://localhost:3000
```

Try searching: **Connaught Place, Delhi** → **India Gate, Delhi**

---

## 🔑 API Key

The Geoapify API key is already configured in `.env` and `backend/.env`.

If you need a new key:
1. Go to [https://www.geoapify.com/](https://www.geoapify.com/) — sign up free
2. Copy your key from the dashboard
3. Edit `.env` and `backend/.env`:
   ```
   GEOAPIFY_API_KEY=your_new_key_here
   ```

---

## 📁 Project Structure

```
smart-city-navigator/
├── .env                    ← Root env file (API key lives here)
├── backend/
│   ├── .env                ← Backend env file (copy of root)
│   ├── main.py             ← FastAPI app
│   ├── routing.py          ← Geoapify API + route scoring
│   ├── requirements.txt    ← Python dependencies
│   └── smart_city_navigator.db  ← SQLite DB (auto-created on first run)
├── frontend/
│   ├── .env                ← Vite env (VITE_API_URL)
│   ├── src/
│   │   ├── App.jsx         ← Main React component
│   │   ├── components/
│   │   │   ├── MapView.jsx ← Leaflet map with animated routes
│   │   │   └── RoutePanel.jsx ← Route list sidebar
│   │   └── index.css       ← Global styles + Tailwind
│   ├── vite.config.js      ← Dev server + proxy config
│   └── package.json
└── data/
    └── traffic_dataset.csv ← Traffic training data
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | API info + status |
| `/health` | GET | Health check |
| `/calculate-route` | POST | Calculate routes with AI optimization |
| `/routes-history` | GET | Recent route history |

### Example request

```bash
curl -X POST http://localhost:8000/calculate-route \
  -H "Content-Type: application/json" \
  -d '{"source": "Connaught Place, Delhi", "destination": "India Gate, Delhi", "mode": "drive"}'
```

---

## 🔧 Bugs Fixed in This Version

1. **`dotenv` loaded after `os.getenv()`** — API key was always empty even with `.env` present
2. **Missing `.env` files** — Created root `.env` and `backend/.env` with API key
3. **`requirements.txt` hard-pinned conflicting versions** — Relaxed to `>=` to avoid pip conflicts
4. **Frontend API URL hardcoded** — Now reads from `VITE_API_URL` env variable
5. **Missing `frontend/.env`** — Created with correct `VITE_API_URL`
6. **Vite proxy only covered `/api/*`** — Fixed to proxy all backend routes
7. **Missing favicon** — Created `/public/vite.svg` (was causing 404)
8. **Duplicate Leaflet CSS** — Removed CDN version (already bundled via npm)
9. **Database path was relative** — Fixed to absolute path based on `__file__`

---

## 🐳 Docker (optional)

```bash
cd docker
docker-compose up --build
```

---

## 🛠 Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Tailwind CSS, Leaflet.js |
| Backend | Python, FastAPI, uvicorn |
| Routing | Geoapify API |
| ML | scikit-learn (Random Forest) |
| Database | SQLite |
| Maps | OpenStreetMap |
