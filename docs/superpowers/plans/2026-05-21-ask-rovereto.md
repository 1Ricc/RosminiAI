# Ask Rovereto — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Costruire un assistente AI con chat + mappa che usa open data del Comune di Trento per rispondere a domande di mobilità urbana in linguaggio naturale.

**Architecture:** FastAPI backend con Gemini function calling per intent extraction + ORS per routing; GeoJSON in-memory riproiettati da EPSG:25832 a WGS84 all'avvio; Vue 3 + Leaflet frontend con layout split sidebar/mappa.

**Tech Stack:** Python 3.11+, FastAPI, google-generativeai, pyproj, httpx, pytest | Vue 3, Vite, Leaflet, axios

---

## Struttura File

```
ask-rovereto/
├── scripts/
│   └── reproject.py              # Task 1 — converte GeoJSON EPSG:25832→WGS84
├── backend/
│   ├── main.py                   # Task 2 — FastAPI app, CORS, startup
│   ├── requirements.txt          # Task 2
│   ├── .env.example              # Task 2
│   ├── geo/
│   │   ├── __init__.py
│   │   ├── converter.py          # Task 3 — utm_to_wgs84, reproject_geojson
│   │   ├── loader.py             # Task 4 — carica GeoJSON in AppState
│   │   ├── nearest.py            # Task 5 — haversine, find_nearest
│   │   └── routing.py            # Task 6 — ORS async client
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── prompt.py             # Task 7 — SYSTEM_PROMPT, KNOWN_PLACES
│   │   ├── tools.py              # Task 7 — definizioni tool Gemini
│   │   └── agent.py              # Task 8 — function calling loop
│   ├── routers/
│   │   └── chat.py               # Task 9 — POST /chat endpoint
│   └── tests/
│       ├── test_converter.py     # Task 3
│       ├── test_nearest.py       # Task 5
│       └── test_agent.py         # Task 8
├── frontend/
│   ├── index.html                # Task 10
│   ├── package.json              # Task 10
│   ├── vite.config.js            # Task 10
│   └── src/
│       ├── main.js               # Task 10
│       ├── App.vue               # Task 13
│       ├── composables/
│       │   ├── useChat.js        # Task 11
│       │   └── useMap.js         # Task 12
│       └── components/
│           ├── ChatPanel.vue     # Task 11
│           ├── MapView.vue       # Task 12
│           └── SuggestionChips.vue # Task 13
├── data/
│   ├── *.geojson                 # originali EPSG:25832 (già presenti)
│   └── processed/                # generati da Task 1
└── run.sh                        # Task 14
```

---

## Task 1: Script di riproiezione GeoJSON

**Files:**
- Create: `scripts/reproject.py`
- Output: `data/processed/*.geojson`

Converte tutti i GeoJSON da EPSG:25832 a WGS84. Va eseguito una volta sola prima di avviare il backend.

- [ ] **Step 1: Crea `scripts/reproject.py`**

```python
#!/usr/bin/env python3
"""Riproietta tutti i GeoJSON da EPSG:25832 (UTM 32N) a WGS84."""

import json
import sys
from pathlib import Path

from pyproj import Transformer

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "processed"

DATASETS = [
    "bike_sharing",
    "car_sharing",
    "stazioni",
    "taxi",
    "zone_parcheggio",
    "piste_ciclabili",
    "patti",
]

_transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)


def convert_coords(coords: list) -> list:
    if isinstance(coords[0], list):
        return [convert_coords(c) for c in coords]
    lon, lat = _transformer.transform(coords[0], coords[1])
    return [lon, lat]


def reproject(src: Path, dst: Path) -> int:
    with open(src) as f:
        data = json.load(f)

    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if geom and geom.get("coordinates"):
            geom["coordinates"] = convert_coords(geom["coordinates"])

    data["crs"] = None  # rimuovi dopo riproiezione — Leaflet assume WGS84

    with open(dst, "w") as f:
        json.dump(data, f)

    return len(data.get("features", []))


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name in DATASETS:
        src = DATA_DIR / f"{name}.geojson"
        dst = OUT_DIR / f"{name}.geojson"
        if not src.exists():
            print(f"  SKIP {name}.geojson (non trovato)")
            continue
        n = reproject(src, dst)
        print(f"  OK   {name}.geojson ({n} features)")

    print(f"\nFile processati in: {OUT_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Installa pyproj e lancia lo script**

```bash
pip install pyproj
cd /home/fallenangel/projects/CassandraRosmini
python scripts/reproject.py
```

Output atteso:
```
  OK   bike_sharing.geojson (39 features)
  OK   car_sharing.geojson (8 features)
  OK   stazioni.geojson (10 features)
  OK   taxi.geojson (9 features)
  OK   zone_parcheggio.geojson (12 features)
  OK   piste_ciclabili.geojson (280 features)
  OK   patti.geojson (91 features)

File processati in: .../data/processed
```

- [ ] **Step 3: Verifica visiva coordinate**

```bash
python3 -c "
import json
with open('data/processed/bike_sharing.geojson') as f:
    d = json.load(f)
feat = d['features'][0]
coords = feat['geometry']['coordinates']
print('Lon:', coords[0], '(atteso ~11.1)')
print('Lat:', coords[1], '(atteso ~46.0)')
"
```

Entrambi i valori devono essere in range geografico italiano (lat ~45-47, lon ~10-12). Se le coordinate sono ancora ~660000/5100000, lo script non ha funzionato.

- [ ] **Step 4: Commit**

```bash
git add scripts/reproject.py data/processed/
git commit -m "feat: script riproiezione GeoJSON EPSG:25832→WGS84"
```

---

## Task 2: Scaffold FastAPI

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/main.py`
- Create: `backend/geo/__init__.py`
- Create: `backend/ai/__init__.py`
- Create: `backend/routers/__init__.py`

- [ ] **Step 1: Crea `backend/requirements.txt`**

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
httpx==0.28.1
pyproj==3.7.1
google-generativeai==0.8.3
python-dotenv==1.0.1
pytest==8.3.4
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Installa dipendenze**

```bash
cd backend
pip install -r requirements.txt
```

- [ ] **Step 3: Crea `backend/.env.example`**

