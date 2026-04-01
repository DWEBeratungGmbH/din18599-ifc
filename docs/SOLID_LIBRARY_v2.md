# Solid Geometry Library v2 - Finale Körper-Bibliothek

**Version:** 2.1  
**Datum:** 01.04.2026  
**Status:** ✅ Finalisiert

---

## 🎯 Übersicht

**4 Körper-Typen für Gebäudemodellierung:**

1. **BOX** - Quader (Geschosse, Räume)
2. **TRIANGULAR_PRISM** - Satteldach (symmetrisch/unsymmetrisch)
3. **TRAPEZOIDAL_PRISM** - Pultdach (Trapezprisma)
4. **PYRAMID_ROOF** - Pyramidendach (Sonderform Walmdach)

**Nicht enthalten:**
- ❌ FLAT_ROOF - Kein Körper, nur Decke (Teil von BOX)
- ❌ L_SHAPE - Besser als 2 BOX-Solids
- ❌ CYLINDER - Zu selten benötigt
- ❌ GABLE_ROOF - Wird als PYRAMID_ROOF modelliert

---

## 📐 1. BOX (Quader)

**Verwendung:** Geschosse, Räume, rechteckige Gebäudeteile

### Parameter

**Required:**
```typescript
{
  type: 'BOX'
  dimensions: {
    length: number   // X-Achse (Ost-West)
    width: number    // Y-Achse (Nord-Süd)
    height: number   // Z-Achse (Vertikal)
  }
}
```

**Optional:** Keine

### Faces

**6 Flächen:**
- Face 0: Süd (-Y, normal: `[0, -1, 0]`)
- Face 1: Ost (+X, normal: `[1, 0, 0]`)
- Face 2: Nord (+Y, normal: `[0, 1, 0]`)
- Face 3: West (-X, normal: `[-1, 0, 0]`)
- Face 4: Oben (+Z, normal: `[0, 0, 1]`)
- Face 5: Unten (-Z, normal: `[0, 0, -1]`)

### Vertices

**8 Ecken:**
```
V0: [0, 0, 0]              V3: [0, width, 0]
V1: [length, 0, 0]         V2: [length, width, 0]

V4: [0, 0, height]         V7: [0, width, height]
V5: [length, 0, height]    V6: [length, width, height]
```

### Beispiel

```json
{
  "id": "eg_main",
  "type": "BOX",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 2.5
  }
}
```

---

## 📐 2. TRIANGULAR_PRISM (Satteldach)

**Verwendung:** Satteldächer, Giebeldächer (symmetrisch/unsymmetrisch)

### Parameter

**Variante A: Symmetrisch (Standard)**
```typescript
{
  type: 'TRIANGULAR_PRISM'
  dimensions: {
    length: number         // REQUIRED: X-Achse (Dachlänge)
    width: number          // REQUIRED: Y-Achse (Basis)
    height: number         // REQUIRED: Z-Achse (Firsthöhe)
  }
}
```

**Variante B: Mit Neigung**
```typescript
{
  type: 'TRIANGULAR_PRISM'
  dimensions: {
    length: number         // REQUIRED
    width: number          // REQUIRED
    slope: number          // REQUIRED: Neigung in Grad (statt height)
  }
}
```

**Berechnung:** `height = tan(slope) × (width / 2)`

**Variante C: Unsymmetrisch**
```typescript
{
  type: 'TRIANGULAR_PRISM'
  dimensions: {
    length: number         // REQUIRED
    width: number          // REQUIRED
    height: number         // REQUIRED
    ridge_offset: number   // OPTIONAL: Verschiebung des Firsts
  }
}
```

**Berechnung:**
- Ridge Position: `(width / 2) + ridge_offset`
- Süd-Neigung: `atan2(height, (width/2) - ridge_offset)`
- Nord-Neigung: `atan2(height, (width/2) + ridge_offset)`

### Optional

```typescript
{
  ridge_direction?: 'X' | 'Y'  // Default: 'X'
  ridge_offset?: number        // Default: 0 (symmetrisch)
  slope?: number               // Alternative zu height
}
```

### Faces (ridge_direction='X')

**4 Flächen:**
- Face 0: Süd-Dachfläche (-Y Seite, schräg)
- Face 1: Nord-Dachfläche (+Y Seite, schräg)
- Face 2: West-Giebel (-X Seite, Dreieck)
- Face 3: Ost-Giebel (+X Seite, Dreieck)

### Vertices (ridge_direction='X', symmetrisch)

**6 Ecken:**
```
V0: [0, 0, 0]                    V3: [0, width, 0]
V1: [length, 0, 0]               V2: [length, width, 0]

V4: [0, width/2, height]         V5: [length, width/2, height]  (First)
```

### Beispiele

