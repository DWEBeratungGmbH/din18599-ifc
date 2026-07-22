#!/usr/bin/env python3
"""Erzeugt schema/v4.0/paths.json — die Pfad-Whitelist des Sidecar-Schemas.

Zweck: aus der Praefix-Konvention ("abgeleitete Pfade nicht schreiben") wird
eine pruefbare Liste. Zwei Konsumenten haben denselben Semantikbedarf und
duerfen nicht auseinanderlaufen:

  - DWEapp verriegelt applyDotPath gegen diese Liste
  - der Python-Export/-Validator prueft dieselbe Frage

Deshalb liegt das Artefakt im Standard-Repo und nicht in einem der beiden
Konsumenten. Aus den TS-Typen abgeleitet wuerde es nur DWEapp abdecken und
gegen die Python-Seite driften — genau das Parser-Doppelungs-Muster, das wir
an anderer Stelle schon haben.

Die Semantik wird NICHT hier hartkodiert, sondern aus dem Schema gelesen:
`readOnly: true` (Draft-07-Standardkeyword) vererbt sich auf den ganzen
Teilbaum darunter.

Notation der Pfade:
  feld              gewoehnliche Property
  feld[]            Array-Ebene
  feld.*            offene Map (additionalProperties mit Schema)
  feld.{pattern:X}  patternProperties

Aufruf:  python3 scripts/build-paths.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PFAD = REPO / "schema" / "v4.0" / "sidecar.schema.json"
ZIEL_PFAD = REPO / "schema" / "v4.0" / "paths.json"


def sammle_pfade(schema: dict) -> list[dict]:
    """Alle gueltigen Dot-Pfade mit ihrer Schreib-Semantik.

    `kette` traegt die Namen der bereits betretenen Definitionen und bricht
    Zyklen ab (z.B. wenn eine Definition sich selbst referenziert).
    """
    defs = schema.get("definitions", {})
    gefunden: dict[str, dict] = {}

    def merke(pfad: str, readonly: bool, art: str) -> None:
        vorhanden = gefunden.get(pfad)
        if vorhanden is None:
            gefunden[pfad] = {"path": pfad, "readonly": readonly, "kind": art}
        elif not readonly:
            # Derselbe Pfad kann ueber mehrere Aeste erreichbar sein. Ist er
            # irgendwo schreibbar, gilt er als schreibbar — sonst wuerde ein
            # zufaelliger Traversierungsweg ueber die Semantik entscheiden.
            vorhanden["readonly"] = False

    def gehe(knoten: dict, pfad: str, readonly: bool, kette: tuple) -> None:
        if not isinstance(knoten, dict):
            return

        ref = knoten.get("$ref")
        if ref:
            name = ref.rsplit("/", 1)[-1]
            if name in kette:
                return
            gehe(defs.get(name, {}), pfad, readonly, kette + (name,))
            return

        # readOnly vererbt sich nach unten und wird nie zurueckgenommen.
        readonly = readonly or bool(knoten.get("readOnly"))

        for schluessel, unter in (knoten.get("properties") or {}).items():
            neu = f"{pfad}.{schluessel}" if pfad else schluessel
            unter_ro = readonly or bool(
                isinstance(unter, dict) and unter.get("readOnly"))
            merke(neu, unter_ro, "property")
            gehe(unter, neu, readonly, kette)

        for muster, unter in (knoten.get("patternProperties") or {}).items():
            neu = f"{pfad}.{{pattern:{muster}}}" if pfad else f"{{pattern:{muster}}}"
            merke(neu, readonly, "pattern_map")
            gehe(unter, neu, readonly, kette)

        # Offene Map: additionalProperties traegt ein Schema (nicht True/False).
        # Ohne diesen Zweig fehlten legitime Ziele wie
        # input.primary_energy_factors.factors.<energietraeger> in der Liste,
        # und eine strikte Verriegelung wuerde gueltige Schreibvorgaenge
        # blockieren.
        zusatz = knoten.get("additionalProperties")
        if isinstance(zusatz, dict) and zusatz:
            neu = f"{pfad}.*" if pfad else "*"
            merke(neu, readonly, "open_map")
            gehe(zusatz, neu, readonly, kette)

        items = knoten.get("items")
        if isinstance(items, dict):
            neu = f"{pfad}[]"
            merke(neu, readonly, "array_item")
            gehe(items, neu, readonly, kette)

        for kombi in ("allOf", "anyOf", "oneOf"):
            for unter in knoten.get(kombi) or []:
                gehe(unter, pfad, readonly, kette)

    gehe(schema, "", False, ())
    return [gefunden[p] for p in sorted(gefunden)]


def baue_artefakt() -> dict:
    schema = json.loads(SCHEMA_PFAD.read_text(encoding="utf-8"))
    pfade = sammle_pfade(schema)
    return {
        "generated_by": "scripts/build-paths.py",
        "schema_id": schema.get("$id"),
        "schema_version": schema.get("version"),
        "notation": {
            "[]": "Array-Ebene",
            ".*": "offene Map (additionalProperties mit Schema)",
            ".{pattern:X}": "patternProperties, X ist der Regex",
        },
        "readonly_hinweis": (
            "readonly=true kommt aus readOnly im Schema und vererbt sich auf "
            "den Teilbaum. Solche Pfade duerfen gelesen, aber nicht "
            "geschrieben werden — sie werden beim Export neu berechnet."
        ),
        "count": len(pfade),
        "paths": pfade,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true",
                   help="Nur pruefen, ob das Artefakt aktuell ist (CI)")
    args = p.parse_args()

    artefakt = baue_artefakt()
    text = json.dumps(artefakt, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not ZIEL_PFAD.exists():
            print(f"FEHLER: {ZIEL_PFAD.relative_to(REPO)} fehlt — "
                  f"python3 scripts/build-paths.py laufen lassen", file=sys.stderr)
            return 1
        if ZIEL_PFAD.read_text(encoding="utf-8") != text:
            print(f"FEHLER: {ZIEL_PFAD.relative_to(REPO)} weicht vom Schema ab — "
                  f"python3 scripts/build-paths.py laufen lassen", file=sys.stderr)
            return 1
        print(f"{ZIEL_PFAD.relative_to(REPO)} ist aktuell "
              f"({artefakt['count']} Pfade)")
        return 0

    ZIEL_PFAD.write_text(text, encoding="utf-8")
    schreibbar = sum(1 for e in artefakt["paths"] if not e["readonly"])
    print(f"{ZIEL_PFAD.relative_to(REPO)}: {artefakt['count']} Pfade "
          f"({schreibbar} schreibbar, {artefakt['count'] - schreibbar} abgeleitet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
