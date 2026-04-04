-- ============================================================================
-- Seed 001: Bundesanzeiger 2020 Katalog
-- ============================================================================
-- Beschreibung: Importiert Bundesanzeiger 2020 U-Werte
-- Quelle: catalogs/constructions/de-bmwi2020-bauteile-v1.0.json
-- ============================================================================

\echo '>>> Seed 001: Bundesanzeiger 2020 Katalog'

-- Katalog-Eintrag erstellen
INSERT INTO din18599.catalogs (
    catalog_id,
    version,
    name,
    description,
    type,
    source,
    source_url,
    valid_from,
    data
) VALUES (
    'DE_BMWI2020_BAUTEILE',
    '1.0.0',
    'Bundesanzeiger 2020 - Bauteile nach Baujahr',
    'Offizielle U-Werte aus Bundesanzeiger AT 04.12.2020 B1 für die Verwendung in der Energieberatung (BEG-konform)',
    'CONSTRUCTIONS',
    'Bundesanzeiger AT 04.12.2020 B1',
    'https://www.bundesanzeiger.de',
    '2020-12-04',
    -- JSON-Daten aus Datei laden
    (SELECT data FROM json_populate_record(null::record, 
        pg_read_file('/opt/din18599-ifc/catalogs/constructions/de-bmwi2020-bauteile-v1.0.json')::json
    ) AS data)
) ON CONFLICT (catalog_id, version) DO NOTHING;

\echo '>>> Bundesanzeiger-Katalog importiert'

-- Statistik ausgeben
DO $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM din18599.catalogs
    WHERE catalog_id = 'DE_BMWI2020_BAUTEILE';
    
    RAISE NOTICE 'Kataloge in DB: %', v_count;
END $$;
