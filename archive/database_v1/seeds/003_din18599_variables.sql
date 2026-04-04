-- ============================================================================
-- DIN 18599 Variablen-Registry - Seed Data
-- ============================================================================
-- Quelle: catalog/din18599_variables.json
-- Tabelle 1: Symbole, Tabelle 2: Indizes, Tabelle 3+4: Ein-/Ausgangsgrößen
-- ============================================================================

-- Tabelle 1: Symbole
INSERT INTO din18599.variables (
    symbol, symbol_latex, name_de, name_en, unit, unit_latex,
    data_type, min_value, max_value,
    din_part, din_table, din_section,
    used_in, category, scope, required,
    calculation_method, default_values, schema_path
) VALUES
-- Temperaturen
('theta_i_h_soll', '\theta_{i,h,soll}', 'Raum-Solltemperatur Heizung', 'Room set-point temperature heating', '°C', '°C',
 'number', NULL, NULL,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5',
 ARRAY['DIN/TS 18599-2', 'DIN/TS 18599-5', 'DIN/TS 18599-8'], 'temperature', 'zone', true,
 'manual', '{"residential_efh": 20, "residential_mfh": 20}'::jsonb, 'zones[].usage_profile.parameters_din.theta_i_h_soll'),

('theta_i_c_soll', '\theta_{i,c,soll}', 'Raum-Solltemperatur Kühlung', 'Room set-point temperature cooling', '°C', '°C',
 'number', NULL, NULL,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5',
 ARRAY['DIN/TS 18599-2'], 'temperature', 'zone', true,
 'manual', '{"residential_efh": 25, "residential_mfh": 25}'::jsonb, 'zones[].usage_profile.parameters_din.theta_i_c_soll'),

('delta_theta_i_NA', '\Delta\theta_{i,NA}', 'Temperaturabsenkung reduzierter Betrieb', 'Temperature reduction during reduced operation', 'K', 'K',
 'number', NULL, NULL,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5',
 ARRAY['DIN/TS 18599-2'], 'temperature', 'zone', true,
 'manual', '{"residential": 4}'::jsonb, 'zones[].usage_profile.parameters_din.delta_theta_i_na'),

-- Wärmebrücken & Transmission
('F_x', 'F_x', 'Temperaturfaktor', 'Temperature correction factor', '-', '-',
 'number', 0, 1,
 'DIN/TS 18599-2', 'Tabelle 5+6', NULL,
 ARRAY['DIN/TS 18599-2'], 'thermal_transmission', 'element', false,
 'automatic', NULL, 'elements[].f_x'),

-- Interne Lasten
('q_I', 'q_I', 'Interne Wärmequellen', 'Internal heat sources', 'Wh/(m²·d)', 'Wh/(m^2 \cdot d)',
 'number', NULL, NULL,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5',
 ARRAY['DIN/TS 18599-2'], 'internal_gains', 'zone', true,
 'manual', '{"residential_efh": 45, "residential_mfh": 90}'::jsonb, 'zones[].usage_profile.parameters_din.q_i'),

('q_el_b', 'q_{el,b}', 'Anwendungsstrombedarf', 'Electrical energy demand for appliances', 'Wh/(m²·d)', 'Wh/(m^2 \cdot d)',
 'number', NULL, NULL,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5',
 ARRAY['DIN/TS 18599-9'], 'electrical_energy', 'zone', true,
 'manual', '{"residential": 63}'::jsonb, 'zones[].usage_profile.parameters_din.q_el_b'),

-- Lüftung
('n_nutz', 'n_{nutz}', 'Nutzungsbedingter Mindestaußenluftwechsel', 'User-related minimum air change rate', '1/h', 'h^{-1}',
 'number', 0, NULL,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5',
 ARRAY['DIN/TS 18599-2'], 'ventilation', 'zone', true,
 'manual', '{"residential_not_controlled": 0.5, "residential_central_controlled": 0.45, "residential_room_controlled": 0.4}'::jsonb, 'zones[].usage_profile.parameters_din.n_nutz'),

-- Geometrie
('A', 'A', 'Fläche', 'Area', 'm²', 'm^2',
 'number', 0, NULL,
 'DIN/TS 18599-10', 'Tabelle 1', NULL,
 NULL, 'geometry', 'element', true,
 'automatic', NULL, 'elements[].area'),

-- Nutzungszeiten
('t_nutz_d', 't_{nutz,d}', 'Tägliche Nutzungsstunden', 'Daily hours of use', 'h/d', 'h/d',
 'number', 0, 24,
 'DIN/TS 18599-10', 'Tabelle 6', 'Abschnitt 6',
 ARRAY['DIN/TS 18599-8'], 'usage_time', 'zone', true,
 'manual', NULL, NULL),

('d_nutz_a', 'd_{nutz,a}', 'Jährliche Nutzungstage', 'Annual days of use', 'd/a', 'd/a',
 'number', 0, 365,
 'DIN/TS 18599-10', 'Tabelle 6', 'Abschnitt 6',
 ARRAY['DIN/TS 18599-2', 'DIN/TS 18599-5', 'DIN/TS 18599-8'], 'usage_time', 'zone', true,
 'manual', '{"residential": 365}'::jsonb, NULL);

