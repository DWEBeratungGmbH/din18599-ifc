# Dynamisches Datenmodell - Progressive Datenerfassung

**Datum:** 29. März 2026 (Nachmittag)  
**Konzept:** Dynamisch erweiterbares Datenmodell statt starre LOD-Stufen  
**Prinzip:** Daten können schrittweise ergänzt werden - LOD ergibt sich aus Vollständigkeit

---

## 🎯 KERNIDEE

**Problem mit starren LODs:**
- ❌ Nicht alle Daten sind zum gleichen Zeitpunkt verfügbar
- ❌ Manche Bauteile sind detailliert bekannt, andere geschätzt
- ❌ Starre Grenzen passen nicht zur Realität

**Lösung: Dynamisches Modell**
- ✅ Jedes Feld kann vorhanden sein oder fehlen
- ✅ LOD bestimmt sich durch **Vollständigkeit** der Daten
- ✅ Gleiche Datei kann von LOD 100 → 300 erweitert werden
- ✅ Software zeigt an: "Für LOD 300 fehlen noch: X, Y, Z"

---

## 📋 VOLLSTÄNDIGE FELDLISTE - ALLE DATEN

### **KATEGORIE 1: GEBÄUDE-STAMMDATEN**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 1.1 | `building.address.street` | Straße + Hausnummer | ✅ | ✅ | ✅ | Energieausweis |
| 1.2 | `building.address.zip` | PLZ | ✅ | ✅ | ✅ | Energieausweis |
| 1.3 | `building.address.city` | Stadt | ✅ | ✅ | ✅ | Energieausweis |
| 1.4 | `building.address.country` | Land | Optional | Optional | ✅ | - |
| 1.5 | `building.construction_year` | Baujahr | ✅ | ✅ | ✅ | Energieausweis |
| 1.6 | `building.renovation_year` | Sanierungsjahr | Optional | Optional | Optional | Energieausweis |
| 1.7 | `building.type` | Gebäudetyp (residential/non_residential) | ✅ | ✅ | ✅ | Energieausweis |
| 1.8 | `building.subtype` | Untertyp (EFH, MFH, Büro, etc.) | Optional | ✅ | ✅ | - |
| 1.9 | `building.number_of_units` | Anzahl Wohneinheiten | Optional | ✅ | ✅ | - |
| 1.10 | `building.number_of_floors` | Anzahl Geschosse | Optional | Optional | ✅ | - |

---

### **KATEGORIE 2: FLÄCHEN & VOLUMEN**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 2.1 | `building.heated_area` | Beheizte Fläche [m²] | ✅ | ✅ | ✅ | Energieausweis |
| 2.2 | `building.gross_floor_area` | Brutto-Grundfläche [m²] | Optional | ✅ | ✅ | - |
| 2.3 | `building.net_floor_area` | Netto-Grundfläche [m²] | Optional | Optional | ✅ | - |
| 2.4 | `building.heated_volume` | Beheiztes Volumen [m³] | Optional | ✅ | ✅ | - |
| 2.5 | `building.envelope_area` | Hüllfläche [m²] | Optional | ✅ | ✅ | - |
| 2.6 | `building.av_ratio` | A/V-Verhältnis [-] | Optional | ✅ | ✅ | Berechnet |

---

### **KATEGORIE 3: ENERGIEKENNWERTE (aus Energieausweis)**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 3.1 | `energy_certificate.type` | Typ (demand/consumption) | ✅ | ✅ | ✅ | Energieausweis |
| 3.2 | `energy_certificate.issue_date` | Ausstellungsdatum | ✅ | ✅ | ✅ | Energieausweis |
| 3.3 | `energy_certificate.valid_until` | Gültig bis | ✅ | ✅ | ✅ | Energieausweis |
| 3.4 | `energy_certificate.final_energy_kwh_m2a` | Endenergie [kWh/(m²a)] | ✅ | ✅ | ✅ | Energieausweis |
| 3.5 | `energy_certificate.primary_energy_kwh_m2a` | Primärenergie [kWh/(m²a)] | ✅ | ✅ | ✅ | Energieausweis |
| 3.6 | `energy_certificate.energy_class` | Energieklasse (A+ bis H) | ✅ | ✅ | ✅ | Energieausweis |
| 3.7 | `energy_certificate.co2_emissions_kg_m2a` | CO₂-Emissionen [kg/(m²a)] | Optional | ✅ | ✅ | Energieausweis |

