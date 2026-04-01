# Face-Mapping Revision - Geometrie-basiert statt Himmelsrichtung

**Datum:** 01.04.2026  
**Problem:** Ursprüngliches Konzept war zu vereinfacht  
**Lösung:** Geometrie-basiertes Face-Mapping mit globalem Kompass

---

## ❌ Probleme des alten Ansatzes

### 1. Himmelsrichtung direkt in Face-Index
```javascript
// ❌ FALSCH - zu starr
const FACE_MAPPING = {
  0: { name: 'Süd', orientation: 180 },
  1: { name: 'Ost', orientation: 90 }
}
```

**Probleme:**
- Funktioniert nur für achsparallele Gebäude
- Keine Flexibilität für gedrehte Gebäude
- Kompass-Abweichung nicht berücksichtigt

### 2. Neigung bei geneigten Flächen
```javascript
// ❌ FALSCH - Dreieck hat keine eindeutige "Orientierung"
{
  "type": "TRIANGULAR_PRISM",
  "face_index": 0,
  "orientation": 180  // Welche Richtung? Süd-Dachfläche ist schräg!
}
```

**Problem:**
- Geneigte Flächen haben **keine** eindeutige Himmelsrichtung
- Normale zeigt schräg nach oben
- Orientierung + Neigung müssen getrennt berechnet werden

---

## ✅ Neues Konzept: Geometrie-basiertes Face-Mapping

### 1. Face-Normale als Grundlage

**Jede Face hat eine geometrische Normale:**
```javascript
// BOX Face 0 (Süd-Seite im lokalen Koordinatensystem)
{
  normal: [0, -1, 0],  // Zeigt in -Y Richtung (lokal)
  vertices: [V0, V1, V2, V3]
}
```

**Keine Himmelsrichtung in der Geometrie!**

### 2. Globaler Kompass (Project-Level) - BIM-Standard

**Konzept aus BIM:**
- **Plannorden (Project North):** Y-Achse im lokalen Koordinatensystem
- **Geografischer Norden (True North):** Echter Norden (Kompass)
- **True North Offset:** Rotation zwischen Plan und Geografie

**Im `meta` Abschnitt:**
```json
{
  "meta": {
    "project_name": "EFH Musterhausen",
    "site": {
      "true_north_offset": -90,  // Geografischer Norden = -90° vom Plannorden
      "description": "Plannorden zeigt nach Osten (geografisch)"
    }
  }
}
```

**Standard:** `true_north_offset: 0` (Plannorden = Geografischer Norden)

**Vorteil:** Gebäude kann im Plan gedreht werden, ohne Geometrie zu ändern!

### 3. Orientierung berechnen (zur Laufzeit)

```javascript
function calculateOrientation(faceNormal, solidRotation, trueNorthOffset) {
  // 1. Face-Normale im lokalen Koordinatensystem (Plannorden)
  let normal = faceNormal  // z.B. [0, -1, 0]
  
  // 2. Solid-Rotation anwenden (falls Solid gedreht ist)
  normal = rotateVector(normal, solidRotation)
  
  // 3. Winkel im Plannorden-System berechnen
  const angleProjectNorth = Math.atan2(normal[1], normal[0]) * 180 / Math.PI
  
  // 4. True North Offset anwenden (Plannorden → Geografischer Norden)
  const orientationTrueNorth = (angleProjectNorth + trueNorthOffset + 360) % 360
  
  return {
    project_north: angleProjectNorth,    // Im Plan-Koordinatensystem
    true_north: orientationTrueNorth     // Geografisch (für DIN 18599)
  }
}
```

**Beispiel 1: Gebäude parallel zum Plan**
```javascript
// Face mit Normale [0, -1, 0] (zeigt in -Y Richtung im Plan)
// Solid-Rotation: 0°
// True North Offset: 0° (Plan = Geografie)

angleProjectNorth = atan2(-1, 0) = -90° = 270° (West im Plan)
orientationTrueNorth = (270 + 0 + 360) % 360 = 270° (West geografisch)
```

**Beispiel 2: Gebäude gedreht im Plan**
```javascript
// Face mit Normale [0, -1, 0] (zeigt in -Y Richtung im Plan)
// Solid-Rotation: 0°
// True North Offset: -90° (Plannorden zeigt nach Osten)

angleProjectNorth = atan2(-1, 0) = 270° (West im Plan)
orientationTrueNorth = (270 + (-90) + 360) % 360 = 180° (Süd geografisch)

// ✅ Gebäude ist im Plan nach Westen ausgerichtet,
//    aber geografisch nach Süden (weil Plan gedreht ist)
```

---

## 🎯 Face-Mapping Schema

### Face-Definitionen (geometrisch)

