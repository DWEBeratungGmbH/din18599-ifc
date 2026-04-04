-- ============================================================================
-- DIN 18599 IFC Sidecar - Migration v2.0 → v2.1
-- ============================================================================
-- Version: 2.1.0
-- Datum: 1. April 2026
-- Beschreibung: Erweitert Schema für v2.1 Features (BuildingElements, neue Felder)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. SCHEMA-VERSION TRACKING
-- ============================================================================

-- Neue Spalte für Schema-Version
ALTER TABLE din18599.sidecars 
ADD COLUMN IF NOT EXISTS schema_version VARCHAR(10) DEFAULT '2.0';

COMMENT ON COLUMN din18599.sidecars.schema_version IS 'DIN 18599 Schema Version (2.0, 2.1, 2.2, etc.)';

-- Bestehende Daten auf v2.0 setzen
UPDATE din18599.sidecars 
SET schema_version = '2.0'
WHERE schema_version IS NULL;

-- ============================================================================
-- 2. GIN INDIZES FÜR NEUE FELDER
-- ============================================================================

-- Index für BuildingElements (LOD 300+)
CREATE INDEX IF NOT EXISTS idx_sidecars_building_elements 
ON din18599.sidecars USING GIN ((data->'input'->'building_elements'))
WHERE data->'input' ? 'building_elements';

COMMENT ON INDEX din18599.idx_sidecars_building_elements IS 'Fast lookup für BuildingElements (Treppen, Korrekturen)';

-- Index für Scenarios
CREATE INDEX IF NOT EXISTS idx_sidecars_scenarios 
ON din18599.sidecars USING GIN ((data->'scenarios'))
WHERE data ? 'scenarios';

COMMENT ON INDEX din18599.idx_sidecars_scenarios IS 'Fast lookup für Sanierungsszenarien';

-- Index für Envelope (Gebäudehülle)
CREATE INDEX IF NOT EXISTS idx_sidecars_envelope 
ON din18599.sidecars USING GIN ((data->'input'->'envelope'))
WHERE data->'input' ? 'envelope';

COMMENT ON INDEX din18599.idx_sidecars_envelope IS 'Fast lookup für Gebäudehülle (Wände, Dächer, Böden, Öffnungen)';

-- Index für Openings (Parent-Child Queries)
CREATE INDEX IF NOT EXISTS idx_sidecars_openings 
ON din18599.sidecars USING GIN ((data->'input'->'envelope'->'openings'))
WHERE data->'input'->'envelope' ? 'openings';

COMMENT ON INDEX din18599.idx_sidecars_openings IS 'Fast lookup für Fenster/Türen (Parent-Child Beziehungen)';

-- Index für Systems (Anlagentechnik)
CREATE INDEX IF NOT EXISTS idx_sidecars_systems 
ON din18599.sidecars USING GIN ((data->'input'->'systems'))
WHERE data->'input' ? 'systems';

COMMENT ON INDEX din18599.idx_sidecars_systems IS 'Fast lookup für Heizung, Lüftung, Warmwasser';

-- ============================================================================
-- 3. VALIDIERUNGS-FUNKTION
-- ============================================================================

-- Basis-Validierung für Sidecar-Struktur
CREATE OR REPLACE FUNCTION din18599.validate_sidecar_schema(data JSONB)
RETURNS BOOLEAN AS $$
DECLARE
    schema_ver TEXT;
