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

# Wohngebaeude-Raumtypen — QUELLE: praxisvalidierte RAUMTYPEN-Tabelle des
# Dynamo-Anreicherungsskripts der Revit-Pipeline (Freigabe Sebi, 21.07.2026).
#
# theta_heizlast_standard_c sind die Auslegungs-Innentemperaturen nach
# DIN EN 12831-1/NA. Sie stehen oeffentlich: Einzelfakten ohne Schoepfungshoehe,
# gleiche Begruendung wie bei den Fx-Werten (Entscheidung 6.6).
#
# counts_as_living_area ist dagegen DWE-eigene Vorbelegung nach WoFlV-Logik und
# bildet die Feinheiten (Treppen ab 4 Steigungen, Zubehoerraeume) NICHT ab.
# Spalten: code, name_de, theta, lueftung, heating, wohnflaeche, ausserhalb_huelle,
#          applicability, keywords
WG_TYPEN = [
    ("WOHNRAUM",     "Wohnraum",       20,   "supply",   "heated",     True,  False, ["WG"], ["wohn", "wohnzimmer", "living"]),
    ("SCHLAFZIMMER", "Schlafzimmer",   20,   "supply",   "heated",     True,  False, ["WG"], ["schlaf", "bedroom"]),
    ("KINDERZIMMER", "Kinderzimmer",   20,   "supply",   "heated",     True,  False, ["WG"], ["kinder", "kinderzimmer"]),
    ("GAESTEZIMMER", "Gaestezimmer",   20,   "supply",   "heated",     True,  False, ["WG"], ["gaeste", "gäste", "guest"]),
    ("ARBEITSZIMMER", "Arbeitszimmer", 20,   "supply",   "heated",     True,  False, ["WG"], ["arbeit", "arbeitszimmer", "study"]),
    ("HOBBYRAUM",    "Hobbyraum",      20,   "supply",   "heated",     True,  False, ["WG"], ["hobby", "hobbyraum"]),
    ("BUERO",        "Buero",          20,   "supply",   "heated",     True,  False, ["WG"], ["buero", "büro", "office"]),
    ("KUECHE",       "Kueche",         20,   "exhaust",  "heated",     True,  False, ["WG"], ["kueche", "küche", "kitchen"]),
    ("BAD",          "Bad",            24,   "exhaust",  "heated",     True,  False, ["WG"], ["bad", "bath", "duschbad"]),
    ("WC",           "WC",             20,   "exhaust",  "heated",     True,  False, ["WG"], ["wc", "gaeste-wc", "toilette"]),
    ("HWR",          "Hauswirtschaftsraum", 20, "exhaust", "heated",   True,  False, ["WG"], ["hwr", "hauswirtschaft", "waschkueche"]),
    ("SAUNA",        "Sauna",          24,   "exhaust",  "heated",     True,  False, ["WG"], ["sauna"]),
    ("FLUR",         "Flur / Diele",   20,   "transfer", "heated",     True,  False, ["WG"], ["flur", "diele", "gang", "corridor"]),
    ("ABSTELLRAUM",  "Abstellraum",    20,   "transfer", "heated",     True,  False, ["WG"], ["abstell", "storage", "speis"]),
    ("TREPPENHAUS",  "Treppenhaus",    15,   None,       "low_heated", False, False, ["WG"], ["treppe", "treppenhaus", "stair"]),
    ("TECHNIKRAUM",  "Technikraum",    15,   None,       "low_heated", False, False, ["WG"], ["technik", "heizung", "hausanschluss"]),
    ("KELLER",       "Keller",         None, None,       "unheated",   False, False, ["WG"], ["keller", "basement"]),
    ("GARAGE",       "Garage / Carport", None, None,     "unheated",   False, False, ["WG"], ["garage", "carport", "stellplatz"]),

    # Zurueckgeholt (Feedback 21.07.): Gegenstueck zu adjacency_type=
    # attic_uninsulated. Ohne ihn laesst sich ein unbeheizter Dachraum nicht
    # typisieren. Wird im 142er-Schluessel als Zeile 143 ergaenzt.
    ("DACHBODEN",    "Dachboden / Spitzboden", None, None, "unheated",  False, False, ["WG"], ["dachboden", "spitzboden", "attic"]),

    # Fuenf Ergaenzungen aus dem NWG-Teil des Raumtypen-Schluessels (21.07.).
    # applicability auf beide gesetzt: Wintergarten und Aussenbereich sind im
    # Wohnbau der Regelfall — bei Widerspruch korrigieren.
    ("AUFENTHALTSRAUM", "Aufenthaltsraum", 20, "supply",  "heated",     False, False, ["WG", "NWG"], ["aufenthalt", "aufenthaltsraum"]),
    ("BEHANDLUNGSRAUM", "Behandlungsraum", 24, "supply",  "heated",     False, False, ["WG", "NWG"], ["behandlung", "behandlungsraum", "praxis"]),
    ("SCHWIMMBAD",   "Schwimmbad",     28,   "exhaust",  "heated",     False, False, ["WG", "NWG"], ["schwimmbad", "pool", "schwimmhalle"]),
    ("AUSSENBEREICH", "Aussenbereich", None, None,       "unheated",   False, True,  ["WG", "NWG"], ["terrasse", "balkon", "loggia", "aussenbereich"]),
    ("WINTERGARTEN", "Wintergarten",   None, None,       "unheated",   False, True,  ["WG", "NWG"], ["wintergarten", "glasvorbau"]),
]


