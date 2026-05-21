OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": (
                "Converte il nome di un luogo (es. 'Stazione FS', 'MART', 'Piazza Duomo') "
                "in coordinate latitudine/longitudine. Usare SEMPRE prima di cercare POI vicini."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "Nome del luogo da geocodificare",
                    },
                },
                "required": ["place_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest_poi",
            "description": (
                "Trova i punti di interesse più vicini a una posizione geografica. "
                "Usare per trovare bike sharing, car sharing, parcheggi, stazioni, taxi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitudine WGS84"},
                    "lon": {"type": "number", "description": "Longitudine WGS84"},
                    "poi_type": {
                        "type": "string",
                        "enum": ["bike_sharing", "car_sharing", "parking", "train_station", "taxi"],
                        "description": "Tipo di POI da cercare",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Numero massimo di risultati (default 3)",
                    },
                },
                "required": ["lat", "lon", "poi_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_route",
            "description": (
                "Calcola un percorso tra due coordinate usando OpenRouteService. "
                "Usare dopo aver trovato le coordinate di origine e destinazione."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_lat": {"type": "number", "description": "Latitudine punto di partenza"},
                    "origin_lon": {"type": "number", "description": "Longitudine punto di partenza"},
                    "dest_lat":   {"type": "number", "description": "Latitudine destinazione"},
                    "dest_lon":   {"type": "number", "description": "Longitudine destinazione"},
                    "profile": {
                        "type": "string",
                        "enum": ["foot-walking", "cycling-regular", "driving-car"],
                        "description": "Modalità di trasporto",
                    },
                },
                "required": ["origin_lat", "origin_lon", "dest_lat", "dest_lon", "profile"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cycling_paths_near",
            "description": "Restituisce se ci sono piste ciclabili vicino a un punto. Utile per suggerire percorsi in bici.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "radius_m": {
                        "type": "integer",
                        "description": "Raggio ricerca in metri (default 500)",
                    },
                },
                "required": ["lat", "lon"],
            },
        },
    },
]
