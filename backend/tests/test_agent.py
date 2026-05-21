import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from ai.agent import execute_tool, build_chips, get_fallback_response


@pytest.mark.asyncio
async def test_execute_tool_geocode_known_place():
    datasets = {}
    result = await execute_tool("geocode_location", {"place_name": "stazione trento"}, datasets, {})
    assert result["found"] is True
    assert 46.05 < result["lat"] < 46.09
    assert 11.10 < result["lon"] < 11.15


@pytest.mark.asyncio
async def test_execute_tool_geocode_unknown_place():
    datasets = {}
    with patch("ai.agent.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MagicMock(json=MagicMock(return_value=[]))
        )
        result = await execute_tool("geocode_location", {"place_name": "luogo_inesistente_xyz"}, datasets, {})
    assert result["found"] is False


@pytest.mark.asyncio
async def test_execute_tool_find_nearest_bike():
    datasets = {
        "bike_sharing": [
            {"lat": 46.07, "lon": 11.12, "fumetto": "Test Station", "cicloposteggi": 8},
            {"lat": 46.09, "lon": 11.14, "fumetto": "Far Station", "cicloposteggi": 4},
        ]
    }
    result = await execute_tool(
        "find_nearest_poi",
        {"lat": 46.07, "lon": 11.12, "poi_type": "bike_sharing", "max_results": 1},
        datasets,
        {},
    )
    assert len(result["pois"]) == 1
    assert result["pois"][0]["fumetto"] == "Test Station"


def test_build_chips_cycling():
    chips = build_chips(distance_m=1200, duration_s=420, profile="cycling-regular")
    labels = [c["label"] for c in chips]
    assert "tempo" in labels
    assert "distanza" in labels
    assert "CO₂ risparmiata" in labels


def test_build_chips_car_no_co2():
    chips = build_chips(distance_m=2000, duration_s=300, profile="driving-car")
    labels = [c["label"] for c in chips]
    assert "CO₂ risparmiata" not in labels


@pytest.mark.asyncio
async def test_fallback_muse_message_returns_trento_route():
    """Con messaggio contenente 'muse', il fallback usa Trento FS → MUSE."""
    with patch("ai.agent.get_route", new_callable=AsyncMock) as mock_route:
        mock_route.return_value = {
            "geojson": {"type": "LineString", "coordinates": []},
            "distance_m": 2000,
            "duration_s": 1500,
        }
        result = await get_fallback_response("da FS trento a MUSE")

    labels = [m["label"] for m in result["markers"]]
    assert any("MUSE" in l or "Trento" in l for l in labels)
    assert result["is_fallback"] is True
    assert "MUSE" in result["reply"]
    assert len(result["chips"]) == 3  # tempo, distanza, CO₂


@pytest.mark.asyncio
async def test_fallback_default_message_returns_rovereto_route():
    """Senza keyword MUSE, il fallback usa Rovereto FS → MART (comportamento esistente)."""
    with patch("ai.agent.get_route", new_callable=AsyncMock) as mock_route:
        mock_route.return_value = {
            "geojson": {"type": "LineString", "coordinates": []},
            "distance_m": 1200,
            "duration_s": 360,
        }
        result = await get_fallback_response("")

    labels = [m["label"] for m in result["markers"]]
    assert any("Rovereto" in l or "MART" in l for l in labels)
    assert result["is_fallback"] is True


@pytest.mark.asyncio
async def test_fallback_muse_ors_failure_returns_hardcoded_chips():
    """Se ORS fallisce nel fallback MUSE, i chips hardcoded vengono usati (non lista vuota)."""
    with patch("ai.agent.get_route", new_callable=AsyncMock) as mock_route:
        mock_route.side_effect = Exception("ORS non disponibile")
        result = await get_fallback_response("voglio andare al museo delle scienze")

    assert result["is_fallback"] is True
    assert len(result["chips"]) == 3  # tempo, distanza, CO₂ hardcoded
    assert result["route"] is None
