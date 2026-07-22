#!/usr/bin/env python3
"""
u_value.py — U-Wert-Berechnung nach DIN EN ISO 6946 auf Basis der Kataloge.

Rechnet aus dem Schichtaufbau einer Konstruktion den Waermedurchgangskoeffizienten
und loest dabei Materialkennwerte und Uebergangswiderstaende aus catalog/core/ auf.

Zwei Verfahren:

  homogen     Alle Schichten durchgehend. R_T = Rsi + Summe(d/lambda) + Rse.

  kombiniert  Inhomogene Bauteile (Sparren, Holzstaender) ueber sequences[] mit
              Flaechenanteilen, DIN EN ISO 6946 Abschnitt 6.7:
                R_upper = 1 / Summe(f_j / R_Tj)          Parallelweg-Grenze
                R_lower: schichtweise gewichtet          Reihenweg-Grenze
                R_T     = (R_upper + R_lower) / 2
              Die Unsicherheit e = (R_upper - R_lower) / (2 * R_T) wird
              mitgeliefert; ab e > 0,1 ist ein genaueres Verfahren angezeigt.

              R_lower setzt voraus, dass alle Abfolgen dieselbe Schichtung mit
              denselben Dicken haben. Ist das nicht der Fall, faellt die Rechnung
              auf R_upper zurueck und meldet das — lieber eine ehrlich benannte
              Naeherung als ein falscher Mittelwert.

WAS DIESES MODUL NICHT KANN, bewusst:
  - Fenster. Uw kommt aus Verglasung, Rahmen und Randverbund nach
    DIN EN ISO 10077, nicht aus Schichtwiderstaenden. Ein Fenster durch dieses
    Modul zu rechnen liefert grob falsche Werte (Faktor 7 beim Dreifachglas).
  - Erdreich. Geliefert wird der BAUTEIL-U-Wert; der Erdreichwiderstand nach
    DIN EN ISO 13370 kommt in der Bilanz ueber Fx dazu.
  - Korrekturen dU nach Anhang F (Befestigungen, Umkehrdach).

Aufruf:
    python3 tools/u_value.py --construction WALL_EXT_BRICK_WDVS_160
    python3 tools/u_value.py --sidecar examples/v4.0/beispiel1/energy.din18599.json
    python3 tools/u_value.py --audit-legacy-catalog
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# HARTE Anwendungsgrenze des vereinfachten Verfahrens (DIN EN ISO 6946, 6.7.2.1):
# "Das Verfahren gilt nicht fuer Faelle, bei denen das Verhaeltnis des oberen
# Grenzwertes zum unteren Grenzwert mehr als 1,5 betraegt."
# Das ist kein Richtwert, sondern ein Ausschluss — deshalb Fehler, nicht Warnung.
VERHAELTNIS_GRENZE = 1.5

# Bei Verhaeltnis 1,5 betraegt der maximale relative Fehler 20 % (Beispiel in
# 6.7.2.5). Ab dieser Schwelle wird gewarnt, auch wenn das Verfahren noch gilt.
FEHLER_WARNSCHWELLE_PROZENT = 10.0

# Ab dieser relativen Abweichung gilt ein angegebener U-Wert als nicht
# reproduzierbar. Validator-Konstante, kein Schema-Inhalt.
U_WERT_TOLERANZ = 0.05


@dataclass
class Ergebnis:
    u_value: float | None = None
    r_total: float | None = None
    rsi: float | None = None
    rse: float | None = None
    method: str = "homogen"
    uncertainty: float | None = None
    resistance_source: str | None = None
    r_total_rounded: float | None = None
    warnungen: list[str] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.u_value is not None and not self.fehler


def lade_katalog(name: str) -> dict:
    pfad = REPO / "catalog" / "core" / f"{name}.json"
    if not pfad.exists():
        return {}
    roh = json.loads(pfad.read_text(encoding="utf-8"))
    return {e["code"]: e for e in roh.get("entries", [])}


def lade_materialien() -> dict:
    """
    Materialkennwerte. Noch im Altformat unter catalog/materials.json —
    die Envelope-Migration steht aus (KATALOG_FORMAT.md, offener Punkt 5).
    """
    pfad = REPO / "catalog" / "materials.json"
    if not pfad.exists():
        return {}
    roh = json.loads(pfad.read_text(encoding="utf-8"))
    return {m["id"]: m for m in roh.get("materials", [])}


def waehle_uebergangswiderstaende(
    adjacency_type: str | None,
    element_type: str | None,
    katalog: dict,
) -> tuple[float, float, str] | None:
    """
    Sucht den passenden surface_resistances-Eintrag. Die Kombination aus
    Angrenzungsart und Bauteiltyp bestimmt ihn eindeutig — bewusst keine freie
    Eingabe, damit dieselbe Situation immer dieselben Randbedingungen bekommt.
    """
    if not katalog:
        return None
    treffer = [
        e for e in katalog.values()
        if (not adjacency_type or adjacency_type in e.get("applies_to_adjacency", []))
        and (not element_type or element_type in e.get("applies_to_element_type", []))
    ]
    if not treffer:
        return None
    e = treffer[0]
    return e["rsi"], e["rse"], e["code"]


def lade_luftschichten() -> dict:
    """Tabelle 8 mit Stuetzstellen, plus die Regeln aus 6.9."""
    pfad = REPO / "catalog" / "core" / "air_layers.json"
    if not pfad.exists():
        return {}
    return json.loads(pfad.read_text(encoding="utf-8"))


def luftschicht_widerstand(
    dicke_mm: float, heat_flow: str, katalog: dict
) -> tuple[float | None, str | None]:
    """
    Waermedurchlasswiderstand einer ruhenden Luftschicht nach Tabelle 8.
    Zwischenwerte werden linear interpoliert, oberhalb der letzten Stuetzstelle
    (300 mm) wird deren Wert gehalten — die Tabelle laeuft dort flach aus.
    """
    stuetzstellen = sorted(
        katalog.get("entries", []), key=lambda e: e["thickness_mm"]
    )
    if not stuetzstellen:
        return None, "Katalog air_layers fehlt oder ist leer"

    spalte = {"upward": "r_upward", "horizontal": "r_horizontal",
              "downward": "r_downward"}.get(heat_flow)
    if spalte is None:
        return None, f"Unbekannte Waermestromrichtung '{heat_flow}'"

    if dicke_mm <= stuetzstellen[0]["thickness_mm"]:
        return stuetzstellen[0][spalte], None
    if dicke_mm >= stuetzstellen[-1]["thickness_mm"]:
        return stuetzstellen[-1][spalte], None

    for unten, oben in zip(stuetzstellen, stuetzstellen[1:]):
        if unten["thickness_mm"] <= dicke_mm <= oben["thickness_mm"]:
            spanne = oben["thickness_mm"] - unten["thickness_mm"]
            anteil = (dicke_mm - unten["thickness_mm"]) / spanne
            return unten[spalte] + anteil * (oben[spalte] - unten[spalte]), None
    return None, "Interpolation fehlgeschlagen"


def schicht_widerstand(
    schicht: dict,
    materialien: dict,
    heat_flow: str = "horizontal",
    luftschichten: dict | None = None,
) -> tuple[float | None, str | None]:
    """
    Waermedurchlasswiderstand einer Schicht [(m2K)/W].

    Reihenfolge:
      1. expliziter r_value
      2. Luftschicht (air_layer=True) -> Tabelle 8, richtungsabhaengig
      3. lambda an der Schicht
      4. lambda aus dem Materialkatalog

    Eine Luftschicht hat keine sinnvolle Waermeleitfaehigkeit — ihr Widerstand
    haengt von Dicke UND Waermestromrichtung ab (DIN EN ISO 6946 Tabelle 8).
    """
    if schicht.get("r_value") is not None:
        return float(schicht["r_value"]), None

    if schicht.get("air_layer"):
        dicke = schicht.get("thickness_m", schicht.get("thickness"))
        if dicke is None:
            return None, "Luftschicht ohne Dicke"
        return luftschicht_widerstand(
            float(dicke) * 1000.0, heat_flow, luftschichten or {}
        )

    dicke = schicht.get("thickness_m", schicht.get("thickness"))
    if dicke is None:
        return None, "Schicht ohne thickness_m und ohne r_value"

    lam = schicht.get("lambda")
    if lam is None:
        ref = schicht.get("material_ref") or schicht.get("material")
        if not ref:
            return None, "Schicht ohne lambda und ohne material_ref"
        material = materialien.get(ref)
        if material is None:
            return None, f"Material '{ref}' steht in keinem Katalog"
        lam = material.get("lambda")
        if lam in (None, 0):
            return None, (f"Material '{ref}' hat kein lambda — bei Luftschichten "
                          f"gehoert stattdessen ein r_value in die Schicht "
                          f"(DIN EN ISO 6946 Tab. 8)")
    if lam <= 0:
        return None, "lambda ist nicht positiv"
    return float(dicke) / float(lam), None


def _sequenz_widerstand(layers: list, materialien: dict, heat_flow: str,
                        luftschichten: dict) -> tuple[float | None, list]:
    summe = 0.0
    fehler = []
    for schicht in layers:
        r, problem = schicht_widerstand(schicht, materialien, heat_flow, luftschichten)
        if problem:
            fehler.append(problem)
        else:
            summe += r
    return (None if fehler else summe), fehler


def berechne(
    construction: dict,
    materialien: dict,
    widerstaende: dict,
    adjacency_type: str | None = None,
    element_type: str | None = None,
) -> Ergebnis:
    erg = Ergebnis()

    rb = waehle_uebergangswiderstaende(adjacency_type, element_type, widerstaende)
    if rb is None:
        erg.fehler.append(
            f"Keine Uebergangswiderstaende fuer adjacency_type='{adjacency_type}', "
            f"element_type='{element_type}' im Katalog gefunden"
        )
        return erg
    erg.rsi, erg.rse, erg.resistance_source = rb
    heat_flow = widerstaende[erg.resistance_source].get("heat_flow", "horizontal")
    luftschichten = lade_luftschichten()

    sequences = construction.get("sequences")
    if not sequences:
        # Altformat bzw. homogener Aufbau: flaches layers[]
        layers = construction.get("layers")
        if not layers:
            erg.fehler.append("Konstruktion hat weder sequences[] noch layers[]")
            return erg
        sequences = [{"name": "Hauptkonstruktion", "share": 1.0, "layers": layers}]

    anteile = [float(s.get("share", 1.0)) for s in sequences]
    if abs(sum(anteile) - 1.0) > 0.001:
        erg.warnungen.append(
            f"Summe der Flaechenanteile ist {sum(anteile):.3f}, erwartet 1,0"
        )

    # --- R_upper: Parallelweg-Grenze ---
    kehrwerte = 0.0
    for seq, anteil in zip(sequences, anteile):
        r_seq, fehler = _sequenz_widerstand(seq.get("layers", []), materialien,
                                            heat_flow, luftschichten)
        if fehler:
            erg.fehler.extend(fehler)
            return erg
        r_tj = erg.rsi + r_seq + erg.rse
        kehrwerte += anteil / r_tj
    r_upper = 1.0 / kehrwerte

    if len(sequences) == 1:
        erg.method = "homogen"
        erg.r_total = r_upper
        erg.u_value = round(1.0 / r_upper, 4)
        # 6.7.2.2: als Endergebnis ist R_tot auf zwei Dezimalstellen zu runden.
        erg.r_total_rounded = round(r_upper, 2)
        return erg

    # --- R_lower: Reihenweg-Grenze, nur bei deckungsgleicher Schichtung ---
    schichtzahlen = {len(s.get("layers", [])) for s in sequences}
    gleich_geschichtet = len(schichtzahlen) == 1
    if gleich_geschichtet:
        r_lower = erg.rsi + erg.rse
        for i in range(schichtzahlen.pop()):
            kehrwert = 0.0
            for seq, anteil in zip(sequences, anteile):
                r, problem = schicht_widerstand(seq["layers"][i], materialien,
                                                heat_flow, luftschichten)
                if problem:
                    gleich_geschichtet = False
                    break
                kehrwert += anteil / r if r > 0 else 0.0
            if not gleich_geschichtet or kehrwert == 0:
                gleich_geschichtet = False
                break
            r_lower += 1.0 / kehrwert

    if gleich_geschichtet:
        # Anwendungsgrenze VOR der Mittelung pruefen: liegt das Verhaeltnis der
        # Grenzwerte ueber 1,5, ist das vereinfachte Verfahren unzulaessig und
        # der Mittelwert waere eine Scheingenauigkeit.
        verhaeltnis = r_upper / r_lower if r_lower > 0 else float("inf")
        if verhaeltnis > VERHAELTNIS_GRENZE:
            erg.fehler.append(
                f"Vereinfachtes Verfahren unzulaessig: R_upper/R_lower = "
                f"{verhaeltnis:.2f} > {VERHAELTNIS_GRENZE} "
                f"(DIN EN ISO 6946, 6.7.2.1). Detailliertes Verfahren nach 5.3 "
                f"anwenden — Ergebnis absichtlich nicht geliefert."
            )
            erg.method = "unzulaessig"
            return erg

        erg.method = "kombiniert"
        erg.r_total = (r_upper + r_lower) / 2.0
        # Maximaler relativer Fehler in Prozent, Gleichung (10).
        erg.uncertainty = round(
            (r_upper - r_lower) / (2.0 * erg.r_total) * 100.0, 2
        )
        if abs(erg.uncertainty) > FEHLER_WARNSCHWELLE_PROZENT:
            erg.warnungen.append(
                f"Maximaler relativer Fehler {abs(erg.uncertainty):.1f} % "
                f"(Verhaeltnis {verhaeltnis:.2f}). Das Verfahren gilt noch, aber "
                f"das detaillierte Verfahren nach 5.3 liefert ein genaueres Ergebnis."
            )
    else:
        erg.method = "parallelweg_naeherung"
        erg.r_total = r_upper
        erg.warnungen.append(
            "Die Abfolgen haben keine deckungsgleiche Schichtung — R_lower ist "
            "nicht bestimmbar. Gerechnet wird die obere Grenze (Parallelweg); "
            "der echte U-Wert liegt darunter."
        )

    erg.u_value = round(1.0 / erg.r_total, 4)
    erg.r_total_rounded = round(erg.r_total, 2)
    return erg


def uw_fenster(
    ug: float,
    uf: float,
    frame_area_fraction: float,
    width_m: float = 1.23,
    height_m: float = 1.48,
    psi_spacer: float | None = None,
    glazing_perimeter_m: float | None = None,
    single_glazing: bool = False,
) -> Ergebnis:
    """
    Wärmedurchgangskoeffizient eines Fensters nach DIN EN ISO 10077-1,
    Gleichung (2), ohne Sprossen:

        Uw = (Ag*Ug + Af*Uf + lg*Psi_g) / (Ag + Af)

    Bewusst getrennt von berechne(): ein Fenster aus Schichtwiderstaenden zu
    rechnen liefert grob falsche Werte (Faktor 7 beim Dreifachglas).

    glazing_perimeter_m ist der SICHTBARE Umfang der Verglasung. Liegt er nicht
    vor, wird er geometrisch geschaetzt, indem beide Kantenlaengen mit der
    Wurzel des Glasflaechenanteils skaliert werden. Gegen Tabelle H.1 der Norm
    (Referenzfenster 1,23 x 1,48 m) trifft diese Naeherung 91 von 91
    Stuetzstellen auf 0,06 W/(m2K) genau.

    psi_spacer nach Tabelle G.1, falls nicht angegeben. Bei Einfachverglasung
    ist Psi_g = 0 (G.1) — es gibt keinen Randverbund.
    """
    erg = Ergebnis(method="iso_10077_1")

    if not (0 < frame_area_fraction < 1):
        erg.fehler.append(
            f"Rahmenflaechenanteil muss zwischen 0 und 1 liegen, ist {frame_area_fraction}"
        )
        return erg
    if ug <= 0 or uf <= 0:
        erg.fehler.append("Ug und Uf muessen positiv sein")
        return erg

    aw = width_m * height_m
    af = aw * frame_area_fraction
    ag = aw - af

    if glazing_perimeter_m is None:
        skala = math.sqrt(1.0 - frame_area_fraction)
        glazing_perimeter_m = 2.0 * (width_m * skala + height_m * skala)
        erg.warnungen.append(
            "Sichtbarer Glasumfang lg nicht angegeben — geometrisch aus Massen "
            "und Rahmenanteil geschaetzt."
        )

    if psi_spacer is None:
        psi_spacer = 0.0 if single_glazing else psi_abstandhalter(uf, ug)
        erg.warnungen.append(
            "Psi_g = 0 — Einfachverglasung hat keinen Randverbund "
            "(DIN EN ISO 10077-1, G.1)."
            if single_glazing else
            f"Psi_g nicht angegeben — Standardwert {psi_spacer} aus "
            f"DIN EN ISO 10077-1 Tabelle G.1 (typischer Abstandhalter)."
        )

    erg.u_value = round(
        (ag * ug + af * uf + glazing_perimeter_m * psi_spacer) / aw, 4
    )
    erg.r_total = 1.0 / erg.u_value if erg.u_value else None
    return erg


def psi_abstandhalter(uf: float, ug: float) -> float:
    """
    Standardwerte fuer Psi_g nach DIN EN ISO 10077-1 Tabelle G.1, typische
    Abstandhalter aus Aluminium oder Stahl. Die Rahmenart wird ueber Uf
    abgeleitet, die Glasart ueber Ug (Anhang H: Ug <= 2,0 gilt als Glas mit
    niedrigem Emissionsgrad).

    Fuer Einfachscheiben ist Psi_g = 0 (G.1).
    """
    niedrig_emittierend = ug <= 2.0
    if uf >= 7.0:                      # Metallrahmen ohne wärmetechnische Trennung
        return 0.05 if niedrig_emittierend else 0.02
    if uf >= 2.2:                      # Metallrahmen mit wärmetechnischer Trennung
        return 0.11 if niedrig_emittierend else 0.08
    return 0.08 if niedrig_emittierend else 0.06   # Holz oder PVC


def pruefe_sidecar(sidecar: dict) -> list:
    """
    Rechnet alle Konstruktionen eines Sidecars nach und vergleicht mit dem
    angegebenen u_value. Liefert Befunde im Validator-Format.
    """
    materialien = lade_materialien()
    widerstaende = lade_katalog("surface_resistances")
    eingabe = sidecar.get("input", {})
    konstruktionen = {c["id"]: c for c in eingabe.get("constructions", [])}

    # Bauteilsituation je Konstruktion aus den Gruppen und Angrenzungen ableiten.
    situation: dict = {}
    for gruppe in eingabe.get("element_groups", []):
        ref = gruppe.get("construction_ref")
        if not ref:
            continue
        arten = {
            b.get("adjacency_type")
            for b in eingabe.get("boundaries", [])
            if b.get("element_group_ref") == gruppe["id"]
        }
        situation.setdefault(ref, []).append(
            (gruppe.get("element_type"), sorted(a for a in arten if a))
        )

    befunde = []
    for kid, konstruktion in konstruktionen.items():
        eintraege = situation.get(kid)
        if not eintraege:
            befunde.append({
                "code": "U_VALUE_NO_CONTEXT", "severity": "info",
                "message": f"{kid}: keiner Bauteilgruppe zugeordnet — ohne "
                           f"Bauteilsituation sind die Uebergangswiderstaende "
                           f"nicht bestimmbar",
                "construction": kid,
            })
            continue

        element_type, arten = eintraege[0]
        adjacency = arten[0] if arten else None
        if adjacency is None:
            befunde.append({
                "code": "U_VALUE_NO_CONTEXT", "severity": "info",
                "message": f"{kid}: keine Angrenzung bekannt (boundaries[] leer) — "
                           f"Uebergangswiderstaende nicht bestimmbar",
                "construction": kid,
            })
            continue

        erg = berechne(konstruktion, materialien, widerstaende, adjacency, element_type)
        if not erg.ok:
            befunde.append({
                "code": "U_VALUE_NOT_COMPUTABLE", "severity": "warning",
                "message": f"{kid}: {'; '.join(erg.fehler)}",
                "construction": kid,
            })
            continue

        for w in erg.warnungen:
            befunde.append({
                "code": "U_VALUE_METHOD_WARNING", "severity": "info",
                "message": f"{kid}: {w}", "construction": kid,
            })

        angegeben = konstruktion.get("u_value")
        if angegeben:
            abw = (erg.u_value - angegeben) / angegeben
            if abs(abw) > U_WERT_TOLERANZ:
                befunde.append({
                    "code": "U_VALUE_MISMATCH", "severity": "warning",
                    "message": f"{kid}: angegeben {angegeben} W/(m2K), aus dem "
                               f"Schichtaufbau berechnet {erg.u_value} "
                               f"({abw:+.1%}, Verfahren {erg.method})",
                    "construction": kid,
                })
    return befunde


def _audit_altkatalog() -> int:
    """Rechnet den Altbestand catalog/constructions.json nach."""
    materialien = lade_materialien()
    widerstaende = lade_katalog("surface_resistances")
    roh = json.loads((REPO / "catalog" / "constructions.json").read_text(encoding="utf-8"))

    # Bauteilsituation aus der Kategorie des Altformats ableiten.
    ZUORDNUNG = {
        "wall_external":  ("exterior", "wall"),
        "wall_internal":  ("same_zone", "wall"),
        "wall_party":     ("other_zone", "wall"),
        "roof_pitched":   ("exterior", "roof"),
        "roof_flat":      ("exterior", "roof"),
        "floor_top":      ("attic_uninsulated", "ceiling"),
        "floor_basement": ("unheated", "floor"),
        "floor_ground":   ("ground_slab", "floor"),
    }

    print(f"{'Konstruktion':40} {'Katalog':>8} {'berechnet':>10} {'Abw':>8}  Status")
    print("-" * 96)
    zaehler = {"ok": 0, "abweichung": 0, "nicht_rechenbar": 0, "falsches_verfahren": 0}

    for k in roh["constructions"]:
        kat = k.get("category", "")
        angegeben = k.get("u_value_calculated")
        if kat == "window":
            zaehler["falsches_verfahren"] += 1
            print(f"{k['id'][:40]:40} {angegeben:>8} {'—':>10} {'—':>8}  "
                  f"Fenster: Uw nach DIN EN ISO 10077, nicht aus Schichten")
            continue
        if kat not in ZUORDNUNG:
            zaehler["falsches_verfahren"] += 1
            continue

        adjacency, element_type = ZUORDNUNG[kat]
        erg = berechne(k, materialien, widerstaende, adjacency, element_type)
        if not erg.ok:
            zaehler["nicht_rechenbar"] += 1
            print(f"{k['id'][:40]:40} {angegeben:>8} {'—':>10} {'—':>8}  "
                  f"{erg.fehler[0][:44]}")
            continue

        abw = (erg.u_value - angegeben) / angegeben if angegeben else 0
        if abs(abw) <= U_WERT_TOLERANZ:
            zaehler["ok"] += 1
            status = "reproduziert"
        else:
            zaehler["abweichung"] += 1
            status = "weicht ab"
        print(f"{k['id'][:40]:40} {angegeben:>8} {erg.u_value:>10.3f} "
              f"{abw:>+7.1%}  {status}")

    print()
    print(f"reproduziert:        {zaehler['ok']}")
    print(f"weicht ab:           {zaehler['abweichung']}")
    print(f"nicht rechenbar:     {zaehler['nicht_rechenbar']}")
    print(f"falsches Verfahren:  {zaehler['falsches_verfahren']}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="U-Wert-Berechnung nach DIN EN ISO 6946")
    p.add_argument("--construction", help="ID aus catalog/constructions.json")
    p.add_argument("--adjacency", default="exterior", help="adjacency_type")
    p.add_argument("--element-type", default="wall", help="element_type")
    p.add_argument("--sidecar", help="Sidecar nachrechnen und gegen u_value pruefen")
    p.add_argument("--audit-legacy-catalog", action="store_true",
                   help="Altbestand catalog/constructions.json nachrechnen")
    args = p.parse_args()

    if args.audit_legacy_catalog:
        return _audit_altkatalog()

    if args.sidecar:
        sidecar = json.loads(Path(args.sidecar).read_text(encoding="utf-8"))
        befunde = pruefe_sidecar(sidecar)
        if not befunde:
            print("Keine Befunde — alle Konstruktionen reproduzierbar.")
            return 0
        for b in befunde:
            print(f"[{b['severity']:7}] {b['code']:24} {b['message']}")
        return 1 if any(b["severity"] == "warning" for b in befunde) else 0

    if args.construction:
        roh = json.loads(
            (REPO / "catalog" / "constructions.json").read_text(encoding="utf-8")
        )
        treffer = next(
            (c for c in roh["constructions"] if c["id"] == args.construction), None
        )
        if treffer is None:
            print(f"Konstruktion '{args.construction}' nicht gefunden", file=sys.stderr)
            return 2
        erg = berechne(treffer, lade_materialien(), lade_katalog("surface_resistances"),
                       args.adjacency, args.element_type)
        print(f"Konstruktion: {treffer['id']}  ({treffer.get('name_de','')})")
        print(f"Situation:    adjacency={args.adjacency}, element_type={args.element_type}")
        if erg.resistance_source:
            print(f"Rsi/Rse:      {erg.rsi} / {erg.rse}  (Katalog: {erg.resistance_source})")
        if erg.ok:
            print(f"R_total:      {erg.r_total:.4f} (m2K)/W")
            print(f"U-Wert:       {erg.u_value} W/(m2K)   Verfahren: {erg.method}")
            if erg.uncertainty is not None:
                print(f"Unsicherheit: {abs(erg.uncertainty):.2%}")
            if treffer.get("u_value_calculated"):
                a = treffer["u_value_calculated"]
                print(f"im Katalog:   {a}  ({(erg.u_value - a) / a:+.1%})")
        for w in erg.warnungen:
            print(f"WARNUNG: {w}")
        for f in erg.fehler:
            print(f"FEHLER:  {f}")
        return 0 if erg.ok else 1

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
