# EVEBI → DIN18599 Sidecar JSON Mapping

**Version:** 1.0  
**Datum:** 1. April 2026  
**Zweck:** Vollständiges Mapping von EVEBI XML zu DIN18599 Sidecar JSON

---

## 📋 Übersicht

Dieses Dokument definiert das Mapping zwischen:
- **Quelle:** EVEBI `.evea`/`.evex` XML-Format
- **Ziel:** DIN18599 Sidecar JSON (Schema v2.0.0)

---

## 🎯 Mapping-Strategie

### Priorität 1: Gebäudehülle (Hoch)
- ✅ Materialien → `input.materials`
- ✅ Konstruktionen → `input.layer_structures`
- ✅ Bauteile → `input.elements` + `input.windows`
- ✅ Zonen → `input.zones`

### Priorität 2: Anlagentechnik (Mittel)
- ✅ Energieträger → `input.systems[].energy_source`
- ✅ Heizung → `input.systems[]` (type: HEAT_PUMP, BOILER, etc.)
- ✅ Warmwasser → `input.dhw[]`
- ✅ Lüftung → `input.ventilation[]`

### Priorität 3: Erneuerbare (Niedrig)
- ✅ PV-Anlagen → `input.pv[]`
- ✅ Batteriespeicher → `input.pv[].battery_capacity`

---

## 🏗️ 1. Materialien (materials)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `konstruktionenListe/item/name` | `materials[].name` | Direkt |
| `konstruktionenListe/item/GUID` | `materials[].id` | `MAT-{GUID}` |
| `konstruktionenListe/item/lambda` | `materials[].lambda` | Float (W/mK) |
| `konstruktionenListe/item/rho` | `materials[].density` | Float (kg/m³) |
| - | `materials[].type` | `"STANDARD"` (default) |
| - | `materials[].specific_heat` | `1000` (default) |
| - | `materials[].vapor_resistance_factor` | Berechnet aus sd-Wert |

### Beispiel-Code

```python
def map_evebi_materials_to_sidecar(evebi_constructions):
    materials = []
    
    for konstr in evebi_constructions:
        if konstr.lambda_value > 0:  # Nur echte Materialien
            material = {
                "id": f"MAT-{konstr.guid[:8]}",
                "name": konstr.name,
                "type": "STANDARD",
                "lambda": konstr.lambda_value,
                "density": konstr.density,
                "specific_heat": 1000,  # Default
                "vapor_resistance_factor": 10  # Default
            }
            materials.append(material)
    
    return materials
```

---

## 🧱 2. Konstruktionen (layer_structures)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `konstruktionenListe/item/name` | `layer_structures[].name` | Direkt |
| `konstruktionenListe/item/GUID` | `layer_structures[].id` | `LS-{GUID}` |
| `konstruktionenListe/item/U` | `layer_structures[].calculated_values.u_value_w_m2k` | Float (W/m²K) |
| - | `layer_structures[].type` | Aus Bauteil-Typ ableiten |
| - | `layer_structures[].layers[]` | ⚠️ Nicht in EVEBI (nur U-Wert) |

**⚠️ Limitation:** EVEBI enthält **keine Schichtaufbauten**, nur U-Werte!

### Workaround

```python
def map_evebi_constructions_to_sidecar(evebi_constructions):
    layer_structures = []
    
    for konstr in evebi_constructions:
        # Erstelle vereinfachte Konstruktion (nur U-Wert, keine Schichten)
        structure = {
            "id": f"LS-{konstr.guid[:8]}",
            "name": konstr.name,
            "type": "WALL",  # Default, wird später aus Bauteil überschrieben
            "layers": [],  # Leer, da nicht in EVEBI
            "calculated_values": {
                "u_value_w_m2k": konstr.u_value
            }
        }
        layer_structures.append(structure)
    
    return layer_structures
```

---

