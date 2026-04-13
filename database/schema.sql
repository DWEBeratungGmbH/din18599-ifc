-- ══════════════════════════════════════════════════════════════════════
-- DIN 18599 IFC Sidecar — Datenbank-Schema v3.0
-- ══════════════════════════════════════════════════════════════════════
--
-- Architektur: Hybrid (Option C)
--   → JSONB als Source of Truth (verlustfreier Roundtrip)
--   → Extrahierte Spalten für schnelle Queries
--   → Validierung in Python VOR dem Insert
--
-- Kompatibel mit: Schema v3.0 (erweitert v2.3 um die Gebäudeakte-Sektionen)
--   v2.3: building, envelope, constructions, systems, scenarios, output
--   v3.0: + documents, funding, roadmap, sla_context (Gebäudeakte-Erweiterung)
--
-- Schema = Single Source of Truth — siehe schema/v3.0-complete.json
-- Erstellt: 2026-04-04, v3.0-Update: 2026-04-10
-- Lizenz: Apache 2.0
-- ══════════════════════════════════════════════════════════════════════

-- Eigenes Schema für Isolation
CREATE SCHEMA IF NOT EXISTS din18599;

-- UUID-Erweiterung (für gen_random_uuid)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ══════════════════════════════════════════════════════════════════════
-- 1. PROJEKTE
-- Verwaltungs-Ebene: Ein Projekt = ein Gebäude mit IFC + Sidecar(s)
-- ══════════════════════════════════════════════════════════════════════

CREATE TABLE din18599.projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    description     TEXT,
    -- IFC-Referenz (optional, da Sidecar auch ohne IFC existieren kann)
    ifc_file_ref    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Automatische Aktualisierung von updated_at
CREATE OR REPLACE FUNCTION din18599.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated
    BEFORE UPDATE ON din18599.projects
    FOR EACH ROW EXECUTE FUNCTION din18599.update_timestamp();


-- ══════════════════════════════════════════════════════════════════════
-- 2. SIDECARS (Kern-Tabelle)
-- Versionierte Sidecar-JSONs mit extrahierten Metadaten
--
-- Design-Entscheidung: data (JSONB) enthält das VOLLSTÄNDIGE JSON.
-- Die extrahierten Spalten sind Convenience-Felder für schnelle Queries,
-- sie werden beim Import aus dem JSON befüllt.
-- Export = SELECT data → 1:1 identisch mit dem Original.
-- ══════════════════════════════════════════════════════════════════════

CREATE TABLE din18599.sidecars (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES din18599.projects(id) ON DELETE CASCADE,
    version             INT NOT NULL,

    -- Das vollständige Sidecar JSON — Source of Truth
    data                JSONB NOT NULL,

    -- SHA-256 Hash des JSON für Duplikat-Erkennung
    data_hash           TEXT NOT NULL,

    -- Versionierung: Nur eine aktuelle Version pro Projekt
    is_current          BOOLEAN NOT NULL DEFAULT true,

    -- ── Extrahierte Metadaten (aus data beim Import befüllt) ──

    -- Schema-Version (z.B. "2.3.0")
    schema_version      TEXT,
    -- Level of Detail: "100" bis "500"
    lod                 TEXT,
    -- Projektname aus meta.project_name
    project_name        TEXT,
    -- IFC-Dateiname aus meta.ifc_file_ref
    ifc_file_ref        TEXT,
    -- IFC-Schema (IFC2X3, IFC4, IFC4X3)
    ifc_schema          TEXT,

    -- ── Extrahierte Gebäudedaten ──

    -- Baujahr aus building.construction_year
    construction_year   INT,
    -- Beheizte Fläche aus building.heated_area [m²]
    heated_area         NUMERIC,

    -- ── Statistik-Spalten (beim Import berechnet) ──

    wall_count          INT DEFAULT 0,
    roof_count          INT DEFAULT 0,
    floor_count         INT DEFAULT 0,
    window_count        INT DEFAULT 0,
    door_count          INT DEFAULT 0,
    zone_count          INT DEFAULT 0,
    room_count          INT DEFAULT 0,
    construction_count  INT DEFAULT 0,

    -- ── v3.0: Statistiken der Gebäudeakte-Sektionen ──
    -- Aus dem JSON beim Import befüllt; ermöglicht schnelle Übersicht
    -- ohne JSONB-Aggregation in der Liste.
    document_count      INT DEFAULT 0,
    funding_count       INT DEFAULT 0,
    roadmap_step_count  INT DEFAULT 0,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(project_id, version)
);

