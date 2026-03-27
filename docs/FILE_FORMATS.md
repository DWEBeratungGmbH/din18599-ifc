# Datei-Formate & Modi

**Version:** 2.0  
**Stand:** März 2026

---

## 1. Überblick

Das **IFC + DIN 18599 Sidecar** Format unterstützt **3 Modi** für unterschiedliche Workflows:

| Modus | Dateien | Geometrie | Use Case | LOD |
|-------|---------|-----------|----------|-----|
| **Standalone** | 1 (JSON) | Keine | Schnellschätzung, iSFP | 100-200 |
| **Simplified** | 1 (JSON) | 2D/3D vereinfacht | Variantenvergleich | 200-300 |
| **IFC-Linked** | 2 (IFC + JSON) | IFC (vollständig) | GEG-Nachweis | 400-500 |

---

## 2. Modus 1: Standalone (nur Sidecar)

**Konzept:** Energiedaten **ohne Geometrie**

### Dateistruktur

```
projekt/
└── gebaeude.din18599.json
```

### Beispiel

```json
{
  "meta": {
    "project_name": "Musterhaus",
    "lod": "100",
    "standalone_mode": true
  },
  "input": {
    "zones": [
      {
        "id": "ZONE-01",
        "name": "Wohnbereich",
        "area_an": 85.5,
        "volume_v": 213.75
      }
    ],
    "elements": [
      {
        "name": "Außenwand Süd",
        "type": "WALL",
        "area": 25.0,
        "orientation": 180,
        "u_value_undisturbed": 1.4
      }
    ]
  }
}
```

### Vorteile
- ✅ **Einfach** - Nur 1 Datei
- ✅ **Schnell** - Keine Geometrie-Berechnung
- ✅ **Flexibel** - Für Bestandsaufnahme ohne Pläne

### Nachteile
- ❌ Keine 3D-Visualisierung
- ❌ Flächen müssen manuell eingegeben werden

### Use Cases
- Schnellschätzung (LOD 100)
- iSFP-Beratung ohne Pläne (LOD 200)
- Monitoring (nur Energiedaten)

---

## 3. Modus 2: Simplified Geometry (Sidecar mit 2D/3D)

**Konzept:** Vereinfachte Geometrie **im Sidecar** (wie gbXML)

### Dateistruktur

```
projekt/
└── gebaeude.din18599.json  (mit geometry-Feldern)
```

### Hierarchisches Modell (Parent-Child)

**Konzept:** Geometrie ist **relativ zum Parent** gespeichert

```
Building (Ursprung 0,0,0)
  └─ Zone (relativ zu Building)
      ├─ Space (relativ zu Zone)
      │   └─ Element (relativ zu Space)
      └─ Element (relativ zu Zone)
```

**Vorteile:**
- ✅ **Änderungen propagieren** automatisch
- ✅ **Koordinaten einfacher** (relativ statt absolut)
- ✅ **Wiederverwendbar** (gleiche Geometrie, verschiedene Positionen)

### Beispiel: Hierarchische Geometrie

```json
{
  "meta": {
    "project_name": "Musterhaus",
    "lod": "300",
    "simplified_geometry": true,
    "geometry_mode": "HIERARCHICAL"
  },
  "input": {
    "building": {
      "geometry": {
        "origin": [0, 0, 0],
        "rotation": 0
      }
    },
    "zones": [
      {
        "id": "ZONE-01",
        "name": "Wohnbereich EG",
        "area_an": 85.5,
        "volume_v": 213.75,
        "geometry": {
          "type": "Polygon2D",
          "parent_ref": "BUILDING",
          "local_origin": [0, 0, 0],
          "coordinates": [
            [0, 0],
            [10, 0],
            [10, 8.5],
            [0, 8.5]
          ],
          "floor_level": 0.0,
          "ceiling_height": 2.5
        },
        "spaces": [
          {
            "id": "SPACE-01",
            "name": "Wohnzimmer",
            "area_an": 45.0,
            "geometry": {
              "type": "Polygon2D",
              "parent_ref": "ZONE-01",
              "local_origin": [0, 0, 0],
              "coordinates": [
                [0, 0],
                [6, 0],
                [6, 7.5],
                [0, 7.5]
              ]
            }
          },
          {
            "id": "SPACE-02",
            "name": "Küche",
            "area_an": 40.5,
            "geometry": {
              "type": "Polygon2D",
              "parent_ref": "ZONE-01",
              "local_origin": [6, 0, 0],
              "coordinates": [
                [0, 0],
                [4, 0],
                [4, 8.5],
                [0, 8.5]
              ]
            }
          }
        ]
      }
    ],
    "elements": [
      {
        "name": "Außenwand Süd",
        "type": "WALL",
        "space_id": "SPACE-01",
        "geometry": {
          "type": "Line2D",
          "parent_ref": "SPACE-01",
          "local_origin": [0, 0, 0],
          "start": [0, 0],
          "end": [6, 0],
          "height": 2.5
        },
        "area": 15.0,
        "orientation": 180,
        "u_value_undisturbed": 0.24
      },
      {
        "name": "Trennwand Wohnzimmer/Küche",
        "type": "WALL",
        "boundary_condition": "INTERIOR",
        "geometry": {
          "type": "Line2D",
          "parent_ref": "ZONE-01",
          "local_origin": [6, 0, 0],
          "start": [0, 0],
          "end": [0, 7.5],
          "height": 2.5
        },
        "area": 18.75
      }
    ]
  }
}
```

