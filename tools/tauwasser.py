#!/usr/bin/env python3
"""
tauwasser.py — Tauwassernachweis nach dem Periodenbilanzverfahren (Glaser),
DIN 4108-3, Anhang A und C.

Rechnet aus dem Schichtaufbau einer Konstruktion die Tauwassermasse der
Tauperiode und die abgegebene Masse der Verdunstungsperiode und bewertet beides
nach 5.2.2/5.3. Klimarandbedingungen, Uebergangswiderstaende, der
Diffusionsleitkoeffizient delta_0 und die Grenzwerte kommen aus dem Katalog
moisture_conditions (Struktur oeffentlich, Zahlen im privaten Werte-Overlay) —
in diesem Modul steht bewusst keine einzige Normzahl.

Verfahren in vier Schritten:

  1. Temperaturverlauf     C.1/C.2/C.4 — ueber die Schichtwiderstaende. Der
                           R-Wert je Schicht kommt aus tools/u_value.py, damit
                           U-Wert und Tauwassernachweis nie auseinanderlaufen.
  2. Saettigungsdruck      C.15/C.16 an jeder Schichtgrenze.
  3. Glaser-Konstruktion   Der Dampfdruckverlauf ueber s_d ist die untere
                           konvexe Huelle ("gespanntes Seil") zwischen (0, p_i)
                           und (s_dT, p_e) unterhalb der Saettigungskurve. Wo
                           das Seil die Kurve beruehrt, faellt Tauwasser aus.
  4. Massenbilanz          Tauperiode A.3 bis A.11, Verdunstungsperiode
                           A.12 bis A.28, je nach Fall.

Abgedeckte Faelle der Norm:

  keine_kondensation  Das Seil beruehrt die Saettigungskurve nicht.
  b                   Eine Tauebene.                 A.3/A.4  ·  A.12/A.13
  c                   Zwei getrennte Tauebenen.      A.5-A.9  ·  A.14-A.26
  d                   Ein zusammenhaengender
                      Tauwasserbereich.              A.10/A.11 ·  A.27/A.28

WAS DIESES MODUL NICHT KANN, bewusst:
  - Mehr als zwei getrennte Tauebenen. Die Norm gibt dafuer keine Gleichungen;
    das Modul meldet den Fall als nicht abgedeckt, statt zu extrapolieren.
  - Tauwasser an der raumseitigen Oberflaeche (Schimmelkriterium nach 4.3,
    fRsi >= 0,7). Wird erkannt und gemeldet, aber nicht bewertet.
  - Das Zusatzkriterium fuer Holz und Holzwerkstoffe nach 5.3 (zulaessige
    Erhoehung des Massenanteils der Feuchte um 5 % bzw. 3 %). Dafuer braucht es
    Rohdichte und Ausgangsfeuchte je Schicht, die der Materialkatalog nicht
    fuehrt.
  - Instationaere Verfahren nach DIN EN 15026. Das Periodenbilanzverfahren ist
    ein Bewertungs-, kein Simulationsverfahren.
  - Tauebenen INNERHALB einer Schicht. Die Glaser-Konstruktion wird wie in der
    Norm ueber die Schichtgrenzen gefuehrt: p_sat wird an den Knoten bestimmt
    und dazwischen geradlinig verbunden. Der wahre Saettigungsverlauf ueber s_d
    ist innerhalb einer Schicht konvex und liegt damit UNTER dieser Geraden —
    in sehr dicken Einzelschichten kann deshalb ein Tauwasserausfall unerkannt
    bleiben, den eine feinere Unterteilung zeigen wuerde. Wer das ausschliessen
    will, teilt dicke Schichten in mehrere Teilschichten auf; das Ergebnis
    konvergiert dann gegen den stetigen Verlauf. Bekannte Eigenschaft des
    Verfahrens, keine Abweichung von der Norm.

Aufruf:
    python3 tools/tauwasser.py --construction WALL_EXT_BRICK_WDVS_160
    python3 tools/tauwasser.py --aufbau aufbau.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from u_value import (  # noqa: E402
    REPO,
    lade_katalog_roh,
    lade_luftschichten,
    lade_materialien,
    schicht_widerstand,
)

SEKUNDEN_PRO_TAG = 24 * 60 * 60

# Bauteiltypen, fuer die das Massenkriterium nach 5.2.2 gilt: Daecher und
# Waende gegen Aussenluft sowie Decken unter nicht ausgebauten Dachraeumen.
# DWE-eigene Auslegung der Aufzaehlung, keine Normzahl.
MASSENKRITERIUM_ELEMENT_TYPEN = {"wall", "roof", "ceiling"}
MASSENKRITERIUM_ANGRENZUNGEN = {"exterior", "attic_uninsulated"}

# Zwei Saettigungsdruecke gelten als gleich, wenn sie sich um weniger als das
# unterscheiden [Pa]. Rechen-Toleranz, keine Normgroesse.
DRUCK_TOLERANZ = 1.0


# ---------------------------------------------------------------------------
# Grundfunktionen der Norm
# ---------------------------------------------------------------------------

def saettigungsdampfdruck(theta: float) -> float:
    """
    Wasserdampf-Saettigungsdruck [Pa], DIN 4108-3 Gleichungen C.15 und C.16.

        theta >= 0 :  p_sat = 610,5 * exp(17,269 * theta / (237,3 + theta))
        theta <  0 :  p_sat = 610,5 * exp(21,875 * theta / (265,5 + theta))

    Die Beiwerte sind Bestandteil der Gleichung, nicht Tabellenwerte — sie
    stehen deshalb hier und nicht im Werte-Overlay.
    """
    if theta >= 0.0:
        return 610.5 * math.exp(17.269 * theta / (237.3 + theta))
    return 610.5 * math.exp(21.875 * theta / (265.5 + theta))


def taupunkttemperatur(p: float) -> float:
    """
    Taupunkttemperatur [Grad C] zu einem Wasserdampfteildruck, C.17/C.18.

    ABWEICHUNG VOM GEDRUCKTEN NORMTEXT, bewusst: C.18 nennt im Nenner den
    Beiwert 265,6, waehrend C.16 fuer denselben Ast mit 265,5 rechnet. Mit
    265,6 ist taupunkttemperatur() nicht die exakte Umkehrung von
    saettigungsdampfdruck() — der Rundgang p -> theta -> p driftet bis zu
    0,006 K bei -15 Grad C auseinander. Implementiert ist deshalb 265,5, damit
    beide Richtungen konsistent sind. Der Unterschied liegt weit unterhalb der
    Ablesegenauigkeit des Verfahrens; die Konsistenz ist wichtiger als die
    woertliche Uebernahme eines offensichtlichen Druckfehlers.
    """
    if p <= 0:
        raise ValueError("Wasserdampfteildruck muss positiv sein")
    ln = math.log(p / 610.5)
    theta = 237.3 * ln / (17.269 - ln)
    if theta < 0.0:
        theta = 265.5 * ln / (21.875 - ln)
    return theta


# ---------------------------------------------------------------------------
# Randbedingungen aus dem Katalog
# ---------------------------------------------------------------------------

@dataclass
class Randbedingungen:
    """Eine Periode aus Tabelle A.3, plus delta_0 und die Grenzwerte."""
    code: str = ""
    theta_i: float | None = None
    phi_i: float | None = None
    theta_e: float | None = None
    phi_e: float | None = None
    duration_days: float | None = None
    rsi: float | None = None
    rse: float | None = None

    @property
    def p_i(self) -> float:
        return self.phi_i * saettigungsdampfdruck(self.theta_i)

    @property
    def p_e(self) -> float:
        return self.phi_e * saettigungsdampfdruck(self.theta_e)

    @property
    def dauer_s(self) -> float:
        return self.duration_days * SEKUNDEN_PRO_TAG

    @property
    def vollstaendig(self) -> bool:
        return None not in (self.theta_i, self.phi_i, self.theta_e, self.phi_e,
                            self.duration_days, self.rsi, self.rse)


@dataclass
class Katalogwerte:
    perioden: dict = field(default_factory=dict)
    delta_0: float | None = None
    m_c_max_general: float | None = None
    m_c_max_non_capillary: float | None = None
    w_capillary_threshold: float | None = None
    fehler: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fehler


def lade_randbedingungen() -> Katalogwerte:
    """
    Laedt moisture_conditions inkl. privatem Werte-Overlay.

    Ohne Overlay bleibt die Struktur lesbar, die Zahlen sind null — dann meldet
    diese Funktion den Fehler und der Nachweis wird gar nicht erst gerechnet.
    Genau das ist gewollt: lieber kein Ergebnis als ein Ergebnis aus geratenen
    Randbedingungen.
    """
    kw = Katalogwerte()
    roh, meldung = lade_katalog_roh("moisture_conditions")
    if not roh:
        kw.fehler.append("Katalog moisture_conditions nicht gefunden")
        return kw
    if meldung:
        kw.fehler.append(meldung)
        return kw

    for eintrag in roh.get("entries", []):
        rb = Randbedingungen(
            code=eintrag.get("code", ""),
            theta_i=eintrag.get("theta_i"), phi_i=eintrag.get("phi_i"),
            theta_e=eintrag.get("theta_e"), phi_e=eintrag.get("phi_e"),
            duration_days=eintrag.get("duration_days"),
            rsi=eintrag.get("rsi"), rse=eintrag.get("rse"),
        )
        kw.perioden[rb.code] = rb
        if not rb.vollstaendig:
            kw.fehler.append(
                f"Randbedingungen '{rb.code}' unvollstaendig — Werte-Overlay fehlt "
                f"oder ist lueckenhaft"
            )

    def hole_block(block: str, code: str):
        for e in (roh.get(block) or {}).get("entries", []):
            if e.get("code") == code:
                return e.get("value")
        return None

    kw.delta_0 = hole_block("diffusion", "delta_0")
    kw.m_c_max_general = hole_block("assessment_limits", "m_c_max_general")
    kw.m_c_max_non_capillary = hole_block("assessment_limits",
                                          "m_c_max_non_capillary")
    kw.w_capillary_threshold = hole_block("assessment_limits",
                                          "w_capillary_threshold")
    if kw.delta_0 is None:
        kw.fehler.append("delta_0 fehlt im Katalog moisture_conditions")
    for name in ("m_c_max_general", "m_c_max_non_capillary",
                 "w_capillary_threshold"):
        if getattr(kw, name) is None:
            kw.fehler.append(f"Grenzwert '{name}' fehlt im Katalog "
                             f"moisture_conditions")
    return kw


def waehle_perioden(kw: Katalogwerte) -> tuple[Randbedingungen | None,
                                               Randbedingungen | None]:
    """Erste Tau- und erste Verdunstungsperiode aus dem Katalog."""
    tau = next((r for r in kw.perioden.values()
                if r.code.startswith("tauperiode")), None)
    verd = next((r for r in kw.perioden.values()
                 if r.code.startswith("verdunstungsperiode")), None)
    return tau, verd


# ---------------------------------------------------------------------------
# Schichtgroessen
# ---------------------------------------------------------------------------

def sd_wert(schicht: dict, materialien: dict) -> tuple[float | None, str | None]:
    """
    Wasserdampfdiffusionsaequivalente Luftschichtdicke s_d = mu * d, C.5.

    Reihenfolge wie bei schicht_widerstand(): expliziter s_d, dann mu an der
    Schicht, dann mu aus dem Materialkatalog. Eine Luftschicht hat mu = 1 —
    sie IST die Referenz, auf die sich s_d bezieht.
    """
    if schicht.get("sd_value") is not None:
        return float(schicht["sd_value"]), None

    dicke = schicht.get("thickness_m", schicht.get("thickness"))
    mu = schicht.get("mu")

    if mu is None and schicht.get("air_layer"):
        mu = 1.0
    if mu is None:
        ref = schicht.get("material_ref") or schicht.get("material")
        if ref:
            material = materialien.get(ref)
            if material is None:
                return None, f"Material '{ref}' steht in keinem Katalog"
            mu = material.get("mu")
    if mu is None:
        return None, ("Schicht ohne mu und ohne sd_value — ohne "
                      "Diffusionswiderstandszahl ist kein Glaser-Diagramm "
                      "aufstellbar")
    if dicke is None:
        return None, "Schicht ohne thickness_m und ohne sd_value"
    if float(mu) < 0:
        return None, "mu ist negativ"
    return float(dicke) * float(mu), None


def kapillar_wasseraufnahmefaehig(
    schicht: dict, materialien: dict, w_grenze: float
) -> bool | None:
    """
    Ist die Schicht kapillar wasseraufnahmefaehig? True/False/None (unbekannt).

    Kriterium nach 5.2.2: w >= w_grenze [kg/(m2*h^0,5)]. Liegt kein
    Wasseraufnahmekoeffizient vor, zaehlt ein ausdruecklich gesetztes Flag
    capillary_active; sonst ist die Lage unbekannt und der Aufrufer entscheidet
    konservativ.
    """
    for quelle in (schicht, materialien.get(
            schicht.get("material_ref") or schicht.get("material") or "", {})):
        if not isinstance(quelle, dict):
            continue
        if quelle.get("w_value") is not None:
            return float(quelle["w_value"]) >= w_grenze
        if quelle.get("capillary_active") is not None:
            return bool(quelle["capillary_active"])
    return None


# ---------------------------------------------------------------------------
# Glaser-Konstruktion
# ---------------------------------------------------------------------------

@dataclass
class Feld:
    """
    Temperatur- und Druckfeld einer Periode.

    Knoten 0 ist die raumseitige Oberflaeche (s_d = 0), Knoten i die Grenze
    hinter Schicht i, letzter Knoten die aussenseitige Oberflaeche.
    """
    sd: list = field(default_factory=list)          # kumuliert [m]
    theta: list = field(default_factory=list)       # [Grad C]
    p_sat: list = field(default_factory=list)       # [Pa]
    r_kumuliert: list = field(default_factory=list) # ab theta_i, inkl. Rsi
    r_total: float = 0.0
    sd_total: float = 0.0
    q: float = 0.0
    p_i: float = 0.0
    p_e: float = 0.0

    def theta_bei_sd(self, s: float) -> float:
        """
        Temperatur an einer beliebigen Stelle des Glaser-Diagramms.

        Innerhalb einer Schicht sind s_d und R beide proportional zur Dicke —
        deshalb ist die lineare Interpolation zwischen zwei Knoten exakt und
        keine Naeherung. Gebraucht wird das nur fuer die Mitte eines
        Tauwasserbereichs (A.27).
        """
        if s <= self.sd[0]:
            return self.theta[0]
        if s >= self.sd[-1]:
            return self.theta[-1]
        for i in range(len(self.sd) - 1):
            unten, oben = self.sd[i], self.sd[i + 1]
            if unten <= s <= oben:
                if oben == unten:
                    return self.theta[i]
                anteil = (s - unten) / (oben - unten)
                return self.theta[i] + anteil * (self.theta[i + 1] - self.theta[i])
        return self.theta[-1]

    def p_sat_bei_sd(self, s: float) -> float:
        return saettigungsdampfdruck(self.theta_bei_sd(s))


def baue_feld(
    layers: list,
    materialien: dict,
    rb: Randbedingungen,
    luftschichten: dict | None = None,
) -> tuple[Feld | None, list]:
    """
    Temperaturverteilung C.1/C.2/C.4 und s_d-Achse C.5 fuer eine Periode.

        q     = (theta_i - theta_e) / R_T
        theta_si = theta_i - q * Rsi
        theta_n  = theta_i - q * (Rsi + R_1 + ... + R_n)

    Gerechnet wird mit q aus dem exakten R_T, nicht aus dem gerundeten U-Wert —
    Runden erst am Ende.
    """
    fehler: list = []
    luftschichten = luftschichten if luftschichten is not None else lade_luftschichten()

    r_werte, sd_werte = [], []
    for i, schicht in enumerate(layers, start=1):
        r, problem = schicht_widerstand(schicht, materialien, "horizontal",
                                        luftschichten)
        if problem:
            fehler.append(f"Schicht {i}: {problem}")
        else:
            r_werte.append(r)
        s, problem = sd_wert(schicht, materialien)
        if problem:
            fehler.append(f"Schicht {i}: {problem}")
        else:
            sd_werte.append(s)
    if fehler:
        return None, fehler

    feld = Feld()
    feld.r_total = rb.rsi + sum(r_werte) + rb.rse
    feld.sd_total = sum(sd_werte)
    if feld.r_total <= 0:
        return None, ["R_T ist nicht positiv"]
    if feld.sd_total <= 0:
        return None, ["Summe s_d ist null — ohne Diffusionswiderstand kein "
                      "Glaser-Diagramm"]

    feld.q = (rb.theta_i - rb.theta_e) / feld.r_total
    kumuliert = rb.rsi
    feld.r_kumuliert = [kumuliert]
    feld.sd = [0.0]
    feld.theta = [rb.theta_i - feld.q * kumuliert]
    for r, s in zip(r_werte, sd_werte):
        kumuliert += r
        feld.r_kumuliert.append(kumuliert)
        feld.sd.append(feld.sd[-1] + s)
        feld.theta.append(rb.theta_i - feld.q * kumuliert)
    feld.p_sat = [saettigungsdampfdruck(t) for t in feld.theta]
    feld.p_i, feld.p_e = rb.p_i, rb.p_e
    return feld, []


def tauebenen(feld: Feld) -> list:
    """
    Knotenindizes, an denen der Dampfdruckverlauf die Saettigungskurve beruehrt.

    Die Glaser-Konstruktion ist nichts anderes als die untere konvexe Huelle
    der Punkte (s_d, p_sat) zwischen (0, p_i) und (s_dT, p_e): ein zwischen den
    Randwerten gespanntes Seil, das nirgends ueber die Saettigungskurve darf.
    Umgesetzt als Kettenschritt — vom aktuellen Punkt aus immer zu dem Knoten
    mit der kleinsten Steigung. Endet der Schritt am Aussenrand, ist die Huelle
    fertig; jeder andere Zielknoten ist eine Tauebene.
    """
    n = len(feld.sd)
    ebenen: list = []
    aktuell, p_aktuell = 0, feld.p_i
    while True:
        bester, beste_steigung = None, None
        for j in range(aktuell + 1, n):
            if feld.sd[j] <= feld.sd[aktuell]:
                continue                       # Schicht ohne s_d-Beitrag
            y = feld.p_e if j == n - 1 else feld.p_sat[j]
            steigung = (y - p_aktuell) / (feld.sd[j] - feld.sd[aktuell])
            if beste_steigung is None or steigung < beste_steigung - 1e-12:
                beste_steigung, bester = steigung, j
        if bester is None or bester == n - 1:
            return ebenen
        ebenen.append(bester)
        aktuell, p_aktuell = bester, feld.p_sat[bester]


def klassifiziere(ebenen: list) -> tuple[str, list]:
    """
    Ordnet die gefundenen Tauebenen einem Fall der Norm zu.

    Zwei BENACHBARTE Beruehrungsknoten bedeuten, dass das Seil der
    Saettigungskurve ueber eine ganze Schicht folgt — dann faellt Tauwasser
    nicht in einer Ebene, sondern im ganzen Bereich dazwischen aus (Fall d).
    Zwei Knoten mit Abstand sind zwei getrennte Ebenen (Fall c).
    """
    if not ebenen:
        return "keine_kondensation", []
    if len(ebenen) == 1:
        return "b", ebenen
    zusammenhaengend = all(b == a + 1 for a, b in zip(ebenen, ebenen[1:]))
    if zusammenhaengend:
        return "d", [ebenen[0], ebenen[-1]]
    if len(ebenen) == 2:
        return "c", ebenen
    return "nicht_abgedeckt", ebenen


# ---------------------------------------------------------------------------
# Massenbilanz
# ---------------------------------------------------------------------------

def tauperiode(feld: Feld, fall: str, ebenen: list, delta_0: float,
               t_c: float) -> dict:
    """
    Tauwassermasse der Tauperiode, A.3 bis A.11.

    Fall b (A.3/A.4):
        g_c = delta_0 * [ (p_i - p_c)/s_dc - (p_c - p_e)/(s_dT - s_dc) ]
    Fall c (A.5 bis A.9): zwei Ebenen, die innere gibt an die aeussere ab.
    Fall d (A.10/A.11): der Strom laeuft in den Bereich hinein und aus ihm
        heraus; zwischen den Bereichsraendern gibt es keinen Transport, weil
        dort ueberall Saettigung herrscht.
    """
    sdt = feld.sd_total
    p_i, p_e = feld.p_i, feld.p_e

    if fall == "b":
        c = ebenen[0]
        sdc, p_c = feld.sd[c], feld.p_sat[c]
        g_c = delta_0 * ((p_i - p_c) / sdc - (p_c - p_e) / (sdt - sdc))
        return {"g_c": [g_c], "m_c": [g_c * t_c], "m_c_gesamt": g_c * t_c}

    c1, c2 = ebenen
    sdc1, sdc2 = feld.sd[c1], feld.sd[c2]
    p_c1, p_c2 = feld.p_sat[c1], feld.p_sat[c2]

    if fall == "c":
        zwischen = (p_c1 - p_c2) / (sdc2 - sdc1)
        g_c1 = delta_0 * ((p_i - p_c1) / sdc1 - zwischen)
        g_c2 = delta_0 * (zwischen - (p_c2 - p_e) / (sdt - sdc2))
        return {"g_c": [g_c1, g_c2], "m_c": [g_c1 * t_c, g_c2 * t_c],
                "m_c_gesamt": (g_c1 + g_c2) * t_c}

    # Fall d
    g_c = delta_0 * ((p_i - p_c1) / sdc1 - (p_c2 - p_e) / (sdt - sdc2))
    return {"g_c": [g_c], "m_c": [g_c * t_c], "m_c_gesamt": g_c * t_c}


def verdunstungsperiode(feld: Feld, fall: str, ebenen: list, m_c: list,
                        delta_0: float, t_ev: float) -> dict:
    """
    Abgegebene Masse der Verdunstungsperiode, A.12 bis A.28.

    Der Vorzeichenwechsel gegenueber der Tauperiode ist der Kern: das Tauwasser
    wird nach BEIDEN Seiten abgegeben, die beiden Terme addieren sich statt sich
    zu subtrahieren.

    Fall c braucht eine Fallunterscheidung, weil eine Ebene vorzeitig
    austrocknen kann (A.16/A.17). Ab diesem Zeitpunkt ist sie keine Quelle mehr,
    sondern ein Durchgang — die verbleibende Ebene gibt dann auch ueber die
    Strecke ab, die vorher die andere Ebene belegt hat (A.22/A.25).
    """
    sdt = feld.sd_total
    p_i, p_e = feld.p_i, feld.p_e
    ergebnis: dict = {"warnungen": []}

    if fall == "b":
        c = ebenen[0]
        sdc = feld.sd[c]
        p_c = feld.p_sat_bei_sd(sdc)
        g_ev = delta_0 * ((p_c - p_i) / sdc + (p_c - p_e) / (sdt - sdc))
        ergebnis.update({"g_ev": [g_ev], "m_ev": [g_ev * t_ev],
                         "m_ev_gesamt": g_ev * t_ev, "p_c": [p_c]})
        return ergebnis

    if fall == "d":
        sdc1, sdc2 = feld.sd[ebenen[0]], feld.sd[ebenen[1]]
        # A.27: die gesamte Masse sitzt rechnerisch in der Bereichsmitte.
        sdcm = sdc1 + 0.5 * (sdc2 - sdc1)
        p_c = feld.p_sat_bei_sd(sdcm)
        g_ev = delta_0 * ((p_c - p_i) / sdcm + (p_c - p_e) / (sdt - sdcm))
        ergebnis.update({"g_ev": [g_ev], "m_ev": [g_ev * t_ev],
                         "m_ev_gesamt": g_ev * t_ev, "p_c": [p_c],
                         "sd_cm": sdcm})
        return ergebnis

    # --- Fall c ------------------------------------------------------------
    c1, c2 = ebenen
    sdc1, sdc2 = feld.sd[c1], feld.sd[c2]
    p_c1 = feld.p_sat_bei_sd(sdc1)
    p_c2 = feld.p_sat_bei_sd(sdc2)
    if abs(p_c1 - p_c2) > DRUCK_TOLERANZ:
        # A.14 bis A.26 setzen p_c1 = p_c2 voraus; nur dann fliesst zwischen den
        # Ebenen nichts. Bei den Randbedingungen der Tabelle A.3 ist das erfuellt,
        # weil innen und aussen dieselbe Temperatur herrscht.
        ergebnis["warnungen"].append(
            f"Voraussetzung p_c1 = p_c2 der Gleichungen A.14 bis A.26 verletzt "
            f"({p_c1:.1f} gegen {p_c2:.1f} Pa) — es gaebe einen Strom zwischen "
            f"den Tauebenen, den die Norm hier nicht abbildet. Ergebnis ist eine "
            f"Naeherung."
        )
    p_c = p_c1

    g_ev1 = delta_0 * (p_c - p_i) / sdc1                    # A.14
    g_ev2 = delta_0 * (p_c - p_e) / (sdt - sdc2)            # A.15

    if g_ev1 <= 0 or g_ev2 <= 0:
        ergebnis["warnungen"].append(
            "Mindestens eine Tauebene gibt kein Wasser ab (Saettigungsdruck "
            "liegt nicht ueber dem Umgebungsdruck) — Austrocknung findet in der "
            "Verdunstungsperiode nicht statt."
        )
        g_ev1, g_ev2 = max(g_ev1, 0.0), max(g_ev2, 0.0)

    t_ev1 = m_c[0] / g_ev1 if g_ev1 > 0 else math.inf      # A.16
    t_ev2 = m_c[1] / g_ev2 if g_ev2 > 0 else math.inf      # A.17

    if t_ev1 > t_ev and t_ev2 > t_ev:
        # Fall a): keine Ebene trocknet vorzeitig aus, A.18 bis A.20
        m_ev1, m_ev2 = g_ev1 * t_ev, g_ev2 * t_ev
        unterfall = "a"
    elif t_ev1 <= t_ev2:
        # Ebene 1 ist zuerst trocken, A.21 bis A.23
        m_ev1 = g_ev1 * t_ev1
        m_ev2 = (g_ev2 * t_ev1
                 + (delta_0 * (p_c2 - p_i) / sdc2 + g_ev2) * (t_ev - t_ev1))
        unterfall = "b/ebene1"
    else:
        # Ebene 2 ist zuerst trocken, A.24 bis A.26
        m_ev2 = g_ev2 * t_ev2
        m_ev1 = (g_ev1 * t_ev2
                 + (g_ev1 + delta_0 * (p_c1 - p_e) / (sdt - sdc1))
                 * (t_ev - t_ev2))
        unterfall = "b/ebene2"

    ergebnis.update({
        "g_ev": [g_ev1, g_ev2], "m_ev": [m_ev1, m_ev2],
        "m_ev_gesamt": m_ev1 + m_ev2, "p_c": [p_c1, p_c2],
        "t_ev": [t_ev1, t_ev2], "unterfall": unterfall,
    })
    return ergebnis


# ---------------------------------------------------------------------------
# Gesamtergebnis
# ---------------------------------------------------------------------------

@dataclass
class Ergebnis:
    fall: str = "keine_kondensation"
    r_total: float | None = None
    sd_total: float | None = None
    u_value: float | None = None
    ebenen: list = field(default_factory=list)      # Knotenindizes
    ebenen_sd: list = field(default_factory=list)
    ebenen_theta: list = field(default_factory=list)
    p_c: list = field(default_factory=list)
    m_c: list = field(default_factory=list)
    m_c_gesamt: float = 0.0
    m_ev: list = field(default_factory=list)
    m_ev_gesamt: float = 0.0
    grenzwerte: list = field(default_factory=list)
    kriterium_verdunstung: bool | None = None
    kriterium_masse: bool | None = None
    bewertung: str = ""
    warnungen: list = field(default_factory=list)
    fehler: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fehler

    @property
    def nachweis_erfuellt(self) -> bool | None:
        if self.fehler:
            return None
        if self.fall == "keine_kondensation":
            return True
        teil = [k for k in (self.kriterium_verdunstung, self.kriterium_masse)
                if k is not None]
        return all(teil) if teil else None


def berechne(
    layers: list,
    materialien: dict | None = None,
    katalogwerte: Katalogwerte | None = None,
    rb_tau: Randbedingungen | None = None,
    rb_verdunstung: Randbedingungen | None = None,
    element_type: str | None = "wall",
    adjacency_type: str | None = "exterior",
) -> Ergebnis:
    """
    Tauwassernachweis fuer einen Schichtaufbau.

    layers ist von INNEN nach AUSSEN geordnet — dieselbe Richtung, in der die
    Norm den Temperatur- und Druckverlauf auftraegt. Eine falsche Reihenfolge
    liefert ein klaglos falsches Ergebnis, deshalb ist sie Teil des Vertrags
    und wird nicht geraten.
    """
    erg = Ergebnis()
    materialien = lade_materialien() if materialien is None else materialien
    kw = lade_randbedingungen() if katalogwerte is None else katalogwerte
    if not kw.ok:
        erg.fehler.extend(kw.fehler)
        return erg

    standard_tau, standard_verd = waehle_perioden(kw)
    rb_tau = rb_tau or standard_tau
    rb_verdunstung = rb_verdunstung or standard_verd
    if rb_tau is None or rb_verdunstung is None:
        erg.fehler.append("Tau- oder Verdunstungsperiode fehlt im Katalog "
                          "moisture_conditions")
        return erg

    luftschichten = lade_luftschichten()
    feld_tau, fehler = baue_feld(layers, materialien, rb_tau, luftschichten)
    if fehler:
        erg.fehler.extend(fehler)
        return erg

    erg.r_total = feld_tau.r_total
    erg.sd_total = feld_tau.sd_total
    erg.u_value = round(1.0 / feld_tau.r_total, 4)

    # Oberflaechentauwasser liegt ausserhalb des Periodenbilanzverfahrens.
    if feld_tau.p_i > feld_tau.p_sat[0]:
        erg.warnungen.append(
            f"p_i = {feld_tau.p_i:.0f} Pa liegt ueber dem Saettigungsdruck der "
            f"raumseitigen Oberflaeche ({feld_tau.p_sat[0]:.0f} Pa) — es faellt "
            f"Tauwasser AN der Oberflaeche aus. Das bewertet Abschnitt 4.3 "
            f"(Schimmelkriterium fRsi), nicht dieses Verfahren."
        )

    ebenen = tauebenen(feld_tau)
    erg.fall, ebenen = klassifiziere(ebenen)
    erg.ebenen = ebenen
    erg.ebenen_sd = [feld_tau.sd[i] for i in ebenen]
    erg.ebenen_theta = [feld_tau.theta[i] for i in ebenen]
    erg.p_c = [feld_tau.p_sat[i] for i in ebenen]

    if erg.fall == "keine_kondensation":
        erg.bewertung = ("Kein Tauwasserausfall — der Dampfdruckverlauf bleibt "
                         "durchgehend unter der Saettigungskurve.")
        return erg
    if erg.fall == "nicht_abgedeckt":
        erg.fehler.append(
            f"{len(ebenen)} getrennte Tauebenen. Anhang A gibt Gleichungen nur "
            f"fuer eine Ebene (A.3), zwei Ebenen (A.5) und einen "
            f"zusammenhaengenden Bereich (A.10) an — fuer diesen Aufbau liefert "
            f"das Periodenbilanzverfahren kein Ergebnis. Instationaeres "
            f"Verfahren nach DIN EN 15026 anwenden."
        )
        return erg

    # --- Tauperiode --------------------------------------------------------
    tau = tauperiode(feld_tau, erg.fall, ebenen, kw.delta_0, rb_tau.dauer_s)
    erg.m_c = tau["m_c"]
    erg.m_c_gesamt = tau["m_c_gesamt"]
    if any(m < 0 for m in erg.m_c):
        erg.warnungen.append(
            "Negative Tauwassermasse in mindestens einer Ebene — die Glaser-"
            "Konstruktion und die Massenbilanz widersprechen sich. Eingabe "
            "pruefen."
        )

    # --- Verdunstungsperiode ----------------------------------------------
    feld_verd, fehler = baue_feld(layers, materialien, rb_verdunstung,
                                  luftschichten)
    if fehler:
        erg.fehler.extend(fehler)
        return erg
    verd = verdunstungsperiode(feld_verd, erg.fall, ebenen, erg.m_c,
                               kw.delta_0, rb_verdunstung.dauer_s)
    erg.m_ev = verd["m_ev"]
    erg.m_ev_gesamt = verd["m_ev_gesamt"]
    erg.warnungen.extend(verd.get("warnungen", []))

    # --- Bewertung 5.2.2 / 5.3 --------------------------------------------
    erg.kriterium_verdunstung = erg.m_ev_gesamt >= erg.m_c_gesamt

    massenkriterium = (element_type in MASSENKRITERIUM_ELEMENT_TYPEN
                       and adjacency_type in MASSENKRITERIUM_ANGRENZUNGEN)
    if massenkriterium:
        erg.kriterium_masse = True
        for nr, knoten in enumerate(ebenen if erg.fall != "d" else [ebenen[0]]):
            # An welcher Beruehrungsflaeche liegt die Ebene? Knoten k trennt
            # Schicht k (innen davon) von Schicht k+1.
            angrenzend = [s for s in (layers[knoten - 1] if knoten >= 1 else None,
                                      layers[knoten] if knoten < len(layers) else None)
                          if s is not None]
            kapillar = [kapillar_wasseraufnahmefaehig(
                s, materialien, kw.w_capillary_threshold) for s in angrenzend]
            if None in kapillar:
                grenze = kw.m_c_max_non_capillary
                erg.warnungen.append(
                    f"Tauebene {nr + 1}: kapillare Wasseraufnahmefaehigkeit der "
                    f"angrenzenden Schichten unbekannt (kein w-Wert, kein "
                    f"capillary_active) — konservativ mit dem strengeren "
                    f"Grenzwert {grenze} kg/m2 bewertet."
                )
            elif all(kapillar):
                grenze = kw.m_c_max_general
            else:
                grenze = kw.m_c_max_non_capillary
            erg.grenzwerte.append(grenze)
            masse = erg.m_c[nr] if nr < len(erg.m_c) else erg.m_c_gesamt
            if masse > grenze:
                erg.kriterium_masse = False
        if erg.m_c_gesamt > kw.m_c_max_general:
            erg.kriterium_masse = False
    else:
        erg.warnungen.append(
            f"Massenkriterium nach 5.2.2 nicht angewendet: es gilt fuer Daecher "
            f"und Waende gegen Aussenluft sowie Decken unter nicht ausgebauten "
            f"Dachraeumen, hier element_type='{element_type}', "
            f"adjacency_type='{adjacency_type}'. Geprueft wird nur, ob das "
            f"Tauwasser wieder abgegeben wird."
        )

    teile = []
    teile.append(
        f"Tauwasser wird {'vollstaendig' if erg.kriterium_verdunstung else 'NICHT'} "
        f"abgegeben (M_ev = {erg.m_ev_gesamt:.3f} gegen M_c = {erg.m_c_gesamt:.3f} kg/m2)"
    )
    if erg.kriterium_masse is not None:
        teile.append(
            f"Massenkriterium {'erfuellt' if erg.kriterium_masse else 'VERLETZT'}"
        )
    erg.bewertung = "; ".join(teile) + "."
    return erg


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _layers_innen_nach_aussen(konstruktion: dict) -> tuple[list, str | None]:
    """
    Bringt das Altformat catalog/constructions.json in die Reihenfolge
    innen -> aussen. Dort sind die Schichten ueber das Feld 'position'
    (interior/core/exterior) gekennzeichnet und in der Regel aussen zuerst
    gelistet.
    """
    layers = konstruktion.get("layers") or []
    if not layers:
        return [], "Konstruktion hat kein layers[]"
    positionen = [s.get("position") for s in layers]
    if positionen[0] == "exterior" and positionen[-1] == "interior":
        return list(reversed(layers)), None
    if positionen[0] == "interior" and positionen[-1] == "exterior":
        return layers, None
    return layers, ("Reihenfolge der Schichten nicht aus 'position' ableitbar — "
                    "angenommen: innen nach aussen")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Tauwassernachweis nach DIN 4108-3 (Periodenbilanzverfahren)")
    p.add_argument("--construction", help="ID aus catalog/constructions.json")
    p.add_argument("--aufbau", help="JSON-Datei mit layers[] von innen nach aussen")
    p.add_argument("--element-type", default="wall")
    p.add_argument("--adjacency", default="exterior")
    args = p.parse_args()

    hinweis = None
    if args.aufbau:
        daten = json.loads(Path(args.aufbau).read_text(encoding="utf-8"))
        layers = daten.get("layers", daten if isinstance(daten, list) else [])
        name = args.aufbau
    elif args.construction:
        roh = json.loads(
            (REPO / "catalog" / "constructions.json").read_text(encoding="utf-8"))
        treffer = next((c for c in roh["constructions"]
                        if c["id"] == args.construction), None)
        if treffer is None:
            print(f"Konstruktion '{args.construction}' nicht gefunden",
                  file=sys.stderr)
            return 2
        layers, hinweis = _layers_innen_nach_aussen(treffer)
        name = f"{treffer['id']} ({treffer.get('name_de', '')})"
    else:
        p.print_help()
        return 2

    erg = berechne(layers, element_type=args.element_type,
                   adjacency_type=args.adjacency)

    print(f"Aufbau:       {name}")
    if hinweis:
        print(f"HINWEIS: {hinweis}")
    if erg.r_total:
        print(f"R_T:          {erg.r_total:.4f} (m2K)/W     "
              f"U = {erg.u_value} W/(m2K)")
        print(f"Summe s_d:    {erg.sd_total:.3f} m")
    print(f"Fall:         {erg.fall}")
    for i, (sd, th, pc) in enumerate(zip(erg.ebenen_sd, erg.ebenen_theta,
                                         erg.p_c), start=1):
        print(f"  Tauebene {i}: s_d = {sd:.3f} m, theta = {th:.2f} Grad C, "
              f"p_c = {pc:.1f} Pa")
    if erg.m_c:
        print(f"M_c:          {'  '.join(f'{m:.3f}' for m in erg.m_c)} "
              f"-> gesamt {erg.m_c_gesamt:.3f} kg/m2")
        print(f"M_ev:         {'  '.join(f'{m:.3f}' for m in erg.m_ev)} "
              f"-> gesamt {erg.m_ev_gesamt:.3f} kg/m2")
    if erg.bewertung:
        print(f"Bewertung:    {erg.bewertung}")
    for w in erg.warnungen:
        print(f"WARNUNG: {w}")
    for f in erg.fehler:
        print(f"FEHLER:  {f}")
    if not erg.ok:
        return 1
    return 0 if erg.nachweis_erfuellt else 1


if __name__ == "__main__":
    raise SystemExit(main())
