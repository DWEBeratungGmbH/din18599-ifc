# DIN 18599 Schema v2.1 → DWEapp Database Integration

**Datum:** 1. April 2026  
**Priorität:** HOCH (vor Viewer-MVP Fertigstellung)  
**Ziel:** DIN 18599 Schema als Master - DWEapp passt sich an

---

## 🎯 Überblick

**Problem:**
- DIN 18599 Schema v2.1 ist komplett (TypeScript + JSON)
- PostgreSQL Schema ist noch auf v2.0
- DWEapp Prisma Schema kennt neue Felder nicht
- Kein Parser für Import/Export

**Lösung:**
- PostgreSQL Schema erweitern (JSONB-basiert)
- Prisma Schema anpassen
- Parser bauen (JSON ↔ DB)
- Migration Script für bestehende Daten

---

## 📋 Neue Felder in Schema v2.1

### 1. Envelope (Gebäudehülle)
**Neue Felder:**
- `thermal_bridge_type` (DEFAULT | REDUCED | DETAILED)
- `thermal_bridge_delta_u` (number)
- `solar_absorption` (number, 0-1)
- `characteristic_dimension_b` (number, für Fx-Faktor)
- `perimeter` (number, für Böden)

**Parent-Child:**
- `parent_element_id` (string)
- `parent_element_type` (WALL_EXT | ROOF | etc.)

### 2. Openings (Öffnungen)
**Neue Felder:**
- `u_value_glass` (Ug)
- `u_value_frame` (Uf)
- `g_value` (Gesamtenergiedurchlassgrad)
- `frame_fraction` (Rahmenanteil)
- `psi_spacer` (Ψ-Wert Abstandhalter)
- `shading_factor_fs` (Verschattungsfaktor)
- `solar_gain_factor` (optional)

### 3. BuildingElements (LOD 300+)
**Komplett neu:**
```typescript
{
  id: string
  type: "STAIR" | "OPENING" | "CORRECTION" | "MANUAL"
  name: string
  source: "IFC" | "CORRECTION" | "MANUAL"
  geometry: {
    location: [x, y, z]
    dimensions: { width, depth, height, area, volume }
  }
  affects_zones: [{ zone_id, area_delta, volume_delta }]
  affects_elements: [{ element_id, element_type, area_delta }]
  thermal?: { is_inside_envelope, boundary_condition, u_value }
  description?: string
  reason?: string
}
```

### 4. Scenarios (Szenarien)
**Erweitert:**
- `measures` Array mit Maßnahmen
- `costs` (total, funding, net)
- `output` mit Einsparungen (energy_savings, co2_savings, cost_savings)

---

## 🗄️ PostgreSQL Schema Anpassungen

### Aktueller Stand
```sql
CREATE TABLE din18599.sidecars (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    version INT NOT NULL,
    data JSONB NOT NULL,  -- ← Hier liegt alles drin
    ...
);
```

**✅ Vorteil:** JSONB ist flexibel, Schema v2.1 passt bereits rein!

### Erforderliche Änderungen

#### 1. Schema-Version Tracking
```sql
ALTER TABLE din18599.sidecars 
ADD COLUMN schema_version VARCHAR(10) DEFAULT '2.1';

COMMENT ON COLUMN din18599.sidecars.schema_version IS 'DIN 18599 Schema Version (2.0, 2.1, etc.)';
```

#### 2. GIN Index für neue Felder
```sql
-- Index für BuildingElements Queries
CREATE INDEX idx_sidecars_building_elements 
ON din18599.sidecars USING GIN ((data->'input'->'building_elements'));

-- Index für Scenarios
CREATE INDEX idx_sidecars_scenarios 
ON din18599.sidecars USING GIN ((data->'scenarios'));

-- Index für Envelope
CREATE INDEX idx_sidecars_envelope 
ON din18599.sidecars USING GIN ((data->'input'->'envelope'));
```

#### 3. Validierungs-Funktion (optional)
```sql
CREATE OR REPLACE FUNCTION din18599.validate_sidecar_schema(data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Prüfe ob meta.schema_version existiert
    IF NOT (data ? 'meta' AND data->'meta' ? 'schema_version') THEN
        RAISE EXCEPTION 'Missing meta.schema_version';
    END IF;
    
    -- Prüfe ob input existiert
    IF NOT (data ? 'input') THEN
        RAISE EXCEPTION 'Missing input section';
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Constraint hinzufügen
ALTER TABLE din18599.sidecars
ADD CONSTRAINT sidecars_data_valid 
CHECK (din18599.validate_sidecar_schema(data));
```

---

## 🔧 Prisma Schema Anpassungen

