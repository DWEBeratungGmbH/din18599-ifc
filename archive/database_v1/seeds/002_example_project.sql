-- ============================================================================
-- Seed 002: Beispiel-Projekt (LOD 400)
-- ============================================================================
-- Beschreibung: Erstellt Beispiel-Projekt mit LOD 400 Sidecar
-- Quelle: examples/lod400_geg_nachweis.din18599.json
-- ============================================================================

\echo '>>> Seed 002: Beispiel-Projekt (LOD 400)'

-- Projekt erstellen
INSERT INTO din18599.projects (
    id,
    name,
    description,
    ifc_file_path,
    ifc_guid_building
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Musterhaus - GEG-Nachweis',
    'Beispiel-Projekt für LOD 400 (GEG-Nachweis mit vollständigen Schichtaufbauten)',
    'examples/musterhaus.ifc',
    '2Uj8Lq3Vr9QxPkXr4bN8FD'
) ON CONFLICT (id) DO NOTHING;

-- Sidecar-Version erstellen (aus JSON-Datei)
DO $$
DECLARE
    v_sidecar_data JSONB;
    v_sidecar_id UUID;
BEGIN
    -- JSON aus Datei laden
    SELECT content::jsonb INTO v_sidecar_data
    FROM pg_read_file('/opt/din18599-ifc/examples/lod400_geg_nachweis.din18599.json') AS content;
    
    -- Sidecar-Version erstellen
    SELECT din18599.create_sidecar_version(
        '00000000-0000-0000-0000-000000000001',
        v_sidecar_data,
        'Initial Version (LOD 400)',
        NULL
    ) INTO v_sidecar_id;
    
    RAISE NOTICE 'Sidecar erstellt: %', v_sidecar_id;
END $$;

\echo '>>> Beispiel-Projekt erstellt'

-- Statistik ausgeben
DO $$
DECLARE
    v_project_count INT;
    v_sidecar_count INT;
BEGIN
    SELECT COUNT(*) INTO v_project_count FROM din18599.projects WHERE deleted_at IS NULL;
    SELECT COUNT(*) INTO v_sidecar_count FROM din18599.sidecars WHERE deleted_at IS NULL;
    
    RAISE NOTICE 'Projekte in DB: %', v_project_count;
    RAISE NOTICE 'Sidecars in DB: %', v_sidecar_count;
END $$;
