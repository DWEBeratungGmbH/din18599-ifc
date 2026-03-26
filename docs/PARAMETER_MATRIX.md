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
| **`zones[].volume_v`** | Float | m³ | Nettoraumvolumen ($V_i$) | Teil 1 |
| **`zones[].space_guids`** | Array | UUID | Liste der verknüpften IFC-Räume (`IfcSpace`) | - |
| **`zones[].air_change_n50`** | Float | 1/h | Luftwechselrate bei 50 Pa (Dichtheit) | Teil 2 |
| **`zones[].design_temp_heating`** | Float | °C | Soll-Temperatur Heizen ($\vartheta_{i,h}$) | Teil 10 |
| **`zones[].design_temp_cooling`** | Float | °C | Soll-Temperatur Kühlen ($\vartheta_{i,c}$) | Teil 10 |
| **`zones[].lighting_control`** | Enum | - | `MANUAL`, `PRESENCE`, `DAYLIGHT`, `FULL_AUTO` | Teil 4 |

### 1.2 Bauteile & Hülle (DIN 18599-2)

Verknüpft mit IFC-Elementen (`IfcWall`, `IfcSlab`, `IfcWindow`).

**Opake Bauteile (Wände, Decken, Dächer):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`elements[].ifc_guid`** | UUID | - | Referenz zum IFC-Objekt | - |
| **`elements[].boundary_condition`** | Enum | - | `EXTERIOR`, `GROUND`, `UNHEATED`, `HEATED`, `ADIABATIC` | Teil 2 ($) |
| **`elements[].u_value_undisturbed`** | Float | W/m²K | U-Wert im Gefach (ohne Wärmebrücken) | Teil 2 |
| **`elements[].thermal_bridge_delta_u`** | Float | W/m²K | Wärmebrückenzuschlag ($\Delta U_{WB}$) | Teil 2 |
| **`elements[].thermal_bridge_type`** | Enum | - | `DEFAULT` (0.10), `REDUCED` (0.05), `DETAILED` | Teil 2 |
| **`elements[].solar_absorption`** | Float | 0..1 | Absorptionsgrad der Oberfläche ($\alpha$) | Teil 2 |
| **`elements[].orientation`** | Float | Grad | Ausrichtung (0=Nord, 90=Ost...), falls nicht aus IFC | Teil 2 |
| **`elements[].inclination`** | Float | Grad | Neigung (0=Horizontal, 90=Vertikal), falls nicht aus IFC | Teil 2 |
| **`elements[].layer_structure_ref`** | UUID | - | Referenz auf Schichtaufbau (optional) | - |

**Transparente Bauteile (Fenster, Türen):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`windows[].ifc_guid`** | UUID | - | Referenz zu `IfcWindow`/`IfcDoor` | - |
| **`windows[].u_value_glass`** | Float | W/m²K | U-Wert Verglasung ($) | Teil 2 |
| **`windows[].u_value_frame`** | Float | W/m²K | U-Wert Rahmen ($) | Teil 2 |
| **`windows[].psi_spacer`** | Float | W/mK | Psi-Wert Randverbund ($\Psi_g$) | Teil 2 |
| **`windows[].g_value`** | Float | 0..1 | Gesamtenergiedurchlassgrad ($) | Teil 2 |
| **`windows[].frame_fraction`** | Float | 0..1 | Rahmenanteil ($) | Teil 2 |
| **`windows[].shading_factor_fs`** | Float | 0..1 | Verschattungsfaktor ($) pauschal | Teil 2 |
| **`windows[].horizon_angle`** | Float | Grad | Horizontüberhöhungswinkel (für detaillierte Verschattung) | Teil 2 |
| **`windows[].overhang_angle`** | Float | Grad | Überhangwinkel (Vordach/Balkon) | Teil 2 |

### 1.3 Anlagentechnik (DIN 18599-5 bis 9)

**Wärmeerzeuger (Heizung):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`systems[].id`** | UUID | - | ID des Erzeugers | - |
| **`systems[].type`** | Enum | - | `BOILER_GAS`, `BOILER_OIL`, `HEAT_PUMP_AIR`, `HEAT_PUMP_BRINE`, `DISTRICT_HEATING`... | Teil 5 |
| **`systems[].energy_source`** | Enum | - | `GAS`, `OIL`, `ELECTRICITY`, `WOOD`, `DISTRICT` | - |
| **`systems[].year_built`** | Int | Jahr | Baujahr | - |
| **`systems[].condensing`** | Bool | - | Brennwerttechnik | Teil 5 |
| **`systems[].operation_mode`** | Enum | - | `MONOVALENT`, `MONOENERGETIC`, `BIVALENT_PARALLEL`, `BIVALENT_ALTERNATIVE` | Teil 5 |
| **`systems[].bivalence_temp`** | Float | °C | Bivalenztemperatur ({biv}$) | Teil 5 |
| **`systems[].heat_pump.cop_a2_w35`** | Float | - | COP bei A2/W35 | Teil 5 |
| **`systems[].heat_pump.cop_a7_w35`** | Float | - | COP bei A7/W35 | Teil 5 |
| **`systems[].heat_pump.refrigerant`** | String | - | Kältemittel (z.B. R290, R410a) | - |

**Wärmeverteilung (Distribution):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`distribution[].type`** | Enum | - | `TWO_PIPE`, `ONE_PIPE`, `TICHELMANN` | Teil 5 |
| **`distribution[].temp_flow_design`** | Float | °C | Auslegungsvorlauftemperatur | Teil 5 |
| **`distribution[].temp_return_design`** | Float | °C | Auslegungsrücklauftemperatur | Teil 5 |
| **`distribution[].pipe_insulation`** | Enum | - | `NONE`, `100_PERCENT`, `50_PERCENT`, `ENEV` | Teil 5 |
| **`distribution[].hydraulic_balance`** | Bool | - | Hydraulischer Abgleich durchgeführt? | Teil 5 |
| **`distribution[].pump_control`** | Enum | - | `UNCONTROLLED`, `PRESSURE_CONTROLLED`, `ADAPTIVE` | Teil 5 |

