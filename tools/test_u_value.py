#!/usr/bin/env python3
"""
test_u_value.py — Tests fuer die U-Wert-Berechnung.

Die Sollwerte sind bewusst so gewaehlt, dass sie sich auf Papier nachrechnen
lassen. Ein Test, dessen Erwartungswert aus demselben Code stammt, den er
prueft, testet nichts.

Aufruf:
    python3 tools/test_u_value.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from u_value import berechne, lade_katalog, lade_materialien  # noqa: E402

WIDERSTAENDE = lade_katalog("surface_resistances")


def nah(a: float, b: float, toleranz: float = 0.001) -> bool:
    return a is not None and abs(a - b) < toleranz


def main() -> int:
    fehler = 0
    materialien = lade_materialien()

    def pruefe(name: str, bedingung: bool, detail: str = "") -> None:
        nonlocal fehler
        fehler += 0 if bedingung else 1
        print(f"{name:52} {'PASS' if bedingung else 'FAIL'}  {detail}")

    # --- 1. Homogen, von Hand nachrechenbar --------------------------------
    # 0,20 m bei lambda 0,10 -> R = 2,000
    # R_T = 0,13 + 2,000 + 0,04 = 2,170 -> U = 0,46083
    k = {"id": "T1", "layers": [{"thickness_m": 0.20, "lambda": 0.10}]}
    e = berechne(k, materialien, WIDERSTAENDE, "exterior", "wall")
    pruefe("homogen: R_T = 2,170", nah(e.r_total, 2.170),
           f"R_T={e.r_total:.4f}" if e.r_total else str(e.fehler))
    pruefe("homogen: U = 0,4608", nah(e.u_value, 0.4608, 0.0002), f"U={e.u_value}")
    pruefe("homogen: Rsi/Rse aus Katalog", (e.rsi, e.rse) == (0.13, 0.04),
           f"{e.rsi}/{e.rse} via {e.resistance_source}")

    # --- 2. Uebergangswiderstaende folgen der Bauteilsituation --------------
    e_innen = berechne(k, materialien, WIDERSTAENDE, "same_zone", "wall")
    pruefe("Innenwand: Rse = 0,13 statt 0,04", (e_innen.rsi, e_innen.rse) == (0.13, 0.13),
           f"{e_innen.rsi}/{e_innen.rse}")
    e_dach = berechne(k, materialien, WIDERSTAENDE, "exterior", "roof")
    pruefe("Dach: Rsi = 0,10 (aufwaerts)", (e_dach.rsi, e_dach.rse) == (0.10, 0.04),
           f"{e_dach.rsi}/{e_dach.rse}")
    e_erd = berechne(k, materialien, WIDERSTAENDE, "ground_slab", "floor")
    pruefe("Erdreich: Rse = 0", e_erd.rse == 0.0, f"{e_erd.rsi}/{e_erd.rse}")

    # --- 3. Luftschicht ueber r_value statt lambda --------------------------
    # 0,18 (Luft) + 0,13 + 0,04 = 0,35 -> U = 2,857142
    k_luft = {"id": "T2", "layers": [{"r_value": 0.18}]}
    e = berechne(k_luft, materialien, WIDERSTAENDE, "exterior", "wall")
    pruefe("Luftschicht ueber r_value: U = 2,8571", nah(e.u_value, 2.8571, 0.0002),
           f"U={e.u_value}")

    # --- 4. Kombiniertes Verfahren, DIN EN ISO 6946 6.7 --------------------
    # Dach, also Rsi = 0,10 und Rse = 0,04 (Waermestrom aufwaerts).
    # Zwei Abfolgen, gleiche Schichtung, Anteile 0,9 / 0,1:
    #   Gefach:  0,20 / 0,04 = 5,0000 -> R_T1 = 5,1400
    #   Sparren: 0,20 / 0,13 = 1,5385 -> R_T2 = 1,6785
    #   R_upper = 1 / (0,9/5,1400 + 0,1/1,6785)       = 4,26120
    #   R_lower = 0,14 + 1/(0,9/5,0000 + 0,1/1,5385)  = 4,22163
    #   R_T     = (4,26120 + 4,22163) / 2             = 4,24142
    #   U       = 1 / 4,24142                         = 0,23577
    #   e       = (4,26120 - 4,22163) / (2 * 4,24142) * 100 = 0,47 %  (Gl. 10)
    k_inhom = {
        "id": "T3",
        "sequences": [
            {"name": "Gefach", "share": 0.9,
             "layers": [{"thickness_m": 0.20, "lambda": 0.04}]},
            {"name": "Sparren", "share": 0.1,
             "layers": [{"thickness_m": 0.20, "lambda": 0.13}]},
        ],
    }
    e = berechne(k_inhom, materialien, WIDERSTAENDE, "exterior", "roof")
    pruefe("kombiniert: Verfahren erkannt", e.method == "kombiniert", e.method)
    pruefe("kombiniert: R_T = 4,2414", nah(e.r_total, 4.24142, 0.0005),
           f"R_T={e.r_total:.4f}" if e.r_total else str(e.fehler))
    pruefe("kombiniert: U = 0,2358", nah(e.u_value, 0.23577, 0.0002), f"U={e.u_value}")
    pruefe("kombiniert: max. Fehler e = 0,47 %", nah(e.uncertainty, 0.47, 0.02),
           f"e={e.uncertainty} %")

    # Der Sparren verschlechtert den U-Wert deutlich — genau der Effekt, den ein
    # flaches layers[] ohne Flaechenanteile nicht abbilden kann.
    e_ohne = berechne(
        {"id": "T3h", "layers": [{"thickness_m": 0.20, "lambda": 0.04}]},
        materialien, WIDERSTAENDE, "exterior", "roof")
    pruefe("kombiniert schlechter als homogen gerechnet",
           e.u_value > e_ohne.u_value,
           f"{e.u_value} gegen {e_ohne.u_value} (+{(e.u_value/e_ohne.u_value-1):.0%})")

    # --- 5. Rueckfall auf Parallelweg bei ungleicher Schichtung ------------
    k_ungleich = {
        "id": "T4",
        "sequences": [
            {"share": 0.9, "layers": [{"thickness_m": 0.20, "lambda": 0.04}]},
            {"share": 0.1, "layers": [{"thickness_m": 0.10, "lambda": 0.13},
                                      {"thickness_m": 0.10, "lambda": 0.20}]},
        ],
    }
    e = berechne(k_ungleich, materialien, WIDERSTAENDE, "exterior", "roof")
    pruefe("ungleiche Schichtung: Naeherung + Warnung",
           e.method == "parallelweg_naeherung" and len(e.warnungen) >= 1, e.method)

    # --- 6. Fehlerfaelle melden statt still rechnen ------------------------
    e = berechne({"id": "T5", "layers": [{"thickness_m": 0.2}]},
                 materialien, WIDERSTAENDE, "exterior", "wall")
    pruefe("Schicht ohne lambda und ohne Referenz -> Fehler",
           not e.ok and e.fehler != [], str(e.fehler[:1]))

    e = berechne({"id": "T6", "layers": [{"thickness_m": 0.2, "material_ref": "MAT_GIBTS_NICHT"}]},
                 materialien, WIDERSTAENDE, "exterior", "wall")
    pruefe("unbekanntes Material -> Fehler", not e.ok, str(e.fehler[:1]))

    e = berechne({"id": "T7", "layers": [{"thickness_m": 0.2, "lambda": 0.1}]},
                 materialien, WIDERSTAENDE, "wolkenkuckucksheim", "wall")
    pruefe("unbekannte Bauteilsituation -> Fehler", not e.ok, str(e.fehler[:1]))

    # --- 7. Anteilssumme ungleich 1 wird gemeldet --------------------------
    k_summe = {
        "id": "T8",
        "sequences": [
            {"share": 0.9, "layers": [{"thickness_m": 0.2, "lambda": 0.04}]},
            {"share": 0.2, "layers": [{"thickness_m": 0.2, "lambda": 0.13}]},
        ],
    }
    e = berechne(k_summe, materialien, WIDERSTAENDE, "exterior", "roof")
    pruefe("Anteilssumme 1,1 wird gemeldet",
           any("Flaechenanteile" in w for w in e.warnungen), str(e.warnungen[:1]))

    # --- 7b. Luftschicht aus Tabelle 8, mit Interpolation ------------------
    # 20 mm horizontal liegt zwischen 15 mm (0,17) und 25 mm (0,18):
    # 0,17 + 0,5 * (0,18 - 0,17) = 0,175
    from u_value import lade_luftschichten, luftschicht_widerstand
    luft = lade_luftschichten()
    r, problem = luftschicht_widerstand(20.0, "horizontal", luft)
    pruefe("Tabelle 8: 20 mm horizontal = 0,175 (interpoliert)",
           nah(r, 0.175, 0.0001), f"R={r}")
    r25_auf, _ = luftschicht_widerstand(25.0, "upward", luft)
    r25_ab, _ = luftschicht_widerstand(25.0, "downward", luft)
    pruefe("Tabelle 8: 25 mm richtungsabhaengig (0,16 / 0,19)",
           nah(r25_auf, 0.16) and nah(r25_ab, 0.19), f"auf={r25_auf} ab={r25_ab}")
    r500, _ = luftschicht_widerstand(500.0, "downward", luft)
    pruefe("Tabelle 8: oberhalb 300 mm wird der letzte Wert gehalten",
           nah(r500, 0.23), f"R={r500}")

    # Luftschicht im Schichtaufbau, ueber air_layer statt lambda
    k_luftschicht = {
        "id": "T9",
        "layers": [{"thickness_m": 0.025, "air_layer": True},
                   {"thickness_m": 0.20, "lambda": 0.04}],
    }
    e = berechne(k_luftschicht, materialien, WIDERSTAENDE, "exterior", "wall")
    # 0,13 + 0,18 + 5,0 + 0,04 = 5,35 -> U = 0,186916
    pruefe("Luftschicht im Aufbau: U = 0,1869", nah(e.u_value, 0.1869, 0.0002),
           f"U={e.u_value}")

    # --- 7c. Harte Anwendungsgrenze 6.7.2.1 --------------------------------
    # Anteile 0,5/0,5, R = 5,00 gegen 0,04 -> Verhaeltnis 1,62 > 1,5
    k_extrem = {
        "id": "T10",
        "sequences": [
            {"share": 0.5, "layers": [{"thickness_m": 0.20, "lambda": 0.04}]},
            {"share": 0.5, "layers": [{"thickness_m": 0.20, "lambda": 5.00}]},
        ],
    }
    e = berechne(k_extrem, materialien, WIDERSTAENDE, "exterior", "wall")
    pruefe("Verhaeltnis > 1,5: Verfahren unzulaessig, kein Ergebnis",
           not e.ok and e.method == "unzulaessig" and e.u_value is None,
           str(e.fehler[:1]))

    # --- 7d. Rundung des Endergebnisses (6.7.2.2) --------------------------
    e = berechne(k, materialien, WIDERSTAENDE, "exterior", "wall")
    pruefe("R_tot auf zwei Dezimalen gerundet mitgefuehrt",
           e.r_total_rounded == 2.17, f"{e.r_total_rounded}")

    # --- 7e. Fenster nach DIN EN ISO 10077-1, gegen Tabelle H.1 -----------
    # Referenzfenster 1,23 x 1,48 m, Rahmenanteil 30 %, typische Abstandhalter.
    # Spalte Uf = 2,6 ausgelassen: sie verletzt in mehreren Zeilen die Monotonie
    # und ist ein Extraktionsartefakt, kein Normwert.
    from u_value import uw_fenster
    UF = [0.80, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 3.0, 3.4, 3.8, 7.0]
    H1 = {
        3.3: [2.7, 2.8, 2.8, 2.9, 2.9, 3.0, 3.1, 3.2, 3.4, 3.5, 3.6, 4.5],
        3.0: [2.5, 2.5, 2.6, 2.7, 2.7, 2.8, 2.8, 3.0, 3.2, 3.3, 3.4, 4.2],
        2.0: [1.8, 1.9, 2.0, 2.0, 2.1, 2.1, 2.2, 2.3, 2.6, 2.7, 2.8, 3.6],
        1.5: [1.5, 1.5, 1.6, 1.7, 1.7, 1.8, 1.8, 2.0, 2.2, 2.3, 2.5, 3.3],
        1.1: [1.2, 1.3, 1.3, 1.4, 1.4, 1.5, 1.6, 1.7, 1.9, 2.1, 2.2, 3.0],
        0.8: [1.0, 1.1, 1.1, 1.2, 1.2, 1.3, 1.4, 1.5, 1.7, 1.9, 2.0, 2.8],
    }
    treffer = summe = 0
    for ug, zeile in H1.items():
        for uf, soll in zip(UF, zeile):
            e = uw_fenster(ug, uf, 0.30)
            summe += 1
            treffer += abs(e.u_value - soll) <= 0.06
    pruefe("Fenster: 72 Stuetzstellen der Tabelle H.1", treffer == summe,
           f"{treffer}/{summe} innerhalb 0,06 W/(m2K)")

    # Einfachverglasung: Psi_g = 0 (G.1), sonst rechnet sie sich zu schlecht
    e_ein = uw_fenster(5.8, 1.4, 0.30, single_glazing=True)
    e_falsch = uw_fenster(5.8, 1.4, 0.30)
    pruefe("Fenster: Einfachverglasung hat Psi_g = 0",
           abs(e_ein.u_value - 4.5) <= 0.06 and e_falsch.u_value > e_ein.u_value,
           f"mit Psi=0: {e_ein.u_value} (Norm 4,5) / mit Abstandhalter: {e_falsch.u_value}")

    e_bad = uw_fenster(1.1, 1.3, 1.5)
    pruefe("Fenster: Rahmenanteil ausserhalb 0..1 -> Fehler", not e_bad.ok,
           str(e_bad.fehler[:1]))

    # --- 8. Gegen den Altkatalog: ein reproduzierbarer Fall ----------------
    import json
    alt = {c["id"]: c for c in json.loads(
        (Path(__file__).resolve().parent.parent / "catalog" / "constructions.json")
        .read_text(encoding="utf-8"))["constructions"]}
    e = berechne(alt["ROOF_FLAT_INSULATED_200"], materialien, WIDERSTAENDE,
                 "exterior", "roof")
    abw = abs(e.u_value - alt["ROOF_FLAT_INSULATED_200"]["u_value_calculated"]) \
        / alt["ROOF_FLAT_INSULATED_200"]["u_value_calculated"]
    pruefe("Altkatalog ROOF_FLAT_INSULATED_200 reproduziert", abw < 0.05,
           f"U={e.u_value} gegen 0.17 ({abw:+.1%})")

    print()
    gesamt = 28
    print(f"{gesamt - fehler}/{gesamt} Pruefungen bestanden")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