**Symmetrisch:**
```json
{
  "id": "roof_satteldach",
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 3
  }
}
```
→ Neigung: 37°, First mittig

**Mit Neigung:**
```json
{
  "id": "roof_45grad",
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "slope": 45
  }
}
```
→ Height: 4m (berechnet)

**Unsymmetrisch:**
```json
{
  "id": "roof_unsym",
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 3,
    "ridge_offset": 2
  }
}
```
→ Süd: 27°, Nord: 56°

---

## 📐 3. TRAPEZOIDAL_PRISM (Pultdach / Trapezprisma)

**Verwendung:** Pultdächer (eine geneigte Fläche)

### Parameter

**Variante A: Mit Höhen**
```typescript
{
  type: 'TRAPEZOIDAL_PRISM'
  dimensions: {
    length: number         // REQUIRED: X-Achse
    width: number          // REQUIRED: Y-Achse
    height_low: number     // REQUIRED: Niedrige Seite
    height_high: number    // REQUIRED: Hohe Seite
  }
}
```

**Variante B: Mit Neigung**
```typescript
{
  type: 'TRAPEZOIDAL_PRISM'
  dimensions: {
    length: number         // REQUIRED
    width: number          // REQUIRED
    height_low: number     // REQUIRED
    slope: number          // REQUIRED: Neigung in Grad
  }
}
```

**Berechnung:** `height_high = height_low + tan(slope) × width`

### Optional

```typescript
{
  slope?: number                           // Alternative zu height_high
  slope_direction?: 'N' | 'S' | 'E' | 'W' // Default: 'S' (Neigung nach Süden)
}
```

### Faces (slope_direction='S')

**5 Flächen:**
- Face 0: Dachfläche (schräg, Trapez)
- Face 1: Süd-Seite (niedrig, Rechteck)
- Face 2: Nord-Seite (hoch, Rechteck)
- Face 3: West-Giebel (Trapez)
- Face 4: Ost-Giebel (Trapez)

### Vertices (slope_direction='S')

**8 Ecken:**
```
V0: [0, 0, height_low]           V3: [0, width, height_high]
V1: [length, 0, height_low]      V2: [length, width, height_high]

V4: [0, 0, 0]                    V7: [0, width, 0]
V5: [length, 0, 0]               V6: [length, width, 0]
```

### Beispiele

**Mit Höhen:**
```json
{
  "id": "roof_pult",
  "type": "TRAPEZOIDAL_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height_low": 2.5,
    "height_high": 4.5
  }
}
```
→ Neigung: 14°

**Mit Neigung:**
```json
{
  "id": "roof_pult_15grad",
  "type": "TRAPEZOIDAL_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height_low": 2.5,
    "slope": 15
  }
}
```
→ height_high: 4.64m (berechnet)

---

## 📐 4. PYRAMID_ROOF (Pyramidendach)

**Verwendung:** Pyramidendächer, Walmdächer (4 Dachflächen)

### Parameter

**Einfachster Fall:**
```typescript
{
  type: 'PYRAMID_ROOF'
  dimensions: {
    base_length: number    // REQUIRED: Basis X
    base_width: number     // REQUIRED: Basis Y
    height: number         // REQUIRED: Spitzenhöhe
  }
}
```

**Mit Neigung:**
```typescript
{
  type: 'PYRAMID_ROOF'
  dimensions: {
    base_length: number    // REQUIRED
    base_width: number     // REQUIRED
    slope: number          // REQUIRED: Neigung in Grad
  }
}
```

**Berechnung:** `height = tan(slope) × min(base_length, base_width) / 2`

### Optional

```typescript
{
  slope?: number           // Alternative zu height
  apex_offset?: [number, number]  // Verschiebung der Spitze [X, Y]
}
```

**Apex Offset:**
- Default: `[base_length/2, base_width/2]` (mittig)
- Für Walmdach: `apex_offset: [0, 0]` (First statt Spitze)

### Faces

**4 Flächen (Pyramide):**
- Face 0: Süd-Dachfläche (Dreieck)
- Face 1: Ost-Dachfläche (Dreieck)
- Face 2: Nord-Dachfläche (Dreieck)
- Face 3: West-Dachfläche (Dreieck)

**4 Flächen (Walmdach mit apex_offset):**
- Face 0: Süd-Dachfläche (Trapez)
- Face 1: Ost-Walm (Dreieck)
- Face 2: Nord-Dachfläche (Trapez)
- Face 3: West-Walm (Dreieck)

### Vertices (Pyramide)

**5 Ecken:**
```
V0: [0, 0, 0]                           V3: [0, base_width, 0]
V1: [base_length, 0, 0]                 V2: [base_length, base_width, 0]

V4: [base_length/2, base_width/2, height]  (Spitze)
```