-- GIN-Index für JSONB-Queries (z.B. alle Wände mit U-Wert < 0.3)
CREATE INDEX idx_sidecars_data_gin ON din18599.sidecars USING GIN (data);

-- B-Tree Indizes für häufige Filter
CREATE INDEX idx_sidecars_project_current ON din18599.sidecars (project_id, is_current) WHERE is_current = true;
CREATE INDEX idx_sidecars_schema_version ON din18599.sidecars (schema_version);
CREATE INDEX idx_sidecars_lod ON din18599.sidecars (lod);

-- Trigger: Nur eine aktuelle Version pro Projekt
-- Wenn ein neuer Sidecar mit is_current=true eingefügt wird,
-- werden alle anderen Versionen desselben Projekts auf is_current=false gesetzt.
CREATE OR REPLACE FUNCTION din18599.ensure_single_current()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_current = true THEN
        UPDATE din18599.sidecars
        SET is_current = false
        WHERE project_id = NEW.project_id
          AND id != NEW.id
          AND is_current = true;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_single_current
    BEFORE INSERT OR UPDATE ON din18599.sidecars
    FOR EACH ROW EXECUTE FUNCTION din18599.ensure_single_current();


-- ══════════════════════════════════════════════════════════════════════
-- 3. KATALOGE
-- Bundesanzeiger U-Werte, Material-Datenbanken, Custom Catalogs
-- ══════════════════════════════════════════════════════════════════════

CREATE TABLE din18599.catalogs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    -- Katalog-Typ: CONSTRUCTIONS, MATERIALS, USAGE_PROFILES, SYSTEMS
    type            TEXT NOT NULL,
    version         TEXT,
    -- Quelle: z.B. "Bundesanzeiger AT 04.12.2020 B1"
    source          TEXT,
    -- Vollständiger Katalog als JSONB
    data            JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ein Katalog-Name + Version muss eindeutig sein
    UNIQUE(name, version)
);


-- ══════════════════════════════════════════════════════════════════════
-- 4. IMPORT-LOG
-- Dokumentiert jeden Import-Versuch mit Validierungsergebnis
-- Wichtig für Nachvollziehbarkeit und Fehleranalyse
-- ══════════════════════════════════════════════════════════════════════

