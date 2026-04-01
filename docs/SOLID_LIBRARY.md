# Solid Geometry Library - Körper-Bibliothek für Gebäude

**Version:** 2.1  
**Datum:** 01.04.2026  
**Status:** Definition Phase

---

## 🎯 Übersicht

Diese Bibliothek definiert alle geometrischen Körper (Solids) für die Gebäudemodellierung.

**Prinzip:** Bauklötze-System mit parametrischen Körpern

---

## 📚 Körper-Typen

### 1. BOX (Quader)

**Verwendung:** Geschosse, Räume, rechteckige Gebäudeteile

**Parameter:**
```typescript
{
  type: 'BOX'
  dimensions: {
    length: number   // X-Achse (Ost-West im Plannorden)
    width: number    // Y-Achse (Nord-Süd im Plannorden)
    height: number   // Z-Achse (Vertikal)
  }
}
```

**Faces:** 6 Flächen
- Face 0: Süd (-Y, normal: [0, -1, 0])
- Face 1: Ost (+X, normal: [1, 0, 0])
- Face 2: Nord (+Y, normal: [0, 1, 0])
- Face 3: West (-X, normal: [-1, 0, 0])
- Face 4: Oben (+Z, normal: [0, 0, 1])
- Face 5: Unten (-Z, normal: [0, 0, -1])

**Vertices:** 8 Ecken
```
V0: [0, 0, 0]              V3: [0, width, 0]
V1: [length, 0, 0]         V2: [length, width, 0]

V4: [0, 0, height]         V7: [0, width, height]
V5: [length, 0, height]    V6: [length, width, height]
```

**Beispiel:**
```json
{
  "id": "eg_main",
  "type": "BOX",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 2.5
  },
  "origin": [0, 0, 0]
}
```

---

### 2. TRIANGULAR_PRISM (Dreiecksprisma / Satteldach)

**Verwendung:** Satteldächer, Giebeldächer

**Parameter:**
```typescript
{
  type: 'TRIANGULAR_PRISM'
  dimensions: {
    length: number         // X-Achse (Länge des Daches)
    width: number          // Y-Achse (Basis des Dreiecks)
    height: number         // Z-Achse (Firsthöhe)
    ridge_direction: 'X' | 'Y'  // Firstrichtung
  }
}
```

**Ridge Direction:**
- `'X'`: First parallel zu X-Achse → Dachflächen zeigen in ±Y
- `'Y'`: First parallel zu Y-Achse → Dachflächen zeigen in ±X

**Faces (ridge_direction='X'):** 4 Flächen
- Face 0: Süd-Dachfläche (-Y Seite, schräg)
- Face 1: Nord-Dachfläche (+Y Seite, schräg)
- Face 2: West-Giebel (-X Seite, Dreieck)
- Face 3: Ost-Giebel (+X Seite, Dreieck)

**Vertices (ridge_direction='X'):** 6 Ecken
```
V0: [0, 0, 0]                    V3: [0, width, 0]
V1: [length, 0, 0]               V2: [length, width, 0]

V4: [0, width/2, height]         V5: [length, width/2, height]  (First)
```

**Neigung berechnen:**
```javascript
const roofSlope = Math.atan2(height, width/2) * 180 / Math.PI
// Beispiel: height=3, width=8 → slope ≈ 37°
```

**Beispiel:**
```json
{
  "id": "roof_main",
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 3,
    "ridge_direction": "X"
  },
  "parent_ref": "eg_main",
  "offset": [0, 0, 2.5]
}
```

---

### 3. GABLE_ROOF (Walmdach)

**Verwendung:** Walmdächer (4 Dachflächen)

**Parameter:**
```typescript
{
  type: 'GABLE_ROOF'
  dimensions: {
    length: number         // X-Achse
    width: number          // Y-Achse
    height: number         // Z-Achse (Firsthöhe)
    hip_length: number     // Länge der Walme (in X-Richtung)
    ridge_direction: 'X' | 'Y'
  }
}
```

**Faces:** 4 Dachflächen
- Face 0: Süd-Dachfläche (Trapez)
- Face 1: Nord-Dachfläche (Trapez)
- Face 2: West-Walm (Dreieck)
- Face 3: Ost-Walm (Dreieck)

**Vertices:** 8 Ecken
```
V0: [0, 0, 0]                           V3: [0, width, 0]
V1: [length, 0, 0]                      V2: [length, width, 0]

V4: [hip_length, width/2, height]       V5: [length-hip_length, width/2, height]  (First)
V6: [length/2, 0, height]               V7: [length/2, width, height]
```

