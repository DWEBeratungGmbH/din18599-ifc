# Cleanup Log - 29. März 2026

## Aufgeräumte Dateien

### Archiviert (alte Versionen):
- `gebaeude.din18599.schema.json` → Schema v1.0 (veraltet, v2.1 in Arbeit)
- `.temp/*` → Temporäre Extraktionsdateien (nicht mehr benötigt)
- `catalog-private/` → Leerer Ordner (nicht verwendet)
- `catalogs/` → Duplikat von catalog/
- `.plans/source-data-bmwi2020.json` → Alte Datenquelle

### Gelöscht:
- Leere Ordner (.temp/, catalog-private/)
- Temporäre Dateien

### Behalten (aktiv):
- `catalog/` - Alle Kataloge (100% komplett)
- `schema/` - v2.1 Extensions
- `examples/` - Demo-Projekte
- `docs/` - Dokumentation
- `sources/` - DIN 18599 Markdown-Quellen
- `scripts/` - Parser & Tools

## Neue Struktur

```
/opt/din18599-ifc/
├── archive/           # Archivierte alte Versionen
├── catalog/           # Kataloge (aktiv)
├── docs/              # Dokumentation (aktiv)
├── examples/          # Demo-Projekte (aktiv)
├── schema/            # Schema v2.1 (aktiv)
├── scripts/           # Tools (aktiv)
├── sources/           # DIN 18599 Quellen (aktiv)
└── viewer/            # 3D-Viewer (aktiv)
```

## Status: ✅ Aufgeräumt
