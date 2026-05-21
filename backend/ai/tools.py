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
                    description="Nome del luogo da geocodificare",
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
                "origin_lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitudine punto di partenza"),
                "origin_lon": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitudine punto di partenza"),
                "dest_lat":   genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitudine destinazione"),
                "dest_lon":   genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitudine destinazione"),
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
                "radius_m": genai.protos.Schema(
                    type=genai.protos.Type.INTEGER,
                    description="Raggio ricerca in metri (default 500)",
                ),
            },
            required=["lat", "lon"],
        ),
    ),
]

GEMINI_TOOL = genai.protos.Tool(function_declarations=TOOL_DECLARATIONS)