---

### **KATEGORIE 4: ENERGIETRÄGER**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 4.1 | `systems.heating.fuel_type` | Energieträger Heizung | ✅ | ✅ | ✅ | Energieausweis |
| 4.2 | `systems.heating.fuel_consumption_kwh_a` | Verbrauch Heizung [kWh/a] | Optional | Optional | Optional | Rechnung |
| 4.3 | `systems.dhw.fuel_type` | Energieträger Warmwasser | Optional | ✅ | ✅ | - |
| 4.4 | `systems.dhw.fuel_consumption_kwh_a` | Verbrauch Warmwasser [kWh/a] | Optional | Optional | Optional | Rechnung |

**Energieträger-Enum:**
- `natural_gas` - Erdgas
- `oil` - Heizöl
- `district_heating` - Fernwärme
- `electricity` - Strom
- `wood_pellets` - Holzpellets
- `wood_logs` - Scheitholz
- `heat_pump` - Wärmepumpe (Strom)
- `solar_thermal` - Solarthermie
- `other` - Sonstige

---

### **KATEGORIE 5: PHOTOVOLTAIK**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 5.1 | `electricity.pv.installed` | PV vorhanden? | ✅ | ✅ | ✅ | - |
| 5.2 | `electricity.pv.peak_power_kwp` | Nennleistung [kWp] | Optional | ✅ | ✅ | - |
| 5.3 | `electricity.pv.area_m2` | Modulfläche [m²] | Optional | Optional | ✅ | - |
| 5.4 | `electricity.pv.orientation` | Ausrichtung [°] | Optional | Optional | ✅ | - |
| 5.5 | `electricity.pv.inclination` | Neigung [°] | Optional | Optional | ✅ | - |
| 5.6 | `electricity.pv.installation_year` | Baujahr | Optional | Optional | ✅ | - |
| 5.7 | `electricity.pv.annual_yield_kwh_a` | Jahresertrag [kWh/a] | Optional | Optional | Optional | Monitoring |

---

### **KATEGORIE 6: VERBRAUCHSDATEN (Monitoring)**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 6.1 | `consumption.heating.kwh_a` | Heizenergie [kWh/a] | ✅ | ✅ | ✅ | Rechnung |
| 6.2 | `consumption.heating.period` | Zeitraum | ✅ | ✅ | ✅ | Rechnung |
| 6.3 | `consumption.dhw.kwh_a` | Warmwasser [kWh/a] | Optional | Optional | Optional | Rechnung |
| 6.4 | `consumption.electricity.kwh_a` | Strom [kWh/a] | Optional | Optional | Optional | Rechnung |
| 6.5 | `consumption.heating.cost_eur_a` | Heizkosten [€/a] | Optional | Optional | Optional | Rechnung |
| 6.6 | `consumption.weather_corrected` | Witterungsbereinigt? | Optional | Optional | ✅ | - |

---

### **KATEGORIE 7: WARMWASSER-ERZEUGUNG**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 7.1 | `systems.dhw.type` | Art der WW-Erzeugung | ✅ | ✅ | ✅ | - |
| 7.2 | `systems.dhw.integrated_heating` | Mit Heizung kombiniert? | Optional | ✅ | ✅ | - |
| 7.3 | `systems.dhw.storage_volume_l` | Speichervolumen [l] | Optional | Optional | ✅ | - |
| 7.4 | `systems.dhw.circulation` | Zirkulation vorhanden? | Optional | Optional | ✅ | - |
| 7.5 | `systems.dhw.solar_thermal` | Solarthermie-Unterstützung? | Optional | Optional | ✅ | - |

**WW-Erzeugung-Enum:**
- `central_boiler` - Zentraler Kessel
- `decentral_electric` - Dezentral elektrisch
- `decentral_gas` - Dezentral Gas
- `heat_pump` - Wärmepumpe
- `district_heating` - Fernwärme
- `solar_thermal` - Solarthermie
- `combined_heating` - Kombiniert mit Heizung

---

