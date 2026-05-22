# Ask Rovereto

Assistente AI per la mobilità urbana di Trento e Rovereto. Digita una domanda in linguaggio naturale ("Come arrivo al MART dalla stazione?", "Dove posso parcheggiare vicino al Duomo?") e ottieni indicazioni, percorsi e informazioni sui punti di interesse — il tutto su una mappa interattiva.

![stack](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi) ![stack](https://img.shields.io/badge/frontend-Vue%203-42b883?logo=vue.js) ![stack](https://img.shields.io/badge/AI-Gemma%204%20%28Ollama%29-FF6F00) ![license](https://img.shields.io/badge/license-MIT-blue)

---

## Funzionalità

- **Chat in linguaggio naturale** — chiedi indicazioni, orari, POI in italiano
- **Mappa interattiva** — percorsi a piedi, in bici o in auto disegnati in tempo reale
- **Open data del Trentino** — piste ciclabili, bike/car sharing, parcheggi, stazioni, taxi, luoghi di interesse
- **Routing preciso** — powered by OpenRouteService
- **Guardrail geografici** — l'AI risponde solo a domande su Trento e Rovereto

## Stack

| Layer | Tecnologia |
|-------|-----------|
| Frontend | Vue 3 + Vite + Leaflet |
| Backend | FastAPI (Python 3.11+) |
| AI | Gemma 4 in locale — function calling via [Ollama](https://ollama.com) |
| Routing | OpenRouteService API |
| Dati | Open data Comune di Trento (GeoJSON, EPSG:25832 → WGS84) |

## Prerequisiti

- Python 3.11+
- Node.js 18+
- Libreria di sistema `proj` (`sudo apt install libproj-dev` / `sudo pacman -S proj` / `brew install proj`)
- [Ollama](https://ollama.com) installato e in esecuzione con il modello Gemma 4:
  ```bash
  ollama pull gemma4
  ```
- Chiave API [OpenRouteService](https://openrouteservice.org/)

## Installazione

```bash
# 1. Clona il repository
git clone https://github.com/CassandraRosmini/ask-rovereto.git
cd ask-rovereto

# 2. Crea il virtual environment Python
python3 -m venv venv
venv/bin/pip install -r backend/requirements.txt

# 3. Configura le chiavi API
cp backend/.env.example backend/.env
# → apri backend/.env e inserisci GEMINI_API_KEY e ORS_API_KEY

# 4. Riproietta i dati geografici (una volta sola)
venv/bin/python scripts/reproject.py

# 5. Avvia il backend
cd backend && ../venv/bin/uvicorn main:app --reload --port 8000

# 6. Avvia il frontend (in un altro terminale)
cd frontend && npm install && npm run dev
```

Apri **http://localhost:5173**

## Variabili d'ambiente

Copia `backend/.env.example` in `backend/.env` e compila:

| Variabile | Descrizione |
|-----------|-------------|
| `ORS_API_KEY` | OpenRouteService API key |
| `DATA_DIR` | Percorso ai GeoJSON processati (default: `../data/processed`) |

## Struttura del progetto

```
backend/
  ai/         # Agente Gemini con function calling
  geo/        # Caricamento e riproiezione GeoJSON
  routers/    # Endpoint FastAPI (chat, POI)
  tests/      # Test unitari (pytest)
frontend/
  src/        # Componenti Vue 3, composables, Leaflet
data/
  *.geojson         # Dati grezzi EPSG:25832 (Comune di Trento)
  processed/        # Output WGS84 generato da reproject.py
scripts/
  reproject.py      # Conversione coordinate EPSG:25832 → WGS84
```

## Dati

I dataset geografici provengono dal portale open data del **Comune di Trento** e sono rilasciati con licenza aperta. Includono: piste ciclabili, stazioni bike/car sharing, parcheggi, fermate taxi, luoghi di interesse, stazioni ferroviarie.

## Sviluppo

```bash
# Test backend
cd backend && ../venv/bin/pytest tests/ -v

# Linting (ruff)
cd backend && ../venv/bin/ruff check .
```

## Licenza

[MIT](LICENSE)
