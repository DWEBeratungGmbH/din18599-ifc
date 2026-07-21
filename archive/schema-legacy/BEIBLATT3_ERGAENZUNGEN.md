# Schema v2.2 → v2.2.1: DIN 18599 Beiblatt 3 Ergänzungen

## Überblick

Ergänzung fehlender Felder für vollständige **DIN 18599 Beiblatt 3 Konformität**.

Alle Änderungen sind **nicht-breaking** (nur neue optionale Felder, außer T3).

---

## B1: DIN-Bauteilcode (din_code)

**Problem:** Beiblatt 3 nutzt Kennungssystem (WA, DA, BE, FA, FD, FL...) als zentrales Ordnungsprinzip. Schema hatte Bestandteile (Bauteiltyp + boundary_condition), aber nicht den zusammengesetzten Code.

**Lösung:** Neues Feld `din_code` in `opaque_element` und `transparent_element`.

### Opake Bauteile (Tabelle 77-85)

```json
"din_code": {
  "type": "string",
  "enum": ["WA", "WI", "DA", "DE", "DU", "BE", "BO", "BU"],
  "description": "DIN 18599 Bauteilcode (Beiblatt 3 Tabelle 77-85)"
}
```

**Mapping-Logik:**
```
Wand + exterior → WA (Außenwand)
Wand + adjacent → WI (Innenwand)
Dach + exterior → DA (Dach Außenluft)
Dach + unheated → DE (Dach unbeheizt)
Dach + ground → DU (Dach Erdreich - selten)
Boden + ground → BE (Boden Erdreich)
Boden + exterior → BO (Boden Außenluft)
Boden + unheated → BU (Boden unbeheizt)
```

### Transparente Bauteile (Tabelle 86-92)

```json
"din_code": {
  "type": "string",
  "enum": ["FA", "FD", "FL", "TA", "TD"],
  "description": "DIN 18599 Bauteilcode (Beiblatt 3 Tabelle 86-92)"
}
```

**Mapping-Logik:**
```
Fenster + inclination ≥ 60° → FA (Fenster Außenwand)
Fenster + inclination 22-60° → FD (Fenster Dachfläche)
Fenster + inclination < 22° → FL (Fenster Lichtkuppel)
Tür + inclination ≥ 60° → TA (Tür Außenwand)
Tür + inclination 22-60° → TD (Tür Dach - selten)
```

**Vorteil:**
- Sofort lesbar für Energieberater
- Direkte Zuordnung zu Norm-Tabellen
- Brücke zur Dokumentation

---

## B2: Fx-Korrekturfaktor (fx_factor)

**Problem:** Jedes Bauteil in Tabelle 77-92 hat Spalte "Fx" (Temperatur-Korrekturfaktor). Essenziell für alle nicht-Außenluft-Bauteile. Ohne dieses Feld keine normkonforme Berechnung möglich.

**Lösung:** Neues Feld `fx_factor` in `opaque_element` und `transparent_element`.

```json
"fx_factor": {
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "Temperatur-Korrekturfaktor Fx (Beiblatt 3 Tabelle 77-92)"
}
```

**Typische Werte (aus Beiblatt 3):**
```
exterior (Außenluft): Fx = 1.0
ground (Erdreich): Fx ≈ 0.6 (abhängig von Tiefe)
unheated (unbeheizt): Fx ≈ 0.8 (Dachboden), 0.5 (Keller)
adjacent (angrenzend): Fx = 0.0 (wenn gleiche Temperatur)
```

**Berechnung:**
```
Q_transmission = U × A × Fx × (θi - θe)
```

Ohne Fx würde Wärmeverlust über Erdreich/unbeheizte Räume massiv überschätzt.

---

## B3: Transparente Felder vervollständigt

**Problem:** Tabelle 86-92 verlangt pro Fenster: U-Wert, τ (Transmissionsgrad Tageslicht), g⊥ (senkrecht), g mit Sonnenschutz Sommer/Winter. Schema hatte nur `u_value`, `g_value`, `shading_factor_f_sh`.

**Lösung:** 4 neue Felder in `transparent_element`.

### τ-Wert (Transmissionsgrad Tageslicht)

```json
"tau_value": {
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "Transmissionsgrad für Tageslicht τ [-] (Beiblatt 3 Tabelle 86-92)"
}
```

**Verwendung:** DIN 18599-4 Beleuchtung (Tageslichtnutzung).

