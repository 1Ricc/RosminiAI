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
