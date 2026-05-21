# Ask Rovereto — Design Spec
**Data:** 2026-05-21
**Contesto:** Hackathon 7 ore — "AI + Open Data per la PA Digitale"
**Team:** 3 persone

---

## 1. Problema e Obiettivo

I portali open data della PA esistono ma sono inaccessibili ai cittadini comuni. Il Comune di Trento pubblica dataset di mobilità urbana (bike sharing, piste ciclabili, zone parcheggio, stazioni) che nessuno sa come usare.

**Ask Rovereto** è un assistente AI con chat + mappa che trasforma questi open data in risposte concrete in linguaggio naturale. Un cittadino scrive "voglio andare al MART senza usare l'auto" e ottiene un percorso reale con indicazioni step-by-step.

---

## 2. Stack Tecnico

| Layer | Tecnologia | Note |
|---|---|---|
| Frontend | Vue 3 + Vite | Familiarità del team |
| Mappa | Leaflet.js | Open source, zero costi |
| Backend | FastAPI (Python) | Avvio rapido, librerie geospatiali mature |
| AI | Gemini API (`gemini-2.0-flash`) | API key disponibile, function calling nativo |
| Routing | OpenRouteService API | Gratuito, endpoint REST, profili multi-modali |
| Dati | GeoJSON in-memory | Caricati all'avvio, riproiettati da EPSG:25832 |

---

## 3. Dataset Utilizzati

Tutti i file sono in EPSG:25832 (UTM Zone 32N). Un unico transformer `pyproj` li converte in WGS84 all'avvio.

| File | Features | Geometria | Uso |
|---|---|---|---|
| `bike_sharing.geojson` | 39 | Point | POI + nearest neighbor |
| `car_sharing.geojson` | 8 | Point | POI |
| `stazioni.geojson` | 10 | Point | POI (treni + ferrovia) |
| `taxi.geojson` | 9 | Point | POI (ha già WGS84 in `x`,`y`) |
| `zone_parcheggio.geojson` | 12 | Polygon | Layer visivo + ricerca parcheggio |
| `piste_ciclabili.geojson` | 280 | LineString | Layer visivo + contesto bici |
| `patti.geojson` | 91 | Point | POI culturali opzionali |

Dataset esclusi per dimensione eccessiva: `territorio_line` (141K), `territorio_polygon` (66K), `isosec` (38K), `usosuolo_view` (12K), `grafo_web` (5K).

---

## 4. Architettura

```
[Vue 3 Frontend]
  ChatPanel.vue   ←→   POST /chat   ←→   [FastAPI Backend]
  MapView.vue          GET /static/            ├── ai/agent.py      (Gemini loop)
                                               ├── geo/loader.py    (GeoJSON → WGS84)
                                               ├── geo/nearest.py   (haversine)
                                               └── geo/routing.py   (ORS client)
                                                        ↕
                                               [Gemini API]  [ORS API]
```

### Flusso richiesta

1. Utente scrive messaggio in italiano
2. `POST /chat` riceve `{ message: string }`
3. `ai/agent.py` invia a Gemini con 4 tool disponibili
4. Gemini chiama tool (max 3 iterazioni)
5. Backend esegue tool: `find_nearest_poi`, `get_route`, `geocode_location`, `get_cycling_paths_near`
6. Gemini riceve risultati, compone risposta in italiano
7. Backend restituisce `{ reply, markers[], route, chips }`
8. Frontend aggiorna chat + mappa in simultanea

---

## 5. AI Design

### Modello
`gemini-2.0-flash` — veloce, economico, function calling affidabile.

### Tool disponibili

