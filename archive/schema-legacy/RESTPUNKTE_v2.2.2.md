# Restpunkte für Schema v2.2.2

## Überblick

Schema v2.2 ist bei **~95% Produktionsreife** und bereit für Parser-Anpassung.

Die folgenden 2 Punkte sind **keine Blocker**, können aber in v2.2.2 nachgezogen werden.

---

## R3: Türen als transparent_element (semantisch unsauber)

**Problem:** Opake Türen (z.B. Haustür aus Holz) haben kein `g_value`, `tau_value`, etc. - diese Felder sind semantisch falsch für nicht-verglaste Türen.

**Aktueller Workaround:** `is_glazed` Flag unterscheidet verglaste von opaken Türen.

**Sauberere Lösung (v2.2.2):**

### Option 1: Separate door_element Definition

```json
"doors": {
  "type": "array",
  "items": {"$ref": "#/definitions/door_element"}
}

"door_element": {
  "type": "object",
  "required": ["id", "area"],
  "properties": {
    "id": {"type": "string"},
    "ifc_guid": {"type": "string"},
    "u_value": {"type": "number"},
    "area": {"type": "number"},
    "is_glazed": {"type": "boolean"},
    // Nur wenn is_glazed=true:
    "g_value": {"type": "number"},
    "tau_value": {"type": "number"}
  }
}
```

### Option 2: oneOf mit glazed/opaque Varianten

```json
"transparent_element": {
  "oneOf": [
    {
      "properties": {
        "is_glazed": {"const": true},
        "g_value": {"type": "number", "required": true}
      }
    },
    {
      "properties": {
        "is_glazed": {"const": false}
      }
    }
  ]
}
```

**Empfehlung:** Option 1 (separate door_element) ist sauberer, aber **nicht dringend**. Aktueller Zustand funktioniert.

---

## R4: g_value vs g_value_perpendicular Redundanz

**Problem:** Welches ist der "Basis-g-Wert"?

**Aktuell:**
- `g_value` (alt, unklar ob senkrecht oder effektiv)
- `g_value_perpendicular` (neu, eindeutig g⊥)
- `g_value_summer` (mit Sonnenschutz Sommer)
- `g_value_winter` (mit Sonnenschutz Winter)

**Fachlich korrekt (DIN 18599):**
- g⊥ = Referenzwert (senkrechter Einfall)
- g_eff = Effektiver g-Wert (winkelabhängig)
- g_summer/winter = Mit Sonnenschutz

**Sauberere Lösung (v2.2.2):**

```json
"g_value_perpendicular": {
  "type": "number",
  "description": "g⊥ senkrecht (Referenzwert)"
},
"g_value_effective": {
  "type": "number",
  "description": "g_eff effektiv (winkelabhängig, optional)"
},
"g_value_summer": {"type": "number"},
"g_value_winter": {"type": "number"}
```

**Und `g_value` als deprecated markieren:**

```json
"g_value": {
  "type": "number",
  "deprecated": true,
  "description": "DEPRECATED: Nutze g_value_perpendicular"
}
```

**Empfehlung:** In v2.2.2 klären und `g_value` entweder entfernen oder als Alias für `g_value_perpendicular` definieren.

---

## Vollständige din_code Mapping-Tabelle

Für Parser-Implementierung (Phase 2):

### Opake Bauteile

| Code | Beschreibung | Bauteiltyp | boundary_condition | Sonstiges |
|------|--------------|------------|-------------------|-----------|
| WA | Außenwand | Wall | exterior | - |
| WI | Innenwand | Wall | adjacent | - |
| WE | Wand Erdreich | Wall | ground | - |
| WU | Wand unbeheizt | Wall | unheated | - |
| WZ | Wand Zone | Wall | adjacent | Zu anderer Zone |
| DA | Dach Außenluft | Roof/Slab(ROOF) | exterior | - |
| DE | Dach unbeheizt | Roof/Slab(ROOF) | unheated | - |
| DU | Dach Erdreich | Roof/Slab(ROOF) | ground | Selten |
| DZ | Dach Zone | Roof/Slab(ROOF) | adjacent | - |
| BE | Boden Erdreich | Slab(FLOOR/BASESLAB) | ground | - |
| BO | Boden Außenluft | Slab(FLOOR/BASESLAB) | exterior | - |
| BU | Boden unbeheizt | Slab(FLOOR/BASESLAB) | unheated | - |
| BZ | Boden Zone | Slab(FLOOR/BASESLAB) | adjacent | - |
| RK | Rollladenkasten | - | - | Sonderbauteil |
| GF | Glasfassade | - | - | Sonderbauteil |
| PF | Pfosten-Riegel | - | - | Sonderbauteil |

