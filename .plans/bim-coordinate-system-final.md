# BIM Coordinate System - Project North vs True North

**Datum:** 01.04.2026  
**Standard:** IFC / Revit / ArchiCAD  
**Status:** ✅ Finalisiert

---

## 🧭 Konzept: Zwei Norden-Systeme

### Project North (Plannorden)
- **Definition:** Y-Achse im lokalen Koordinatensystem
- **Zweck:** Gebäude im Plan optimal ausrichten (z.B. parallel zu Blattrand)
- **Geometrie:** Alle Solids sind relativ zum Plannorden definiert

### True North (Geografischer Norden)
- **Definition:** Echter Norden (Kompass, Himmelsrichtung)
- **Zweck:** Energieberechnung (Sonneneinstrahlung, Verschattung)
- **Offset:** Rotation zwischen Plannorden und geografischem Norden

---

## 📐 Koordinatensystem-Definition

### Lokales Koordinatensystem (Project North)
```
X-Achse: Rechts im Plan (Ost im Plannorden-System)
Y-Achse: Oben im Plan (Nord im Plannorden-System)
Z-Achse: Vertikal nach oben
```

### True North Offset
```
true_north_offset = Winkel vom Plannorden zum geografischen Norden
```

**Beispiele:**
- `0°`: Plannorden = Geografischer Norden (Standard)
- `-90°`: Plannorden zeigt nach Osten (geografisch)
- `90°`: Plannorden zeigt nach Westen (geografisch)
- `180°`: Plannorden zeigt nach Süden (geografisch)

---

## 🏗️ Schema-Definition

```json
{
  "meta": {
    "project_name": "EFH Musterhausen",
    "site": {
      "address": "Musterstraße 1, 12345 Berlin",
      "latitude": 52.520008,
      "longitude": 13.404954,
      "true_north_offset": -90,
      "description": "Plannorden zeigt nach Osten (geografisch)"
    }
  },
  "geometry": {
    "coordinate_system": {
      "type": "PROJECT_NORTH",
      "x_axis": "EAST (Project)",
      "y_axis": "NORTH (Project)",
      "z_axis": "UP",
      "unit": "METER"
    },
    "solids": [
      {
        "id": "eg_main",
        "type": "BOX",
        "dimensions": {"length": 10, "width": 8, "height": 2.5},
        "origin": [0, 0, 0],
        "rotation": 0  // Rotation um Z-Achse (im Plannorden-System)
      }
    ]
  }
}
```

---

## 🧮 Orientierung berechnen

### Formel

```javascript
function calculateTrueNorthOrientation(face, solid, trueNorthOffset) {
  // 1. Face-Normale im lokalen Koordinatensystem
  const normal = face.normal  // z.B. [0, -1, 0]
  
  // 2. Solid-Rotation anwenden (falls Solid gedreht)
  const rotatedNormal = rotateVector(normal, solid.rotation || 0)
  
  // 3. Winkel im Plannorden-System
  const angleProjectNorth = Math.atan2(rotatedNormal[1], rotatedNormal[0]) * 180 / Math.PI
  
  // 4. True North Offset anwenden
  const orientationTrueNorth = (angleProjectNorth + trueNorthOffset + 360) % 360
  
  return {
    project_north: angleProjectNorth,
    true_north: orientationTrueNorth
  }
}
```

### Beispiel-Szenarien

**Szenario 1: Standard (Plan = Geografie)**
```javascript
Face-Normale: [0, -1, 0]  // -Y (Süd im Plan)
Solid-Rotation: 0°
True North Offset: 0°

angleProjectNorth = atan2(-1, 0) = 270° (West im Plan)
orientationTrueNorth = 270° (West geografisch)
```

**Szenario 2: Plan gedreht**
```javascript
Face-Normale: [0, -1, 0]  // -Y (Süd im Plan)
Solid-Rotation: 0°
True North Offset: -90°  // Plannorden = Osten (geografisch)

angleProjectNorth = 270° (West im Plan)
orientationTrueNorth = (270 + (-90) + 360) % 360 = 180° (Süd geografisch)

// ✅ Im Plan zeigt die Wand nach Westen,
//    geografisch aber nach Süden!
```

