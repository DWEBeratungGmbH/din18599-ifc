#!/usr/bin/env python3
"""
test_dwe_validate.py — Negativtests fuer den Validator.

Jede Regel bekommt ein gezielt kaputtes Sidecar und muss anschlagen. Zusaetzlich
die Gegenprobe: keiner dieser Codes darf im sauberen Referenz-Beispiel auftauchen
(sonst ist die Regel ein Falsch-Positiv-Generator).

Ohne diese Tests verrottet der Validator lautlos — eine Regel, die nie ausloest,
sieht genauso aus wie eine, die funktioniert.

Aufruf:
    python3 tools/test_dwe_validate.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dwe_validate import lade_kataloge, validiere  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
BEISPIEL = REPO / "examples" / "v4.0" / "beispiel1" / "energy.din18599.json"


def _grenze(**kwargs) -> dict:
    """Minimale Boundary, per kwargs gezielt verbogen."""
    basis = {
        "id": "B1",
        "element_group_ref": "AW-NO-01",
        "space_a": "R-WE1-01",
        "adjacency_type": "exterior",
    }
    basis.update(kwargs)
    return basis


def baue_faelle(basis: dict) -> list[tuple[str, dict, str]]:
    faelle: list[tuple[str, dict, str]] = []

    d = copy.deepcopy(basis)
    d["input"]["rooms"][0]["room_type_ref"] = "SCHWIMMHALLE"
    faelle.append(("unbekannter room_type_ref", d, "ROOM_TYPE_UNRESOLVED"))

    d = copy.deepcopy(basis)
    d["input"]["rooms"][0]["zone_memberships"][0]["zone_id"] = "Z-GIBTS-NICHT"
    faelle.append(("Zone existiert nicht", d, "ZONE_UNRESOLVED"))

    d = copy.deepcopy(basis)
    d["input"]["element_groups"][0]["construction_ref"] = "C-FAKE"
    faelle.append(("construction_ref ins Leere", d, "CONSTRUCTION_UNRESOLVED"))

    # Zwei Gruppen auf derselben Ebene mit gleichem Typ waeren in Wahrheit eine.
    d = copy.deepcopy(basis)
    d["input"]["element_groups"][1]["fingerprint"] = copy.deepcopy(
        d["input"]["element_groups"][0]["fingerprint"]
    )
    faelle.append(("Fingerprint-Kollision", d, "FINGERPRINT_COLLISION"))

    # Der Befund aus der Revit-Testphase: raumbegrenzendes Toposolid
    # verfaelscht die gemeldeten Raumvolumina still (-2,9 Prozent).
    d = copy.deepcopy(basis)
    for raum in d["input"]["rooms"][:12]:
        if "volume_ve_m3" in raum:
            raum["volume_reported_m3"] = round(raum["volume_ve_m3"] * 0.971, 2)
    faelle.append(("Toposolid raumbegrenzend", d, "TOPOSOLID_ROOM_BOUNDING"))

    d = copy.deepcopy(basis)
    d["input"]["boundaries"] = [
        _grenze(adjacency_type="low_heated", space_b="R-WE2-01",
                measurement_reference="outer")
    ]
    faelle.append(("Massbezug widerspricht adjacency_type", d,
                   "MEASUREMENT_REFERENCE_MISMATCH"))

    d = copy.deepcopy(basis)
    d["input"]["boundaries"] = [_grenze(space_b="R-WE2-01")]
    faelle.append(("exterior mit Gegenraum", d, "BOUNDARY_SPACE_B_UNEXPECTED"))

    d = copy.deepcopy(basis)
    d["input"]["boundaries"] = [_grenze(adjacency_type="unheated")]
    faelle.append(("unheated ohne Gegenraum", d, "BOUNDARY_SPACE_B_MISSING"))

    d = copy.deepcopy(basis)
    d["input"]["boundaries"] = [
        _grenze(geometry={"type": "z_range", "z_from": 4.2, "z_to": 0.0})
    ]
    faelle.append(("z_to nicht groesser z_from", d, "Z_RANGE_INVALID"))

    d = copy.deepcopy(basis)
    d["input"]["boundaries"] = [
        _grenze(openings=[{"id": "O1", "opening_type": "window"}])
    ]
    d["input"]["openings_index"] = [{"opening_ref": "O-GEISTER", "boundary_ref": "B1"}]
    faelle.append(("openings_index stimmt nicht", d, "OPENINGS_INDEX_INCONSISTENT"))

    d = copy.deepcopy(basis)
    d["input"]["rooms"][0]["theta_heizlast_standard_c"] = 20
    d["input"]["rooms"][0]["theta_heizlast_override_c"] = 26
    faelle.append(("theta-Override groesser 3 K", d, "THETA_OVERRIDE_LARGE"))

    d = copy.deepcopy(basis)
    d["input"]["building"]["envelope_area_m2"] = 500.0
    d["input"]["boundaries"] = [_grenze(area_18599=300.0, relevant_18599=True)]
    faelle.append(("Huellflaeche ausserhalb Toleranz", d, "ENVELOPE_AREA_MISMATCH"))

    # Raum ausserhalb der thermischen Huelle in einer thermischen Zone. Der
    # Default kommt aus dem Katalog, ohne dass am Raum ein Feld gesetzt ist.
    d = copy.deepcopy(basis)
    d["input"]["rooms"].append({
        "id": "R-TER-01", "name": "Terrasse", "storey_ref": "S-EG",
        "room_type_ref": "AUSSENBEREICH", "heating_status": "unheated",
        "zone_memberships": [{"zone_type": "thermal", "zone_id": "Z-THERM-01"}],
        "area_ngf_m2": 24.0,
    })
    faelle.append(("Aussenbereich in thermischer Zone", d,
                   "ROOM_OUTSIDE_ENVELOPE_IN_ZONE"))

    d = copy.deepcopy(basis)
    d["input"]["rooms"].append({
        "id": "R-WIG-01", "name": "Wintergarten", "storey_ref": "S-EG",
        "room_type_ref": "WINTERGARTEN", "heating_status": "heated",
        "zone_memberships": [], "area_ngf_m2": 12.0,
    })
    faelle.append(("Wintergarten ausserhalb Huelle als beheizt", d,
                   "ROOM_OUTSIDE_ENVELOPE_HEATED"))

    return faelle


def pruefe_override(basis: dict, kataloge: dict) -> bool:
    """
    Der Katalog-Default muss am Raum ueberschreibbar sein — ein beheizter
    Wintergarten innerhalb der Huelle ist ein zulaessiger Fall.
    """
    from dwe_validate import validiere  # lokal, damit der Import oben schlank bleibt

    d = copy.deepcopy(basis)
    d["input"]["rooms"].append({
        "id": "R-WIG-02", "name": "Wintergarten beheizt", "storey_ref": "S-EG",
        "room_type_ref": "WINTERGARTEN", "outside_thermal_envelope": False,
        "heating_status": "heated", "area_ngf_m2": 12.0,
        "zone_memberships": [{"zone_type": "thermal", "zone_id": "Z-THERM-01"}],
    })
    codes = {b.code for b in validiere(d, kataloge).befunde}
    return "ROOM_OUTSIDE_ENVELOPE_IN_ZONE" not in codes


def pruefe_fingerprint_grenzfaelle() -> list[tuple[str, bool]]:
    """Grenzfaelle des Kollisions-Checks.

    Der Check vergleicht Winkelabstaende, nicht gerundete Werte. Fall A ist
    genau der, den die frueher vorgesehene Rundungs-Gleichheit uebersehen
    haette: 0,4 Grad Abstand liegen innerhalb der 1-Grad-Toleranz, fallen aber
    bei 2 Dezimalen in verschiedene Buckets.
    """
    import math

    from dwe_validate import Ergebnis, pruefe_fingerprint_kollisionen

    def gruppe(gid, grad, dist, typ="wall", winkel_tol=1.0):
        return {
            "id": gid, "element_type": typ,
            "fingerprint": {
                "normal_x": math.sin(math.radians(grad)),
                "normal_y": math.cos(math.radians(grad)),
                "normal_z": 0.0,
                "dist_m": dist,
                "tolerance": {"angle_tolerance_deg": winkel_tol,
                              "dist_tolerance_m": 0.02},
            },
        }

    def roh(gid, nx, ny, dist):
        """Gruppe mit direkt gesetzter Normale (fuer den Kanonisierungsfall)."""
        return {
            "id": gid, "element_type": "wall",
            "fingerprint": {
                "normal_x": nx, "normal_y": ny, "normal_z": 0.0, "dist_m": dist,
                "tolerance": {"angle_tolerance_deg": 1.0,
                              "dist_tolerance_m": 0.02},
            },
        }

    faelle = [
        ("0,4 Grad -- Rundung haette getrennt",
         [gruppe("W1", 0.0, 4.20), gruppe("W2", 0.4, 4.21)], True),
        ("antiparallel, dist gespiegelt",
         [roh("W3", 1.0, 0.0, 5.0), roh("W4", -1.0, 0.0, -5.0)], True),
        ("1,8 Grad -- ausserhalb der Toleranz",
         [gruppe("W5", 0.0, 4.20), gruppe("W6", 1.8, 4.20)], False),
        ("gleiche Ebene, anderer Bauteiltyp",
         [gruppe("W7", 0.0, 4.20), gruppe("D1", 0.0, 4.20, typ="roof")], False),
        ("ungleiche Toleranzen -- Maximum gilt",
         [gruppe("W8", 0.0, 4.20), gruppe("W9", 1.4, 4.20, winkel_tol=2.0)], True),
        ("gleiche Ebene, 5 cm auseinander",
         [gruppe("WA", 0.0, 4.20), gruppe("WB", 0.0, 4.25)], False),
    ]

    ergebnisse = []
    for name, gruppen, erwartet_treffer in faelle:
        erg = Ergebnis()
        pruefe_fingerprint_kollisionen({g["id"]: g for g in gruppen}, erg)
        getroffen = any(b.code == "FINGERPRINT_COLLISION" for b in erg.befunde)
        ergebnisse.append((name, getroffen == erwartet_treffer))
    return ergebnisse


def main() -> int:
    if not BEISPIEL.exists():
        print(f"Referenz-Beispiel fehlt: {BEISPIEL}", file=sys.stderr)
        print("Erst erzeugen: python3 scripts/build-example-beispiel1.py", file=sys.stderr)
        return 2

    kataloge = lade_kataloge()
    if not kataloge:
        print("Keine Kataloge unter catalog/core/ gefunden.", file=sys.stderr)
        return 2

    basis = json.loads(BEISPIEL.read_text(encoding="utf-8"))
    faelle = baue_faelle(basis)

    def codes(sidecar: dict) -> set:
        return {b.code for b in validiere(sidecar, kataloge).befunde}

    print(f"{'Fall':42} {'erwarteter Code':32} Ergebnis")
    print("-" * 92)
    fehlgeschlagen = 0
    for name, doc, erwartet in faelle:
        ok = erwartet in codes(doc)
        fehlgeschlagen += 0 if ok else 1
        print(f"{name:42} {erwartet:32} {'PASS' if ok else 'FAIL'}")

    # Gegenprobe: das saubere Beispiel darf keinen dieser Codes ausloesen.
    sauber = codes(basis)
    falsch_positiv = sorted({e for _, _, e in faelle if e in sauber})
    print()
    print("Falsch-Positive im sauberen Beispiel:", ", ".join(falsch_positiv) or "keine")
    fehlgeschlagen += len(falsch_positiv)

    override_ok = pruefe_override(basis, kataloge)
    print(f"Katalog-Default am Raum ueberschreibbar: "
          f"{'PASS' if override_ok else 'FAIL'}")
    fehlgeschlagen += 0 if override_ok else 1

    # Das Referenz-Beispiel muss die dokumentierte Stufe erreichen.
    erg = validiere(basis, kataloge)
    erwartete_stufe = "enriched"
    stufe_ok = erg.erreichte_stufe == erwartete_stufe
    print(f"Referenz-Beispiel erreicht '{erg.erreichte_stufe}' "
          f"(erwartet '{erwartete_stufe}'): {'PASS' if stufe_ok else 'FAIL'}")
    fehlgeschlagen += 0 if stufe_ok else 1

    print()
    print("Fingerprint-Kollision, Grenzfaelle:")
    fp_faelle = pruefe_fingerprint_grenzfaelle()
    for name, ok in fp_faelle:
        print(f"  {name:48} {'PASS' if ok else 'FAIL'}")
        fehlgeschlagen += 0 if ok else 1

    print()
    gesamt = len(faelle) + 3 + len(fp_faelle)
    print(f"{gesamt - fehlgeschlagen}/{gesamt} Pruefungen bestanden")
    return 1 if fehlgeschlagen else 0


if __name__ == "__main__":
    raise SystemExit(main())
