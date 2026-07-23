#!/usr/bin/env python3
"""
test_ventilated_air_layers.py — Tests fuer belueftete Luftschichten nach
DIN EN ISO 6946, Abschnitt 6.9.

Der schaerfste Test ist die Stetigkeit: Gleichung (11) muss an ihren Raendern
exakt in die Nachbarfaelle uebergehen. Ein Vorzeichen- oder Schwellenfehler
faellt dort sofort auf, waehrend er in der Mitte des Bereichs unauffaellig
bleibt.

Aufruf:
    python3 tools/test_ventilated_air_layers.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from u_value import lade_katalog  # noqa: E402
from ventilated_air_layers import (  # noqa: E402
    RUHEND,
    SCHWACH,
    STARK,
    berechne,
    einstufung,
    lade_belueftungswerte,
)

WIDERSTAENDE = lade_katalog("surface_resistances")

# Zweischalige Aussenwand, von INNEN nach AUSSEN. Die Luftschicht bekommt einen
# expliziten r_value, damit der Test nicht von den geschuetzten Werten der
# Tabelle 8 abhaengt — geprueft wird die Verknuepfungslogik von 6.9, nicht die
# Tabelle.
#   0 Innenputz     0,015 / lambda 0,70 -> R = 0,0214286
#   1 Daemmung      0,100 / lambda 0,04 -> R = 2,5000000
#   2 Luftschicht   r_value 0,18        -> R = 0,1800000
#   3 Vorsatzschale 0,115 / lambda 0,96 -> R = 0,1197917
AUFBAU = [
    {"thickness_m": 0.015, "lambda": 0.70},
    {"thickness_m": 0.100, "lambda": 0.04},
    {"air_layer": True, "thickness_m": 0.04, "r_value": 0.18},
    {"thickness_m": 0.115, "lambda": 0.96},
]
LUFTSCHICHT = 2

# Rsi = 0,13 und Rse = 0,04 (exterior_horizontal, Tabelle 7).
#   R_tot;nve = 0,13 + 0,0214286 + 2,5 + 0,18 + 0,1197917 + 0,04 = 2,9912203
# 6.9.4: Luftschicht und Vorsatzschale entfallen, Rse wird zum ruhenden Wert
# (= Rsi derselben Waermestromrichtung, 0,13):
#   R_tot;ve  = 0,13 + 0,0214286 + 2,5 + 0,13                    = 2,7814286
R_NVE = 2.9912203
R_VE = 2.7814286


def nah(a, b, toleranz: float = 1e-6) -> bool:
    return a is not None and abs(a - b) < toleranz


def main() -> int:
    fehler = 0

    def pruefe(name: str, bedingung: bool, detail: str = "") -> None:
        nonlocal fehler
        fehler += 0 if bedingung else 1
        print(f"{name:58} {'PASS' if bedingung else 'FAIL'}  {detail}")

    bw = lade_belueftungswerte()
    pruefe("Katalog air_layers: Schwellen und Flag geladen", bw.ok,
           str(bw.fehler[:1]))
    if not bw.ok:
        print("\nOhne Werte-Overlay keine weiteren Tests.")
        return 1
    pruefe("Schwellen 500 / 1500, Divisor 1000 aus dem Overlay",
           (bw.schwelle_ruhend, bw.schwelle_stark, bw.divisor) == (500, 1500, 1000),
           f"{bw.schwelle_ruhend}/{bw.schwelle_stark}/{bw.divisor}")

    # --- 1. Einstufung, 6.9.2 / 6.9.3 / 6.9.4 -----------------------------
    pruefe("Einstufung: 499 mm2 -> ruhend", einstufung(499, bw) == RUHEND)
    pruefe("Einstufung: 500 mm2 -> schwach belueftet",
           einstufung(500, bw) == SCHWACH)
    pruefe("Einstufung: 1499 mm2 -> schwach belueftet",
           einstufung(1499, bw) == SCHWACH)
    pruefe("Einstufung: 1500 mm2 -> stark belueftet",
           einstufung(1500, bw) == STARK)

    def rechne(a_ve):
        return berechne(AUFBAU, LUFTSCHICHT, a_ve, materialien={},
                        widerstaende=WIDERSTAENDE, belueftungswerte=bw)

    # --- 2. Die beiden Nachbarfaelle --------------------------------------
    e_ruhend = rechne(200)
    pruefe("6.9.2: R_tot;nve = 2,99122 (m2K)/W",
           e_ruhend.ok and nah(e_ruhend.r_tot, R_NVE, 1e-5),
           f"{e_ruhend.r_tot:.6f}" if e_ruhend.ok else str(e_ruhend.fehler))
    e_stark = rechne(2000)
    pruefe("6.9.4: R_tot;ve = 2,78143 (m2K)/W (Rse = 0,13 ruhend)",
           e_stark.ok and nah(e_stark.r_tot, R_VE, 1e-5)
           and nah(e_stark.rse_ruhend, 0.13),
           f"{e_stark.r_tot:.6f}, Rse={e_stark.rse_ruhend}")

    # --- 3. Stetigkeit an beiden Raendern, Gleichung (11) -----------------
    # A_ve = 500: (1500-500)/1000 = 1,0 auf R_nve, (500-500)/1000 = 0 auf R_ve
    # A_ve = 1500: 0 auf R_nve, 1,0 auf R_ve
    e_500 = rechne(500)
    pruefe("Gl. (11) bei A_ve = 500: exakt R_tot;nve",
           e_500.einstufung == SCHWACH and nah(e_500.r_tot, e_ruhend.r_tot, 1e-12),
           f"{e_500.r_tot:.9f} gegen {e_ruhend.r_tot:.9f}")
    e_1500 = rechne(1500)
    pruefe("A_ve = 1500 faellt in 6.9.4 und trifft R_tot;ve",
           e_1500.einstufung == STARK and nah(e_1500.r_tot, e_stark.r_tot, 1e-12),
           f"{e_1500.r_tot:.9f}")
    # Der obere Randpunkt der Gleichung selbst: 1499,999... liegt noch in 6.9.3
    # und muss gegen R_tot;ve konvergieren.
    e_fast = rechne(1499.999)
    pruefe("Gl. (11) konvergiert bei A_ve -> 1500 gegen R_tot;ve",
           e_fast.einstufung == SCHWACH and nah(e_fast.r_tot, R_VE, 1e-5),
           f"{e_fast.r_tot:.7f}")

    # --- 4. Mitte des Bereichs, von Hand hergeleitet ----------------------
    # A_ve = 1000 mm2:
    #   (1500-1000)/1000 = 0,5   und   (1000-500)/1000 = 0,5
    #   R_tot = 0,5*2,9912203 + 0,5*2,7814286 = 0,5*5,7726489 = 2,8863245
    #   U = 1/2,8863245 = 0,346462 -> gerundet 0,3465
    e_1000 = rechne(1000)
    pruefe("Gl. (11) bei A_ve = 1000: R_tot = 2,8863245",
           nah(e_1000.r_tot, 2.8863245, 1e-5), f"{e_1000.r_tot:.7f}")
    pruefe("Gl. (11) bei A_ve = 1000: U = 0,3465",
           nah(e_1000.u_value, 0.3465, 1e-4), f"{e_1000.u_value}")
    pruefe("Gl. (11): beide Nachbarrechnungen werden mitgeliefert",
           nah(e_1000.r_tot_nve, R_NVE, 1e-5) and nah(e_1000.r_tot_ve, R_VE, 1e-5),
           f"nve={e_1000.r_tot_nve:.5f} ve={e_1000.r_tot_ve:.5f}")

    # Monotonie: mehr Oeffnungsflaeche darf den Widerstand nicht erhoehen.
    werte = [rechne(a).r_tot for a in (500, 750, 1000, 1250, 1499.999)]
    pruefe("Gl. (11): R_tot faellt monoton mit A_ve",
           all(a >= b - 1e-12 for a, b in zip(werte, werte[1:])),
           " > ".join(f"{w:.4f}" for w in werte))

    # --- 5. Zulaessigkeit nach Tabelle B.6 --------------------------------
    pruefe("Standardauswahl (Tabelle B.6): Naeherung 6.9.3 zulaessig",
           bw.naeherung_zulaessig is True, str(bw.naeherung_zulaessig))
    pruefe("Ergebnis weist die Standardauswahl aus",
           any("Tabelle B.6" in h for h in e_1000.hinweise),
           str([h for h in e_1000.hinweise if "B.6" in h][:1]))
    # Umschaltbar ohne Code-Aenderung: steht das Flag auf false, gibt es kein
    # Ergebnis — statt still auf einen der Nachbarfaelle auszuweichen.
    bw_aus = lade_belueftungswerte()
    bw_aus.naeherung_zulaessig = False
    e_gesperrt = berechne(AUFBAU, LUFTSCHICHT, 1000, materialien={},
                          widerstaende=WIDERSTAENDE, belueftungswerte=bw_aus)
    pruefe("Flag false: kein Ergebnis statt Ausweichen auf einen Nachbarfall",
           not e_gesperrt.ok and any("6.9.3" in f for f in e_gesperrt.fehler),
           str(e_gesperrt.fehler[:1]))

    # --- 6. A_ve ist Pflicht ----------------------------------------------
    e_ohne = berechne(AUFBAU, LUFTSCHICHT, None, materialien={},
                      widerstaende=WIDERSTAENDE, belueftungswerte=bw)
    pruefe("A_ve fehlt: abgelehnt, kein Rueckfall auf 'ruhend'",
           not e_ohne.ok and e_ohne.r_tot is None
           and any("A_ve" in f for f in e_ohne.fehler),
           str(e_ohne.fehler[:1]))

    # --- 7. Bezug der Oeffnungsflaeche wird mitgefuehrt -------------------
    e_horiz = berechne(AUFBAU, LUFTSCHICHT, 1000, materialien={},
                       widerstaende=WIDERSTAENDE, orientierung="horizontal",
                       belueftungswerte=bw)
    pruefe("vertikal: Bezug je Meter Laenge",
           "je Meter Laenge" in e_1000.bezug, e_1000.bezug)
    pruefe("horizontal: Bezug je Quadratmeter Oberflaeche",
           "je Quadratmeter" in e_horiz.bezug, e_horiz.bezug)

    # --- 8. Fehlerfaelle ---------------------------------------------------
    e_index = berechne(AUFBAU, 9, 1000, materialien={},
                       widerstaende=WIDERSTAENDE, belueftungswerte=bw)
    pruefe("luftschicht_index ausserhalb der Liste -> Fehler", not e_index.ok,
           str(e_index.fehler[:1]))
    e_negativ = berechne(AUFBAU, LUFTSCHICHT, -1, materialien={},
                         widerstaende=WIDERSTAENDE, belueftungswerte=bw)
    pruefe("negatives A_ve -> Fehler", not e_negativ.ok,
           str(e_negativ.fehler[:1]))

    print()
    print(f"{'ALLE TESTS BESTANDEN' if fehler == 0 else str(fehler) + ' TEST(S) FEHLGESCHLAGEN'}")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
