"""
Parser B — idi-al.ini (deterministisch, Confidence 1.0)

Format: Windows INI, Encoding latin-1.
Erkennung: [Kennung]-Sektion mit Programmkennung=HS_Energieberater

Extrahiert Energiebedarfswerte aus EVEBI-Berechnungsdokumentation.
Feldnamen können je EVEBI-Version leicht variieren — alternative Keys
werden der Reihe nach probiert (erster Treffer gewinnt).
"""

import configparser
import io
from typing import Any


# Alternative Schlüsselnamen je EVEBI-Version (erster Treffer gewinnt)
_PRIMAERENERGIE_KEYS = ["Primaerenergiebedarf", "Primärenergiebedarf", "PrimaerenergiebKf"]
_ENDENERGIE_KEYS     = ["Endenergiebedarf", "Endenergiebedarf_gesamt"]
_CO2_KEYS            = ["CO2_Emissionen", "CO2Emissionen", "CO2_Aequivalent"]
_BEZUGSFLAECHE_KEYS  = ["Bezugsflaeche", "Bezugsfläche", "BehGebFlaeche", "EbfGebaeude"]


def _first_key(section: configparser.SectionProxy, candidates: list[str]) -> float | None:
    """Gibt den Wert des ersten gefundenen Schlüssels als float zurück."""
    for key in candidates:
        # configparser normalisiert Keys zu lowercase
        v = section.get(key.lower())
        if v is not None:
            try:
                return float(v.replace(",", ".").strip())
            except ValueError:
                pass
    return None


def parse(content: bytes) -> dict[str, Any]:
    """
    Parst idi-al.ini (EVEBI Energiebedarfsausweis).

    Args:
        content: INI-Dateiinhalt als Bytes (latin-1 encodiert)

    Returns:
        {
          "kanal": "evebi_idi_al_ini",
          "ki_extrahiert": { "sidecar_pfad": {"wert": X, "confidence": 1.0}, ... },
          "ki_confidence": 1.0,
          "warnungen": [str],
        }
    """
    # latin-1 ist EVEBI Standard für Windows-INI-Exporte
    text = content.decode("latin-1", errors="replace")

    cfg = configparser.ConfigParser()
    cfg.read_file(io.StringIO(text))

    warnungen: list[str] = []

    # Erkennung: [Kennung] Sektion muss HS_Energieberater enthalten
    if cfg.has_section("kennung"):
        kennung = cfg.get("kennung", "programmkennung", fallback="")
        if "hs_energieberater" not in kennung.lower():
            warnungen.append(
                f"Unbekannte Programmkennung: {kennung!r}. Parser könnte falsche Feldnamen verwenden."
            )
    else:
        raise ValueError("Keine [Kennung]-Sektion gefunden — kein idi-al.ini-Format")

    ki_extrahiert: dict[str, dict[str, Any]] = {}

    # Ergebnis-Sektion
    if cfg.has_section("ergebnis"):
        sek = cfg["ergebnis"]
        primaer = _first_key(sek, _PRIMAERENERGIE_KEYS)
        if primaer is not None:
            ki_extrahiert["output.base.specific_values.primary_energy.total"] = {
                "wert": primaer, "confidence": 1.0,
            }
        else:
            warnungen.append("Primärenergiebedarf nicht gefunden in [Ergebnis]")

        endenergie = _first_key(sek, _ENDENERGIE_KEYS)
        if endenergie is not None:
            ki_extrahiert["output.base.specific_values.final_energy.total"] = {
                "wert": endenergie, "confidence": 1.0,
            }

        co2 = _first_key(sek, _CO2_KEYS)
        if co2 is not None:
            ki_extrahiert["output.base.specific_values.co2_emissions.total"] = {
                "wert": co2, "confidence": 1.0,
            }
    else:
        warnungen.append("[Ergebnis]-Sektion fehlt")

    # Gebäude-Sektion (Flächen)
    for sekname in ("gebaeude", "gebaude"):
        if cfg.has_section(sekname):
            sek = cfg[sekname]
            flaeche = _first_key(sek, _BEZUGSFLAECHE_KEYS)
            if flaeche is not None:
                ki_extrahiert["input.building.heated_area"] = {
                    "wert": flaeche, "confidence": 1.0,
                }
            break
    else:
        warnungen.append("[Gebaeude]-Sektion fehlt — Bezugsfläche unbekannt")

    return {
        "kanal": "evebi_idi_al_ini",
        "ki_extrahiert": ki_extrahiert,
        "ki_confidence": 1.0,
        "warnungen": warnungen,
    }