CREATE TABLE din18599.import_log (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Referenz zum erstellten Sidecar (NULL wenn Import fehlgeschlagen)
    sidecar_id              UUID REFERENCES din18599.sidecars(id) ON DELETE SET NULL,
    project_id              UUID REFERENCES din18599.projects(id) ON DELETE CASCADE,

    -- Quelldatei-Info
    filename                TEXT,
    file_size_bytes         INT,

    -- Import-Status: SUCCESS, WARNINGS, FAILED
    status                  TEXT NOT NULL,

    -- Validierungsergebnisse (3 Ebenen)
    schema_valid            BOOLEAN,       -- Ebene 1: JSON Schema
    references_valid        BOOLEAN,       -- Ebene 2: Interne Referenzen
    plausibility_valid      BOOLEAN,       -- Ebene 3: Fachliche Plausibilität

    -- Details zu Fehlern und Warnungen
    errors                  JSONB DEFAULT '[]'::jsonb,
    warnings                JSONB DEFAULT '[]'::jsonb,

    -- Wie lange hat die Validierung gedauert?
    validation_duration_ms  INT,

    imported_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_import_log_project ON din18599.import_log (project_id);
CREATE INDEX idx_import_log_status ON din18599.import_log (status);


-- ══════════════════════════════════════════════════════════════════════
-- 5. VIEW: Projekt-Übersicht
-- Für schnelle Auflistung aller Projekte mit aktuellem Sidecar-Status
-- ══════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW din18599.v_projects_overview AS
SELECT
    p.id                    AS project_id,
    p.name                  AS project_name,
    p.description,
    p.ifc_file_ref          AS project_ifc_ref,
    p.created_at            AS project_created,
    p.updated_at            AS project_updated,
    -- Aktueller Sidecar
    s.id                    AS sidecar_id,
    s.version               AS sidecar_version,
    s.schema_version,
    s.lod,
    s.project_name          AS sidecar_project_name,
    s.ifc_file_ref          AS sidecar_ifc_ref,
    s.ifc_schema,
    s.construction_year,
    s.heated_area,
    -- Statistiken
    s.wall_count,
    s.roof_count,
    s.floor_count,
    s.window_count,
    s.door_count,
    s.zone_count,
    s.room_count,
    s.construction_count,
    -- v3.0: Gebäudeakte-Statistiken
    s.document_count,
    s.funding_count,
    s.roadmap_step_count,
    s.created_at            AS sidecar_created,
    -- Gesamte Versionen
    (SELECT COUNT(*) FROM din18599.sidecars sv WHERE sv.project_id = p.id)::int AS total_versions,
    -- Letzter Import-Status
    (SELECT il.status FROM din18599.import_log il
     WHERE il.project_id = p.id
     ORDER BY il.imported_at DESC LIMIT 1) AS last_import_status
FROM din18599.projects p
LEFT JOIN din18599.sidecars s ON s.project_id = p.id AND s.is_current = true;


-- ══════════════════════════════════════════════════════════════════════
-- 6. HELPER-FUNKTIONEN
-- Nützliche SQL-Funktionen für häufige JSONB-Abfragen
-- ══════════════════════════════════════════════════════════════════════

-- Alle Wände eines Sidecars mit U-Werten extrahieren
CREATE OR REPLACE FUNCTION din18599.get_walls(p_sidecar_id UUID)
RETURNS TABLE (
    ifc_guid TEXT,
    name TEXT,
    u_value NUMERIC,
    area NUMERIC,
    orientation INT,
    boundary_condition TEXT,
    din_code TEXT
) AS $$
    SELECT
        wall->>'ifc_guid',
        wall->>'name',
        (wall->>'u_value')::NUMERIC,
        (wall->>'area')::NUMERIC,
        (wall->>'orientation')::INT,
        wall->>'boundary_condition',
        wall->>'din_code'
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'input'->'envelope'->'walls') AS wall
    WHERE s.id = p_sidecar_id;
$$ LANGUAGE sql STABLE;

-- Alle Zonen eines Sidecars extrahieren
CREATE OR REPLACE FUNCTION din18599.get_zones(p_sidecar_id UUID)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    area NUMERIC,
    volume NUMERIC,
    height NUMERIC,
    usage_profile_ref TEXT
) AS $$
    SELECT
        zone->>'id',
        zone->>'name',
        (zone->>'area')::NUMERIC,
        (zone->>'volume')::NUMERIC,
        (zone->>'height')::NUMERIC,
        zone->>'usage_profile_ref'
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'input'->'building'->'zones') AS zone
    WHERE s.id = p_sidecar_id;
$$ LANGUAGE sql STABLE;

-- Durchschnittlicher U-Wert aller Außenwände eines Projekts
CREATE OR REPLACE FUNCTION din18599.avg_u_value_walls(p_sidecar_id UUID)
RETURNS NUMERIC AS $$
    SELECT ROUND(AVG((wall->>'u_value')::NUMERIC), 3)
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'input'->'envelope'->'walls') AS wall
    WHERE s.id = p_sidecar_id
      AND (wall->>'u_value')::NUMERIC > 0;
$$ LANGUAGE sql STABLE;


-- ══════════════════════════════════════════════════════════════════════
-- 7. v3.0 HELPER-FUNKTIONEN — Gebäudeakte-Sektionen
-- Zugriff auf documents, funding und roadmap-Schritte ohne Client-Code
-- ══════════════════════════════════════════════════════════════════════

