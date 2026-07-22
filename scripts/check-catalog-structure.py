#!/usr/bin/env python3
"""
check-catalog-structure.py — verhindert, dass Normzahlenwerte zurueck in den
oeffentlichen Katalog wandern.

check-catalog-values.sh sperrt die VERZEICHNISSE catalog/values/ und
catalog-private/. Dieses Skript prueft die Gegenrichtung: dass in
catalog/core/ keine Zahlen stehen, die laut values_overlay ins private
Overlay gehoeren.

Der Fall, den es faengt: jemand befuellt einen null-Platzhalter in
catalog/core/ direkt, weil es bequemer ist als das Overlay zu pflegen.
Der Verzeichnis-Guard merkt davon nichts.

Aufruf:
    python3 scripts/check-catalog-structure.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORE = REPO / "catalog" / "core"

# Muss mit FELDER in split-catalog-values.py uebereinstimmen.
GESCHUETZT = {
    "adjacency_types": ["fx.value", "fx.simplified_value"],
    "surface_resistances": ["rsi", "rse"],
    "air_layers": ["r_upward", "r_horizontal", "r_downward"],
}
GESCHUETZT_EXTRA = {
    "air_layers": [("unheated_attic_spaces", "entries", "r_u")],
}


def hole(obj: dict, pfad: str):
    ziel = obj
    for teil in pfad.split("."):
        if not isinstance(ziel, dict) or teil not in ziel:
            return None
        ziel = ziel[teil]
    return ziel


def main() -> int:
    befunde: list[str] = []

    for pfad in sorted(CORE.glob("*.json")):
        katalog = json.loads(pfad.read_text(encoding="utf-8"))
        kid = katalog.get("catalog_id")
        felder = GESCHUETZT.get(kid)
        if not felder:
            continue

        if not (katalog.get("values_overlay") or {}).get("required"):
            befunde.append(
                f"{pfad.name}: values_overlay.required ist nicht true, obwohl der "
                f"Katalog geschuetzte Felder hat"
            )

        for eintrag in katalog.get("entries", []):
            for feld in felder:
                wert = hole(eintrag, feld)
                if isinstance(wert, (int, float)):
                    befunde.append(
                        f"{pfad.name}: entries[{eintrag.get('code')}].{feld} "
                        f"= {wert} — gehoert ins private Overlay"
                    )

        for top, liste, feld in GESCHUETZT_EXTRA.get(kid, []):
            block = katalog.get(top) or {}
            for eintrag in block.get(liste, []):
                wert = eintrag.get(feld)
                if isinstance(wert, (int, float)):
                    befunde.append(
                        f"{pfad.name}: {top}.{liste}[{eintrag.get('code')}].{feld} "
                        f"= {wert} — gehoert ins private Overlay"
                    )

    if befunde:
        print("FEHLER: Normzahlenwerte im oeffentlichen Katalog gefunden.\n",
              file=sys.stderr)
        for b in befunde:
            print(f"  {b}", file=sys.stderr)
        print("\nWerte ins Overlay unter catalog/values/ verschieben:", file=sys.stderr)
        print("  python3 scripts/split-catalog-values.py", file=sys.stderr)
        return 1

    print("[check-catalog-structure] OK — keine Normzahlenwerte in catalog/core/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
