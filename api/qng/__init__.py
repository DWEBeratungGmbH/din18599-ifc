"""QNG/external-import orchestration — Phase 3.9 Welle 3.

The package dispatches format-specific import adapters. EVEBI handlers are one
optional adapter among several and are not part of the neutral Sidecar API.

Architektur:
  - Deterministisch (Confidence 1.0): BEG-GEG XML, idi-al.ini, eLCA XML
  - KI-unterstützt (Confidence < 1.0): Nachhaltigkeit DOCX (Ollama)
  - Optional: IFC (wenn Datei vorhanden)

Alle Parser geben eine ParseResult-Struktur zurück:
  {
    "kanal":        EingangKanal-Enum-String,
    "ki_extrahiert": { "sidecar.pfad": {"wert": X, "confidence": 1.0} },
    "ki_confidence": float,           # niedrigster Einzelwert
    "warnungen":    [str],             # Plausibilitätswarnungen
  }
"""
from .orchestrator import orchestrate, ParseResult

__all__ = ["orchestrate", "ParseResult"]