### Aktuelles Prisma Schema (DWEapp)
```prisma
// Vermutlich noch nicht vorhanden - muss neu erstellt werden
model Din18599Sidecar {
  id            String   @id @default(uuid()) @db.Uuid
  projectId     String   @db.Uuid
  version       Int
  versionName   String?  @db.VarChar(100)
  isCurrent     Boolean  @default(false)
  
  lod           String?  @db.VarChar(10)
  mode          String?  @db.VarChar(20)
  
  data          Json     @db.JsonB
  dataHash      String?  @db.VarChar(64)
  schemaVersion String   @default("2.1") @db.VarChar(10)
  
  createdAt     DateTime @default(now()) @db.Timestamptz(6)
  createdBy     String?  @db.Uuid
  deletedAt     DateTime? @db.Timestamptz(6)
  
  project       Project  @relation(fields: [projectId], references: [id], onDelete: Cascade)
  
  @@unique([projectId, version])
  @@index([projectId, isCurrent])
  @@map("sidecars")
  @@schema("din18599")
}

model Din18599Project {
  id              String   @id @default(uuid()) @db.Uuid
  name            String   @db.VarChar(255)
  description     String?  @db.Text
  
  ifcFilePath     String?  @db.Text
  ifcGuidBuilding String?  @db.Uuid
  
  createdAt       DateTime @default(now()) @db.Timestamptz(6)
  updatedAt       DateTime @updatedAt @db.Timestamptz(6)
  createdBy       String?  @db.Uuid
  updatedBy       String?  @db.Uuid
  deletedAt       DateTime? @db.Timestamptz(6)
  
  sidecars        Din18599Sidecar[]
  
  @@index([createdAt])
  @@map("projects")
  @@schema("din18599")
}
```

---

## 🔄 Parser Implementation

### 1. Import Parser (JSON → DB)

**Datei:** `/opt/din18599-ifc/database/parsers/import.ts`

```typescript
import { PrismaClient } from '@prisma/client'
import { DIN18599Data } from '../../viewer/src/types/din18599'
import crypto from 'crypto'

const prisma = new PrismaClient()

export async function importSidecar(
  projectId: string,
  jsonData: DIN18599Data,
  options: {
    versionName?: string
    setCurrent?: boolean
    userId?: string
  } = {}
): Promise<string> {
  // 1. Validierung
  if (!jsonData.meta?.schema_version) {
    throw new Error('Missing meta.schema_version')
  }
  
  if (!jsonData.input) {
    throw new Error('Missing input section')
  }
  
  // 2. Hash berechnen
  const dataHash = crypto
    .createHash('sha256')
    .update(JSON.stringify(jsonData))
    .digest('hex')
  
  // 3. Nächste Version ermitteln
  const lastVersion = await prisma.din18599Sidecar.findFirst({
    where: { projectId },
    orderBy: { version: 'desc' }
  })
  
  const nextVersion = (lastVersion?.version || 0) + 1
  
  // 4. Sidecar erstellen
  const sidecar = await prisma.din18599Sidecar.create({
    data: {
      projectId,
      version: nextVersion,
      versionName: options.versionName || `Version ${nextVersion}`,
      isCurrent: options.setCurrent ?? true,
      lod: jsonData.meta.lod || '200',
      mode: jsonData.meta.mode || 'STANDALONE',
      data: jsonData as any, // JSONB
      dataHash,
      schemaVersion: jsonData.meta.schema_version,
      createdBy: options.userId
    }
  })
  
  return sidecar.id
}
```

### 2. Export Parser (DB → JSON)

**Datei:** `/opt/din18599-ifc/database/parsers/export.ts`

```typescript
import { PrismaClient } from '@prisma/client'
import { DIN18599Data } from '../../viewer/src/types/din18599'

const prisma = new PrismaClient()

export async function exportSidecar(
  sidecarId: string
): Promise<DIN18599Data> {
  const sidecar = await prisma.din18599Sidecar.findUnique({
    where: { id: sidecarId }
  })
  
  if (!sidecar) {
    throw new Error(`Sidecar ${sidecarId} not found`)
  }
  
  // JSONB → TypeScript Type
  return sidecar.data as DIN18599Data
}

export async function exportCurrentSidecar(
  projectId: string
): Promise<DIN18599Data> {
  const sidecar = await prisma.din18599Sidecar.findFirst({
    where: { 
      projectId,
      isCurrent: true,
      deletedAt: null
    }
  })
  
  if (!sidecar) {
    throw new Error(`No current sidecar for project ${projectId}`)
  }
  
  return sidecar.data as DIN18599Data
}
```

### 3. Validator

**Datei:** `/opt/din18599-ifc/database/parsers/validate.ts`

