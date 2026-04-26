"""
Parser C — eLCA XML Export (deterministisch, Confidence 1.0)

Format: XML mit Namespace https://www.bauteileditor.de/EnEV/2017
Erkennung: Namespace enthält "bauteileditor" oder "elca"

Extrahiert Flächen (BGF, NRF) und Bauteil-Metadaten aus eLCA-Export.
Bauteilkatalog KG 300/400 wird für zukünftige Holz-Auswertung (SB 3.3.1) mitgeliefert.
"""

import xml.etree.ElementTree as ET
from typing import Any


def _detect_namespace(root: ET.Element) -> str:
    """Extrahiert den Namespace-URI aus dem Root-Tag."""
    if "}" in root.tag:
        return root.tag.split("}")[0].strip("{")
    return ""


def _find_text(root: ET.Element, path: str, ns: dict[str, str]) -> str | None:
    """Sucht ein Element per XPath und gibt dessen Text zurück."""
    el = root.find(path, ns)
    return el.text.strip() if el is not None and el.text else None


def _find_float(root: ET.Element, path: str, ns: dict[str, str]) -> float | None:
    """Sucht ein Element per XPath und gibt dessen Wert als float zurück."""
    text = _find_text(root, path, ns)
    if text is None:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def parse(content: bytes) -> dict[str, Any]:
    """
    Parst eLCA XML Export.

    Args:
        content: XML-Dateiinhalt als Bytes

    Returns:
        {
          "kanal": "evebi_elca_xml",
          "ki_extrahiert": { "sidecar_pfad": {"wert": X, "confidence": 1.0}, ... },
          "ki_confidence": 1.0,
          "warnungen": [str],
          "bauteilkatalog": [{din276Code, name, flaeche_m2, schichten: [...]}, ...],
        }
    """
    root = ET.fromstring(content)

    ns_uri = _detect_namespace(root)
    # Erkennung: Namespace muss bauteileditor oder elca enthalten
    if "bauteileditor" not in ns_uri.lower() and "elca" not in ns_uri.lower():
        # Fallback: Root-Tag prüfen
        local = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if "elca" not in local.lower():
            raise ValueError(
                f"Kein eLCA-Namespace gefunden ('{ns_uri}'). Kein eLCA XML-Format."
            )

    ns = {"e": ns_uri} if ns_uri else {}
    prefix = "e:" if ns_uri else ""

    warnungen: list[str] = []
    ki_extrahiert: dict[str, dict[str, Any]] = {}

    # Flächen aus variant/construction
    bgf = _find_float(root, f".//{prefix}grossFloorSpace", ns)
    nrf = _find_float(root, f".//{prefix}netFloorSpace", ns)

    if bgf is not None:
        ki_extrahiert["input.building.gross_floor_area"] = {"wert": bgf, "confidence": 1.0}
    else:
        warnungen.append("BGF (grossFloorSpace) nicht gefunden")

    if nrf is not None:
        ki_extrahiert["input.building.heated_area"] = {"wert": nrf, "confidence": 1.0}
    else:
        warnungen.append("NRF (netFloorSpace) nicht gefunden")

    # Plausibilitätsprüfung: NRF < BGF
    if bgf is not None and nrf is not None and nrf >= bgf:
        warnungen.append(
            f"NRF ({nrf} m²) ≥ BGF ({bgf} m²) — NRF muss kleiner als BGF sein"
        )

    # Projektmetadaten
    projekt_name = _find_text(root, f".//{prefix}name", ns)
    if projekt_name:
        ki_extrahiert["_meta.projekt_name_elca"] = {"wert": projekt_name, "confidence": 1.0}

    for pfad, sidecar in [
        (f".//{prefix}street",   "meta.address.street"),
        (f".//{prefix}postcode", "meta.address.postcode"),
        (f".//{prefix}city",     "meta.address.city"),
    ]:
        val = _find_text(root, pfad, ns)
        if val:
            ki_extrahiert[sidecar] = {"wert": val, "confidence": 1.0}

    # Bauteilkatalog KG 300/400 (für SB 3.3.1 Holz-Auswertung)
    bauteilkatalog: list[dict[str, Any]] = []
    for el in root.iter(f"{{{ns_uri}}}element" if ns_uri else "element"):
        din276 = el.get("din276Code", "")
        if not din276.startswith(("3", "4")):
            continue

        name_el = el.find(f".//{prefix}n", ns) or el.find(f".//{prefix}name", ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else "Unbekannt"
        qty_str = el.get("quantity", "0")
        try:
            flaeche = float(qty_str)
        except ValueError:
            flaeche = 0.0

        schichten: list[dict[str, Any]] = []
        for comp in el.iter(f"{{{ns_uri}}}component" if ns_uri else "component"):
            if comp.get("isLayer") != "true":
                continue
            schichten.append({
                "material": comp.get("processConfigName", ""),
                "dicke_m": float(comp.get("layerSize", 0) or 0),
                "flaechen_anteil": float(comp.get("layerAreaRatio", 1) or 1),
                "din276": comp.get("din276Code", din276),
            })

        bauteilkatalog.append({
            "din276Code": din276,
            "name": name,
            "flaeche_m2": flaeche,
            "schichten": schichten,
        })

    result: dict[str, Any] = {
        "kanal": "evebi_elca_xml",
        "ki_extrahiert": ki_extrahiert,
        "ki_confidence": 1.0,
        "warnungen": warnungen,
    }
    if bauteilkatalog:
        result["bauteilkatalog"] = bauteilkatalog

    return result
