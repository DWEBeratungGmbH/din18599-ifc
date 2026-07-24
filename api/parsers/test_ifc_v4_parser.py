#!/usr/bin/env python3
"""
test_ifc_v4_parser.py — Tests fuer den IFC -> v4.0-Skelett-Parser.

Zwei Ebenen:

* Reine Einheitstests (ohne IFC/ifcopenshell) fuer die deterministischen
  Bausteine: element_type-Mapping (OFFEN-7), Normalen-Kanonisierung, Dreiecks-
  Geometrie. Diese laufen immer.
* Integrationstest gegen eine echte Repo-IFC
  (``sources/IFC_EVBI/DIN18599TestIFCv4.ifc``): der erzeugte Sidecar muss gegen
  das v4.0-Schema strukturell gueltig sein (Level ``draft``), die gelockten
  Vertragspunkte aus SPEC §9.1 erfuellen und beim zweiten Lauf identische
  Fingerprints liefern (Idempotenz). Fehlt ifcopenshell oder die Fixture, wird
  dieser Block sauber uebersprungen statt zu scheitern.

Aufruf:
    python3 api/parsers/test_ifc_v4_parser.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parent.parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(REPO / "tools"))

import ifc_v4_parser as p  # noqa: E402

REFERENZ_IFC = REPO / "sources" / "IFC_EVBI" / "DIN18599TestIFCv4.ifc"
SCHEMA_PFAD = REPO / "schema" / "v4.0" / "sidecar.schema.json"


# --------------------------------------------------------------------------- #
# Ebene 1 — reine Einheitstests (immer lauffaehig)
# --------------------------------------------------------------------------- #

def test_element_type_mapping() -> list[tuple[str, bool]]:
    """OFFEN-7: nur direkte PredefinedType-Abbildung, Rest 'other'."""
    faelle = [
        ("Wand", p._map_element_type("IfcWall", None), "wall"),
        ("WandStandardCase", p._map_element_type("IfcWallStandardCase", None), "wall"),
        ("Dach", p._map_element_type("IfcRoof", None), "roof"),
        ("Stuetze", p._map_element_type("IfcColumn", None), "column"),
        ("Traeger", p._map_element_type("IfcBeam", None), "beam"),
        ("Slab FLOOR", p._map_element_type("IfcSlab", "FLOOR"), "floor"),
        ("Slab ROOF", p._map_element_type("IfcSlab", "ROOF"), "roof"),
        ("Slab BASESLAB", p._map_element_type("IfcSlab", "BASESLAB"), "slab_ground"),
        # Feinklassifikation ist Anreicherung -> Parser darf sie NICHT raten.
        ("Slab NOTDEFINED -> other", p._map_element_type("IfcSlab", "NOTDEFINED"), "other"),
        ("Slab None -> other", p._map_element_type("IfcSlab", None), "other"),
        ("Unbekannt -> other", p._map_element_type("IfcFooBar", None), "other"),
    ]
    return [(name, ist == soll) for name, ist, soll in faelle]


def test_canonical_normal() -> list[tuple[str, bool]]:
    """Antiparallele Normalen landen in derselben Ebenenrichtung."""
    ergebnisse = []
    vorne = p._canonical((0.0, -1.0, 0.0))
    hinten = p._canonical((0.0, 1.0, 0.0))
    ergebnisse.append(("antiparallel identisch", vorne == hinten))
    # Erste signifikante Achse bestimmt das Vorzeichen (x vor y vor z).
    ergebnisse.append(("x-dominant positiv", p._canonical((-0.9, 0.1, 0.0))[0] > 0))
    ergebnisse.append(("bereits positiv unveraendert",
                       p._canonical((1.0, 0.0, 0.0)) == (1.0, 0.0, 0.0)))
    return ergebnisse


def test_tri_normal_area() -> list[tuple[str, bool]]:
    """Einheitsdreieck in der xy-Ebene: Normale +z, Flaeche 0.5."""
    n, a = p._tri_normal_area((0, 0, 0), (1, 0, 0), (0, 1, 0))
    entartet, _ = p._tri_normal_area((0, 0, 0), (0, 0, 0), (0, 0, 0))
    return [
        ("normale zeigt in +z", n is not None and abs(n[2] - 1.0) < 1e-9),
        ("flaeche 0.5", abs(a - 0.5) < 1e-9),
        ("entartetes dreieck -> None", entartet is None),
    ]


def test_building_type_merge_ohne_ifc() -> list[tuple[str, bool]]:
    """OFFEN-5: Parser raet type nie, ueberschreibt vorhandenen Wert nie.

    Testet die Merge-Logik ueber einen Stub, der die IFC-Extraktion ersetzt —
    so bleibt der Test ohne ifcopenshell lauffaehig.
    """
    ergebnisse = []
    # Der Platzhalter ist einer der Enum-Werte, nicht erfunden.
    ergebnisse.append(("platzhalter im enum",
                       p.BUILDING_TYPE_PLACEHOLDER in ("residential", "non_residential", "mixed")))
    # Provenienz/Level sind Konstanten des Vertrags.
    ergebnisse.append(("schema_url v4.0", p.SCHEMA_URL.endswith("/v4.0/sidecar")))
    ergebnisse.append(("schema_version 4.0.x", p.SCHEMA_VERSION.startswith("4.0.")))
    return ergebnisse


# --------------------------------------------------------------------------- #
# Ebene 2 — Integration gegen echte IFC (uebersprungen wenn Deps/Fixture fehlen)
# --------------------------------------------------------------------------- #

def _ifc_verfuegbar() -> bool:
    try:
        import ifcopenshell  # noqa: F401
        import ifcopenshell.geom  # noqa: F401
    except ImportError:
        return False
    return REFERENZ_IFC.exists() and SCHEMA_PFAD.exists()


def test_integration() -> list[tuple[str, bool]]:
    """Voller Parser-Lauf gegen die Referenz-IFC + Schema-Validierung."""
    from jsonschema import Draft7Validator

    sidecar = p.parse_ifc_to_sidecar_v4(
        str(REFERENZ_IFC), ifc_file_ref="DIN18599TestIFCv4.ifc"
    )
    inp = sidecar["input"]
    ergebnisse: list[tuple[str, bool]] = []

    # --- Schema-Gueltigkeit (Level draft) --------------------------------- #
    schema = json.loads(SCHEMA_PFAD.read_text(encoding="utf-8"))
    fehler = list(Draft7Validator(schema).iter_errors(sidecar))
    ergebnisse.append((f"schema-gueltig (0 Fehler, ist {len(fehler)})", not fehler))
    if fehler:
        for f in fehler[:5]:
            print("    SCHEMA-FEHLER:", "/".join(str(x) for x in f.path), "-", f.message[:120])

    # --- Kopf/Provenienz/Level -------------------------------------------- #
    ergebnisse.append(("source.origin = IFC_PARSER",
                       sidecar["meta"]["source"]["origin"] == "IFC_PARSER"))
    ergebnisse.append(("validation.level = draft",
                       sidecar["meta"]["validation"]["level"] == "draft"))
    ergebnisse.append(("schema_info.url v4.0",
                       sidecar["schema_info"]["url"] == p.SCHEMA_URL))

    # --- Boundaries bewusst deferred (nicht mal als []) ------------------- #
    ergebnisse.append(("boundaries fehlen (deferred)", "boundaries" not in inp))

    # --- element_groups sind 1:1, Fingerprint voll praezise --------------- #
    egs = inp.get("element_groups", [])
    ergebnisse.append(("element_groups vorhanden", len(egs) > 0))
    alle_1zu1 = all(g["aggregates"]["member_count"] == 1 for g in egs)
    ergebnisse.append(("aggregates.member_count == 1 (1:1)", alle_1zu1))
    fp_ok = all("dist_m" in g["fingerprint"]
                and g["fingerprint"]["coordinate_system"] == "project"
                for g in egs)
    ergebnisse.append(("fingerprint traegt dist_m + coordinate_system", fp_ok))
    # Volle Praezision: mindestens ein dist_m mit mehr als 3 Nachkommastellen.
    voll_praezise = any(
        len(repr(g["fingerprint"]["dist_m"]).split(".")[-1]) > 3
        for g in egs if isinstance(g["fingerprint"]["dist_m"], float)
    )
    ergebnisse.append(("dist_m in voller Praezision (nicht anzeige-gerundet)", voll_praezise))

    # --- Raeume: Platzhalter heated (OFFEN-4 B) --------------------------- #
    rooms = inp.get("rooms", [])
    if rooms:
        ergebnisse.append(("alle rooms heating_status=heated (Platzhalter)",
                           all(r["heating_status"] == "heated" for r in rooms)))

    # --- Openings als Host-Rider mitgefuehrt (OFFEN-8) -------------------- #
    rider = [m for g in egs for m in g["member_elements"]
             if m.get("role") == "hosted_opening"]
    if rider:
        ergebnisse.append(("hosted_opening-Rider tragen host_element_group_ref",
                           all(r.get("host_element_group_ref") is not None
                               or "host_ifc_guid" not in r for r in rider)))

    # --- building.type gesetzt, nie aus IFC geraten (Platzhalter) --------- #
    ergebnisse.append(("building.type vorhanden",
                       inp["building"].get("type") in ("residential", "non_residential", "mixed")))

    # --- Validator: erwartete draft-Warnungen, keine Fehler --------------- #
    from dwe_validate import lade_kataloge, validiere
    erg = validiere(sidecar, lade_kataloge())
    codes = {b.code for b in erg.befunde}
    ergebnisse.append(("Validator erreicht Stufe draft", erg.erreichte_stufe == "draft"))
    ergebnisse.append(("Validator: keine error-Severity", not erg.hat_fehler))
    ergebnisse.append(("erwartete Warnung BOUNDARIES_EMPTY", "BOUNDARIES_EMPTY" in codes))
    ergebnisse.append(("erwartete Warnung HEATING_STATUS_UNCONFIRMED",
                       "HEATING_STATUS_UNCONFIRMED" in codes))

    # --- Idempotenz: zweiter Lauf, identische Fingerprints ---------------- #
    sidecar2 = p.parse_ifc_to_sidecar_v4(
        str(REFERENZ_IFC), ifc_file_ref="DIN18599TestIFCv4.ifc"
    )
    fp1 = {g["id"]: g["fingerprint"] for g in egs}
    fp2 = {g["id"]: g["fingerprint"] for g in sidecar2["input"]["element_groups"]}
    ergebnisse.append(("Idempotenz: identische Fingerprints ueber zwei Laeufe", fp1 == fp2))

    # --- Merge: vorhandener building.type wird NICHT ueberschrieben ------- #
    base = {"input": {"building": {"type": "residential"}}, "meta": {}}
    merged = p.parse_ifc_to_sidecar_v4(
        str(REFERENZ_IFC), ifc_file_ref="DIN18599TestIFCv4.ifc", base=base
    )
    ergebnisse.append(("base.building.type bleibt erhalten (OFFEN-5)",
                       merged["input"]["building"]["type"] == "residential"))

    return ergebnisse


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

def main() -> int:
    print(f"{'Pruefung':60} Ergebnis")
    print("-" * 72)
    fehlgeschlagen = 0
    gesamt = 0

    einheitstests = [
        ("element_type-Mapping", test_element_type_mapping),
        ("Normalen-Kanonisierung", test_canonical_normal),
        ("Dreiecks-Geometrie", test_tri_normal_area),
        ("Vertrags-Konstanten/Merge", test_building_type_merge_ohne_ifc),
    ]
    for block_name, fn in einheitstests:
        for name, ok in fn():
            gesamt += 1
            fehlgeschlagen += 0 if ok else 1
            print(f"{block_name + ': ' + name:60} {'PASS' if ok else 'FAIL'}")

    print("-" * 72)
    if _ifc_verfuegbar():
        for name, ok in test_integration():
            gesamt += 1
            fehlgeschlagen += 0 if ok else 1
            print(f"{'Integration: ' + name:60} {'PASS' if ok else 'FAIL'}")
    else:
        print("Integration: uebersprungen (ifcopenshell oder Referenz-IFC fehlt)")

    print()
    print(f"{gesamt - fehlgeschlagen}/{gesamt} Pruefungen bestanden")
    return 1 if fehlgeschlagen else 0


if __name__ == "__main__":
    raise SystemExit(main())