```typescript
import { DIN18599Data } from '../../viewer/src/types/din18599'

export interface ValidationError {
  path: string
  message: string
  severity: 'error' | 'warning'
}

export function validateSidecar(data: DIN18599Data): ValidationError[] {
  const errors: ValidationError[] = []
  
  // Meta validieren
  if (!data.meta?.schema_version) {
    errors.push({
      path: 'meta.schema_version',
      message: 'Missing schema version',
      severity: 'error'
    })
  }
  
  // Input validieren
  if (!data.input) {
    errors.push({
      path: 'input',
      message: 'Missing input section',
      severity: 'error'
    })
  }
  
  // Zones validieren
  if (data.input?.zones) {
    data.input.zones.forEach((zone, idx) => {
      if (!zone.id) {
        errors.push({
          path: `input.zones[${idx}].id`,
          message: 'Missing zone ID',
          severity: 'error'
        })
      }
      
      if (!zone.area_an || zone.area_an <= 0) {
        errors.push({
          path: `input.zones[${idx}].area_an`,
          message: 'Invalid area_an (must be > 0)',
          severity: 'error'
        })
      }
    })
  }
  
  // Envelope validieren
  if (data.input?.envelope) {
    const { walls_external, openings } = data.input.envelope
    
    // Parent-Child Beziehungen prüfen
    if (openings) {
      openings.forEach((opening, idx) => {
        if (opening.parent_element_id) {
          const parentExists = walls_external?.some(w => w.id === opening.parent_element_id)
          if (!parentExists) {
            errors.push({
              path: `input.envelope.openings[${idx}].parent_element_id`,
              message: `Parent element ${opening.parent_element_id} not found`,
              severity: 'warning'
            })
          }
        }
      })
    }
  }
  
  // BuildingElements validieren
  if (data.input?.building_elements) {
    data.input.building_elements.forEach((elem, idx) => {
      if (!elem.id || !elem.type) {
        errors.push({
          path: `input.building_elements[${idx}]`,
          message: 'Missing id or type',
          severity: 'error'
        })
      }
      
      // Affects_zones validieren
      if (elem.affects_zones) {
        elem.affects_zones.forEach((zone, zIdx) => {
          if (!zone.zone_id) {
            errors.push({
              path: `input.building_elements[${idx}].affects_zones[${zIdx}].zone_id`,
              message: 'Missing zone_id',
              severity: 'error'
            })
          }
        })
      }
    })
  }
  
  return errors
}
```

---

## 🚀 Migration Script

**Datei:** `/opt/din18599-ifc/database/migrations/001_schema_v2.1.sql`

```sql
-- ============================================================================
-- Migration: Schema v2.0 → v2.1
-- ============================================================================

BEGIN;

-- 1. Schema-Version Spalte hinzufügen
ALTER TABLE din18599.sidecars 
ADD COLUMN IF NOT EXISTS schema_version VARCHAR(10) DEFAULT '2.0';

COMMENT ON COLUMN din18599.sidecars.schema_version IS 'DIN 18599 Schema Version';

-- 2. Bestehende Daten auf v2.0 setzen
UPDATE din18599.sidecars 
SET schema_version = '2.0'
WHERE schema_version IS NULL;

-- 3. GIN Indizes für neue Felder
CREATE INDEX IF NOT EXISTS idx_sidecars_building_elements 
ON din18599.sidecars USING GIN ((data->'input'->'building_elements'));

CREATE INDEX IF NOT EXISTS idx_sidecars_scenarios 
ON din18599.sidecars USING GIN ((data->'scenarios'));

CREATE INDEX IF NOT EXISTS idx_sidecars_envelope 
ON din18599.sidecars USING GIN ((data->'input'->'envelope'));

-- 4. Validierungs-Funktion
CREATE OR REPLACE FUNCTION din18599.validate_sidecar_schema(data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    IF NOT (data ? 'meta' AND data->'meta' ? 'schema_version') THEN
        RAISE EXCEPTION 'Missing meta.schema_version';
    END IF;
    
    IF NOT (data ? 'input') THEN
        RAISE EXCEPTION 'Missing input section';
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 5. Constraint hinzufügen (nur für neue Einträge)
ALTER TABLE din18599.sidecars
ADD CONSTRAINT sidecars_data_valid 
CHECK (din18599.validate_sidecar_schema(data));

COMMIT;
```

---

## 📦 Server Actions für DWEapp

**Datei:** `/opt/weclapp-manager/src/app/actions/din18599.ts`