### **KATEGORIE 8: HEIZLAST & AUSLEGUNG**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 8.1 | `heating_load.calculated` | Heizlast berechnet? | Optional | Optional | ✅ | - |
| 8.2 | `heating_load.norm_heating_load_kw` | Norm-Heizlast [kW] | Optional | Optional | ✅ | DIN EN 12831 |
| 8.3 | `heating_load.design_outdoor_temp_c` | Auslegungstemperatur [°C] | Optional | Optional | ✅ | DIN EN 12831 |
| 8.4 | `heating_load.design_indoor_temp_c` | Innentemperatur Auslegung [°C] | Optional | Optional | ✅ | DIN EN 12831 |
| 8.5 | `heating_load.transmission_losses_kw` | Transmissionswärmeverluste [kW] | Optional | Optional | ✅ | Berechnung |
| 8.6 | `heating_load.ventilation_losses_kw` | Lüftungswärmeverluste [kW] | Optional | Optional | ✅ | Berechnung |
| 8.7 | `heating_load.specific_load_w_m2` | Spezifische Heizlast [W/m²] | Optional | Optional | ✅ | Berechnung |

**Hinweis:** Heizlast nach DIN EN 12831 ist nicht Teil von DIN 18599, aber wichtig für:
- Dimensionierung Wärmeerzeuger
- Hydraulischer Abgleich
- Heizkörper-/Flächenheizungsauslegung

---

### **KATEGORIE 9: HEIZUNGSSYSTEM (Detailliert)**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 9.1 | `systems.heating.generation.type` | Wärmeerzeuger-Typ | Optional | ✅ | ✅ | - |
| 9.2 | `systems.heating.generation.installation_year` | Baujahr | Optional | ✅ | ✅ | - |
| 9.3 | `systems.heating.generation.nominal_power_kw` | Nennleistung [kW] | Optional | ✅ | ✅ | Typenschild |
| 9.4 | `systems.heating.generation.efficiency` | Wirkungsgrad [-] | Optional | ✅ | ✅ | - |
| 9.6 | `systems.heating.emission.type` | Übergabesystem | Optional | Optional | ✅ | - |
| 9.7 | `systems.heating.control.type` | Regelungsart | Optional | Optional | ✅ | - |
| 9.8 | `systems.heating.auxiliary_energy` | Hilfsenergie [kWh/a] | Optional | Optional | ✅ | Rechnung |
|---|------|--------------|---------|---------|---------|--------|
| 10.1 | `envelope.opaque_elements.walls_external[]` | Einzelne Außenwände | ❌ | Optional | ✅ | IFC |
| 10.2 | `envelope.opaque_elements.walls_external[].ifc_guid` | IFC GUID | ❌ | ❌ | ✅ | IFC |
| 10.3 | `envelope.opaque_elements.walls_external[].construction_ref` | Konstruktion | ❌ | Optional | ✅ | Katalog |
| 10.4 | `envelope.opaque_elements.walls_external[].area` | Fläche [m²] | ❌ | Optional | ✅ | IFC |
| 10.5 | `envelope.opaque_elements.walls_external[].orientation` | Orientierung [°] | ❌ | Optional | ✅ | IFC |
| 10.6 | `envelope.transparent_elements.windows[]` | Einzelne Fenster | ❌ | Optional | ✅ | IFC |
| 10.7 | `envelope.thermal_bridges.linear_bridges[]` | Lineare Wärmebrücken | ❌ | ❌ | Optional | Berechnung |

---

### **KATEGORIE 11: ZONEN (LOD 200+)**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 11.1 | `building.zones[]` | Zonierung | ❌ | ✅ | ✅ | Planung |
| 11.2 | `building.zones[].usage_profile_ref` | Nutzungsprofil | ❌ | ✅ | ✅ | DIN 18599-10 |
| 11.3 | `building.zones[].area` | Fläche [m²] | ❌ | ✅ | ✅ | Planung |
| 11.4 | `building.zones[].volume` | Volumen [m³] | ❌ | Optional | ✅ | Planung |
| 11.5 | `building.zones[].height` | Raumhöhe [m] | ❌ | Optional | ✅ | Planung |
| 11.6 | `building.zones[].setpoint_heating_c` | Solltemperatur Heizung [°C] | ❌ | Optional | ✅ | Nutzungsprofil |
| 11.7 | `building.zones[].setpoint_cooling_c` | Solltemperatur Kühlung [°C] | ❌ | Optional | ✅ | Nutzungsprofil |
| 11.8 | `building.zones[].air_change_rate_h` | Luftwechselrate [1/h] | ❌ | Optional | ✅ | Nutzungsprofil |
| 11.9 | `building.zones[].operating_hours` | Betriebszeiten | ❌ | Optional | ✅ | Nutzungsprofil |
| 11.10 | `building.zones[].conditioned` | Konditioniert (beheizt/gekühlt)? | ❌ | ✅ | ✅ | - |

