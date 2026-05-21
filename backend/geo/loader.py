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


def _load_geojson_polygons(path: Path) -> list[dict]:
    """Carica poligoni WGS84 calcolando il centroide dalla bounding box."""
    if not path.exists():
        print(f"  WARN: {path.name} non trovato, skip")
        return []
    with open(path) as f:
        data = json.load(f)
    result = []
    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        props = feat.get("properties", {})
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        coords = geom["coordinates"]
        if geom["type"] == "MultiPolygon":
            flat = [c for ring in coords for poly in ring for c in poly]
        else:
            flat = [c for ring in coords for c in ring]
        lons = [c[0] for c in flat]
        lats = [c[1] for c in flat]
        lat = (min(lats) + max(lats)) / 2
        lon = (min(lons) + max(lons)) / 2
        result.append({"lat": lat, "lon": lon, **props})
    return result


def load_all_datasets(data_dir: Path) -> dict:
    """Carica tutti i dataset in memoria. Chiamato una volta sola all'avvio."""
    return {
        "bike_sharing":  _load_geojson_points(data_dir / "bike_sharing.geojson"),
        "car_sharing":   _load_geojson_points(data_dir / "car_sharing.geojson"),
        "stazioni":      _load_geojson_points(data_dir / "stazioni.geojson"),
        "taxi":          _load_taxi(data_dir / "taxi.geojson"),
        "parcheggi":     _load_geojson_polygons(data_dir / "zone_parcheggio.geojson"),
        "patti":         _load_geojson_points(data_dir / "patti.geojson"),
    }
