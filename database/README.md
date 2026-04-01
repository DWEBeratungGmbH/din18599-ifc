# DIN 18599 Sidecar - Database Layer

PostgreSQL database layer für das DIN 18599 Sidecar Format mit Import/Export Parsern.

## 📋 Features

- ✅ **PostgreSQL Schema** mit JSONB-Speicherung
- ✅ **Versionierung** - Mehrere Versionen pro Projekt
- ✅ **Import/Export Parser** - JSON ↔ Database
- ✅ **CLI Tool** - Einfache Kommandozeilen-Nutzung
- ✅ **Schema v2.1 Support** - BuildingElements, Parent-Child, neue Felder
- ✅ **Validierung** - Automatische Struktur-Prüfung
- ✅ **GIN Indizes** - Schnelle Queries auf JSONB
- ✅ **Helper Functions** - SQL-Funktionen für häufige Queries

---

## 🚀 Quick Start

### 1. Installation

```bash
cd database
npm install
```

### 2. Database Setup

```bash
# PostgreSQL Schema erstellen
psql -U postgres -d din18599 -f schema.sql

# Migration auf v2.1 ausführen
psql -U postgres -d din18599 -f migrations/001_schema_v2.1.sql
```

### 3. Environment Variables

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=din18599
export DB_USER=postgres
export DB_PASSWORD=your-password
```

### 4. CLI nutzen

```bash
# TypeScript kompilieren
npm run build

# Projekt erstellen
npx din18599 create "EFH Musterhausen" ../viewer/public/demo/efh-demo.din18599.json

# Projekte auflisten
npx din18599 list

# Export
npx din18599 export --current <project-id> ./output.json
```

---

## 📚 CLI Commands

### Import

```bash
# JSON in bestehendes Projekt importieren
din18599 import <project-id> <json-file> [--version-name "Name"]

# Beispiel
din18599 import abc-123 ./demo.json --version-name "Sanierung WDVS"
```

### Export

```bash
# Spezifische Version exportieren
din18599 export <sidecar-id> <output-file>

# Aktuelle Version exportieren
din18599 export --current <project-id> <output-file>

# Beispiel
din18599 export --current abc-123 ./export.din18599.json
```

### Create

```bash
# Neues Projekt mit initialem Sidecar
din18599 create <project-name> <json-file> [--description "..."]

# Beispiel
din18599 create "EFH 1978" ./demo.json --description "Einfamilienhaus Baujahr 1978"
```

### List

```bash
# Alle Projekte auflisten
din18599 list
```

---

## 🔧 Programmatic Usage

### Import

```typescript
import { Pool } from 'pg'
import { importSidecar } from './parsers/import'
import demoData from './demo.json'

const pool = new Pool({ /* config */ })

const result = await importSidecar(
  pool,
  'project-id',
  demoData,
  {
    versionName: 'Version 1.0',
    setCurrent: true,
    userId: 'user-id'
  }
)

if (result.success) {
  console.log('Sidecar ID:', result.sidecarId)
}
```

### Export

```typescript
import { exportCurrentSidecar } from './parsers/export'

const result = await exportCurrentSidecar(pool, 'project-id')

if (result.success) {
  console.log('Data:', result.data)
  console.log('Metadata:', result.metadata)
}
```

---

## 🗄️ Database Schema

### Tabellen

#### `din18599.projects`
Projekt-Metadaten (Name, IFC-Referenz, etc.)

#### `din18599.sidecars`
Versionierte Sidecar-JSONs (JSONB-Speicherung)

**Wichtige Spalten:**
- `data` - Vollständiges Sidecar JSON (JSONB)
- `schema_version` - DIN 18599 Schema Version (2.0, 2.1, etc.)
- `version` - Versions-Nummer (1, 2, 3, ...)
- `is_current` - Aktuelle Version (Boolean)
- `data_hash` - SHA-256 Hash für Änderungserkennung

#### `din18599.catalogs`
Kataloge (Bundesanzeiger, Custom)

#### `din18599.audit_log`
Audit-Trail für alle Änderungen

---

## 📊 Helper Functions

### `get_building_elements(project_id)`

Extrahiert alle BuildingElements aus dem aktuellen Sidecar:

```sql
SELECT * FROM din18599.get_building_elements('abc-123');
```

### `get_openings_with_parent(project_id)`

Extrahiert alle Öffnungen mit Parent-Referenz:

```sql
SELECT * FROM din18599.get_openings_with_parent('abc-123');
```

### `get_scenarios(project_id)`

Extrahiert alle Sanierungsszenarien:

```sql
SELECT * FROM din18599.get_scenarios('abc-123');
```

---

## 🔍 Views

### `v_projects_overview`

Übersicht aller Projekte mit Statistiken:

```sql
SELECT * FROM din18599.v_projects_overview;
```

**Spalten:**
- `project_id`, `project_name`
- `schema_version`, `lod`, `mode`
- `zone_count`, `building_element_count`, `scenario_count`
- `has_zones`, `has_building_elements`, `has_scenarios`

---

## 🧪 Testing

### Roundtrip Test

```bash
# Import
din18599 import test-project ./demo.json