**Koordinaten-Berechnung:**

```javascript
// Absolute Position eines Elements berechnen
function getAbsolutePosition(element) {
  let position = element.geometry.local_origin;
  let parent = element.geometry.parent_ref;
  
  while (parent) {
    const parentGeom = findGeometry(parent);
    position = add(position, parentGeom.local_origin);
    parent = parentGeom.parent_ref;
  }
  
  return position;
}

// Beispiel: Außenwand Süd
// local_origin: [0, 0, 0] (relativ zu SPACE-01)
// SPACE-01.local_origin: [0, 0, 0] (relativ zu ZONE-01)
// ZONE-01.local_origin: [0, 0, 0] (relativ zu BUILDING)
// BUILDING.origin: [0, 0, 0]
// → Absolute Position: [0, 0, 0]

// Beispiel: Trennwand
// local_origin: [6, 0, 0] (relativ zu ZONE-01)
// ZONE-01.local_origin: [0, 0, 0] (relativ zu BUILDING)
// → Absolute Position: [6, 0, 0]
```

### Transformations (Änderungen propagieren)

**Szenario 1: Zone verschieben**

```javascript
// Zone um 5m nach Osten verschieben
zone.geometry.local_origin = [5, 0, 0];

// Automatisch betroffen:
// - Alle Spaces in der Zone
// - Alle Elements in der Zone
// - Alle Elements in den Spaces
```

**Szenario 2: Space verschieben (innerhalb Zone)**

```javascript
// Küche um 1m nach Norden verschieben
space_02.geometry.local_origin = [6, 1, 0];

// Automatisch betroffen:
// - Alle Elements in SPACE-02
// - ZONE-01 bleibt unverändert
```

**Szenario 3: Gebäude rotieren**

```javascript
// Gebäude um 45° drehen
building.geometry.rotation = 45;

// Automatisch betroffen:
// - Alle Zones
// - Alle Spaces
// - Alle Elements
// → Orientierung aller Wände ändert sich!
```

### Use Cases

**Use Case 1: Mehrfamilienhaus (gleiche Wohnungen)**

```json
{
  "zones": [
    {
      "id": "ZONE-EG-01",
      "name": "Wohnung EG",
      "geometry": {
        "parent_ref": "BUILDING",
        "local_origin": [0, 0, 0],
        "template_ref": "WOHNUNG_TYP_A"
      }
    },
    {
      "id": "ZONE-OG-01",
      "name": "Wohnung OG",
      "geometry": {
        "parent_ref": "BUILDING",
        "local_origin": [0, 0, 3.0],
        "template_ref": "WOHNUNG_TYP_A"
      }
    }
  ],
  "templates": {
    "WOHNUNG_TYP_A": {
      "spaces": [...],
      "elements": [...]
    }
  }
}
```

**Use Case 2: Sanierung (vorher/nachher)**

```json
{
  "scenarios": [
    {
      "id": "BASE",
      "name": "Bestand",
      "elements": [
        {
          "id": "AW-01",
          "geometry": {
            "parent_ref": "ZONE-01",
            "local_origin": [0, 0, 0],
            "start": [0, 0],
            "end": [10, 0]
          },
          "u_value_undisturbed": 1.4
        }
      ]
    },
    {
      "id": "SANIERT",
      "name": "Saniert",
      "changes": {
        "elements": [
          {
            "id": "AW-01",
            "u_value_undisturbed": 0.24,
            "layer_structure_ref": "LS-AW-GEDAEMMT"
          }
        ]
      }
    }
  ]
}
```

**Vorteil:** Geometrie bleibt gleich, nur U-Wert ändert sich!

**Use Case 3: Anbau (Geometrie ändert sich)**

