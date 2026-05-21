#!/usr/bin/env python3
"""Verifica interattiva delle coordinate di luoghi_interesse.geojson.
Apre ogni luogo su OSM, chiede conferma, raccoglie correzioni e aggiorna il file.
"""

import json
import subprocess
from pathlib import Path

GEOJSON = Path(__file__).parent.parent / "data/processed/luoghi_interesse.geojson"


def main():
    with open(GEOJSON) as f:
        data = json.load(f)

    features = data["features"]
    corrections = 0

    print(f"\nVerifica {len(features)} luoghi — premi Invio se corretto, 'n' se sbagliato.\n")

    for feat in features:
        p = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        nome = p.get("nome", "?")
        url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=17"

        subprocess.Popen(["xdg-open", url])
        risposta = input(f"  {nome:<40} corretto? [Invio = sì / n = no]: ").strip().lower()

        if risposta == "n":
            try:
                new_lat = float(input(f"    Nuova latitudine  (attuale {lat}): ").strip())
                new_lon = float(input(f"    Nuova longitudine (attuale {lon}): ").strip())
                feat["geometry"]["coordinates"] = [new_lon, new_lat]
                print(f"    ✓ Aggiornato: [{new_lat}, {new_lon}]")
                corrections += 1
            except ValueError:
                print("    ! Valore non valido, coordinata non modificata.")

    if corrections > 0:
        with open(GEOJSON, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ {corrections} correzioni salvate in {GEOJSON}")
    else:
        print("\n✅ Nessuna correzione necessaria.")


if __name__ == "__main__":
    main()
