"""
IFC -> v4.0-Sidecar-Skelett-Parser (Level ``draft``)

Erzeugt aus einer NACKTEN IFC-Datei (ohne mitgelieferten Sidecar) ein strukturell
gueltiges v4.0-Sidecar auf Level ``draft`` — den Eingangs-Kanal 2 "IFC-Upload" der
Gebaeudeakte. Ein Berater zieht das Skelett danach mensch-gefuehrt (Anreicherungs-
Assistent) hoch.

Vertrag: ``docs/v4/SPEC-ifc-skelett-parser-v4.md`` §9.1 (gelockte Master-
Entscheidungen). Kurzfassung der harten Leitplanken:

* REIN GEOMETRIE (ADR-033). Keine Anreicherungsregeln: kein ``adjacency_type``,
  kein Raumtyp->theta/Lueftung, keine Konstruktions-/U-Wert-Aufloesung, kein ``fx``,
  keine Waermebruecken, keine tolerante Gruppen-Vereinigung.
* ``element_groups`` als TRIVIALE 1:1-Gruppen (ein IFC-Element = eine Gruppe). Der
  ``fingerprint`` wird aus der Geometrie DIESES einen Elements berechnet, in voller
  Praezision (keine Anzeige-Rundung). Die tolerante Gruppierung ist Sache der
  spaeteren Core-Engine (OFFEN-2).
* ``boundaries`` bleiben LEER (bewusst deferred, OFFEN-1/§1.1).
* ``room.heating_status`` = Platzhalter ``"heated"`` (OFFEN-4 Variante B). Der
  Validator meldet ``HEATING_STATUS_UNCONFIRMED`` und blockiert damit ``geometry_ok``,
  bis der Assistent die Konditionierung bestaetigt.
* ``building.type`` wird NICHT aus der IFC erraten (OFFEN-5). Der Stammdaten-Wizard
  ist die Quelle. Liegt kein Wert vor, setzt der Parser einen merge-sicheren
  Platzhalter, den der Wizard ueberschreibt — er ueberschreibt einen vorhandenen
  Wert nie.
* Openings (IfcWindow/IfcDoor) haben im ``draft`` keinen Boundary-Platz (OFFEN-8).
  Ihre Parent-Child-Relation (Fenster -> Wand-GUID) wird in den
  ``member_elements``-Metadaten der Host-Wand-Gruppe mitgefuehrt, damit der
  Assistent sie spaeter zuordnen kann.

Die reine Geometrie-Extraktion ist konzeptionell aus ``ifc_parser.py`` uebernommen
(Flaeche, Normale, Parent-Child, Material-Layer), aber neu und praezise
implementiert: der Alt-Parser rundet Normale/Flaeche auf 1-2 Nachkommastellen und
kennt ``fingerprint.dist_m`` nicht.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Optional

import ifcopenshell
import ifcopenshell.geom

# Material-Layer-Extraktion wird wiederverwendet (§5). Relativer Import, mit
# Fallback fuer den direkten Skript-Aufruf ausserhalb des Pakets.
try:  # pragma: no cover - Importpfad haengt vom Aufrufkontext ab
    from .ifc_material_extractor import extract_material_layers
except ImportError:  # pragma: no cover
    from ifc_material_extractor import extract_material_layers


SCHEMA_URL = "https://din18599-ifc.de/schema/v4.0/sidecar"
SCHEMA_VERSION = "4.0.0"
PARSER_TOOL = "din18599-ifc IFC v4 Skelett-Parser"
PARSER_VERSION = "0.1.0"

# Schema-Default-Toleranzen. Dokumentieren, WOMIT gruppiert WUERDE — der Parser
# selbst gruppiert nicht (1:1), die Vereinigung ist Core-Engine-Sache.
DEFAULT_ANGLE_TOLERANCE_DEG = 1.0
DEFAULT_DIST_TOLERANCE_M = 0.02

# Merge-sicherer Platzhalter fuer building.type, falls kein Wizard-Wert vorliegt
# (OFFEN-5). Bewusst nicht aus der IFC abgeleitet; der Wizard ueberschreibt ihn.
BUILDING_TYPE_PLACEHOLDER = "non_residential"


# --------------------------------------------------------------------------- #
# Geometrie-Grundbausteine (reine Berechnung, keine Anreicherung)
# --------------------------------------------------------------------------- #

def _iter_triangles(verts: list, faces: list):
    """Iteriert die Dreiecke eines ifcopenshell-Mesh als Punkt-Tripel."""
    for i in range(0, len(faces), 3):
        a, b, c = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
        yield (
            (verts[a], verts[a + 1], verts[a + 2]),
            (verts[b], verts[b + 1], verts[b + 2]),
            (verts[c], verts[c + 1], verts[c + 2]),
        )


def _tri_normal_area(p1, p2, p3):
    """Einheitsnormale und Flaeche eines Dreiecks (Kreuzprodukt/2)."""
    ux, uy, uz = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
    vx, vy, vz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    laenge = math.sqrt(nx * nx + ny * ny + nz * nz)
    if laenge < 1e-12:
        return None, 0.0
    return (nx / laenge, ny / laenge, nz / laenge), 0.5 * laenge


def _canonical(n):
    """Kanonisiert eine Normale in die positive Halbkugel.

    Vorne- und Rueckseite eines Bauteils (antiparallele Normalen) landen so in
    derselben Ebenenrichtung. Das Vorzeichen richtet sich nach der ersten
    signifikanten Achse (x, dann y, dann z) — deterministisch und mit dem im
    Schema beschriebenen Kanonisierungs-Kipppunkt bei normal_x nahe 0 vertraeglich.
    """
    for k in n:
        if abs(k) > 1e-9:
            return tuple(-c for c in n) if k < 0 else tuple(n)
    return tuple(n)


def _centroid(verts: list):
    """Schwerpunkt aller Mesh-Knoten (mittlere Ebene eines Solids)."""
    anzahl = len(verts) // 3
    if anzahl == 0:
        return (0.0, 0.0, 0.0)
    sx = sum(verts[0::3])
    sy = sum(verts[1::3])
    sz = sum(verts[2::3])
    return (sx / anzahl, sy / anzahl, sz / anzahl)


def _dominant_plane(verts: list, faces: list):
    """Dominante Ebene eines Mesh als (Normale, dist_m) in VOLLER Praezision.

    Dreiecke werden nach ihrer kanonischen Normalenrichtung gebucketet und je
    Bucket flaechengewichtet gemittelt; der flaechengroesste Bucket gewinnt. Bei
    Waenden ist das die Wandebene, bei flachen Decken die Horizontale, bei einer
    geneigten Dachflaeche die Schraege. ``dist_m`` ist der Abstand der durch den
    Bauteilschwerpunkt laufenden Ebene vom Projektursprung (Mittelebenen-Konvention,
    passend zu den Wand-Achsabstaenden im Referenzbeispiel).
    """
    buckets: dict[tuple, list] = {}
    for p1, p2, p3 in _iter_triangles(verts, faces):
        n, area = _tri_normal_area(p1, p2, p3)
        if n is None or area <= 0.0:
            continue
        cn = _canonical(n)
        key = (round(cn[0], 2), round(cn[1], 2), round(cn[2], 2))
        acc = buckets.setdefault(key, [0.0, 0.0, 0.0, 0.0])
        acc[0] += area
        acc[1] += cn[0] * area
        acc[2] += cn[1] * area
        acc[3] += cn[2] * area
    if not buckets:
        return None
    _, wx, wy, wz = buckets[max(buckets, key=lambda k: buckets[k][0])]
    laenge = math.sqrt(wx * wx + wy * wy + wz * wz)
    if laenge < 1e-12:
        return None
    normal = _canonical((wx / laenge, wy / laenge, wz / laenge))
    cx, cy, cz = _centroid(verts)
    dist = normal[0] * cx + normal[1] * cy + normal[2] * cz
    return normal, dist


def _skin_area_up(verts: list, faces: list, nz_min: float = 0.5) -> float:
    """Flaeche der nach oben zeigenden Skin (Grundriss bzw. Dachhaut).

    Fuer flache Decken die Deckenoberflaeche (= Grundrissflaeche), fuer ein
    Satteldach beide Schraegen zusammen, fuer einen Raum-Solid die Deckenflaeche
    (= Grundflaeche bei senkrechten Waenden).
    """
    total = 0.0
    for p1, p2, p3 in _iter_triangles(verts, faces):
        n, area = _tri_normal_area(p1, p2, p3)
        if n is not None and n[2] > nz_min:
            total += area
    return total


def _wall_face_area(verts: list, faces: list) -> float:
    """Flaeche der dominanten vertikalen Bauteilebene, EINE Seite.

    Nur nahezu senkrechte Dreiecke; die dominante Richtung wird gebucketet und
    innerhalb des Buckets nach Vorder-/Rueckseite getrennt, damit die
    zurueckgegebene Flaeche eine Wandseite ist (nicht die doppelte Solid-Huelle).
    """
    buckets: dict[tuple, list] = {}
    for p1, p2, p3 in _iter_triangles(verts, faces):
        n, area = _tri_normal_area(p1, p2, p3)
        if n is None or abs(n[2]) >= 0.5:
            continue
        cn = _canonical(n)
        key = (round(cn[0], 2), round(cn[1], 2), round(cn[2], 2))
        acc = buckets.setdefault(key, [0.0, 0.0])
        if n[0] * cn[0] + n[1] * cn[1] + n[2] * cn[2] >= 0.0:
            acc[0] += area
        else:
            acc[1] += area
    if not buckets:
        return 0.0
    aligned, anti = max(buckets.values(), key=lambda v: v[0] + v[1])
    return max(aligned, anti)


def _element_area(verts: list, faces: list, element_type: str) -> float:
    """Repraesentative Bauteilflaeche je nach Typ (rohe Geometrie, brutto).

    Waende/Stuetzen/Traeger ueber die dominante vertikale Ebene, flaechige
    Bauteile (Decken/Dach/Boden) ueber die obere Skin. Oeffnungen werden auf
    ``draft`` NICHT abgezogen — das ist Boundary-/Anreicherungsarbeit.
    """
    if element_type in ("wall", "column", "beam"):
        return _wall_face_area(verts, faces)
    flaeche = _skin_area_up(verts, faces)
    if flaeche <= 0.0:
        flaeche = _wall_face_area(verts, faces)
    return flaeche


def _bbox_height(verts: list) -> Optional[float]:
    """Z-Ausdehnung (lichte Hoehe naeherungsweise) aus der Bounding-Box."""
    if len(verts) < 3:
        return None
    zs = verts[2::3]
    hoehe = max(zs) - min(zs)
    return hoehe if hoehe > 0 else None


# --------------------------------------------------------------------------- #
# IFC-Typ -> v4.0-element_type (OFFEN-7: nur PredefinedType-Direktabbildung)
# --------------------------------------------------------------------------- #

def _map_element_type(ifc_type: str, predefined_type: Optional[str]) -> str:
    """Bildet den IFC-Bauteiltyp auf das v4.0-``element_type``-Enum ab.

    Fuer ``IfcSlab`` gilt die gelockte Regel (OFFEN-7): NUR die direkte
    ``PredefinedType``-Abbildung (FLOOR/ROOF/BASESLAB); alles andere landet in
    ``other``. Die Feinklassifikation floor/ceiling/slab_ground/slab_basement ist
    Anreicherung und Sache des Assistenten.
    """
    if ifc_type in ("IfcWall", "IfcWallStandardCase"):
        return "wall"
    if ifc_type == "IfcRoof":
        return "roof"
    if ifc_type == "IfcColumn":
        return "column"
    if ifc_type == "IfcBeam":
        return "beam"
    if ifc_type == "IfcSlab":
        pt = (predefined_type or "").upper()
        if "ROOF" in pt:
            return "roof"
        if "BASESLAB" in pt:
            return "slab_ground"
        if "FLOOR" in pt:
            return "floor"
        return "other"
    return "other"


_TYPE_PREFIX = {
    "wall": "W",
    "roof": "R",
    "floor": "F",
    "ceiling": "D",
    "slab_ground": "BO",
    "slab_basement": "KB",
    "column": "ST",
    "beam": "BT",
    "other": "E",
}


# --------------------------------------------------------------------------- #
# IFC-Hilfen
# --------------------------------------------------------------------------- #

def _predefined_type(element) -> Optional[str]:
    if hasattr(element, "PredefinedType") and element.PredefinedType is not None:
        return str(element.PredefinedType)
    return None


def _type_name(element) -> Optional[str]:
    """Bauteil-/Familienname aus dem Autorensystem (IsTypedBy oder Name)."""
    try:
        for rel in getattr(element, "IsTypedBy", []) or []:
            typ = rel.RelatingType
            if typ is not None and getattr(typ, "Name", None):
                return typ.Name
    except Exception:
        pass
    return getattr(element, "Name", None)


def _dms_to_decimal(t) -> Optional[float]:
    """IFC-Grad/Minute/Sekunde-Tupel in Dezimalgrad."""
    if not t:
        return None
    try:
        deg, mn, sec = float(t[0]), float(t[1]), float(t[2])
        frac = float(t[3]) / 1_000_000.0 if len(t) > 3 else 0.0
        val = abs(deg) + mn / 60.0 + (sec + frac) / 3600.0
        return -val if deg < 0 else val
    except Exception:
        return None


def _true_north_offset(ifc_file) -> Optional[float]:
    """True-North-Drehung des Projektsystems (dokumentarisch, §4)."""
    try:
        for ctx in ifc_file.by_type("IfcGeometricRepresentationContext"):
            tn = getattr(ctx, "TrueNorth", None)
            if tn is not None and getattr(tn, "DirectionRatios", None):
                dr = tn.DirectionRatios
                return math.degrees(math.atan2(dr[0], dr[1]))
    except Exception:
        return None
    return None


def _build_host_map(ifc_file) -> dict[str, str]:
    """Oeffnungs-GUID -> Host-Wand-GUID (IfcRelVoids + IfcRelFills).

    IfcWindow/IfcDoor -> IfcRelFillsElement -> IfcOpeningElement
    IfcOpeningElement -> IfcRelVoidsElement -> IfcWall
    """
    opening_to_wall: dict[str, str] = {}
    for rel in ifc_file.by_type("IfcRelVoidsElement"):
        if rel.RelatingBuildingElement and rel.RelatedOpeningElement:
            opening_to_wall[rel.RelatedOpeningElement.GlobalId] = (
                rel.RelatingBuildingElement.GlobalId
            )
    element_to_host: dict[str, str] = {}
    for rel in ifc_file.by_type("IfcRelFillsElement"):
        if rel.RelatingOpeningElement and rel.RelatedBuildingElement:
            wall = opening_to_wall.get(rel.RelatingOpeningElement.GlobalId)
            if wall:
                element_to_host[rel.RelatedBuildingElement.GlobalId] = wall
    return element_to_host


def _space_storey_map(ifc_file) -> dict[str, str]:
    """IfcSpace-GUID -> IfcBuildingStorey-GUID (Aggregation + Containment)."""
    result: dict[str, str] = {}
    for storey in ifc_file.by_type("IfcBuildingStorey"):
        for rel in getattr(storey, "IsDecomposedBy", []) or []:
            for obj in rel.RelatedObjects:
                if obj.is_a("IfcSpace"):
                    result[obj.GlobalId] = storey.GlobalId
        for rel in getattr(storey, "ContainsElements", []) or []:
            for obj in rel.RelatedElements:
                if obj.is_a("IfcSpace"):
                    result[obj.GlobalId] = storey.GlobalId
    return result


# --------------------------------------------------------------------------- #
# Hauptfunktion
# --------------------------------------------------------------------------- #

def parse_ifc_to_sidecar_v4(
    ifc_path: str,
    *,
    ifc_file_ref: str = "model.ifc",
    base: Optional[dict] = None,
    building_type: Optional[str] = None,
    tool_version: str = PARSER_VERSION,
) -> dict:
    """Parst eine nackte IFC-Datei in ein v4.0-Sidecar (Level ``draft``).

    Args:
        ifc_path: Pfad zur IFC-Datei.
        ifc_file_ref: Container-relativer Pfad, der in ``meta.ifc_file_ref`` landet.
        base: Optionales Bestands-Sidecar (z.B. aus dem Stammdaten-Wizard). Der
            Parser merged Geometrie hinein und laesst ``input.building.type`` und
            bestehende ``meta``-Kopfdaten unangetastet (OFFEN-5).
        building_type: Optionaler Gebaeudetyp aus dem Wizard. Vorrang vor ``base``;
            fehlt beides, wird ein merge-sicherer Platzhalter gesetzt.
        tool_version: Version, die in ``meta.source.tool_version`` protokolliert wird.

    Returns:
        Das v4.0-Sidecar als ``dict`` (nacktes JSON, OFFEN-6).
    """
    ifc_file = ifcopenshell.open(ifc_path)

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    # Geometrie-Cache: GUID -> (verts, faces). Einmal je Element rechnen.
    def _shape(element):
        try:
            shape = ifcopenshell.geom.create_shape(settings, element)
            return list(shape.geometry.verts), list(shape.geometry.faces)
        except Exception:
            return None, None

    # ---- Kopfdaten -------------------------------------------------------- #
    projekte = ifc_file.by_type("IfcProject")
    project_name = (projekte[0].Name if projekte and projekte[0].Name
                    else ifc_file_ref)

    # ---- Geschosse -------------------------------------------------------- #
    ifc_storeys = list(ifc_file.by_type("IfcBuildingStorey"))
    # Deterministische Reihenfolge: nach Elevation, dann GUID.
    ifc_storeys.sort(key=lambda s: (getattr(s, "Elevation", 0.0) or 0.0,
                                    s.GlobalId))
    storey_id_by_guid: dict[str, str] = {}
    storeys_out: list[dict] = []
    for idx, st in enumerate(ifc_storeys, start=1):
        sid = f"S{idx}"
        storey_id_by_guid[st.GlobalId] = sid
        elev = getattr(st, "Elevation", None)
        eintrag: dict[str, Any] = {
            "id": sid,
            "ifc_guid": st.GlobalId,
            "name": st.Name or sid,
        }
        if elev is not None:
            eintrag["elevation_m"] = float(elev)
            # Geometrische Heuristik, kein Fachurteil (§4).
            eintrag["below_ground"] = float(elev) < 0.0
        storeys_out.append(eintrag)

    storeys_above = sum(1 for s in storeys_out
                        if not s.get("below_ground", False))
    storeys_below = sum(1 for s in storeys_out if s.get("below_ground", False))

    # ---- element_groups (1:1) + Openings-Metadaten ----------------------- #
    host_map = _build_host_map(ifc_file)

    # Bauteil-GUID -> Gruppen-Objekt (fuer das Anhaengen der Openings).
    gruppe_by_guid: dict[str, dict] = {}
    element_groups: list[dict] = []

    # Reihenfolge je Typ deterministisch nach GUID -> stabile IDs + Idempotenz.
    zaehler: dict[str, int] = {}

    bauteil_typen = ["IfcWall", "IfcRoof", "IfcSlab", "IfcColumn", "IfcBeam"]
    bauteile = []
    for ifc_type in bauteil_typen:
        for el in ifc_file.by_type(ifc_type):
            # IfcWallStandardCase kommt ueber IfcWall bereits mit; keine Doppelung.
            bauteile.append(el)
    # Nach GUID sortieren fuer stabile Nummerierung ueber Laeufe hinweg.
    bauteile.sort(key=lambda e: e.GlobalId)

    for el in bauteile:
        ifc_type = el.is_a()
        etype = _map_element_type(ifc_type, _predefined_type(el))
        prefix = _TYPE_PREFIX.get(etype, "E")
        zaehler[prefix] = zaehler.get(prefix, 0) + 1
        gid = f"{prefix}-{zaehler[prefix]:04d}"

        verts, faces = _shape(el)
        ebene = _dominant_plane(verts, faces) if verts and faces else None
        if ebene is None:
            # Ohne belastbare Ebene keine gueltige Gruppe (fingerprint required).
            # Dach ohne eigene Geometrie: Flaeche/Ebene aus Kind-Slabs (§4).
            continue
        normal, dist = ebene
        area = _element_area(verts, faces, etype) if verts and faces else 0.0

        member = {
            "source_id": el.GlobalId,
            "source_kind": "ifc_guid",
        }
        tname = _type_name(el)
        if tname:
            member["type_name"] = tname
        if area > 0:
            member["area_m2"] = round(area, 3)

        gruppe: dict[str, Any] = {
            "id": gid,
            "name": el.Name or gid,
            "element_type": etype,
            "fingerprint": {
                # VOLLE Praezision — keine Anzeige-Rundung (§2.4 / Schema Z. 463).
                "normal_x": normal[0],
                "normal_y": normal[1],
                "normal_z": normal[2],
                "dist_m": dist,
                "coordinate_system": "project",
                "tolerance": {
                    "angle_tolerance_deg": DEFAULT_ANGLE_TOLERANCE_DEG,
                    "dist_tolerance_m": DEFAULT_DIST_TOLERANCE_M,
                },
            },
            "member_elements": [member],
            "aggregates": {
                "member_count": 1,
                "boundary_count": 0,
            },
        }
        if area > 0:
            gruppe["aggregates"]["area_total_m2"] = round(area, 3)

        gruppe_by_guid[el.GlobalId] = gruppe
        element_groups.append(gruppe)

    # ---- Openings (IfcWindow/IfcDoor) — OFFEN-8 -------------------------- #
    # Kein Boundary-Platz auf draft. Die Parent-Child-Relation wird als
    # markierte member_elements-Metadaten an der Host-Wand-Gruppe mitgefuehrt.
    openings = []
    for ifc_type in ("IfcWindow", "IfcDoor"):
        for el in ifc_file.by_type(ifc_type):
            openings.append(el)
    openings.sort(key=lambda e: e.GlobalId)

    unassigned: list[dict] = []
    for el in openings:
        ifc_type = el.is_a()
        otype = "window" if ifc_type == "IfcWindow" else "door"
        verts, faces = _shape(el)
        area = _wall_face_area(verts, faces) if verts and faces else 0.0

        rider = {
            "source_id": el.GlobalId,
            "source_kind": "ifc_guid",
            "type_name": _type_name(el) or ifc_type,
            # Metadaten (additiv, schema-vertraeglich): kennzeichnet den Eintrag
            # als Oeffnung, nicht als Wand-Instanz, und traegt die Host-Relation.
            "role": "hosted_opening",
            "opening_type": otype,
        }
        if area > 0:
            rider["area_m2"] = round(area, 3)

        host_guid = host_map.get(el.GlobalId)
        host_gruppe = gruppe_by_guid.get(host_guid) if host_guid else None
        if host_gruppe is not None:
            rider["host_element_group_ref"] = host_gruppe["id"]
            rider["host_ifc_guid"] = host_guid
            host_gruppe["member_elements"].append(rider)
        else:
            # Kein aufloesbarer Host -> eigene 'other'-Gruppe mit realem
            # Fingerprint, damit nichts verloren geht (Fallback; im Regelfall leer).
            rider["host_element_group_ref"] = None
            unassigned.append((el, rider, verts, faces))

    for el, rider, verts, faces in unassigned:
        ebene = _dominant_plane(verts, faces) if verts and faces else None
        if ebene is None:
            continue
        normal, dist = ebene
        zaehler["E"] = zaehler.get("E", 0) + 1
        gid = f"E-{zaehler['E']:04d}"
        element_groups.append({
            "id": gid,
            "name": el.Name or gid,
            "element_type": "other",
            "fingerprint": {
                "normal_x": normal[0],
                "normal_y": normal[1],
                "normal_z": normal[2],
                "dist_m": dist,
                "coordinate_system": "project",
                "tolerance": {
                    "angle_tolerance_deg": DEFAULT_ANGLE_TOLERANCE_DEG,
                    "dist_tolerance_m": DEFAULT_DIST_TOLERANCE_M,
                },
            },
            "member_elements": [rider],
            "aggregates": {"member_count": 0, "boundary_count": 0},
        })

    # ---- Raeume (IfcSpace) — OFFEN-4 Variante B -------------------------- #
    space_storey = _space_storey_map(ifc_file)
    ifc_spaces = list(ifc_file.by_type("IfcSpace"))
    ifc_spaces.sort(key=lambda s: s.GlobalId)
    rooms_out: list[dict] = []
    for idx, sp in enumerate(ifc_spaces, start=1):
        verts, faces = _shape(sp)
        area = _skin_area_up(verts, faces) if verts and faces else 0.0
        hoehe = _bbox_height(verts) if verts else None

        raum: dict[str, Any] = {
            "id": f"R{idx}",
            "ifc_guid": sp.GlobalId,
            # Platzhalter (OFFEN-4 B). Der Validator meldet
            # HEATING_STATUS_UNCONFIRMED und blockiert geometry_ok.
            "heating_status": "heated",
        }
        name = getattr(sp, "LongName", None) or getattr(sp, "Name", None)
        if name:
            raum["name"] = name
        if getattr(sp, "Name", None):
            raum["number"] = sp.Name
        host_storey = space_storey.get(sp.GlobalId)
        if host_storey and host_storey in storey_id_by_guid:
            raum["storey_ref"] = storey_id_by_guid[host_storey]
        if area > 0:
            raum["area_ngf_m2"] = round(area, 3)
        if hoehe:
            raum["height_m"] = round(hoehe, 3)
        rooms_out.append(raum)

    # ---- Konstruktionen (Skelett aus IfcMaterialLayerSet) — §2.2/§2.3 --- #
    # OHNE lambda/u_value (= Katalog-Inhalt, Rolle energiekatalog). KEIN
    # construction_ref an den Gruppen (Aufloesung = Anreicherung, §7.6).
    constructions: list[dict] = []
    seen_constructions: dict[str, str] = {}
    for el in bauteile:
        try:
            struktur = extract_material_layers(el, ifc_file)
        except Exception:
            struktur = None
        if struktur is None or not struktur.layers:
            continue
        origin = struktur.name or f"LS-{el.GlobalId[:8]}"
        if origin in seen_constructions:
            continue
        layers = [
            {
                "position": layer.position,
                "material": layer.material_name,
                "thickness_m": round(float(layer.thickness), 4),
            }
            for layer in struktur.layers
        ]
        cid = f"CON-{len(constructions) + 1:03d}"
        seen_constructions[origin] = cid
        constructions.append({
            "id": cid,
            "name": origin,
            "source": "IFC",
            "origin_ref": origin,
            "total_thickness_m": round(float(struktur.total_thickness), 4),
            "sequences": [{"layers": layers}],
        })

    # ---- building (OFFEN-5: type nie aus IFC raten, nur mergen) ---------- #
    basis_building = {}
    if base:
        basis_building = dict(base.get("input", {}).get("building", {}) or {})
    building: dict[str, Any] = dict(basis_building)
    if building_type:
        building["type"] = building_type
    elif "type" not in building:
        building["type"] = BUILDING_TYPE_PLACEHOLDER
    ngf = sum(r.get("area_ngf_m2", 0.0) or 0.0 for r in rooms_out)
    if ngf > 0 and "ngf_m2" not in building:
        building["ngf_m2"] = round(ngf, 3)
    building.setdefault("storeys_above_ground", storeys_above)
    building.setdefault("storeys_below_ground", storeys_below)

    # ---- meta ------------------------------------------------------------- #
    jetzt = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    basis_meta = dict(base.get("meta", {})) if base else {}
    meta: dict[str, Any] = dict(basis_meta)
    meta.setdefault("project_name", project_name)
    meta.setdefault("norm_editions", {"din_18599": "2018-09"})
    meta["ifc_file_ref"] = ifc_file_ref
    meta.setdefault("created_at", jetzt)
    meta["updated_at"] = jetzt
    meta["validation"] = {
        "level": "draft",
        "validated_at": jetzt,
        "ruleset_version": PARSER_VERSION,
    }
    meta["source"] = {
        "origin": "IFC_PARSER",
        "tool": PARSER_TOOL,
        "tool_version": tool_version,
    }
    tn = _true_north_offset(ifc_file)
    if tn is not None:
        meta.setdefault("true_north_offset_deg", round(tn, 6))

    # Klima (rein geografisch, optional) aus IfcSite.
    sites = ifc_file.by_type("IfcSite")
    climate: dict[str, Any] = {}
    if sites:
        lat = _dms_to_decimal(getattr(sites[0], "RefLatitude", None))
        lon = _dms_to_decimal(getattr(sites[0], "RefLongitude", None))
        if lat is not None:
            climate["latitude"] = round(lat, 6)
        if lon is not None:
            climate["longitude"] = round(lon, 6)

    # ---- Zusammenbau ------------------------------------------------------ #
    inp: dict[str, Any] = {"building": building}
    if storeys_out:
        inp["storeys"] = storeys_out
    if rooms_out:
        inp["rooms"] = rooms_out
    if element_groups:
        inp["element_groups"] = element_groups
    if constructions:
        inp["constructions"] = constructions
    if climate:
        inp["climate"] = climate
    # boundaries bleiben bewusst weg (deferred, §1.1). Nicht als [] setzen.

    return {
        "schema_info": {"url": SCHEMA_URL, "version": SCHEMA_VERSION},
        "meta": meta,
        "input": inp,
    }


def _cli(argv: list[str]) -> int:  # pragma: no cover - Bequemlichkeit fuer Tests
    import json

    if not argv:
        print("Aufruf: python3 ifc_v4_parser.py <ifc-datei> [ifc_file_ref]")
        return 2
    ref = argv[1] if len(argv) > 1 else "model.ifc"
    sidecar = parse_ifc_to_sidecar_v4(argv[0], ifc_file_ref=ref)
    print(json.dumps(sidecar, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_cli(sys.argv[1:]))
