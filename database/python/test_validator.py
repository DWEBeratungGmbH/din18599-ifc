"""
Test-Script: Validator + Metadaten-Extraktion gegen echte Daten.

Testet den kompletten Validierungs-Flow ohne Datenbank-Verbindung.
"""

import json
import sys
import os

# Pfad zum Modul hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.validator import SidecarValidator, extract_metadata


def test_roundtrip_file():
    """Testet gegen die echte Roundtrip-Datei"""

    filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "output_roundtrip_FINAL_v11.json"
    )

    print(f"📂 Lade: {os.path.basename(filepath)}")
    with open(filepath, "r") as f:
        data = json.load(f)

    # ── 1. Validierung ──
    print("\n🔍 Starte 3-Ebenen-Validierung...")
    validator = SidecarValidator()
    result = validator.validate(data)
    result.print_summary()

    # ── 2. Metadaten-Extraktion ──
    print("📊 Extrahierte Metadaten:")
    meta = extract_metadata(data)
    for key, value in meta.items():
        icon = "✅" if value else "⚠️ "
        print(f"   {icon} {key}: {value}")

    # ── 3. Assertions ──
    print("\n🧪 Assertions:")

    # Muss importierbar sein (keine Errors)
    assert result.valid, f"Sidecar sollte valide sein, hat aber {len(result.errors)} Fehler"
    print("   ✅ Sidecar ist importierbar (keine Errors)")

    # Sollte Warnings haben (bekannte Probleme)
    assert len(result.warnings) > 0, "Sollte Warnings haben"
    print(f"   ✅ {len(result.warnings)} Warnings gefunden (erwartet)")

    # Metadaten müssen extrahiert werden
    assert meta["wall_count"] > 0, "Sollte Wände haben"
    assert meta["window_count"] > 0, "Sollte Fenster haben"
    assert meta["zone_count"] > 0, "Sollte Zonen haben"
    print(f"   ✅ Statistiken: {meta['wall_count']} Wände, {meta['window_count']} Fenster, {meta['zone_count']} Zonen")

    # Schema-Version muss vorhanden sein
    assert meta["schema_version"] is not None, "Schema-Version fehlt"
    print(f"   ✅ Schema-Version: {meta['schema_version']}")

    print("\n🎉 Alle Tests bestanden!\n")


def test_minimal_sidecar():
    """Testet mit einem minimalen Sidecar (LOD 100)"""
    print("\n" + "═" * 60)
    print("  Test 2: Minimales Sidecar (LOD 100)")
    print("═" * 60)

    data = {
        "schema_info": {"url": "https://din18599-ifc.de/schema/v2.3/complete", "version": "2.3.0"},
        "meta": {"project_name": "Test Minimal", "created": "2026-04-04T10:00:00Z", "lod": "100"},
        "input": {
            "building": {
                "address": {"zip": "10115", "city": "Berlin"},
                "construction_year": 1975,
                "heated_area": 120.0
            }
        }
    }

    validator = SidecarValidator()
    result = validator.validate(data)
    result.print_summary()

    assert result.valid, "Minimales Sidecar muss valide sein"
    print("   ✅ Minimales Sidecar ist importierbar")

    meta = extract_metadata(data)
    assert meta["lod"] == "100"
    assert meta["construction_year"] == 1975
    print(f"   ✅ LOD: {meta['lod']}, Baujahr: {meta['construction_year']}")


def test_broken_sidecar():
    """Testet mit einem kaputten Sidecar (sollte Fehler produzieren)"""
    print("\n" + "═" * 60)
    print("  Test 3: Kaputtes Sidecar (Fehler erwartet)")
    print("═" * 60)

    # Kein input-Block → muss Fehler sein
    data = {
        "meta": {"project_name": "Kaputt"},
    }

    validator = SidecarValidator()
    result = validator.validate(data)
    result.print_summary()

    assert not result.valid, "Kaputtes Sidecar muss als FAILED gelten"
    assert len(result.errors) > 0, "Muss mindestens einen Fehler haben"
    print(f"   ✅ Korrekt abgelehnt: {len(result.errors)} Fehler")


def test_bad_references():
    """Testet mit falschen Referenzen"""
    print("\n" + "═" * 60)
    print("  Test 4: Falsche Referenzen")
    print("═" * 60)

    data = {
        "schema_info": {"version": "2.3.0"},
        "meta": {"project_name": "Ref-Test"},
        "input": {
            "building": {
                "zones": [{"id": "zone_1", "area": 50}],
                "rooms": [{"id": "room_1", "name": "Wohnzimmer", "area": 20, "zone_ref": "zone_GIBTS_NICHT"}],
            },
            "envelope": {
                "walls": [{
                    "id": "wall_1", "area": 15.0, "u_value": 1.4,
                    "construction_ref": "konstr_GIBTS_NICHT"
                }],
            },
            "constructions": [{"id": "konstr_1", "name": "Außenwand"}],
        }
    }

    validator = SidecarValidator()
    result = validator.validate(data)
    result.print_summary()

    # Referenz-Fehler sollten als Error (zone_ref) oder Warning (construction_ref) kommen
    ref_messages = [m for m in result.errors + result.warnings if m.level == "reference"]
    assert len(ref_messages) >= 2, f"Sollte mind. 2 Referenz-Probleme finden, hat {len(ref_messages)}"
    print(f"   ✅ {len(ref_messages)} Referenz-Probleme korrekt erkannt")


if __name__ == "__main__":
    test_roundtrip_file()
    test_minimal_sidecar()
    test_broken_sidecar()
    test_bad_references()

    print("\n" + "═" * 60)
    print("  🎉 ALLE 4 TESTS BESTANDEN")
    print("═" * 60 + "\n")
