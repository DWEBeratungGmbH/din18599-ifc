# Solid Parameters - Minimal vs. Optional

**Version:** 2.1  
**Datum:** 01.04.2026  
**Prinzip:** Nur nötige Parameter definieren, Rest berechnen

---

## 🎯 Philosophie

**Minimalismus:**
- Nur die **minimal nötigen** Parameter im JSON
- Alle ableitbaren Werte werden **berechnet**
- Optionale Parameter für **Sonderfälle**

**Vorteile:**
- Einfacher zu schreiben
- Weniger Fehlerquellen
- Konsistente Daten

---

## 📐 Parameter-Definitionen

### 1. BOX (Quader)

**Einfachster Fall:**
```json
{
  "type": "BOX",
  "dimensions": {
    "length": 10,    // REQUIRED: X-Achse
    "width": 8,      // REQUIRED: Y-Achse
    "height": 2.5    // REQUIRED: Z-Achse
  }
}
```

**Optionale Parameter:**
```typescript
{
  // KEINE - Box ist immer symmetrisch
}
```

**Berechnete Werte:**
- Volumen: `length × width × height`
- Fläche jeder Seite: automatisch
- Vertices: automatisch aus Dimensionen

---

### 2. TRIANGULAR_PRISM (Satteldach)

**Variante A: Symmetrisch (Standard)**
```json
{
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,    // REQUIRED: X-Achse (Dachlänge)
    "width": 8,      // REQUIRED: Y-Achse (Basis)
    "height": 3      // REQUIRED: Z-Achse (Firsthöhe)
  }
}
```

**Berechnete Werte (symmetrisch):**
- Ridge Position: `width / 2` (mittig)
- Neigung: `atan2(height, width/2) * 180/π`
- Ridge Direction: `'X'` (Default)

**Variante B: Mit Neigung**
```json
{
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "slope": 45      // OPTIONAL: Neigung in Grad
  }
}
```

**Berechnung:**
- `height = tan(slope) × (width / 2)`
- Beispiel: `slope=45°, width=8 → height = tan(45°) × 4 = 4m`

**Variante C: Unsymmetrisch**
```json
{
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 3,
    "ridge_offset": 2  // OPTIONAL: Verschiebung des Firsts (von Mitte)
  }
}
```

**Berechnung:**
- Ridge Position: `(width / 2) + ridge_offset`
- Süd-Neigung: `atan2(height, (width/2) - ridge_offset)`
- Nord-Neigung: `atan2(height, (width/2) + ridge_offset)`

**Beispiel unsymmetrisch:**
```javascript
width = 8, height = 3, ridge_offset = 2
ridge_position = 4 + 2 = 6m (von Süd-Kante)

süd_breite = 6m → süd_neigung = atan2(3, 6) ≈ 27°
nord_breite = 2m → nord_neigung = atan2(3, 2) ≈ 56°
```

**Optionale Parameter:**
```typescript
{
  ridge_direction?: 'X' | 'Y'  // Default: 'X'
  ridge_offset?: number        // Default: 0 (symmetrisch)
  slope?: number               // Alternative zu height (Grad)
}
```

**Priorität:**
1. Wenn `slope` gegeben: `height` berechnen
2. Wenn `height` gegeben: `slope` berechnen
3. Wenn beide: `height` hat Vorrang

---

### 3. FLAT_ROOF (Flachdach)

**Einfachster Fall:**
```json
{
  "type": "FLAT_ROOF",
  "dimensions": {
    "length": 10,       // REQUIRED
    "width": 8          // REQUIRED
  }
}
```

**Berechnete Werte:**
- `thickness`: 0.3m (Default)
- `parapet_height`: 0 (keine Attika)

**Optionale Parameter:**
```typescript
{
  thickness?: number         // Default: 0.3
  parapet_height?: number    // Default: 0 (keine Attika)
}
```

**Mit Attika:**
```json
{
  "type": "FLAT_ROOF",
  "dimensions": {
    "length": 10,
    "width": 8,
    "parapet_height": 0.8  // Attika 80cm
  }
}
```

---

### 4. SHED_ROOF (Pultdach)

**Variante A: Mit Höhen**
```json
{
  "type": "SHED_ROOF",
  "dimensions": {
    "length": 10,         // REQUIRED
    "width": 8,           // REQUIRED
    "height_low": 2.5,    // REQUIRED
    "height_high": 4.5    // REQUIRED
  }
}
```

**Berechnete Werte:**
- `slope`: `atan2(height_high - height_low, width) * 180/π`
- `slope_direction`: `'S'` (Default, Neigung nach Süden)

**Variante B: Mit Neigung**
```json
{
  "type": "SHED_ROOF",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height_low": 2.5,
    "slope": 15           // Neigung in Grad
  }
}
```

**Berechnung:**
- `height_high = height_low + tan(slope) × width`

**Optionale Parameter:**
```typescript
{
  slope?: number                           // Alternative zu height_high
  slope_direction?: 'N' | 'S' | 'E' | 'W' // Default: 'S'
}
```

---

### 5. GABLE_ROOF (Walmdach)