```python
tools = [
    {
        "name": "find_nearest_poi",
        "description": "Trova i punti di interesse più vicini a una posizione.",
        "parameters": {
            "type": "object",
            "properties": {
                "lat":      {"type": "number"},
                "lon":      {"type": "number"},
                "poi_type": {"type": "string", "enum": ["bike_sharing","car_sharing","parking","train_station","taxi","cycling_path"]},
                "max_results": {"type": "integer", "default": 3}
            },
            "required": ["lat", "lon", "poi_type"]
        }
    },
    {
        "name": "get_route",
        "description": "Calcola un percorso tra due coordinate via OpenRouteService.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin_lat":  {"type": "number"},
                "origin_lon":  {"type": "number"},
                "dest_lat":    {"type": "number"},
                "dest_lon":    {"type": "number"},
                "profile":     {"type": "string", "enum": ["foot-walking","cycling-regular","driving-car"]}
            },
            "required": ["origin_lat","origin_lon","dest_lat","dest_lon","profile"]
        }
    },
    {
        "name": "geocode_location",
        "description": "Converte un nome di luogo (es. 'Stazione FS', 'MART') in coordinate lat/lon.",
        "parameters": {
            "type": "object",
            "properties": {
                "place_name": {"type": "string"}
            },
            "required": ["place_name"]
        }
    },
    {
        "name": "get_cycling_paths_near",
        "description": "Restituisce le piste ciclabili vicine a un punto.",
        "parameters": {
            "type": "object",
            "properties": {
                "lat":      {"type": "number"},
                "lon":      {"type": "number"},
                "radius_m": {"type": "integer", "default": 500}
            },
            "required": ["lat", "lon"]
        }
    }
]
```

### System prompt

```
Sei un assistente di mobilità urbana per la città di Trento.
Aiuti cittadini e turisti a muoversi in modo sostenibile.

REGOLE:
- Rispondi sempre in italiano
- Preferisci modalità sostenibili (bici > piedi > auto)
- Usa geocode_location quando l'utente menziona un luogo
- Usa find_nearest_poi per trovare opzioni di mobilità vicine
- Usa get_route per calcolare il percorso
- Rispondi con passi numerati (1. ... 2. ... 3. ...)
- Non inventare distanze o indirizzi: usa sempre i tool
- Se un luogo non è riconosciuto, chiedi chiarimenti
```

### Geocoding dei luoghi (dizionario hardcoded)

I 20 luoghi più citati da pre-mappare con coordinate WGS84:

```python
KNOWN_PLACES = {
    "stazione fs": (46.0707, 11.1193),
    "stazione trento": (46.0707, 11.1193),
    "stazione ftm": (46.0714, 11.1198),
    "mart": (46.0669, 11.1236),
    "museo mart": (46.0669, 11.1236),
    "piazza duomo": (46.0668, 11.1213),
    "duomo": (46.0668, 11.1213),
    "castello del buonconsiglio": (46.0725, 11.1261),
    "buonconsiglio": (46.0725, 11.1261),
    "muse": (46.0613, 11.1164),
    "museo delle scienze": (46.0613, 11.1164),
    "piedicastello": (46.0731, 11.1100),
    "centro storico": (46.0668, 11.1213),
    "via roma": (46.0672, 11.1220),
    "trento nord": (46.0835, 11.1183),
    "villazzano": (46.0544, 11.1411),
    "gardolo": (46.0932, 11.1222),
    "mattarello": (45.9997, 11.1278),
    "aeroporto": (46.0183, 11.1211),
    "povo": (46.0664, 11.1506),
}
```

Fallback per luoghi non noti: Nominatim geocoding API (`https://nominatim.openstreetmap.org/search?q={place}+Trento&format=json`), gratuito, no key.

---

## 6. Geospatial Logic

### Conversione coordinate

```python
from pyproj import Transformer
_t = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)

def utm_to_wgs84(x: float, y: float) -> tuple[float, float]:
    lon, lat = _t.transform(x, y)
    return lat, lon
```

**Nota:** `taxi.geojson` ha già WGS84 nei campi `x` (lat) e `y` (lon) — non riproiettare.

### Riproiezione GeoJSON completo (script pre-processamento)

```python
def reproject_geojson(input_path, output_path):
    with open(input_path) as f:
        data = json.load(f)
    def convert_coords(coords):
        if isinstance(coords[0], list):
            return [convert_coords(c) for c in coords]
        lon, lat = _t.transform(coords[0], coords[1])
        return [lon, lat]
    for feature in data["features"]:
        feature["geometry"]["coordinates"] = convert_coords(
            feature["geometry"]["coordinates"]
        )
    data["crs"] = None
    with open(output_path, "w") as f:
        json.dump(data, f)
```

### Nearest neighbor

```python
import math

def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def find_nearest(poi_list, lat, lon, n=3):
    scored = sorted(
        [(haversine(lat, lon, p["lat"], p["lon"]), p) for p in poi_list],
        key=lambda x: x[0]
    )
    return [{"distance_m": round(d), **p} for d, p in scored[:n]]
```