```json
{
  "scenarios": [
    {
      "id": "BASE",
      "zones": [
        {
          "id": "ZONE-01",
          "geometry": {
            "coordinates": [[0,0], [10,0], [10,8.5], [0,8.5]]
          }
        }
      ]
    },
    {
      "id": "ANBAU",
      "changes": {
        "zones": [
          {
            "id": "ZONE-02",
            "name": "Anbau",
            "geometry": {
              "parent_ref": "BUILDING",
              "local_origin": [10, 0, 0],
              "coordinates": [[0,0], [5,0], [5,6], [0,6]]
            }
          }
        ]
      }
    }
  ]
}
```

### Geometrie-Typen

#### Polygon2D (Zonen-Grundriss)

```json
{
  "type": "Polygon2D",
  "coordinates": [
    [x1, y1],
    [x2, y2],
    [x3, y3],
    [x4, y4]
  ],
  "floor_level": 0.0,      // z-Koordinate Boden
  "ceiling_height": 2.5    // Raumhöhe
}
```

**Berechnung:**
- `area_an` = Fläche des Polygons (Shoelace-Formel)
- `volume_v` = area_an × ceiling_height

#### Line2D (Wände)

```json
{
  "type": "Line2D",
  "start": [x1, y1],
  "end": [x2, y2],
  "height": 2.5,
  "base_level": 0.0
}
```

**Berechnung:**
- `area` = Länge × height
- `orientation` = Azimut der Linie (0=Nord, 90=Ost, 180=Süd, 270=West)

#### Rectangle2D (Fenster, Türen)

```json
{
  "type": "Rectangle2D",
  "center": [x, y],
  "width": 1.5,
  "height": 1.2,
  "base_level": 0.8
}
```

**Berechnung:**
- `area` = width × height

### Vorteile
- ✅ **3D-Visualisierung** möglich (Three.js)
- ✅ **Flächen-Berechnung** automatisch
- ✅ **Leichtgewichtig** (10-100 KB statt 10-100 MB IFC)
- ✅ **Editierbar** (JSON, kein IFC-Editor nötig)

### Nachteile
- ⚠️ Vereinfachte Geometrie (keine komplexen Formen)
- ⚠️ Keine BIM-Kollisionsprüfung

### Use Cases
- Variantenvergleich (LOD 300)
- iSFP mit Grundrissen (LOD 200-300)
- Sanierungsplanung

---

## 4. Modus 3: IFC-Linked (Sidecar + IFC)

**Konzept:** Sidecar **referenziert** IFC-Geometrie via GUIDs

### Dateistruktur

```
projekt/
├── gebaeude.ifc
└── gebaeude.din18599.json
```

### Beispiel

```json
{
  "meta": {
    "project_name": "Musterhaus",
    "lod": "400",
    "ifc_file_ref": "gebaeude.ifc",
    "ifc_guid_building": "2Uj8Lq3Vr9QxPkXr4bN8FD"
  },
  "input": {
    "zones": [
      {
        "id": "ZONE-01",
        "name": "Wohnbereich",
        "space_guids": ["3Fk9Mp4Ws0RyQlYs5cO9GE"],
        "area_an": 85.5,
        "volume_v": 213.75
      }
    ],
    "elements": [
      {
        "ifc_guid": "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8",
        "name": "Außenwand Süd",
        "type": "WALL",
        "u_value_undisturbed": 0.24
      }
    ]
  }
}
```

### Vorteile
- ✅ **Vollständige Geometrie** (IFC)
- ✅ **BIM-Workflow** (Architekten-Export)
- ✅ **Automatische Flächen** (aus IFC)
- ✅ **3D-Viewer** (xeokit, IFC.js)

### Nachteile
- ❌ **2 Dateien** nötig
- ❌ **Große Dateien** (10-100 MB IFC)
- ❌ **Synchronisation** (GUID-Änderungen)

### Use Cases
- GEG-Nachweis (LOD 400)
- Bauantrag (LOD 400)
- As-Built-Dokumentation (LOD 500)

---

## 5. Modus-Vergleich

### Workflow-Entscheidungsbaum

```
Habe ich IFC-Pläne?
│
├─ Nein
│  │
│  ├─ Habe ich Grundrisse (PDF/CAD)?
│  │  │
│  │  ├─ Ja → Modus 2 (Simplified Geometry)
│  │  │        - Grundriss digitalisieren
│  │  │        - Polygon2D erstellen
│  │  │
│  │  └─ Nein → Modus 1 (Standalone)
│  │             - Flächen manuell eingeben
│  │
│  └─ Nur grobe Schätzung → Modus 1 (Standalone)
│
└─ Ja (IFC vorhanden)
   │
   └─ Modus 3 (IFC-Linked)
      - IFC + Sidecar
      - GUID-Verknüpfung
```