**Einfachster Fall:**
```json
{
  "type": "GABLE_ROOF",
  "dimensions": {
    "length": 12,      // REQUIRED
    "width": 8,        // REQUIRED
    "height": 3        // REQUIRED
  }
}
```

**Berechnete Werte:**
- `hip_length`: `width / 2` (Default, symmetrisch)
- Ridge Length: `length - 2 × hip_length`

**Optionale Parameter:**
```typescript
{
  hip_length?: number      // Default: width / 2
  ridge_direction?: 'X' | 'Y'  // Default: 'X'
}
```

**Mit custom Hip:**
```json
{
  "type": "GABLE_ROOF",
  "dimensions": {
    "length": 12,
    "width": 8,
    "height": 3,
    "hip_length": 3    // Walme 3m lang
  }
}
```

---

### 6. PYRAMID_ROOF (Pyramidendach)

**Einfachster Fall:**
```json
{
  "type": "PYRAMID_ROOF",
  "dimensions": {
    "base_length": 8,   // REQUIRED
    "base_width": 8,    // REQUIRED
    "height": 4         // REQUIRED
  }
}
```

**Berechnete Werte:**
- Spitze Position: `[base_length/2, base_width/2, height]`
- Neigung: `atan2(height, base_length/2) * 180/π`

**Optionale Parameter:**
```typescript
{
  slope?: number  // Alternative zu height
}
```

---

### 7. L_SHAPE (L-Gebäude)

**Einfachster Fall:**
```json
{
  "type": "L_SHAPE",
  "dimensions": {
    "main_length": 12,    // REQUIRED: Hauptteil X
    "main_width": 8,      // REQUIRED: Hauptteil Y
    "wing_length": 6,     // REQUIRED: Flügel X
    "wing_width": 4,      // REQUIRED: Flügel Y
    "height": 2.5         // REQUIRED
  }
}
```

**Berechnete Werte:**
- `wing_position`: `'NE'` (Default, Nordost)

**Optionale Parameter:**
```typescript
{
  wing_position?: 'NE' | 'NW' | 'SE' | 'SW'  // Default: 'NE'
}
```

---

### 8. CYLINDER (Zylinder)

**Einfachster Fall:**
```json
{
  "type": "CYLINDER",
  "dimensions": {
    "radius": 2,      // REQUIRED
    "height": 8       // REQUIRED
  }
}
```

**Berechnete Werte:**
- `segments`: 32 (Default, für runde Darstellung)

**Optionale Parameter:**
```typescript
{
  segments?: number  // Default: 32 (min: 8, max: 64)
}
```

---

## 📊 Parameter-Übersicht

| Solid | Required | Optional | Berechnete |
|-------|----------|----------|------------|
| **BOX** | length, width, height | - | Volumen, Flächen |
| **TRIANGULAR_PRISM** | length, width, height | ridge_direction, ridge_offset, slope | Neigung, Ridge Position |
| **FLAT_ROOF** | length, width | thickness, parapet_height | - |
| **SHED_ROOF** | length, width, height_low, height_high | slope, slope_direction | Neigung |
| **GABLE_ROOF** | length, width, height | hip_length, ridge_direction | Ridge Length |
| **PYRAMID_ROOF** | base_length, base_width, height | slope | Spitze, Neigung |
| **L_SHAPE** | main_length, main_width, wing_length, wing_width, height | wing_position | - |
| **CYLINDER** | radius, height | segments | - |

---

## 🎨 Beispiele

### Symmetrisches Satteldach
```json
{
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "height": 3
  }
}
```
→ Neigung: 37°, Ridge mittig

### Satteldach mit Neigung
```json
{
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10,
    "width": 8,
    "slope": 45
  }
}
```
→ Height: 4m (berechnet), Neigung: 45°

### Unsymmetrisches Satteldach
```json
{
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

## 🔧 Validierungs-Regeln

### TRIANGULAR_PRISM
```typescript
// Wenn slope gegeben, height berechnen
if (dimensions.slope && !dimensions.height) {
  dimensions.height = Math.tan(dimensions.slope * Math.PI / 180) * (dimensions.width / 2)
}

// Wenn beide gegeben, height hat Vorrang
if (dimensions.slope && dimensions.height) {
  console.warn('Both slope and height provided, using height')
}

// Ridge offset validieren
if (dimensions.ridge_offset) {
  const maxOffset = dimensions.width / 2
  if (Math.abs(dimensions.ridge_offset) > maxOffset) {
    throw new Error('ridge_offset exceeds width/2')
  }
}
```

### CYLINDER
```typescript
// Segments begrenzen
dimensions.segments = Math.max(8, Math.min(64, dimensions.segments || 32))
```

---

## ✅ Nächste Schritte

1. ✅ Parameter-Definitionen festgelegt
2. ⏳ JSON Schema mit required/optional
3. ⏳ TypeScript Types mit Defaults
4. ⏳ Validation Functions
5. ⏳ Calculation Functions

---

**Status:** ✅ Parameter-Definitionen komplett  
**Nächster Schritt:** JSON Schema erstellen
