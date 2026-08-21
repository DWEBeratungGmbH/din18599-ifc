#!/usr/bin/env python3
"""
test_upload_utils.py — Negativtests fuer die zentrale Upload-Verarbeitung.

Jede Sicherheitsregel bekommt einen gezielt boesen Input und muss anschlagen:
Pfad-Traversal, Gross-/Kleinschreibung, leere Datei, uebergrosse Datei,
unzulaessige Endung, fehlender Name. Zusaetzlich die Gegenprobe, dass
gueltige Uploads durchkommen (kein Falsch-Positiv).

Aufruf:
    python3 tools/test_upload_utils.py

Ohne pytest/httpx (nicht im Projekt vorhanden) — reine stdlib, wie die
uebrigen tools/test_*.py-Harnesses. Siehe CLAUDE.md und Plan Phase 1.4.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from upload_utils import (  # noqa: E402
    DEFAULT_MAX_BYTES,
    UploadError,
    lese_upload,
    pruefe_dateiname,
    schreibe_temporaer,
    verarbeite_upload,
)


def _nah(a, b, toleranz=0.0):
    return a is not None and abs(a - b) <= toleranz


def main() -> int:
    fehler = 0

    def pruefe(name: str, bedingung: bool, detail: str = "") -> None:
        nonlocal fehler
        fehler += 0 if bedingung else 1
        print(f"{name:60} {'PASS' if bedingung else 'FAIL'}  {detail}")

    def erwartet_upload_error(fn, *args, code, **kwargs):
        """Ruft fn auf und liefert True, wenn UploadError mit code geworfen wurde."""
        try:
            fn(*args, **kwargs)
        except UploadError as e:
            return e.status_code == code, str(e)
        return False, "kein UploadError"

    # --- 1. pruefe_dateiname: gueltig ----------------------------------------
    pruefe("gueltig: '.ifc' wird akzeptiert",
           pruefe_dateiname("haus.ifc", [".ifc"]) == ".ifc")
    pruefe("case-insensitiv: '.IFC' wird akzeptiert",
           pruefe_dateiname("HAUS.IFC", [".ifc"]) == ".ifc")
    pruefe("case-insensitiv: '.EVEA'",
           pruefe_dateiname("a.EVEA", [".evea", ".evex"]) == ".evea")

    # --- 2. pruefe_dateiname: boese -----------------------------------------
    ok, detail = erwartet_upload_error(
        pruefe_dateiname, None, [".ifc"], code=400)
    pruefe("None-Name -> 400", ok, detail)
    ok, detail = erwartet_upload_error(
        pruefe_dateiname, "", [".ifc"], code=400)
    pruefe("leerer Name -> 400", ok, detail)
    ok, detail = erwartet_upload_error(
        pruefe_dateiname, "haus.txt", [".ifc"], code=400)
    pruefe("unzulaessige Endung -> 400", ok, detail)
    ok, detail = erwartet_upload_error(
        pruefe_dateiname, ".ifc", [".ifc"], code=400)
    pruefe("nur-Endung ohne Basis -> 400", ok, detail)

    # --- 3. Pfad-Traversal wird unschaedlich --------------------------------
    # pruefe_dateiname laesst den Namen zu (er hat .ifc-Endung); schreibe_
    # temporaer ignoriert den Originalnamamen komplett und erzeugt einen
    # sicheren numerierten Namen. Traversal duerfte NIE eine Datei ausserhalb
    # des Temp-Verzeichnisses erzeugen.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Ein boeser Name mit Pfadkomponenten — frueher: Path(tmp)/file.filename
        pfad, _ = verarbeite_upload(
            filename="../../../etc/passwd.ifc",
            inhalt=b"IFC-DUMMY",
            erlaubt=[".ifc"],
            ziel_verzeichnis=tmp_path,
        )
        # Datei muss INNERHALB von tmp_path liegen — nicht im uebergeordneten
        innerhalb = pfad.resolve().is_relative_to(tmp_path.resolve())
        pruefe("Traversal: Datei liegt im Temp-Verzeichnis", innerhalb,
               str(pfad))
        pruefe("Traversal: Dateiname enthaelt keine '../'",
               "../" not in pfad.name and "passwd" not in pfad.name, pfad.name)

    # --- 4. lese_upload: leere Datei ----------------------------------------
    ok, detail = erwartet_upload_error(lese_upload, b"", code=400)
    pruefe("leere Datei -> 400", ok, detail)

    # --- 5. lese_upload: uebergross -----------------------------------------
    zu_gross = b"x" * (DEFAULT_MAX_BYTES + 1)
    ok, detail = erwartet_upload_error(lese_upload, zu_gross, code=413)
    pruefe("uebergrosse Datei -> 413", ok, detail)

    # --- 6. lese_upload: genau am Limit -------------------------------------
    genau = b"x" * DEFAULT_MAX_BYTES
    try:
        lese_upload(genau)
        pruefe("genau am Limit wird akzeptiert", True)
    except UploadError as e:
        pruefe("genau am Limit wird akzeptiert", False, str(e))

    # --- 7. schreibe_temporaer: sichere Namen, keine Kollisionen -----------
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        p1 = schreibe_temporaer(b"a", ziel_verzeichnis=tmp_path, endung=".ifc")
        p2 = schreibe_temporaer(b"b", ziel_verzeichnis=tmp_path, endung=".ifc")
        pruefe("zwei Uploads bekommen unterschiedliche Dateien",
               p1 != p2, f"{p1.name} vs {p2.name}")
        pruefe("erzeugter Name enthaelt Originalendung",
               p1.suffix == ".ifc", p1.name)
        pruefe("kein Originalnamensteil uebrig",
               p1.name.startswith("upload_"), p1.name)

    # --- 8. verarbeite_upload: Endung trennt IFC von EVEBI ------------------
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        ok, detail = erwartet_upload_error(
            verarbeite_upload, code=400,
            filename="bild.png", inhalt=b"x", erlaubt=[".ifc"],
            ziel_verzeichnis=tmp_path)
        pruefe("PNG wird als IFC abgelehnt", ok, detail)

    # --- 9. Gross-/Kleinschreibung des Dateinamens endet korrekt -----------
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pfad, _ = verarbeite_upload(
            filename="DACH.IFC",
            inhalt=b"IFC",
            erlaubt=[".ifc"],
            ziel_verzeichnis=tmp_path,
        )
        pruefe(".IFC wird mit .ifc-Endung abgelegt",
               pfad.suffix == ".ifc", pfad.name)

    print()
    if fehler:
        print(f"FAIL: {fehler} Test(s) fehlgeschlagen")
        return 1
    print("PASS: alle Upload-Regeln ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