def main() -> int:
    quelle = json.loads(
        (REPO / "catalog" / "din18599_usage_profiles.json").read_text(encoding="utf-8")
    )

    entries = []

    for (code, name, theta, lueftung, heating, wohnflaeche,
         ausserhalb, applicability, keywords) in WG_TYPEN:
        defaults = {
            "heating_status": heating,
            "theta_heizlast_standard_c": theta,
            "counts_as_living_area": wohnflaeche,
        }
        if lueftung is not None:
            defaults["ventilation_function"] = lueftung
        if ausserhalb:
            # Liegt ausserhalb der thermischen Huelle: wird nicht bilanziert und
            # gehoert in KEINE thermische Zone. Unterscheidet sich von "unbeheizt":
            # ein unbeheizter Keller liegt im Gebaeudevolumen, eine Terrasse nicht.
            defaults["outside_thermal_envelope"] = True
        entries.append({
            "code": code,
            "name_de": name,
            "applicability": applicability,
            # Hook fuer den 142er-Namens-Synonymschluessel. Bleibt leer, bis der
            # Schluessel nachgereicht wird — dann ohne Schema-Aenderung befuellbar.
            "aliases": [],
            "mapping": {
                # Wohngebaeude werden auf Zonenebene ueber R1/R2 bilanziert.
                # Die Zuordnung geschieht an der Zone, nicht am Raumtyp.
                "din_18599_profile": None,
                # DIN-277-Zuordnung liefert Sebi nach Normpruefung nach.
                "din_277_category": None,
                "geg_category": None,
            },
            "defaults": defaults,
            "suggestion_keywords": keywords,
            "value_source": "norm_table" if theta is not None else "dwe_definition",
            "norm_cell": "DIN EN 12831-1/NA" if theta is not None else None,
            "note": "theta_heizlast_standard_c nach DIN EN 12831-1/NA. "
                    "heating_status, ventilation_function und counts_as_living_area "
                    "sind DWE-Vorbelegungen aus der praxisvalidierten Revit-Pipeline.",
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
            "aliases": [],
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
        "catalog_version": "0.3.0",
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
            "catalog_version 0.2.0: WG-Typen stammen aus der praxisvalidierten "
            "RAUMTYPEN-Tabelle der Revit-Pipeline (Freigabe 21.07.2026). NWG-Typen "
            "sind weiterhin ein aus den Nutzungsprofilen abgeleiteter Seed.",
            "din_277_category fuer alle Eintraege offen — Sebi liefert nach Normpruefung nach.",
            "theta_heizlast_standard_c fuer die 43 NWG-Typen offen (DIN EN 12831-1/NA). "
            "Fuer die WG-Typen belegt.",
            "geg_category nur fuer NWG relevant, haengt an der GEG-Anlage-2-Zonierung.",
            "aliases[] ist ueberall leer — Hook fuer den 142er-Namens-Synonym"
            "schluessel, der nach Review nachgereicht wird. Befuellbar ohne "
            "Schema-Aenderung.",
            "ESSEN wurde entfernt: der Schluessel mappt 'Essen'/'Essbereich' auf "
            "WOHNRAUM. DACHBODEN ist zurueckgeholt (Gegenstueck zu adjacency_type="
            "attic_uninsulated).",
            "Die fuenf Ergaenzungen vom 21.07. stehen auf applicability [WG, NWG], "
            "obwohl sie aus dem NWG-Teil des Schluessels stammen — Wintergarten und "
            "Aussenbereich sind im Wohnbau der Regelfall. Bei Widerspruch korrigieren.",
            "Namenskollision: SCHWIMMBAD steht neben dem abgeleiteten NWG_22 "
            "(Nutzungsprofil 22, Schwimmbad). Ob beide bleiben oder der "
            "Schluessel-Typ auf NWG_22 mappt, ist offen.",
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