```typescript
'use server'

import { prisma } from '@/lib/prisma'
import { requireAuth } from '@/lib/auth'
import { importSidecar, exportSidecar, exportCurrentSidecar } from '@/lib/din18599/parsers'
import { validateSidecar } from '@/lib/din18599/validate'
import { DIN18599Data } from '@/types/din18599'

export async function createDin18599Project(data: {
  name: string
  description?: string
  ifcFilePath?: string
}) {
  const session = await requireAuth()
  
  const project = await prisma.din18599Project.create({
    data: {
      ...data,
      createdBy: session.user.id
    }
  })
  
  return { success: true, projectId: project.id }
}

export async function importDin18599Sidecar(
  projectId: string,
  jsonData: DIN18599Data,
  versionName?: string
) {
  const session = await requireAuth()
  
  // Validierung
  const errors = validateSidecar(jsonData)
  const criticalErrors = errors.filter(e => e.severity === 'error')
  
  if (criticalErrors.length > 0) {
    return { 
      success: false, 
      errors: criticalErrors 
    }
  }
  
  // Import
  const sidecarId = await importSidecar(projectId, jsonData, {
    versionName,
    setCurrent: true,
    userId: session.user.id
  })
  
  return { 
    success: true, 
    sidecarId,
    warnings: errors.filter(e => e.severity === 'warning')
  }
}

export async function exportDin18599Sidecar(sidecarId: string) {
  await requireAuth()
  
  const data = await exportSidecar(sidecarId)
  
  return { success: true, data }
}

export async function getDin18599Projects() {
  await requireAuth()
  
  const projects = await prisma.din18599Project.findMany({
    where: { deletedAt: null },
    include: {
      sidecars: {
        where: { 
          isCurrent: true,
          deletedAt: null 
        },
        take: 1
      }
    },
    orderBy: { updatedAt: 'desc' }
  })
  
  return { success: true, projects }
}
```

---

## ✅ Testing Strategy

### 1. Unit Tests
```typescript
// __tests__/parsers/import.test.ts
import { importSidecar } from '@/lib/din18599/parsers/import'
import { prisma } from '@/lib/prisma'

describe('importSidecar', () => {
  it('should import valid sidecar', async () => {
    const jsonData = {
      meta: { schema_version: '2.1', ... },
      input: { ... }
    }
    
    const sidecarId = await importSidecar('project-id', jsonData)
    
    expect(sidecarId).toBeDefined()
    
    const sidecar = await prisma.din18599Sidecar.findUnique({
      where: { id: sidecarId }
    })
    
    expect(sidecar?.schemaVersion).toBe('2.1')
  })
  
  it('should reject invalid sidecar', async () => {
    const jsonData = { meta: {} } // Missing schema_version
    
    await expect(
      importSidecar('project-id', jsonData as any)
    ).rejects.toThrow('Missing meta.schema_version')
  })
})
```

### 2. Integration Tests
```typescript
// __tests__/integration/roundtrip.test.ts
import { importSidecar, exportSidecar } from '@/lib/din18599/parsers'
import demoData from '@/fixtures/efh-demo.din18599.json'

describe('Import/Export Roundtrip', () => {
  it('should preserve data integrity', async () => {
    // Import
    const sidecarId = await importSidecar('test-project', demoData)
    
    // Export
    const exported = await exportSidecar(sidecarId)
    
    // Compare
    expect(exported.meta.schema_version).toBe(demoData.meta.schema_version)
    expect(exported.input.zones).toEqual(demoData.input.zones)
    expect(exported.input.building_elements).toEqual(demoData.input.building_elements)
  })
})
```

---

## 📋 Implementierungs-Reihenfolge

### Phase 1: PostgreSQL Schema (30 Min)
1. ✅ Migration Script erstellen
2. ✅ Auf Dev-DB ausführen
3. ✅ Indizes testen

### Phase 2: Prisma Schema (20 Min)
1. ✅ Model erstellen
2. ✅ `prisma generate` ausführen
3. ✅ Types prüfen

### Phase 3: Parser (1-2h)
1. ✅ Import Parser
2. ✅ Export Parser
3. ✅ Validator
4. ✅ Unit Tests

### Phase 4: Server Actions (1h)
1. ✅ CRUD Actions
2. ✅ Auth Guards
3. ✅ Error Handling

### Phase 5: Testing (30 Min)
1. ✅ Roundtrip Test
2. ✅ Validation Test
3. ✅ Performance Test

---

## 🎯 Success Criteria

- [ ] PostgreSQL Migration erfolgreich
- [ ] Prisma Schema generiert ohne Fehler
- [ ] Import/Export Roundtrip funktioniert
- [ ] Validation erkennt Fehler
- [ ] Demo-JSON kann importiert werden
- [ ] Exported JSON ist identisch mit Original
- [ ] Performance: Import <500ms, Export <100ms
- [ ] Tests: 100% Coverage für Parser

---

## 📚 Dokumentation

Nach Implementierung:
- [ ] README.md aktualisieren (Database Section)
- [ ] API-Docs für Server Actions
- [ ] Migration Guide für bestehende Daten
- [ ] Beispiel-Code für Import/Export

---

**Status:** 🔄 IN ARBEIT  
**Nächster Schritt:** PostgreSQL Migration Script erstellen
