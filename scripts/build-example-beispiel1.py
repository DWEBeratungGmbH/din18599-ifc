#!/usr/bin/env python3
"""
build-example-beispiel1.py — erzeugt examples/v4.0/beispiel1/

Referenz-Container zum Testmodell "Beispiel1" der Revit-2026-Testphase.

Belegte Eckdaten (Stand 21.07.2026, Sebi):
    23 Raeume (2 Maisonette-WE zu je 11 Raeumen + Garage als Nebenflaeche)
    n_WE = 2, Wohnflaeche 240,96 m², 2 Geschosse, 1 Toposolid
    true_north_offset_deg = 35,0
    13 element_groups aus 28 Wandinstanzen, 3 Wandtypen
    Gruppennamen: AW-NO-01..03, AW-SO-01..05, IW-WE1-01/02,
                  IW-WE1-WE2-01, IW-WE2-01/02

NICHT belegt und daher als illustrativ markiert: die Raumaufteilung innerhalb
der Wohnungen und die Ebenenabstaende der Fingerprints. Die Flaechensummen sind
dagegen exakt auf die belegten 240,96 m² gerechnet.

boundaries[] bleibt LEER — Stufe 2d der Revit-Pipeline ist in Arbeit. Genau
deshalb steht der Container auf validation_level "draft": ohne Angrenzungsmatrix
ist keine Huellflaeche und kein geometry_ok moeglich. Das ist der demonstrierte
Normalfall eines Zwischenstands, kein Fehler.

Aufruf:
    python3 scripts/build-example-beispiel1.py
"""
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZIEL = REPO / "examples" / "v4.0" / "beispiel1"

SIDECAR_URL = "https://din18599-ifc.de/schema/v4.0/sidecar"
MANIFEST_URL = "https://din18599-ifc.de/schema/v4.0/manifest"

TRUE_NORTH_OFFSET = 35.0
RAUMHOEHE = 2.50

# Raumaufteilung je Wohneinheit. Summe je WE = 120,48 m², mal zwei = 240,96 m².
# (raum_nr, room_type_ref, name, geschoss, flaeche_m2)
WE_RAEUME = [
    ("01", "FLUR",         "Flur EG",        "S-EG",  8.20),
    ("02", "WOHNRAUM",     "Wohnen/Essen",   "S-EG", 28.50),
    ("03", "KUECHE",       "Kueche",         "S-EG", 11.30),
    ("04", "WC",           "Gaeste-WC",      "S-EG",  3.60),
    ("05", "HWR",          "Hauswirtschaft", "S-EG",  5.40),
    ("06", "FLUR",         "Flur OG",        "S-OG",  6.48),
    ("07", "SCHLAFZIMMER", "Schlafen",       "S-OG", 16.20),
    ("08", "KINDERZIMMER", "Kind 1",         "S-OG", 13.50),
    ("09", "GAESTEZIMMER", "Gast",           "S-OG", 11.80),
    ("10", "BAD",          "Bad",            "S-OG",  9.50),
    ("11", "ABSTELLRAUM",  "Abstellraum",    "S-OG",  6.00),
]

# Fingerprints im PROJEKTSYSTEM. Geografischer Azimut = Projekt + 35 Grad.
# Geografisch Nordost = 45 Grad -> Projekt 10 Grad; Suedost = 135 -> Projekt 100.
AZIMUT_PROJEKT = {"NO": 10.0, "SO": 100.0}

# (gruppen_id, azimut_schluessel, ebenenabstand_m, construction_ref, instanz_anzahl)
ELEMENT_GROUPS = [
    ("AW-NO-01",      "NO",   0.00, "C-AW-01", 4),
    ("AW-NO-02",      "NO",   4.20, "C-AW-01", 2),
    ("AW-NO-03",      "NO",   8.60, "C-AW-01", 2),
    ("AW-SO-01",      "SO",   0.00, "C-AW-01", 2),
    ("AW-SO-02",      "SO",   5.20, "C-AW-01", 2),
    ("AW-SO-03",      "SO",  10.40, "C-AW-01", 2),
    ("AW-SO-04",      "SO",  15.60, "C-AW-01", 2),
    ("AW-SO-05",      "SO",  20.80, "C-AW-01", 2),
    ("IW-WE1-01",     "NO",   2.60, "C-IW-02", 2),
    ("IW-WE1-02",     "SO",   3.80, "C-IW-02", 2),
    ("IW-WE1-WE2-01", "SO",   9.30, "C-IW-01", 2),
    ("IW-WE2-01",     "NO",   6.90, "C-IW-02", 2),
    ("IW-WE2-02",     "SO",  14.20, "C-IW-02", 2),
]

# Aus dem Fingerprint-Stabilitaetstest der Revit-Testphase: dieselbe Gruppe
# ueberlebte Loeschen und Neuzeichnen, die Mitglieder wechselten.
BELEGTE_INSTANZ_IDS = {"AW-NO-01": ["2521171", "2527976"]}


def normale(azimut_grad: float) -> tuple:
    """Normale einer senkrechten Wand aus dem Azimut, gerundet auf 2 Dezimalen."""
    bogen = math.radians(azimut_grad)
    return (round(math.sin(bogen), 2), round(math.cos(bogen), 2), 0.0)