BEGIN
    -- Prüfe ob meta.schema_version existiert
    IF NOT (data ? 'meta' AND data->'meta' ? 'schema_version') THEN
        RAISE EXCEPTION 'Missing meta.schema_version';
    END IF;
    
    schema_ver := data->'meta'->>'schema_version';
    
    -- Prüfe ob Version gültig ist
    IF schema_ver NOT IN ('2.0', '2.1', '2.2') THEN
        RAISE EXCEPTION 'Invalid schema_version: %. Allowed: 2.0, 2.1, 2.2', schema_ver;
    END IF;
    
    -- Prüfe ob input existiert
    IF NOT (data ? 'input') THEN
        RAISE EXCEPTION 'Missing input section';
    END IF;
    
    -- Prüfe ob input.building existiert
    IF NOT (data->'input' ? 'building') THEN
        RAISE EXCEPTION 'Missing input.building section';
    END IF;
    
    -- Prüfe ob input.zones existiert (optional für LOD 100)
    -- Warnung: Keine Exception, nur Log
    IF NOT (data->'input' ? 'zones') THEN
        RAISE NOTICE 'Missing input.zones - OK for LOD 100, but required for LOD 200+';
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION din18599.validate_sidecar_schema IS 'Validiert Basis-Struktur des Sidecar JSON (meta, input, building)';

-- ============================================================================
-- 4. CONSTRAINT FÜR VALIDIERUNG (Optional - kann deaktiviert werden)
-- ============================================================================

-- Constraint hinzufügen (nur für neue Einträge)
-- WICHTIG: Kann bei Problemen mit ALTER TABLE ... DROP CONSTRAINT entfernt werden
DO $$
BEGIN
    -- Prüfe ob Constraint bereits existiert
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'sidecars_data_valid'
    ) THEN
        ALTER TABLE din18599.sidecars
        ADD CONSTRAINT sidecars_data_valid 
        CHECK (din18599.validate_sidecar_schema(data));
        
        RAISE NOTICE 'Constraint sidecars_data_valid hinzugefügt';
    ELSE
        RAISE NOTICE 'Constraint sidecars_data_valid existiert bereits';
    END IF;
END $$;

-- ============================================================================
-- 5. HELPER FUNCTIONS FÜR QUERIES
-- ============================================================================