-- Alle Dokumente eines Sidecars extrahieren
-- (Pläne, Nachweise, Fotos, Rechnungen, Förderdokumente)
CREATE OR REPLACE FUNCTION din18599.get_documents(p_sidecar_id UUID)
RETURNS TABLE (
    id TEXT,
    type TEXT,
    name TEXT,
    storage_ref TEXT,
    mime_type TEXT,
    scenario_ref TEXT,
    valid_until TIMESTAMPTZ,
    amount_eur NUMERIC,
    uploaded_at TIMESTAMPTZ
) AS $$
    SELECT
        doc->>'id',
        doc->>'type',
        doc->>'name',
        doc->>'storage_ref',
        doc->>'mime_type',
        doc->>'scenario_ref',
        (doc->>'valid_until')::TIMESTAMPTZ,
        (doc->>'amount_eur')::NUMERIC,
        (doc->>'uploaded_at')::TIMESTAMPTZ
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'documents') AS doc
    WHERE s.id = p_sidecar_id;
$$ LANGUAGE sql STABLE;

-- Alle Förderungen eines Sidecars extrahieren
-- (BEG, KfW, BAFA — Snapshot-Daten, ERPNext bleibt Master)
CREATE OR REPLACE FUNCTION din18599.get_funding(p_sidecar_id UUID)
RETURNS TABLE (
    id TEXT,
    program TEXT,
    name TEXT,
    scenario_ref TEXT,
    document_ref TEXT,
    erpnext_ref TEXT,
    status TEXT,
    amount_applied_eur NUMERIC,
    amount_approved_eur NUMERIC,
    synced_at TIMESTAMPTZ
) AS $$
    SELECT
        f->>'id',
        f->>'program',
        f->>'name',
        f->>'scenario_ref',
        f->>'document_ref',
        f->>'erpnext_ref',
        f->'snapshot'->>'status',
        (f->'snapshot'->>'amount_applied_eur')::NUMERIC,
        (f->'snapshot'->>'amount_approved_eur')::NUMERIC,
        (f->'snapshot'->>'synced_at')::TIMESTAMPTZ
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'funding') AS f
    WHERE s.id = p_sidecar_id;
$$ LANGUAGE sql STABLE;

-- Alle Roadmap-Schritte eines Sidecars extrahieren
-- (Sanierungsfahrplan mit priorisierten Schritten)
CREATE OR REPLACE FUNCTION din18599.get_roadmap_steps(p_sidecar_id UUID)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    description TEXT,
    scenario_ref TEXT,
    planned_year INT,
    status TEXT,
    priority INT,
    estimated_cost_eur NUMERIC
) AS $$
    SELECT
        step->>'id',
        step->>'name',
        step->>'description',
        step->>'scenario_ref',
        (step->>'planned_year')::INT,
        step->>'status',
        (step->>'priority')::INT,
        (step->>'estimated_cost_eur')::NUMERIC
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'roadmap'->'steps') AS step
    WHERE s.id = p_sidecar_id;
$$ LANGUAGE sql STABLE;

-- Summe der bewilligten Förderungen eines Projekts [EUR]
-- Schnelle Kennzahl für Übersicht und Reporting
CREATE OR REPLACE FUNCTION din18599.sum_approved_funding(p_sidecar_id UUID)
RETURNS NUMERIC AS $$
    SELECT COALESCE(SUM((f->'snapshot'->>'amount_approved_eur')::NUMERIC), 0)
    FROM din18599.sidecars s,
         jsonb_array_elements(s.data->'funding') AS f
    WHERE s.id = p_sidecar_id;
$$ LANGUAGE sql STABLE;


-- ══════════════════════════════════════════════════════════════════════
-- FERTIG — v3.0
-- Schema bereit für: Python Validator → Import → Export
-- Quelle der Wahrheit: schema/v3.0-complete.json
-- ══════════════════════════════════════════════════════════════════════