### Feature-Matrix

| Feature | Standalone | Simplified | IFC-Linked |
|---------|-----------|------------|------------|
| **Dateien** | 1 | 1 | 2 |
| **Dateigröße** | 10 KB | 50 KB | 10 MB |
| **3D-Viewer** | ❌ | ✅ (einfach) | ✅ (komplex) |
| **Flächen** | Manuell | Automatisch | Automatisch |
| **Editierbar** | ✅ | ✅ | ⚠️ |
| **LOD** | 100-200 | 200-300 | 400-500 |
| **Zeitaufwand** | 1-2h | 4-8h | 40-60h |

---

## 6. Geometrie-Berechnung

### Flächen-Berechnung (Polygon2D)

**Shoelace-Formel:**

```javascript
function calculateArea(coordinates) {
  let area = 0;
  const n = coordinates.length;
  
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += coordinates[i][0] * coordinates[j][1];
    area -= coordinates[j][0] * coordinates[i][1];
  }
  
  return Math.abs(area) / 2;
}

// Beispiel
const coords = [[0, 0], [10, 0], [10, 8.5], [0, 8.5]];
const area = calculateArea(coords); // 85.5 m²
```

### Orientierung-Berechnung (Line2D)

**Azimut-Berechnung:**

```javascript
function calculateOrientation(start, end) {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  
  let azimuth = Math.atan2(dx, dy) * 180 / Math.PI;
  
  // Normalisieren auf 0-360°
  if (azimuth < 0) azimuth += 360;
  
  return azimuth;
}

// Beispiel
const start = [0, 0];
const end = [10, 0];
const orientation = calculateOrientation(start, end); // 90° (Ost)
```

---

## 7. Validierung

### Geometrie-Validierung

```python
def validate_geometry(zone):
    """Validiert Zonen-Geometrie"""
    
    if not zone.get("geometry"):
        return  # Optional
    
    geom = zone["geometry"]
    
    # Polygon2D
    if geom["type"] == "Polygon2D":
        coords = geom["coordinates"]
        
        # Mindestens 3 Punkte
        if len(coords) < 3:
            error("Polygon muss mindestens 3 Punkte haben")
        
        # Geschlossen (erster = letzter Punkt)
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        
        # Fläche berechnen
        area = calculate_area(coords)
        
        # Plausibilität
        if area < 5:
            warn("Sehr kleine Fläche (< 5 m²)")
        if area > 1000:
            warn("Sehr große Fläche (> 1000 m²)")
```

---

## 8. Migration zwischen Modi

### Standalone → Simplified

```python
def add_simplified_geometry(data):
    """Fügt vereinfachte Geometrie hinzu"""
    
    for zone in data["input"]["zones"]:
        # Rechteck aus Fläche generieren
        area = zone["area_an"]
        side = math.sqrt(area)
        
        zone["geometry"] = {
            "type": "Polygon2D",
            "coordinates": [
                [0, 0],
                [side, 0],
                [side, side],
                [0, side]
            ],
            "floor_level": 0.0,
            "ceiling_height": 2.5
        }
```

### Simplified → IFC-Linked

```python
def link_to_ifc(sidecar_data, ifc_file):
    """Verknüpft Sidecar mit IFC"""
    
    # IFC laden
    ifc = ifcopenshell.open(ifc_file)
    
    # Building GUID
    building = ifc.by_type("IfcBuilding")[0]
    sidecar_data["meta"]["ifc_guid_building"] = building.GlobalId
    
    # Spaces zu Zonen mappen
    for zone in sidecar_data["input"]["zones"]:
        # Finde passende IfcSpaces (nach Name oder Fläche)
        spaces = find_matching_spaces(ifc, zone)
        zone["space_guids"] = [s.GlobalId for s in spaces]
        
        # Geometrie aus IFC entfernen (optional)
        del zone["geometry"]
```

---

## 9. Hierarchisches Modell - Best Practices

### Parent-Referenzen

**Regel 1: Immer parent_ref angeben**

```json
{
  "geometry": {
    "type": "Polygon2D",
    "parent_ref": "ZONE-01",  // Pflicht!
    "local_origin": [0, 0, 0],
    "coordinates": [...]
  }
}
```

**Regel 2: Zirkuläre Referenzen vermeiden**