**Hinweis:** Zonen müssen mit Nutzungsprofilen verknüpft sein - Betriebszeiten und Temperaturen können aus Profil übernommen oder überschrieben werden

---

### **KATEGORIE 12: LÜFTUNG & LUFTDICHTHEIT** ⚠️ **KRITISCH!**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 12.1 | `ventilation.type` | Lüftungsart | Optional | ✅ | ✅ | - |
| 12.2 | `ventilation.air_change_rate_h` | Luftwechselrate [1/h] | Optional | ✅ | ✅ | DIN 18599-2 |
| 12.3 | `ventilation.n50_value` | n₅₀-Wert [1/h] | Optional | Optional | ✅ | Blower-Door |
| 12.4 | `ventilation.n50_estimated` | n₅₀ geschätzt (ohne Messung)? | Optional | ✅ | Optional | Baujahr |
| 12.5 | `ventilation.mechanical_system` | Mechanische Lüftung vorhanden? | Optional | ✅ | ✅ | - |
| 12.6 | `ventilation.heat_recovery` | Wärmerückgewinnung vorhanden? | Optional | Optional | ✅ | - |
| 12.7 | `ventilation.heat_recovery_efficiency` | WRG-Effizienz [-] | Optional | Optional | ✅ | Datenblatt |
| 12.8 | `ventilation.air_flow_rate_m3h` | Luftmengenstrom [m³/h] | Optional | Optional | ✅ | Auslegung |
| 12.9 | `ventilation.operating_hours` | Betriebszeiten | Optional | Optional | ✅ | Nutzungsprofil |
| 12.10 | `ventilation.control_type` | Regelungsart | Optional | Optional | ✅ | - |

**Lüftungsart Enum:**
- `natural` - Freie Lüftung (Fensterlüftung)
- `mechanical_exhaust` - Mechanische Abluftanlage
- `mechanical_supply_exhaust` - Mechanische Zu-/Abluftanlage
- `hybrid` - Hybridlüftung
- `demand_controlled` - Bedarfsgeführte Lüftung

**Hinweis:** n₅₀-Wert ist kritisch für Lüftungswärmeverluste nach DIN 18599-2!

---

### **KATEGORIE 13: KÜHLUNG** ⚠️ **KRITISCH!**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 13.1 | `cooling.installed` | Kühlung vorhanden? | Optional | ✅ | ✅ | - |
| 13.2 | `cooling.type` | Kühlsystem-Typ | Optional | ✅ | ✅ | - |
| 13.3 | `cooling.nominal_power_kw` | Nennleistung [kW] | Optional | Optional | ✅ | Typenschild |
| 13.4 | `cooling.eer` | EER (Energy Efficiency Ratio) [-] | Optional | Optional | ✅ | Datenblatt |
| 13.5 | `cooling.free_cooling` | Freikühlung vorhanden? | Optional | Optional | ✅ | - |
| 13.6 | `cooling.distribution_type` | Verteilungstyp | Optional | Optional | ✅ | - |
| 13.7 | `cooling.operating_hours` | Betriebszeiten | Optional | Optional | ✅ | Nutzungsprofil |
| 13.8 | `cooling.setpoint_temp_c` | Solltemperatur Kühlung [°C] | Optional | Optional | ✅ | - |

**Kühlsystem-Typ Enum:**
- `none` - Keine Kühlung
- `split_unit` - Split-Klimagerät
- `vrv_vrf` - VRV/VRF-System
- `chiller` - Kaltwassersatz
- `reversible_heat_pump` - Reversible Wärmepumpe
- `district_cooling` - Fernkälte
- `free_cooling` - Freie Kühlung

**Hinweis:** Kühlung nach DIN 18599-7 (RLT-Anlagen Nichtwohngebäude)

---

