# Ask Rovereto 🗺️

Assistente AI con chat + mappa per la mobilità urbana di Trento.
Usa open data del Comune + Gemini AI + OpenRouteService.

## Setup rapido

```bash
# 1. Copia le chiavi API
cp backend/.env.example backend/.env
# → inserisci GEMINI_API_KEY e ORS_API_KEY in backend/.env

# 2. Avvia tutto
./run.sh
```

Apri http://localhost:5173

## Stack

- **Frontend**: Vue 3 + Vite + Leaflet
- **Backend**: FastAPI (Python)
- **AI**: Gemini 2.0 Flash (function calling)
- **Routing**: OpenRouteService API
- **Dati**: Open data Comune di Trento (EPSG:25832 → WGS84)

## Struttura

```
backend/    → FastAPI, AI agent, geo utils
frontend/   → Vue 3, Leaflet map, chat UI
data/       → GeoJSON open data
scripts/    → preprocessing
docs/       → spec e piano di implementazione
```

## Piano implementazione

Vedi `docs/superpowers/plans/2026-05-21-ask-rovereto.md`

## Divisione lavoro

| Dev | Branch | Tasks |
|-----|--------|-------|
| A — Frontend | `dev/frontend` | Task 10-13 (Vue, Leaflet, chat UI) |
| B — Backend/AI | `dev/backend` | Task 2, 6-9 (FastAPI, Gemini, ORS) |
| C — Data/Geo | `dev/data` | Task 1, 3-5 (riproiezione, loader, nearest) |
