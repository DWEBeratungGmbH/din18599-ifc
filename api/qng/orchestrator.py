"""External import orchestrator — automatic format detection and dispatch.

Reihenfolge der Erkennungsregeln (load-bearing — deterministisch zuerst):
  1. BEG-GEG XML:          Inhalt enthält b'LCAQs_Gebaeude'
  2. eLCA XML:              Inhalt enthält b'bauteileditor' oder b'elca' (Namespace)
  3. idi-al.ini:            Inhalt enthält b'HS_Energieberater' oder Endung .ini
  4. Nachhaltigkeit DOCX:   Endung .docx (+ optional Namens-Heuristik)
  5. IFC:                   Endung .ifc (nur Metadaten, kein LCA-Wert)
"""

from dataclasses import dataclass, field
from typing import Any

from . import parser_beg_geg_xml, parser_idi_al_ini, parser_elca_xml, parser_nachhaltigkeit_docx


@dataclass
class ParseResult:
    """Ergebnis einer Orchestrator-Analyse."""
    kanal: str
    ki_extrahiert: dict[str, dict[str, Any]]
    ki_confidence: float
    warnungen: list[str] = field(default_factory=list)
    # Nur bei eLCA: Bauteilkatalog für SB 3.3.1
    bauteilkatalog: list[dict[str, Any]] | None = None
    # True wenn Werte direkt in Sidecar übernommen werden können (Confidence = 1.0)
    direkt_freigabe: bool = False

    @property
    def adapter(self) -> str:
        """Neutral adapter identity; ``kanal`` remains a legacy detail."""
        if self.kanal.startswith("evebi_"):
            return "adapter:evebi"
        if self.kanal == "ifc":
            return "adapter:ifc"
        return "adapter:external-import"

    @property
    def source_format(self) -> str:
        """Stable neutral format identity for API consumers."""
        if self.kanal.startswith("evebi_"):
            return self.kanal.removeprefix("evebi_")
        return self.kanal


def _is_xml(content: bytes) -> bool:
    """Grobe XML-Erkennung via BOM / Prolog."""
    stripped = content.lstrip()
    return stripped.startswith(b"<?xml") or stripped.startswith(b"<")


def _is_zip(content: bytes) -> bool:
    """ZIP-Signatur: PK\x03\x04."""
    return content[:4] == b"PK\x03\x04"


def orchestrate(content: bytes, filename: str) -> ParseResult:
    """
    Erkennt den Dateityp automatisch und dispatcht an den richtigen Parser.

    Args:
        content:  Roher Dateiinhalt als Bytes
        filename: Originaler Dateiname (für Endungs-Fallback)

    Returns:
        ParseResult mit ki_extrahiert + Metadaten

    Raises:
        ValueError: Wenn Dateiformat nicht erkannt wird
    """
    fname = filename.lower()
    warnungen: list[str] = []

    # ── Erkennung 1: BEG-GEG XML ──────────────────────────────────────────────
    if _is_xml(content) and b"LCAQs_Gebaeude" in content:
        raw = parser_beg_geg_xml.parse(content)
        return ParseResult(
            kanal          = raw["kanal"],
            ki_extrahiert  = raw["ki_extrahiert"],
            ki_confidence  = raw["ki_confidence"],
            warnungen      = raw["warnungen"],
            direkt_freigabe = raw["ki_confidence"] >= 1.0,
        )

    # ── Erkennung 2: eLCA XML ─────────────────────────────────────────────────
    if _is_xml(content) and (b"bauteileditor" in content.lower() or b"elca" in content[:2000].lower()):
        raw = parser_elca_xml.parse(content)
        return ParseResult(
            kanal           = raw["kanal"],
            ki_extrahiert   = raw["ki_extrahiert"],
            ki_confidence   = raw["ki_confidence"],
            warnungen       = raw["warnungen"],
            bauteilkatalog  = raw.get("bauteilkatalog"),
            direkt_freigabe = raw["ki_confidence"] >= 1.0,
        )

    # ── Erkennung 3: idi-al.ini ───────────────────────────────────────────────
    if b"HS_Energieberater" in content or b"hs_energieberater" in content.lower() or fname.endswith(".ini"):
        raw = parser_idi_al_ini.parse(content)
        return ParseResult(
            kanal           = raw["kanal"],
            ki_extrahiert   = raw["ki_extrahiert"],
            ki_confidence   = raw["ki_confidence"],
            warnungen       = raw["warnungen"],
            direkt_freigabe = raw["ki_confidence"] >= 1.0,
        )

    # ── Erkennung 4: DOCX ─────────────────────────────────────────────────────
    if _is_zip(content) and fname.endswith(".docx"):
        raw = parser_nachhaltigkeit_docx.parse(content)
        return ParseResult(
            kanal           = raw["kanal"],
            ki_extrahiert   = raw["ki_extrahiert"],
            ki_confidence   = raw["ki_confidence"],
            warnungen       = raw["warnungen"],
            direkt_freigabe = False,  # DOCX immer in Warteliste
        )

    # ── Erkennung 5: IFC (nur Dateiendung, kein LCA-Parser) ──────────────────
    if fname.endswith(".ifc"):
        warnungen.append(
            "IFC-Datei erkannt. IFC-Parser extrahiert keine LCA-Werte — "
            "nur Gebäudegeometrie (BGF, NRF, Orientierung)."
        )
        return ParseResult(
            kanal           = "ifc",
            ki_extrahiert   = {},
            ki_confidence   = 0.0,
            warnungen       = warnungen,
            direkt_freigabe = False,
        )

    # ── Fallback: nicht erkannt ───────────────────────────────────────────────
    raise ValueError(
        f"Dateiformat nicht erkannt: {filename!r}. "
        "Unterstützt: BEG-GEG XML, eLCA XML, idi-al.ini, Nachhaltigkeit.docx, .ifc"
    )