### **KATEGORIE 14: BELEUCHTUNG** ⚠️ **KRITISCH (Nichtwohngebäude)!**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 14.1 | `lighting.applicable` | Beleuchtung relevant? (Nichtwohngebäude) | Optional | ✅ | ✅ | - |
| 14.2 | `lighting.installed_power_w_m2` | Installierte Leistung [W/m²] | Optional | ✅ | ✅ | Planung |
| 14.3 | `lighting.control_type` | Regelungsart | Optional | ✅ | ✅ | - |
| 14.4 | `lighting.daylight_utilization` | Tageslichtnutzung | Optional | Optional | ✅ | - |
| 14.5 | `lighting.presence_detection` | Präsenzerkennung vorhanden? | Optional | Optional | ✅ | - |
| 14.6 | `lighting.dimming` | Dimmung vorhanden? | Optional | Optional | ✅ | - |
| 14.7 | `lighting.operating_hours` | Betriebszeiten | Optional | ✅ | ✅ | Nutzungsprofil |
| 14.8 | `lighting.luminaire_efficiency` | Leuchten-Effizienz [lm/W] | Optional | Optional | ✅ | Datenblatt |

**Regelungsart Enum:**
- `manual` - Manuelle Schaltung
- `time_controlled` - Zeitgesteuert
- `daylight_dependent` - Tageslichtabhängig
- `presence_controlled` - Präsenzabhängig
- `constant_illuminance` - Konstantlichtregelung

**Hinweis:** Beleuchtung nach DIN 18599-4 (nur Nichtwohngebäude relevant!)

---

### **KATEGORIE 15: INTERNE LASTEN & NUTZUNG**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 15.1 | `internal_loads.persons_count` | Personenanzahl | Optional | Optional | ✅ | Nutzungsprofil |
| 15.2 | `internal_loads.persons_heat_w_person` | Wärmeabgabe pro Person [W] | Optional | Optional | ✅ | DIN 18599-10 |
| 15.3 | `internal_loads.appliances_w_m2` | Gerätelasten [W/m²] | Optional | ✅ | ✅ | Nutzungsprofil |
| 15.4 | `internal_loads.process_heat_w_m2` | Prozesswärme [W/m²] | Optional | Optional | ✅ | - |
| 15.5 | `internal_loads.dhw_demand_l_person_day` | Warmwasserbedarf [l/(Person·Tag)] | Optional | ✅ | ✅ | DIN 18599-10 |
| 15.6 | `internal_loads.occupancy_profile` | Belegungsprofil | Optional | Optional | ✅ | Nutzungsprofil |
| 15.7 | `internal_loads.operating_hours_weekday` | Betriebszeiten Werktag | Optional | ✅ | ✅ | Nutzungsprofil |
| 15.8 | `internal_loads.operating_hours_weekend` | Betriebszeiten Wochenende | Optional | ✅ | ✅ | Nutzungsprofil |

**Hinweis:** Interne Lasten nach DIN 18599-10 (Nutzungsrandbedingungen)

---

### **KATEGORIE 16: KLIMA & STANDORT**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 16.1 | `climate.location` | Klimaregion | Optional | ✅ | ✅ | PLZ |
| 16.2 | `climate.try_region` | TRY-Region | Optional | ✅ | ✅ | DWD |
| 16.3 | `climate.altitude_m` | Höhe ü. NN [m] | Optional | Optional | ✅ | - |
| 16.4 | `climate.heating_degree_days` | Heizgradtage [Kd] | Optional | Optional | ✅ | DWD |

---