-- Tabelle 2: Indizes
INSERT INTO din18599.indices (index_symbol, name_de, name_en) VALUES
('i', 'innen', 'indoor, interior'),
('e', 'außen', 'external, exterior, outdoor'),
('h', 'Heizung, Raumheizsystem', 'heating, heating system'),
('c', 'Kühlung, Raumkühlsystem', 'cooling system'),
('soll', 'Sollwert', 'set-point value'),
('a', 'Anteil, Jahr/Jahreswert', 'proportion, Year/annual value'),
('d', 'Tag, Tageswert', 'day, daily value'),
('nutz', 'Nutzung', 'use, during using hours'),
('NA', 'Nachtabschaltung', 'reduced heating operation (night-time set-back)'),
('el', 'elektrisch, elektrische Energie', 'electrical, electric power'),
('b', 'Bedarf', 'use, need, demand'),
('I', 'innere', 'internal'),
('op', 'Betrieb, Betriebszeit', 'operating, operation time'),
('min', 'minimal', 'minimal'),
('max', 'maximal', 'maximum');

-- Tabelle 3+4: Ein-/Ausgangsgrößen
-- Zuerst Variablen-IDs holen (für Foreign Keys)
DO $$
DECLARE
    v_theta_i_h_soll UUID;
    v_n_nutz UUID;
    v_q_I UUID;
BEGIN
    -- IDs holen
    SELECT id INTO v_theta_i_h_soll FROM din18599.variables WHERE symbol = 'theta_i_h_soll';
    SELECT id INTO v_n_nutz FROM din18599.variables WHERE symbol = 'n_nutz';
    SELECT id INTO v_q_I FROM din18599.variables WHERE symbol = 'q_I';
    
    -- Tabelle 3: Eingangsgrößen (INPUT)
    INSERT INTO din18599.interface_variables (
        variable_id, interface_type, source_part, target_part,
        din_table, description_de
    ) VALUES
    -- A_NGF_WE_m wird separat erstellt, da es nicht in variables ist
    (NULL, 'INPUT', 'DIN/TS 18599-1', 'DIN/TS 18599-10',
     'Tabelle 3', 'Mittlere Nettogrundfläche einer Wohnung - wird aus Teil 1 benötigt');
    
    -- Tabelle 4: Ausgangsgrößen (OUTPUT)
    INSERT INTO din18599.interface_variables (
        variable_id, interface_type, source_part, target_part,
        din_table, din_section, description_de
    ) VALUES
    (v_theta_i_h_soll, 'OUTPUT', 'DIN/TS 18599-10', 'DIN/TS 18599-2',
     'Tabelle 4', 'Abschnitt 5 bzw. Abschnitt 6', 'Wird in Teil 2, 5 und 8 benötigt'),
    
    (v_n_nutz, 'OUTPUT', 'DIN/TS 18599-10', 'DIN/TS 18599-2',
     'Tabelle 4', 'Abschnitt 5 bzw. Abschnitt 6', 'Wird in Teil 2 benötigt'),
    
    (v_q_I, 'OUTPUT', 'DIN/TS 18599-10', 'DIN/TS 18599-2',
     'Tabelle 4', 'Abschnitt 5', 'Wird in Teil 2 benötigt');
END $$;

-- Zusätzliche Variable für A_NGF_WE_m (Eingangsgröße)
INSERT INTO din18599.variables (
    symbol, symbol_latex, name_de, name_en, unit, unit_latex,
    data_type, min_value,
    din_part, din_table,
    category, scope, required,
    calculation_method
) VALUES
('A_NGF_WE_m', 'A_{NGF,WE,m}', 'Mittlere Nettogrundfläche einer Wohnung', 'Average net floor area per dwelling unit', 'm²', 'm^2',
 'number', 0,
 'DIN/TS 18599-1', 'Tabelle 3',
 'geometry', 'building', true,
 'manual');

-- F_V (Verschmutzungsfaktor) für Ausgangsgröße
INSERT INTO din18599.variables (
    symbol, symbol_latex, name_de, name_en, unit, unit_latex,
    data_type, min_value, max_value,
    din_part, din_table, din_section,
    used_in, category, scope, required,
    calculation_method, default_values
) VALUES
('F_V', 'F_V', 'Abminderungsfaktor infolge von Verschmutzung', 'Reduction factor due to pollution', '-', '-',
 'number', 0, 1,
 'DIN/TS 18599-10', 'Tabelle 5', 'Abschnitt 5 bzw. Abschnitt 6',
 ARRAY['DIN/TS 18599-2'], 'solar_transmission', 'zone', true,
 'manual', '{"default": 0.95}'::jsonb);

-- Ausgangsgröße F_V hinzufügen
DO $$
DECLARE
    v_F_V UUID;
BEGIN
    SELECT id INTO v_F_V FROM din18599.variables WHERE symbol = 'F_V';
    
    INSERT INTO din18599.interface_variables (
        variable_id, interface_type, source_part, target_part,
        din_table, din_section, description_de
    ) VALUES
    (v_F_V, 'OUTPUT', 'DIN/TS 18599-10', 'DIN/TS 18599-2',
     'Tabelle 4', 'Abschnitt 5 bzw. Abschnitt 6', 'Wird in Teil 2 benötigt');
END $$;

-- Erfolgsmeldung
DO $$
DECLARE
    v_count_variables INT;
    v_count_indices INT;
    v_count_interface INT;
BEGIN
    SELECT COUNT(*) INTO v_count_variables FROM din18599.variables;
    SELECT COUNT(*) INTO v_count_indices FROM din18599.indices;
    SELECT COUNT(*) INTO v_count_interface FROM din18599.interface_variables;
    
    RAISE NOTICE 'DIN 18599 Variablen-Registry erfolgreich geladen:';
    RAISE NOTICE '  - % Symbole (Tabelle 1)', v_count_variables;
    RAISE NOTICE '  - % Indizes (Tabelle 2)', v_count_indices;
    RAISE NOTICE '  - % Ein-/Ausgangsgrößen (Tabelle 3+4)', v_count_interface;
END $$;
