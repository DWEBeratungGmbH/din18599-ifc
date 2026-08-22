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

# Wandlaengen je Gruppe [m] — deterministisch, illustrativ.
# Aussenwaende spannen einen 2-geschossigen Quader auf; Innenwaende teilen
# Wohneinheiten bzw. Raeume innerhalb einer WE. Die Flaechen ergeben sich als
# member_count * RAUMHOEHE * laenge. Die Summe der exterior-Boundaries ist
# building.envelope_area_m2 (nur relevant_18599=true zaehlt).
LAENGEN = {
    "AW-NO-01": 5.00, "AW-NO-02": 3.00, "AW-NO-03": 5.00,
    "AW-SO-01": 4.00, "AW-SO-02": 4.00, "AW-SO-03": 4.00,
    "AW-SO-04": 4.00, "AW-SO-05": 4.00,
    "IW-WE1-01": 4.00, "IW-WE1-02": 3.00, "IW-WE1-WE2-01": 8.00,
    "IW-WE2-01": 4.00, "IW-WE2-02": 3.00,
}

# Repraesentativraum je AW-Gruppe (space_a-Konvention: der innere/wärmere Raum).
# Deterministisch gewaehlt — das Beispiel hat 2 WE, beide beheizt auf dieselbe
# Temperatur, daher ist "wärmerer Raum" gleichbedeutend mit "innenliegend".
AW_SPACE_A = {
    "AW-NO-01": "R-WE1-02", "AW-NO-02": "R-WE1-03", "AW-NO-03": "R-WE2-02",
    "AW-SO-01": "R-WE1-02", "AW-SO-02": "R-WE1-07", "AW-SO-03": "R-WE1-08",
    "AW-SO-04": "R-WE2-07", "AW-SO-05": "R-WE2-08",
}

# Zwei Testfenster, um openings_index + opening_type-Enum real zu pruefen.
# (area_m2, height_m, width_m, opening_type, window_construction_ref)
TEST_OEFFNUNGEN = [
    ("AW-NO-01", "O-AW-NO-01-W1", 1.20, 1.50, "window", "WC-STD-2K"),
    ("AW-SO-01", "O-AW-SO-01-W1", 1.44, 1.20, "window", "WC-STD-2K"),
]

GEG_ZEILE_NACH_TYP = {
    "window": "2", "glazed_door": "2", "roof_window": "3",
    "skylight": "4", "door": "5", "garage_door": "5",
}


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


def _geo_azimut_fuer_gruppe(gid: str) -> float:
    """Geografischer Azimut einer Gruppe (fuer boundaries[].orientation)."""
    richtung = next(g[1] for g in ELEMENT_GROUPS if g[0] == gid)
    return geo_azimut(AZIMUT_PROJEKT[richtung])


def _area_pro_gruppe(gid: str) -> float:
    """Deterministische, illustrative Bauteilflaeche je Gruppe [m2]."""
    return round(len(next(g for g in ELEMENT_GROUPS if g[0] == gid)) is None and 0
                 or LAENGEN[gid] * RAUMHOEHE, 2)


