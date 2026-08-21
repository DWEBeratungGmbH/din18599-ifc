"""
upload_utils.py — Zentrale, sichere Upload-Verarbeitung fuer die DIN 18599 API.

Bisher duplizierte jeder Endpunkt die gleiche Logik fuer Endungspruefung,
temporäre Ablage und Fehlermeldung — und zwar uneinheitlich: manche prüften
case-sensitiv (`.ifc` lehnte `.IFC` ab), keiner hatte ein Groessenlimit, und
Dateinamen flossen direkt in ``Path(temp_dir) / file.filename`` ein, was bei
``../``- oder absoluten Namen zu Pfad-Traversal fuehrt.

Dieses Modul kapselt die gemeinsamen Regeln als reine Funktionen, sodass sie
ohne FastAPI/TestClient mit stdlib allein pruefbar sind (das Projekt setzt
kein pytest/httpx voraus — siehe ``tools/test_*.py``).

Vorgehen pro Upload:

  1. ``pruefe_dateiname``   — Endung case-insensitiv, Name sanitisiert.
  2. ``schreibe_temporaer`` — Bytes in eine numerierte Temporaerdatei im
                              vorgegebenen Verzeichnis schreiben; niemals
                              den Originalnamamen als Pfadkomponente verwenden.
  3. ``lese_upload``        — Bytes lesen, Groesse begrenzen, Inhalt pruefen.

Alle Schritte werfen ``UploadError`` mit HTTP-tauglichem ``status_code`` und
``detail`` (keine internen Pfade, keine Stacktraces) — die Endpunkte wandeln
das direkt in ``HTTPException`` um.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# Default-Limit 50 MB. Bewusst konservativ: IFC-Dateien in der Praxis sind
# selten ueber 20 MB, EVEBI-Archive liegen im einstelligen MB-Bereich. Wer
# groessere Dateien braucht, setzt UPLOAD_MAX_BYTES hoeher (Umgebungsvariable
# koennte spaeter ergaenzt werden — vorerst Konstante, kein Config-Boom).
DEFAULT_MAX_BYTES = 50 * 1024 * 1024


@dataclass
class UploadError(Exception):
    """Fehler beim Upload, direkt in HTTPException uebersetzbar."""
    status_code: int
    detail: str

    def __str__(self) -> str:  # fuer Tests / Logs ohne interne Pfade
        return f"[{self.status_code}] {self.detail}"


def _erlaubte_endung(filename: str | None, erlaubt: Iterable[str]) -> str | None:
    """Kleingeschriebene Endung inklusive Punkt, oder None."""
    if not filename:
        return None
    name = Path(filename).name  # streift Pfade ab, auch bei "a/b.ifc"
    for ext in erlaubt:
        if name.lower().endswith(ext.lower()):
            return ext.lower()
    return None


def pruefe_dateiname(
    filename: str | None,
    erlaubt: Iterable[str],
    *,  # keine variablen Default-Endungen verbergen
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """
    Validiert einen Upload-Dateinamen und liefert die bereinigte Endung.

    ``erlaubt`` enthaelt die zulaessigen Endungen MIT fuehrendem Punkt
    (z.B. ``[".ifc"]``); Gross-/Kleinschreibung wird ignoriert. Ein leerer
    oder fehlender Name, eine unzulaessige Endung und ein Dateiname, der
    nach dem Strippen des Pfades leer waere, werden als 400 abgewiesen.

    ``max_bytes`` ist hier nur deklariert, damit Endpunkte und Tests eine
    einzige Quelle der Wahrheit nutzen; die eigentliche Groessenpruefung
    erfolgt in :func:`lese_upload`, weil dort die Bytes vorliegen.
    """
    erlaubt_list = list(erlaubt)
    if not filename:
        raise UploadError(400, "Dateiname fehlt")
    name = Path(filename).name
    if not name or name in (".", ".."):
        raise UploadError(400, "Dateiname ist leer oder nur ein Pfad")
    # Ein Name, der nur aus der Endung besteht (".ifc"), hat keinen Stamm —
    # solche Uploads sind in der Praxis immer kaputt und erzeugen im Helper
    # einen sicheren Namen OHNE erkennbare Provenienz. Frueher abweisen.
    # pathlib behandelt ".ifc" als Name ohne Endung, deshalb explizit pruefen.
    if name.startswith(".") and "." not in name[1:]:
        raise UploadError(400, "Dateiname hat keinen Namensteil vor der Endung")
    ext = _erlaubte_endung(filename, erlaubt_list)
    if ext is None:
        raise UploadError(
            400,
            f"Datei muss eine der Endungen haben: {', '.join(erlaubt_list)}",
        )
    return ext


def lese_upload(
    inhalt: bytes,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    leer_verboten: bool = True,
) -> bytes:
    """
    Prueft die gelesenen Bytes auf Groesse und (optional) Leere.

    Wird AFTER ``await file.read()`` aufgerufen — FastAPI puffert die Datei
    bereits, aber ohne Limit. Dieses Limit ist die einzige Stelle, an der
    die Groesse vor der Verarbeitung geprueft wird.
    """
    if leer_verboten and not inhalt:
        raise UploadError(400, "Datei ist leer (0 Bytes)")
    if len(inhalt) > max_bytes:
        raise UploadError(
            413,
            f"Datei ist {len(inhalt)} Bytes gross, zulaessig sind "
            f"{max_bytes} Bytes",
        )
    return inhalt


def schreibe_temporaer(
    inhalt: bytes,
    *,
    ziel_verzeichnis: Path,
    endung: str,
    prefix: str = "upload",
) -> Path:
    """
    Schreibt Bytes in eine numerierte Temporaerdatei.

    Der Originaldateiname wird NICHT verwendet — er ist Eingabedaten und
    duerfte Pfade enthalten (``../``) oder Leerzeichen/Sonderzeichen, die
    Shells oder nachgelagerte Parser falsch interpretieren. Statt dessen
    erhaelt die Datei die gepruefte Endung und einen eindeutigen Namen.
    """
    if not ziel_verzeichnis.exists():
        raise UploadError(500, "Temporaerverzeichnis nicht vorhanden")
    # numeriert, atomar innerhalb dieses Verzeichnisses; Collision-Schutz
    # ueber existierende Dateien, kein zufaelliger Anteil noetig.
    n = 0
    while True:
        kandidat = ziel_verzeichnis / f"{prefix}_{n:06d}{endung}"
        if not kandidat.exists():
            kandidat.write_bytes(inhalt)
            return kandidat
        n += 1
        if n > 1_000_000:  # paranoia, nie in Praxis erreicht
            raise UploadError(500, "Konnte keinen Temporaerdateinamen erzeugen")


def verarbeite_upload(
    *,
    filename: str | None,
    inhalt: bytes,
    erlaubt: Iterable[str],
    ziel_verzeichnis: Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
    leer_verboten: bool = True,
    prefix: str = "upload",
) -> tuple[Path, str]:
    """
    End-to-End-Helfer: Name pruefen, Bytes pruefen, temporaer ablegen.

    Liefert (Pfad der Temporaerdatei, Originaldateiname-fuer-Logging).

    Die Endpunkte rufen dies einmal pro Upload; der Originaldateiname wird
    NICHT als Pfad weitergereicht, sondern nur fuer Provenienz/Logs.
    """
    pruefe_dateiname(filename, erlaubt, max_bytes=max_bytes)
    bytes_ok = lese_upload(inhalt, max_bytes=max_bytes, leer_verboten=leer_verboten)
    endung = _erlaubte_endung(filename, erlaubt) or ""
    pfad = schreibe_temporaer(
        bytes_ok,
        ziel_verzeichnis=ziel_verzeichnis,
        endung=endung,
        prefix=prefix,
    )
    return pfad, filename or "unbekannt"