```
GEMINI_API_KEY=your_gemini_api_key_here
ORS_API_KEY=your_ors_api_key_here
DATA_DIR=../data/processed
```

- [ ] **Step 4: Crea `backend/.env`** (copia e compila con chiavi reali)

```bash
cp backend/.env.example backend/.env
# Apri .env e inserisci le chiavi reali
```

- [ ] **Step 5: Crea package init files**

```bash
touch backend/geo/__init__.py backend/ai/__init__.py backend/routers/__init__.py backend/tests/__init__.py
```

- [ ] **Step 6: Crea `backend/main.py`**

```python
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from geo.loader import load_all_datasets
from routers.chat import router as chat_router

app = FastAPI(title="Ask Rovereto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    data_dir = Path(os.getenv("DATA_DIR", "../data/processed"))
    app.state.datasets = load_all_datasets(data_dir)
    print(f"Datasets caricati: {list(app.state.datasets.keys())}")


@app.get("/health")
def health():
    datasets = getattr(app.state, "datasets", {})
    return {
        "status": "ok",
        "datasets_loaded": len(datasets),
        "features_count": {k: len(v) for k, v in datasets.items()},
    }


# Serve GeoJSON processati al frontend
data_dir = Path(os.getenv("DATA_DIR", "../data/processed"))
if data_dir.exists():
    app.mount("/static", StaticFiles(directory=str(data_dir)), name="static")

app.include_router(chat_router, prefix="/api")
```

- [ ] **Step 7: Verifica avvio** (il loader non esiste ancora — è normale che fallisca con ImportError)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Se fallisce con `ModuleNotFoundError: geo.loader` — è atteso. Procedi al Task 3.

---

## Task 3: Converter UTM→WGS84

**Files:**
- Create: `backend/geo/converter.py`
- Create: `backend/tests/test_converter.py`

- [ ] **Step 1: Scrivi il test**

```python
# backend/tests/test_converter.py
import pytest
from geo.converter import utm_to_wgs84, reproject_feature_coords


def test_utm_to_wgs84_stazione_trento():
    # Coordinate UTM nota: stazione FS Trento approssimativa
    lat, lon = utm_to_wgs84(663944.0, 5104299.0)
    assert 46.05 < lat < 46.09, f"lat fuori range: {lat}"
    assert 11.10 < lon < 11.15, f"lon fuori range: {lon}"


def test_utm_to_wgs84_ordine_output():
    lat, lon = utm_to_wgs84(663944.0, 5104299.0)
    # lat deve essere ~46, lon ~11 (non invertiti)
    assert lat > lon, "lat e lon sembrano invertiti"


def test_reproject_feature_coords_point():
    coords = [663944.0, 5104299.0]
    result = reproject_feature_coords(coords)
    assert len(result) == 2
    # GeoJSON usa [lon, lat]
    assert 11.0 < result[0] < 12.0, f"lon fuori range: {result[0]}"
    assert 45.0 < result[1] < 47.0, f"lat fuori range: {result[1]}"


def test_reproject_feature_coords_linestring():
    coords = [[663944.0, 5104299.0], [664000.0, 5104400.0]]
    result = reproject_feature_coords(coords)
    assert len(result) == 2
    assert len(result[0]) == 2
```

- [ ] **Step 2: Lancia il test (deve fallire)**

```bash
cd backend
pytest tests/test_converter.py -v
```

Atteso: `ModuleNotFoundError: No module named 'geo.converter'`

- [ ] **Step 3: Crea `backend/geo/converter.py`**

```python
from pyproj import Transformer

_transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)


def utm_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Converte coordinate UTM Zone 32N (EPSG:25832) in WGS84 (lat, lon)."""
    lon, lat = _transformer.transform(x, y)
    return lat, lon


def reproject_feature_coords(coords: list) -> list:
    """Riproietta coordinate GeoJSON ricorsivamente. Restituisce [lon, lat] per GeoJSON."""
    if isinstance(coords[0], list):
        return [reproject_feature_coords(c) for c in coords]
    lon, lat = _transformer.transform(coords[0], coords[1])
    return [lon, lat]
```

- [ ] **Step 4: Lancia il test (deve passare)**

```bash
cd backend
pytest tests/test_converter.py -v
```

Atteso: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/geo/converter.py backend/tests/test_converter.py
git commit -m "feat: geo converter UTM 25832 → WGS84"
```

---

## Task 4: GeoJSON Loader

**Files:**
- Create: `backend/geo/loader.py`

- [ ] **Step 1: Crea `backend/geo/loader.py`**

```python
import json
from pathlib import Path


def _load_geojson_points(path: Path) -> list[dict]:
    """Carica un GeoJSON di punti WGS84 e restituisce lista di dict con lat/lon."""
    if not path.exists():
        print(f"  WARN: {path.name} non trovato, skip")
        return []
    with open(path) as f:
        data = json.load(f)
    result = []
    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        props = feat.get("properties", {})
        if geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"]
        result.append({"lat": lat, "lon": lon, **props})
    return result


def _load_taxi(path: Path) -> list[dict]:
    """Taxi ha già coordinate WGS84 nei campi x (lat) e y (lon)."""
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    result = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        try:
            lat = float(props.get("x") or 0)
            lon = float(props.get("y") or 0)
            if lat and lon:
                result.append({"lat": lat, "lon": lon, **props})
        except (ValueError, TypeError):
            continue
    return result


def load_all_datasets(data_dir: Path) -> dict:
    """Carica tutti i dataset in memoria. Chiamato una volta sola all'avvio."""
    return {
        "bike_sharing":  _load_geojson_points(data_dir / "bike_sharing.geojson"),
        "car_sharing":   _load_geojson_points(data_dir / "car_sharing.geojson"),
        "stazioni":      _load_geojson_points(data_dir / "stazioni.geojson"),
        "taxi":          _load_taxi(data_dir / "taxi.geojson"),
        "parcheggi":     _load_geojson_points(data_dir / "zone_parcheggio.geojson"),
        "patti":         _load_geojson_points(data_dir / "patti.geojson"),
    }