### ORS Client

```python
import httpx

ORS_BASE = "https://api.openrouteservice.org/v2/directions"

async def get_route(origin, destination, profile, api_key):
    url = f"{ORS_BASE}/{profile}/geojson"
    payload = {
        "coordinates": [
            [origin[1], origin[0]],       # ORS vuole [lon, lat]
            [destination[1], destination[0]]
        ],
        "instructions": False
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(url, json=payload, headers={"Authorization": api_key})
        r.raise_for_status()
        feat = r.json()["features"][0]
        return {
            "geojson":    feat["geometry"],
            "distance_m": feat["properties"]["summary"]["distance"],
            "duration_s": feat["properties"]["summary"]["duration"]
        }
```

---

## 7. API Backend

```
GET  /health
     → { status: "ok", datasets_loaded: 7, features_count: {...} }

POST /chat
     Body:    { message: string }
     Returns: {
       reply:   string,              # testo risposta AI in italiano
       markers: [                    # punti da mostrare sulla mappa
         { lat, lon, type, label, distance_m? }
       ],
       route:   Feature | null,      # GeoJSON LineString per Leaflet
       chips:   [                    # badge informativi (calcolati dal backend, non da Gemini)
         { icon, label, value }      # es. { icon:"🚲", label:"tempo", value:"7 min" }
         # CO₂ risparmiato: co2_saved_g = route.distance_m * 0.21  (vs auto media 210g/km)
         # Mostrato solo per profili foot-walking e cycling-regular
       ]
       # Nota: la risposta è sincrona (no streaming) per semplicità.
       # Lo streaming Gemini è opzionale e va implementato solo se rimane tempo all'ora 4.
     }

GET  /static/{filename}.geojson
     → serve i GeoJSON WGS84 processati (piste_ciclabili, zone_parcheggio)
```

---

## 8. Frontend

### Layout (Layout A — Sidebar + Mappa)

```
┌─────────────────────────────────────────────┐
│  ⬡ Ask Rovereto              [Light Civic]  │
├──────────────┬──────────────────────────────┤
│  ChatPanel   │  MapView (Leaflet)            │
│  (35%)       │  (65%)                        │
│              │                               │
│  [msg AI]    │  [OSM tiles]                  │
│  [msg user]  │  [layer: piste ciclabili]     │
│              │  [layer: zone parcheggio]     │
│  [chips]     │  [markers: POI]               │
│              │  [polyline: route]            │
│  [input ↑]   │                               │
└──────────────┴──────────────────────────────┘
```

### Tema visivo: Light Civic

- Background: `#f8fafc` (sidebar), OSM default tiles (mappa)
- Accent: `#2563eb` (blu istituzionale)
- Messaggio utente: `#dbeafe` bubble, allineato a destra
- Messaggio AI: bianco con bordo sinistro blu, shadow leggera
- Chips: `#eff6ff` con testo blu, bordo `#bfdbfe`
- Font: system-ui (zero dipendenze)

### Marker colori per tipo

```javascript
const MARKER_COLORS = {
  origin:       '#22c55e',   // verde — punto di partenza
  destination:  '#ec4899',   // rosa — destinazione
  bike_sharing: '#3b82f6',   // blu
  car_sharing:  '#8b5cf6',   // viola
  parking:      '#f59e0b',   // ambra
  train_station:'#64748b',   // grigio
  taxi:         '#ef4444',   // rosso
}
```

### Zone parcheggio colori

```javascript
const ZONE_COLORS = {
  blu: '#3b82f6', cblu: '#60a5fa', cblu2: '#93c5fd',
  rosso: '#ef4444', crosso: '#f87171', crosso2: '#fca5a5',
  verde: '#22c55e', cverde: '#4ade80', cverde2: '#86efac',
  viola: '#a855f7', giallo1: '#eab308', giallo4: '#facc15',
}
```

### Comportamenti mappa

- All'avvio: carica layer piste ciclabili (verde, `opacity: 0.6`) + zone parcheggio (semitrasparenti)
- Dopo risposta AI: `map.flyToBounds(routeBounds, { padding: [40,40] })`
- Marker con popup: nome + distanza + tipo
- Route: `L.polyline` blu tratteggiato, `weight: 4`

---

