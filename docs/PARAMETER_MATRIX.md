# Parameter Matrix: IFC + DIN 18599 Sidecar

Diese Matrix definiert die Datenpunkte, die im Sidecar (`*.din18599.json`) gespeichert werden.
Sie ist unterteilt in **INPUT** (Eingabedaten für die Berechnung) und **OUTPUT** (Ergebnisse der Berechnung).

---

## 1. INPUT: Definition (Eingabedaten)

Daten, die den energetischen Zustand des Gebäudes beschreiben.

### 1.1 Topologie & Zonierung (DIN 18599-1)

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`zones[].id`** | UUID | - | Eindeutige ID der thermischen Zone | - |
| **`zones[].name`** | String | - | Bezeichnung (z.B. "Büro Süd") | - |
| **`zones[].usage_profile`** | Code | - | Nutzungsprofil (z.B. "17" für Einzelbüro) | DIN 18599-10 |
| **`zones[].area_an`** | Float | m² | Energiebezugsfläche der Zone ($A_N$) | Teil 1 |
| **`zones[].height_h`** | Float | m | Lichte Raumhöhe (mittlere) | Teil 1 |
| **`zones[].space_guids`** | Array | UUID | Liste der verknüpften IFC-Räume (`IfcSpace`) | - |
| **`zones[].air_change_n50`** | Float | 1/h | Luftwechselrate bei 50 Pa (Dichtheit) | Teil 2 |

### 1.2 Bauteile & Hülle (DIN 18599-2)

Verknüpft mit IFC-Elementen (`IfcWall`, `IfcSlab`, `IfcWindow`).

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`elements[].ifc_guid`** | UUID | - | Referenz zum IFC-Objekt | - |
| **`elements[].boundary_condition`** | Enum | - | `EXTERIOR`, `GROUND`, `UNHEATED`, `HEATED` | Teil 2 (Fx) |
| **`elements[].u_value`** | Float | W/m²K | Wärmedurchgangskoeffizient | Teil 2 |
| **`elements[].thermal_bridge_delta_u`** | Float | W/m²K | Wärmebrückenzuschlag ($\Delta U_{WB}$) | Teil 2 |
| **`elements[].orientation`** | Float | Grad | Ausrichtung (0=Nord, 90=Ost...), falls nicht aus IFC | Teil 2 |
| **`elements[].inclination`** | Float | Grad | Neigung (0=Horizontal, 90=Vertikal), falls nicht aus IFC | Teil 2 |
| **`elements[].layer_structure`** | Array | Object | Optional: Schichtaufbau für U-Wert-Berechnung | - |

**Spezifisch für Fenster:**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`windows[].g_value_tot`** | Float | - | Gesamtenergiedurchlassgrad ($g_{tot}$) | Teil 2 |
| **`windows[].frame_fraction`** | Float | 0..1 | Rahmenanteil ($F_F$) | Teil 2 |
| **`windows[].shading_factor_fs`** | Float | 0..1 | Verschattungsfaktor ($F_S$) durch Umgebung | Teil 2 |

### 1.3 Materialien & Ökobilanz (QNG/LCA)

| Parameter | Typ | Einheit | Beschreibung | Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`materials[].name`** | String | - | Materialname | - |
| **`materials[].lambda`** | Float | W/mK | Wärmeleitfähigkeit | - |
| **`materials[].density`** | Float | kg/m³ | Rohdichte | - |
| **`materials[].oekobau_uuid`** | UUID | - | ID in der Ökobaudat (für LCA/QNG) | Ökobaudat |

### 1.4 Anlagentechnik (DIN 18599-5 bis 9)

Struktur: **Erzeuger -> Speicher -> Verteilung -> Übergabe -> Zone**

**Erzeuger (Generation):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`systems[].type`** | Enum | - | `BOILER_GAS`, `HEAT_PUMP_AIR`, `DISTRICT_HEATING`... | Teil 5/8 |
| **`systems[].year_built`** | Int | Jahr | Baujahr (Effizienz, Austauschpflicht) | - |
| **`systems[].condensing`** | Bool | - | Brennwerttechnik (Ja/Nein) | Teil 5 |
| **`systems[].cop_a2_w35`** | Float | - | COP bei A2/W35 (nur Wärmepumpe) | Teil 5 |
| **`systems[].refrigerant_gwp`** | Float | - | GWP des Kältemittels (nur WP/Klima) | Förderung |
| **`systems[].biomass_type`** | Enum | - | `PELLET`, `LOG_WOOD`, `CHIPS` | Teil 5 |

**Speicher & Übergabe:**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`storage[].volume`** | Float | Liter | Speichervolumen (Puffer/Trinkwasser) | Teil 8 |
| **`emission[].type`** | Enum | - | `RADIATOR`, `FLOOR_HEATING`, `PANEL` | Teil 5 |
| **`emission[].system_temp_flow`** | Float | °C | Vorlauftemperatur (Auslegung) | Teil 5 |
| **`emission[].system_temp_return`** | Float | °C | Rücklauftemperatur | Teil 5 |
| **`ventilation[].heat_recovery_efficiency`** | Float | % | Wärmerückgewinnungsgrad (Lüftung) | Teil 6 |

---

## 2. OUTPUT: Snapshot (Ergebnisdaten)

Ergebnisse eines Berechnungslaufs. Diese Daten sind **read-only** und dienen der Anzeige/Weiterverarbeitung.

### 2.1 Energiebilanz (Bedarf)

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`results.final_energy`** | Float | kWh/a | Endenergiebedarf ($Q_E$) | - |
| **`results.primary_energy`** | Float | kWh/a | Primärenergiebedarf ($Q_P$) | - |
| **`results.useful_energy`** | Float | kWh/a | Nutzenergiebedarf ($Q_N$) | - |
| **`results.sectors.heating`** | Float | kWh/a | Anteil Heizung | - |
| **`results.sectors.cooling`** | Float | kWh/a | Anteil Kühlung | - |
| **`results.sectors.dhw`** | Float | kWh/a | Anteil Warmwasser | - |
| **`results.sectors.lighting`** | Float | kWh/a | Anteil Beleuchtung | - |

### 2.2 Bewertung & Indikatoren

| Parameter | Typ | Einheit | Beschreibung | Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`results.qp_ref`** | Float | kWh/m²a | Primärenergie Referenzgebäude | GEG |
| **`results.ht_prime`** | Float | W/m²K | Spezifischer Transmissionswärmeverlust ($H'_T$) | GEG |
| **`results.ht_prime_ref`** | Float | W/m²K | Grenzwert $H'_T$ (Referenz) | GEG |
| **`results.efficiency_class`** | String | - | Energieeffizienzklasse (A+ bis H) | Energieausweis |
| **`results.co2_emissions`** | Float | kg/a | CO2-Emissionen (Gesamt) | - |
| **`results.share_renewable`** | Float | % | Anteil erneuerbarer Energien (EE-Klasse) | GEG |

### 2.3 Validierung

| Parameter | Typ | Beschreibung |
| :--- | :--- | :--- |
| **`meta.software_name`** | String | Name der berechnenden Software |
| **`meta.software_version`** | String | Version des Kernels |
| **`meta.calculation_date`** | ISO8601 | Zeitstempel der Berechnung |
| **`meta.norm_version`** | String | Angewandte Norm (z.B. "DIN V 18599:2018-09") |
