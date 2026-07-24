#!/usr/bin/env python3
"""
dwe_validate.py — Validator fuer .dwe-Container (Schema v4.0)

Prueft ein Sidecar (und optional das Manifest) in fuenf aufsteigenden Stufen und
meldet, welche Stufe erreicht ist. Beta: alle Stufen-Checks sind WARNUNGEN,
keine Blocker. Der Rueckgabecode ist nur bei Schema- oder Strukturfehlern
ungleich null.

    draft        strukturell gueltig gegen das JSON-Schema
    enriched     Fachdaten vollstaendig (Raumtypen, Zonen, Konstruktionen)
    geometry_ok  Geometrie plausibel (Angrenzungen, Flaechen, Volumina)
    balanced     Huellflaeche, Ve und NGF innerhalb der Toleranzen
    calc_ready   alle Katalogwerte aufgeloest, rechenbar

Die TOLERANZEN sind Validator-Konstanten und stehen bewusst NICHT im Schema
(Handoff E9) — sie sind Auslegungssache und aendern sich ohne Formatbruch.

Dies ist zugleich der erste echte Katalog-Konsument im Repo: adjacency_types,
room_types und usage_profiles werden geladen und Referenzen dagegen aufgeloest.

Aufruf:
    python3 tools/dwe_validate.py examples/v4.0/beispiel1/energy.din18599.json
    python3 tools/dwe_validate.py <sidecar> --manifest <manifest.json> --json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("jsonschema fehlt: pip install jsonschema", file=sys.stderr)
    raise SystemExit(2)

REPO = Path(__file__).resolve().parent.parent

STUFEN = ["draft", "enriched", "geometry_ok", "balanced", "calc_ready"]

# --- Toleranzen (Validator-Konstanten, NICHT Schema-Inhalt) ------------------
TOLERANZ_HUELLFLAECHE = 0.03   # 3 Prozent Huellflaechenabgleich
TOLERANZ_VE = 0.10             # 10 Prozent beheiztes Volumen
TOLERANZ_NGF = 0.15            # 15 Prozent Nettogrundflaeche
TOLERANZ_VOLUMEN_MELDUNG = 0.01  # ab 1 Prozent Abweichung Toposolid-Verdacht

RULESET_VERSION = "0.1.0"


@dataclass
class Befund:
    code: str
    severity: str          # info | warning | error
    message: str
    blocks_level: str | None = None
    json_pointer: str | None = None

    def __str__(self) -> str:
        ort = f"  {self.json_pointer}" if self.json_pointer else ""
        return f"[{self.severity:7}] {self.code:28} {self.message}{ort}"


@dataclass
class Ergebnis:
    befunde: list[Befund] = field(default_factory=list)
    erreichte_stufe: str = "draft"

    def melde(self, *args, **kwargs) -> None:
        self.befunde.append(Befund(*args, **kwargs))

    @property
    def hat_fehler(self) -> bool:
        return any(b.severity == "error" for b in self.befunde)

    def blockiert(self, stufe: str) -> bool:
        return any(b.blocks_level == stufe for b in self.befunde)


# --- Kataloge ----------------------------------------------------------------

def lade_kataloge() -> dict:
    """Laedt die Kern-Kataloge und indiziert sie nach code."""
    kataloge = {}
    verzeichnis = REPO / "catalog" / "core"
    if not verzeichnis.exists():
        return kataloge
    for pfad in sorted(verzeichnis.glob("*.json")):
        try:
            roh = json.loads(pfad.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        kid = roh.get("catalog_id")
        if not kid:
            continue
        kataloge[kid] = {
            "meta": roh,
            "by_code": {e["code"]: e for e in roh.get("entries", []) if "code" in e},
        }
    return kataloge


# --- Stufe 1: draft ----------------------------------------------------------

def pruefe_schema(sidecar: dict, erg: Ergebnis) -> bool:
    schema_pfad = REPO / "schema" / "v4.0" / "sidecar.schema.json"
    validator = Draft7Validator(json.loads(schema_pfad.read_text(encoding="utf-8")))
    fehler = sorted(validator.iter_errors(sidecar), key=lambda e: list(e.path))
    for f in fehler:
        erg.melde(
            "SCHEMA_INVALID", "error", f.message[:200],
            blocks_level="draft",
            json_pointer="/" + "/".join(str(p) for p in f.path),
        )
    return not fehler


# --- Stufe 2: enriched -------------------------------------------------------

def _ebene(gruppe: dict) -> tuple | None:
    """Normierte Ebene (Einheitsnormale, Abstand) einer Gruppe, oder None.

    Gibt None zurueck, wenn der Fingerprint fehlt oder entartet ist — solche
    Gruppen sind kein Kollisionsbefund, sondern ein Schema-Thema.
    """
    fp = gruppe.get("fingerprint") or {}
    try:
        n = (float(fp.get("normal_x", 0.0)),
             float(fp.get("normal_y", 0.0)),
             float(fp.get("normal_z") or 0.0))
        dist = float(fp.get("dist_m", 0.0))
    except (TypeError, ValueError):
        return None
    laenge = math.sqrt(sum(k * k for k in n))
    if laenge < 1e-9:
        return None
    return tuple(k / laenge for k in n), dist


def pruefe_fingerprint_kollisionen(gruppen: dict, erg: Ergebnis) -> None:
    """Zwei Gruppen, deren Ebenen innerhalb der Gruppierungstoleranzen liegen,
    waeren in Wahrheit eine Gruppe.

    Verglichen wird der WINKELABSTAND der Normalen, nicht die Gleichheit
    gerundeter Werte: Runden ist Quantisierung, keine Toleranz. Der alte
    Bucket-Vergleich uebersah jede Kollision, die knapp ueber einer
    Rundungsgrenze lag, und war nicht transitiv.

    Der Betrag |n_a . n_b| vergleicht EBENEN statt Vektoren und faengt damit
    den Kanonisierungs-Kipppunkt bei normal_x nahe 0 mit ab — dort kippt das
    Vorzeichen der Normalen und dist_m wird mitgespiegelt.

    Die Paar-Toleranz ist das MAXIMUM beider Gruppen: sonst haengt der Befund
    davon ab, welche Gruppe zufaellig zuerst in der Liste steht.

    Der Check ist mit der Greedy-Repraesentanten-Regel konsistent — dort wird
    eine neue Gruppe nur eroeffnet, wenn das Element zu KEINEM bestehenden
    Repraesentanten passt. Zwei Repraesentanten innerhalb der Toleranz sind
    also per Konstruktion unmoeglich und jeder Treffer ein echter Befund.
    """
    # Vorsortierung nach Bauteiltyp: Gruppen verschiedenen Typs kollidieren
    # per Definition nie, das spart den Grossteil der Paare. Innerhalb des
    # Typs nach |dist| sortiert, damit die Schleife abbrechen kann.
    nach_typ: dict[str, list] = {}
    for gruppe in gruppen.values():
        ebene = _ebene(gruppe)
        if ebene is None:
            continue
        nach_typ.setdefault(gruppe.get("element_type"), []).append((gruppe, ebene))

    for eintraege in nach_typ.values():
        eintraege.sort(key=lambda e: abs(e[1][1]))
        # Konservative Abbruchschranke fuer diesen Typ: die groesste im Typ
        # dokumentierte Abstandstoleranz.
        max_dist_tol = max(
            float((g.get("fingerprint", {}).get("tolerance") or {})
                  .get("dist_tolerance_m", 0.02))
            for g, _ in eintraege
        )
        for ia, (ga, (na, da)) in enumerate(eintraege):
            for gb, (nb, db) in eintraege[ia + 1:]:
                # |s*da - db| <= tol erzwingt ||da| - |db|| <= tol, also darf
                # ab dieser Differenz abgebrochen werden (nach |dist| sortiert).
                if abs(db) - abs(da) > max_dist_tol:
                    break

                tol_a = (ga.get("fingerprint", {}).get("tolerance") or {})
                tol_b = (gb.get("fingerprint", {}).get("tolerance") or {})
                winkel_tol = max(float(tol_a.get("angle_tolerance_deg", 1.0)),
                                 float(tol_b.get("angle_tolerance_deg", 1.0)))
                dist_tol = max(float(tol_a.get("dist_tolerance_m", 0.02)),
                               float(tol_b.get("dist_tolerance_m", 0.02)))

                skalar = sum(x * y for x, y in zip(na, nb))
                skalar = max(-1.0, min(1.0, skalar))     # Rundungsdrift abfangen
                if abs(skalar) < math.cos(math.radians(winkel_tol)) - 1e-12:
                    continue
                # Bei antiparalleler Normale ist dist mitgespiegelt.
                vorzeichen = 1.0 if skalar >= 0 else -1.0
                if abs(vorzeichen * da - db) <= dist_tol:
                    winkel = math.degrees(math.acos(abs(skalar)))
                    erg.melde("FINGERPRINT_COLLISION", "warning",
                              f"{ga['id']} und {gb['id']}: Ebenen liegen innerhalb "
                              f"der Gruppierungstoleranzen ({winkel:.2f} von "
                              f"{winkel_tol:g} Grad, {abs(vorzeichen * da - db):.3f} "
                              f"von {dist_tol:g} m) — sie muessten eine Gruppe sein",
                              json_pointer="/input/element_groups")


def pruefe_fachdaten(sidecar: dict, kataloge: dict, erg: Ergebnis) -> None:
    eingabe = sidecar.get("input", {})
    raeume = eingabe.get("rooms", [])
    zonen = {z["id"]: z for z in eingabe.get("zones", [])}
    konstruktionen = {c["id"] for c in eingabe.get("constructions", [])}
    gruppen = {g["id"]: g for g in eingabe.get("element_groups", [])}

    raumtypen = kataloge.get("room_types", {}).get("by_code", {})
    profile = kataloge.get("usage_profiles", {}).get("by_code", {})

    for i, raum in enumerate(raeume):
        zeiger = f"/input/rooms/{i}"

        ref = raum.get("room_type_ref")
        if not ref:
            erg.melde("ROOM_TYPE_MISSING", "warning",
                      f"{raum['id']}: kein room_type_ref",
                      blocks_level="enriched", json_pointer=zeiger)
        elif raumtypen and ref not in raumtypen:
            erg.melde("ROOM_TYPE_UNRESOLVED", "error",
                      f"{raum['id']}: room_type_ref '{ref}' steht in keinem Katalog",
                      blocks_level="enriched", json_pointer=zeiger)

        arten = {m["zone_type"] for m in raum.get("zone_memberships", [])}
        for m in raum.get("zone_memberships", []):
            if zonen and m["zone_id"] not in zonen:
                erg.melde("ZONE_UNRESOLVED", "error",
                          f"{raum['id']}: zone_id '{m['zone_id']}' existiert nicht",
                          blocks_level="enriched", json_pointer=zeiger)

        # Raeume ausserhalb der thermischen Huelle duerfen nicht bilanziert werden.
        # Vorbelegung kommt aus dem Katalog, am Raum ueberschreibbar.
        katalog_eintrag = raumtypen.get(ref, {})
        ausserhalb = raum.get(
            "outside_thermal_envelope",
            katalog_eintrag.get("defaults", {}).get("outside_thermal_envelope", False),
        )
        if ausserhalb and "thermal" in arten:
            erg.melde("ROOM_OUTSIDE_ENVELOPE_IN_ZONE", "error",
                      f"{raum['id']}: liegt ausserhalb der thermischen Huelle, ist "
                      f"aber einer thermischen Zone zugeordnet",
                      blocks_level="enriched", json_pointer=zeiger)
        if ausserhalb and raum.get("heating_status") != "unheated":
            erg.melde("ROOM_OUTSIDE_ENVELOPE_HEATED", "warning",
                      f"{raum['id']}: liegt ausserhalb der thermischen Huelle, "
                      f"heating_status ist aber '{raum.get('heating_status')}'",
                      json_pointer=zeiger)

        # Pflicht laut Handoff E2: thermal bei konditionierten Raeumen.
        if ausserhalb:
            pass
        elif raum.get("heating_status") in ("heated", "low_heated") and "thermal" not in arten:
            erg.melde("ZONE_THERMAL_MISSING", "warning",
                      f"{raum['id']} ist konditioniert, aber keiner thermischen Zone zugeordnet",
                      blocks_level="enriched", json_pointer=zeiger)
        if "dwelling_unit" not in arten and raum.get("heating_status") != "unheated":
            erg.melde("ZONE_DWELLING_MISSING", "info",
                      f"{raum['id']}: keine Wohneinheit zugeordnet",
                      blocks_level="enriched", json_pointer=zeiger)

        # Abweichende Auslegungstemperatur: beide Werte werden mitgefuehrt,
        # ab 3 K Unterschied ist das begruendungspflichtig.
        standard = raum.get("theta_heizlast_standard_c")
        override = raum.get("theta_heizlast_override_c")
        if standard is not None and override is not None:
            if abs(override - standard) > 3.0:
                erg.melde("THETA_OVERRIDE_LARGE", "warning",
                          f"{raum['id']}: Auslegungstemperatur weicht um "
                          f"{abs(override - standard):.1f} K vom Standard ab",
                          json_pointer=zeiger)

    for i, gruppe in enumerate(eingabe.get("element_groups", [])):
        ref = gruppe.get("construction_ref")
        if not ref:
            erg.melde("CONSTRUCTION_MISSING", "warning",
                      f"{gruppe['id']}: keine construction_ref",
                      blocks_level="enriched",
                      json_pointer=f"/input/element_groups/{i}")
        elif konstruktionen and ref not in konstruktionen:
            erg.melde("CONSTRUCTION_UNRESOLVED", "error",
                      f"{gruppe['id']}: construction_ref '{ref}' nicht in constructions[]",
                      blocks_level="enriched",
                      json_pointer=f"/input/element_groups/{i}")

    for i, zone in enumerate(eingabe.get("zones", [])):
        if zone.get("zone_type") != "thermal":
            continue
        ref = zone.get("usage_profile_ref")
        if not ref:
            erg.melde("USAGE_PROFILE_MISSING", "warning",
                      f"{zone['id']}: thermische Zone ohne usage_profile_ref",
                      blocks_level="enriched", json_pointer=f"/input/zones/{i}")
        elif profile and ref not in profile:
            erg.melde("USAGE_PROFILE_UNRESOLVED", "error",
                      f"{zone['id']}: usage_profile_ref '{ref}' steht in keinem Katalog",
                      blocks_level="enriched", json_pointer=f"/input/zones/{i}")

    pruefe_fingerprint_kollisionen(gruppen, erg)


# --- Stufe 3: geometry_ok ----------------------------------------------------

def pruefe_geometrie(sidecar: dict, kataloge: dict, erg: Ergebnis) -> None:
    eingabe = sidecar.get("input", {})
    grenzen = eingabe.get("boundaries", [])
    raeume = {r["id"] for r in eingabe.get("rooms", [])}
    gruppen = {g["id"] for g in eingabe.get("element_groups", [])}
    angrenzungen = kataloge.get("adjacency_types", {}).get("by_code", {})

    if not grenzen:
        erg.melde("BOUNDARIES_EMPTY", "warning",
                  "input.boundaries[] ist leer — ohne Angrenzungsmatrix keine "
                  "Huellflaeche und keine Energiebilanz",
                  blocks_level="geometry_ok", json_pointer="/input/boundaries")

    # Der IFC-Skelett-Parser kann die Konditionierung nicht aus der Geometrie
    # ableiten und setzt heating_status als Platzhalter 'heated' (OFFEN-4
    # Variante B, SPEC-ifc-skelett-parser-v4 §9.1). Herkunft IFC_PARSER heisst
    # daher per Konstruktion: die Raum-Konditionierung ist unbestaetigt. Das
    # blockiert geometry_ok, bis der Anreicherungs-Assistent sie bestaetigt —
    # ohne bestaetigte Konditionierung darf nicht gerechnet werden.
    herkunft = sidecar.get("meta", {}).get("source", {}).get("origin")
    if herkunft == "IFC_PARSER":
        with_status = [r for r in eingabe.get("rooms", []) if r.get("heating_status")]
        if with_status:
            erg.melde("HEATING_STATUS_UNCONFIRMED", "warning",
                      f"{len(with_status)} Raeume tragen einen unbestaetigten "
                      f"heating_status-Platzhalter (Herkunft IFC_PARSER) — die "
                      f"Konditionierung ist vom Assistenten zu bestaetigen",
                      blocks_level="geometry_ok", json_pointer="/input/rooms")

    for i, grenze in enumerate(grenzen):
        zeiger = f"/input/boundaries/{i}"

        if grenze.get("element_group_ref") not in gruppen:
            erg.melde("BOUNDARY_GROUP_UNRESOLVED", "error",
                      f"{grenze['id']}: element_group_ref "
                      f"'{grenze.get('element_group_ref')}' existiert nicht",
                      blocks_level="geometry_ok", json_pointer=zeiger)
        if grenze.get("space_a") not in raeume:
            erg.melde("BOUNDARY_SPACE_A_UNRESOLVED", "error",
                      f"{grenze['id']}: space_a '{grenze.get('space_a')}' existiert nicht",
                      blocks_level="geometry_ok", json_pointer=zeiger)

        art = grenze.get("adjacency_type")
        eintrag = angrenzungen.get(art)
        if angrenzungen and eintrag is None:
            erg.melde("ADJACENCY_UNRESOLVED", "error",
                      f"{grenze['id']}: adjacency_type '{art}' steht in keinem Katalog",
                      blocks_level="geometry_ok", json_pointer=zeiger)
        elif eintrag:
            braucht_b = eintrag.get("space_b_required")
            hat_b = grenze.get("space_b") is not None
            if braucht_b and not hat_b:
                erg.melde("BOUNDARY_SPACE_B_MISSING", "warning",
                          f"{grenze['id']}: '{art}' verlangt einen Gegenraum, "
                          f"space_b fehlt",
                          blocks_level="geometry_ok", json_pointer=zeiger)
            if braucht_b is False and hat_b:
                erg.melde("BOUNDARY_SPACE_B_UNEXPECTED", "info",
                          f"{grenze['id']}: '{art}' hat normalerweise keinen "
                          f"Gegenraum, space_b ist trotzdem gesetzt",
                          json_pointer=zeiger)
            if hat_b and grenze["space_b"] not in raeume:
                erg.melde("BOUNDARY_SPACE_B_UNRESOLVED", "error",
                          f"{grenze['id']}: space_b '{grenze['space_b']}' existiert nicht",
                          blocks_level="geometry_ok", json_pointer=zeiger)

            # Massbezug muss zur Angrenzungsart passen. Ausnahme
            # 'clear_structural': das ist bewusst KEIN aus der Angrenzungsart
            # ableitbarer Wert, sondern die Doku einer offenen Umrechnung —
            # er wird deshalb unten eigens geprueft und hier nicht als
            # Mismatch gegen den Katalog gemeldet.
            soll = eintrag.get("measurement_reference")
            ist = grenze.get("measurement_reference")
            if ist and soll and ist != soll and ist != "clear_structural":
                erg.melde("MEASUREMENT_REFERENCE_MISMATCH", "warning",
                          f"{grenze['id']}: '{art}' verlangt Massbezug '{soll}', "
                          f"gesetzt ist '{ist}'",
                          json_pointer=zeiger)

        # Lichtes Rohbaumass ist ein Uebergangszustand. Solange eine
        # bilanzrelevante Flaeche darauf steht, ist die Huellflaeche zu klein
        # gerechnet — das darf calc_ready nicht erreichen. Warnung statt
        # Fehler nach der Beta-Konvention: die Stufen-Checks blockieren, sie
        # brechen nicht ab.
        if (grenze.get("measurement_reference") == "clear_structural"
                and grenze.get("relevant_18599")):
            erg.melde("MEASUREMENT_CLEAR_RELEVANT", "warning",
                      f"{grenze['id']}: Massbezug 'clear_structural' (lichtes "
                      f"Rohbaumass) an einer bilanzrelevanten Flaeche — "
                      f"Umrechnung auf Aussen- bzw. Achsmass steht noch aus",
                      blocks_level="calc_ready", json_pointer=zeiger)

        geom = grenze.get("geometry") or {}
        if geom.get("type") == "polygon":
            punkte = geom.get("polygon", [])
            if len(punkte) >= 3 and punkte[0] == punkte[-1]:
                erg.melde("POLYGON_CLOSED_EXPLICITLY", "warning",
                          f"{grenze['id']}: erster Punkt wird am Ende wiederholt — "
                          f"der Ringzug wird implizit geschlossen",
                          json_pointer=zeiger)
        elif geom.get("type") == "z_range":
            if geom.get("z_to") is not None and geom.get("z_from") is not None:
                if geom["z_to"] <= geom["z_from"]:
                    erg.melde("Z_RANGE_INVALID", "error",
                              f"{grenze['id']}: z_to ist nicht groesser als z_from",
                              blocks_level="geometry_ok", json_pointer=zeiger)

        for groesse in ("area_18599", "area_heizlast"):
            wert = grenze.get(groesse)
            if wert is not None and wert <= 0:
                erg.melde("AREA_NOT_POSITIVE", "warning",
                          f"{grenze['id']}: {groesse} ist {wert}",
                          blocks_level="geometry_ok", json_pointer=zeiger)

    # Toposolid-Verdacht: gemeldetes Raumvolumen weicht vom gerechneten ab.
    # Aus der Revit-Testphase: ein raumbegrenzendes Toposolid verfaelscht die
    # Raumvolumina still (im Testmodell -2,9 Prozent ueber 12 Raeume).
    verdaechtig = []
    for raum in sidecar.get("input", {}).get("rooms", []):
        gerechnet = raum.get("volume_ve_m3")
        gemeldet = raum.get("volume_reported_m3")
        if gerechnet and gemeldet and gerechnet > 0:
            if abs(gemeldet - gerechnet) / gerechnet > TOLERANZ_VOLUMEN_MELDUNG:
                verdaechtig.append(raum["id"])
    if verdaechtig:
        erg.melde("TOPOSOLID_ROOM_BOUNDING", "warning",
                  f"{len(verdaechtig)} Raeume: gemeldetes Volumen weicht vom "
                  f"gerechneten ab (Verdacht: Toposolid mit Raumbegrenzung aktiv). "
                  f"Betroffen: {', '.join(verdaechtig[:5])}"
                  + (" ..." if len(verdaechtig) > 5 else ""),
                  json_pointer="/input/rooms")

    if not sidecar.get("meta", {}).get("ve_method"):
        erg.melde("VE_METHOD_MISSING", "warning",
                  "meta.ve_method fehlt — die Ermittlungsmethode des beheizten "
                  "Volumens ist immer zu dokumentieren",
                  blocks_level="geometry_ok", json_pointer="/meta")

    # openings_index ist eine reine Sicht und muss zur Quelle passen.
    index = eingabe.get("openings_index")
    if index is not None:
        quelle = {o["id"] for b in grenzen for o in b.get("openings", [])}
        indiziert = {e["opening_ref"] for e in index}
        if quelle != indiziert:
            fehlend = quelle - indiziert
            ueberzaehlig = indiziert - quelle
            erg.melde("OPENINGS_INDEX_INCONSISTENT", "warning",
                      f"openings_index stimmt nicht mit boundaries[].openings[] "
                      f"ueberein ({len(fehlend)} fehlen, {len(ueberzaehlig)} ueberzaehlig). "
                      f"Der Index ist read-only, die Quelle gewinnt.",
                      blocks_level="geometry_ok", json_pointer="/input/openings_index")


# --- Stufe 4: balanced -------------------------------------------------------

def pruefe_bilanz(sidecar: dict, erg: Ergebnis) -> None:
    eingabe = sidecar.get("input", {})
    gebaeude = eingabe.get("building", {})
    grenzen = eingabe.get("boundaries", [])

    summe_huelle = sum(
        b.get("area_18599", 0) or 0 for b in grenzen if b.get("relevant_18599")
    )
    angegeben = gebaeude.get("envelope_area_m2")
    if angegeben and summe_huelle:
        abweichung = abs(summe_huelle - angegeben) / angegeben
        if abweichung > TOLERANZ_HUELLFLAECHE:
            erg.melde("ENVELOPE_AREA_MISMATCH", "warning",
                      f"Huellflaeche weicht um {abweichung:.1%} ab "
                      f"(Summe boundaries {summe_huelle:.1f} m² gegen "
                      f"building.envelope_area_m2 {angegeben:.1f} m², "
                      f"Toleranz {TOLERANZ_HUELLFLAECHE:.0%})",
                      blocks_level="balanced", json_pointer="/input/building")
    elif not angegeben:
        erg.melde("ENVELOPE_AREA_UNKNOWN", "info",
                  "building.envelope_area_m2 fehlt — Huellflaechenabgleich nicht moeglich",
                  blocks_level="balanced", json_pointer="/input/building")

    summe_ngf = sum(r.get("area_ngf_m2", 0) or 0 for r in eingabe.get("rooms", []))
    ngf = gebaeude.get("ngf_m2")
    if ngf and summe_ngf:
        abweichung = abs(summe_ngf - ngf) / ngf
        if abweichung > TOLERANZ_NGF:
            erg.melde("NGF_MISMATCH", "warning",
                      f"NGF weicht um {abweichung:.1%} ab (Summe Raeume "
                      f"{summe_ngf:.1f} m² gegen building.ngf_m2 {ngf:.1f} m², "
                      f"Toleranz {TOLERANZ_NGF:.0%})",
                      blocks_level="balanced", json_pointer="/input/building")

    summe_ve = sum(r.get("volume_ve_m3", 0) or 0 for r in eingabe.get("rooms", []))
    ve = gebaeude.get("ve_m3")
    if ve and summe_ve:
        abweichung = abs(summe_ve - ve) / ve
        if abweichung > TOLERANZ_VE:
            erg.melde("VE_MISMATCH", "warning",
                      f"Beheiztes Volumen weicht um {abweichung:.1%} ab "
                      f"(Toleranz {TOLERANZ_VE:.0%})",
                      blocks_level="balanced", json_pointer="/input/building")
    elif not ve:
        erg.melde("VE_UNKNOWN", "info",
                  "building.ve_m3 fehlt — Volumenabgleich nicht moeglich",
                  blocks_level="balanced", json_pointer="/input/building")


# --- Stufe 5: calc_ready -----------------------------------------------------

def pruefe_rechenbarkeit(sidecar: dict, kataloge: dict, erg: Ergebnis) -> None:
    eingabe = sidecar.get("input", {})
    angrenzungen = kataloge.get("adjacency_types", {}).get("by_code", {})

    for i, grenze in enumerate(eingabe.get("boundaries", [])):
        if grenze.get("fx") is None:
            art = grenze.get("adjacency_type")
            eintrag = angrenzungen.get(art, {})
            fx = eintrag.get("fx", {})
            ersatz = fx.get("value") if fx.get("value") is not None else fx.get("simplified_value")
            if ersatz is None:
                erg.melde("FX_UNRESOLVED", "warning",
                          f"{grenze['id']}: Fx nicht gesetzt und aus '{art}' nicht "
                          f"aufloesbar (Methode '{fx.get('method')}')",
                          blocks_level="calc_ready",
                          json_pointer=f"/input/boundaries/{i}")

    # Werte-Overlays: ohne aufgeloeste Normwerte keine Berechnung.
    for kid, katalog in kataloge.items():
        overlay = katalog["meta"].get("values_overlay", {})
        if not overlay.get("required"):
            continue
        erwartet = overlay.get("expected_file")
        if erwartet and not (REPO / erwartet).exists():
            erg.melde("VALUES_OVERLAY_MISSING", "warning",
                      overlay.get("missing_value_message",
                                  f"Werte-Overlay fuer '{kid}' fehlt"),
                      blocks_level="calc_ready", json_pointer="/meta/catalogs")

    # U-Werte gegen den Schichtaufbau gegenrechnen. Erst hier sinnvoll: ohne
    # boundaries[] ist die Bauteilsituation und damit Rsi/Rse nicht bestimmbar.
    try:
        from u_value import pruefe_sidecar as _pruefe_u
        for b in _pruefe_u(sidecar):
            erg.melde(b["code"], b["severity"], b["message"],
                      blocks_level="calc_ready" if b["severity"] == "warning" else None,
                      json_pointer="/input/constructions")
    except ImportError:
        erg.melde("U_VALUE_MODULE_MISSING", "info",
                  "u_value.py nicht ladbar — U-Wert-Gegenrechnung uebersprungen",
                  json_pointer="/input/constructions")

    for i, zone in enumerate(eingabe.get("zones", [])):
        if zone.get("zone_type") == "thermal" and not zone.get("used_profile_values"):
            erg.melde("PROFILE_SNAPSHOT_MISSING", "info",
                      f"{zone['id']}: kein used_profile_values-Snapshot — die "
                      f"Berechnung waere spaeter nicht mehr nachvollziehbar",
                      blocks_level="calc_ready", json_pointer=f"/input/zones/{i}")


# --- Ablauf ------------------------------------------------------------------

def validiere(sidecar: dict, kataloge: dict) -> Ergebnis:
    erg = Ergebnis()

    if not pruefe_schema(sidecar, erg):
        erg.erreichte_stufe = "invalid"
        return erg

    pruefe_fachdaten(sidecar, kataloge, erg)
    pruefe_geometrie(sidecar, kataloge, erg)
    pruefe_bilanz(sidecar, erg)
    pruefe_rechenbarkeit(sidecar, kataloge, erg)

    erreicht = "draft"
    for stufe in STUFEN[1:]:
        if erg.blockiert(stufe):
            break
        erreicht = stufe
    erg.erreichte_stufe = erreicht
    return erg


def main() -> int:
    p = argparse.ArgumentParser(description="Validiert ein .dwe-Sidecar (Schema v4.0)")
    p.add_argument("sidecar", nargs="?", help="Pfad zur energy.din18599.json")
    p.add_argument("--manifest", help="Optional: manifest.json gegenpruefen")
    p.add_argument("--json", action="store_true", help="Befunde als JSON ausgeben")
    p.add_argument("--list-paths", action="store_true",
                   help="Pfad-Whitelist aus schema/v4.0/paths.json ausgeben "
                        "(erzeugt wird sie von scripts/build-paths.py)")
    args = p.parse_args()

    if args.list_paths:
        # Bewusst nur LESEN, nicht erzeugen: das Artefakt ist versioniert und
        # per CI gegen das Schema verriegelt. Wuerde die CLI es selbst
        # ableiten, gaebe es zwei Wahrheiten mit demselben Namen.
        artefakt = REPO / "schema" / "v4.0" / "paths.json"
        if not artefakt.exists():
            print(f"{artefakt} fehlt — python3 scripts/build-paths.py laufen lassen",
                  file=sys.stderr)
            return 2
        daten = json.loads(artefakt.read_text(encoding="utf-8"))
        if args.json:
            print(json.dumps(daten, indent=2, ensure_ascii=False))
        else:
            for eintrag in daten["paths"]:
                marke = "ro" if eintrag["readonly"] else "rw"
                print(f"{marke}  {eintrag['path']}")
        return 0

    if not args.sidecar:
        p.error("sidecar fehlt (oder --list-paths verwenden)")

    pfad = Path(args.sidecar)
    if not pfad.exists():
        print(f"Datei nicht gefunden: {pfad}", file=sys.stderr)
        return 2

    sidecar = json.loads(pfad.read_text(encoding="utf-8"))
    kataloge = lade_kataloge()
    erg = validiere(sidecar, kataloge)

    if args.manifest:
        import hashlib
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        eintrag = manifest.get("contents", {}).get("sidecar", {})
        soll = eintrag.get("checksum", {}).get("value")
        ist = hashlib.sha256(pfad.read_bytes()).hexdigest()
        if soll and soll != ist:
            erg.melde("CHECKSUM_MISMATCH", "error",
                      "Sidecar-Checksumme im Manifest stimmt nicht mit der Datei ueberein",
                      json_pointer="/contents/sidecar/checksum")
        gemeldet = manifest.get("validation", {}).get("level")
        if gemeldet and gemeldet != erg.erreichte_stufe:
            erg.melde("MANIFEST_LEVEL_MISMATCH", "info",
                      f"Manifest meldet Stufe '{gemeldet}', geprueft wurde "
                      f"'{erg.erreichte_stufe}'",
                      json_pointer="/validation/level")

    if args.json:
        print(json.dumps({
            "level": erg.erreichte_stufe,
            "ruleset_version": RULESET_VERSION,
            "findings": [vars(b) for b in erg.befunde],
        }, indent=2, ensure_ascii=False))
        return 1 if erg.hat_fehler else 0

    print(f"Datei:            {pfad}")
    print(f"Kataloge geladen: {', '.join(sorted(kataloge)) or 'keine'}")
    print(f"Regelsatz:        {RULESET_VERSION} (Beta — Stufen-Checks sind Warnungen)")
    print()
    if erg.befunde:
        for b in erg.befunde:
            print(str(b))
        print()
    else:
        print("Keine Befunde.")
        print()

    print(f"Erreichte Stufe:  {erg.erreichte_stufe}")
    for stufe in STUFEN:
        blockiert = [b for b in erg.befunde if b.blocks_level == stufe]
        erreicht = STUFEN.index(stufe) <= STUFEN.index(erg.erreichte_stufe) \
            if erg.erreichte_stufe in STUFEN else False
        zeichen = "erreicht" if erreicht else f"blockiert ({len(blockiert)})"
        print(f"  {stufe:12} {zeichen}")

    return 1 if erg.hat_fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
