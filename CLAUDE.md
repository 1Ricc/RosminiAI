# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ask Rovereto — AI-powered urban mobility assistant for Trento, Italy. FastAPI backend with Gemini 2.0 Flash function calling, Vue 3 + Leaflet frontend, and open GeoJSON data from the Municipality of Trento.

## Critical: Data Preprocessing

**Run this once before any backend startup:**
```bash
python scripts/reproject.py
```
All raw GeoJSON files in `data/` use EPSG:25832 (UTM Zone 32N). Leaflet and the API expect WGS84 (EPSG:4326). Skipping this step causes coordinates to be ~600 km off.

**Exception:** `data/taxi.geojson` already contains WGS84 coords in `x` (latitude) and `y` (longitude) fields — the data loader must handle this format separately.

## Setup

```bash
# Backend
cd backend && pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY and ORS_API_KEY

# Frontend (once scaffolded)
cd frontend && npm install
```

## Dev Commands

```bash
# Backend dev server
cd backend && uvicorn main:app --reload --port 8000

# Frontend dev server
cd frontend && npm run dev        # Vite on :5173

# Tests
cd backend && pytest tests/ -v
```

## Environment Variables

Required in `backend/.env`:
- `GEMINI_API_KEY` — Google Gemini API key
- `ORS_API_KEY` — OpenRouteService API key
- `DATA_DIR` — path to processed GeoJSON, default `../data/processed`

## Gotchas

- **ORS coordinate order:** OpenRouteService expects `[lon, lat]` (not lat/lon).
- **ORS profiles:** `foot-walking`, `cycling-regular`, `driving-car`.
- **Large GeoJSON files excluded from frontend:** `territorio_line`, `territorio_polygon`, `usosuolo_view`, `isosec`, `grafo_web` are 40–85 MB — do not load them in the browser.
- **Gemini language:** The system prompt and all Gemini responses must be in Italian only.
- **Function calling limit:** Cap the agent loop at 5 iterations to prevent runaway calls.
- **Geocoding fallback:** Use Nominatim if a place isn't in the `KNOWN_PLACES` dict.

## Architecture

```
backend/
  ai/         # Gemini function-calling agent
  geo/        # Geospatial utilities (pyproj, GeoJSON loading)
  routers/    # FastAPI route handlers
  tests/      # pytest unit tests (mock Gemini and ORS)
frontend/
  src/        # Vue 3 components and composables
data/
  *.geojson         # Raw EPSG:25832 (do not edit)
  processed/        # WGS84 output of reproject.py
scripts/
  reproject.py      # EPSG:25832 → WGS84 conversion
```

Detailed spec: `@docs/superpowers/specs/2026-05-21-ask-rovereto-design.md`  
Implementation plan (15 tasks): `@docs/superpowers/plans/2026-05-21-ask-rovereto.md`

## Branches

- `dev/backend` — FastAPI, AI agent, geo utilities
- `dev/frontend` — Vue 3, Leaflet, chat UI
- `dev/data` — data preprocessing and GeoJSON handling
- Merge to `main` when stable