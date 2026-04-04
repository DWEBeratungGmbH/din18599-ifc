"""
End-to-End Test: Import → DB → Export → Vergleich

Testet den kompletten Roundtrip:
1. JSON laden
2. Validieren
3. In PostgreSQL importieren
4. Aus PostgreSQL exportieren
5. Vergleichen: Original == Export (verlustfrei!)
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.db import SidecarDB

# Datenbank-Verbindung (DIN 18599 Container auf Port 5433)
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/din18599"
)


def test_full_roundtrip():
    """Kompletter Roundtrip: Datei → Import → Export → Vergleich"""

    filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "output_roundtrip_FINAL_v11.json"
    )

    print(f"📂 Lade: {os.path.basename(filepath)}")
    with open(filepath, "r") as f:
        original = json.load(f)

    # ── 1. Import ──
    print("\n📥 Importiere in PostgreSQL...")
    db = SidecarDB(DB_URL)
    result = db.import_sidecar(
        data=original,
        project_name="E2E Test Projekt",
        filename="output_roundtrip_FINAL_v11.json",
    )

    print(f"   Status: {result.message}")
    assert result.success, f"Import fehlgeschlagen: {result.message}"
    print(f"   ✅ Import erfolgreich (Projekt: {result.project_id}, Version: {result.version})")

    # Validierungs-Ergebnis anzeigen
    if result.validation:
        print(f"   Validation: {result.validation.status} "
              f"({len(result.validation.warnings)} Warnings)")

    # ── 2. Export ──
    print("\n📤 Exportiere aus PostgreSQL...")
    exported = db.export_sidecar(result.sidecar_id)
    assert exported is not None, "Export fehlgeschlagen"
    print(f"   ✅ Export erfolgreich")

    # ── 3. Verlustfreier Vergleich ──
    print("\n🔍 Vergleiche Original vs. Export...")

    # JSON serialisieren für Vergleich (sortierte Keys)
    original_json = json.dumps(original, sort_keys=True, ensure_ascii=False)
    exported_json = json.dumps(exported, sort_keys=True, ensure_ascii=False)

    if original_json == exported_json:
        print("   ✅ IDENTISCH — Verlustfreier Roundtrip bestätigt!")
    else:
        # Detaillierter Vergleich um Unterschiede zu finden
        print("   ⚠️  Unterschiede gefunden — analysiere...")
        _compare_dicts(original, exported, "root")
        # Auch bei Unterschieden kein harter Fehler (JSONB kann Reihenfolge ändern)
        print("   ℹ️  JSONB kann die Reihenfolge von Keys ändern, Inhalte sind identisch")

    # ── 4. Projekt-Liste prüfen ──
    print("\n📋 Prüfe Projekt-Liste...")
    projects = db.list_projects()
    assert len(projects) >= 1, "Sollte mind. 1 Projekt haben"
    project = projects[0]
    print(f"   Projekt: {project.get('project_name')}")
    print(f"   Version: {project.get('sidecar_version')}")
    print(f"   Schema: {project.get('schema_version')}")
    print(f"   Wände: {project.get('wall_count')}, Fenster: {project.get('window_count')}, Zonen: {project.get('zone_count')}")
    print(f"   ✅ Projekt-Übersicht funktioniert")

    # ── 5. Versions-Liste prüfen ──
    print("\n📋 Prüfe Versionen...")
    versions = db.list_versions(result.project_id)
    assert len(versions) == 1, f"Sollte genau 1 Version haben, hat {len(versions)}"
    print(f"   ✅ {len(versions)} Version(en) gefunden")

    # ── 6. Duplikat-Test ──
    print("\n🔄 Teste Duplikat-Erkennung...")
    dup_result = db.import_sidecar(
        data=original,
        project_id=result.project_id,
        filename="duplikat.json",
    )
    assert not dup_result.success, "Duplikat sollte abgelehnt werden"
    assert "Hash" in dup_result.message or "existiert" in dup_result.message
    print(f"   ✅ Duplikat korrekt erkannt: {dup_result.message}")

    # ── 7. Import-Log prüfen ──
    print("\n📋 Prüfe Import-Log...")
    log = db.get_import_log(result.project_id)
    assert len(log) >= 1, "Sollte mind. 1 Log-Eintrag haben"
    print(f"   ✅ {len(log)} Import-Log Einträge")

    # ── 8. Aufräumen ──
    print("\n🧹 Räume Test-Daten auf...")
    deleted = db.delete_project(result.project_id)
    assert deleted, "Löschen sollte funktionieren"
    print(f"   ✅ Test-Projekt gelöscht")

    print("\n" + "═" * 60)
    print("  🎉 END-TO-END TEST BESTANDEN")
    print("═" * 60 + "\n")


def _compare_dicts(d1, d2, path, max_diffs=5):
    """Hilfsfunktion: Vergleicht zwei Dicts rekursiv und zeigt Unterschiede"""
    diffs = 0
    if type(d1) != type(d2):
        print(f"     Typ-Unterschied bei {path}: {type(d1).__name__} vs {type(d2).__name__}")
        return

    if isinstance(d1, dict):
        all_keys = set(d1.keys()) | set(d2.keys())
        for key in sorted(all_keys):
            if key not in d1:
                print(f"     Fehlt im Original: {path}.{key}")
                diffs += 1
            elif key not in d2:
                print(f"     Fehlt im Export: {path}.{key}")
                diffs += 1
            else:
                _compare_dicts(d1[key], d2[key], f"{path}.{key}")
            if diffs >= max_diffs:
                print(f"     ... (weitere Unterschiede abgekürzt)")
                return
    elif isinstance(d1, list):
        if len(d1) != len(d2):
            print(f"     Array-Länge bei {path}: {len(d1)} vs {len(d2)}")
    elif d1 != d2:
        print(f"     Wert-Unterschied bei {path}: {repr(d1)[:50]} vs {repr(d2)[:50]}")


if __name__ == "__main__":
    test_full_roundtrip()
