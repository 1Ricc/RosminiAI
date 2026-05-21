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