## 🏠 3. Bauteile (elements + windows)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `tflListe/item/GUID` | `elements[].ifc_guid` | ⚠️ EVEBI-GUID ≠ IFC-GUID |
| `tflListe/item/name` | - | Nur für Typ-Erkennung |
| `tflListe/item/U` | `elements[].u_value_undisturbed` | Float (W/m²K) |
| `tflListe/item/orientierung` | `elements[].orientation` | Float (0-360°) |
| `tflListe/item/neigGrad` | `elements[].inclination` | Float (0-90°) |
| `tflListe/item/nettoA` | - | Fläche (in IFC vorhanden) |
| - | `elements[].boundary_condition` | `"EXTERIOR"` (default) |
| - | `elements[].thermal_bridge_delta_u` | `0.02` (default) |

### Bauteil-Typ Mapping

| EVEBI Name (enthält) | Sidecar Type | boundary_condition |
|----------------------|--------------|-------------------|
| "Außenwand" | WALL | EXTERIOR |
| "Innenwand" / "Zwischenwand" | WALL | INTERIOR |
| "Dach" | ROOF | EXTERIOR |
| "Boden nach außen" | FLOOR | EXTERIOR |
| "Bodenplatte" | FLOOR | GROUND |
| "Decke" | FLOOR | INTERIOR |
| "Fenster" | WINDOW | EXTERIOR |
| "Tür" | DOOR | EXTERIOR |

### Fenster-Spezifisch

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `konstrFensterListe/item/Uf` | `windows[].u_value_frame` | Float (W/m²K) |
| `konstrFensterListe/item/Ug` | `windows[].u_value_glass` | Float (W/m²K) |
| `konstrFensterListe/item/g` | `windows[].g_value` | Float (0-1) |
| `konstrFensterListe/item/rahmenAnteil` | `windows[].frame_fraction` | Float (0-1) |

### Beispiel-Code

```python
def map_evebi_elements_to_sidecar(evebi_elements, ifc_elements):
    sidecar_elements = []
    sidecar_windows = []
    
    for evebi_elem in evebi_elements:
        # Finde passendes IFC-Element (via PosNo oder Name)
        ifc_elem = find_matching_ifc_element(evebi_elem, ifc_elements)
        
        if not ifc_elem:
            continue  # Skip wenn kein IFC-Match
        
        # Typ-Erkennung
        element_type = detect_element_type(evebi_elem.name)
        
        if element_type == "WINDOW":
            # Fenster
            window = {
                "ifc_guid": ifc_elem.guid,
                "u_value_glass": evebi_elem.u_value or 1.1,
                "u_value_frame": 1.3,  # Default
                "g_value": 0.6,  # Default
                "frame_fraction": 0.2,  # Default
                "shading_factor_fs": 1.0,
                "horizon_angle": 0,
                "overhang_angle": 0
            }
            sidecar_windows.append(window)
        else:
            # Opakes Bauteil
            element = {
                "ifc_guid": ifc_elem.guid,
                "boundary_condition": detect_boundary_condition(evebi_elem.name),
                "layer_structure_ref": f"LS-{evebi_elem.construction_ref[:8]}" if evebi_elem.construction_ref else None,
                "u_value_undisturbed": evebi_elem.u_value,
                "thermal_bridge_delta_u": 0.02,  # Default
                "thermal_bridge_type": "SIMPLIFIED",
                "orientation": evebi_elem.orientation or 0,
                "inclination": evebi_elem.inclination or 90
            }
            sidecar_elements.append(element)
    
    return sidecar_elements, sidecar_windows
```

---

## 🏠 4. Zonen (zones)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `geschosseListe/item/name` | `zones[].name` | Direkt |
| `geschosseListe/item/GUID` | `zones[].id` | `ZONE-{GUID}` |
| `geschosseListe/item/A` | `zones[].area_an` | Float (m²) |
| `geschosseListe/item/V` | `zones[].volume_v` | Float (m³) |
| - | `zones[].height_h` | Berechnet: V / A |
| - | `zones[].usage_profile` | `"17"` (Wohnen, default) |
| - | `zones[].air_change_n50` | `0.6` (default) |
| - | `zones[].design_temp_heating` | `20` (default) |
| - | `zones[].lighting_control` | `"MANUAL"` (default) |