**Trinkwarmwasser (DHW):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`dhw[].type`** | Enum | - | `CENTRAL`, `DECENTRAL_ELECTRIC`, `DECENTRAL_GAS` | Teil 8 |
| **`dhw[].storage_volume`** | Float | Liter | Speichervolumen ({S}$) | Teil 8 |
| **`dhw[].storage_loss_factor`** | Float | W/K | Bereitschaftsverlust ( \cdot A$) | Teil 8 |
| **`dhw[].circulation`** | Bool | - | Zirkulationsleitung vorhanden? | Teil 8 |
| **`dhw[].circulation_length`** | Float | m | Länge der Zirkulationsleitung | Teil 8 |
| **`dhw[].pipe_insulation`** | Enum | - | `NONE`, `100_PERCENT`, `ENEV` | Teil 8 |

**Lüftung (Ventilation):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`ventilation[].type`** | Enum | - | `WINDOW`, `EXHAUST_ONLY`, `SUPPLY_EXHAUST` | Teil 6 |
| **`ventilation[].heat_recovery`** | Bool | - | Wärmerückgewinnung (WRG) vorhanden? | Teil 6 |
| **`ventilation[].heat_recovery_efficiency`** | Float | 0..1 | Rückwärmezahl ($\eta_{WRG}$) | Teil 6 |
| **`ventilation[].volume_flow`** | Float | m³/h | Auslegungsvolumenstrom | Teil 6 |
| **`ventilation[].spf_fan`** | Float | Wh/m³ | Spezifische Ventilatorleistung ({el}$) | Teil 6 |

**Beleuchtung (Lighting) - DIN 18599-4:**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`lighting[].zone_id`** | UUID | - | Referenz zur Zone | Teil 4 |
| **`lighting[].technology`** | Enum | - | `LED`, `FLUORESCENT`, `HALOGEN`, `INCANDESCENT` | Teil 4 |
| **`lighting[].control`** | Enum | - | `MANUAL`, `PRESENCE`, `DAYLIGHT`, `CONSTANT_LIGHT` | Teil 4 |
| **`lighting[].installed_power`** | Float | W/m² | Installierte Leistung ($) | Teil 4 |

**Automation (DIN 18599-11):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`automation.class`** | Enum | - | `A` (High Performance), `B` (Advanced), `C` (Standard), `D` (None) | Teil 11 |

**Photovoltaik (PV):**

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`pv[].peak_power`** | Float | kWp | Nennleistung ({pk}$) | Teil 9 |
| **`pv[].orientation`** | Float | Grad | Ausrichtung (180=Süd) | Teil 9 |
| **`pv[].inclination`** | Float | Grad | Neigung | Teil 9 |
| **`pv[].system_loss`** | Float | 0..1 | Systemverluste (Kabel, Wechselrichter), typ. 0.14-0.20 | Teil 9 |
| **`pv[].battery_capacity`** | Float | kWh | Batteriespeicher (optional) | - |

---

## 2. OUTPUT: Snapshot (Ergebnisdaten)

Ergebnisse eines Berechnungslaufs. Read-Only.

### 2.1 Energiebilanz (Bedarf & Verbrauch)

| Parameter | Typ | Einheit | Beschreibung | DIN Referenz |
| :--- | :--- | :--- | :--- | :--- |
| **`results.final_energy`** | Float | kWh/a | Endenergiebedarf ($) | - |
| **`results.primary_energy`** | Float | kWh/a | Primärenergiebedarf ($) | - |
| **`results.useful_energy`** | Float | kWh/a | Nutzenergiebedarf ($) | - |
| **`results.energy_reference_area`** | Float | m² | Energiebezugsfläche ($) | Teil 1 |

### 2.2 Sektorale Aufschlüsselung

| Parameter | Typ | Einheit | Beschreibung |
| :--- | :--- | :--- | :--- |
| **`results.sectors.heating`** | Float | kWh/a | Heizung ({h,E}$) |
| **`results.sectors.cooling`** | Float | kWh/a | Kühlung ({c,E}$) |
| **`results.sectors.dhw`** | Float | kWh/a | Warmwasser ({w,E}$) |
| **`results.sectors.ventilation`** | Float | kWh/a | Lüftung/Hilfsenergie ({v,E}$) |
| **`results.sectors.lighting`** | Float | kWh/a | Beleuchtung ({l,E}$) |

### 2.3 Bewertung & GEG-Nachweis

| Parameter | Typ | Einheit | Beschreibung |
| :--- | :--- | :--- | :--- |
| **`results.qp_val`** | Float | kWh/m²a | Primärenergie Ist-Wert ($) |
| **`results.qp_ref`** | Float | kWh/m²a | Primärenergie Anforderung ({p,ref}$) |
| **`results.ht_prime_val`** | Float | W/m²K | Transmissionswärmeverlust ('_T$) |
| **`results.ht_prime_ref`** | Float | W/m²K | Anforderung '_T$ |
| **`results.efficiency_class`** | String | - | Energieeffizienzklasse (A+ bis H) |
| **`results.co2_emissions`** | Float | kg/a | CO2-Emissionen (Gesamt) |
| **`results.renewable_share`** | Float | % | Anteil erneuerbarer Energien (EE-Klasse) |

