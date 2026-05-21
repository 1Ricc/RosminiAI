import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

MOCK_DATASETS = {
    "bike_sharing": [{"lat": 45.89, "lon": 11.04, "fumetto": "Test Station"}],
    "car_sharing":  [{"lat": 45.88, "lon": 11.03, "nome": "Car A"}],
    "stazioni":     [],
    "taxi":         [],
    "parcheggi":    [],
    "patti":        [],
}


@pytest.fixture
def client():
    app.state.datasets = MOCK_DATASETS
    return TestClient(app)


def test_list_categories(client):
    r = client.get("/api/poi")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data
    assert data["categories"]["bike_sharing"] == 1
    assert data["categories"]["car_sharing"] == 1


def test_get_poi_valid_category(client):
    r = client.get("/api/poi/bike_sharing")
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "bike_sharing"
    assert len(data["items"]) == 1
    assert data["items"][0]["fumetto"] == "Test Station"


def test_get_poi_empty_category(client):
    r = client.get("/api/poi/stazioni")
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_get_poi_invalid_category(client):
    r = client.get("/api/poi/invalid_cat")
    assert r.status_code == 404
    assert "Valori ammessi" in r.json()["detail"]