### Transparente Bauteile

| Code | Beschreibung | Bauteiltyp | inclination | boundary_condition |
|------|--------------|------------|-------------|-------------------|
| FA | Fenster Außenwand | Window | ≥ 60° | exterior |
| FD | Fenster Dachfläche | Window | 22-60° | exterior |
| FL | Fenster Lichtkuppel | Window | < 22° | exterior |
| FU | Fenster unbeheizt | Window | - | unheated |
| FZ | Fenster Zone | Window | - | adjacent |
| TA | Tür Außenwand | Door | ≥ 60° | exterior |
| TD | Tür Dach | Door | 22-60° | exterior |
| TU | Tür unbeheizt | Door | - | unheated |
| TZ | Tür Zone | Door | - | adjacent |

---

## Parser-Implementierung (Phase 2)

```python
def derive_din_code(elem):
    """Vollständige din_code Ableitung"""
    
    # Opake Bauteile
    if elem.ifc_type == 'IfcWall':
        if elem.boundary_condition == 'exterior':
            return 'WA'
        elif elem.boundary_condition == 'ground':
            return 'WE'
        elif elem.boundary_condition == 'unheated':
            return 'WU'
        elif elem.zone_ref:  # Zu anderer Zone
            return 'WZ'
        else:
            return 'WI'
    
    elif elem.ifc_type in ['IfcRoof', 'IfcSlab'] and elem.predefined_type == 'ROOF':
        if elem.boundary_condition == 'exterior':
            return 'DA'
        elif elem.boundary_condition == 'unheated':
            return 'DE'
        elif elem.boundary_condition == 'ground':
            return 'DU'
        elif elem.zone_ref:
            return 'DZ'
    
    elif elem.ifc_type == 'IfcSlab':
        if elem.boundary_condition == 'ground':
            return 'BE'
        elif elem.boundary_condition == 'exterior':
            return 'BO'
        elif elem.boundary_condition == 'unheated':
            return 'BU'
        elif elem.zone_ref:
            return 'BZ'
    
    # Transparente Bauteile
    elif elem.ifc_type == 'IfcWindow':
        if elem.boundary_condition == 'unheated':
            return 'FU'
        elif elem.zone_ref:
            return 'FZ'
        elif elem.inclination >= 60:
            return 'FA'
        elif elem.inclination >= 22:
            return 'FD'
        else:
            return 'FL'
    
    elif elem.ifc_type == 'IfcDoor':
        if elem.boundary_condition == 'unheated':
            return 'TU'
        elif elem.zone_ref:
            return 'TZ'
        elif elem.inclination >= 60:
            return 'TA'
        else:
            return 'TD'
    
    return None
```

---

## Zusammenfassung

**Schema v2.2 Status:**
- ✅ Struktur: Produktionsreif
- ✅ DIN 18599: Normkonform
- ✅ IFC-Alignment: Parser-kompatibel
- ⚠️ R3+R4: Sauberkeitspunkte für v2.2.2

**Empfehlung:** 
- Jetzt mit Phase 2 (Parser-Anpassung) starten
- R3+R4 parallel in v2.2.2 nachziehen
- Keine Blocker mehr für End-to-End-Test

**Nächste Schritte:**
1. Parser v3 an Schema v2.2 anpassen
2. End-to-End Test mit DIN18599Test v3.ifc
3. Roundtrip-Test IFC → Sidecar → Hottgenroth