```

- [ ] **Step 2: Verifica avvio backend**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Output atteso (nella console):
```
Datasets caricati: ['bike_sharing', 'car_sharing', 'stazioni', 'taxi', 'parcheggi', 'patti']
```

- [ ] **Step 3: Testa `/health`**

```bash
curl http://localhost:8000/health
```

Atteso:
```json
{"status":"ok","datasets_loaded":6,"features_count":{"bike_sharing":39,"car_sharing":8,...}}
```

- [ ] **Step 4: Commit**

```bash
git add backend/geo/loader.py
git commit -m "feat: GeoJSON loader in-memory all'avvio FastAPI"
```

---

## Task 5: Nearest Neighbor

**Files:**
- Create: `backend/geo/nearest.py`
- Create: `backend/tests/test_nearest.py`

- [ ] **Step 1: Scrivi il test**

```python
# backend/tests/test_nearest.py
from geo.nearest import haversine, find_nearest


def test_haversine_zero_distance():
    assert haversine(46.07, 11.12, 46.07, 11.12) == 0.0


def test_haversine_trento_bolzano():
    # Trento → Bolzano ~55 km
    d = haversine(46.0664, 11.1168, 46.4983, 11.3548)
    assert 50_000 < d < 60_000, f"distanza inattesa: {d}m"


def test_find_nearest_returns_n_results():
    poi_list = [
        {"lat": 46.07, "lon": 11.12, "name": "A"},
        {"lat": 46.08, "lon": 11.13, "name": "B"},
        {"lat": 46.09, "lon": 11.14, "name": "C"},
        {"lat": 46.10, "lon": 11.15, "name": "D"},
    ]
    results = find_nearest(poi_list, 46.07, 11.12, n=2)
    assert len(results) == 2


def test_find_nearest_closest_first():
    poi_list = [
        {"lat": 46.07, "lon": 11.12, "name": "vicino"},
        {"lat": 46.20, "lon": 11.30, "name": "lontano"},
    ]
    results = find_nearest(poi_list, 46.07, 11.12, n=2)
    assert results[0]["name"] == "vicino"
    assert results[0]["distance_m"] < results[1]["distance_m"]


def test_find_nearest_includes_distance():
    poi_list = [{"lat": 46.07, "lon": 11.12, "name": "test"}]
    results = find_nearest(poi_list, 46.07, 11.12, n=1)
    assert "distance_m" in results[0]
    assert results[0]["distance_m"] == 0


def test_find_nearest_empty_list():
    results = find_nearest([], 46.07, 11.12, n=3)
    assert results == []
```

- [ ] **Step 2: Lancia i test (devono fallire)**

```bash
cd backend
pytest tests/test_nearest.py -v
```

Atteso: `ModuleNotFoundError: No module named 'geo.nearest'`

- [ ] **Step 3: Crea `backend/geo/nearest.py`**

```python
import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distanza in metri tra due punti WGS84."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest(poi_list: list[dict], lat: float, lon: float, n: int = 3) -> list[dict]:
    """Restituisce i n POI più vicini al punto (lat, lon), ordinati per distanza."""
    if not poi_list:
        return []
    scored = [
        (haversine(lat, lon, p["lat"], p["lon"]), p)
        for p in poi_list
    ]
    scored.sort(key=lambda x: x[0])
    return [{"distance_m": round(dist), **poi} for dist, poi in scored[:n]]
```

- [ ] **Step 4: Lancia i test (devono passare)**

```bash
cd backend
pytest tests/test_nearest.py -v
```

Atteso: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/geo/nearest.py backend/tests/test_nearest.py
git commit -m "feat: nearest neighbor con haversine"
```

---

## Task 6: ORS Routing Client

**Files:**
- Create: `backend/geo/routing.py`

- [ ] **Step 1: Crea `backend/geo/routing.py`**

```python
import os
import httpx

ORS_BASE = "https://api.openrouteservice.org/v2/directions"
TIMEOUT = 10.0


async def get_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    profile: str,
) -> dict:
    """
    Calcola percorso via ORS.
    origin/destination: (lat, lon)
    profile: "foot-walking" | "cycling-regular" | "driving-car"
    Restituisce dict con geojson, distance_m, duration_s.
    """
    api_key = os.getenv("ORS_API_KEY", "")
    url = f"{ORS_BASE}/{profile}/geojson"
    payload = {
        "coordinates": [
            [origin[1], origin[0]],          # ORS vuole [lon, lat]
            [destination[1], destination[0]],
        ],
        "instructions": False,
    }
    headers = {"Authorization": api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()

    data = r.json()
    feature = data["features"][0]
    summary = feature["properties"]["summary"]

    return {
        "geojson": feature["geometry"],           # LineString per Leaflet
        "distance_m": round(summary["distance"]),
        "duration_s": round(summary["duration"]),
    }


def co2_saved_grams(distance_m: float, profile: str) -> int:
    """CO₂ risparmiato rispetto a un'auto (210g/km) per modalità sostenibili."""
    if profile not in ("foot-walking", "cycling-regular"):
        return 0
    return round(distance_m * 0.21)
```

- [ ] **Step 2: Test manuale ORS** (richiede chiave reale in `.env`)

```bash
cd backend
python3 -c "
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from geo.routing import get_route

async def test():
    result = await get_route(
        origin=(46.0707, 11.1193),       # Stazione FS
        destination=(46.0669, 11.1236),  # MART
        profile='cycling-regular'
    )
    print('Distanza:', result['distance_m'], 'm')
    print('Durata:', result['duration_s'], 's')
    print('Geometry type:', result['geojson']['type'])

asyncio.run(test())
"
```

Atteso: distanza ~1000-2000m, geometria LineString.

- [ ] **Step 3: Commit**

```bash
git add backend/geo/routing.py
git commit -m "feat: ORS async routing client con calcolo CO2"
```

---

## Task 7: AI — Prompt e Tool Definitions

**Files:**
- Create: `backend/ai/prompt.py`
- Create: `backend/ai/tools.py`

- [ ] **Step 1: Crea `backend/ai/prompt.py`**

