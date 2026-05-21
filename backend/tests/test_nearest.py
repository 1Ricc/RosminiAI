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