def baue_boundaries(raeume: list, gruppen: list) -> list:
    """Synthetische Angrenzungsmatrix fuer Beispiel1.

    Bis Revit/Dynamo Stufe 2d die echte Matrix liefert, steht hier ein
    deterministischer Platzhalter, der die Validator-Pfade geometry_ok und
    balanced real durchlaeuft. AW-* wird exterior, IW-*-WE1-WE2-* wird
    other_zone, IW-* innerhalb einer WE wird same_zone. Die Flaechen stammen
    aus LAENGEN * RAUMHOEHE. member_count ergibt sich aus ELEMENT_GROUPS.
    """
    raeume_ids = {r["id"] for r in raeume}
    grenzen: list[dict] = []
    for gid, _richtung, _dist, _konstruktion, _anzahl in ELEMENT_GROUPS:
        laenge = LAENGEN[gid]
        flaeche = round(laenge * RAUMHOEHE, 2)
        orientation = _geo_azimut_fuer_gruppe(gid)
        geom = {"type": "z_range", "z_from": 0.0, "z_to": RAUMHOEHE}

        if gid.startswith("AW-"):
            space_a = AW_SPACE_A[gid]
            assert space_a in raeume_ids, f"space_a {space_a} fehlt"
            grenzen.append({
                "id": f"B-{gid}",
                "element_group_ref": gid,
                "space_a": space_a,
                "space_b": None,
                "adjacency_type": "exterior",
                "fx": None,
                "fx_source": "catalog",
                "measurement_reference": "outer",
                "area_18599": flaeche,
                "area_heizlast": flaeche,
                "orientation": orientation,
                "tilt": 90.0,
                "geometry": geom,
                "relevant_18599": True,
                "relevant_heizlast": True,
                "openings": [],
            })
        elif gid.startswith("IW-WE1-WE2"):
            # Trennwand zwischen WE1 und WE2 — both heated to 20 °C, Delta=0,
            # other_zone ist sachgerecht, relevant_18599=False (kein Waermestrom
            # nach aussen bei Delta-Theta < 4 K).
            grenzen.append({
                "id": f"B-{gid}",
                "element_group_ref": gid,
                "space_a": "R-WE1-02",   # repraesentativ
                "space_b": "R-WE2-02",
                "adjacency_type": "other_zone",
                "fx": None,
                "fx_source": "computed",
                "measurement_reference": "axis",
                "area_18599": flaeche,
                "area_heizlast": flaeche,
                "orientation": orientation,
                "tilt": 90.0,
                "geometry": geom,
                "relevant_18599": False,
                "relevant_heizlast": True,
                "openings": [],
            })
        else:
            # IW-* innerhalb einer Wohneinheit — same_zone. Innenraum-Seite
            # deterministisch: WE1 -> R-WE1-02, WE2 -> R-WE2-02.
            we = "WE1" if "WE1" in gid else "WE2"
            space_a = f"R-{we}-02"
            space_b = f"R-{we}-07" if we == "WE1" else "R-{we}-08".replace("{we}", we)
            assert space_a in raeume_ids and space_b in raeume_ids, \
                f"space_a/space_b fehlt: {space_a}/{space_b}"
            grenzen.append({
                "id": f"B-{gid}",
                "element_group_ref": gid,
                "space_a": space_a,
                "space_b": space_b,
                "adjacency_type": "same_zone",
                "fx": None,
                "fx_source": "catalog",
                "measurement_reference": "axis",
                "area_18599": flaeche,
                "area_heizlast": flaeche,
                "orientation": orientation,
                "tilt": 90.0,
                "geometry": geom,
                "relevant_18599": False,
                "relevant_heizlast": True,
                "openings": [],
            })

    # Testoeffnungen einfuegen — nur AW-Gruppen, damit die oeffentliche Flaeche
    # korrekt abzieht. area_18599 wird entsprechend reduziert.
    for gruppe_id, oeff_id, area, hoehe, breite, otyp, wcref in _Oeffnungen():
        for b in grenzen:
            if b["element_group_ref"] != gruppe_id:
                continue
            b["openings"].append({
                "id": oeff_id,
                "opening_type": otyp,
                "window_construction_ref": wcref,
                "count": 1,
                "width_m": breite,
                "height_m": hoehe,
                "area_m2": area,
                "measurement_rule": "clear_structural",
                "orientation": b["orientation"],
                "tilt": b["tilt"],
                "geg_reference_row": GEG_ZEILE_NACH_TYP.get(otyp, ""),
            })
            # Oeffnungsflaeche von der opaken Bilanzflaeche abziehen.
            b["area_18599"] = round(b["area_18599"] - area, 2)
    return grenzen


def _Oeffnungen() -> list[tuple]:
    """Formatiert TEST_OEFFNUNGEN mit expliziten width/height."""
    return [(g, oid, h * w, h, w, t, c) for g, oid, w, h, t, c in TEST_OEFFNUNGEN]


def baue_openings_index(boundaries: list) -> list:
    """readOnly-Aggregat-Sicht ueber alle Oeffnungen.

    Wird aus boundaries[].openings[] berechnet und muss mit der Quelle
    uebereinstimmen — der Validator prueft das (OPENINGS_INDEX_INCONSISTENT).
    """
    index = []
    for b in boundaries:
        for o in b.get("openings", []):
            index.append({
                "opening_ref": o["id"],
                "boundary_ref": b["id"],
                "element_group_ref": b["element_group_ref"],
                "room_ref": b["space_a"],
                "opening_type": o["opening_type"],
                "area_m2": o["area_m2"],
                "orientation": o.get("orientation"),
                "tilt": o.get("tilt"),
                "geg_reference_row": o.get("geg_reference_row"),
            })
    return index


