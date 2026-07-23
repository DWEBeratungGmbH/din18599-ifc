# Migration Guide: Schema v2.1 → v2.2

## Überblick

**Kernänderung:** Umstellung von opak/transparent-Struktur auf **Bauteiltyp-basierte Struktur** (walls, roofs, floors, windows, doors).

**Begründung:** Alle Standards (gbXML, EnergyPlus, IFC, HBJSON) strukturieren nach Bauteiltyp. Die opak/transparent-Achse ist eine GEG-Kategorisierung, keine Datenstruktur.

---

## A1: envelope neu strukturiert

### v2.1 (ALT)
```json
"envelope": {
  "opaque_elements": {
    "walls_external": [...],
    "walls_internal": [...],
    "roofs": [...],
    "floors": [...]
  },
  "transparent_elements": {
    "windows": [...],
    "doors": [...]
  }
}
```

### v2.2 (NEU)
```json
"envelope": {
  "walls": [...],      // Alle Wände (AW + IW)
  "roofs": [...],      // Alle Dächer
  "floors": [...],     // Alle Böden/Decken
  "windows": [...],    // Alle Fenster
  "doors": [...]       // Alle Türen
}
```

**Vorteil:**
- Parser liefert bereits `walls[]`, `roofs[]`, `floors[]` → direktes Mapping
- Konsistent mit IFC-Struktur (IfcWall, IfcSlab, IfcRoof)
- Konsistent mit allen Branchenstandards

---

## A2: boundary_condition Attribut (NEU)

**Ersetzt:** Die opak/transparent-Unterscheidung durch eine präzisere Randbedingung.

**Hinzugefügt zu:** `opaque_element` und `transparent_element`

```json
"boundary_condition": {
  "type": "string",
  "enum": ["exterior", "ground", "unheated", "adjacent"],
  "description": "Randbedingung für Fx-Faktoren"
}
```

**Mapping:**
- `exterior` = Außenwand/Außenluft (IsExternal=true)
- `ground` = Erdreich (z < 0)
- `unheated` = Unbeheizt (z.B. Keller, Dachboden)
- `adjacent` = Angrenzend an andere Zone

**Vorteil:**
- DIN 18599 braucht diese Unterscheidung für Fx-Korrekturfaktoren
- Präziser als nur "opak" vs "transparent"
- Kann aus IFC abgeleitet werden (IsExternal + Z-Position)

---

## A3: zone erweitert

### v2.1 (ALT)
```json
"zone": {
  "id": "...",
  "name": "...",
  "usage_profile_ref": "...",
  "area": 50.0
}
```

### v2.2 (NEU)
```json
"zone": {
  "id": "...",
  "ifc_guid": "...",           // NEU
  "name": "...",
  "usage_profile_ref": "...",
  "area": 50.0,
  "volume": 125.0,             // NEU (essenziell für DIN 18599)
  "height": 2.5,               // NEU (essenziell für DIN 18599)
  "storey_ref": "..."          // NEU (Referenz zu Geschoss)
}
```

**Begründung:**
- `volume` und `height` sind **Pflichtgrößen** für DIN 18599 Berechnung
- Können direkt aus IfcSpace extrahiert werden (ExtrudedAreaSolid oder IfcElementQuantity)
- `storey_ref` ermöglicht Zuordnung zu Geschoss

---

## A4: IFC-Metadaten hinzugefügt

**Neue Felder in allen Elementen:**

```json
"ifc_guid": "2O2Fr$t4X7Zf8NOew3FLOH",
"ifc_type": "IfcWall",
"predefined_type": "SOLIDWALL",
"name": "Wand - 014",
"storey_ref": "storey_guid_123",
"parent_element_guid": "wall_guid_456"  // Für Fenster/Türen
```

**Vorteil:**
- Vollständige Rückverfolgbarkeit zur IFC-Datei
- `predefined_type` ermöglicht korrekte Slab-Klassifizierung (ROOF → roofs)
- `parent_element_guid` für Fenster-Wand-Zuordnung

---

## A5: building.storeys (NEU)

```json
"building": {
  "storeys": [
    {
      "id": "guid_eg",
      "name": "EG",
      "elevation": -0.2
    },
    {
      "id": "guid_og",
      "name": "OG",
      "elevation": 2.7
    },
    {
      "id": "guid_dg",
      "name": "DG",
      "elevation": 5.5
    }
  ]
}
```

**Vorteil:**
- Geschoss-Elevations für DG-Ebene und Bodenplatten-Check
- Ermöglicht Validierung (fehlt Bodenplatte?)

---

## Migration-Schritte

### 1. Parser-Output anpassen

**Aktuell (v2.1):**
```python
return {
    "walls": [...],
    "roofs": [...],
    "floors": [...]
}
```

**Neu (v2.2):**
```python
return {
    "envelope": {
        "walls": [...],
        "roofs": [...],
        "floors": [...],
        "windows": [...],
        "doors": [...]
    },
    "building": {
        "storeys": [...],
        "zones": [...]
    }
}
```

### 2. boundary_condition ableiten

```python
def derive_boundary_condition(elem):
    if elem.is_external:
        return "exterior"
    elif elem.z_position < 0:
        return "ground"
    elif elem.storey in ["Keller", "Dachboden"]:
        return "unheated"
    else:
        return "adjacent"
```

### 3. Zone-Geometrie berechnen

```python
def calculate_zone_geometry(ifc_space):
    # Aus ExtrudedAreaSolid
    area = calculate_area(ifc_space.Representation)
    volume = calculate_volume(ifc_space.Representation)
    height = volume / area
    
    # Oder aus IfcElementQuantity
    qto = get_quantity_set(ifc_space, "BaseQuantities")
    area = qto.get("NetFloorArea")
    volume = qto.get("NetVolume")
    height = qto.get("Height")
    
    return {"area": area, "volume": volume, "height": height}
```

---

## Abwärtskompatibilität

**Keine Abwärtskompatibilität** - v2.2 ist ein Breaking Change.

**Grund:** Die Struktur ist fundamental anders (Bauteiltyp statt opak/transparent).

**Empfehlung:** 
- Alte Sidecars mit v2.1 Schema behalten
- Neue Sidecars mit v2.2 Schema erstellen
- Migrations-Tool für Bestandsdaten (falls nötig)

---

## Validierung

**Test mit DIN18599Test v3.ifc:**

```bash
# Parser v3 mit Schema v2.2
python -m api.parsers.ifc_parser_v2 ../sources/IFC_EVBI/DIN18599TestIFCv3.ifc

# Erwartete Ausgabe:
{
  "envelope": {
    "walls": [20 Elemente],
    "roofs": [12 Elemente],
    "floors": [3 Elemente],
    "windows": [9 Elemente],
    "doors": [4 Elemente]
  },
  "building": {
    "storeys": [3 Geschosse],
    "zones": [6 Zonen mit volume/height]
  }
}
```

---

## Zusammenfassung

| Änderung | v2.1 | v2.2 | Begründung |
|----------|------|------|------------|
| **Struktur** | opaque/transparent | walls/roofs/floors | Konsistent mit IFC + Standards |
| **Randbedingung** | Implizit (opak/transparent) | `boundary_condition` | Fx-Faktoren für DIN 18599 |
| **Zone** | Nur area | area + volume + height | Pflichtgrößen für Berechnung |
| **IFC-Metadaten** | Nur ifc_guid | guid + type + predefined_type | Rückverfolgbarkeit |
| **Geschosse** | Fehlt | storeys mit elevation | Validierung + Zuordnung |

**Ergebnis:** Schema v2.2 ist **IFC-nativ** und **berechnungsbereit** für DIN 18599.
