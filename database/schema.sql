-- ============================================================================
-- DIN 18599 IFC Sidecar - PostgreSQL Database Schema
-- ============================================================================
-- Version: 2.0.0
-- Stand: März 2026
-- Beschreibung: Optional Backend für Multi-User, Versionierung, Kataloge
-- ============================================================================

-- Schema erstellen
CREATE SCHEMA IF NOT EXISTS din18599;

-- Kommentar
COMMENT ON SCHEMA din18599 IS 'DIN 18599 IFC Sidecar - Projekt-Management und Kataloge';

-- ============================================================================
-- 1. PROJEKTE
-- ============================================================================

CREATE TABLE din18599.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- IFC-Referenz
    ifc_file_path TEXT,
    ifc_guid_building UUID,
    
    -- Metadaten
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT projects_name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

CREATE INDEX idx_projects_created_at ON din18599.projects(created_at);
CREATE INDEX idx_projects_deleted_at ON din18599.projects(deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE din18599.projects IS 'Energieberatungs-Projekte';
COMMENT ON COLUMN din18599.projects.ifc_file_path IS 'Pfad zur IFC-Datei (relativ oder absolut)';
COMMENT ON COLUMN din18599.projects.ifc_guid_building IS 'GlobalId des IfcBuilding';

-- ============================================================================
-- 2. SIDECARS (Versionierte JSON-Daten)
-- ============================================================================

CREATE TABLE din18599.sidecars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES din18599.projects(id) ON DELETE CASCADE,
    
    -- Versionierung
    version INT NOT NULL,
    version_name VARCHAR(100),
    is_current BOOLEAN NOT NULL DEFAULT false,
    
    -- Metadaten
    lod VARCHAR(10),
    mode VARCHAR(20) CHECK (mode IN ('STANDALONE', 'SIMPLIFIED', 'IFC_LINKED')),
    
    -- Vollständiges Sidecar JSON
    data JSONB NOT NULL,
    
    -- Hash für Änderungserkennung
    data_hash VARCHAR(64),
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    UNIQUE(project_id, version),
    CONSTRAINT sidecars_version_positive CHECK (version > 0),
    CONSTRAINT sidecars_lod_valid CHECK (lod IN ('100', '200', '300', '400', '500'))
);