**BOX:**
```javascript
const BOX_FACES = [
  {
    index: 0,
    name: 'Face 0',
    normal: [0, -1, 0],  // -Y
    vertices: [0, 1, 2, 3]
  },
  {
    index: 1,
    name: 'Face 1',
    normal: [1, 0, 0],   // +X
    vertices: [4, 5, 6, 7]
  },
  {
    index: 2,
    name: 'Face 2',
    normal: [0, 1, 0],   // +Y
    vertices: [8, 9, 10, 11]
  },
  {
    index: 3,
    name: 'Face 3',
    normal: [-1, 0, 0],  // -X
    vertices: [12, 13, 14, 15]
  },
  {
    index: 4,
    name: 'Face 4 (Top)',
    normal: [0, 0, 1],   // +Z
    vertices: [16, 17, 18, 19]
  },
  {
    index: 5,
    name: 'Face 5 (Bottom)',
    normal: [0, 0, -1],  // -Z
    vertices: [20, 21, 22, 23]
  }
]
```

**TRIANGULAR_PRISM:**
```javascript
const PRISM_FACES = [
  {
    index: 0,
    name: 'Face 0 (Roof South)',
    normal: [0, -0.6, 0.8],  // Schräg! (Neigung ~37°)
    vertices: [0, 1, 4, 5]
  },
  {
    index: 1,
    name: 'Face 1 (Roof North)',
    normal: [0, 0.6, 0.8],   // Schräg! (Neigung ~37°)
    vertices: [2, 3, 5, 4]
  },
  {
    index: 2,
    name: 'Face 2 (Gable West)',
    normal: [-1, 0, 0],      // Vertikal
    vertices: [0, 2, 4]
  },
  {
    index: 3,
    name: 'Face 3 (Gable East)',
    normal: [1, 0, 0],       // Vertikal
    vertices: [1, 3, 5]
  }
]
```

---

## 📐 Orientierung & Neigung berechnen

### Für vertikale Flächen (Wände)

```javascript
function calculateWallOrientation(normal, compassOffset) {
  // Projektion auf XY-Ebene (ignoriere Z)
  const projected = [normal[0], normal[1], 0]
  const angle = Math.atan2(projected[1], projected[0]) * 180 / Math.PI
  
  // Kompass-Offset anwenden
  const orientation = (angle + compassOffset + 360) % 360
  
  return {
    orientation: orientation,
    inclination: 90  // Vertikal
  }
}
```

### Für geneigte Flächen (Dächer)

```javascript
function calculateRoofOrientation(normal, compassOffset) {
  // 1. Neigung berechnen (Winkel zur Horizontalen)
  const inclination = Math.acos(normal[2]) * 180 / Math.PI
  
  // 2. Orientierung der Projektion auf XY-Ebene
  const projected = [normal[0], normal[1], 0]
  const length = Math.sqrt(projected[0]**2 + projected[1]**2)
  
  if (length < 0.01) {
    // Flachdach (Normale zeigt fast vertikal)
    return {
      orientation: null,
      inclination: inclination
    }
  }
  
  const angle = Math.atan2(projected[1], projected[0]) * 180 / Math.PI
  const orientation = (angle + compassOffset + 360) % 360
  
  return {
    orientation: orientation,
    inclination: inclination
  }
}
```

**Beispiel:**
```javascript
// Süd-Dachfläche mit Normale [0, -0.6, 0.8]
// Kompass-Offset: 0°

inclination = acos(0.8) * 180/π ≈ 37°
projected = [0, -0.6, 0]
angle = atan2(-0.6, 0) = -90° = 270° (West)
orientation = (270 + 0 + 360) % 360 = 270°

// ❌ FALSCH! Dachfläche zeigt nach Süden, nicht Westen!
```

**Korrektur:** Für Dachflächen Normale **umkehren** (zeigt nach außen):
```javascript
// Dachfläche: Normale zeigt nach oben-außen
// Für Orientierung: Projektion umkehren
const projected = [-normal[0], -normal[1], 0]
angle = atan2(0.6, 0) = 90° (Ost)
orientation = (90 + 0 + 360) % 360 = 90°

// ✅ Besser, aber immer noch nicht perfekt...
```

**Bessere Lösung:** Orientierung aus **Firstrichtung** ableiten:
```javascript
function calculateRoofOrientation(prism, faceIndex) {
  if (faceIndex === 0 || faceIndex === 1) {
    // Dachflächen: Orientierung = senkrecht zur Firstrichtung
    const ridgeDirection = prism.dimensions.ridge_direction
    
    if (ridgeDirection === 'X') {
      // First parallel zu X → Dachflächen zeigen in ±Y
      return faceIndex === 0 ? 180 : 0  // Süd : Nord
    } else {
      // First parallel zu Y → Dachflächen zeigen in ±X
      return faceIndex === 0 ? 90 : 270  // Ost : West
    }
  }
  
  // Giebel: Normale verwenden
  return calculateWallOrientation(normal, compassOffset)
}
```