### Beispiele

**Pyramide:**
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
→ 4 gleiche Dachflächen, Neigung: 45°

**Walmdach:**
```json
{
  "id": "roof_walm",
  "type": "PYRAMID_ROOF",
  "dimensions": {
    "base_length": 12,
    "base_width": 8,
    "height": 3,
    "apex_offset": [3, 0]
  }
}
```
→ First von X=3 bis X=9, 2 Walme an den Enden

---

## 📊 Parameter-Übersicht

| Solid | Required | Optional | Berechnete |
|-------|----------|----------|------------|
| **BOX** | length, width, height | - | Volumen, Flächen |
| **TRIANGULAR_PRISM** | length, width, height OR slope | ridge_direction, ridge_offset | Neigung, Ridge Position |
| **TRAPEZOIDAL_PRISM** | length, width, height_low, height_high OR slope | slope_direction | Neigung |
| **PYRAMID_ROOF** | base_length, base_width, height OR slope | apex_offset | Spitze, Neigung |

---

## 🎨 Vollständige Beispiele

### Einfamilienhaus (EG + Satteldach)

```json
{
  "solids": [
    {
      "id": "eg",
      "type": "BOX",
      "dimensions": {
        "length": 10,
        "width": 8,
        "height": 2.5
      },
      "origin": [0, 0, 0]
    },
    {
      "id": "roof",
      "type": "TRIANGULAR_PRISM",
      "dimensions": {
        "length": 10,
        "width": 8,
        "height": 3
      },
      "parent_ref": "eg",
      "offset": [0, 0, 2.5]
    }
  ]
}
```

### Mehrfamilienhaus (3 Geschosse + Pultdach)

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
      "type": "TRAPEZOIDAL_PRISM",
      "dimensions": {
        "length": 20,
        "width": 12,
        "height_low": 0,
        "slope": 15
      },
      "parent_ref": "og2",
      "offset": [0, 0, 2.8]
    }
  ]
}
```

### L-förmiges Gebäude (2 BOX-Solids)

```json
{
  "solids": [
    {
      "id": "main",
      "type": "BOX",
      "dimensions": {"length": 15, "width": 10, "height": 2.5}
    },
    {
      "id": "wing",
      "type": "BOX",
      "dimensions": {"length": 8, "width": 6, "height": 2.5},
      "parent_ref": "main",
      "offset": [15, 0, 0]
    }
  ]
}
```

---

## 🔧 Validierungs-Regeln

### TRIANGULAR_PRISM
```typescript
// Wenn slope gegeben, height berechnen
if (dimensions.slope && !dimensions.height) {
  dimensions.height = Math.tan(dimensions.slope * Math.PI / 180) * (dimensions.width / 2)
}

// Ridge offset validieren
if (dimensions.ridge_offset) {
  const maxOffset = dimensions.width / 2
  if (Math.abs(dimensions.ridge_offset) > maxOffset) {
    throw new Error('ridge_offset exceeds width/2')
  }
}
```

### TRAPEZOIDAL_PRISM
```typescript
// Wenn slope gegeben, height_high berechnen
if (dimensions.slope && !dimensions.height_high) {
  dimensions.height_high = dimensions.height_low + 
    Math.tan(dimensions.slope * Math.PI / 180) * dimensions.width
}

// height_high muss größer als height_low sein
if (dimensions.height_high <= dimensions.height_low) {
  throw new Error('height_high must be greater than height_low')
}
```

### PYRAMID_ROOF
```typescript
// Wenn slope gegeben, height berechnen
if (dimensions.slope && !dimensions.height) {
  const minDim = Math.min(dimensions.base_length, dimensions.base_width)
  dimensions.height = Math.tan(dimensions.slope * Math.PI / 180) * (minDim / 2)
}

// Apex offset validieren
if (dimensions.apex_offset) {
  if (dimensions.apex_offset[0] < 0 || dimensions.apex_offset[0] > dimensions.base_length) {
    throw new Error('apex_offset X out of bounds')
  }
  if (dimensions.apex_offset[1] < 0 || dimensions.apex_offset[1] > dimensions.base_width) {
    throw new Error('apex_offset Y out of bounds')
  }
}
```

---

## ✅ Implementation-Priorität

| Phase | Solid | Grund |
|-------|-------|-------|
| **MVP** | BOX | Basis für alle Gebäude |
| **MVP** | TRIANGULAR_PRISM | Häufigstes Dach |
| **v2.2** | TRAPEZOIDAL_PRISM | Pultdächer häufig |
| **v2.3** | PYRAMID_ROOF | Walmdächer seltener |

---

**Status:** ✅ Finalisiert (4 Körper-Typen)  
**Nächster Schritt:** JSON Schema erstellen