def geo_azimut(azimut_projekt: float) -> float:
    """Geo-Korrektur beim Export: positiver Offset dreht gegen den Uhrzeigersinn."""
    return round((azimut_projekt + TRUE_NORTH_OFFSET) % 360, 1)


def baue_raeume() -> list:
    raeume = []
    for we in (1, 2):
        for nr, typ, name, geschoss, flaeche in WE_RAEUME:
            raeume.append({
                "id": f"R-WE{we}-{nr}",
                "dwe_uid": f"BSP1-WE{we}-{nr}",
                "name": f"{name} (WE{we})",
                "number": f"{we}.{nr}",
                "storey_ref": geschoss,
                "room_type_ref": typ,
                "zone_memberships": [
                    {"zone_type": "thermal", "zone_id": "Z-THERM-01"},
                    {"zone_type": "dwelling_unit", "zone_id": f"Z-WE{we}"},
                ],
                "heating_status": "heated",
                "area_ngf_m2": flaeche,
                "height_m": RAUMHOEHE,
                "volume_ve_m3": round(flaeche * RAUMHOEHE, 2),
            })
    # Garage: Nebenflaeche, gehoert keiner Wohneinheit und keiner thermischen Zone an.
    # Bewusst ohne zone_memberships — der Validator soll das melden duerfen.
    raeume.append({
        "id": "R-GAR-01",
        "dwe_uid": "BSP1-GAR-01",
        "name": "Garage",
        "number": "0.01",
        "storey_ref": "S-EG",
        "room_type_ref": "GARAGE",
        "zone_memberships": [],
        "heating_status": "unheated",
        "area_ngf_m2": 18.00,
        "height_m": RAUMHOEHE,
    })
    return raeume


def baue_element_groups() -> list:
    gruppen = []
    for gid, richtung, dist, konstruktion, anzahl in ELEMENT_GROUPS:
        az = AZIMUT_PROJEKT[richtung]
        nx, ny, nz = normale(az)
        ids = BELEGTE_INSTANZ_IDS.get(gid)
        mitglieder = []
        for i in range(anzahl):
            quelle = ids[i] if ids and i < len(ids) else f"{gid}-INST-{i + 1}"
            mitglieder.append({
                "source_id": quelle,
                "source_kind": "revit_element_id",
                "type_name": "Aussenwand 36,5" if gid.startswith("AW") else "Innenwand 17,5",
            })
        gruppen.append({
            "id": gid,
            "name": gid,
            "element_type": "wall",
            "fingerprint": {
                "normal_x": nx,
                "normal_y": ny,
                "normal_z": nz,
                "dist_m": dist,
                "coordinate_system": "project",
                "tolerance": {"angle_tolerance_deg": 1.0, "dist_tolerance_m": 0.02},
            },
            "construction_ref": konstruktion,
            "member_elements": mitglieder,
            "aggregates": {
                "member_count": len(mitglieder),
                "boundary_count": 0,
            },
        })
    return gruppen


def baue_sidecar() -> dict:
    raeume = baue_raeume()
    wohnflaeche = round(
        sum(r["area_ngf_m2"] for r in raeume if r["id"].startswith("R-WE")), 2
    )
    ngf_gesamt = round(sum(r["area_ngf_m2"] for r in raeume), 2)

    return {
        "schema_info": {"url": SIDECAR_URL, "version": "4.0.0"},
        "meta": {
            "project_name": "Beispiel1",
            "building_uid": "bsp1-0000-0000-0000-000000000001",
            "created_at": "2026-07-21T10:00:00Z",
            "ifc_file_ref": "model.ifc",
            "norm_editions": {"din_18599": "2018-09", "din_277": "2021-08", "geg": "2024"},
            "catalogs": [
                {"catalog_id": "adjacency_types", "catalog_version": "1.0.0",
                 "catalog_source": "core",
                 "dimension": {"type": "norm_edition", "value": "2018-09"}},
                {"catalog_id": "room_types", "catalog_version": "0.2.0",
                 "catalog_source": "core", "dimension": {"type": "none"}},
                {"catalog_id": "usage_profiles", "catalog_version": "1.0.0",
                 "catalog_source": "core",
                 "dimension": {"type": "norm_edition", "value": "2018-09"}},
            ],
            "true_north_offset_deg": TRUE_NORTH_OFFSET,
            "azimuth_reference": "geographic",
            "validation": {
                "level": "enriched",
                "validated_at": "2026-07-21T10:00:00Z",
                "ruleset_version": "0.1.0",
            },
            "source": {
                "origin": "REVIT_DYNAMO",
                "tool": "DWE Dynamo Export",
                "tool_version": "0.1.0-stufe1",
            },
        },
        "input": {
            "building": {
                "type": "residential",
                "subtype": "Doppelhaus, zwei Maisonette-Wohnungen",
                "ngf_m2": ngf_gesamt,
                "storeys_above_ground": 2,
                "storeys_below_ground": 0,
            },
            "storeys": [
                {"id": "S-EG", "name": "Erdgeschoss", "elevation_m": 0.00,
                 "height_m": RAUMHOEHE, "below_ground": False},
                {"id": "S-OG", "name": "Obergeschoss", "elevation_m": 2.75,
                 "height_m": RAUMHOEHE, "below_ground": False},
            ],
            "rooms": raeume,
            "zones": [
                {
                    "id": "Z-THERM-01",
                    "name": "Beheizte Zone Gesamtgebaeude",
                    "zone_type": "thermal",
                    "usage_profile_ref": "WG_R2",
                    "conditioned": True,
                    "area_m2": wohnflaeche,
                },
                {"id": "Z-WE1", "name": "Wohneinheit 1 (Maisonette)",
                 "zone_type": "dwelling_unit", "area_m2": round(wohnflaeche / 2, 2)},
                {"id": "Z-WE2", "name": "Wohneinheit 2 (Maisonette)",
                 "zone_type": "dwelling_unit", "area_m2": round(wohnflaeche / 2, 2)},
            ],
            "element_groups": baue_element_groups(),
            # Stufe 2d der Revit-Pipeline in Arbeit. Leer ist gueltig, haelt den
            # Container aber auf validation_level "draft".
            "boundaries": [],
            "constructions": [
                {"id": "C-AW-01", "name": "Aussenwand 36,5 Ziegel",
                 "source": "IFC", "origin_ref": "Aussenwand 36,5"},
                {"id": "C-IW-01", "name": "Innenwand 24 tragend",
                 "source": "IFC", "origin_ref": "Innenwand 24"},
                {"id": "C-IW-02", "name": "Innenwand 17,5 nicht tragend",
                 "source": "IFC", "origin_ref": "Innenwand 17,5"},
            ],
            "climate": {"try_region": "TRY04", "location_name": "Koeln"},
        },
        "sla_context": {
            "gebaeudeart": "WG",
            "we": 2,
            "bt": len(ELEMENT_GROUPS),
        },
    }