CREATE INDEX idx_sidecars_project_id ON din18599.sidecars(project_id);
CREATE INDEX idx_sidecars_is_current ON din18599.sidecars(project_id, is_current) WHERE is_current = true;
CREATE INDEX idx_sidecars_data_gin ON din18599.sidecars USING GIN (data);
CREATE INDEX idx_sidecars_deleted_at ON din18599.sidecars(deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE din18599.sidecars IS 'Versionierte Sidecar-JSONs';
COMMENT ON COLUMN din18599.sidecars.data IS 'Vollständiges Sidecar JSON (JSONB für schnelle Queries)';
COMMENT ON COLUMN din18599.sidecars.data_hash IS 'SHA-256 Hash des JSON (für Änderungserkennung)';
COMMENT ON COLUMN din18599.sidecars.is_current IS 'Aktuelle Version (nur eine pro Projekt)';

-- Trigger: Nur eine aktuelle Version pro Projekt
CREATE OR REPLACE FUNCTION din18599.ensure_single_current_version()
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

CREATE TRIGGER trigger_ensure_single_current_version
    BEFORE INSERT OR UPDATE ON din18599.sidecars
    FOR EACH ROW
    EXECUTE FUNCTION din18599.ensure_single_current_version();

-- ============================================================================
-- 3. KATALOGE
-- ============================================================================

CREATE TABLE din18599.catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Katalog-Info
    catalog_id VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Typ
    type VARCHAR(50) NOT NULL CHECK (type IN ('CONSTRUCTIONS', 'MATERIALS', 'SYSTEMS', 'CUSTOM')),
    
    -- Quelle
    source VARCHAR(255),
    source_url TEXT,
    valid_from DATE,
    valid_to DATE,
    
    -- Katalog-Daten (JSON)
    data JSONB NOT NULL,
    
    -- Metadaten
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    UNIQUE(catalog_id, version),
    CONSTRAINT catalogs_name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

CREATE INDEX idx_catalogs_type ON din18599.catalogs(type);
CREATE INDEX idx_catalogs_data_gin ON din18599.catalogs USING GIN (data);
CREATE INDEX idx_catalogs_deleted_at ON din18599.catalogs(deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE din18599.catalogs IS 'Kataloge (Bundesanzeiger, Custom)';
COMMENT ON COLUMN din18599.catalogs.catalog_id IS 'Eindeutige Katalog-ID (z.B. DE_BMWI2020_BAUTEILE)';
COMMENT ON COLUMN din18599.catalogs.data IS 'Katalog-Daten als JSONB';

-- ============================================================================
-- 4. AUDIT LOG
-- ============================================================================

CREATE TABLE din18599.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Referenz
    project_id UUID REFERENCES din18599.projects(id) ON DELETE SET NULL,
    sidecar_id UUID REFERENCES din18599.sidecars(id) ON DELETE SET NULL,
    
    -- Aktion
    action VARCHAR(50) NOT NULL CHECK (action IN (
        'CREATE', 'UPDATE', 'DELETE', 'RESTORE',
        'CALCULATE', 'EXPORT', 'IMPORT'
    )),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN (
        'PROJECT', 'SIDECAR', 'CATALOG'
    )),
    
    -- Änderungen (JSON Diff)
    changes JSONB,
    
    -- Metadaten
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    
    -- Zeitstempel
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_project_id ON din18599.audit_log(project_id);
CREATE INDEX idx_audit_log_timestamp ON din18599.audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_action ON din18599.audit_log(action);

COMMENT ON TABLE din18599.audit_log IS 'Audit-Trail für alle Änderungen';
COMMENT ON COLUMN din18599.audit_log.changes IS 'JSON Diff (old_value, new_value)';

-- ============================================================================
-- 5. BENUTZER (Optional - wenn nicht externes Auth-System)
-- ============================================================================

CREATE TABLE din18599.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Auth
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    
    -- Profil
    name VARCHAR(255),
    organization VARCHAR(255),
    
    -- Rollen
    role VARCHAR(50) NOT NULL DEFAULT 'USER' CHECK (role IN ('ADMIN', 'USER', 'VIEWER')),
    
    -- Metadaten
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    
    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT users_email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON din18599.users(email);
CREATE INDEX idx_users_deleted_at ON din18599.users(deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE din18599.users IS 'Benutzer (optional, wenn kein externes Auth-System)';

-- ============================================================================
-- 6. PROJEKT-MITGLIEDER (Team-Zugriff)
-- ============================================================================

CREATE TABLE din18599.project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Referenzen
    project_id UUID NOT NULL REFERENCES din18599.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES din18599.users(id) ON DELETE CASCADE,
    
    -- Rolle
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER' CHECK (role IN ('OWNER', 'EDITOR', 'VIEWER')),
    
    -- Metadaten
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    
    -- Constraints
    UNIQUE(project_id, user_id)
);

CREATE INDEX idx_project_members_project_id ON din18599.project_members(project_id);
CREATE INDEX idx_project_members_user_id ON din18599.project_members(user_id);

COMMENT ON TABLE din18599.project_members IS 'Projekt-Team (Multi-User-Zugriff)';

-- ============================================================================
-- 7. VIEWS (Convenience)
-- ============================================================================

-- Aktuelle Sidecars
CREATE VIEW din18599.current_sidecars AS
SELECT 
    s.*,
    p.name AS project_name
FROM din18599.sidecars s
JOIN din18599.projects p ON s.project_id = p.id
WHERE s.is_current = true
  AND s.deleted_at IS NULL
  AND p.deleted_at IS NULL;

COMMENT ON VIEW din18599.current_sidecars IS 'Nur aktuelle Sidecar-Versionen';

-- Projekt-Übersicht
CREATE VIEW din18599.project_overview AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.ifc_file_path,
    COUNT(DISTINCT s.id) AS version_count,
    MAX(s.version) AS latest_version,
    MAX(s.created_at) AS last_updated,
    p.created_at,
    p.created_by
FROM din18599.projects p
LEFT JOIN din18599.sidecars s ON p.id = s.project_id AND s.deleted_at IS NULL
WHERE p.deleted_at IS NULL
GROUP BY p.id;

COMMENT ON VIEW din18599.project_overview IS 'Projekt-Übersicht mit Statistiken';

-- ============================================================================
-- 8. FUNKTIONEN (Helper)
-- ============================================================================

-- Neue Sidecar-Version erstellen
CREATE OR REPLACE FUNCTION din18599.create_sidecar_version(
    p_project_id UUID,
    p_data JSONB,
    p_version_name VARCHAR(100) DEFAULT NULL,
    p_created_by UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_version INT;
    v_sidecar_id UUID;
    v_data_hash VARCHAR(64);
BEGIN
    -- Nächste Version ermitteln
    SELECT COALESCE(MAX(version), 0) + 1 INTO v_version
    FROM din18599.sidecars
    WHERE project_id = p_project_id;
    
    -- Hash berechnen
    v_data_hash := encode(digest(p_data::text, 'sha256'), 'hex');
    
    -- Sidecar erstellen
    INSERT INTO din18599.sidecars (
        project_id,
        version,
        version_name,
        is_current,
        lod,
        mode,
        data,
        data_hash,
        created_by
    ) VALUES (
        p_project_id,
        v_version,
        p_version_name,
        true,
        p_data->'meta'->>'lod',
        CASE 
            WHEN p_data->'meta'->>'ifc_file_ref' IS NOT NULL THEN 'IFC_LINKED'
            WHEN p_data->'meta'->>'simplified_geometry' = 'true' THEN 'SIMPLIFIED'
            ELSE 'STANDALONE'
        END,
        p_data,
        v_data_hash,
        p_created_by
    ) RETURNING id INTO v_sidecar_id;
    
    RETURN v_sidecar_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION din18599.create_sidecar_version IS 'Erstellt neue Sidecar-Version';

-- ============================================================================
-- 9. BEISPIEL-QUERIES
-- ============================================================================

-- Alle Projekte mit aktueller Version
COMMENT ON SCHEMA din18599 IS 'Beispiel-Query: SELECT * FROM din18599.project_overview;';

-- Alle Bauteile mit U-Wert < 0.3
COMMENT ON TABLE din18599.sidecars IS 'Beispiel-Query: 
SELECT 
    p.name AS project,
    elem->''name'' AS element_name,
    (elem->>''u_value_undisturbed'')::float AS u_value
FROM din18599.current_sidecars s
JOIN din18599.projects p ON s.project_id = p.id,
     jsonb_array_elements(s.data->''input''->''elements'') AS elem
WHERE (elem->>''u_value_undisturbed'')::float < 0.3;';

-- Varianten-Anzahl pro Projekt
COMMENT ON TABLE din18599.projects IS 'Beispiel-Query:
SELECT 
    p.name,
    jsonb_array_length(s.data->''scenarios'') AS scenario_count
FROM din18599.current_sidecars s
JOIN din18599.projects p ON s.project_id = p.id
WHERE s.data ? ''scenarios'';';

-- ============================================================================
-- 10. GRANTS (Berechtigungen)
-- ============================================================================

-- Erstelle Rollen (optional)
-- CREATE ROLE din18599_admin;
-- CREATE ROLE din18599_user;
-- CREATE ROLE din18599_viewer;

-- GRANT ALL ON SCHEMA din18599 TO din18599_admin;
-- GRANT USAGE ON SCHEMA din18599 TO din18599_user, din18599_viewer;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA din18599 TO din18599_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA din18599 TO din18599_viewer;

-- ============================================================================
-- ENDE
-- ============================================================================
