#!/usr/bin/env python3
"""
test_thermal_corrections.py — Tests fuer die delta_U-Korrekturen nach
DIN EN ISO 6946 Anhang F.

Jeder Sollwert ist im Kommentar von Hand hergeleitet. Ein Test, dessen
Erwartungswert aus demselben Code stammt, den er prueft, testet nichts.

Aufruf:
    python3 tools/test_thermal_corrections.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from thermal_corrections import (  # noqa: E402
    korrigiere,
    lade_korrekturwerte,
)


def nah(a, b, toleranz: float = 1e-6) -> bool:
    return a is not None and abs(a - b) < toleranz


def main() -> int:
    fehler = 0

    def pruefe(name: str, bedingung: bool, detail: str = "") -> None:
        nonlocal fehler
        fehler += 0 if bedingung else 1
        print(f"{name:58} {'PASS' if bedingung else 'FAIL'}  {detail}")

    kw = lade_korrekturwerte()
    pruefe("Katalog thermal_corrections vollstaendig geladen", kw.ok,
           str(kw.fehler[:1]))
    if not kw.ok:
        print("\nOhne Werte-Overlay keine weiteren Tests.")
        return 1
    pruefe("Tabelle F.1 hat die Stufen 0/1/2",
           sorted(kw.delta_u_double_prime) == [0, 1, 2],
           str(sorted(kw.delta_u_double_prime)))

    # --- 1. Luftspalte, F.3 ------------------------------------------------
    # Stufe 2 -> delta_U'' = 0,04 ; R_1 = 2,5 ; R_tot = 3,0 ; U = 1/3 = 0,33333
    #   (R_1/R_tot)^2 = (0,833333)^2 = 0,694444
    #   delta_U_g = 0,04 * 0,694444 = 0,0277778 W/(m2K)
    #   3 % von U = 0,0100000  ->  0,02778 > 0,01, also angewendet
    #   U_korr = 0,333333 + 0,027778 = 0,361111 -> gerundet 0,3611
    k = korrigiere(1 / 3.0, 3.0, luftspalte={"stufe": 2, "r_1": 2.5},
                   korrekturwerte=kw)
    pruefe("F.3 Luftspalte Stufe 2: delta_U_g = 0,027778",
           nah(k.delta_u_g, 0.0277778, 1e-6), f"{k.delta_u_g:.6f}")
    pruefe("F.3: angewendet, U_korr = 0,3611",
           k.angewendet and nah(k.u_korrigiert, 0.3611, 1e-4),
           f"{k.u_korrigiert}")

    # Stufe 0 ist der Nullfall: delta_U'' = 0, es gibt nichts zu korrigieren.
    k0 = korrigiere(1 / 3.0, 3.0, luftspalte={"stufe": 0, "r_1": 2.5},
                    korrekturwerte=kw)
    pruefe("F.3 Stufe 0: delta_U = 0, geprueft aber nicht angewendet",
           k0.geprueft and not k0.angewendet and k0.delta_u_gesamt == 0.0
           and nah(k0.u_korrigiert, 1 / 3.0),
           f"{k0.delta_u_gesamt}")

    # F.2.2: versetzte Fugen -> Verzicht zulaessig, unabhaengig von der Stufe.
    k_versetzt = korrigiere(1 / 3.0, 3.0,
                            luftspalte={"stufe": 2, "r_1": 2.5,
                                        "versetzte_fugen": True},
                            korrekturwerte=kw)
    pruefe("F.2.2 versetzte Fugen: delta_U_g = 0 mit Begruendung",
           k_versetzt.delta_u_g == 0.0
           and any("versetzten Fugen" in b for b in k_versetzt.begruendungen),
           str(k_versetzt.begruendungen[:1]))

    # --- 2. Befestigungselemente, F.5 --------------------------------------
    # lambda_f = 50 W/(mK) ; A_f = 0,00002 m2 ; n_f = 4 /m2 ; d_0 = 0,20 m
    # R_1 = 5,0 ; R_tot = 5,5 ; U = 1/5,5 = 0,1818182
    #   lambda_f*A_f*n_f/d_0 = 50*0,00002*4/0,20 = 0,004/0,20 = 0,02
    #   (R_1/R_tot)^2 = (0,9090909)^2 = 0,8264463
    #   delta_U_f = 0,8 * 0,02 * 0,8264463 = 0,0132231 W/(m2K)
    #   3 % von U = 0,0054545  ->  angewendet
    #   U_korr = 0,1818182 + 0,0132231 = 0,1950413 -> gerundet 0,195
    duebel = {"lambda_f": 50.0, "a_f": 0.00002, "n_f": 4.0, "d_0": 0.20,
              "r_1": 5.0}
    k_f = korrigiere(1 / 5.5, 5.5, befestigungen=duebel, korrekturwerte=kw)
    pruefe("F.5 Duebel: delta_U_f = 0,0132231",
           nah(k_f.delta_u_f, 0.0132231, 1e-6), f"{k_f.delta_u_f:.7f}")
    pruefe("F.5: angewendet, U_korr = 0,1950",
           k_f.angewendet and nah(k_f.u_korrigiert, 0.1950, 1e-4),
           f"{k_f.u_korrigiert}")

    # Aussparung: alpha = 0,8 * d_1/d_0 = 0,8 * 0,10/0,20 = 0,4
    #   -> genau die Haelfte von oben: 0,0066116
    k_aus = korrigiere(1 / 5.5, 5.5,
                       befestigungen={**duebel, "d_1": 0.10,
                                      "in_aussparung": True},
                       korrekturwerte=kw)
    pruefe("F.5 Aussparung: alpha skaliert mit d_1/d_0",
           nah(k_aus.delta_u_f, 0.0066116, 1e-6), f"{k_aus.delta_u_f:.7f}")

    # ANMERKUNG 1: d_1 > d_0 ist bei schraegem Einbau gueltig und wird NICHT
    # abgefangen. alpha bleibt der Grundwert, das Ergebnis ist identisch zum
    # Grundfall.
    k_schraeg = korrigiere(1 / 5.5, 5.5,
                           befestigungen={**duebel, "d_1": 0.25},
                           korrekturwerte=kw)
    pruefe("F.5 schraeger Einbau d_1 > d_0: gueltig, alpha = Grundwert",
           k_schraeg.ok and nah(k_schraeg.delta_u_f, 0.0132231, 1e-6),
           f"{k_schraeg.delta_u_f:.7f}")
    # Ein als Aussparung gekennzeichnetes Element mit d_1 > d_0 ist dagegen ein
    # Widerspruch in der Eingabe und wird gemeldet.
    k_widerspruch = korrigiere(1 / 5.5, 5.5,
                               befestigungen={**duebel, "d_1": 0.25,
                                              "in_aussparung": True},
                               korrekturwerte=kw)
    pruefe("F.5 Aussparung mit d_1 > d_0 -> Fehler statt stiller Rechnung",
           not k_widerspruch.ok, str(k_widerspruch.fehler[:1]))

    # --- 3. Umkehrdach, F.6 ------------------------------------------------
    # Standardauswahl: p = 3 mm/Tag (Tabelle B.7), f*x = 0,04
    # R_1 = 4,0 ; R_tot = 4,5 ; U = 1/4,5 = 0,2222222
    #   (R_1/R_tot)^2 = (0,8888889)^2 = 0,7901235
    #   delta_U_r = 3 * 0,04 * 0,7901235 = 0,12 * 0,7901235 = 0,0948148
    #   3 % von U = 0,0066667  ->  angewendet
    #   U_korr = 0,2222222 + 0,0948148 = 0,3170370 -> gerundet 0,3170
    k_r = korrigiere(1 / 4.5, 4.5, umkehrdach={"r_1": 4.0}, korrekturwerte=kw)
    pruefe("F.6 Umkehrdach mit p aus Tabelle B.7: delta_U_r = 0,094815",
           nah(k_r.delta_u_r, 0.0948148, 1e-6), f"{k_r.delta_u_r:.7f}")
    pruefe("F.6: p = 3 mm/Tag als Standardauswahl ausgewiesen",
           any("Tabelle B.7" in b for b in k_r.begruendungen),
           str([b for b in k_r.begruendungen if "B.7" in b][:1]))
    pruefe("F.6: angewendet, U_korr = 0,3170",
           k_r.angewendet and nah(k_r.u_korrigiert, 0.3170, 1e-4),
           f"{k_r.u_korrigiert}")

    # p ueberschrieben (nationale Festlegung): 1,5 mm/Tag -> exakt die Haelfte
    k_r2 = korrigiere(1 / 4.5, 4.5, umkehrdach={"r_1": 4.0, "p": 1.5},
                      korrekturwerte=kw)
    pruefe("F.6: p ueberschreibbar (1,5 mm/Tag -> halber Zuschlag)",
           nah(k_r2.delta_u_r, 0.0474074, 1e-6), f"{k_r2.delta_u_r:.7f}")

    # Anwendungsgrenzen: harte Sperren, keine Warnungen.
    k_pu = korrigiere(1 / 4.5, 4.5,
                      umkehrdach={"r_1": 4.0, "daemmstoff": "PU"},
                      korrekturwerte=kw)
    pruefe("F.6: PU-Umkehrdach wird abgelehnt (nur XPS)",
           not k_pu.ok and any("XPS" in f for f in k_pu.fehler),
           str(k_pu.fehler[:1]))
    k_kuehl = korrigiere(1 / 4.5, 4.5,
                         umkehrdach={"r_1": 4.0, "betriebsfall": "kuehlfall"},
                         korrekturwerte=kw)
    pruefe("F.6: Kuehlfall wird abgelehnt (nur Heizfall)",
           not k_kuehl.ok and any("Heizfall" in f for f in k_kuehl.fehler),
           str(k_kuehl.fehler[:1]))

    # --- 4. Bagatellgrenze 6.7.3 ------------------------------------------
    # Stufe 1 -> delta_U'' = 0,01 ; R_1 = 1,0 ; R_tot = 2,0 ; U = 0,5
    #   delta_U_g = 0,01 * (0,5)^2 = 0,0025 W/(m2K)
    #   3 % von U = 0,015  ->  0,0025 < 0,015, Korrektur entfaellt
    #   U_korr bleibt 0,5 — aber geprueft=True und delta_U wird ausgewiesen.
    k_bag = korrigiere(0.5, 2.0, luftspalte={"stufe": 1, "r_1": 1.0},
                       korrekturwerte=kw)
    pruefe("6.7.3: delta_U = 0,0025 unter der Bagatellgrenze 0,015",
           nah(k_bag.delta_u_gesamt, 0.0025, 1e-9)
           and nah(k_bag.bagatellgrenze, 0.015, 1e-9),
           f"delta_U={k_bag.delta_u_gesamt:.5f} Grenze={k_bag.bagatellgrenze:.5f}")
    pruefe("6.7.3: Korrektur entfaellt, U bleibt unveraendert",
           not k_bag.angewendet and nah(k_bag.u_korrigiert, 0.5),
           f"{k_bag.u_korrigiert}")
    pruefe("6.7.3: geprueft und verworfen wird ausgewiesen",
           k_bag.geprueft and any("geprueft und verworfen" in b
                                  for b in k_bag.begruendungen),
           str([b for b in k_bag.begruendungen if "verworfen" in b][:1]))

    # --- 5. Summe der drei Anteile, F.2 ------------------------------------
    # Alle drei zusammen: 0,0277778 + 0,0132231 ... aber mit gemeinsamem R_tot.
    # R_tot = 5,0 ; U = 0,2 ; R_1 jeweils 4,0 -> (4/5)^2 = 0,64
    #   delta_U_g = 0,01 * 0,64            = 0,0064
    #   delta_U_f = 0,8 * 0,02 * 0,64      = 0,01024
    #   delta_U_r = 3 * 0,04 * 0,64        = 0,0768
    #   Summe                              = 0,09344
    #   U_korr = 0,2 + 0,09344 = 0,29344
    k_alle = korrigiere(
        0.2, 5.0,
        luftspalte={"stufe": 1, "r_1": 4.0},
        befestigungen={"lambda_f": 50.0, "a_f": 0.00002, "n_f": 4.0,
                       "d_0": 0.20, "r_1": 4.0},
        umkehrdach={"r_1": 4.0},
        korrekturwerte=kw)
    pruefe("F.2: delta_U = delta_U_g + delta_U_f + delta_U_r = 0,09344",
           nah(k_alle.delta_u_gesamt, 0.09344, 1e-7),
           f"{k_alle.delta_u_g:.5f}+{k_alle.delta_u_f:.5f}+"
           f"{k_alle.delta_u_r:.5f}={k_alle.delta_u_gesamt:.5f}")
    pruefe("F.2: U_korr = 0,29344", nah(k_alle.u_korrigiert, 0.2934, 1e-4),
           f"{k_alle.u_korrigiert}")

    # --- 6. Ohne korrekturpflichtigen Sachverhalt -------------------------
    k_leer = korrigiere(0.2, 5.0, korrekturwerte=kw)
    pruefe("ohne Eingabe: delta_U = 0, geprueft, U unveraendert",
           k_leer.geprueft and not k_leer.angewendet
           and nah(k_leer.u_korrigiert, 0.2), f"{k_leer.u_korrigiert}")

    # --- 7. Fehlerfaelle ---------------------------------------------------
    k_stufe = korrigiere(0.2, 5.0, luftspalte={"stufe": 7, "r_1": 4.0},
                         korrekturwerte=kw)
    pruefe("unbekannte Luftspalt-Stufe -> Fehler", not k_stufe.ok,
           str(k_stufe.fehler[:1]))
    k_d0 = korrigiere(0.2, 5.0,
                      befestigungen={"lambda_f": 50.0, "a_f": 0.00002,
                                     "n_f": 4.0, "d_0": 0.0, "r_1": 4.0},
                      korrekturwerte=kw)
    pruefe("d_0 = 0 -> Fehler statt Division durch null", not k_d0.ok,
           str(k_d0.fehler[:1]))

    print()
    print(f"{'ALLE TESTS BESTANDEN' if fehler == 0 else str(fehler) + ' TEST(S) FEHLGESCHLAGEN'}")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