### Beispiel-Code

```python
def map_evebi_zones_to_sidecar(evebi_zones):
    sidecar_zones = []
    
    for zone in evebi_zones:
        height = zone.volume / zone.area if zone.area > 0 else 3.0
        
        sidecar_zone = {
            "id": f"ZONE-{zone.guid[:8]}",
            "name": zone.name,
            "usage_profile": "17",  # Wohnen
            "area_an": zone.area,
            "volume_v": zone.volume,
            "height_h": round(height, 2),
            "air_change_n50": 0.6,  # Default
            "design_temp_heating": 20,  # Default
            "lighting_control": "MANUAL",
            "space_guids": []  # Leer, da keine IFC-Verknüpfung
        }
        sidecar_zones.append(sidecar_zone)
    
    return sidecar_zones
```

---

## 🔥 5. Heizung (systems)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `hzErzListe/item/name` | `systems[].name` | Direkt |
| `hzErzListe/item/GUID` | `systems[].id` | `SYS-{GUID}` |
| `hzErzListe/item/art` | `systems[].type` | Mapping (siehe unten) |
| `hzErzListe/item/baujahr` | `systems[].year_built` | Integer |
| - | `systems[].energy_source` | Aus Energieträger ableiten |

### Heizungs-Typ Mapping

| EVEBI `art` | Sidecar `type` |
|-------------|----------------|
| `HZ_ZENTRALHEIZUNG` | `BOILER` |
| `HZ_WAERMEPUMPE` | `HEAT_PUMP_AIR` / `HEAT_PUMP_BRINE` |
| `HZ_FERNWAERME` | `DISTRICT_HEATING` |
| `HZ_EINZELOFEN` | `STOVE` |

### Beispiel-Code

```python
def map_evebi_heating_to_sidecar(evebi_heating, evebi_energy_carriers):
    systems = []
    
    for hz in evebi_heating:
        # Typ-Mapping
        system_type = {
            "HZ_ZENTRALHEIZUNG": "BOILER",
            "HZ_WAERMEPUMPE": "HEAT_PUMP_AIR",
            "HZ_FERNWAERME": "DISTRICT_HEATING"
        }.get(hz.art, "BOILER")
        
        # Energieträger ermitteln
        energy_source = "GAS"  # Default
        if "Strom" in hz.name or "WP" in hz.name:
            energy_source = "ELECTRICITY"
        elif "Öl" in hz.name:
            energy_source = "OIL"
        
        system = {
            "id": f"SYS-{hz.guid[:8]}",
            "type": system_type,
            "name": hz.name,
            "energy_source": energy_source,
            "year_built": hz.year_built or 2020,
            "operation_mode": "MONOVALENT"
        }
        
        # Wärmepumpen-spezifisch
        if "HEAT_PUMP" in system_type:
            system["heat_pump"] = {
                "cop_a2_w35": 4.0,  # Default
                "cop_a7_w35": 4.5,  # Default
                "refrigerant": "R410A"  # Default
            }
        
        systems.append(system)
    
    return systems
```

---

## 💧 6. Warmwasser (dhw)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `twErzListe/item/art` | `dhw[].type` | Mapping (siehe unten) |
| `twErzListe/item/volumen` | `dhw[].storage_volume` | Float (Liter) |
| `twListe/item/zirBetrieb` | `dhw[].circulation` | Boolean (0/1) |

### Warmwasser-Typ Mapping

| EVEBI `art` | Sidecar `type` |
|-------------|----------------|
| `WT_ZENTRAL` | `CENTRAL` |
| `WT_DEZENTRAL` | `DECENTRAL` |
| `WT_HZG` | `CENTRAL` (Kombibereiter) |

### Beispiel-Code