## 9. Struttura Cartelle

```
ask-rovereto/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.vue
│   │   │   ├── MapView.vue
│   │   │   └── SuggestionChips.vue
│   │   ├── composables/
│   │   │   ├── useChat.js
│   │   │   └── useMap.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── public/
│   └── vite.config.js
│
├── backend/
│   ├── main.py
│   ├── routers/chat.py
│   ├── geo/
│   │   ├── loader.py
│   │   ├── converter.py
│   │   ├── nearest.py
│   │   └── routing.py
│   ├── ai/
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── prompt.py
│   └── requirements.txt
│
├── data/
│   ├── *.geojson                  (originali EPSG:25832)
│   └── processed/                 (WGS84, generati da scripts/reproject.py)
│
├── scripts/
│   └── reproject.py
│
├── .env
├── .env.example
└── run.sh
```

---

## 10. Roadmap 7 Ore

| Ora | Dev A (Frontend) | Dev B (Backend/AI) | Dev C (Dati/QA) |
|---|---|---|---|
| 1 | Vite scaffold, Leaflet base, OSM tiles | FastAPI scaffold, `/health`, CORS | `scripts/reproject.py`, verifica su geojson.io |
| 2 | `MapView.vue` con layer piste+parcheggi, `ChatPanel.vue` statico | `geo/` (loader, nearest, routing ORS) | Test loader, fixture JSON |
| 3 | Connette frontend a `/chat`, typing indicator | `ai/agent.py` con Gemini + 4 tool, loop | Test end-to-end, log tool calls |
| 4 | Marker custom, `flyToBounds`, popup, chips UI | Streaming Gemini, geocoding dizionario | 10 query stress test, fix bug |
| 5 | Query suggerite cliccabili, polish UI | Edge case handling, errori graceful | 5 golden path testati e documentati |
| 6 | `run.sh`, slide pitch (5 slide) | Fix bug, `docker-compose` opzionale | README, screenshot |
| 7 | Rehearsal ×3 | Rehearsal ×3 | Rehearsal ×3 |

---

## 11. Script Demo (2 minuti)

```
[0:00] App aperta — mappa Trento con piste ciclabili e zone parcheggio visibili
       "Ask Rovereto usa open data del Comune per aiutare i cittadini a muoversi"

[0:20] Query: "Sono alla stazione FS, voglio raggiungere il MART senza usare l'auto"
       → AI risponde in streaming, mappa si anima con flyTo + markers + route

[0:50] Mostra chips: "🚲 7 min · 1.2 km · ♻️ 0.3 kg CO₂ risparmiati"
       "Usa piste ciclabili ufficiali del Comune — dati reali, non strade generiche"

[1:10] Query: "Dove posso parcheggiare vicino al Castello del Buonconsiglio?"
       → zona parcheggio evidenziata sulla mappa, piano tariffario nella risposta

[1:35] "Zero costi di licenza — tutto open data aggiornabile dalla PA autonomamente"

[1:50] "3 sviluppatori, 7 ore, open data pubblici. Questo è il potenziale della PA digitale."
```

---

## 12. Rischi e Fallback

| Rischio | Fallback |
|---|---|
| ORS timeout/rate limit | Cache percorsi, risposta testuale senza mappa |
| Gemini tool calling errato | Fix prompt, test pre-demo con 5 query fisse |
| CORS errori | `CORSMiddleware` FastAPI — 3 righe |
| Coordinate sbagliate | Verifica su geojson.io subito dopo `reproject.py` |
| No internet alla demo | Dati in memoria OK, solo ORS+Gemini richiedono rete |
| Large GeoJSON blocca browser | NON caricare territorio_line/polygon — usare solo i 7 dataset elencati |

---

## 13. Pitch

**Elevator pitch:** I Comuni hanno già tutti i dati. Manca solo l'interfaccia che li rende accessibili. Ask Rovereto è quella interfaccia — un LLM sopra gli open data esistenti, zero nuova infrastruttura.

**Impatto PA:** Riuso immediato di asset esistenti. Aggiornamento autonomo. Zero vendor lock-in.

**Impatto cittadino:** Mobilità sostenibile spiegata in italiano, contestuale, senza navigare 5 portali.

**Estensibilità:** GTFS per orari bus, eventi culturali, segnalazioni guasti — stessa architettura.
