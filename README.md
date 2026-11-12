# Weather App

**Author:** Ritwik Aggarwal
**Submission:** _Completed — PM Accelerator AI Engineer Intern · Tech Assessments #1 and #2 (Full Stack)_

A small full-stack weather app: search any place, see current conditions + a
five-day outlook with practical tips, and save date-range requests with a
daily temperature record you can edit, export, and chart.

---

## Stack

- **Frontend** — React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, react-leaflet, Recharts
- **Backend** — Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, async httpx
- **Database** — SQLite by default (switch via `DATABASE_URL`)
- **Testing** — `pytest` + `respx` (backend); `vitest` (frontend)

## External services

The React app only talks to the FastAPI backend; the backend proxies every
external call, caches results, and returns one consistent error shape
(`{ error: { code, message, details } }`).

| Purpose                                 | Service                        | Key needed? |
| --------------------------------------- | ------------------------------ | ----------- |
| Place resolution (towns, landmarks, zip)| Nominatim (OpenStreetMap)      | No          |
| Autocomplete + forecast + archive + AQI | Open-Meteo                     | No          |
| Place blurb                             | Wikipedia REST                 | No          |
| Map                                     | Leaflet + OpenStreetMap tiles  | No          |
| Videos                                  | YouTube Data API v3            | Optional    |

Without a YouTube key the videos panel shows a "Watch videos of _place_ on
YouTube" search link.

---

## Setup

**Prerequisites:** Python 3.11+, Node 20+, Git.

```bash
git clone <this-repo-url> weather-app
cd weather-app
```

**Backend:**

```bash
cd backend
python -m venv venv
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# macOS/Linux:          source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # optional; defaults work
uvicorn app.main:app --reload --port 8000
```

Check <http://localhost:8000/api/v1/health> → `{"status": "ok"}`.
Interactive API docs: <http://localhost:8000/docs>.

**Frontend (new terminal):**

```bash
cd frontend
npm install
cp .env.example .env            # optional; defaults to localhost:8000
npm run dev
```

Open <http://localhost:5173>.

**Tests:**

```bash
cd backend && pytest -q && ruff check .
cd frontend && npm run lint && npm run test && npm run build
```

---

## Environment variables

Defaults ship in each `.env.example`.

| Name                   | Scope    | Default                                       | Purpose                                |
| ---------------------- | -------- | --------------------------------------------- | -------------------------------------- |
| `CORS_ORIGINS`         | backend  | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins               |
| `DATABASE_URL`         | backend  | `sqlite:///./weather.db`                      | SQLAlchemy URL; drop in Postgres       |
| `NOMINATIM_USER_AGENT` | backend  | `weather-app/0.1`                             | Required by Nominatim usage policy     |
| `YOUTUBE_API_KEY`      | backend  | _empty_                                       | Optional YouTube Data API v3 key       |
| `VITE_API_BASE_URL`    | frontend | `http://localhost:8000/api/v1`                | Backend base URL for the SPA           |

---

## What's implemented

### Tech Assessment #1 — frontend

- Location input accepting city, landmark, postal code, or `lat, lon`
- Autocomplete + fuzzy matching with a "Did you mean…?" picker when ambiguous
- "Use my location" button with permission / timeout / unsupported messages
- Current conditions card with weather icon (Lucide), feels-like, humidity, wind, UV, sunrise/sunset
- 5-day forecast grid
- "Things you might not think about" tips (umbrella, UV, layers, heat, wind, AQI, travel)
- °C / °F toggle persisted in localStorage
- Friendly error messages with Retry; app-wide error boundary
- Responsive layout tested at 375 / 768 / 1024 / 1440 px
- Author name in footer; About PM Accelerator modal

### Tech Assessment #2 — backend

- **CRUD** on saved weather requests (`/api/v1/requests`)
  - CREATE validates the date range and resolves the location (fuzzy match; 409 with candidates if ambiguous)
  - READ list supports search, sort, pagination; detail returns per-day rows
  - UPDATE re-validates and re-fetches daily temps when location or dates change
  - DELETE cascades to daily rows
- Archive vs. forecast routing — Open-Meteo archive for dates > ~5 days past, forecast for recent + up to 16 days ahead; results merged
- **Data export** in JSON, CSV, XML, Markdown, and PDF (ReportLab)
- **Extras** per location: YouTube videos, map, air quality, Wikipedia summary — each fetched in parallel and failing independently

---

## API reference

Full interactive docs at `/docs`.

- `GET  /api/v1/health`
- `GET  /api/v1/locations/autocomplete?q=&limit=`
- `GET  /api/v1/locations/resolve?q=`
- `GET  /api/v1/locations/extras?lat=&lon=&name=`
- `GET  /api/v1/weather/current?q=&location_index=`
- `POST /api/v1/requests` — body: `{location, start_date, end_date, notes?, location_index?}`
- `GET  /api/v1/requests?q=&sort=&page=&page_size=`
- `GET  /api/v1/requests/{id}`
- `PATCH /api/v1/requests/{id}` — any of `location`, `start_date`, `end_date`, `notes`
- `DELETE /api/v1/requests/{id}` (cascade)
- `GET  /api/v1/requests/export?format=json|csv|xml|md|pdf&ids=1,2,3`

Every error response has the shape:

```json
{ "error": { "code": "LOCATION_AMBIGUOUS", "message": "…", "details": { } } }
```

---

## Design notes

- **Backend proxies every external API.** The frontend never calls Nominatim,
  Open-Meteo, or YouTube directly, so the backend can rate-limit Nominatim
  (≤1 req/s per its policy), cache hot values, and normalise errors.
- **Temperatures are not directly editable.** Changing the location or dates
  re-fetches from the upstream API; raw numbers stay trustworthy.
- **Archive / forecast split.** Each date in a saved range is routed to the
  right Open-Meteo endpoint and merged into one daily series.
- **In-process TTL cache.** Geocoding 24 h, weather 10 min, extras 15 min.
- **Responsive technique summary.** Mobile-first Tailwind with `sm` / `md` /
  `lg` breakpoints, `min-w-0` on flex children to prevent overflow,
  collapsing grids (forecast `1 → 2 → 5` cols; extras `1 → 2`), tables with
  `overflow-x-auto`, and accessible roles / live regions / focus rings.

---

## Known limitations

- In-process cache only (fine for a single worker; use Redis for multi-worker).
- No authentication — all users share the saved-requests pool.
- No code-splitting on the SPA (~240 KB gzipped, mostly Leaflet + Recharts).