```json
// ❌ FALSCH
{
  "zones": [
    {"id": "ZONE-01", "geometry": {"parent_ref": "ZONE-02"}},
    {"id": "ZONE-02", "geometry": {"parent_ref": "ZONE-01"}}
  ]
}

// ✅ RICHTIG
{
  "zones": [
    {"id": "ZONE-01", "geometry": {"parent_ref": "BUILDING"}},
    {"id": "ZONE-02", "geometry": {"parent_ref": "BUILDING"}}
  ]
}
```

**Regel 3: Hierarchie-Ebenen**

```
BUILDING (Level 0)
  └─ ZONE (Level 1)
      └─ SPACE (Level 2)
          └─ ELEMENT (Level 3)
```

**Max. 4 Ebenen empfohlen!**

### Koordinaten-System

**Regel 1: Rechts-Hand-System (Relativ)**

```
X-Achse: Relativ nach rechts (positiv)
Y-Achse: Relativ nach vorne (positiv)
Z-Achse: Höhe (positiv nach oben)
```

**Regel 2: Einheiten**

```
Längen: Meter (m)
Winkel: Grad (°) - relativ zum Gebäude
Flächen: Quadratmeter (m²)
```

**Regel 3: Ursprung & Orientierung**

```json
{
  "building": {
    "geometry": {
      "origin": [0, 0, 0],        // Gebäude-Ursprung
      "north_angle": 0            // Nord-Ausrichtung (0° = Y-Achse zeigt nach Norden)
    }
  }
}
```

**Vorteil:** Gebäude kann gedreht werden, ohne alle Elemente anzupassen!

```javascript
// Beispiel: Gebäude um 45° drehen
building.geometry.north_angle = 45;

// Alle Orientierungen bleiben relativ:
// - Wand mit relative_orientation: 0° bleibt "vorne"
// - Absolute Orientierung = north_angle + relative_orientation
// - 45° + 0° = 45° (Nordost)
```

### Performance-Optimierung

**Regel 1: Templates nutzen**

Für wiederkehrende Geometrien (z.B. gleiche Wohnungen):

```json
{
  "templates": {
    "WOHNUNG_60QM": {
      "spaces": [...],
      "elements": [...]
    }
  },
  "zones": [
    {"id": "ZONE-01", "template_ref": "WOHNUNG_60QM", "local_origin": [0, 0, 0]},
    {"id": "ZONE-02", "template_ref": "WOHNUNG_60QM", "local_origin": [0, 0, 3]}
  ]
}
```

**Regel 2: Lazy Loading**

Nur benötigte Ebenen laden:

```javascript
// Nur Zonen laden (ohne Spaces/Elements)
const zones = data.input.zones.map(z => ({
  id: z.id,
  name: z.name,
  geometry: z.geometry
}));
```

**Regel 3: Caching**

Absolute Positionen cachen:

```javascript
const positionCache = new Map();

function getAbsolutePosition(element) {
  if (positionCache.has(element.id)) {
    return positionCache.get(element.id);
  }
  
  const position = calculateAbsolutePosition(element);
  positionCache.set(element.id, position);
  return position;
}
```

---

## 10. Best Practices (Modi)

### Wann welcher Modus?

**Standalone:**
- ✅ Schnellschätzung (LOD 100)
- ✅ Bestandsaufnahme ohne Pläne
- ✅ Monitoring (nur Energiedaten)

**Simplified:**
- ✅ iSFP mit Grundrissen (LOD 200-300)
- ✅ Variantenvergleich
- ✅ Sanierungsplanung

**IFC-Linked:**
- ✅ GEG-Nachweis (LOD 400)
- ✅ Bauantrag
- ✅ BIM-Workflow (Architekten-Export)

### Geometrie-Qualität

**Simplified Geometry:**
- ✅ Genauigkeit: ±5-10% (ausreichend für LOD 200-300)
- ✅ Rechtecke für einfache Räume
- ✅ Polygone für komplexe Grundrisse
- ❌ Keine schrägen Wände/Dächer

**IFC:**
- ✅ Genauigkeit: ±1-2% (erforderlich für LOD 400+)
- ✅ Alle Geometrie-Typen
- ✅ BIM-Kollisionsprüfung

---

## 10. Beispiele

### Beispiel 1: Standalone (LOD 100)

Siehe: `examples/lod100_schnellschaetzung.din18599.json`

### Beispiel 2: Simplified Geometry (LOD 300)

Siehe: `examples/lod300_sanierung_varianten.din18599.json`
(wird erweitert um `geometry`-Felder)

### Beispiel 3: IFC-Linked (LOD 400)

Siehe: `examples/lod400_geg_nachweis.din18599.json`

---

**Status:** ✅ Alle 3 Modi sind definiert und dokumentiert.  
**Nächster Schritt:** Schema erweitern um `geometry`-Felder.