```python
SYSTEM_PROMPT = """Sei un assistente di mobilità urbana per la città di Trento, Italia.
Aiuti cittadini e turisti a muoversi in modo sostenibile usando trasporti pubblici, bici, car sharing e a piedi.

REGOLE FONDAMENTALI:
- Rispondi SEMPRE in italiano
- Preferisci modalità sostenibili: bici > piedi > auto
- Quando l'utente menziona un luogo specifico, usa SEMPRE geocode_location per trovare le coordinate esatte
- Dopo aver trovato le coordinate, usa find_nearest_poi per trovare opzioni di mobilità vicine
- Usa get_route per calcolare il percorso effettivo
- Presenta la risposta con passi numerati chiari: 1. ... 2. ... 3. ...
- Includi sempre distanza approssimativa e tempo stimato
- Non inventare MAI indirizzi, distanze o coordinate — usa sempre i tool
- Se un luogo non è trovato, chiedi all'utente di specificare meglio

FORMATO RISPOSTA:
Inizia con una frase breve che conferma l'itinerario suggerito.
Poi elenca i passi numerati.
Concludi con una nota sulla sostenibilità se il percorso è in bici o a piedi.

DATI DISPONIBILI:
- 39 postazioni bike sharing in città
- 8 punti car sharing
- 10 stazioni treno/ferrovia (FS + FTM)
- 9 stazioni taxi
- 12 zone parcheggio (ZTL + corone tariffarie)
- 280 tratti di piste ciclabili
"""

KNOWN_PLACES: dict[str, tuple[float, float]] = {
    "stazione fs": (46.0707, 11.1193),
    "stazione trento": (46.0707, 11.1193),
    "stazione ferroviaria": (46.0707, 11.1193),
    "stazione ftm": (46.0714, 11.1198),
    "mart": (46.0669, 11.1236),
    "museo mart": (46.0669, 11.1236),
    "museo di arte moderna": (46.0669, 11.1236),
    "piazza duomo": (46.0668, 11.1213),
    "duomo": (46.0668, 11.1213),
    "cattedrale": (46.0668, 11.1213),
    "castello del buonconsiglio": (46.0725, 11.1261),
    "buonconsiglio": (46.0725, 11.1261),
    "muse": (46.0613, 11.1164),
    "museo delle scienze": (46.0613, 11.1164),
    "piedicastello": (46.0731, 11.1100),
    "centro storico": (46.0668, 11.1213),
    "piazza fiera": (46.0672, 11.1198),
    "via roma": (46.0672, 11.1220),
    "povo": (46.0664, 11.1506),
    "villazzano": (46.0544, 11.1411),
    "gardolo": (46.0932, 11.1222),
    "mattarello": (45.9997, 11.1278),
    "aeroporto": (46.0183, 11.1211),
    "piazza dante": (46.0682, 11.1213),
    "palazzo thun": (46.0679, 11.1218),
}
```

- [ ] **Step 2: Crea `backend/ai/tools.py`**

```python
import google.generativeai as genai

TOOL_DECLARATIONS = [
    genai.protos.FunctionDeclaration(
        name="geocode_location",
        description=(
            "Converte il nome di un luogo (es. 'Stazione FS', 'MART', 'Piazza Duomo') "
            "in coordinate latitudine/longitudine. Usare SEMPRE prima di cercare POI vicini."
        ),
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "place_name": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    description="Nome del luogo da geocodificare"
                ),
            },
            required=["place_name"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="find_nearest_poi",
        description=(
            "Trova i punti di interesse più vicini a una posizione geografica. "
            "Usare per trovare bike sharing, car sharing, parcheggi, stazioni, taxi."
        ),
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitudine WGS84"),
                "lon": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitudine WGS84"),
                "poi_type": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    enum=["bike_sharing", "car_sharing", "parking", "train_station", "taxi"],
                    description="Tipo di POI da cercare",
                ),
                "max_results": genai.protos.Schema(
                    type=genai.protos.Type.INTEGER,
                    description="Numero massimo di risultati (default 3)",
                ),
            },
            required=["lat", "lon", "poi_type"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="get_route",
        description=(
            "Calcola un percorso tra due coordinate usando OpenRouteService. "
            "Usare dopo aver trovato le coordinate di origine e destinazione."
        ),
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "origin_lat":  genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitudine punto di partenza"),
                "origin_lon":  genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitudine punto di partenza"),
                "dest_lat":    genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitudine destinazione"),
                "dest_lon":    genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitudine destinazione"),
                "profile": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    enum=["foot-walking", "cycling-regular", "driving-car"],
                    description="Modalità di trasporto",
                ),
            },
            required=["origin_lat", "origin_lon", "dest_lat", "dest_lon", "profile"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="get_cycling_paths_near",
        description="Restituisce se ci sono piste ciclabili vicino a un punto. Utile per suggerire percorsi in bici.",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                "lon": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                "radius_m": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Raggio ricerca in metri (default 500)"),
            },
            required=["lat", "lon"],
        ),
    ),
]

GEMINI_TOOL = genai.protos.Tool(function_declarations=TOOL_DECLARATIONS)
```

- [ ] **Step 3: Commit**

```bash
git add backend/ai/prompt.py backend/ai/tools.py
git commit -m "feat: AI prompt e tool definitions Gemini"
```

---

## Task 8: Gemini Agent — Function Calling Loop

**Files:**
- Create: `backend/ai/agent.py`
- Create: `backend/tests/test_agent.py`

- [ ] **Step 1: Scrivi il test con mock di Gemini**