def baue_manifest(sidecar_bytes: bytes) -> dict:
    return {
        "manifest_info": {"url": MANIFEST_URL, "version": "4.0.0"},
        "container": {
            "format": "dwe-container",
            "container_id": "bsp1-container-0001",
            "project_name": "Beispiel1",
            "created_at": "2026-07-21T10:00:00Z",
            "created_by": {
                "tool": "DWE Dynamo Export",
                "version": "0.1.0-stufe1",
                "vendor": "DWE Beratung GmbH",
                "host_application": "Autodesk Revit 2026",
            },
        },
        "contents": {
            "sidecar": {
                "path": "energy.din18599.json",
                "schema_version": "4.0.0",
                "checksum": {
                    "algorithm": "sha256",
                    "value": hashlib.sha256(sidecar_bytes).hexdigest(),
                },
                "size_bytes": len(sidecar_bytes),
            }
        },
        "validation": {
            # Vom Validator ermittelt, nicht geschaetzt: Fachdaten sind
            # vollstaendig, erst die fehlende Angrenzungsmatrix blockiert weiter.
            "level": "enriched",
            "validated_at": "2026-07-21T10:00:00Z",
            "validator": {"name": "dwe-validate", "version": "0.1.0",
                          "ruleset_version": "0.1.0"},
            "findings": [
                {
                    "code": "BOUNDARIES_EMPTY",
                    "severity": "warning",
                    "message": "input.boundaries[] ist leer — ohne Angrenzungsmatrix "
                               "keine Huellflaeche und keine Energiebilanz. "
                               "Revit-Pipeline Stufe 2d ausstehend.",
                    "blocks_level": "geometry_ok",
                    "json_pointer": "/input/boundaries",
                },
                {
                    "code": "ROOM_WITHOUT_ZONE",
                    "severity": "info",
                    "message": "R-GAR-01 (Garage) hat keine zone_memberships. Bei "
                               "einer unbeheizten Nebenflaeche ist das zulaessig.",
                    "blocks_level": "enriched",
                    "json_pointer": "/input/rooms/22",
                },
            ],
        },
    }


def main() -> int:
    ZIEL.mkdir(parents=True, exist_ok=True)

    sidecar = baue_sidecar()
    sidecar_text = json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
    (ZIEL / "energy.din18599.json").write_text(sidecar_text, encoding="utf-8")

    manifest = baue_manifest(sidecar_text.encode("utf-8"))
    (ZIEL / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    raeume = sidecar["input"]["rooms"]
    wohn = sum(r["area_ngf_m2"] for r in raeume if r["id"].startswith("R-WE"))
    print(f"{ZIEL.relative_to(REPO)}/")
    print(f"  Raeume:          {len(raeume)}")
    print(f"  Wohnflaeche:     {wohn:.2f} m²  (Soll 240,96)")
    print(f"  element_groups:  {len(sidecar['input']['element_groups'])}")
    print(f"  Wandinstanzen:   {sum(len(g['member_elements']) for g in sidecar['input']['element_groups'])}")
    print(f"  boundaries:      {len(sidecar['input']['boundaries'])} (Stufe 2d ausstehend)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