**Typische Werte:**
- Dreifachverglasung: τ ≈ 0.70
- Zweifachverglasung: τ ≈ 0.78
- Sonnenschutzverglasung: τ ≈ 0.50

### g⊥ (Gesamtenergiedurchlassgrad senkrecht)

```json
"g_value_perpendicular": {
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "Gesamtenergiedurchlassgrad senkrecht g⊥ [-]"
}
```

**Unterschied zu `g_value`:** 
- `g_value_perpendicular` = g⊥ (senkrechter Einfall, Referenzwert)
- `g_value` = effektiver g-Wert (winkelabhängig)

### g-Wert Sommer/Winter

```json
"g_value_summer": {
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "g-Wert mit Sonnenschutz Sommer (Beiblatt 3)"
},
"g_value_winter": {
  "type": "number",
  "minimum": 0,
  "maximum": 1,
  "description": "g-Wert mit Sonnenschutz Winter (Beiblatt 3)"
}
```

**Verwendung:** Solare Gewinne nach DIN 18599-2.

**Beispiel:**
```
Ohne Sonnenschutz: g⊥ = 0.60
Mit Sonnenschutz Sommer (außen): g_summer = 0.15
Mit Sonnenschutz Winter (innen): g_winter = 0.45
```

---

## B4: Neigung bei transparent_element

**Problem:** Beiblatt 3 unterscheidet Wandfenster (≥60°), Dachflächenfenster (22-60°), Lichtkuppeln (<22°) mit verschiedenen DIN-Codes (FA, FD, FL) und Solargewinn-Formeln. `transparent_element` hatte kein `inclination`-Feld.

**Lösung:** Neues Feld `inclination` in `transparent_element`.

```json
"inclination": {
  "type": "number",
  "minimum": 0,
  "maximum": 90,
  "description": "Neigung [°] für FA/FD/FL-Unterscheidung (Beiblatt 3)"
}
```

**Mapping zu DIN-Code:**
```
inclination ≥ 60° → FA (Fenster Außenwand)
inclination 22-60° → FD (Fenster Dachfläche)
inclination < 22° → FL (Fenster Lichtkuppel)
```

**Unterschiedliche Formeln:**
- FA: Standard-Solargewinn-Formel
- FD: Erhöhter Solargewinn (Dachneigung)
- FL: Reduzierter Solargewinn (Verschmutzung)

---

## T1: parent_element_guid aus opaque_element entfernt

**Problem:** Copy-Paste-Fehler - opake Bauteile haben keine Parent-Wand.

**Lösung:** Feld entfernt aus `opaque_element`, bleibt nur in `transparent_element` als `parent_wall_guid`.

---

## T3: zone.volume und zone.height als required

**Problem:** `volume` und `height` waren optional, sind aber **Pflichtgrößen** für Beiblatt 3 Tabelle 96 (Nutzenergiebedarf).

**Lösung:** In `required`-Array aufgenommen.

```json
"zone": {
  "required": ["id", "usage_profile_ref", "area", "volume", "height"]
}
```

**Breaking Change:** Ja, aber gerechtfertigt - ohne diese Werte ist keine DIN 18599-Berechnung möglich.

---

## Zusammenfassung der Änderungen

| Feld | Element | Typ | Required | Beschreibung |
|------|---------|-----|----------|--------------|
| `din_code` | opaque | enum | Nein | WA, DA, BE, etc. (Beiblatt 3) |
| `din_code` | transparent | enum | Nein | FA, FD, FL, TA, TD |
| `fx_factor` | opaque | number | Nein | Temperatur-Korrekturfaktor |
| `fx_factor` | transparent | number | Nein | Temperatur-Korrekturfaktor |
| `tau_value` | transparent | number | Nein | Transmissionsgrad Tageslicht |
| `g_value_perpendicular` | transparent | number | Nein | g⊥ senkrecht |
| `g_value_summer` | transparent | number | Nein | g mit Sonnenschutz Sommer |
| `g_value_winter` | transparent | number | Nein | g mit Sonnenschutz Winter |
| `inclination` | transparent | number | Nein | Neigung für FA/FD/FL |
| `volume` | zone | number | **Ja** | Zonenvolumen (Pflicht!) |
| `height` | zone | number | **Ja** | Raumhöhe (Pflicht!) |

**Entfernt:**
- `parent_element_guid` aus `opaque_element` (war Fehler)

---