```python
def map_evebi_dhw_to_sidecar(evebi_dhw_erzeuger, evebi_dhw_system):
    dhw = []
    
    for tw_erz in evebi_dhw_erzeuger:
        dhw_type = {
            "WT_ZENTRAL": "CENTRAL",
            "WT_DEZENTRAL": "DECENTRAL",
            "WT_HZG": "CENTRAL"
        }.get(tw_erz.art, "CENTRAL")
        
        # Zirkulation aus System
        circulation = False
        if evebi_dhw_system:
            circulation = evebi_dhw_system[0].circulation > 0
        
        dhw_entry = {
            "type": dhw_type,
            "storage_volume": tw_erz.storage_volume or 300,
            "storage_loss_factor": 1.8,  # Default
            "circulation": circulation,
            "circulation_length": 15 if circulation else 0,
            "pipe_insulation": "100_PERCENT"
        }
        dhw.append(dhw_entry)
    
    return dhw
```

---

## 💨 7. Lüftung (ventilation)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `luftListe/item/art` | `ventilation[].type` | Mapping (siehe unten) |
| `luftListe/item/wrg` | `ventilation[].heat_recovery` | Boolean (0/1) |
| `luftListe/item/wrgGrad` | `ventilation[].heat_recovery_efficiency` | Float (0-1) |
| `luftListe/item/luftWechsel` | - | Nicht direkt mappbar |

### Lüftungs-Typ Mapping

| EVEBI `art` | Sidecar `type` |
|-------------|---------------|
| `LA_FREI` | `NATURAL` (Fensterlüftung) |
| `LA_ZENTRAL` | `SUPPLY_EXHAUST` |
| `LA_DEZENTRAL` | `EXHAUST_ONLY` |

### Beispiel-Code

```python
def map_evebi_ventilation_to_sidecar(evebi_ventilation):
    ventilation = []
    
    for luft in evebi_ventilation:
        vent_type = {
            "LA_FREI": "NATURAL",
            "LA_ZENTRAL": "SUPPLY_EXHAUST",
            "LA_DEZENTRAL": "EXHAUST_ONLY"
        }.get(luft.art, "NATURAL")
        
        # WRG nur bei mechanischer Lüftung
        has_wrg = luft.wrg > 0 and vent_type != "NATURAL"
        
        vent_entry = {
            "type": vent_type,
            "heat_recovery": has_wrg,
            "heat_recovery_efficiency": luft.wrg_grad if has_wrg else 0,
            "volume_flow": 250,  # Default
            "spf_fan": 0.35  # Default
        }
        ventilation.append(vent_entry)
    
    return ventilation
```

---

## ☀️ 8. PV-Anlagen (pv)

### EVEBI → Sidecar

| EVEBI XML | Sidecar JSON | Transformation |
|-----------|--------------|----------------|
| `pvListe/item/leistung` | `pv[].peak_power` | Float (kWp) |
| `pvListe/item/orientierung` | `pv[].orientation` | Float (0-360°) |
| `pvListe/item/neigung` | `pv[].inclination` | Float (0-90°) |
| `batterienListe/item/kapazitaet` | `pv[].battery_capacity` | Float (kWh) |

### Beispiel-Code

```python
def map_evebi_pv_to_sidecar(evebi_pv, evebi_batteries):
    pv = []
    
    for pv_anlage in evebi_pv:
        # Batterie-Kapazität (falls vorhanden)
        battery_capacity = 0.0
        if evebi_batteries:
            battery_capacity = evebi_batteries[0].capacity
        
        pv_entry = {
            "peak_power": pv_anlage.peak_power,
            "orientation": pv_anlage.orientation or 180,
            "inclination": pv_anlage.inclination or 30,
            "system_loss": 0.14,  # Default
            "battery_capacity": battery_capacity
        }
        pv.append(pv_entry)
    
    return pv
```

---

## 🔗 9. IFC-Verknüpfung (Mapping)

### Problem: EVEBI-GUID ≠ IFC-GUID

EVEBI und IFC haben **unterschiedliche GUIDs**. Verknüpfung erfolgt über:

1. **PosNo** (aus EVEBI-Name) → IFC-Property `PosNo`
2. **Name-Matching** (Fuzzy-Match)
3. **Geometrie-Matching** (Fläche, Orientierung, Neigung)

