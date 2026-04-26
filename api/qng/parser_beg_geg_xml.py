"""
Parser A — BEG-GEG-Nachweis-Import.xml (deterministisch, Confidence 1.0)

Liest EVEBI-Export "BEG/GEG-LCA-Import für eLCA".
Format: LCAQs_Gebaeude XSD 2022-11-16

Alle XML-Werte sind absolute Gebäudewerte (kWh, kg CO₂-Äqu. gesamt).
Umrechnung auf [/m²NRF·a] erfolgt nach Freigabe durch den Auditor,
weil lca_nrf_m2 aus einer zweiten Quelle (eLCA XML oder Nachhaltigkeit.docx) kommt.

Plausibilitätsprüfungen gemäß QNG_IMPL_Guide §2.1:
  - GWP gesamt 5–100 kg CO₂/(m²NRFa)
  - PEne gesamt 20–250 kWh/(m²a)
"""

import xml.etree.ElementTree as ET
from typing import Any


# Mapping XML-Tag → Sidecar-Pfad (je GWP + PEne)
_PHASE_MAPPING: list[tuple[str, str, str]] = [
    ("umweltwirkung_A1_3",   "output.base.lca.gwp_a1_a3",      "output.base.lca.pene_a1_a3"),
    ("umweltwirkung_B4",     "output.base.lca.gwp_b4",          "output.base.lca.pene_b4"),
    ("umweltwirkung_B6",     "output.base.lca.gwp_b6_gesamt",   "output.base.lca.pene_b6_gesamt"),
    ("umweltwirkung_B6_1",   "output.base.lca.gwp_b6_heizung",  None),
    ("umweltwirkung_B6_2",   "output.base.lca.gwp_b6_kuehlung", None),
    ("umweltwirkung_B6_3",   "output.base.lca.gwp_b6_tww",      None),
    ("umweltwirkung_C3_4",   "output.base.lca.gwp_c3_c4",       "output.base.lca.pene_c3_c4"),
    ("umweltwirkung_D",      "output.base.lca.gwp_d",           "output.base.lca.pene_d"),
    # _ABC nur als Plausibilitätscheck gespeichert, kein offizieller Sidecar-Pfad
    ("umweltwirkung_ABC",    "_check.gwp_abc",                   "_check.pene_abc"),
]


def _float_text(element: ET.Element | None, tag: str) -> float | None:
    """Liest einen numerischen Wert aus einem Kindelement heraus."""
    if element is None:
        return None
    child = element.find(tag)
    if child is None or child.text is None:
        return None
    try:
        return float(child.text.strip())
    except ValueError:
        return None


def parse(content: bytes) -> dict[str, Any]:
    """
    Parst BEG-GEG-Nachweis-Import.xml.

    Args:
        content: XML-Dateiinhalt als Bytes

    Returns:
        {
          "kanal": "evebi_beg_geg_xml",
          "ki_extrahiert": { "sidecar_pfad": {"wert": X, "confidence": 1.0}, ... },
          "ki_confidence": 1.0,
          "warnungen": [str],
        }
    """
    root = ET.fromstring(content)

    # Erkennung: Root-Element muss LCAQs_Gebaeude sein
    local_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if local_tag != "LCAQs_Gebaeude":
        raise ValueError(f"Unerwartetes Root-Element: {local_tag!r}. Erwartet: LCAQs_Gebaeude")

    ki_extrahiert: dict[str, dict[str, Any]] = {}
    warnungen: list[str] = []

    # Phasenwerte auslesen
    for xml_tag, gwp_pfad, pene_pfad in _PHASE_MAPPING:
        el = root.find(xml_tag)
        if el is None:
            continue

        gwp_val = _float_text(el, "gwp")
        pene_val = _float_text(el, "pene")

        if gwp_val is not None:
            ki_extrahiert[gwp_pfad] = {"wert": gwp_val, "confidence": 1.0}
        if pene_val is not None and pene_pfad is not None:
            ki_extrahiert[pene_pfad] = {"wert": pene_val, "confidence": 1.0}

    # PV-Ertrag
    pv_el = root.find("ertragErneuerbar")
    if pv_el is not None and pv_el.text:
        try:
            ki_extrahiert["input.electricity.pv_ertrag_kwh_a"] = {
                "wert": float(pv_el.text.strip()),
                "confidence": 1.0,
            }
        except ValueError:
            pass

    # QNG-Anforderungswerte (Benchmarks aus der Datei selbst)
    anf_el = root.find("anforderungswerte")
    if anf_el is not None:
        anf_gwp = _float_text(anf_el, "gwp")
        anf_pene = _float_text(anf_el, "pene")
        if anf_gwp is not None:
            ki_extrahiert["_check.qng_anforderung_gwp"] = {"wert": anf_gwp, "confidence": 1.0}
        if anf_pene is not None:
            ki_extrahiert["_check.qng_anforderung_pene"] = {"wert": anf_pene, "confidence": 1.0}

    # Plausibilitätsprüfungen (auf Absolutwerte — noch ohne NRF-Division)
    # Hinweis: Grenzwerte beziehen sich auf /m²NRFa — hier absolut, deshalb nur grobe Prüfung
    gwp_abc = ki_extrahiert.get("_check.gwp_abc", {}).get("wert")
    pene_abc = ki_extrahiert.get("_check.pene_abc", {}).get("wert")

    if gwp_abc is not None and gwp_abc <= 0:
        warnungen.append(f"GWP-Gesamtwert ({gwp_abc}) ist ≤ 0 — Datei prüfen")
    if pene_abc is not None and pene_abc <= 0:
        warnungen.append(f"PEne-Gesamtwert ({pene_abc}) ist ≤ 0 — Datei prüfen")

    # Interne Check-Pfade nicht in ki_extrahiert exportieren
    ki_final = {k: v for k, v in ki_extrahiert.items() if not k.startswith("_check.")}

    return {
        "kanal": "evebi_beg_geg_xml",
        "ki_extrahiert": ki_final,
        "ki_confidence": 1.0,
        "warnungen": warnungen,
    }