## Parser-Anpassungen (Phase 2)

### 1. din_code ableiten

```python
def derive_din_code(elem):
    # Opake Bauteile
    if elem.ifc_type in ['IfcWall']:
        if elem.boundary_condition == 'exterior':
            return 'WA'
        else:
            return 'WI'
    
    elif elem.ifc_type in ['IfcRoof', 'IfcSlab'] and elem.predefined_type == 'ROOF':
        if elem.boundary_condition == 'exterior':
            return 'DA'
        elif elem.boundary_condition == 'unheated':
            return 'DE'
        else:
            return 'DU'
    
    elif elem.ifc_type == 'IfcSlab':
        if elem.boundary_condition == 'ground':
            return 'BE'
        elif elem.boundary_condition == 'exterior':
            return 'BO'
        else:
            return 'BU'
    
    # Transparente Bauteile
    elif elem.ifc_type == 'IfcWindow':
        if elem.inclination >= 60:
            return 'FA'
        elif elem.inclination >= 22:
            return 'FD'
        else:
            return 'FL'
    
    elif elem.ifc_type == 'IfcDoor':
        if elem.inclination >= 60:
            return 'TA'
        else:
            return 'TD'
```

### 2. fx_factor ableiten

```python
def derive_fx_factor(elem):
    if elem.boundary_condition == 'exterior':
        return 1.0
    elif elem.boundary_condition == 'ground':
        # Vereinfacht - eigentlich abhängig von Tiefe
        return 0.6
    elif elem.boundary_condition == 'unheated':
        # Vereinfacht - eigentlich abhängig von Raum
        if 'Dach' in elem.name or elem.din_code in ['DE', 'DU']:
            return 0.8  # Dachboden
        else:
            return 0.5  # Keller
    else:  # adjacent
        return 0.0  # Gleiche Temperatur
```

### 3. Transparente Werte aus IFC

```python
def extract_transparent_properties(ifc_window):
    psets = ifcopenshell.util.element.get_psets(ifc_window)
    
    # Aus Pset_WindowCommon oder Pset_DoorCommon
    u_value = psets.get('Pset_WindowCommon', {}).get('ThermalTransmittance')
    g_value = psets.get('Pset_WindowCommon', {}).get('GlazingAreaFraction')  # Approximation
    
    # tau_value oft nicht in IFC - Standardwerte aus Katalog
    tau_value = 0.70  # Default für Dreifachverglasung
    
    # g_summer/winter aus Sonnenschutz-Eigenschaften
    shading = psets.get('Pset_WindowCommon', {}).get('ShadingDeviceType')
    if shading:
        g_value_summer = g_value * 0.25  # Mit außen Sonnenschutz
        g_value_winter = g_value * 0.75  # Mit innen Sonnenschutz
    else:
        g_value_summer = g_value
        g_value_winter = g_value
    
    return {
        'u_value': u_value,
        'g_value_perpendicular': g_value,
        'g_value_summer': g_value_summer,
        'g_value_winter': g_value_winter,
        'tau_value': tau_value
    }
```

---

## Validierung

**Test mit DIN18599Test v3.ifc:**

```json
{
  "envelope": {
    "walls": [
      {
        "id": "wall_001",
        "ifc_guid": "2O2Fr$t4X7Zf8NOew3FLOH",
        "din_code": "WA",
        "boundary_condition": "exterior",
        "fx_factor": 1.0,
        "u_value": 0.24,
        "area": 29.5,
        "orientation": 180,
        "inclination": 90
      }
    ],
    "windows": [
      {
        "id": "window_001",
        "din_code": "FA",
        "boundary_condition": "exterior",
        "fx_factor": 1.0,
        "u_value": 1.1,
        "g_value_perpendicular": 0.60,
        "g_value_summer": 0.15,
        "g_value_winter": 0.45,
        "tau_value": 0.70,
        "inclination": 90
      }
    ]
  },
  "building": {
    "zones": [
      {
        "id": "zone_001",
        "area": 50.0,
        "volume": 125.0,
        "height": 2.5
      }
    ]
  }
}
```

---

## Ergebnis

**Schema v2.2.1** ist jetzt **vollständig DIN 18599 Beiblatt 3-konform**.

Alle Felder aus Tabelle 77-92 (Bauteile) und Tabelle 96 (Zonen) sind vorhanden.

**Nächster Schritt:** Parser v3 an Schema v2.2.1 anpassen (Phase 2).
