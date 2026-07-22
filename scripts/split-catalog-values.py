#!/usr/bin/env python3
"""
split-catalog-values.py — trennt Normzahlenwerte von der Katalogstruktur.

Die Struktur (Codes, Namen, Norm-Referenzen, DWE-eigene Auslegungsregeln) bleibt
oeffentlich in catalog/core/. Die Zahlenwerte wandern nach catalog/values/, das
per .gitignore und scripts/check-catalog-values.sh gesperrt ist.

Warum als Skript und nicht als Einmal-Edit: die Trennung muss nachvollziehbar und
fuer kuenftige Kataloge wiederholbar sein. Wer wissen will, WELCHE Felder entwertet
wurden, liest FELDER unten — nicht einen Commit-Diff von vor Monaten.

Idempotent: bereits entwertete Kataloge werden erkannt und nicht doppelt gesplittet
(ein vorhandenes Overlay wird dann nicht ueberschrieben).

Aufruf:
    python3 scripts/split-catalog-values.py --dry-run
    python3 scripts/split-catalog-values.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORE = REPO / "catalog" / "core"
VALUES = REPO / "catalog" / "values"

# Welche Felder je Katalog Normzahlenwerte tragen.
#   entries:  Feldpfade innerhalb eines entries[]-Eintrags. Punkt = eine Ebene tiefer.
#   extra:    (Top-Level-Schluessel, Listenname, Feld) fuer Anhaenge ausserhalb entries[].
#   datei:    abweichender Pfad relativ zum Repo (Default: catalog/core/<id>.json)
#   liste:    abweichender Listenname (Default: "entries")
#   schluessel: abweichendes Merge-Feld (Default: "code")
FELDER = {
    "adjacency_types": {
        "entries": ["fx.value", "fx.simplified_value"],
        "extra": [],
        "grund": "Fx-Werte aus DIN V 18599-2 Tabelle 5/6",
    },
    "surface_resistances": {
        "entries": ["rsi", "rse"],
        "extra": [],
        "grund": "Waermeuebergangswiderstaende aus DIN EN ISO 6946 Tabelle 7",
    },
    "air_layers": {
        "entries": ["r_upward", "r_horizontal", "r_downward"],
        "extra": [("unheated_attic_spaces", "entries", "r_u")],
        "grund": "Luftschicht-Widerstaende aus DIN EN ISO 6946 Tabelle 8 und 9",
    },
    "moisture_conditions": {
        "entries": ["theta_i", "phi_i", "theta_e", "phi_e",
                    "duration_days", "rsi", "rse"],
        "extra": [("diffusion", "entries", "value"),
                  ("assessment_limits", "entries", "value")],
        "grund": "Klimarandbedingungen aus DIN 4108-3 Tabelle A.3, "
                 "delta_0 aus C.2.4, Grenzwerte aus 5.2.2/5.3",
    },
    # Nachtrag 22.07.2026: Der Materialkatalog lag ausserhalb von catalog/core/
    # und ist dem Guard deshalb durchgerutscht — 48 Eintraege mit Bemessungswerten
    # aus DIN 4108-4 Tabelle 1 standen im PUBLIC-Repo. Gleicher Fall wie der
    # 605-KB-Befund, gleiche Behandlung.
    #
    # wlg (Waermeleitgruppe) wird mit entwertet: sie ist eine direkte Ableitung
    # aus lambda und wuerde den Wert sonst auf 0,001 genau rekonstruierbar machen.
    "materials": {
        "datei": "catalog/materials.json",
        "liste": "materials",
        "schluessel": "id",
        "entries": ["lambda", "mu", "rho", "c", "wlg",
                    "r_value", "u_value", "g_value"],
        "extra": [],
        "grund": "Bemessungswerte aus DIN 4108-4 Tabelle 1 ff.",
    },
}


def hole(obj: dict, pfad: str):
    """Wert an einem punktgetrennten Pfad, oder None wenn der Pfad nicht existiert."""
    ziel = obj
    for teil in pfad.split("."):
        if not isinstance(ziel, dict) or teil not in ziel:
            return None
        ziel = ziel[teil]
    return ziel


def setze(obj: dict, pfad: str, wert) -> bool:
    """Setzt den Wert an einem punktgetrennten Pfad. False, wenn der Pfad fehlt."""
    teile = pfad.split(".")
    ziel = obj
    for teil in teile[:-1]:
        if not isinstance(ziel, dict) or teil not in ziel:
            return False
        ziel = ziel[teil]
    if not isinstance(ziel, dict) or teile[-1] not in ziel:
        return False
    ziel[teile[-1]] = wert
    return True


def split(katalog_id: str, konfig: dict, dry_run: bool) -> dict | None:
    liste = konfig.get("liste", "entries")
    schluessel = konfig.get("schluessel", "code")

    if konfig.get("datei"):
        pfad = REPO / konfig["datei"]
        if not pfad.exists():
            print(f"  {katalog_id}: {konfig['datei']} nicht gefunden, uebersprungen")
            return None
    else:
        pfad = CORE / f"{katalog_id}.json"
        if not pfad.exists():
            # Kataloge mit Editions-Suffix (usage_profiles.2018-09) haben eigene Namen.
            treffer = sorted(CORE.glob(f"{katalog_id}*.json"))
            if not treffer:
                print(f"  {katalog_id}: nicht gefunden, uebersprungen")
                return None
            pfad = treffer[0]

    katalog = json.loads(pfad.read_text(encoding="utf-8"))
    werte: dict = {"entries": {}}
    entwertet = 0

    for eintrag in katalog.get(liste, []):
        code = eintrag.get(schluessel)
        if not code:
            continue
        gesammelt = {}
        for feld in konfig["entries"]:
            wert = hole(eintrag, feld)
            if wert is not None:
                gesammelt[feld] = wert
                setze(eintrag, feld, None)
                entwertet += 1
        if gesammelt:
            werte["entries"][code] = gesammelt

    for top, liste, feld in konfig["extra"]:
        block = katalog.get(top)
        if not isinstance(block, dict):
            continue
        gesammelt = {}
        for eintrag in block.get(liste, []):
            code = eintrag.get("code")
            if code and eintrag.get(feld) is not None:
                gesammelt[code] = {feld: eintrag[feld]}
                eintrag[feld] = None
                entwertet += 1
        if gesammelt:
            werte.setdefault(top, {})[liste] = gesammelt

    if entwertet == 0:
        print(f"  {katalog_id}: bereits entwertet, keine Aenderung")
        return None

    # Overlay wird ab jetzt zwingend gebraucht.
    dimension = katalog.get("dimension", {})
    suffix = f".{dimension['value']}" if dimension.get("value") else ""
    overlay_datei = f"catalog/values/{katalog_id}{suffix}.values.json"
    katalog["values_overlay"] = {
        "required": True,
        "expected_file": overlay_datei,
        "merge_key": schluessel,
        "missing_value_message": (
            f"Werte fuer '{katalog_id}' fehlen ({konfig['grund']}). "
            f"Overlay unter {overlay_datei} bereitstellen — aus eigener Normlizenz "
            f"oder ueber DWEapp. Ohne aufgeloeste Werte kein calc_ready."
        ),
    }
    katalog.pop("c4_hinweis", None)

    werte.update({
        "$schema_ref": "https://din18599-ifc.de/schema/v4.0/catalog-values",
        "catalog_id": katalog_id,
        "catalog_version": katalog.get("catalog_version"),
        "dimension": dimension,
        "norm_ref": katalog.get("norm_ref"),
        "_hinweis": (
            "URHEBERRECHTLICH GESCHUETZTE NORMWERTE. Nicht committen, nicht "
            "weitergeben. Gesperrt per .gitignore und scripts/check-catalog-values.sh."
        ),
    })

    ziel = REPO / overlay_datei
    print(f"  {katalog_id}: {entwertet} Werte -> {overlay_datei}")
    if dry_run:
        return None

    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(werte, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    pfad.write_text(json.dumps(katalog, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                   help="nur anzeigen, was passieren wuerde")
    args = p.parse_args()

    print("Trenne Normzahlenwerte von der Katalogstruktur"
          + (" (Probelauf)" if args.dry_run else "") + "\n")
    for katalog_id, konfig in FELDER.items():
        split(katalog_id, konfig, args.dry_run)

    if not args.dry_run:
        print("\nGegenprobe mit: bash scripts/check-catalog-values.sh --all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
