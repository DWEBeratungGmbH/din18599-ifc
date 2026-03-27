# Architektur & Datenmodell

**Projekt:** IFC + DIN 18599 Sidecar  
**Version:** 2.0  
**Stand:** März 2026

---

## 1. Systemarchitektur (Überblick)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Anwendungsebene                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ BIM-Software │  │ Energiesoft- │  │ Viewer/Editor│          │
│  │ (Revit, AC)  │  │ ware (PHPP)  │  │ (Web-App)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Austauschschicht                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  IFC-Datei (Geometrie)        +  Sidecar JSON (Physik)   │  │
│  │  - IfcBuilding, IfcSpace      |  - Zonen, U-Werte        │  │
│  │  - IfcWall, IfcWindow         |  - Systeme, LOD          │  │
│  │  - Koordinaten, Flächen       |  - Varianten, Kataloge   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                                      │
          ↓                                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Validierungsebene                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ IFC-Validator│  │ JSON-Schema  │  │ GUID-Checker │          │
│  │ (IfcOpenShell│  │ (jsonschema) │  │ (Custom)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
          │                                      │
          ↓                                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Berechnungsebene                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DIN 18599 Rechenkern (Software-spezifisch)              │  │
│  │  - Energiebedarf                                         │  │
│  │  - Primärenergie                                         │  │
│  │  - Effizienzklassen                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-Architektur (Detailliert)

### Layer 1: Datenschicht (Data Layer)

**Verantwortung:** Persistierung und Austausch von Daten

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Data Layer                                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  IFC-Datei       │         │  Sidecar JSON    │             │
│  │  (ISO 16739)     │         │  (Custom Schema) │             │
│  ├──────────────────┤         ├──────────────────┤             │
│  │ • Geometrie      │         │ • Zonen          │             │
│  │ • Topologie      │         │ • U-Werte        │             │
│  │ • GUIDs          │         │ • Systeme        │             │
│  │ • Räume          │         │ • LOD            │             │
│  │ • Bauteile       │         │ • Varianten      │             │
│  └──────────────────┘         └──────────────────┘             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Kataloge (JSON)                                         │  │
│  │  - Bundesanzeiger 2020 (U-Werte nach Baujahr)           │  │
│  │  - Material-Datenbank (λ-Werte, ρ, c)                   │  │
│  │  - Ökobaudat (GWP, PEI)                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Dateiformate:**
- **IFC:** `.ifc` (ISO 16739, IFC4/IFC4.3)
- **Sidecar:** `.din18599.json` (JSON Schema Draft-07)
- **Kataloge:** `.json` (Custom Schema)

**Speicherorte:**
- **Lokal:** Dateisystem (Desktop, Netzlaufwerk)
- **Cloud:** S3, Azure Blob, OneDrive (optional)
- **Versionierung:** Git, DMS (optional)

---

### Layer 2: Schema & Validierung (Schema Layer)

**Verantwortung:** Datenintegrität und Konsistenz

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Schema & Validation Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  JSON Schema (gebaeude.din18599.schema.json)            │  │
│  │  - Struktur-Validierung (required, types)               │  │
│  │  - Enum-Validierung (boundary_condition, lod)           │  │
│  │  - Format-Validierung (uuid, date-time)                 │  │
│  │  - oneOf: Legacy vs. Varianten-Format                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Custom Validators (Python/JavaScript)                  │  │
│  │  - GUID-Existenz-Check (IFC ↔ Sidecar)                 │  │
│  │  - Referenz-Integrität (material_id, layer_structure_ref)│ │
│  │  - LOD-Konsistenz (Pflichtfelder je LOD)                │  │
│  │  - Physikalische Plausibilität (U-Wert > 0)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Validierungs-Pipeline:**
```
Input JSON → JSON Schema Validation → Custom Validators → ✅/❌
```

**Fehlertypen:**
- **Strukturfehler:** Fehlende Felder, falsche Typen
- **Referenzfehler:** GUID nicht in IFC, material_id nicht vorhanden
- **Logikfehler:** U-Wert negativ, LOD-Inkonsistenz
- **Warnungen:** Fehlende optionale Felder, veraltete Kataloge

---

### Layer 3: Business Logic (Domain Layer)

**Verantwortung:** Fachliche Logik und Berechnungen

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Domain Layer                                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  IFC-Geometrie-Extraktion                               │  │
│  │  - Flächen-Berechnung (AN, NGF)                         │  │
│  │  - Orientierung (Normalenvektor → Azimut)               │  │
│  │  - Neigung (Normalenvektor → Inclination)               │  │
│  │  - Raum-Bauteil-Zuordnung (IfcRelSpaceBoundary)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  U-Wert-Berechnung (EN ISO 6946)                        │  │
│  │  - R_total = Σ(d_i / λ_i) + R_si + R_se                │  │
│  │  - U = 1 / R_total                                      │  │
│  │  - sd_total = Σ(d_i × μ_i) (Dampfdiffusion)            │  │
│  │  - Air Layers: R_value aus Tabellen (EN ISO 6946)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Varianten-Merge (Delta-Modell)                         │  │
│  │  - Base + Scenario.delta → Merged Input                 │  │
│  │  - Array-Merge: ID-basiert (upsert)                     │  │
│  │  - Object-Merge: Deep merge                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DIN 18599 Berechnung (Software-spezifisch)             │  │
│  │  - Energiebedarf (Teil 1-10)                            │  │
│  │  - Primärenergie (GEG)                                  │  │
│  │  - Effizienzklassen (A+ bis H)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Berechnungs-Workflow:**
```
IFC + Sidecar → Merge → Geometrie-Extraktion → U-Wert-Calc → DIN 18599 → Output
```

---

### Layer 4: API & Services (Service Layer)

**Verantwortung:** Schnittstellen und Dienste

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Service Layer                                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API (FastAPI/Express)                             │  │
│  │  POST /validate     - Validiert JSON gegen Schema       │  │
│  │  POST /calculate    - Berechnet Energiebedarf           │  │
│  │  GET  /catalogs     - Listet verfügbare Kataloge        │  │
│  │  POST /merge        - Merged Base + Scenario            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CLI Tools (Python)                                     │  │
│  │  validate.py        - Validiert JSON-Dateien            │  │
│  │  convert.py         - Konvertiert Legacy → v2.0         │  │
│  │  merge.py           - Merged Varianten                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Libraries (npm/PyPI)                                   │  │
│  │  @din18599/validator   - JSON Schema Validator          │  │
│  │  @din18599/merger      - Varianten-Merge                │  │
│  │  din18599-python       - Python SDK                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Layer 5: Präsentation (Presentation Layer)

**Verantwortung:** Benutzerinteraktion und Visualisierung

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: Presentation Layer                                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Web Viewer (HTML/JS)                                   │  │
│  │  - Drag & Drop JSON-Upload                              │  │
│  │  - Beispiel-Auswahl (LOD 100-400)                       │  │
│  │  - Bauteilliste mit U-Werten                            │  │
│  │  - Wärmebrücken-Analyse                                 │  │
│  │  - Energiebilanz-Dashboard                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Editor (Future - Phase 2)                              │  │
│  │  - Inline-Edit U-Werte                                  │  │
│  │  - Schichtaufbau-Editor (Modal)                         │  │
│  │  - Material-Dropdown                                    │  │
│  │  - Save/Export JSON                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  IFC-Viewer (Future - Phase 4)                          │  │
│  │  - xeokit 3D-Viewer                                     │  │
│  │  - GUID-Highlighting                                    │  │
│  │  - Click-to-inspect                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Datenbank-Schema (Optional - für Backend-Systeme)

**Hinweis:** Das Sidecar-Format ist **dateibasiert** (JSON). Eine Datenbank ist **optional** für:
- Multi-User-Editing
- Versionierung
- Projekt-Management
- Katalog-Verwaltung

### 3.1 PostgreSQL Schema (Beispiel)

```sql
-- Schema für Projekt-Management
CREATE SCHEMA din18599;

-- Projekte
CREATE TABLE din18599.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    ifc_file_path TEXT,
    ifc_guid_building UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sidecar-Versionen (JSONB für Flexibilität)
CREATE TABLE din18599.sidecars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES din18599.projects(id) ON DELETE CASCADE,
    version INT NOT NULL,
    lod VARCHAR(10),
    data JSONB NOT NULL, -- Vollständiges Sidecar JSON
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    UNIQUE(project_id, version)
);

-- Index für schnelle JSONB-Queries
CREATE INDEX idx_sidecars_data_gin ON din18599.sidecars USING GIN (data);

-- Kataloge
CREATE TABLE din18599.catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    type VARCHAR(50), -- 'CONSTRUCTIONS', 'MATERIALS', 'SYSTEMS'
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit-Log
CREATE TABLE din18599.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES din18599.projects(id),
    action VARCHAR(50), -- 'CREATE', 'UPDATE', 'DELETE', 'CALCULATE'
    user_id UUID,
    changes JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 JSONB Queries (Beispiele)

```sql
-- Alle Projekte mit LOD 300+
SELECT id, name, data->>'meta'->>'lod' as lod
FROM din18599.sidecars
WHERE (data->'meta'->>'lod')::int >= 300;

-- Alle Bauteile mit U-Wert < 0.3
SELECT 
    project_id,
    elem->>'ifc_guid' as ifc_guid,
    (elem->>'u_value_undisturbed')::float as u_value
FROM din18599.sidecars,
     jsonb_array_elements(data->'input'->'elements') as elem
WHERE (elem->>'u_value_undisturbed')::float < 0.3;

-- Varianten-Anzahl pro Projekt
SELECT 
    project_id,
    jsonb_array_length(data->'scenarios') as scenario_count
FROM din18599.sidecars
WHERE data ? 'scenarios';
```

---

## 4. Komponenten-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Viewer     │  │    Editor    │  │  IFC-Viewer  │          │
│  │  (HTML/JS)   │  │  (Vue/React) │  │  (xeokit)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API (FastAPI/Express)                             │  │
│  │  /validate, /calculate, /merge, /catalogs               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Validator   │  │   Merger     │  │  Calculator  │          │
│  │  (jsonschema)│  │  (Delta)     │  │  (DIN 18599) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  IFC Files   │  │  Sidecar JSON│  │  Catalogs    │          │
│  │  (Filesystem)│  │  (Filesystem)│  │  (JSON)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL (Optional - für Multi-User/Versionierung)    │  │
│  │  - projects, sidecars, catalogs, audit_log              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Deployment-Architektur

### 5.1 Standalone (Desktop-Anwendung)

```
┌─────────────────────────────────────────┐
│  Desktop (Windows/macOS/Linux)          │
│  ┌───────────────────────────────────┐  │
│  │  Electron App                     │  │
│  │  - Viewer (HTML/JS)               │  │
│  │  - Validator (Python/Node)        │  │
│  │  - IFC-Parser (IfcOpenShell)      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Local Files                      │  │
│  │  - IFC-Dateien                    │  │
│  │  - Sidecar JSONs                  │  │
│  │  - Kataloge                       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 5.2 Web-Anwendung (Cloud)

```
┌─────────────────────────────────────────────────────────────────┐
│  Client (Browser)                                               │
│  - Viewer (Static HTML/JS)                                      │
│  - Editor (Vue/React SPA)                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  CDN (Cloudflare/CloudFront)                                    │
│  - Static Assets (HTML/JS/CSS)                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  API Server (Docker Container)                                  │
│  - FastAPI/Express                                              │
│  - Validator, Merger, Calculator                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  Storage                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  S3/Blob     │  │  PostgreSQL  │  │  Redis Cache │          │
│  │  (IFC/JSON)  │  │  (Metadata)  │  │  (Sessions)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Technologie-Stack

### Backend
- **Python:** FastAPI, Pydantic, IfcOpenShell, jsonschema
- **Node.js:** Express, Ajv (JSON Schema), ifc.js (optional)

### Frontend
- **Viewer:** Vanilla JS (aktuell), Vue.js/React (geplant)
- **IFC-Viewer:** xeokit-sdk (geplant)
- **UI:** Tailwind CSS, shadcn/ui (optional)

### Datenbank (Optional)
- **PostgreSQL:** JSONB für flexible Schema-Evolution
- **Redis:** Caching, Session-Management

### DevOps
- **Docker:** Container für API-Server
- **Git:** Versionierung (GitHub)
- **CI/CD:** GitHub Actions (Tests, Linting, Deployment)

---

## 7. Sicherheit & Performance

### Sicherheit
- **Input Validation:** JSON Schema + Custom Validators
- **GUID-Injection:** Whitelist-basierte GUID-Validierung
- **File Upload:** Größenbeschränkung (max. 100 MB IFC, 10 MB JSON)
- **CORS:** Konfigurierbar für API-Server

### Performance
- **JSONB-Indexing:** GIN-Index für schnelle Queries
- **Caching:** Redis für häufig genutzte Kataloge
- **Lazy Loading:** IFC-Geometrie nur bei Bedarf laden
- **XKT-Konvertierung:** Komprimierte IFC-Dateien für Viewer

---

## 8. Erweiterbarkeit

### Plugin-System (Future)
```javascript
// Beispiel: Custom Validator Plugin
class CustomValidator {
  validate(data) {
    // Custom Logic
    return { valid: true, errors: [] };
  }
}

registerValidator('my-custom-validator', CustomValidator);
```

### Katalog-Erweiterungen
- **Custom Catalogs:** Nutzer können eigene Kataloge hinzufügen
- **Catalog-API:** REST-Endpunkt für Katalog-Upload
- **Versioning:** Kataloge haben Versionsnummern

---

## 9. Offene Architektur-Fragen

1. **Multi-Tenancy:** Soll die Datenbank mandantenfähig sein?
2. **Real-Time Collaboration:** WebSockets für Multi-User-Editing?
3. **Offline-First:** Service Worker für Offline-Nutzung?
4. **Mobile App:** Native App (React Native) oder PWA?
5. **IFC-Konvertierung:** Server-seitig oder Client-seitig?

---

## 10. Nächste Schritte

- [ ] **PostgreSQL Schema** finalisieren (wenn Backend geplant)
- [ ] **API-Spezifikation** (OpenAPI/Swagger)
- [ ] **Docker Compose** für lokale Entwicklung
- [ ] **CI/CD Pipeline** (Tests, Linting, Deployment)
- [ ] **Deployment-Guide** (AWS/Azure/On-Premise)

---

**Status:** ✅ Architektur ist definiert und dokumentiert.  
**Nächster Schritt:** Implementierung nach Layer-Prinzip (Bottom-Up: Data → Schema → Logic → API → UI)