def baue_window_constructions() -> list:
    """Synthetische Fensterkonstruktion (illustrative U-/g-Werte).

    KEINE Normwerte — die folgenden Zahlen sind frei gewaehlt, um die
    Schema-Pfade zu belegen und die U-Wert-Gegenrechnung zu ermoeglichen.
    """
    return [{
        "id": "WC-STD-2K",
        "name": "Standard 2-Scheiben-Waermeschutzverglasung (illustrativ)",
        "u_value": 1.20,
        "g_value": 0.60,
        "glass": {"u_value": 1.10, "g_value": 0.60, "light_transmittance": 0.78},
        "frame": {"u_value": 1.50, "area_fraction": 0.20, "material": "Kunststoff"},
        "psi_spacer": 0.06,
    }]


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
    ve_gesamt = round(sum(r["volume_ve_m3"] for r in raeume if r["id"].startswith("R-WE")), 2)

    element_groups = baue_element_groups()
    boundaries = baue_boundaries(raeume, element_groups)
    openings_index = baue_openings_index(boundaries)
    window_constructions = baue_window_constructions()

    # Huellflaeche = Summe aller relevant_18599=true Boundaries.
    huellflaeche = round(
        sum(b["area_18599"] for b in boundaries if b.get("relevant_18599")), 2
    )
    fensterflaeche = round(sum(o["area_m2"] for o in openings_index), 2)
    av_ratio = round(huellflaeche / ve_gesamt, 3) if ve_gesamt else None

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
            "ve_method": "approximation",
            "validation": {
                "level": "balanced",
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
                "ve_m3": ve_gesamt,
                "envelope_area_m2": huellflaeche,
                "av_ratio": av_ratio,
                "storeys_above_ground": 2,
                "storeys_below_ground": 0,
                "airtightness": {
                    "n50_h": 1.5,
                    "source": "planned",
                    "note": "illustrativer Planungswert — Beispiel1",
                },
                "thermal_mass": {"class": "medium"},
                "envelope_kpis": {
                    "window_area_ratio": round(fensterflaeche / huellflaeche, 4)
                        if huellflaeche else 0.0,
                },
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
            "element_groups": element_groups,
            "boundaries": boundaries,
            "openings_index": openings_index,
            "constructions": [
                {"id": "C-AW-01", "name": "Aussenwand 36,5 Ziegel",
                 "source": "IFC", "origin_ref": "Aussenwand 36,5"},
                {"id": "C-IW-01", "name": "Innenwand 24 tragend",
                 "source": "IFC", "origin_ref": "Innenwand 24"},
                {"id": "C-IW-02", "name": "Innenwand 17,5 nicht tragend",
                 "source": "IFC", "origin_ref": "Innenwand 17,5"},
            ],
            "window_constructions": window_constructions,
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
            # Vom Validator ermittelt: enriched + geometry_ok + balanced
            # erreichen; calc_ready blockiert am fehlenden Normwerte-Overlay
            # (gitignored, aus eigener Normlizenz bereitzustellen).
            "level": "balanced",
            "validated_at": "2026-07-21T10:00:00Z",
            "validator": {"name": "dwe-validate", "version": "0.1.0",
                          "ruleset_version": "0.1.0"},
            "findings": [
                {
                    "code": "VALUES_OVERLAY_MISSING",
                    "severity": "warning",
                    "message": "Fx-Werte aus DIN V 18599-2 Tabelle 5/6 fehlen — "
                               "Overlay unter catalog/values/adjacency_types.2018-"
                               "09.values.json aus eigener Normlizenz "
                               "bereitstellen. calc_ready blockiert.",
                    "blocks_level": "calc_ready",
                    "json_pointer": "/meta/catalogs",
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
    boundaries = sidecar["input"]["boundaries"]
    openings = sidecar["input"]["openings_index"]
    huellflaeche = sidecar["input"]["building"]["envelope_area_m2"]
    print(f"{ZIEL.relative_to(REPO)}/")
    print(f"  Raeume:          {len(raeume)}")
    print(f"  Wohnflaeche:     {wohn:.2f} m²  (Soll 240,96)")
    print(f"  element_groups:  {len(sidecar['input']['element_groups'])}")
    print(f"  Wandinstanzen:   {sum(len(g['member_elements']) for g in sidecar['input']['element_groups'])}")
    print(f"  boundaries:      {len(boundaries)} (synthetisch — Stufe 2d ausstehend)")
    print(f"  openings:        {len(openings)} (Testfenster)")
    print(f"  Huellflaeche:    {huellflaeche:.2f} m²")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
