import os
from typing import Any

import httpx
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted
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
        lat, lon = None, None
        if place in KNOWN_PLACES:
            lat, lon = KNOWN_PLACES[place]
        else:
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

        if lat is None:
            return {"lat": None, "lon": None, "found": False, "error": "Luogo non trovato"}

        # Prima geocodifica = origin, seconda = destination, ulteriori = waypoint
        count = geo_state.get("_geocode_count", 0)
        geo_state["_geocode_count"] = count + 1
        marker_type = "origin" if count == 0 else "destination" if count == 1 else "waypoint"

        geo_state.setdefault("markers", []).append({
            "lat":        lat,
            "lon":        lon,
            "type":       marker_type,
            "label":      args["place_name"],
            "distance_m": None,
        })
        return {"lat": lat, "lon": lon, "found": True}

    if name == "find_nearest_poi":
        poi_type = args["poi_type"]
        dataset_key = POI_TYPE_MAP.get(poi_type, poi_type)
        poi_list = datasets.get(dataset_key, [])
        n = int(args.get("max_results", 3))
        nearest = find_nearest(poi_list, args["lat"], args["lon"], n=n)

        for poi in nearest:
            geo_state.setdefault("markers", []).append({
                "lat":        poi["lat"],
                "lon":        poi["lon"],
                "type":       MARKER_TYPE_MAP.get(poi_type, poi_type),
                "label":      poi.get("fumetto") or poi.get("nome") or poi.get("via") or poi_type,
                "distance_m": poi.get("distance_m"),
            })

        return {"pois": nearest, "count": len(nearest)}

    if name == "get_route":
        origin  = (args["origin_lat"], args["origin_lon"])
        dest    = (args["dest_lat"],   args["dest_lon"])
        profile = args["profile"]

        try:
            route = await get_route(origin, dest, profile)
        except Exception as e:
            return {"error": str(e), "fallback": "Percorso non disponibile al momento"}

        geo_state["route"]      = route["geojson"]
        geo_state["distance_m"] = route["distance_m"]
        geo_state["duration_s"] = route["duration_s"]
        geo_state["profile"]    = profile

        return {
            "distance_m": route["distance_m"],
            "duration_s": route["duration_s"],
            "profile":    profile,
        }

    if name == "get_cycling_paths_near":
        radius = args.get("radius_m", 500)
        return {
            "message": f"Rete ciclabile disponibile nell'area (raggio {radius}m)",
            "tip":     "Segui le piste ciclabili verdi sulla mappa",
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
        {"icon": icon,  "label": "tempo",    "value": f"{minutes} min"},
        {"icon": "📏",  "label": "distanza", "value": f"{km} km"},
    ]
    if profile in ("foot-walking", "cycling-regular"):
        co2 = co2_saved_grams(distance_m, profile)
        chips.append({"icon": "♻️", "label": "CO₂ risparmiata", "value": f"{co2} g"})

    return chips


async def get_fallback_response() -> dict:
    """Risposta demo durante cooldown Gemini: percorso ciclabile Stazione FS → MART."""
    origin = KNOWN_PLACES["stazione rovereto"]
    destination = KNOWN_PLACES["mart"]
    profile = "cycling-regular"

    markers = [
        {"lat": origin[0],      "lon": origin[1],      "type": "origin",      "label": "Stazione FS Rovereto", "distance_m": None},
        {"lat": destination[0], "lon": destination[1], "type": "destination", "label": "MART",                 "distance_m": None},
    ]
    reply = (
        "Ecco un percorso ciclabile di esempio: Stazione FS Rovereto → MART.\n\n"
        "1. Parti dalla Stazione Ferroviaria di Rovereto in bici.\n"
        "2. Imbocca Corso Rosmini verso il centro.\n"
        "3. Svolta su Corso Bettini.\n"
        "4. Arrivi al MART – Museo di Arte Moderna e Contemporanea di Rovereto.\n\n"
        "⚠️ Il servizio AI è temporaneamente in pausa (quota esaurita). "
        "Questa è una risposta di esempio — riprova tra qualche minuto."
    )

    try:
        route_data = await get_route(origin, destination, profile)
        return {
            "reply":   reply,
            "markers": markers,
            "route":   route_data["geojson"],
            "chips":   build_chips(route_data["distance_m"], route_data["duration_s"], profile),
        }
    except Exception:
        return {"reply": reply, "markers": markers, "route": None, "chips": []}


async def run_agent(message: str, datasets: dict) -> dict:
    """
    Esegue il loop Gemini function calling.
    Restituisce { reply, markers, route, chips }.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=[GEMINI_TOOL],
        system_instruction=SYSTEM_PROMPT,
    )

    chat = model.start_chat()
    try:
        response = chat.send_message(message)
        geo_state: dict = {"markers": []}

        # Loop tool calling — max 5 iterazioni per sicurezza
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

    except (ResourceExhausted, GoogleAPIError, Exception):
        return await get_fallback_response()

    reply = "".join(
        part.text for part in response.parts if hasattr(part, "text") and part.text
    )

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