### Matching-Strategie

```python
def find_matching_ifc_element(evebi_elem, ifc_elements):
    """
    Findet passendes IFC-Element für EVEBI-Element
    
    Priorität:
    1. PosNo-Match (exakt)
    2. Name-Match (Fuzzy, >80% Ähnlichkeit)
    3. Geometrie-Match (Fläche ±10%, Orientierung ±15°)
    """
    
    # 1. PosNo-Match
    if evebi_elem.posno:
        for ifc_elem in ifc_elements:
            if ifc_elem.posno == evebi_elem.posno:
                return ifc_elem
    
    # 2. Name-Match
    for ifc_elem in ifc_elements:
        similarity = calculate_name_similarity(evebi_elem.name, ifc_elem.name)
        if similarity > 0.8:
            return ifc_elem
    
    # 3. Geometrie-Match
    for ifc_elem in ifc_elements:
        if geometry_matches(evebi_elem, ifc_elem):
            return ifc_elem
    
    return None
```

---

## 📊 10. Vollständiges Mapping-Beispiel

### Input: EVEBI XML

```xml
<Projekt GUID="{D61C47A5-E6B0-46AD-94B0-E2877B201ED4}">
  <eing>
    <tflListe>
      <item GUID="{EF26E269-5A36-4475-BB56-62AC05EF916E}">
        <name>Außenwand Nord Pos 001</name>
        <nettoA>15.49</nettoA>
        <U auto="true" man="0.0000000" calc="0.2000000" unit="W/(m²K)">0.2000000</U>
        <orientierung>0</orientierung>
        <neigGrad>90</neigGrad>
      </item>
    </tflListe>
  </eing>
</Projekt>
```

### Output: Sidecar JSON

```json
{
  "input": {
    "elements": [
      {
        "ifc_guid": "1Eu7Wz4Hz2DzBwEz6nY0QP",
        "boundary_condition": "EXTERIOR",
        "layer_structure_ref": "LS-EF26E269",
        "u_value_undisturbed": 0.2,
        "thermal_bridge_delta_u": 0.02,
        "thermal_bridge_type": "SIMPLIFIED",
        "orientation": 0,
        "inclination": 90
      }
    ]
  }
}
```

---

## ⚠️ Limitationen & Workarounds

### 1. Keine Schichtaufbauten
**Problem:** EVEBI enthält nur U-Werte, keine Schichten  
**Workaround:** Erstelle `layer_structures` nur mit `calculated_values.u_value_w_m2k`

### 2. Keine IFC-GUIDs
**Problem:** EVEBI-GUIDs ≠ IFC-GUIDs  
**Workaround:** Matching via PosNo, Name, Geometrie

### 3. Fehlende Defaults
**Problem:** Viele Sidecar-Felder haben keine EVEBI-Entsprechung  
**Workaround:** Verwende sinnvolle Defaults (siehe Tabellen oben)

### 4. Keine Raumzuordnung
**Problem:** EVEBI-Zonen ≠ IFC-Spaces  
**Workaround:** `space_guids` bleibt leer, nur Zonen-Metadaten

---

## 📝 Implementierungs-Checkliste

- [x] EVEBI-Format dokumentiert (8 Kategorien)
- [ ] Mapping-Funktionen implementiert
  - [ ] Materialien
  - [ ] Konstruktionen
  - [ ] Bauteile (opak)
  - [ ] Fenster
  - [ ] Zonen
  - [ ] Heizung
  - [ ] Warmwasser
  - [ ] Lüftung
  - [ ] PV
- [ ] IFC-Matching-Algorithmus
- [ ] Sidecar-Generator erweitert
- [ ] Tests mit Real-World Daten
  - [ ] DIN18599Test (74 Bauteile)
  - [ ] IST-Zustand (204 Bauteile)
  - [ ] Breuer (193 Bauteile)

---

**Letzte Aktualisierung:** 1. April 2026  
**Version:** 1.0 (Vollständiges Mapping definiert)
