#!/usr/bin/env python3
"""
ventilated_air_layers.py — belueftete Luftschichten nach DIN EN ISO 6946,
Abschnitt 6.9.

Einstufung ueber die Flaeche der Lueftungsoeffnungen A_ve. Bezug ist je Meter
Laenge in horizontaler Richtung bei VERTIKALEN Luftschichten und je
Quadratmeter Oberflaeche bei HORIZONTALEN Luftschichten:

    A_ve <  500 mm2            ruhend            6.9.2, Tabelle 8
    500 <= A_ve < 1500 mm2     schwach belueftet 6.9.3, Gleichung (11)
    A_ve >= 1500 mm2           stark belueftet   6.9.4

Gleichung (11):

    R_tot = (1500 - A_ve)/1000 * R_tot;nve  +  (A_ve - 500)/1000 * R_tot;ve

  R_tot;nve  Gesamtwiderstand mit RUHENDER Luftschicht nach 6.9.2
  R_tot;ve   Gesamtwiderstand mit STARK BELUEFTETER Luftschicht nach 6.9.4:
             die Luftschicht und alle Schichten zwischen ihr und der
             Aussenumgebung entfallen, als aeusserer Uebergangswiderstand wird
             der Wert fuer ruhende Luft angesetzt (Rsi derselben
             Waermestromrichtung aus Tabelle 7).

Die Gleichung ist an beiden Raendern stetig an die Nachbarfaelle angeschlossen:
bei A_ve = 500 ergibt sie exakt R_tot;nve, bei A_ve = 1500 exakt R_tot;ve. Das
ist die schaerfste Probe auf die Implementierung und steht als Test fest.

A_ve IST PFLICHT. Ohne Angabe wird nicht geraten und nicht auf "ruhend"
zurueckgefallen — der Fall bleibt abgelehnt. Eine geratene Oeffnungsflaeche
verschiebt den U-Wert um zweistellige Prozente.

ZULAESSIGKEIT DER NAEHERUNG: nach der informativen Standardauswahl (Tabelle
B.6) ist die Naeherung nach 6.9.3 zulaessig. Tabelle A.6 ist eine leere Vorlage
fuer nationale Festlegungen; eine abweichende nationale Festlegung geht der
Standardauswahl vor. Das Flag steht im Werte-Overlay und ist umschaltbar, ohne
diesen Code anzufassen — steht es auf false, liefert das Modul kein Ergebnis.

Alle Zahlenwerte (die beiden Schwellen, der Divisor, die Flags) kommen aus dem
Katalog air_layers.

Aufruf:
    python3 tools/ventilated_air_layers.py --aufbau aufbau.json \\
        --air-layer-index 2 --a-ve 1000
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from u_value import (  # noqa: E402
    berechne as berechne_u,
    lade_katalog,
    lade_katalog_roh,
    lade_materialien,
    waehle_uebergangswiderstaende,
)

RUHEND = "unventilated"
SCHWACH = "slightly_ventilated"
STARK = "well_ventilated"


@dataclass
class Belueftungswerte:
    schwelle_ruhend: float | None = None       # A_ve unterhalb -> 6.9.2
    schwelle_stark: float | None = None        # A_ve ab        -> 6.9.4
    divisor: float | None = None
    naeherung_zulaessig: bool | None = None
    fehler: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fehler


def lade_belueftungswerte() -> Belueftungswerte:
    """Schwellen, Divisor und Standardauswahl-Flag aus dem Katalog air_layers."""
    bw = Belueftungswerte()
    roh, meldung = lade_katalog_roh("air_layers")
    if not roh:
        bw.fehler.append("Katalog air_layers nicht gefunden")
        return bw
    if meldung:
        bw.fehler.append(meldung)
        return bw

    def hole(block: str, code: str):
        for e in (roh.get(block) or {}).get("entries", []):
            if e.get("code") == code:
                return e.get("value")
        return None

    bw.schwelle_ruhend = hole("ventilation", "threshold_unventilated_mm2")
    bw.schwelle_stark = hole("ventilation", "threshold_well_ventilated_mm2")
    bw.divisor = hole("ventilation", "interpolation_divisor")
    bw.naeherung_zulaessig = hole("standard_selection",
                                  "approximation_6_9_3_permitted")
    for name in ("schwelle_ruhend", "schwelle_stark", "divisor",
                 "naeherung_zulaessig"):
        if getattr(bw, name) is None:
            bw.fehler.append(f"'{name}' fehlt im Katalog air_layers — "
                             f"Werte-Overlay unvollstaendig")
    return bw


def einstufung(a_ve_mm2: float, bw: Belueftungswerte) -> str:
    """Einstufung nach 6.9. Identisch fuer beide Richtungen, nur der Bezug von
    A_ve unterscheidet sich (je Meter Laenge bzw. je Quadratmeter)."""
    if a_ve_mm2 < bw.schwelle_ruhend:
        return RUHEND
    if a_ve_mm2 < bw.schwelle_stark:
        return SCHWACH
    return STARK


@dataclass
class Ergebnis:
    einstufung: str = ""
    a_ve_mm2: float | None = None
    bezug: str = ""
    r_tot: float | None = None
    r_tot_nve: float | None = None
    r_tot_ve: float | None = None
    u_value: float | None = None
    rse_ruhend: float | None = None
    hinweise: list = field(default_factory=list)
    warnungen: list = field(default_factory=list)
    fehler: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.r_tot is not None and not self.fehler


def _bezugstext(orientierung: str) -> str:
    return ("je Meter Laenge in horizontaler Richtung (vertikale Luftschicht)"
            if orientierung == "vertical"
            else "je Quadratmeter Oberflaeche (horizontale Luftschicht)")


def _r_tot_stark_belueftet(
    layers: list, luftschicht_index: int, materialien: dict,
    widerstaende: dict, adjacency_type: str, element_type: str,
) -> tuple[float | None, float | None, list]:
    """
    R_tot;ve nach 6.9.4.

    Die Luftschicht und ALLES, was zwischen ihr und der Aussenumgebung liegt,
    entfaellt. Als aeusserer Uebergangswiderstand wird der Wert fuer ruhende
    Luft angesetzt; die Norm laesst dafuer ausdruecklich den Rsi-Wert derselben
    Waermestromrichtung aus Tabelle 7 zu. Genau der wird hier aus dem Katalog
    genommen — kein neuer Zahlenwert im Code.
    """
    rb = waehle_uebergangswiderstaende(adjacency_type, element_type, widerstaende)
    if rb is None:
        return None, None, [
            f"Keine Uebergangswiderstaende fuer adjacency_type="
            f"'{adjacency_type}', element_type='{element_type}' im Katalog"]
    rsi, _rse, code = rb
    rse_ruhend = rsi

    innen = layers[:luftschicht_index]

    # Synthetischer Widerstands-Katalog: derselbe Eintrag, aber mit dem
    # ruhenden Aussenwert. So bleibt die Rechnung in u_value.berechne() und wird
    # nicht nachgebaut.
    eintrag_ve = dict(widerstaende[code])
    eintrag_ve["rse"] = rse_ruhend
    widerstaende_ve = {code: eintrag_ve}

    if not innen:
        # Die Luftschicht ist die innerste Schicht — es bleiben nur die beiden
        # Uebergangswiderstaende.
        return rsi + rse_ruhend, rse_ruhend, []

    erg = berechne_u({"id": "ve", "layers": innen}, materialien, widerstaende_ve,
                     adjacency_type, element_type)
    if not erg.ok:
        return None, rse_ruhend, erg.fehler
    return erg.r_total, rse_ruhend, []


def berechne(
    layers: list,
    luftschicht_index: int,
    a_ve_mm2: float | None,
    materialien: dict | None = None,
    widerstaende: dict | None = None,
    adjacency_type: str = "exterior",
    element_type: str = "wall",
    orientierung: str = "vertical",
    belueftungswerte: Belueftungswerte | None = None,
) -> Ergebnis:
    """
    Gesamtwiderstand eines Aufbaus mit belueftbarer Luftschicht nach 6.9.

    layers ist von innen nach aussen geordnet; luftschicht_index zeigt auf die
    Luftschicht in dieser Liste.
    """
    erg = Ergebnis(a_ve_mm2=a_ve_mm2, bezug=_bezugstext(orientierung))
    materialien = lade_materialien() if materialien is None else materialien
    widerstaende = (lade_katalog("surface_resistances") if widerstaende is None
                    else widerstaende)
    bw = lade_belueftungswerte() if belueftungswerte is None else belueftungswerte
    if not bw.ok:
        erg.fehler.extend(bw.fehler)
        return erg

    if a_ve_mm2 is None:
        erg.fehler.append(
            "A_ve (Flaeche der Lueftungsoeffnungen) fehlt. Ohne diese Angabe ist "
            "die Luftschicht nicht einstufbar; es wird weder geraten noch auf "
            "'ruhend' zurueckgefallen. A_ve angeben — Bezug: "
            + _bezugstext(orientierung))
        return erg
    if a_ve_mm2 < 0:
        erg.fehler.append("A_ve darf nicht negativ sein")
        return erg
    if not 0 <= luftschicht_index < len(layers):
        erg.fehler.append(
            f"luftschicht_index {luftschicht_index} liegt ausserhalb der "
            f"Schichtliste (0 bis {len(layers) - 1})")
        return erg

    erg.einstufung = einstufung(a_ve_mm2, bw)

    # R_tot;nve — Luftschicht ruhend nach 6.9.2/Tabelle 8.
    erg_nve = berechne_u({"id": "nve", "layers": layers}, materialien,
                         widerstaende, adjacency_type, element_type)
    if not erg_nve.ok:
        erg.fehler.extend(erg_nve.fehler)
        return erg
    erg.r_tot_nve = erg_nve.r_total

    if erg.einstufung == RUHEND:
        erg.r_tot = erg.r_tot_nve
        erg.hinweise.append(
            f"A_ve = {a_ve_mm2:g} mm2 ({erg.bezug}) liegt unter "
            f"{bw.schwelle_ruhend:g} mm2 — Luftschicht ruhend, gerechnet nach "
            f"6.9.2 mit Tabelle 8.")
        erg.u_value = round(1.0 / erg.r_tot, 4)
        return erg

    # R_tot;ve — Luftschicht und alles aussen davon entfaellt, 6.9.4.
    r_ve, rse_ruhend, fehler = _r_tot_stark_belueftet(
        layers, luftschicht_index, materialien, widerstaende, adjacency_type,
        element_type)
    erg.rse_ruhend = rse_ruhend
    if fehler:
        erg.fehler.extend(fehler)
        return erg
    erg.r_tot_ve = r_ve

    if erg.einstufung == STARK:
        erg.r_tot = erg.r_tot_ve
        erg.hinweise.append(
            f"A_ve = {a_ve_mm2:g} mm2 ({erg.bezug}) erreicht "
            f"{bw.schwelle_stark:g} mm2 — stark belueftet nach 6.9.4: "
            f"Luftschicht und alle aussen davon liegenden Schichten entfallen, "
            f"Rse = {rse_ruhend} (ruhende Luft).")
        erg.u_value = round(1.0 / erg.r_tot, 4)
        return erg

    # --- 6.9.3, Gleichung (11) --------------------------------------------
    if not bw.naeherung_zulaessig:
        erg.fehler.append(
            "Die Naeherung nach 6.9.3 ist im Werte-Overlay als nicht zulaessig "
            "gekennzeichnet (standard_selection.approximation_6_9_3_permitted = "
            "false). Kein Ergebnis — nationale Festlegung beachten.")
        return erg

    erg.r_tot = ((bw.schwelle_stark - a_ve_mm2) / bw.divisor * erg.r_tot_nve
                 + (a_ve_mm2 - bw.schwelle_ruhend) / bw.divisor * erg.r_tot_ve)
    erg.u_value = round(1.0 / erg.r_tot, 4)
    erg.hinweise.append(
        f"A_ve = {a_ve_mm2:g} mm2 ({erg.bezug}) liegt zwischen "
        f"{bw.schwelle_ruhend:g} und {bw.schwelle_stark:g} mm2 — schwach "
        f"belueftet, Gleichung (11): R_tot = "
        f"({bw.schwelle_stark:g}-{a_ve_mm2:g})/{bw.divisor:g} * "
        f"{erg.r_tot_nve:.4f} + ({a_ve_mm2:g}-{bw.schwelle_ruhend:g})/"
        f"{bw.divisor:g} * {erg.r_tot_ve:.4f} = {erg.r_tot:.4f} (m2K)/W")
    erg.hinweise.append(
        "Zulaessigkeit der Naeherung: nach der informativen Standardauswahl "
        "(Tabelle B.6) zulaessig. Eine abweichende nationale Festlegung geht "
        "vor (Tabelle A.6 ist die leere Vorlage dafuer).")
    return erg


def main() -> int:
    p = argparse.ArgumentParser(
        description="Belueftete Luftschichten nach DIN EN ISO 6946, 6.9")
    p.add_argument("--aufbau", required=True,
                   help="JSON-Datei mit layers[] von innen nach aussen")
    p.add_argument("--air-layer-index", type=int, required=True)
    p.add_argument("--a-ve", type=float,
                   help="Flaeche der Lueftungsoeffnungen in mm2 (Pflicht)")
    p.add_argument("--orientation", default="vertical",
                   choices=["vertical", "horizontal"])
    p.add_argument("--adjacency", default="exterior")
    p.add_argument("--element-type", default="wall")
    args = p.parse_args()

    daten = json.loads(Path(args.aufbau).read_text(encoding="utf-8"))
    layers = daten.get("layers", daten if isinstance(daten, list) else [])

    erg = berechne(layers, args.air_layer_index, args.a_ve,
                   adjacency_type=args.adjacency, element_type=args.element_type,
                   orientierung=args.orientation)

    print(f"Einstufung:   {erg.einstufung or '—'}")
    print(f"A_ve:         {erg.a_ve_mm2} mm2  ({erg.bezug})")
    if erg.r_tot_nve is not None:
        print(f"R_tot;nve:    {erg.r_tot_nve:.4f} (m2K)/W")
    if erg.r_tot_ve is not None:
        print(f"R_tot;ve:     {erg.r_tot_ve:.4f} (m2K)/W")
    if erg.r_tot is not None:
        print(f"R_tot:        {erg.r_tot:.4f} (m2K)/W     U = {erg.u_value}")
    for h in erg.hinweise:
        print(f"  - {h}")
    for w in erg.warnungen:
        print(f"WARNUNG: {w}")
    for f in erg.fehler:
        print(f"FEHLER:  {f}")
    return 0 if erg.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