**Szenario 3: Solid gedreht + Plan gedreht**
```javascript
Face-Normale: [0, -1, 0]  // -Y im Solid-Koordinatensystem
Solid-Rotation: 45°       // Solid um 45° gedreht
True North Offset: -90°   // Plan gedreht

rotatedNormal = rotate([0, -1, 0], 45°) = [-0.707, -0.707, 0]
angleProjectNorth = atan2(-0.707, -0.707) = 225° (Südwest im Plan)
orientationTrueNorth = (225 + (-90) + 360) % 360 = 135° (Südost geografisch)
```

---

## 🎨 Visualisierung

### Im Viewer

**Plan-Ansicht (Project North):**
```
        N (Plan)
        ↑
        |
W ------+------ E
        |
        ↓
        S
```

**Mit True North Offset = -90°:**
```
Plan-Ansicht:          Geografisch:
        N (Plan)              E
        ↑                     ↑
        |                     |
W ------+------ E     S ------+------ N
        |                     |
        ↓                     ↓
        S                     W
```

**Kompass-Anzeige im Viewer:**
```javascript
// Zeige beide Norden
<Compass 
  projectNorth={0}           // Y-Achse
  trueNorth={-90}            // Geografischer Norden
  showBoth={true}
/>
```

---

## 📊 Vergleich mit BIM-Software

### Revit
- **Project North:** Definiert durch Projektbasis
- **True North:** Einstellbar in Site Settings
- **Rotation:** Über "Rotate True North" Tool

### ArchiCAD
- **Project North:** Story-Koordinatensystem
- **True North:** In Project Location Settings
- **Rotation:** Über Project North Angle

### IFC
- **IfcLocalPlacement:** Project North
- **IfcSite.RefLatitude/RefLongitude:** Geografische Position
- **IfcGeometricRepresentationContext.TrueNorth:** True North Direction

---

## ✅ Vorteile

1. **Flexibilität:** Gebäude kann im Plan gedreht werden, ohne Geometrie zu ändern
2. **Standard-konform:** Wie in Revit, ArchiCAD, IFC
3. **Energieberechnung:** True North für korrekte Sonneneinstrahlung
4. **Plan-Optimierung:** Project North für optimale Darstellung
5. **Einfach:** Nur ein Offset-Wert nötig

---

## 🔧 Implementation

### Schema v2.1

```json
{
  "meta": {
    "site": {
      "true_north_offset": 0,  // Default: Plan = Geografie
      "latitude": null,
      "longitude": null
    }
  }
}
```

### TypeScript

```typescript
interface Site {
  address?: string
  latitude?: number
  longitude?: number
  true_north_offset: number  // Grad, Default: 0
  description?: string
}

interface GeometryContext {
  coordinate_system: {
    type: 'PROJECT_NORTH'
    x_axis: 'EAST (Project)'
    y_axis: 'NORTH (Project)'
    z_axis: 'UP'
    unit: 'METER'
  }
}
```

### Viewer

```typescript
// In Zustand Store
const trueNorthOffset = project.meta.site?.true_north_offset || 0

// Bei Face-Rendering
const orientation = calculateTrueNorthOrientation(
  face,
  solid,
  trueNorthOffset
)

// Für DIN 18599 Berechnung
const wallOrientation = orientation.true_north  // Geografisch!
```

---

## 📝 Nächste Schritte

1. ✅ Schema v2.1 um `meta.site.true_north_offset` erweitern
2. ✅ `calculateTrueNorthOrientation()` implementieren
3. ✅ Demo-JSON mit verschiedenen Offsets testen
4. ⏳ Kompass-UI im Viewer (zeigt beide Norden)
5. ⏳ Dokumentation aktualisieren

---

**Status:** ✅ Konzept finalisiert  
**Nächster Schritt:** Schema v2.1 erweitern
