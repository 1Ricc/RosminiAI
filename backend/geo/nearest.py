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