# Export
din18599 export --current test-project ./export.json

# Vergleich
diff demo.json export.json
```

### Validierung

```typescript
import { validateSidecarStructure } from './parsers/import'

const errors = validateSidecarStructure(jsonData)

if (errors.length > 0) {
  console.error('Validation errors:', errors)
}
```

---

## 📈 Performance

### GIN Indizes

Schnelle Queries auf JSONB-Felder:

```sql
-- Alle Projekte mit BuildingElements
SELECT * FROM din18599.sidecars
WHERE data->'input' ? 'building_elements';

-- Alle Projekte mit Szenarien
SELECT * FROM din18599.sidecars
WHERE data ? 'scenarios';

-- Fenster in Südwand suchen
SELECT * FROM din18599.sidecars
WHERE data->'input'->'envelope'->'openings' @> '[{"parent_element_id": "wall_sued"}]';
```

### Benchmarks

- **Import:** ~200ms für 360 Zeilen JSON
- **Export:** ~50ms
- **Query (GIN Index):** ~5ms

---

## 🔐 Security

### SQL Injection Prevention

Alle Queries nutzen **Prepared Statements** mit Parametern:

```typescript
// ✅ SICHER
await pool.query('SELECT * FROM projects WHERE id = $1', [projectId])

// ❌ UNSICHER (niemals so!)
await pool.query(`SELECT * FROM projects WHERE id = '${projectId}'`)
```

### Validierung

Automatische Struktur-Validierung via PostgreSQL Constraint:

```sql
ALTER TABLE din18599.sidecars
ADD CONSTRAINT sidecars_data_valid 
CHECK (din18599.validate_sidecar_schema(data));
```

---

## 🐛 Troubleshooting

### Migration schlägt fehl

```bash
# Constraint entfernen (falls Probleme)
psql -d din18599 -c "ALTER TABLE din18599.sidecars DROP CONSTRAINT IF EXISTS sidecars_data_valid;"

# Migration erneut ausführen
psql -d din18599 -f migrations/001_schema_v2.1.sql
```

### Import schlägt fehl

```bash
# Validierung überspringen
din18599 import <project-id> <json-file> --skip-validation
```

### TypeScript Errors

```bash
# Dependencies installieren
npm install

# Types generieren
npm run build
```

---

## 📝 Migration Guide

### v2.0 → v2.1

Die Migration ist **non-destructive** und abwärtskompatibel:

1. Neue Spalte `schema_version` wird hinzugefügt
2. Bestehende Daten bleiben unverändert
3. Neue GIN Indizes für Performance
4. Helper Functions für neue Felder

**Keine Breaking Changes!**

---

## 🤝 Integration mit DWEapp

Die Database-Layer ist **standalone** und kann später in DWEapp integriert werden:

```typescript
// In DWEapp Server Actions
import { importSidecar } from '@din18599/database/parsers/import'

export async function importDin18599(projectId: string, jsonData: any) {
  const result = await importSidecar(pool, projectId, jsonData)
  return result
}
```

**Wichtig:** DWEapp-Integration erfolgt separat - dieser Layer ist unabhängig!

---

## 📚 Weitere Dokumentation

- [Schema v2.1 Specification](../.plans/schema-v2.1-final.md)
- [Database Integration Plan](../.plans/database-integration-plan.md)
- [PostgreSQL Schema](./schema.sql)
- [Migration Script](./migrations/001_schema_v2.1.sql)

---

## ✅ Status

- [x] PostgreSQL Schema v2.1
- [x] Import Parser
- [x] Export Parser
- [x] CLI Tool
- [x] Helper Functions
- [x] Views
- [x] Dokumentation
- [ ] Unit Tests (TODO)
- [ ] Integration Tests (TODO)
- [ ] DWEapp Integration (später)

---

## 📄 License

Apache 2.0 - siehe [LICENSE](../LICENSE)

**Autor:** DWE Beratung GmbH  
**Repository:** https://github.com/DWEBeratungGmbH/din18599-ifc
