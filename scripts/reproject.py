#!/usr/bin/env python3
"""Riproietta tutti i GeoJSON da EPSG:25832 (UTM 32N) a WGS84."""

import json
import sys
from pathlib import Path

from pyproj import Transformer

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "processed"

DATASETS = [
    "bike_sharing",
    "car_sharing",
    "stazioni",
    "taxi",
    "zone_parcheggio",
    "piste_ciclabili",
    "patti",
]

_transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)


def convert_coords(coords: list) -> list:
    if isinstance(coords[0], list):
        return [convert_coords(c) for c in coords]
    lon, lat = _transformer.transform(coords[0], coords[1])
    return [lon, lat]


def reproject(src: Path, dst: Path) -> int:
    with open(src) as f:
        data = json.load(f)

    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if geom and geom.get("coordinates"):
            geom["coordinates"] = convert_coords(geom["coordinates"])

    data["crs"] = None  # rimuovi dopo riproiezione — Leaflet assume WGS84

    with open(dst, "w") as f:
        json.dump(data, f)

    return len(data.get("features", []))


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name in DATASETS:
        src = DATA_DIR / f"{name}.geojson"
        dst = OUT_DIR / f"{name}.geojson"
        if not src.exists():
            print(f"  SKIP {name}.geojson (non trovato)")
            continue
        n = reproject(src, dst)
        print(f"  OK   {name}.geojson ({n} features)")

    print(f"\nFile processati in: {OUT_DIR}")


if __name__ == "__main__":
    main()
