#!/usr/bin/env python3
"""
build-usage-profiles-catalog.py — erzeugt catalog/core/usage_profiles.<edition>.json

Baut den STRUKTUR-Katalog der DIN-18599-10-Nutzungsprofile: Profilnummern, Namen,
Kategorien und die Parameter-SLOTS mit norm_cell-Zeigern. Enthaelt bewusst KEINE
Zahlenwerte — die kommen zur Laufzeit aus catalog/values/ (Entscheidung 6.1).

Quelle der Profilnamen: catalog/din18599_usage_profiles.json (Altbestand v1.0).

Aufruf:
    python3 scripts/build-usage-profiles-catalog.py --edition 2018-09
"""
import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Parameter-Slots je Profil. Namen nach DIN-Notation, Einheiten aus dem Altbestand.
# norm_table: in welcher Tabelle der Wert steht (Wohnen = 5, NWG = 7).
PARAMETER_SLOTS = [
    ("theta_i_h_soll",   "°C",           "Raum-Solltemperatur Heizung"),
    ("theta_i_c_soll",   "°C",           "Raum-Solltemperatur Kuehlung"),
    ("delta_theta_i_NA", "K",            "Temperaturabsenkung reduzierter Betrieb"),
    ("q_I",              "Wh/(m²·d)",    "Interne Waermequellen"),
    ("n_nutz",           "1/h",          "Nutzungsbedingter Mindestaussenluftwechsel"),
    ("q_w_b_a",          "kWh/(m²·a)",   "Jahreswert Nutzenergiebedarf Trinkwarmwasser"),
    ("q_el_b",           "Wh/(m²·d)",    "Anwendungsstrombedarf"),
    ("t_nutz_d",         "h/d",          "Taegliche Nutzungszeit"),
    ("d_nutz_a",         "d/a",          "Jaehrliche Nutzungstage"),
]

# Profile ohne eigene Betriebszeiten: sie erben t_nutz_d und d_nutz_a von der
# uebergeordneten Zone (Handoff E2, zone.parent_zone_ref). Fuer sie ist der Wert
# nicht "noch nicht befuellt", sondern "existiert fuer dieses Profil nicht" —
# genau dafuer ist null reserviert und NICHT als Platzhalter zu verwenden.
INHERITS_OPERATING_HOURS = {"16", "18", "19", "20", "41"}
INHERITED_SLOTS = {"t_nutz_d", "d_nutz_a"}


def parameter_slots(profil_nummer: str) -> dict:
    """
    Baut die Parameter-Slots eines Profils — Struktur ohne Zahlenwerte.

    Feldnamen und value_source-Werte folgen strikt
    schema/v4.0/catalogs/usage_profiles.schema.json.
    """
    slots = {}
    for name, unit, beschreibung in PARAMETER_SLOTS:
        if profil_nummer in INHERITS_OPERATING_HOURS and name in INHERITED_SLOTS:
            # Kein eigener Normwert: die Betriebszeiten kommen von der
            # uebergeordneten Zone (parent_zone_ref). Genau der Fall, fuer den
            # null reserviert bleibt — deshalb not_applicable und KEIN Overlay-Slot.
            slots[name] = {
                "unit": unit,
                "description": beschreibung,
                "value_source": "not_applicable",
                "norm_column": None,
            }
        else:
            slots[name] = {
                "unit": unit,
                "description": beschreibung,
                "value_source": "norm_table",
                # Spalte muss beim Befuellen aus der lizenzierten Quelle
                # ergaenzt werden. Bewusst nicht geraten.
                "norm_column": None,
            }
    return slots


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", default="2018-09")
    args = parser.parse_args()

    quelle = json.loads(
        (REPO / "catalog" / "din18599_usage_profiles.json").read_text(encoding="utf-8")
    )

    entries = []

    for profil in quelle["residential_profiles"]:
        nummer = profil["number"]                      # R1, R2
        entries.append({
            "code": f"WG_{nummer}",
            "number": nummer,
            "name_de": profil["name_de"],
            "name_en": profil.get("name_en", ""),
            "category": profil.get("category", "residential"),
            "applicability": ["WG"],
            "norm_ref": f"DIN V 18599-10:{args.edition}, Tabelle 5",
            "norm_cell": f"T5-Z{nummer}",
            "parameters": parameter_slots(nummer),
        })

    for profil in quelle["non_residential_profiles"]:
        nummer = profil["number"]                      # 01 .. 43
        eintrag = {
            "code": f"NWG_{nummer}",
            "number": nummer,
            "name_de": profil["name_de"],
            "name_en": profil.get("name_en", ""),
            "category": profil.get("category", ""),
            "applicability": ["NWG"],
            "norm_ref": f"DIN V 18599-10:{args.edition}, Tabelle 6 und 7",
            "norm_cell": f"T7-Z{nummer}",
            "parameters": parameter_slots(nummer),
        }
        if profil.get("description"):
            eintrag["description"] = profil["description"]
        if nummer in INHERITS_OPERATING_HOURS:
            # Betriebszeiten kommen von der uebergeordneten Zone, nicht aus der
            # Profiltabelle. Das Sidecar loest das ueber zone.parent_zone_ref auf.
            eintrag["parent_profile"] = "__parent_zone__"
        entries.append(eintrag)

    katalog = {
        "$schema_ref": "https://din18599-ifc.de/schema/v4.0/catalog-envelope",
        "catalog_id": "usage_profiles",
        "catalog_version": "1.0.0",
        "catalog_source": "core",
        "dimension": {"type": "norm_edition", "value": args.edition},
        "title": f"DIN 18599-10 Nutzungsprofile ({args.edition})",
        "description": (
            "STRUKTUR-Katalog: Profilnummern, Namen, Kategorien und Parameter-Slots "
            "mit norm_cell-Zeigern. Enthaelt KEINE Zahlenwerte — diese sind "
            "urheberrechtlich geschuetzt (DIN/Beuth) und werden zur Laufzeit aus "
            "einem Werte-Overlay gemerged."
        ),
        "last_updated": "2026-07-21",
        "norm_ref": f"DIN V 18599-10:{args.edition}, Tabellen 5 bis 7",
        "values_overlay": {
            "required": True,
            "expected_file": f"catalog/values/usage_profiles.{args.edition}.values.json",
            "merge_key": "code",
            "missing_value_message": (
                "Werte-Katalog fehlt — DWEapp verbinden oder Overlay aus eigener "
                "Normlizenz befuellen. Ohne aufgeloeste Werte kein calc_ready."
            ),
        },
        "entry_schema_ref": "schema/v4.0/catalogs/usage_profiles.schema.json",
        "entries": entries,
    }

    ziel = REPO / "catalog" / "core" / f"usage_profiles.{args.edition}.json"
    ziel.write_text(
        json.dumps(katalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    geerbt = sum(1 for e in entries if e.get("parent_profile"))
    print(f"{ziel.relative_to(REPO)}: {len(entries)} Profile "
          f"({sum(1 for e in entries if e['applicability'] == ['WG'])} WG / "
          f"{sum(1 for e in entries if e['applicability'] == ['NWG'])} NWG), "
          f"{geerbt} mit geerbten Betriebszeiten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