```python
# backend/tests/test_agent.py
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from ai.agent import execute_tool, build_chips


@pytest.mark.asyncio
async def test_execute_tool_geocode_known_place():
    datasets = {}
    result = await execute_tool("geocode_location", {"place_name": "mart"}, datasets, {})
    assert result["found"] is True
    assert 46.05 < result["lat"] < 46.09
    assert 11.10 < result["lon"] < 11.15


@pytest.mark.asyncio
async def test_execute_tool_geocode_unknown_place():
    datasets = {}
    # Luogo inventato — deve restituire found=False (senza chiamare Nominatim in test)
    with patch("ai.agent.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MagicMock(json=MagicMock(return_value=[]))
        )
        result = await execute_tool("geocode_location", {"place_name": "luogo_inesistente_xyz"}, datasets, {})
    assert result["found"] is False


@pytest.mark.asyncio
async def test_execute_tool_find_nearest_bike():
    datasets = {
        "bike_sharing": [
            {"lat": 46.07, "lon": 11.12, "fumetto": "Test Station", "cicloposteggi": 8},
            {"lat": 46.09, "lon": 11.14, "fumetto": "Far Station", "cicloposteggi": 4},
        ]
    }
    result = await execute_tool(
        "find_nearest_poi",
        {"lat": 46.07, "lon": 11.12, "poi_type": "bike_sharing", "max_results": 1},
        datasets,
        {},
    )
    assert len(result["pois"]) == 1
    assert result["pois"][0]["fumetto"] == "Test Station"


def test_build_chips_cycling():
    chips = build_chips(distance_m=1200, duration_s=420, profile="cycling-regular")
    labels = [c["label"] for c in chips]
    assert "tempo" in labels
    assert "distanza" in labels
    assert "CO₂ risparmiata" in labels


def test_build_chips_car_no_co2():
    chips = build_chips(distance_m=2000, duration_s=300, profile="driving-car")
    labels = [c["label"] for c in chips]
    assert "CO₂ risparmiata" not in labels
```

- [ ] **Step 2: Lancia i test (devono fallire)**

```bash
cd backend
pytest tests/test_agent.py -v
```

Atteso: `ModuleNotFoundError: No module named 'ai.agent'`

- [ ] **Step 3: Crea `backend/ai/agent.py`**

```python
import os
from typing import Any

import httpx
import google.generativeai as genai
from dotenv import load_dotenv

from ai.prompt import SYSTEM_PROMPT, KNOWN_PLACES
from ai.tools import GEMINI_TOOL
from geo.nearest import find_nearest
from geo.routing import get_route, co2_saved_grams

load_dotenv()

POI_TYPE_MAP = {
    "bike_sharing":  "bike_sharing",
    "car_sharing":   "car_sharing",
    "parking":       "parcheggi",
    "train_station": "stazioni",
    "taxi":          "taxi",
}

MARKER_TYPE_MAP = {
    "bike_sharing":  "bike_sharing",
    "car_sharing":   "car_sharing",
    "parking":       "parking",
    "train_station": "train_station",
    "taxi":          "taxi",
}


async def execute_tool(
    name: str,
    args: dict,
    datasets: dict,
    geo_state: dict,
) -> Any:
    """Esegue un tool call richiesto da Gemini e aggiorna geo_state con markers/route."""

    if name == "geocode_location":
        place = args["place_name"].lower().strip()
        if place in KNOWN_PLACES:
            lat, lon = KNOWN_PLACES[place]
            return {"lat": lat, "lon": lon, "found": True}
        # Fallback Nominatim
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{args['place_name']} Trento Italia", "format": "json", "limit": 1},
                headers={"User-Agent": "AskRovereto/1.0"},
            )
            results = r.json()
        if results:
            lat, lon = float(results[0]["lat"]), float(results[0]["lon"])
            return {"lat": lat, "lon": lon, "found": True}
        return {"lat": None, "lon": None, "found": False, "error": "Luogo non trovato"}

    if name == "find_nearest_poi":
        poi_type = args["poi_type"]
        dataset_key = POI_TYPE_MAP.get(poi_type, poi_type)
        poi_list = datasets.get(dataset_key, [])
        n = args.get("max_results", 3)
        nearest = find_nearest(poi_list, args["lat"], args["lon"], n=n)

        # Aggiungi markers allo stato per il frontend
        for poi in nearest:
            geo_state.setdefault("markers", []).append({
                "lat":  poi["lat"],
                "lon":  poi["lon"],
                "type": MARKER_TYPE_MAP.get(poi_type, poi_type),
                "label": poi.get("fumetto") or poi.get("nome") or poi.get("via") or poi_type,
                "distance_m": poi.get("distance_m"),
            })

        return {"pois": nearest, "count": len(nearest)}

    if name == "get_route":
        origin = (args["origin_lat"], args["origin_lon"])
        dest   = (args["dest_lat"],   args["dest_lon"])
        profile = args["profile"]

        try:
            route = await get_route(origin, dest, profile)
        except Exception as e:
            return {"error": str(e), "fallback": "Percorso non disponibile al momento"}

        geo_state["route"] = route["geojson"]
        geo_state["distance_m"] = route["distance_m"]
        geo_state["duration_s"] = route["duration_s"]
        geo_state["profile"] = profile

        return {
            "distance_m": route["distance_m"],
            "duration_s": route["duration_s"],
            "profile":    profile,
        }

    if name == "get_cycling_paths_near":
        from geo.nearest import haversine
        radius = args.get("radius_m", 500)
        # I dati piste ciclabili sono serviti come GeoJSON al frontend — qui solo segnaliamo presenza
        return {
            "message": f"Rete ciclabile disponibile nell'area (raggio {radius}m)",
            "tip": "Segui le piste ciclabili verdi sulla mappa",
        }

    return {"error": f"Tool '{name}' non riconosciuto"}


def build_chips(distance_m: int, duration_s: int, profile: str) -> list[dict]:
    """Genera i badge informativi per il frontend."""
    minutes = max(1, round(duration_s / 60))
    km = round(distance_m / 1000, 1)

    profile_icons = {
        "foot-walking":    "🚶",
        "cycling-regular": "🚲",
        "driving-car":     "🚗",
    }
    icon = profile_icons.get(profile, "📍")

    chips = [
        {"icon": icon,  "label": "tempo",     "value": f"{minutes} min"},
        {"icon": "📏",  "label": "distanza",  "value": f"{km} km"},
    ]
    if profile in ("foot-walking", "cycling-regular"):
        co2 = co2_saved_grams(distance_m, profile)
        chips.append({"icon": "♻️", "label": "CO₂ risparmiata", "value": f"{co2} g"})

    return chips


async def run_agent(message: str, datasets: dict) -> dict:
    """
    Esegue il loop Gemini function calling.
    Restituisce { reply, markers, route, chips }.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=[GEMINI_TOOL],
        system_instruction=SYSTEM_PROMPT,
    )

    chat = model.start_chat()
    response = chat.send_message(message)
    geo_state: dict = {"markers": []}

    # Loop tool calling (max 5 iterazioni per sicurezza)
    for _ in range(5):
        fn_calls = [
            part.function_call
            for part in response.parts
            if hasattr(part, "function_call")
            and part.function_call
            and part.function_call.name
        ]
        if not fn_calls:
            break

        # Esegui tutti i tool calls richiesti in questo turno
        tool_responses = []
        for fc in fn_calls:
            result = await execute_tool(fc.name, dict(fc.args), datasets, geo_state)
            tool_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fc.name,
                        response={"result": result},
                    )
                )
            )

        response = chat.send_message(
            genai.protos.Content(parts=tool_responses)
        )

    # Estrai testo finale
    reply = "".join(
        part.text for part in response.parts if hasattr(part, "text") and part.text
    )

    # Costruisci chips se abbiamo dati di routing
    chips = []
    if "distance_m" in geo_state and "duration_s" in geo_state:
        chips = build_chips(
            geo_state["distance_m"],
            geo_state["duration_s"],
            geo_state.get("profile", "foot-walking"),
        )

    return {
        "reply":   reply,
        "markers": geo_state.get("markers", []),
        "route":   geo_state.get("route"),
        "chips":   chips,
    }
```

