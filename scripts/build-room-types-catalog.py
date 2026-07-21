#!/usr/bin/env python3
"""
build-room-types-catalog.py — erzeugt catalog/core/room_types.json

Raumtypen als FLACHE Liste mit applicability-Feld (Entscheidung 6.5).

Zwei Quellen:
  1. NWG-Typen — 1:1 aus den DIN-18599-10-Nutzungsprofilen abgeleitet. Fuer
     Nichtwohngebaeude entspricht der Raumtyp in der Praxis genau dem
     Nutzungsprofil, das Mapping ist damit belegt und nicht geraten.
  2. WG-Typen — DWE-eigene Definitionen aus der Baupraxis. Wohngebaeude werden
     nach DIN 18599 ueber die zwei Profile R1/R2 auf ZONEN-Ebene bilanziert;
     eine Raumtypisierung darunter braucht die Norm nicht, die Heizlast und die
     Wohnflaechenermittlung dagegen schon.

BEWUSST NICHT BEFUELLT: din_277_category und theta_heizlast_standard_c.
Beides sind Normgroessen (DIN 277-1 bzw. DIN EN 12831), fuer die im Repo keine
belegte Quelle vorliegt. null heisst hier "noch nicht belegt" — siehe
docs/v4/KATALOG_FORMAT.md, offene Punkte.

Aufruf:
    python3 scripts/build-room-types-catalog.py
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Wohngebaeude-Raumtypen. heating_status und counts_as_living_area sind
# DWE-eigene Vorbelegungen aus der Baupraxis (WoFlV-Logik), keine Normwerte.
WG_TYPEN = [
    # code,            name_de,             heating,      wohnflaeche, keywords
    ("WOHNEN",         "Wohnen",            "heated",     True,  ["wohn", "living", "wohnzimmer"]),
    ("SCHLAFEN",       "Schlafen",          "heated",     True,  ["schlaf", "bedroom", "kinderzimmer"]),
    ("KUECHE",         "Kueche",            "heated",     True,  ["kueche", "küche", "kitchen"]),
    ("ESSEN",          "Essen",             "heated",     True,  ["essen", "esszimmer", "dining"]),
    ("ARBEITEN",       "Arbeiten",          "heated",     True,  ["arbeit", "buero", "büro", "study"]),
    ("BAD",            "Bad",               "heated",     True,  ["bad", "bath", "duschbad"]),
    ("WC",             "WC",                "heated",     True,  ["wc", "gaeste-wc", "toilette"]),
    ("FLUR",           "Flur / Diele",      "heated",     True,  ["flur", "diele", "gang", "corridor"]),
    ("TREPPENHAUS",    "Treppenhaus",       "heated",     True,  ["treppe", "treppenhaus", "stair"]),
    ("ABSTELL",        "Abstellraum",       "heated",     True,  ["abstell", "hwr", "storage"]),
    ("TECHNIK",        "Technikraum",       "low_heated", False, ["technik", "heizung", "hausanschluss"]),
    ("KELLER",         "Keller",            "unheated",   False, ["keller", "basement"]),
    ("GARAGE",         "Garage / Carport",  "unheated",   False, ["garage", "carport", "stellplatz"]),
    ("DACHBODEN",      "Dachboden",         "unheated",   False, ["dachboden", "spitzboden", "attic"]),
]


def main() -> int:
    quelle = json.loads(
        (REPO / "catalog" / "din18599_usage_profiles.json").read_text(encoding="utf-8")
    )

    entries = []

    for code, name, heating, wohnflaeche, keywords in WG_TYPEN:
        entries.append({
            "code": code,
            "name_de": name,
            "applicability": ["WG"],
            "mapping": {
                # Wohngebaeude werden auf Zonenebene ueber R1/R2 bilanziert.
                # Die Zuordnung geschieht an der Zone, nicht am Raumtyp.
                "din_18599_profile": None,
                "din_277_category": None,
                "geg_category": None,
            },
            "defaults": {
                "heating_status": heating,
                "theta_heizlast_standard_c": None,
                "counts_as_living_area": wohnflaeche,
            },
            "suggestion_keywords": keywords,
            "value_source": "dwe_definition",
            "note": "DWE-eigene Definition aus der Baupraxis. din_277_category und "
                    "theta_heizlast_standard_c sind Normgroessen und noch nicht belegt.",
        })

    for profil in quelle["non_residential_profiles"]:
        nummer = profil["number"]
        name = profil["name_de"]
        code = f"NWG_{nummer}"
        entries.append({
            "code": code,
            "name_de": name,
            "name_en": profil.get("name_en", ""),
            "applicability": ["NWG"],
            "mapping": {
                "din_18599_profile": f"NWG_{nummer}",
                "din_277_category": None,
                "geg_category": None,
            },
            "defaults": {
                "heating_status": "heated",
                "theta_heizlast_standard_c": None,
                "counts_as_living_area": False,
            },
            "suggestion_keywords": [name.lower()],
            "value_source": "derived",
            "derived_from": "catalog/core/usage_profiles.2018-09.json",
        })

    katalog = {
        "$schema_ref": "https://din18599-ifc.de/schema/v4.0/catalog-envelope",
        "catalog_id": "room_types",
        "catalog_version": "0.1.0",
        "catalog_source": "core",
        "dimension": {"type": "none"},
        "title": "Raumtypen (flach, mit applicability)",
        "description": (
            "Raumtypen fuer rooms[].room_type_ref. Flache Liste mit applicability "
            "statt getrennter WG-/NWG-Listen (Entscheidung 6.5). NWG-Eintraege sind "
            "1:1 aus den Nutzungsprofilen abgeleitet, WG-Eintraege sind DWE-eigene "
            "Definitionen aus der Baupraxis."
        ),
        "last_updated": "2026-07-21",
        "norm_ref": "DIN V 18599-10:2018-09 (Profilbezug), DIN 277-1 (Flaechenkategorien, noch offen)",
        "values_overlay": {
            "required": False,
            "missing_value_message": (
                "Raumtypen sind ohne Overlay nutzbar. Die Normgroessen "
                "din_277_category und theta_heizlast_standard_c sind jedoch noch "
                "unbelegt und blockieren die Heizlastrechnung."
            ),
        },
        "entry_schema_ref": "schema/v4.0/catalogs/room_types.schema.json",
        "entries": entries,
        "open_points": [
            "catalog_version bewusst 0.1.0: Der Katalog ist ein belegter Seed, keine "
            "abgenommene Liste. Die im Handoff genannten rund 55 Typen mit "
            "3-Normen-Mapping haben im Repo keine Quelle — Handoff Abschnitt 5 "
            "enthaelt die Revit-Testbefunde, keine Raumtypen.",
            "din_277_category fuer alle Eintraege offen (DIN 277-1 Nutzungsarten).",
            "theta_heizlast_standard_c fuer alle Eintraege offen (DIN EN 12831).",
            "geg_category nur fuer NWG relevant, haengt an der GEG-Anlage-2-Zonierung.",
        ],
    }

    ziel = REPO / "catalog" / "core" / "room_types.json"
    ziel.write_text(
        json.dumps(katalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    wg = sum(1 for e in entries if e["applicability"] == ["WG"])
    nwg = sum(1 for e in entries if e["applicability"] == ["NWG"])
    print(f"{ziel.relative_to(REPO)}: {len(entries)} Raumtypen ({wg} WG / {nwg} NWG)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
