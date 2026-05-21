# Ask Rovereto 🗺️

Assistente AI con chat + mappa per la mobilità urbana di Trento.
Usa open data del Comune + Gemini AI + OpenRouteService.

## Setup rapido

> **Arch Linux / sistemi con Python externally-managed:** `pip install` globale non funziona.
> Usa il venv come descritto sotto.

```bash
# 1. Crea il virtual environment Python (una volta sola)
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

# 2. Copia le chiavi API
cp backend/.env.example backend/.env
# → inserisci GEMINI_API_KEY e ORS_API_KEY in backend/.env

# 3. Riproietta i dati geografici (una volta sola)
.venv/bin/python scripts/reproject.py

# 4. Avvia il backend
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000

# 5. Avvia il frontend (in un altro terminale)
cd frontend && npm install && npm run dev
```

Apri http://localhost:5173

### Comandi utili

```bash
# Test backend
cd backend && ../.venv/bin/pytest tests/ -v

# Aggiornare dipendenze Python
.venv/bin/pip install -r backend/requirements.txt
```

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