### **KATEGORIE 17: GEBÄUDEAUTOMATION (BACS)** ⚠️ **KRITISCH!**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 17.1 | `automation.installed` | Gebäudeautomation vorhanden? | Optional | ✅ | ✅ | - |
| 17.2 | `automation.bacs_class` | BACS-Klasse (A-D) | Optional | Optional | ✅ | DIN EN 15232 |
| 17.3 | `automation.efficiency_factor_heating` | Effizienzfaktor Heizung [-] | Optional | Optional | ✅ | DIN 18599-11 |
| 17.4 | `automation.efficiency_factor_cooling` | Effizienzfaktor Kühlung [-] | Optional | Optional | ✅ | DIN 18599-11 |
| 17.5 | `automation.efficiency_factor_ventilation` | Effizienzfaktor Lüftung [-] | Optional | Optional | ✅ | DIN 18599-11 |
| 17.6 | `automation.efficiency_factor_lighting` | Effizienzfaktor Beleuchtung [-] | Optional | Optional | ✅ | DIN 18599-11 |
| 17.7 | `automation.building_management_system` | Gebäudeleittechnik (GLT) vorhanden? | Optional | Optional | ✅ | - |
| 17.8 | `automation.room_automation` | Raumautomation-Stufe | Optional | Optional | ✅ | - |
| 17.9 | `automation.sensors.temperature` | Temperatursensoren vorhanden? | Optional | Optional | ✅ | - |
| 17.10 | `automation.sensors.co2` | CO₂-Sensoren vorhanden? | Optional | Optional | ✅ | - |
| 17.11 | `automation.sensors.presence` | Präsenzsensoren vorhanden? | Optional | Optional | ✅ | - |
| 17.12 | `automation.actuators.valves` | Regelventile vorhanden? | Optional | Optional | ✅ | - |
| 17.13 | `automation.actuators.dampers` | Regelklappen vorhanden? | Optional | Optional | ✅ | - |
| 17.14 | `automation.control_quality` | Regelungsqualität | Optional | Optional | ✅ | - |

**BACS-Klasse Enum (DIN EN 15232):**
- `D` - Nicht energieeffizient (manuell)
- `C` - Standard (einfache Automation)
- `B` - Fortgeschritten (erweiterte Automation)
- `A` - Hocheffizient (optimierte Automation)

**Hinweis:** Gebäudeautomation nach DIN 18599-11 ist kritisch für:
- Effizienzfaktoren (Reduktion Energiebedarf)
- Primärenergie-Reduktion
- KfW-Effizienzhaus-Nachweis
- GEG-Anforderungen §71a (Nichtwohngebäude)

---

### **KATEGORIE 18: PRIMÄRENERGIEFAKTOREN** ⚠️ **KRITISCH!**

| # | Feld | Beschreibung | LOD 100 | LOD 200 | LOD 300 | Quelle |
|---|------|--------------|---------|---------|---------|--------|
| 18.1 | `primary_energy.source` | Quelle der Faktoren | ✅ | ✅ | ✅ | - |
| 18.2 | `primary_energy.reference_year` | Referenzjahr | ✅ | ✅ | ✅ | - |
| 18.3 | `primary_energy.factors.electricity` | fp Strom [-] | ✅ | ✅ | ✅ | GEG/BEG |
| 18.4 | `primary_energy.factors.natural_gas` | fp Erdgas [-] | ✅ | ✅ | ✅ | GEG/BEG |
| 18.5 | `primary_energy.factors.oil` | fp Heizöl [-] | Optional | ✅ | ✅ | GEG/BEG |
| 18.6 | `primary_energy.factors.district_heating` | fp Fernwärme [-] | Optional | ✅ | ✅ | GEG/BEG |
| 18.7 | `primary_energy.factors.wood_pellets` | fp Holzpellets [-] | Optional | Optional | ✅ | GEG/BEG |
| 18.8 | `primary_energy.factors.wood_logs` | fp Scheitholz [-] | Optional | Optional | ✅ | GEG/BEG |
| 18.9 | `primary_energy.factors.renewable_share` | EE-Anteil Strom [-] | Optional | Optional | ✅ | - |
| 18.10 | `primary_energy.factors.grid_mix` | Strommix (Bundesmix/regional) | Optional | Optional | ✅ | - |
| 18.11 | `primary_energy.co2_factors.electricity` | CO₂-Faktor Strom [kg/kWh] | Optional | ✅ | ✅ | UBA |
| 18.12 | `primary_energy.co2_factors.natural_gas` | CO₂-Faktor Erdgas [kg/kWh] | Optional | ✅ | ✅ | UBA |
| 18.13 | `primary_energy.co2_factors.oil` | CO₂-Faktor Heizöl [kg/kWh] | Optional | ✅ | ✅ | UBA |

**Quelle Enum:**
- `GEG_2024` - Gebäudeenergiegesetz 2024 (Anlage 4)
- `BEG_2024` - Bundesförderung effiziente Gebäude
- `CUSTOM` - Benutzerdefiniert
- `DIN_18599` - DIN 18599 Standardwerte