-- Funktion: Hole alle BuildingElements eines Projekts
CREATE OR REPLACE FUNCTION din18599.get_building_elements(p_project_id UUID)
RETURNS TABLE (
    sidecar_id UUID,
    element_id TEXT,
    element_type TEXT,
    element_name TEXT,
    element_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS sidecar_id,
        elem->>'id' AS element_id,
        elem->>'type' AS element_type,
        elem->>'name' AS element_name,
        elem AS element_data
    FROM din18599.sidecars s,
         LATERAL jsonb_array_elements(s.data->'input'->'building_elements') AS elem
    WHERE s.project_id = p_project_id
      AND s.is_current = true
      AND s.deleted_at IS NULL
      AND s.data->'input' ? 'building_elements';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION din18599.get_building_elements IS 'Extrahiert alle BuildingElements aus dem aktuellen Sidecar';

-- Funktion: Hole alle Öffnungen mit Parent-Referenz
CREATE OR REPLACE FUNCTION din18599.get_openings_with_parent(p_project_id UUID)
RETURNS TABLE (
    sidecar_id UUID,
    opening_id TEXT,
    opening_name TEXT,
    parent_element_id TEXT,
    parent_element_type TEXT,
    opening_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS sidecar_id,
        opening->>'id' AS opening_id,
        opening->>'name' AS opening_name,
        opening->>'parent_element_id' AS parent_element_id,
        opening->>'parent_element_type' AS parent_element_type,
        opening AS opening_data
    FROM din18599.sidecars s,
         LATERAL jsonb_array_elements(s.data->'input'->'envelope'->'openings') AS opening
    WHERE s.project_id = p_project_id
      AND s.is_current = true
      AND s.deleted_at IS NULL
      AND s.data->'input'->'envelope' ? 'openings';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION din18599.get_openings_with_parent IS 'Extrahiert alle Öffnungen mit Parent-Referenz (Fenster in Wänden)';

-- Funktion: Hole alle Szenarien eines Projekts
CREATE OR REPLACE FUNCTION din18599.get_scenarios(p_project_id UUID)
RETURNS TABLE (
    sidecar_id UUID,
    scenario_id TEXT,
    scenario_name TEXT,
    total_cost NUMERIC,
    total_funding NUMERIC,
    energy_savings NUMERIC,
    scenario_data JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS sidecar_id,
        scenario->>'id' AS scenario_id,
        scenario->>'name' AS scenario_name,
        (scenario->'costs'->>'total')::NUMERIC AS total_cost,
        (scenario->'costs'->>'funding')::NUMERIC AS total_funding,
        (scenario->'output'->'savings'->>'energy_kwh_a')::NUMERIC AS energy_savings,
        scenario AS scenario_data
    FROM din18599.sidecars s,
         LATERAL jsonb_array_elements(s.data->'scenarios') AS scenario
    WHERE s.project_id = p_project_id
      AND s.is_current = true
      AND s.deleted_at IS NULL
      AND s.data ? 'scenarios';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION din18599.get_scenarios IS 'Extrahiert alle Sanierungsszenarien mit Kosten und Einsparungen';

-- ============================================================================
-- 6. VIEWS FÜR REPORTING
-- ============================================================================

-- View: Aktuelle Projekte mit LOD und Schema-Version
CREATE OR REPLACE VIEW din18599.v_projects_overview AS
SELECT 
    p.id AS project_id,
    p.name AS project_name,
    p.description,
    p.ifc_file_path,
    s.id AS sidecar_id,
    s.version AS sidecar_version,
    s.schema_version,
    s.lod,
    s.mode,
    s.data->'meta'->>'project_name' AS sidecar_project_name,
    (s.data->'input'->'zones' IS NOT NULL) AS has_zones,
    (s.data->'input'->'building_elements' IS NOT NULL) AS has_building_elements,
    (s.data->'scenarios' IS NOT NULL) AS has_scenarios,
    jsonb_array_length(COALESCE(s.data->'input'->'zones', '[]'::jsonb)) AS zone_count,
    jsonb_array_length(COALESCE(s.data->'input'->'building_elements', '[]'::jsonb)) AS building_element_count,
    jsonb_array_length(COALESCE(s.data->'scenarios', '[]'::jsonb)) AS scenario_count,
    s.created_at AS sidecar_created_at,
    p.updated_at AS project_updated_at
FROM din18599.projects p
LEFT JOIN din18599.sidecars s ON s.project_id = p.id AND s.is_current = true AND s.deleted_at IS NULL
WHERE p.deleted_at IS NULL
ORDER BY p.updated_at DESC;

COMMENT ON VIEW din18599.v_projects_overview IS 'Übersicht aller Projekte mit aktuellem Sidecar und Statistiken';

-- ============================================================================
-- 7. MIGRATION ABSCHLUSS
-- ============================================================================

-- Log Migration
INSERT INTO din18599.audit_log (
    action,
    entity_type,
    changes,
    user_agent
) VALUES (
    'UPDATE',
    'CATALOG',
    jsonb_build_object(
        'migration', '001_schema_v2.1',
        'description', 'Schema v2.0 → v2.1 Migration',
        'changes', jsonb_build_array(
            'Added schema_version column',
            'Added GIN indexes for BuildingElements, Scenarios, Envelope',
            'Added validation function',
            'Added helper functions for queries',
            'Added v_projects_overview view'
        )
    ),
    'PostgreSQL Migration Script'
);

COMMIT;

-- ============================================================================
-- MIGRATION ERFOLGREICH
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001_schema_v2.1 erfolgreich abgeschlossen!';
    RAISE NOTICE '';
    RAISE NOTICE 'Neue Features:';
    RAISE NOTICE '  - schema_version Spalte';
    RAISE NOTICE '  - GIN Indizes für schnelle Queries';
    RAISE NOTICE '  - Validierungs-Funktion';
    RAISE NOTICE '  - Helper Functions (get_building_elements, get_openings_with_parent, get_scenarios)';
    RAISE NOTICE '  - View: v_projects_overview';
    RAISE NOTICE '';
    RAISE NOTICE 'Nächste Schritte:';
    RAISE NOTICE '  1. Parser implementieren (TypeScript)';
    RAISE NOTICE '  2. CLI Tool für Import/Export';
    RAISE NOTICE '  3. Testing (Roundtrip)';
END $$;