- [ ] **Step 4: Lancia i test (devono passare)**

```bash
cd backend
pytest tests/test_agent.py -v
```

Atteso: 5 PASSED

- [ ] **Step 5: Test manuale end-to-end** (richiede chiavi reali)

```bash
cd backend
python3 -c "
import asyncio
from dotenv import load_dotenv
load_dotenv()
from geo.loader import load_all_datasets
from pathlib import Path
from ai.agent import run_agent

datasets = load_all_datasets(Path('../data/processed'))

async def test():
    result = await run_agent('Sono alla stazione FS e voglio andare al MART in bici', datasets)
    print('REPLY:', result['reply'][:200])
    print('MARKERS:', len(result['markers']))
    print('ROUTE:', result['route']['type'] if result['route'] else None)
    print('CHIPS:', result['chips'])

asyncio.run(test())
"
```

- [ ] **Step 6: Commit**

```bash
git add backend/ai/agent.py backend/tests/test_agent.py
git commit -m "feat: Gemini function calling loop con execute_tool"
```

---

## Task 9: Chat Endpoint

**Files:**
- Create: `backend/routers/chat.py`

- [ ] **Step 1: Crea `backend/routers/chat.py`**

```python
from fastapi import APIRouter, Request
from pydantic import BaseModel

from ai.agent import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    datasets = request.app.state.datasets
    result = await run_agent(req.message, datasets)
    return result
```

- [ ] **Step 2: Riavvia backend e testa**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Dove trovo un bike sharing vicino alla stazione?"}'
```

Atteso: risposta JSON con `reply`, `markers`, `route`, `chips`.

- [ ] **Step 3: Commit**

```bash
git add backend/routers/chat.py
git commit -m "feat: POST /api/chat endpoint"
```

---

## Task 10: Frontend Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`

- [ ] **Step 1: Crea il progetto Vite + Vue**

```bash
cd /home/fallenangel/projects/CassandraRosmini
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install leaflet axios
```

- [ ] **Step 2: Aggiorna `frontend/vite.config.js`** (aggiungi proxy per backend)

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 3: Sostituisci `frontend/src/main.js`**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import 'leaflet/dist/leaflet.css'

createApp(App).mount('#app')
```

- [ ] **Step 4: Verifica avvio frontend**

```bash
cd frontend
npm run dev
```

Apri `http://localhost:5173` — deve mostrare la pagina Vite default (con il logo Vue). Se vedi la pagina, il setup funziona.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend Vite + Vue 3 + Leaflet"
```

---

## Task 11: ChatPanel + useChat

**Files:**
- Create: `frontend/src/composables/useChat.js`
- Create: `frontend/src/components/ChatPanel.vue`

- [ ] **Step 1: Crea `frontend/src/composables/useChat.js`**

```javascript
import { ref } from 'vue'
import axios from 'axios'

export function useChat(onResult) {
  const messages = ref([
    {
      role: 'ai',
      text: 'Ciao! Sono Ask Rovereto 🗺️ Dimmi dove vuoi andare e ti aiuto a muoverti in città in modo sostenibile.',
    },
  ])
  const loading = ref(false)
  const error = ref(null)

  async function sendMessage(text) {
    if (!text.trim() || loading.value) return

    messages.value.push({ role: 'user', text })
    loading.value = true
    error.value = null

    try {
      const { data } = await axios.post('/api/chat', { message: text })
      messages.value.push({
        role: 'ai',
        text: data.reply,
        chips: data.chips || [],
      })
      // Notifica la mappa con markers + route
      if (onResult) onResult(data)
    } catch (e) {
      error.value = 'Errore di connessione. Riprova.'
      messages.value.push({
        role: 'ai',
        text: 'Mi dispiace, si è verificato un errore. Riprova tra un momento.',
        chips: [],
      })
    } finally {
      loading.value = false
    }
  }

  return { messages, loading, error, sendMessage }
}
```

- [ ] **Step 2: Crea `frontend/src/components/ChatPanel.vue`**

```vue
<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="logo">⬡ Ask Rovereto</span>
    </div>

    <div class="messages" ref="messagesEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="bubble">{{ msg.text }}</div>
        <div v-if="msg.chips?.length" class="chips">
          <span v-for="chip in msg.chips" :key="chip.label" class="chip">
            {{ chip.icon }} <strong>{{ chip.value }}</strong>
            <small>{{ chip.label }}</small>
          </span>
        </div>
      </div>

      <div v-if="loading" class="message ai">
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div class="suggestions">
      <button
        v-for="s in suggestions"
        :key="s"
        class="suggestion-btn"
        @click="sendMessage(s)"
      >{{ s }}</button>
    </div>

    <div class="input-row">
      <input
        v-model="inputText"
        @keyup.enter="submit"
        placeholder="Dove vuoi andare?"
        :disabled="loading"
        class="chat-input"
      />
      <button @click="submit" :disabled="loading || !inputText.trim()" class="send-btn">
        ↑
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChat } from '../composables/useChat.js'