**Beispiel:**
```json
{
  "id": "roof_walm",
  "type": "GABLE_ROOF",
  "dimensions": {
    "length": 12,
    "width": 8,
    "height": 3,
    "hip_length": 2,
    "ridge_direction": "X"
  }
}
```

---

### 4. FLAT_ROOF (Flachdach)

**Verwendung:** Flachdächer, Attika

**Parameter:**
```typescript
{
  type: 'FLAT_ROOF'
  dimensions: {
    length: number         // X-Achse
    width: number          // Y-Achse
    thickness: number      // Dicke der Dachkonstruktion
    parapet_height: number // Attika-Höhe (optional)
  }
}
```

**Faces:** 1-5 Flächen
- Face 0: Dachfläche (oben)
- Face 1-4: Attika (optional, falls parapet_height > 0)

**Beispiel:**
```json
{
  "id": "roof_flat",
  "type": "FLAT_ROOF",
  "dimensions": {
    "length": 10,
    "width": 8,
    "thickness": 0.3,
    "parapet_height": 0.5
  }
}
```

---

### 5. L_SHAPE (L-förmiger Grundriss)

**Verwendung:** L-förmige Gebäude, Anbauten

**Parameter:**
```typescript
{
  type: 'L_SHAPE'
  dimensions: {
    main_length: number    // Hauptteil X
    main_width: number     // Hauptteil Y
    wing_length: number    // Flügel X
    wing_width: number     // Flügel Y
    height: number         // Z-Achse
    wing_position: 'NE' | 'NW' | 'SE' | 'SW'  // Position des Flügels
  }
}
```

**Wing Position:**
- `'NE'`: Nordost (rechts oben)
- `'NW'`: Nordwest (links oben)
- `'SE'`: Südost (rechts unten)
- `'SW'`: Südwest (links unten)

**Faces:** 10 Außenflächen + 1 Oben + 1 Unten

**Beispiel:**
```json
{
  "id": "eg_l_shape",
  "type": "L_SHAPE",
  "dimensions": {
    "main_length": 12,
    "main_width": 8,
    "wing_length": 6,
    "wing_width": 4,
    "height": 2.5,
    "wing_position": "NE"
  }
}
```

---

### 6. CYLINDER (Zylinder)

**Verwendung:** Runde Türme, Silos, Schornsteine

**Parameter:**
```typescript
{
  type: 'CYLINDER'
  dimensions: {
    radius: number         // Radius
    height: number         // Höhe
    segments: number       // Anzahl Segmente (Default: 32)
  }
}
```

**Faces:** segments + 2
- Face 0: Oben (Kreis)
- Face 1: Unten (Kreis)
- Face 2-N: Mantel (segments Flächen)

**Beispiel:**
```json
{
  "id": "tower",
  "type": "CYLINDER",
  "dimensions": {
    "radius": 2,
    "height": 8,
    "segments": 16
  }
}
```

---

### 7. PYRAMID_ROOF (Pyramidendach)

**Verwendung:** Pyramidendächer (4 gleiche Dachflächen)

**Parameter:**
```typescript
{
  type: 'PYRAMID_ROOF'
  dimensions: {
    base_length: number    // Basis X
    base_width: number     // Basis Y
    height: number         // Spitzenhöhe
  }
}
```

**Faces:** 4 Dreiecke
- Face 0-3: Dachflächen (Süd, Ost, Nord, West)

**Vertices:** 5 Ecken
```
V0: [0, 0, 0]                           V3: [0, base_width, 0]
V1: [base_length, 0, 0]                 V2: [base_length, base_width, 0]

V4: [base_length/2, base_width/2, height]  (Spitze)
```

**Beispiel:**
```json
{
  "id": "roof_pyramid",
  "type": "PYRAMID_ROOF",
  "dimensions": {
    "base_length": 8,
    "base_width": 8,
    "height": 4
  }
}
```

---

### 8. SHED_ROOF (Pultdach)

**Verwendung:** Pultdächer (eine geneigte Fläche)

**Parameter:**
```typescript
{
  type: 'SHED_ROOF'
  dimensions: {
    length: number         // X-Achse
    width: number          // Y-Achse
    height_low: number     // Niedrige Seite
    height_high: number    // Hohe Seite
    slope_direction: 'N' | 'S' | 'E' | 'W'  // Richtung der Neigung
  }
}
```

**Slope Direction:**
- `'N'`: Neigung nach Norden (hoch im Süden)
- `'S'`: Neigung nach Süden (hoch im Norden)
- `'E'`: Neigung nach Osten (hoch im Westen)
- `'W'`: Neigung nach Westen (hoch im Osten)

**Faces:** 5 Flächen
- Face 0: Dachfläche (schräg)
- Face 1-4: Seitenwände

