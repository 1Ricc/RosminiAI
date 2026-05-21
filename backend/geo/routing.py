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
            [origin[1], origin[0]],           # ORS vuole [lon, lat]
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
        "geojson": feature["geometry"],            # LineString per Leaflet
        "distance_m": round(summary["distance"]),
        "duration_s": round(summary["duration"]),
    }


def co2_saved_grams(distance_m: float, profile: str) -> int:
    """CO₂ risparmiato rispetto a un'auto (210g/km) per modalità sostenibili."""
    if profile not in ("foot-walking", "cycling-regular"):
        return 0
    return round(distance_m * 0.21)
