#!/usr/bin/env python3
"""
test_tauwasser.py — Tests fuer den Tauwassernachweis nach DIN 4108-3.

Der Kern ist das Beispiel aus Anhang B der Norm: ein realer Aufbau mit zwei
Tauebenen, dessen Zwischen- und Endergebnisse in der Norm abgedruckt sind. Ein
Rechenkern, der dieses Beispiel nicht trifft, ist nicht einsatzfaehig — egal wie
gruen alle Einzeltests sind.

Die uebrigen Sollwerte sind so gewaehlt, dass sie sich auf Papier nachrechnen
lassen. Ein Test, dessen Erwartungswert aus demselben Code stammt, den er
prueft, testet nichts.

Aufruf:
    python3 tools/test_tauwasser.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tauwasser import (  # noqa: E402
    Randbedingungen,
    baue_feld,
    berechne,
    klassifiziere,
    lade_randbedingungen,
    saettigungsdampfdruck,
    taupunkttemperatur,
    tauebenen,
)

# --- Anhang B: Aussenwand, Schichten von INNEN nach AUSSEN -----------------
# (Dicke [m], mu [-], lambda [W/(mK)])
#   1 Gipskarton     0,0125 /   8 / 0,210
#   2 Daemmstoff     0,0800 /   2 / 0,040
#   3 Vollziegel     0,3000 /  10 / 0,790
#   4 EPS            0,0600 /  25 / 0,035
#   5 Kunstharzputz  0,0080 / 150 / 1,000
ANHANG_B = [
    {"name": "Gipskarton", "thickness_m": 0.0125, "mu": 8, "lambda": 0.210},
    {"name": "Daemmstoff", "thickness_m": 0.0800, "mu": 2, "lambda": 0.040},
    {"name": "Vollziegel", "thickness_m": 0.3000, "mu": 10, "lambda": 0.790},
    {"name": "EPS", "thickness_m": 0.0600, "mu": 25, "lambda": 0.035},
    {"name": "Kunstharzputz", "thickness_m": 0.0080, "mu": 150, "lambda": 1.000},
]

class _FesteDruecke(Randbedingungen):
    """
    Randbedingung mit direkt vorgegebenem p_i/p_e.

    Anhang B nennt p_i = 1168 Pa und p_e = 321 Pa, nicht die relativen Feuchten.
    Statt phi rueckzurechnen (und dabei eine Rundung einzuschleppen, die das
    Beispiel nicht hat) werden die Druecke hier direkt gesetzt.
    """
    def __init__(self, p_i: float, p_e: float, **kwargs):
        super().__init__(**kwargs)
        self._p_i, self._p_e = p_i, p_e

    @property
    def p_i(self) -> float:
        return self._p_i

    @property
    def p_e(self) -> float:
        return self._p_e


# Randbedingungen des Beispiels. Bewusst explizit im Test und nicht aus dem
# Katalog gezogen: der Test soll den RECHENKERN pruefen, nicht das Overlay.
# Dass dieselben Werte auch im Overlay stehen, prueft Block 12.
RB_TAU_B = _FesteDruecke(1168.0, 321.0, code="anhang_b_tau", theta_i=20.0,
                         phi_i=0.5, theta_e=-5.0, phi_e=0.8, duration_days=90,
                         rsi=0.25, rse=0.04)
RB_VERD_B = Randbedingungen(code="anhang_b_verdunstung", theta_i=12.0, phi_i=0.70,
                            theta_e=12.0, phi_e=0.70, duration_days=90,
                            rsi=0.25, rse=0.04)


def nah(a, b, toleranz: float = 0.001) -> bool:
    return a is not None and abs(a - b) < toleranz


def relativ_nah(a, b, prozent: float = 1.0) -> bool:
    return a is not None and abs(a - b) <= abs(b) * prozent / 100.0


def main() -> int:
    fehler = 0

    def pruefe(name: str, bedingung: bool, detail: str = "") -> None:
        nonlocal fehler
        fehler += 0 if bedingung else 1
        print(f"{name:58} {'PASS' if bedingung else 'FAIL'}  {detail}")

    # --- 1. Saettigungsdampfdruck C.15/C.16 --------------------------------
    # 610,5 * exp(17,269*20/(237,3+20)) = 610,5 * exp(1,342325) = 2336,95 Pa.
    # Bewusst NICHT 2339 Pa: das ist der Wert der Magnus-Formel mit anderen
    # Beiwerten, der in vielen Tabellenwerken steht. Gerechnet wird, was C.15
    # vorgibt — sonst passt das Ergebnis nicht mehr zum Rest der Norm.
    pruefe("p_sat(20) = 2336,95 Pa (C.15)",
           nah(saettigungsdampfdruck(20.0), 2336.95, 0.05),
           f"{saettigungsdampfdruck(20.0):.2f}")
    # 610,5 * exp(21,875*(-5)/(265,5-5)) = 610,5 * exp(-0,419865) = 401,18 Pa.
    # Gegenprobe zu Anhang B: 0,80 * 401,18 = 320,9 Pa, dort mit 321 Pa
    # angegeben.
    pruefe("p_sat(-5) = 401,18 Pa (C.16)",
           nah(saettigungsdampfdruck(-5.0), 401.18, 0.05),
           f"{saettigungsdampfdruck(-5.0):.2f}")
    pruefe("p_sat(0) stetig", nah(saettigungsdampfdruck(0.0), 610.5, 0.001),
           f"{saettigungsdampfdruck(0.0):.2f}")

    # --- 2. Taupunkt ist die exakte Umkehrung ------------------------------
    # Mit dem gedruckten Beiwert 265,6 in C.18 waere dieser Test bei -15 Grad C
    # um rund 0,006 K daneben. Implementiert ist 265,5 (siehe Modul-Kommentar).
    schlimmster = max(abs(taupunkttemperatur(saettigungsdampfdruck(t)) - t)
                      for t in (-15.0, -5.0, -0.1, 0.0, 5.0, 12.0, 20.0, 30.0))
    pruefe("Taupunkt invertiert p_sat exakt (C.17/C.18)", schlimmster < 1e-9,
           f"groesste Abweichung {schlimmster:.2e} K")
    pruefe("Taupunkt(1168 Pa) = 9,26 Grad C",
           nah(taupunkttemperatur(1168.0), 9.26, 0.01),
           f"{taupunkttemperatur(1168.0):.3f}")

    # --- 3. Anhang B: Feld ------------------------------------------------
    # R = 0,059524 + 2,000000 + 0,379747 + 1,714286 + 0,008000 = 4,161557
    # R_T = 0,25 + 4,161557 + 0,04 = 4,451557 -> gerundet 4,452
    # s_d = 0,1 + 0,16 + 3,0 + 1,5 + 1,2 = 5,96
    # U = 1/4,451557 = 0,2246 -> gerundet 0,22
    feld, feld_fehler = baue_feld(ANHANG_B, {}, RB_TAU_B)
    pruefe("Anhang B: Feld rechenbar", not feld_fehler, str(feld_fehler))
    pruefe("Anhang B: R_T = 4,452 (m2K)/W", nah(feld.r_total, 4.452, 0.001),
           f"{feld.r_total:.4f}")
    pruefe("Anhang B: Summe s_d = 5,96 m", nah(feld.sd_total, 5.96, 0.001),
           f"{feld.sd_total:.3f}")
    pruefe("Anhang B: U = 0,22 W/(m2K)", nah(round(1 / feld.r_total, 2), 0.22),
           f"{1 / feld.r_total:.4f}")

    # Temperaturverteilung C.4: q = 25 / 4,451557 = 5,6160 W/m2
    #   theta_si = 20 - 5,6160*0,25          = 18,596
    #   nach Schicht 2 (s_d = 0,26): 20 - 5,6160*2,309524 = 7,030
    #   nach Schicht 4 (s_d = 4,76): 20 - 5,6160*4,403557 = -4,730
    pruefe("Anhang B: theta_si = 18,60 Grad C", nah(feld.theta[0], 18.596, 0.01),
           f"{feld.theta[0]:.3f}")
    pruefe("Anhang B: theta bei s_d 0,26 = 7,03 Grad C",
           nah(feld.theta[2], 7.030, 0.01), f"{feld.theta[2]:.3f}")
    pruefe("Anhang B: theta bei s_d 4,76 = -4,73 Grad C",
           nah(feld.theta[4], -4.730, 0.01), f"{feld.theta[4]:.3f}")

    # --- 4. Anhang B: Glaser-Konstruktion ---------------------------------
    ebenen = tauebenen(feld)
    fall, ebenen = klassifiziere(ebenen)
    pruefe("Anhang B: Fall c (zwei getrennte Tauebenen)", fall == "c",
           f"{fall}, Knoten {ebenen}")
    pruefe("Anhang B: Tauebenen bei s_d 0,26 und 4,76",
           [round(feld.sd[i], 3) for i in ebenen] == [0.26, 4.76],
           str([feld.sd[i] for i in ebenen]))

    # --- 5. Anhang B: Massenbilanz (der Abnahmetest) ----------------------
    #
    # TOLERANZ 1 %, und woher die Abweichung kommt:
    #   Norm-Beispiel:  M_c1 = 0,783   M_c gesamt = 0,872 kg/m2
    #   dieses Modul:   M_c1 = 0,780   M_c gesamt = 0,869 kg/m2   (-0,3 %)
    #
    # Ursache ist p_c2, der Saettigungsdruck in der aeusseren Tauebene: das
    # gedruckte Beispiel rechnet mit 409 Pa, dieses Modul mit 410,5 Pa. Das
    # entspricht einem Temperaturunterschied von rund 0,04 K in dieser Ebene
    # (-4,730 gegen -4,775 Grad C) und ruehrt daher, dass das Normbeispiel die
    # Zwischenwerte der Temperatur- und Drucktabelle gerundet weiterverwendet,
    # waehrend hier durchgehend ungerundet gerechnet wird. Bemerkenswert: 409 Pa
    # ist exakt der Saettigungsdruck der AUSSENOBERFLAECHE (-4,775 Grad C) —
    # die gedruckte Tabelle fuehrt fuer die letzten beiden Knoten offenbar
    # denselben gerundeten Wert.
    #
    # Es wird bewusst NICHTS hingebogen, um 0,783 zu treffen: die Formeln stehen
    # so in A.5 bis A.9, und die Eingangswerte stehen so in Anhang B. Eine
    # Konstante, die die Differenz schliesst, waere eine Luege ueber die
    # Genauigkeit des Verfahrens.
    erg = berechne(ANHANG_B, materialien={}, rb_tau=RB_TAU_B,
                   rb_verdunstung=RB_VERD_B, element_type="wall",
                   adjacency_type="exterior")
    pruefe("Anhang B: Nachweis rechenbar", erg.ok, str(erg.fehler))
    pruefe("Anhang B: M_c1 = 0,783 kg/m2 (1 %)",
           relativ_nah(erg.m_c[0], 0.783, 1.0), f"{erg.m_c[0]:.4f}")
    pruefe("Anhang B: M_c gesamt = 0,872 kg/m2 (1 %)",
           relativ_nah(erg.m_c_gesamt, 0.872, 1.0), f"{erg.m_c_gesamt:.4f}")
    pruefe("Anhang B: M_c2 = M_c - M_c1",
           nah(erg.m_c[0] + erg.m_c[1], erg.m_c_gesamt, 1e-9),
           f"{erg.m_c[1]:.4f}")

    # --- 6. Anhang B: Verdunstungsperiode ---------------------------------
    # theta_i = theta_e = 12 Grad C -> kein Gefaelle, p_c = p_sat(12) = 1402,3 Pa
    # in BEIDEN Ebenen; p_i = p_e = 0,70 * 1402,3 = 981,6 Pa.
    #   g_ev1 = 2e-10 * (1402,3-981,6)/0,26  = 3,2362e-7 kg/(m2s)
    #   g_ev2 = 2e-10 * (1402,3-981,6)/1,20  = 7,0117e-8 kg/(m2s)
    #   t_ev1 = 0,7798/3,2362e-7 = 2,410e6 s = 27,9 d
    #   t_ev2 = 0,0889/7,0117e-8 = 1,267e6 s = 14,7 d  -> Ebene 2 zuerst trocken
    # Beide unter 90 d, also A.24 bis A.26. M_ev2 = M_c2 (mehr war nicht da).
    pruefe("Anhang B: M_ev2 = M_c2 (Ebene 2 trocknet vorzeitig aus, A.24)",
           nah(erg.m_ev[1], erg.m_c[1], 1e-9),
           f"M_ev2={erg.m_ev[1]:.4f} M_c2={erg.m_c[1]:.4f}")
    pruefe("Anhang B: M_ev1 = 2,61 kg/m2 (A.25)",
           relativ_nah(erg.m_ev[0], 2.612, 1.0), f"{erg.m_ev[0]:.4f}")
    pruefe("Anhang B: Tauwasser wird vollstaendig abgegeben (M_ev >= M_c)",
           erg.kriterium_verdunstung is True,
           f"M_ev={erg.m_ev_gesamt:.3f} >= M_c={erg.m_c_gesamt:.3f}")
    # Der Daemmstoff (mu 2, lambda 0,04) ist Mineralwolle, also nicht kapillar
    # wasseraufnahmefaehig — ohne w-Wert greift der strengere Grenzwert. 0,78
    # kg/m2 liegen darueber, das Massenkriterium ist verletzt. Der Aufbau ist
    # im Normbeispiel ein Rechenbeispiel, kein Musterbauteil.
    pruefe("Anhang B: Massenkriterium verletzt (M_c1 > 0,5 kg/m2)",
           erg.kriterium_masse is False, f"Grenzwerte {erg.grenzwerte}")
    pruefe("Anhang B: Gesamtnachweis damit nicht erfuellt",
           erg.nachweis_erfuellt is False, erg.bewertung)

    # --- 7. Fall b: eine Tauebene, von Hand nachgerechnet ------------------
    # Zwei Schichten, Grenze dazwischen ist die einzige Tauebene.
    #   1: d 0,02  mu 100  lambda 1,0  -> R 0,02   s_d 2,0
    #   2: d 0,20  mu 1    lambda 0,04 -> R 5,00   s_d 0,2
    # R_T = 0,25 + 5,02 + 0,04 = 5,31 ; q = 25/5,31 = 4,70810
    # theta an der Grenze = 20 - 4,70810*(0,25+0,02) = 18,7288 Grad C
    #   -> p_sat = 2160,0 Pa ... liegt weit ueber p_i, also KEIN Tauwasser.
    # Deshalb umgekehrt aufgebaut: Dampfbremse AUSSEN.
    #   1: d 0,20  mu 1    lambda 0,04 -> R 5,00   s_d 0,2
    #   2: d 0,02  mu 100  lambda 1,0  -> R 0,02   s_d 2,0
    # theta an der Grenze = 20 - 4,70810*(0,25+5,00) = -4,7175 Grad C
    #   p_sat = 610,5*exp(21,875*(-4,7175)/(265,5-4,7175)) = 410,9 Pa
    #   s_dc = 0,2 ; s_dT = 2,2
    #   g_c = 2e-10*[(1168-410,9)/0,2 - (410,9-321)/2,0]
    #       = 2e-10*[3785,5 - 44,95] = 7,4811e-7 kg/(m2s)
    #   M_c = 7,4811e-7 * 7,776e6 s = 5,817 kg/m2
    fall_b = [
        {"thickness_m": 0.20, "mu": 1, "lambda": 0.04, "capillary_active": False},
        {"thickness_m": 0.02, "mu": 100, "lambda": 1.0, "capillary_active": True},
    ]
    erg_b = berechne(fall_b, materialien={}, rb_tau=RB_TAU_B,
                     rb_verdunstung=RB_VERD_B)
    pruefe("Fall b: erkannt", erg_b.fall == "b", erg_b.fall)
    pruefe("Fall b: p_c = 410,9 Pa", nah(erg_b.p_c[0], 410.9, 0.5),
           f"{erg_b.p_c[0]:.2f}")
    pruefe("Fall b: M_c = 5,817 kg/m2 (A.3/A.4)",
           relativ_nah(erg_b.m_c_gesamt, 5.817, 0.5), f"{erg_b.m_c_gesamt:.4f}")
    # Verdunstung, A.12/A.13: p_c = p_sat(12) = 1402,3 ; p_i = p_e = 981,6
    #   g_ev = 2e-10*[(1402,3-981,6)/0,2 + (1402,3-981,6)/2,0]
    #        = 2e-10*[2103,5 + 210,35] = 4,6277e-7
    #   M_ev = 4,6277e-7 * 7,776e6 = 3,598 kg/m2  -> kleiner als M_c
    pruefe("Fall b: M_ev = 3,598 kg/m2 (A.12/A.13, PLUS statt Minus)",
           relativ_nah(erg_b.m_ev_gesamt, 3.598, 0.5),
           f"{erg_b.m_ev_gesamt:.4f}")
    pruefe("Fall b: Verdunstungskriterium verletzt (M_ev < M_c)",
           erg_b.kriterium_verdunstung is False,
           f"{erg_b.m_ev_gesamt:.3f} < {erg_b.m_c_gesamt:.3f}")

    # --- 8. Kein Tauwasser: Dampfbremse innen ------------------------------
    innen_gebremst = [
        {"thickness_m": 0.02, "mu": 1000, "lambda": 1.0},
        {"thickness_m": 0.20, "mu": 1, "lambda": 0.04},
    ]
    erg_ok = berechne(innen_gebremst, materialien={}, rb_tau=RB_TAU_B,
                      rb_verdunstung=RB_VERD_B)
    pruefe("Dampfbremse innen: kein Tauwasser",
           erg_ok.fall == "keine_kondensation" and erg_ok.m_c_gesamt == 0.0,
           erg_ok.fall)
    pruefe("Dampfbremse innen: Nachweis erfuellt",
           erg_ok.nachweis_erfuellt is True, erg_ok.bewertung)

    # --- 9. Fall d: zusammenhaengender Tauwasserbereich --------------------
    # Ein Bereich entsteht, wenn ZWEI BENACHBARTE Knoten auf der unteren Huelle
    # liegen — dann folgt der Dampfdruckverlauf der Saettigungslinie ueber eine
    # ganze Schicht. Dafuer muss die mittlere Schicht flacher abfallen als die
    # innere und steiler als die aeussere (bezogen auf s_d).
    #   1 Daemmung  0,10 / mu 1  / lambda 0,04 -> R 2,50  s_d 0,10
    #   2 Daemmung  0,04 / mu 2  / lambda 0,04 -> R 1,00  s_d 0,08
    #   3 Ziegel    0,24 / mu 10 / lambda 0,80 -> R 0,30  s_d 2,40
    # R_T = 0,25 + 3,80 + 0,04 = 4,09 ; q = 25/4,09 = 6,11247 W/m2
    #   theta(s_d 0,10) = 20 - 6,11247*2,75 = 3,1907 -> p_sat = 767,70 Pa
    #   theta(s_d 0,18) = 20 - 6,11247*3,75 = -2,9218 -> p_sat = 478,60 Pa
    # A.10/A.11:
    #   g_c = 2e-10*[(1168-767,70)/0,10 - (478,60-321)/(2,58-0,18)]
    #       = 2e-10*[4003,0 - 65,67] = 7,8747e-7 kg/(m2s)
    #   M_c = 7,8747e-7 * 7,776e6 s = 6,123 kg/m2
    fall_d = [
        {"thickness_m": 0.10, "mu": 1, "lambda": 0.04},
        {"thickness_m": 0.04, "mu": 2, "lambda": 0.04},
        {"thickness_m": 0.24, "mu": 10, "lambda": 0.80},
    ]
    erg_d = berechne(fall_d, materialien={}, rb_tau=RB_TAU_B,
                     rb_verdunstung=RB_VERD_B)
    pruefe("Fall d: Bereich statt zwei Ebenen erkannt", erg_d.fall == "d",
           f"{erg_d.fall}, s_d {erg_d.ebenen_sd}")
    pruefe("Fall d: Bereichsraender s_d 0,10 und 0,18",
           [round(s, 3) for s in erg_d.ebenen_sd] == [0.10, 0.18],
           str(erg_d.ebenen_sd))
    pruefe("Fall d: M_c = 6,123 kg/m2 (A.10/A.11)",
           len(erg_d.m_c) == 1 and relativ_nah(erg_d.m_c_gesamt, 6.123, 0.5),
           f"M_c={erg_d.m_c_gesamt:.4f}")
    # A.27/A.28: die Masse sitzt rechnerisch in der Bereichsmitte
    # s_dcm = 0,10 + 0,5*(0,18-0,10) = 0,14. In der Verdunstungsperiode ist
    # ueberall 12 Grad C, also p_c = p_sat(12) = 1401,81 Pa, p_i = p_e = 981,27:
    #   g_ev = 2e-10*[(1401,81-981,27)/0,14 + (1401,81-981,27)/(2,58-0,14)]
    #        = 2e-10*[3003,9 + 172,35] = 6,3525e-7 kg/(m2s)
    #   M_ev = 6,3525e-7 * 7,776e6 s = 4,940 kg/m2
    pruefe("Fall d: M_ev = 4,940 kg/m2 (A.27/A.28)",
           len(erg_d.m_ev) == 1 and relativ_nah(erg_d.m_ev_gesamt, 4.940, 0.5),
           f"M_ev={erg_d.m_ev_gesamt:.4f}")

    # --- 10. Klassifizierung isoliert --------------------------------------
    pruefe("Klassifizierung: [] -> keine_kondensation",
           klassifiziere([]) == ("keine_kondensation", []))
    pruefe("Klassifizierung: [3] -> b", klassifiziere([3]) == ("b", [3]))
    pruefe("Klassifizierung: [2,5] -> c", klassifiziere([2, 5]) == ("c", [2, 5]))
    pruefe("Klassifizierung: [2,3] -> d (benachbart)",
           klassifiziere([2, 3]) == ("d", [2, 3]))
    pruefe("Klassifizierung: [2,3,4] -> d ueber den ganzen Lauf",
           klassifiziere([2, 3, 4]) == ("d", [2, 4]))
    pruefe("Klassifizierung: [1,3,6] -> nicht abgedeckt",
           klassifiziere([1, 3, 6])[0] == "nicht_abgedeckt")

    # --- 11. Fehlerfaelle melden statt still rechnen -----------------------
    erg_f = berechne([{"thickness_m": 0.2, "lambda": 0.04}], materialien={},
                     rb_tau=RB_TAU_B, rb_verdunstung=RB_VERD_B)
    pruefe("Schicht ohne mu -> Fehler statt Annahme",
           not erg_f.ok and any("mu" in f for f in erg_f.fehler),
           str(erg_f.fehler[:1]))

    # --- 12. Overlay: Randbedingungen kommen aus dem Katalog ---------------
    kw = lade_randbedingungen()
    pruefe("Katalog moisture_conditions vollstaendig geladen", kw.ok,
           str(kw.fehler[:1]))
    if kw.ok:
        tau = next(r for r in kw.perioden.values()
                   if r.code.startswith("tauperiode"))
        verd = next(r for r in kw.perioden.values()
                    if r.code.startswith("verdunstungsperiode"))
        # Gegenprobe zum Normbeispiel: p_i = 0,50*p_sat(20) = 1169,7 Pa und
        # p_e = 0,80*p_sat(-5) = 321,4 Pa. Anhang B nennt 1168 und 321 — die
        # Differenz von 1,7 Pa ist die Rundung der abgedruckten Tabellenwerte.
        pruefe("Overlay Tauperiode: p_i ~ 1168 Pa (0,5 %)",
               relativ_nah(tau.p_i, 1168.0, 0.5), f"{tau.p_i:.1f}")
        pruefe("Overlay Tauperiode: p_e ~ 321 Pa (0,5 %)",
               relativ_nah(tau.p_e, 321.0, 0.5), f"{tau.p_e:.1f}")
        pruefe("Overlay Verdunstung: kein Temperaturgefaelle (A.14-A.26)",
               verd.theta_i == verd.theta_e, f"{verd.theta_i}/{verd.theta_e}")
        pruefe("Overlay: delta_0 in der Groessenordnung 1e-10",
               kw.delta_0 is not None and 1e-10 <= kw.delta_0 <= 3e-10,
               str(kw.delta_0))
        # Anhang B mit den Katalog-Randbedingungen statt den gerundeten
        # Druecken: das Ergebnis darf sich nur im Promillebereich verschieben.
        erg_kat = berechne(ANHANG_B, materialien={}, element_type="wall",
                           adjacency_type="exterior")
        pruefe("Anhang B mit Katalog-Randbedingungen: M_c weiterhin ~0,87 (1 %)",
               relativ_nah(erg_kat.m_c_gesamt, 0.872, 1.0),
               f"{erg_kat.m_c_gesamt:.4f}")

    # --- 13. Massenkriterium folgt der Bauteilsituation --------------------
    erg_innen = berechne(fall_b, materialien={}, rb_tau=RB_TAU_B,
                         rb_verdunstung=RB_VERD_B, element_type="wall",
                         adjacency_type="same_zone")
    pruefe("Innenwand: Massenkriterium nach 5.2.2 nicht angewendet",
           erg_innen.kriterium_masse is None,
           str(erg_innen.kriterium_masse))

    print()
    print(f"{'ALLE TESTS BESTANDEN' if fehler == 0 else str(fehler) + ' TEST(S) FEHLGESCHLAGEN'}")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