---

## 🏗️ Neues Schema-Design

### Solid-Definition

```json
{
  "id": "eg_main",
  "type": "BOX",
  "dimensions": {
    "length": 10,  // X-Achse
    "width": 8,    // Y-Achse
    "height": 2.5  // Z-Achse
  },
  "origin": [0, 0, 0],
  "rotation": 0  // Rotation um Z-Achse (optional)
}
```

### Face-Referenz in Envelope

```json
{
  "envelope": {
    "walls_external": [
      {
        "id": "wall_sued",
        "name": "Außenwand Süd",
        "solid_ref": "eg_main",
        "face_index": 0,
        "u_value_undisturbed": 1.4
        // KEINE orientation hier! Wird berechnet.
      }
    ],
    "roofs": [
      {
        "id": "roof_sued",
        "name": "Dachfläche Süd",
        "solid_ref": "roof_main",
        "face_index": 0,
        "u_value_undisturbed": 0.35
        // KEINE inclination hier! Wird berechnet.
      }
    ]
  }
}
```

### Berechnete Properties (zur Laufzeit)

```typescript
interface EnvelopeElement {
  // Aus JSON
  id: string
  name: string
  solid_ref: string
  face_index: number
  u_value_undisturbed: number
  
  // Berechnet (nicht in JSON)
  area: number           // Aus Geometrie
  orientation: number    // Aus Normale + Kompass
  inclination: number    // Aus Normale
  vertices: Vector3[]    // Aus Solid-Geometrie
  normal: Vector3        // Aus Solid-Geometrie
}
```

---

## 🎨 Implementierung

### 1. Solid-Geometrie generieren

```typescript
class SolidGeometry {
  static generateBox(dimensions: BoxDimensions) {
    const { length, width, height } = dimensions
    
    const vertices = [
      // Face 0 (-Y)
      [-length/2, -width/2, 0], [length/2, -width/2, 0],
      [length/2, -width/2, height], [-length/2, -width/2, height],
      // ... weitere Faces
    ]
    
    const faces = [
      {
        index: 0,
        normal: [0, -1, 0],
        vertices: [0, 1, 2, 3]
      },
      // ... weitere Faces
    ]
    
    return { vertices, faces }
  }
}
```

### 2. Orientierung berechnen

```typescript
class FaceUtils {
  static calculateOrientation(
    face: Face,
    solid: Solid,
    compassOffset: number
  ): { orientation: number, inclination: number } {
    
    // Normale mit Solid-Rotation transformieren
    const rotatedNormal = this.rotateVector(
      face.normal,
      solid.rotation || 0
    )
    
    // Neigung berechnen
    const inclination = Math.acos(rotatedNormal[2]) * 180 / Math.PI
    
    // Orientierung berechnen
    if (inclination > 80) {
      // Vertikale Fläche (Wand)
      return this.calculateWallOrientation(rotatedNormal, compassOffset)
    } else {
      // Geneigte Fläche (Dach)
      return this.calculateRoofOrientation(rotatedNormal, compassOffset, solid)
    }
  }
}
```

### 3. Envelope enrichern

```typescript
function enrichEnvelope(
  envelope: any,
  solids: Solid[],
  compassOffset: number
): EnvelopeElement[] {
  
  const elements: EnvelopeElement[] = []
  
  for (const wall of envelope.walls_external) {
    const solid = solids.find(s => s.id === wall.solid_ref)
    const geometry = SolidGeometry.generate(solid)
    const face = geometry.faces[wall.face_index]
    
    const { orientation, inclination } = FaceUtils.calculateOrientation(
      face,
      solid,
      compassOffset
    )
    
    elements.push({
      ...wall,
      area: FaceUtils.calculateArea(face),
      orientation,
      inclination,
      vertices: face.vertices,
      normal: face.normal
    })
  }
  
  return elements
}
```

---

## ✅ Vorteile des neuen Ansatzes

1. **Flexibel:** Funktioniert für gedrehte Gebäude
2. **Korrekt:** Orientierung wird geometrisch berechnet
3. **Sauber:** Keine Himmelsrichtung in Geometrie-Definition
4. **Realistisch:** Neigung wird korrekt berechnet
5. **Kompatibel:** Globaler Kompass wie in BIM-Software

---

## 📝 TODO

- [ ] Schema v2.1 um `meta.compass` erweitern
- [ ] Face-Definitionen ohne Orientierung
- [ ] `FaceUtils.calculateOrientation()` implementieren
- [ ] Demo-JSON mit `compass.north_offset` testen
- [ ] Dokumentation aktualisieren

---

**Status:** 🚧 Konzept überarbeitet  
**Nächster Schritt:** Schema v2.1 anpassen
