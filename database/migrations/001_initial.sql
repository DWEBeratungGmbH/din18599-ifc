-- ============================================================================
-- Migration 001: Initial Schema
-- ============================================================================
-- Beschreibung: Erstellt alle Tabellen, Indizes, Trigger und Views
-- Version: 2.0.0
-- Datum: 2026-03-27
-- ============================================================================

\echo '>>> Migration 001: Initial Schema'

-- Schema erstellen
CREATE SCHEMA IF NOT EXISTS din18599;

-- ============================================================================
-- TABELLEN
-- ============================================================================

\echo '>>> Erstelle Tabelle: projects'
CREATE TABLE din18599.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ifc_file_path TEXT,
    ifc_guid_building UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT projects_name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

\echo '>>> Erstelle Tabelle: sidecars'
CREATE TABLE din18599.sidecars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES din18599.projects(id) ON DELETE CASCADE,
    version INT NOT NULL,
    version_name VARCHAR(100),
    is_current BOOLEAN NOT NULL DEFAULT false,
    lod VARCHAR(10),
    mode VARCHAR(20) CHECK (mode IN ('STANDALONE', 'SIMPLIFIED', 'IFC_LINKED')),
    data JSONB NOT NULL,
    data_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    deleted_at TIMESTAMPTZ,
    UNIQUE(project_id, version),
    CONSTRAINT sidecars_version_positive CHECK (version > 0),
    CONSTRAINT sidecars_lod_valid CHECK (lod IN ('100', '200', '300', '400', '500'))
);

\echo '>>> Erstelle Tabelle: catalogs'
CREATE TABLE din18599.catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_id VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('CONSTRUCTIONS', 'MATERIALS', 'SYSTEMS', 'CUSTOM')),
    source VARCHAR(255),
    source_url TEXT,
    valid_from DATE,
    valid_to DATE,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    deleted_at TIMESTAMPTZ,
    UNIQUE(catalog_id, version),
    CONSTRAINT catalogs_name_not_empty CHECK (LENGTH(TRIM(name)) > 0)
);

\echo '>>> Erstelle Tabelle: audit_log'
CREATE TABLE din18599.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES din18599.projects(id) ON DELETE SET NULL,
    sidecar_id UUID REFERENCES din18599.sidecars(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN (
        'CREATE', 'UPDATE', 'DELETE', 'RESTORE',
        'CALCULATE', 'EXPORT', 'IMPORT'
    )),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN (
        'PROJECT', 'SIDECAR', 'CATALOG'
    )),
    changes JSONB,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

\echo '>>> Erstelle Tabelle: users'
CREATE TABLE din18599.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    organization VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'USER' CHECK (role IN ('ADMIN', 'USER', 'VIEWER')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT users_email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

\echo '>>> Erstelle Tabelle: project_members'
CREATE TABLE din18599.project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES din18599.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES din18599.users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER' CHECK (role IN ('OWNER', 'EDITOR', 'VIEWER')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    UNIQUE(project_id, user_id)
);

-- ============================================================================
-- INDIZES
-- ============================================================================

\echo '>>> Erstelle Indizes'

-- Projects
CREATE INDEX idx_projects_created_at ON din18599.projects(created_at);
CREATE INDEX idx_projects_deleted_at ON din18599.projects(deleted_at) WHERE deleted_at IS NULL;

-- Sidecars
CREATE INDEX idx_sidecars_project_id ON din18599.sidecars(project_id);
CREATE INDEX idx_sidecars_is_current ON din18599.sidecars(project_id, is_current) WHERE is_current = true;
CREATE INDEX idx_sidecars_data_gin ON din18599.sidecars USING GIN (data);
CREATE INDEX idx_sidecars_deleted_at ON din18599.sidecars(deleted_at) WHERE deleted_at IS NULL;

-- Catalogs
CREATE INDEX idx_catalogs_type ON din18599.catalogs(type);
CREATE INDEX idx_catalogs_data_gin ON din18599.catalogs USING GIN (data);
CREATE INDEX idx_catalogs_deleted_at ON din18599.catalogs(deleted_at) WHERE deleted_at IS NULL;

-- Audit Log
CREATE INDEX idx_audit_log_project_id ON din18599.audit_log(project_id);
CREATE INDEX idx_audit_log_timestamp ON din18599.audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_action ON din18599.audit_log(action);

-- Users
CREATE INDEX idx_users_email ON din18599.users(email);
CREATE INDEX idx_users_deleted_at ON din18599.users(deleted_at) WHERE deleted_at IS NULL;

-- Project Members
CREATE INDEX idx_project_members_project_id ON din18599.project_members(project_id);
CREATE INDEX idx_project_members_user_id ON din18599.project_members(user_id);

-- ============================================================================
-- TRIGGER
-- ============================================================================

\echo '>>> Erstelle Trigger'

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
-- VIEWS
-- ============================================================================

\echo '>>> Erstelle Views'

CREATE VIEW din18599.current_sidecars AS
SELECT 
    s.*,
    p.name AS project_name
FROM din18599.sidecars s
JOIN din18599.projects p ON s.project_id = p.id
WHERE s.is_current = true
  AND s.deleted_at IS NULL
  AND p.deleted_at IS NULL;

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

-- ============================================================================
-- FUNKTIONEN
-- ============================================================================

\echo '>>> Erstelle Funktionen'

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
    SELECT COALESCE(MAX(version), 0) + 1 INTO v_version
    FROM din18599.sidecars
    WHERE project_id = p_project_id;
    
    v_data_hash := encode(digest(p_data::text, 'sha256'), 'hex');
    
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

-- ============================================================================
-- KOMMENTARE
-- ============================================================================

\echo '>>> Füge Kommentare hinzu'

COMMENT ON SCHEMA din18599 IS 'DIN 18599 IFC Sidecar - Projekt-Management und Kataloge';
COMMENT ON TABLE din18599.projects IS 'Energieberatungs-Projekte';
COMMENT ON TABLE din18599.sidecars IS 'Versionierte Sidecar-JSONs';
COMMENT ON TABLE din18599.catalogs IS 'Kataloge (Bundesanzeiger, Custom)';
COMMENT ON TABLE din18599.audit_log IS 'Audit-Trail für alle Änderungen';
COMMENT ON TABLE din18599.users IS 'Benutzer (optional)';
COMMENT ON TABLE din18599.project_members IS 'Projekt-Team (Multi-User-Zugriff)';

\echo '>>> Migration 001 erfolgreich abgeschlossen!'
