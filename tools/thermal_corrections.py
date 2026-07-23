#!/usr/bin/env python3
"""
thermal_corrections.py — Korrekturen delta_U des Waermedurchgangskoeffizienten
nach DIN EN ISO 6946, Abschnitt 6.7.3 und Anhang F.

Zusammenfuehrung (6.7.3 / F.1):

    U_korrigiert = U + delta_U        mit    delta_U = delta_U_g + delta_U_f + delta_U_r

Die drei Anteile:

  delta_U_g  Luftspalte in der Daemmschicht (F.3):
                 delta_U_g = delta_U'' * (R_1 / R_tot)^2
             delta_U'' nach Tabelle F.1, Stufe 0/1/2. R_1 ist der Widerstand der
             Schicht, die die Zwischenraeume enthaelt, R_tot der Gesamtwiderstand
             OHNE Beruecksichtigung von Waermebruecken.

  delta_U_f  Mechanische Befestigungselemente (F.3.2, Gleichung F.5):
                 delta_U_f = alpha * (lambda_f * A_f * n_f / d_0) * (R_1 / R_tot)^2
             alpha = 0,8 bei vollstaendiger Durchdringung der Daemmschicht,
             alpha = 0,8 * d_1/d_0 bei einem in eine Aussparung eingebauten
             Element.

  delta_U_r  Umkehrdach (F.4, Gleichung F.6):
                 delta_U_r = p * f * x * (R_1 / R_tot)^2
             p ist die mittlere Niederschlagsmenge waehrend der Heizperiode.

BAGATELLGRENZE, 6.7.3, woertlich: "Ist jedoch die nach Gleichung (F.2)
ermittelte Gesamtkorrektur geringer als 3 % von U, braucht keine Korrektur
vorgenommen zu werden." Das Ergebnis weist trotzdem aus, dass geprueft und
verworfen wurde (geprueft=True, angewendet=False) — sonst sieht ein
unkorrigiertes Ergebnis aus wie ein nie geprueftes.

ANWENDUNGSGRENZEN, die hier RECHNEN und nicht nur dokumentiert sind:
  - F.2.2: Wird die Daemmung mehrlagig mit VERSETZTEN Fugen eingebaut, darf auf
    die Luftspaltkorrektur verzichtet werden. Nur Zwischenraeume, die die
    gesamte Daemmdicke von warm nach kalt durchdringen, rechtfertigen eine
    Korrektur.
  - F.4 gilt NUR fuer extrudierten Polystyrol-Hartschaum (XPS) und NUR im
    Heizfall. Ein PU-Umkehrdach oder eine Kuehllastrechnung wird abgelehnt,
    nicht schoengerechnet.

Alle Zahlenwerte (die drei Stufen delta_U'', alpha, f*x, p, die 3-%-Grenze)
kommen aus dem Katalog thermal_corrections — Struktur oeffentlich, Zahlen im
privaten Werte-Overlay.

Aufruf:
    python3 tools/thermal_corrections.py --u 0.18 --r-tot 5.5 \\
        --fasteners 50,0.00002,4,0.20,5.0
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from u_value import lade_katalog_roh  # noqa: E402

# Materialien, fuer die F.4 gilt. Die Norm nennt ausdruecklich nur extrudierten
# Polystyrol-Hartschaum — die Einschraenkung ist Teil der Rechenvorschrift.
UMKEHRDACH_ZULAESSIGE_DAEMMUNG = {"XPS"}

# Betriebsfaelle, in denen F.4 gilt. Im Kuehlfall wirkt das Regenwasser nicht
# als Verlust, die Korrektur waere falsch.
UMKEHRDACH_ZULAESSIGE_BETRIEBSFAELLE = {"heizfall"}


@dataclass
class Korrekturwerte:
    """Zahlenwerte aus dem Katalog thermal_corrections."""
    delta_u_double_prime: dict = field(default_factory=dict)   # level -> Wert
    alpha_full_penetration: float | None = None
    f_times_x: float | None = None
    p_default: float | None = None
    negligibility_threshold: float | None = None
    fehler: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fehler


def lade_korrekturwerte() -> Korrekturwerte:
    """Laedt thermal_corrections inkl. privatem Werte-Overlay."""
    kw = Korrekturwerte()
    roh, meldung = lade_katalog_roh("thermal_corrections")
    if not roh:
        kw.fehler.append("Katalog thermal_corrections nicht gefunden")
        return kw
    if meldung:
        kw.fehler.append(meldung)
        return kw

    for eintrag in roh.get("entries", []):
        wert = eintrag.get("delta_u_double_prime")
        if wert is None:
            kw.fehler.append(f"delta_U'' fehlt fuer '{eintrag.get('code')}' — "
                             f"Werte-Overlay unvollstaendig")
        kw.delta_u_double_prime[eintrag.get("level")] = wert

    def hole(block: str, code: str):
        for e in (roh.get(block) or {}).get("entries", []):
            if e.get("code") == code:
                return e.get("value")
        return None

    kw.alpha_full_penetration = hole("fastener_factors", "alpha_full_penetration")
    kw.f_times_x = hole("inverted_roof_factors",
                        "f_times_x_single_layer_open_cover")
    kw.p_default = hole("inverted_roof_factors", "p_default_heating_season")
    kw.negligibility_threshold = hole("application_rules",
                                      "negligibility_threshold")
    for name in ("alpha_full_penetration", "f_times_x", "p_default",
                 "negligibility_threshold"):
        if getattr(kw, name) is None:
            kw.fehler.append(f"'{name}' fehlt im Katalog thermal_corrections")
    return kw


@dataclass
class Korrektur:
    u_ausgang: float | None = None
    delta_u_g: float = 0.0
    delta_u_f: float = 0.0
    delta_u_r: float = 0.0
    delta_u_gesamt: float = 0.0
    bagatellgrenze: float | None = None
    geprueft: bool = False
    angewendet: bool = False
    u_korrigiert: float | None = None
    begruendungen: list = field(default_factory=list)
    warnungen: list = field(default_factory=list)
    fehler: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fehler


def _verhaeltnis_quadrat(r_1: float, r_tot: float) -> float:
    """(R_1/R_tot)^2 — der gemeinsame Faktor aller drei Korrekturen."""
    return (r_1 / r_tot) ** 2


def luftspalt_korrektur(
    stufe: int, r_1: float, r_tot: float, kw: Korrekturwerte,
    versetzte_fugen: bool = False, durchdringt_daemmdicke: bool = True,
) -> tuple[float, list, list]:
    """
    delta_U_g nach F.3. Liefert (Wert, Begruendungen, Fehler).

    Die beiden Verzichtsgruende aus F.2.2 sind hier bewusst Rechenweg und nicht
    Doku: mehrlagig mit versetzten Fugen, oder Zwischenraeume, die die
    Daemmdicke nicht von warm nach kalt durchdringen — in beiden Faellen ist
    delta_U_g null.
    """
    begruendungen: list = []
    if versetzte_fugen:
        begruendungen.append(
            "delta_U_g = 0: Daemmung mehrlagig mit versetzten Fugen eingebaut, "
            "F.2.2 laesst den Verzicht auf die Luftspaltkorrektur zu.")
        return 0.0, begruendungen, []
    if not durchdringt_daemmdicke:
        begruendungen.append(
            "delta_U_g = 0: die Zwischenraeume durchdringen die Daemmdicke nicht "
            "von der warmen zur kalten Seite (F.2.2).")
        return 0.0, begruendungen, []
    if stufe not in kw.delta_u_double_prime:
        return 0.0, [], [f"Luftspalt-Stufe {stufe} steht nicht in Tabelle F.1 "
                         f"(bekannt: {sorted(kw.delta_u_double_prime)})"]
    if r_tot <= 0:
        return 0.0, [], ["R_tot muss positiv sein"]
    wert = kw.delta_u_double_prime[stufe] * _verhaeltnis_quadrat(r_1, r_tot)
    begruendungen.append(
        f"delta_U_g = {kw.delta_u_double_prime[stufe]} * ({r_1:.3f}/{r_tot:.3f})^2 "
        f"= {wert:.5f} W/(m2K) (F.3, Tabelle F.1 Stufe {stufe})")
    return wert, begruendungen, []


def befestigungs_korrektur(
    lambda_f: float, a_f: float, n_f: float, d_0: float, r_1: float,
    r_tot: float, kw: Korrekturwerte, d_1: float | None = None,
    in_aussparung: bool = False,
) -> tuple[float, list, list]:
    """
    delta_U_f nach F.3.2, Gleichung F.5.

    alpha folgt der Einbausituation:
      - Element durchdringt die Daemmschicht vollstaendig -> alpha = 0,8
      - Element in einer Aussparung                       -> alpha = 0,8 * d_1/d_0

    ANMERKUNG 1 der Norm: d_1 kann die Daemmschichtdicke UEBERSTEIGEN, wenn das
    Element schraeg eingebaut wird. Dieser Fall wird nicht abgefangen — er ist
    gueltig, und er faellt unter die erste Regel: das Element durchdringt die
    Daemmschicht vollstaendig, alpha bleibt der Grundwert. Nur die Aussparung
    (d_1 < d_0, ausdruecklich als solche gekennzeichnet) skaliert alpha.
    """
    begruendungen: list = []
    if d_0 <= 0:
        return 0.0, [], ["d_0 (Dicke der Daemmschicht) muss positiv sein"]
    if r_tot <= 0:
        return 0.0, [], ["R_tot muss positiv sein"]
    if min(lambda_f, a_f, n_f) < 0:
        return 0.0, [], ["lambda_f, A_f und n_f duerfen nicht negativ sein"]

    alpha = kw.alpha_full_penetration
    if in_aussparung:
        if d_1 is None:
            return 0.0, [], ["Element in Aussparung, aber d_1 fehlt — ohne die "
                             "durchdringende Laenge ist alpha nicht bestimmbar"]
        if d_1 > d_0:
            return 0.0, [], [f"in_aussparung=True, aber d_1 ({d_1}) > d_0 ({d_0}). "
                             f"Ein Element, das laenger ist als die Daemmschicht "
                             f"dick, sitzt nicht in einer Aussparung — Eingabe "
                             f"pruefen."]
        alpha = kw.alpha_full_penetration * (d_1 / d_0)
        begruendungen.append(
            f"alpha = {kw.alpha_full_penetration} * {d_1}/{d_0} = {alpha:.4f} "
            f"(Element in Aussparung, F.3.2)")
    else:
        begruendungen.append(
            f"alpha = {alpha} (Element durchdringt die Daemmschicht "
            f"vollstaendig, F.3.2)")
        if d_1 is not None and d_1 > d_0:
            begruendungen.append(
                f"d_1 = {d_1} m > d_0 = {d_0} m — zulaessig bei schraegem Einbau "
                f"(ANMERKUNG 1); alpha bleibt der Grundwert.")

    wert = alpha * (lambda_f * a_f * n_f / d_0) * _verhaeltnis_quadrat(r_1, r_tot)
    begruendungen.append(
        f"delta_U_f = {alpha:.4f} * ({lambda_f} * {a_f} * {n_f} / {d_0}) * "
        f"({r_1:.3f}/{r_tot:.3f})^2 = {wert:.5f} W/(m2K) (F.5)")
    return wert, begruendungen, []


def umkehrdach_korrektur(
    r_1: float, r_tot: float, kw: Korrekturwerte,
    daemmstoff: str = "XPS", betriebsfall: str = "heizfall",
    p: float | None = None, f_times_x: float | None = None,
) -> tuple[float, list, list]:
    """
    delta_U_r nach F.4, Gleichung F.6.

    Beide Anwendungsgrenzen sind harte Sperren, keine Warnungen: F.4 gilt nur
    fuer XPS und nur im Heizfall. Wer ein PU-Umkehrdach im Kuehlfall korrigiert,
    rechnet es schoen.

    p ohne Angabe = Standardauswahl aus Tabelle B.7. Die ist informativ und darf
    national abweichend festgelegt werden — deshalb ueberschreibbar.
    """
    begruendungen: list = []
    if daemmstoff.upper() not in UMKEHRDACH_ZULAESSIGE_DAEMMUNG:
        return 0.0, [], [
            f"F.4 gilt nur fuer extrudierten Polystyrol-Hartschaum (XPS), "
            f"angegeben ist '{daemmstoff}'. Keine Korrektur — der Ansatz ist auf "
            f"das Feuchteverhalten von XPS abgestimmt und auf andere Daemmstoffe "
            f"nicht uebertragbar."]
    if betriebsfall.lower() not in UMKEHRDACH_ZULAESSIGE_BETRIEBSFAELLE:
        return 0.0, [], [
            f"F.4 gilt nur im Heizfall, angegeben ist '{betriebsfall}'. Im "
            f"Kuehlfall wird nicht korrigiert."]
    if r_tot <= 0:
        return 0.0, [], ["R_tot muss positiv sein"]

    fx = kw.f_times_x if f_times_x is None else f_times_x
    if p is None:
        p = kw.p_default
        begruendungen.append(
            f"p = {p} mm/Tag aus der Standardauswahl (Tabelle B.7, informativ). "
            f"Abweichende nationale Festlegung geht vor und ist am Aufruf "
            f"ueberschreibbar.")
    if p < 0:
        return 0.0, [], ["p (Niederschlagsmenge) darf nicht negativ sein"]

    wert = p * fx * _verhaeltnis_quadrat(r_1, r_tot)
    begruendungen.append(
        f"delta_U_r = {p} * {fx} * ({r_1:.3f}/{r_tot:.3f})^2 = {wert:.5f} "
        f"W/(m2K) (F.6)")
    return wert, begruendungen, []


def korrigiere(
    u: float,
    r_tot: float,
    luftspalte: dict | None = None,
    befestigungen: dict | None = None,
    umkehrdach: dict | None = None,
    korrekturwerte: Korrekturwerte | None = None,
) -> Korrektur:
    """
    Gesamtkorrektur nach 6.7.3 / F.1 bis F.4.

    Die drei Eingabeblocks sind optional; was nicht angegeben ist, liefert
    keinen Beitrag. Ohne jeden Block ist delta_U = 0 und das Ergebnis weist
    aus, dass nichts zu korrigieren war.

    r_tot ist der Gesamtwiderstand OHNE Beruecksichtigung von Waermebruecken —
    also das R_T aus u_value.berechne(), nicht ein bereits korrigierter Wert.
    """
    k = Korrektur(u_ausgang=u)
    kw = lade_korrekturwerte() if korrekturwerte is None else korrekturwerte
    if not kw.ok:
        k.fehler.extend(kw.fehler)
        return k
    if u <= 0:
        k.fehler.append("U muss positiv sein")
        return k

    if luftspalte:
        wert, gruende, fehler = luftspalt_korrektur(
            luftspalte.get("stufe", 0), luftspalte["r_1"], r_tot, kw,
            versetzte_fugen=luftspalte.get("versetzte_fugen", False),
            durchdringt_daemmdicke=luftspalte.get("durchdringt_daemmdicke", True))
        k.delta_u_g, k.fehler = wert, k.fehler + fehler
        k.begruendungen.extend(gruende)

    if befestigungen:
        wert, gruende, fehler = befestigungs_korrektur(
            befestigungen["lambda_f"], befestigungen["a_f"],
            befestigungen["n_f"], befestigungen["d_0"], befestigungen["r_1"],
            r_tot, kw, d_1=befestigungen.get("d_1"),
            in_aussparung=befestigungen.get("in_aussparung", False))
        k.delta_u_f, k.fehler = wert, k.fehler + fehler
        k.begruendungen.extend(gruende)

    if umkehrdach:
        wert, gruende, fehler = umkehrdach_korrektur(
            umkehrdach["r_1"], r_tot, kw,
            daemmstoff=umkehrdach.get("daemmstoff", "XPS"),
            betriebsfall=umkehrdach.get("betriebsfall", "heizfall"),
            p=umkehrdach.get("p"), f_times_x=umkehrdach.get("f_times_x"))
        k.delta_u_r, k.fehler = wert, k.fehler + fehler
        k.begruendungen.extend(gruende)

    if k.fehler:
        return k

    k.delta_u_gesamt = k.delta_u_g + k.delta_u_f + k.delta_u_r
    k.bagatellgrenze = kw.negligibility_threshold * u
    k.geprueft = True

    if k.delta_u_gesamt == 0.0:
        k.angewendet = False
        k.u_korrigiert = u
        k.begruendungen.append(
            "delta_U = 0 — es liegt kein korrekturpflichtiger Sachverhalt vor.")
        return k

    if k.delta_u_gesamt < k.bagatellgrenze:
        # 6.7.3: unterhalb 3 % von U braucht nicht korrigiert zu werden. Das
        # Ergebnis fuehrt den geprueften Wert trotzdem mit — sonst ist ein
        # verworfener Zuschlag von einem nie gerechneten nicht zu unterscheiden.
        k.angewendet = False
        k.u_korrigiert = u
        k.begruendungen.append(
            f"Korrektur geprueft und verworfen: delta_U = {k.delta_u_gesamt:.5f} "
            f"< 3 % von U ({k.bagatellgrenze:.5f} W/(m2K)). Nach 6.7.3 braucht "
            f"keine Korrektur vorgenommen zu werden.")
        return k

    k.angewendet = True
    k.u_korrigiert = round(u + k.delta_u_gesamt, 4)
    k.begruendungen.append(
        f"U_korrigiert = {u:.4f} + {k.delta_u_gesamt:.5f} = {k.u_korrigiert} "
        f"W/(m2K) (delta_U >= 3 % von U, 6.7.3)")
    return k


def main() -> int:
    p = argparse.ArgumentParser(
        description="delta_U-Korrekturen nach DIN EN ISO 6946 Anhang F")
    p.add_argument("--u", type=float, required=True, help="U-Wert ohne Korrektur")
    p.add_argument("--r-tot", type=float, required=True,
                   help="Gesamtwiderstand ohne Waermebruecken")
    p.add_argument("--air-gaps", help="stufe,R_1  (F.3)")
    p.add_argument("--staggered-joints", action="store_true",
                   help="mehrlagig mit versetzten Fugen (F.2.2)")
    p.add_argument("--fasteners", help="lambda_f,A_f,n_f,d_0,R_1  (F.5)")
    p.add_argument("--recess-d1", type=float,
                   help="d_1 fuer ein in eine Aussparung eingebautes Element")
    p.add_argument("--inverted-roof", help="R_1  (F.6)")
    p.add_argument("--precipitation", type=float,
                   help="p in mm/Tag, Standard aus Tabelle B.7")
    p.add_argument("--insulation", default="XPS")
    p.add_argument("--operation", default="heizfall",
                   choices=["heizfall", "kuehlfall"])
    args = p.parse_args()

    luftspalte = befestigungen = umkehrdach = None
    if args.air_gaps:
        stufe, r_1 = args.air_gaps.split(",")
        luftspalte = {"stufe": int(stufe), "r_1": float(r_1),
                      "versetzte_fugen": args.staggered_joints}
    if args.fasteners:
        lam, a_f, n_f, d_0, r_1 = (float(x) for x in args.fasteners.split(","))
        befestigungen = {"lambda_f": lam, "a_f": a_f, "n_f": n_f, "d_0": d_0,
                         "r_1": r_1}
        if args.recess_d1 is not None:
            befestigungen.update({"d_1": args.recess_d1, "in_aussparung": True})
    if args.inverted_roof:
        umkehrdach = {"r_1": float(args.inverted_roof), "p": args.precipitation,
                      "daemmstoff": args.insulation,
                      "betriebsfall": args.operation}

    k = korrigiere(args.u, args.r_tot, luftspalte, befestigungen, umkehrdach)

    print(f"U (unkorrigiert):  {args.u} W/(m2K)")
    print(f"delta_U_g:         {k.delta_u_g:.5f}")
    print(f"delta_U_f:         {k.delta_u_f:.5f}")
    print(f"delta_U_r:         {k.delta_u_r:.5f}")
    print(f"delta_U gesamt:    {k.delta_u_gesamt:.5f}")
    if k.bagatellgrenze is not None:
        print(f"Bagatellgrenze:    {k.bagatellgrenze:.5f} (3 % von U)")
    print(f"geprueft:          {k.geprueft}")
    print(f"angewendet:        {k.angewendet}")
    print(f"U (korrigiert):    {k.u_korrigiert}")
    for b in k.begruendungen:
        print(f"  - {b}")
    for w in k.warnungen:
        print(f"WARNUNG: {w}")
    for f in k.fehler:
        print(f"FEHLER:  {f}")
    return 0 if k.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