**Standardwerte GEG 2024 (Anlage 4):**
- Strom (Netzstrom): fp = 1.8
- Erdgas: fp = 1.1
- Heizöl: fp = 1.1
- Fernwärme: fp = 0.0 bis 1.3 (je nach Erzeugung)
- Holzpellets: fp = 0.2
- Umweltwärme (Wärmepumpe): fp = 0.0

**Hinweis:** Primärenergiefaktoren sind kritisch für:
- Energieausweis (Primärenergiebedarf)
- GEG-Grenzwerte (Effizienzhaus-Niveau)
- KfW-Förderung
- CO₂-Bilanzierung

---

## 🎯 LOD-DEFINITION DURCH VOLLSTÄNDIGKEIT

### **LOD 100: Energieausweis-Daten + Verbrauch**

**Minimum Required:**
- ✅ Adresse (PLZ, Stadt)
- ✅ Baujahr
- ✅ Beheizte Fläche
- ✅ Endenergie [kWh/(m²a)]
- ✅ Primärenergie [kWh/(m²a)]
- ✅ Energieträger Heizung
- ✅ Verbrauch Heizung [kWh/a]

**Optional:**
- PV vorhanden (ja/nein)
- Art der WW-Erzeugung

**Verwendung:**
- Erste Einschätzung
- Verbrauchsabgleich
- Sanierungspotenzial grob

---

### **LOD 200: Energieausweis + Bauteil-Übersicht**

**Zusätzlich zu LOD 100:**
- ✅ Zonen mit Nutzungsprofilen
- ✅ Hüllflächen mit Ø U-Werten (Wand, Dach, Boden, Fenster)
- ✅ Heizungssystem (Typ, Baujahr, Effizienz)
- ✅ WW-Erzeugung (Typ)
- ✅ Klimaregion

**Verwendung:**
- Energieausweis Bedarfsausweis
- Sanierungsfahrplan (iSFP)
- Förderantrag

---

### **LOD 300: Detaillierte Energieberatung**

**Zusätzlich zu LOD 200:**
- ✅ Jedes Bauteil einzeln mit IFC GUID
- ✅ Exakte Flächen, Orientierungen
- ✅ Detaillierte Schichtaufbauten ODER Katalog-Referenzen
- ✅ Heizung: Erzeugung + Verteilung + Übergabe + Regelung
- ✅ Wärmebrücken detailliert

**Verwendung:**
- DIN 18599 vollständige Berechnung
- KfW-Effizienzhaus Nachweis
- Detaillierte Sanierungsplanung

---

## 💡 VORTEILE DYNAMISCHES MODELL

### **1. Schrittweise Erweiterung**
```json
// Start: LOD 100
{
  "lod": "100",
  "building": {
    "heated_area": 145.5,
    "construction_year": 1978
  },
  "energy_certificate": {
    "final_energy_kwh_m2a": 140
  }
}

// Später: LOD 200 (gleiche Datei erweitert!)
{
  "lod": "200",
  "building": {
    "heated_area": 145.5,
    "construction_year": 1978,
    "zones": [
      {"usage_profile_ref": "PROFILE_RES_EFH", "area": 145.5}
    ]
  },
  "energy_certificate": {
    "final_energy_kwh_m2a": 140
  },
  "envelope": {
    "walls_external": {
      "u_value_avg": 1.4,
      "area_total": 167.7
    }
  }
}

// Noch später: LOD 300 (weiter erweitert!)
{
  "lod": "300",
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD",
          "construction_ref": "WALL_EXT_BRICK_UNINSULATED",
          "area": 35.2,
          "orientation": 180
        }
      ]
    }
  }
}
```

### **2. Flexible Validierung**
- Software prüft: "Für LOD 200 fehlen noch: Zonen, U-Werte"
- Nutzer kann entscheiden: "Erst mal LOD 100, später mehr"

### **3. Realitätsnah**
- Manche Daten sind früh bekannt (Verbrauch)
- Andere später (detaillierte Bauteile)
- Modell passt sich an

---

## 🚀 NÄCHSTE SCHRITTE

1. **Vollständige Feldliste finalisieren** (heute)
2. **Schema v2.1: Alle Felder optional, LOD-Hinweise** (nächste Woche)
3. **Validierungs-Tool: LOD-Checker** (später)
4. **Beispiele: LOD 100 → 200 → 300 Migration** (später)

---

**Status:** Konzept  
**Nächster Schritt:** Feldliste vervollständigen
