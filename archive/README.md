# Archiv - DIN 18599 IFC Parser

Dieses Verzeichnis enthält alte Entwicklungsversionen und Dokumentation, die für die aktuelle Produktionsversion nicht mehr benötigt werden.

## Struktur

### `roundtrip_development/`
Entwicklungsversionen des Roundtrip Processors (v2-v10):
- `output_roundtrip_FINAL_v2.json` bis `v10.json` - Entwicklungs-Outputs
- `output_roundtrip_FIXED.json` - Frühe Fix-Version
- `test_parser_v3.py` - Test-Script für Parser v3
- `evebi_parser_backup.py`, `evebi_parser_old.py` - Alte EVEBI Parser Versionen
- `ifc_parser.py`, `ifc_parser_v2.py` - Alte IFC Parser Versionen
- `main_v2.py` - Alte API-Version

**Aktuelle Produktionsversion:** `output_roundtrip_FINAL_v11.json` (Roundtrip Processor v8)

### `old_docs/`
Alte Dokumentation und Reports:
- `FINAL_SUMMARY_v3.3.md` - Zusammenfassung Parser v3.3
- `MULTI_IFC_TEST_REPORT.md` - Multi-IFC Test Report
- `PARSER_V3_FINAL_REPORT.md` - Parser v3 Final Report

**Aktuelle Dokumentation:** Siehe Root-Verzeichnis (README.md, CHANGELOG.md, ROADMAP.md)

### `analysis_scripts/`
Analyse-Scripts für IFC-Dateien:
- `analyze-ifc.py` - Basis IFC-Analyse
- `analyze-roof-slabs.py` - Dach-Slab-Analyse
- `deep-analyze-ifc.py` - Tiefe IFC-Analyse
- `ifc-complete-analysis.py` - Vollständige IFC-Analyse
- `systematic-slab-analysis.py` - Systematische Slab-Analyse

**Aktuelle Tools:** Siehe `tools/` Verzeichnis

## Roundtrip Processor Entwicklung

### Meilensteine
- **v2-v4:** Initiale EVEBI-Integration, Zonen-Extraktion
- **v5:** U-Wert-Merge via DIN-Code (20/20 Wände)
- **v6:** PV vollständig + Inhomogene Schichten getrennt
- **v7:** 100% Hülle komplett (45/45 Bauteile mit U-Werten)
- **v8:** Schema-Konformität + Detailfelder (Produktionsversion)

### Aktuelle Version: v8 (v11.json)
- ✅ 45/45 Bauteile mit U-Werten (100%)
- ✅ Inhomogene Schichten getrennt (DIN EN ISO 6946-konform)
- ✅ Fenster-Konstruktionen (Schema-konform mit nested objects)
- ✅ Systeme mit Detailfeldern (Heizung, DHW, Lüftung, PV)
- ✅ Schema v2.3 vollständig konform

## Hinweise

Diese Dateien werden für historische Zwecke aufbewahrt und können bei Bedarf gelöscht werden.
Für die aktuelle Entwicklung siehe die Dateien im Root-Verzeichnis und in `api/parsers/`.
