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
    "materials": ["lambda", "mu", "rho", "c", "wlg",
                  "r_value", "u_value", "g_value"],
    "moisture_conditions": ["theta_i", "phi_i", "theta_e", "phi_e",
                            "duration_days", "rsi", "rse"],
}
GESCHUETZT_EXTRA = {
    "air_layers": [("unheated_attic_spaces", "entries", "r_u")],
    "moisture_conditions": [("diffusion", "entries", "value"),
                            ("assessment_limits", "entries", "value")],
}

# Kataloge ausserhalb von catalog/core/ mit abweichender Listen-/Schluesselform.
# Genau hier lag die Luecke: materials.json liegt eine Ebene hoeher und heisst
# seine Liste "materials" statt "entries" — der Glob auf CORE hat sie nie gesehen,
# obwohl 48 Eintraege Bemessungswerte aus DIN 4108-4 trugen.
SONDERFAELLE = {
    "materials": {"datei": "catalog/materials.json",
                  "liste": "materials", "schluessel": "id"},
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

    zu_pruefen = [(p, "entries", "code") for p in sorted(CORE.glob("*.json"))]
    for kid, konfig in SONDERFAELLE.items():
        pfad = REPO / konfig["datei"]
        if pfad.exists():
            zu_pruefen.append((pfad, konfig["liste"], konfig["schluessel"]))
        else:
            befunde.append(f"{konfig['datei']}: erwartet, aber nicht gefunden")

    for pfad, liste, schluessel in zu_pruefen:
        katalog = json.loads(pfad.read_text(encoding="utf-8"))
        kid = katalog.get("catalog_id") or pfad.stem
        felder = GESCHUETZT.get(kid)
        if not felder:
            continue

        if not (katalog.get("values_overlay") or {}).get("required"):
            befunde.append(
                f"{pfad.name}: values_overlay.required ist nicht true, obwohl der "
                f"Katalog geschuetzte Felder hat"
            )

        for eintrag in katalog.get(liste, []):
            for feld in felder:
                wert = hole(eintrag, feld)
                if isinstance(wert, (int, float)):
                    befunde.append(
                        f"{pfad.name}: {liste}[{eintrag.get(schluessel)}].{feld} "
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

    print(f"[check-catalog-structure] OK — keine Normzahlenwerte in "
          f"{len(zu_pruefen)} oeffentlichen Katalogdateien.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