**Beispiel:**
```json
{
  "id": "roof_shed",
  "type": "SHED_ROOF",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height_low": 2.5,
    "height_high": 4.5,
    "slope_direction": "S"
  }
}
```

---

## 🔗 Gemeinsame Parameter

Alle Solids haben folgende gemeinsame Properties:

```typescript
interface SolidBase {
  id: string                          // Eindeutige ID
  type: SolidType                     // Körper-Typ
  dimensions: SolidDimensions         // Typ-spezifische Dimensionen
  origin?: [number, number, number]   // Ursprung (Default: [0,0,0])
  parent_ref?: string                 // Parent-Solid ID
  offset?: [number, number, number]   // Offset zum Parent (Default: [0,0,0])
  rotation?: number                   // Rotation um Z-Achse in Grad (Default: 0)
  description?: string                // Beschreibung
}
```

---

## 📐 Face-Definitionen

Jeder Solid-Typ hat vordefinierte Faces mit:

```typescript
interface Face {
  index: number              // Face-Index (0-basiert)
  normal: [number, number, number]  // Normale (normalisiert)
  vertices: number[]         // Vertex-Indizes
  area?: number              // Fläche (berechnet)
  type?: 'WALL' | 'ROOF' | 'FLOOR' | 'CEILING'
}
```

---

## 🎨 Verwendungs-Beispiele

### Einfamilienhaus (EG + Satteldach)

```json
{
  "solids": [
    {
      "id": "eg",
      "type": "BOX",
      "dimensions": {"length": 10, "width": 8, "height": 2.5},
      "origin": [0, 0, 0]
    },
    {
      "id": "roof",
      "type": "TRIANGULAR_PRISM",
      "dimensions": {
        "length": 10,
        "width": 8,
        "height": 3,
        "ridge_direction": "X"
      },
      "parent_ref": "eg",
      "offset": [0, 0, 2.5]
    }
  ]
}
```

### Mehrfamilienhaus (3 Geschosse + Walmdach)

```json
{
  "solids": [
    {
      "id": "eg",
      "type": "BOX",
      "dimensions": {"length": 20, "width": 12, "height": 3}
    },
    {
      "id": "og1",
      "type": "BOX",
      "dimensions": {"length": 20, "width": 12, "height": 2.8},
      "parent_ref": "eg",
      "offset": [0, 0, 3]
    },
    {
      "id": "og2",
      "type": "BOX",
      "dimensions": {"length": 20, "width": 12, "height": 2.8},
      "parent_ref": "og1",
      "offset": [0, 0, 2.8]
    },
    {
      "id": "roof",
      "type": "GABLE_ROOF",
      "dimensions": {
        "length": 20,
        "width": 12,
        "height": 4,
        "hip_length": 3,
        "ridge_direction": "X"
      },
      "parent_ref": "og2",
      "offset": [0, 0, 2.8]
    }
  ]
}
```

### L-förmiges Gebäude

```json
{
  "solids": [
    {
      "id": "eg",
      "type": "L_SHAPE",
      "dimensions": {
        "main_length": 15,
        "main_width": 10,
        "wing_length": 8,
        "wing_width": 6,
        "height": 2.5,
        "wing_position": "NE"
      }
    },
    {
      "id": "roof",
      "type": "FLAT_ROOF",
      "dimensions": {
        "length": 15,
        "width": 10,
        "thickness": 0.3,
        "parapet_height": 0.8
      },
      "parent_ref": "eg",
      "offset": [0, 0, 2.5]
    }
  ]
}
```

---

## 📊 Priorität für Implementation

| Priorität | Solid-Typ | Verwendung | Komplexität |
|-----------|-----------|------------|-------------|
| **P0** | BOX | Geschosse, Räume | Niedrig |
| **P0** | TRIANGULAR_PRISM | Satteldach | Mittel |
| **P1** | FLAT_ROOF | Flachdach | Niedrig |
| **P1** | SHED_ROOF | Pultdach | Mittel |
| **P2** | GABLE_ROOF | Walmdach | Hoch |
| **P2** | PYRAMID_ROOF | Pyramidendach | Mittel |
| **P2** | L_SHAPE | L-Gebäude | Hoch |
| **P3** | CYLINDER | Türme | Mittel |

**Für MVP (Berlin-Demo):** P0 reicht (BOX + TRIANGULAR_PRISM)

---

## ✅ Nächste Schritte

1. ✅ Körper-Typen definiert
2. ⏳ JSON Schema erstellen
3. ⏳ TypeScript Types generieren
4. ⏳ Geometry Generators implementieren
5. ⏳ Face-Mapping implementieren

---

**Status:** ✅ Körper-Bibliothek definiert  
**Nächster Schritt:** JSON Schema erstellen