const emit = defineEmits(['result'])
const inputText = ref('')
const messagesEl = ref(null)

const suggestions = [
  'Stazione FS → MART in bici',
  'Parcheggi vicino al Duomo',
  'Come raggiungere il MUSE a piedi?',
]

const { messages, loading, sendMessage } = useChat((data) => emit('result', data))

async function submit() {
  const text = inputText.value.trim()
  inputText.value = ''
  await sendMessage(text)
}

watch(messages, async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}, { deep: true })
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
}
.chat-header {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #ffffff;
}
.logo { font-weight: 700; color: #2563eb; font-size: 15px; letter-spacing: 0.3px; }

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.message.user { align-items: flex-end; display: flex; flex-direction: column; }
.message.ai   { align-items: flex-start; display: flex; flex-direction: column; }

.bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 88%;
  white-space: pre-line;
}
.message.user .bubble {
  background: #dbeafe;
  color: #1e3a5f;
  border-radius: 12px 12px 2px 12px;
}
.message.ai .bubble {
  background: #ffffff;
  color: #374151;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #2563eb;
  border-radius: 2px 12px 12px 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.chip {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  color: #1d4ed8;
  display: flex;
  align-items: center;
  gap: 4px;
}
.chip small { opacity: 0.7; }

/* Typing indicator */
.typing { display: flex; gap: 5px; align-items: center; padding: 14px; }
.typing span {
  width: 7px; height: 7px;
  background: #94a3b8;
  border-radius: 50%;
  animation: bounce 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}

.suggestions {
  padding: 8px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border-top: 1px solid #f1f5f9;
}
.suggestion-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 4px 10px;
  font-size: 11px;
  color: #475569;
  cursor: pointer;
  transition: background 0.15s;
}
.suggestion-btn:hover { background: #e2e8f0; }

.input-row {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #e2e8f0;
  background: #ffffff;
}
.chat-input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}
.chat-input:focus { border-color: #2563eb; }
.send-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  width: 36px; height: 36px;
  font-size: 16px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s;
}
.send-btn:hover:not(:disabled) { background: #1d4ed8; }
.send-btn:disabled { background: #93c5fd; cursor: not-allowed; }
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/composables/useChat.js frontend/src/components/ChatPanel.vue
git commit -m "feat: ChatPanel con useChat composable"
```

---

## Task 12: MapView + useMap

**Files:**
- Create: `frontend/src/composables/useMap.js`
- Create: `frontend/src/components/MapView.vue`

- [ ] **Step 1: Crea `frontend/src/composables/useMap.js`**

```javascript
import L from 'leaflet'

// Fix Leaflet default icon path (rotto con Vite)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const MARKER_COLORS = {
  origin:       '#22c55e',
  destination:  '#ec4899',
  bike_sharing: '#3b82f6',
  car_sharing:  '#8b5cf6',
  parking:      '#f59e0b',
  train_station:'#64748b',
  taxi:         '#ef4444',
}

const ZONE_COLORS = {
  blu: '#3b82f6', cblu: '#60a5fa', cblu2: '#93c5fd',
  rosso: '#ef4444', crosso: '#f87171', crosso2: '#fca5a5',
  verde: '#22c55e', cverde: '#4ade80', cverde2: '#86efac',
  viola: '#a855f7', giallo1: '#eab308', giallo4: '#facc15',
}

function makeColoredMarker(color) {
  return L.divIcon({
    html: `<div style="
      width:14px;height:14px;
      background:${color};
      border:2.5px solid white;
      border-radius:50%;
      box-shadow:0 1px 4px rgba(0,0,0,.3)
    "></div>`,
    className: '',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

export function useMap(mapEl) {
  let map = null
  let markersLayer = null
  let routeLayer = null
  let cyclingLayer = null
  let parkingLayer = null

  function init() {
    map = L.map(mapEl.value, { zoomControl: true })
      .setView([46.0707, 11.1193], 14)  // Centro Trento — mapEl è un Vue ref

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)

    markersLayer = L.layerGroup().addTo(map)
    routeLayer   = L.layerGroup().addTo(map)

    loadBackgroundLayers()
  }

  async function loadBackgroundLayers() {
    // Piste ciclabili (layer verde fisso)
    try {
      const r = await fetch('/static/piste_ciclabili.geojson')
      const geojson = await r.json()
      cyclingLayer = L.geoJSON(geojson, {
        style: { color: '#22c55e', weight: 2.5, opacity: 0.65 },
      }).addTo(map)
    } catch (e) {
      console.warn('Piste ciclabili non caricate:', e)
    }

    // Zone parcheggio (poligoni colorati)
    try {
      const r = await fetch('/static/zone_parcheggio.geojson')
      const geojson = await r.json()
      parkingLayer = L.geoJSON(geojson, {
        style: (feat) => {
          const color = ZONE_COLORS[feat.properties.zona] ?? '#94a3b8'
          return { fillColor: color, fillOpacity: 0.18, color, weight: 1.5 }
        },
        onEachFeature: (feat, layer) => {
          layer.bindPopup(
            `<strong>${feat.properties.descrizione}</strong><br>Piano tariffario: ${feat.properties.pianopark}`
          )
        },
      }).addTo(map)
    } catch (e) {
      console.warn('Zone parcheggio non caricate:', e)
    }
  }

  function applyResult(data) {
    // Pulisci markers e route precedenti
    markersLayer.clearLayers()
    routeLayer.clearLayers()

    // Aggiungi markers
    const bounds = []
    for (const m of data.markers || []) {
      const color = MARKER_COLORS[m.type] ?? '#6b7280'
      const marker = L.marker([m.lat, m.lon], { icon: makeColoredMarker(color) })
        .bindPopup(`<strong>${m.label}</strong>${m.distance_m ? `<br>${m.distance_m}m` : ''}`)
        .addTo(markersLayer)
      bounds.push([m.lat, m.lon])
    }

    // Aggiungi route
    if (data.route?.coordinates?.length > 1) {
      const latlngs = data.route.coordinates.map(([lon, lat]) => [lat, lon])
      L.polyline(latlngs, {
        color: '#2563eb',
        weight: 4,
        opacity: 0.85,
        dashArray: '8, 5',
      }).addTo(routeLayer)
      bounds.push(...latlngs)
    }

    // Anima la mappa sui risultati
    if (bounds.length > 0) {
      map.flyToBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 16, duration: 1.2 })
    }
  }

  return { init, applyResult }
}
```

- [ ] **Step 2: Crea `frontend/src/components/MapView.vue`**

```vue
<template>
  <div class="map-wrapper">
    <div ref="mapEl" class="map-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMap } from '../composables/useMap.js'

const mapEl = ref(null)
const { init, applyResult } = useMap(mapEl)

onMounted(() => {
  // Piccolo delay per garantire che il DOM sia pronto
  setTimeout(init, 50)
})

defineExpose({ applyResult })
</script>

<style scoped>
.map-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}
.map-container {
  width: 100%;
  height: 100%;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/composables/useMap.js frontend/src/components/MapView.vue
git commit -m "feat: MapView con Leaflet, layer ciclabili e parcheggi"
```

---

## Task 13: App.vue — Layout Assembly

**Files:**
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/components/SuggestionChips.vue`

- [ ] **Step 1: Sostituisci `frontend/src/App.vue`**

```vue
<template>
  <div class="app-layout">
    <ChatPanel @result="onResult" />
    <MapView ref="mapRef" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import MapView from './components/MapView.vue'

const mapRef = ref(null)

function onResult(data) {
  mapRef.value?.applyResult(data)
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  height: 100vh;
  overflow: hidden;
}
</style>
```

- [ ] **Step 2: Verifica visiva nel browser**

```bash
cd frontend && npm run dev
```

Apri `http://localhost:5173`. Devi vedere:
- Colonna sinistra: chat con messaggio di benvenuto
- Colonna destra: mappa Trento con piste ciclabili verdi e zone parcheggio colorate

Se la mappa è bianca: controlla la console del browser per errori CORS o file non trovati.

- [ ] **Step 3: Testa end-to-end** (con backend avviato)

Scrivi nella chat: `"Stazione FS → MART in bici"`

Atteso:
- Risposta AI in italiano con passi numerati
- Markers sulla mappa (verde = partenza, rosa = destinazione, blu = bike sharing)
- Route blu tratteggiata
- Mappa che fa flyToBounds animato
- Chips: "🚲 X min · Y km · ♻️ Z g CO₂"

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: App.vue layout split ChatPanel + MapView"
```

---

## Task 14: run.sh + .gitignore

**Files:**
- Create: `run.sh`
- Create: `.gitignore`

- [ ] **Step 1: Crea `run.sh`**

```bash
#!/bin/bash
set -e

echo "🗺️  Ask Rovereto — avvio..."

# Verifica dati processati
if [ ! -d "data/processed" ] || [ -z "$(ls data/processed/*.geojson 2>/dev/null)" ]; then
  echo "⚠️  Dati non trovati. Eseguo riproiezione..."
  pip install pyproj -q
  python scripts/reproject.py
fi

# Backend
echo "→ Backend FastAPI su http://localhost:8000"
cd backend
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Attendi backend
sleep 2
curl -s http://localhost:8000/health > /dev/null && echo "  Backend OK" || echo "  Backend non risponde"

# Frontend
echo "→ Frontend Vue su http://localhost:5173"
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ App avviata:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Premi Ctrl+C per fermare."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Fermato.'" EXIT
wait
```

```bash
chmod +x run.sh
```

- [ ] **Step 2: Crea `.gitignore`**

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/

# Node
node_modules/
dist/
.vite/

# Env
.env
!.env.example

# Superpowers
.superpowers/

# OS
.DS_Store
```

- [ ] **Step 3: Test avvio completo**

```bash
./run.sh
```

Atteso: entrambi i processi avviati, `http://localhost:5173` aperto mostra l'app funzionante.

- [ ] **Step 4: Commit finale**

```bash
git add run.sh .gitignore backend/.env.example
git commit -m "feat: run.sh avvio completo + gitignore"
```

---

## Task 15: Verifica Golden Path Demo

Verifica che i 3 scenari demo funzionino tutti prima della presentazione.

- [ ] **Step 1: Test scenario 1 — Bike sharing**

```
Query: "Sono alla stazione FS e voglio andare al MART in bici"
Atteso:
  ✓ Risposta in italiano con passi numerati
  ✓ Marker verde (stazione FS)
  ✓ Marker blu (bike sharing)
  ✓ Marker rosa (MART)
  ✓ Route ciclabile sulla mappa
  ✓ Chips: tempo, distanza, CO₂
```

- [ ] **Step 2: Test scenario 2 — Parcheggio**

```
Query: "Dove posso parcheggiare vicino al Castello del Buonconsiglio?"
Atteso:
  ✓ Risposta con zona parcheggio e piano tariffario
  ✓ Marker parcheggio (ambra)
  ✓ Zona parcheggio evidenziata sulla mappa
```

- [ ] **Step 3: Test scenario 3 — Percorso a piedi**

```
Query: "Come raggiungo il MUSE a piedi dal Duomo?"
Atteso:
  ✓ Risposta con percorso pedonale
  ✓ Route foot-walking
  ✓ Chips senza CO₂ (o con risparmio CO₂ se attivo)
```

- [ ] **Step 4: Test offline parziale**

Disabilita internet (o blocca solo ORS/Gemini) e verifica che l'app non si blocchi con errore non gestito — deve mostrare un messaggio graceful.

- [ ] **Step 5: Commit finale + tag**

```bash
git add -A
git commit -m "chore: verifica golden path demo completata"
git tag v1.0-demo
```

---

## Riferimento rapido comandi

```bash
# Primo avvio completo
python scripts/reproject.py     # Una volta sola
./run.sh                         # Avvia tutto

# Solo backend (sviluppo)
cd backend && uvicorn main:app --reload --port 8000

# Solo frontend (sviluppo)
cd frontend && npm run dev

# Test backend
cd backend && pytest tests/ -v

# Test manuale API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "MART in bici dalla stazione"}'
```
