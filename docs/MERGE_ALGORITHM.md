# Delta-Merge-Algorithmus - Formale Spezifikation

**Version:** 1.0  
**Stand:** 31. März 2026  
**Status:** Specification

---

## 🎯 Zweck

Dieser Algorithmus definiert **formal und eindeutig**, wie ein Szenario (Base + Delta) gemergt wird.

**Ziel:** Verschiedene Implementierungen (JavaScript, Python, etc.) müssen **identische Ergebnisse** liefern.

---

## 📋 Grundprinzipien

### **1. Base + Delta = Merged**

```
Base Input (Ist-Zustand)
    +
Delta (Änderungen)
    =
Merged (Szenario)
```

### **2. Delta überschreibt Base**

- Wenn ein Feld in Delta vorhanden ist → Delta-Wert wird verwendet
- Wenn ein Feld nur in Base vorhanden ist → Base-Wert wird verwendet
- Wenn ein Feld in keinem vorhanden ist → undefined

### **3. Arrays werden nach ID gemergt**

- Arrays werden **nicht** konkateniert
- Arrays werden **element-weise** gemergt
- Merge-Key: `id` (oder `ifc_guid` falls `id` fehlt)

---

## 🔧 Merge-Regeln

### **Regel 1: Primitive Werte (String, Number, Boolean)**

```javascript
// Delta überschreibt Base
merge(base, delta) {
  return delta !== undefined ? delta : base
}
```

**Beispiel:**
```json
Base:  {"construction_year": 1978}
Delta: {"construction_year": 1985}
→ Merged: {"construction_year": 1985}
```

---

### **Regel 2: Objekte (Deep Merge)**

```javascript
merge(base, delta) {
  if (delta === undefined) return base
  if (base === undefined) return delta
  
  const merged = {...base}
  for (const key in delta) {
    merged[key] = merge(base[key], delta[key])
  }
  return merged
}
```

**Beispiel:**
```json
Base: {
  "heating": {
    "generation": {"type": "gas_boiler", "efficiency": 0.85},
    "distribution": {"type": "two_pipe"}
  }
}

Delta: {
  "heating": {
    "generation": {"type": "heat_pump", "cop": 3.5}
  }
}

→ Merged: {
  "heating": {
    "generation": {"type": "heat_pump", "cop": 3.5, "efficiency": 0.85},
    "distribution": {"type": "two_pipe"}
  }
}
```

**Wichtig:** `generation.type` wird überschrieben, aber `generation.efficiency` bleibt erhalten!

---

### **Regel 3: Arrays (Element-weise nach ID)**

```javascript
mergeArrays(baseArray, deltaArray) {
  if (deltaArray === undefined) return baseArray
  if (baseArray === undefined) return deltaArray
  
  const merged = [...baseArray]
  
  for (const deltaItem of deltaArray) {
    const id = deltaItem.id || deltaItem.ifc_guid
    if (!id) throw new Error("Delta array item missing id/ifc_guid")
    
    const baseIndex = merged.findIndex(item => 
      (item.id === id) || (item.ifc_guid === id)
    )
    
    if (baseIndex >= 0) {
      // Element existiert in Base → Merge
      merged[baseIndex] = merge(merged[baseIndex], deltaItem)
    } else {
      // Element existiert nicht in Base → Hinzufügen
      merged.push(deltaItem)
    }
  }
  
  return merged
}
```

**Beispiel:**
```json
Base: {
  "walls_external": [
    {"id": "wall_ext_sued", "construction_ref": "WALL_UNINSULATED", "area": 35.2},
    {"id": "wall_ext_nord", "construction_ref": "WALL_UNINSULATED", "area": 28.5}
  ]
}

Delta: {
  "walls_external": [
    {"id": "wall_ext_sued", "construction_ref": "WALL_WDVS_160"}
  ]
}

→ Merged: {
  "walls_external": [
    {"id": "wall_ext_sued", "construction_ref": "WALL_WDVS_160", "area": 35.2},
    {"id": "wall_ext_nord", "construction_ref": "WALL_UNINSULATED", "area": 28.5}
  ]
}
```

**Wichtig:** 
- `wall_ext_sued` wird gemergt (construction_ref überschrieben, area bleibt)
- `wall_ext_nord` bleibt unverändert

---

### **Regel 4: Null-Werte (Explizites Löschen)**

```javascript
merge(base, delta) {
  if (delta === null) return null  // Explizit löschen
  if (delta === undefined) return base
  return delta
}
```

**Beispiel:**
```json
Base:  {"renovation_year": 2010}
Delta: {"renovation_year": null}
→ Merged: {"renovation_year": null}
```

**Verwendung:** Feld explizit auf "nicht vorhanden" setzen

---

## 🔍 Merge-Keys (Priorität)

### **Array-Element-Identifikation:**

1. **Priorität 1:** `id` (String)
2. **Priorität 2:** `ifc_guid` (String, falls `id` fehlt)
3. **Fehler:** Wenn beides fehlt → Exception

**Beispiel:**
```json
// OK: id vorhanden
{"id": "wall_ext_sued", "area": 35.2}

// OK: ifc_guid vorhanden (id fehlt)
{"ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD", "area": 35.2}

// FEHLER: Beides fehlt
{"area": 35.2}  // ❌ Exception!
```

---

## 📐 Vollständiger Algorithmus (Pseudocode)

```javascript
function mergeSidecar(base, scenario) {
  // 1. Base Input kopieren
  const merged = deepClone(base.input)
  
  // 2. Delta anwenden
  const delta = scenario.delta
  
  // 3. Merge durchführen
  return {
    ...base,
    input: merge(merged, delta)
  }
}

function merge(base, delta) {
  // Null-Werte (explizites Löschen)
  if (delta === null) return null
  
  // Delta undefined → Base verwenden
  if (delta === undefined) return base
  
  // Base undefined → Delta verwenden
  if (base === undefined) return delta
  
  // Arrays → Element-weise mergen
  if (Array.isArray(base) && Array.isArray(delta)) {
    return mergeArrays(base, delta)
  }
  
  // Objekte → Deep Merge
  if (typeof base === 'object' && typeof delta === 'object') {
    const merged = {...base}
    for (const key in delta) {
      merged[key] = merge(base[key], delta[key])
    }
    return merged
  }
  
  // Primitive Werte → Delta überschreibt
  return delta
}

function mergeArrays(baseArray, deltaArray) {
  const merged = [...baseArray]
  
  for (const deltaItem of deltaArray) {
    // Merge-Key ermitteln
    const id = deltaItem.id || deltaItem.ifc_guid
    if (!id) {
      throw new Error(`Delta array item missing id/ifc_guid: ${JSON.stringify(deltaItem)}`)
    }
    
    // Element in Base suchen
    const baseIndex = merged.findIndex(item => 
      (item.id === id) || (item.ifc_guid === id)
    )
    
    if (baseIndex >= 0) {
      // Element existiert → Merge
      merged[baseIndex] = merge(merged[baseIndex], deltaItem)
    } else {
      // Element existiert nicht → Hinzufügen
      merged.push(deltaItem)
    }
  }
  
  return merged
}
```

---

## 🧪 Test-Cases

### **Test 1: Einfacher Wert-Override**

```json
Base: {"construction_year": 1978}
Delta: {"construction_year": 1985}
Expected: {"construction_year": 1985}
```

### **Test 2: Objekt Deep Merge**

```json
Base: {
  "heating": {
    "generation": {"type": "gas_boiler", "efficiency": 0.85},
    "distribution": {"type": "two_pipe"}
  }
}
Delta: {
  "heating": {
    "generation": {"type": "heat_pump"}
  }
}
Expected: {
  "heating": {
    "generation": {"type": "heat_pump", "efficiency": 0.85},
    "distribution": {"type": "two_pipe"}
  }
}
```

### **Test 3: Array Element Merge**

```json
Base: {
  "walls_external": [
    {"id": "wall_1", "u_value": 1.2, "area": 35.2},
    {"id": "wall_2", "u_value": 1.2, "area": 28.5}
  ]
}
Delta: {
  "walls_external": [
    {"id": "wall_1", "u_value": 0.21}
  ]
}
Expected: {
  "walls_external": [
    {"id": "wall_1", "u_value": 0.21, "area": 35.2},
    {"id": "wall_2", "u_value": 1.2, "area": 28.5}
  ]
}
```

### **Test 4: Array Element Hinzufügen**

```json
Base: {
  "walls_external": [
    {"id": "wall_1", "u_value": 1.2}
  ]
}
Delta: {
  "walls_external": [
    {"id": "wall_2", "u_value": 0.21}
  ]
}
Expected: {
  "walls_external": [
    {"id": "wall_1", "u_value": 1.2},
    {"id": "wall_2", "u_value": 0.21}
  ]
}
```

### **Test 5: Null-Wert (Explizites Löschen)**

```json
Base: {"renovation_year": 2010}
Delta: {"renovation_year": null}
Expected: {"renovation_year": null}
```

### **Test 6: Nested Array Merge**

```json
Base: {
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {"id": "wall_1", "u_value": 1.2}
      ]
    }
  }
}
Delta: {
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {"id": "wall_1", "u_value": 0.21}
      ]
    }
  }
}
Expected: {
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {"id": "wall_1", "u_value": 0.21}
      ]
    }
  }
}
```

### **Test 7: IFC GUID als Merge-Key**

```json
Base: {
  "walls_external": [
    {"ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD", "u_value": 1.2}
  ]
}
Delta: {
  "walls_external": [
    {"ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD", "u_value": 0.21}
  ]
}
Expected: {
  "walls_external": [
    {"ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD", "u_value": 0.21}
  ]
}
```

### **Test 8: Fehler - Kein Merge-Key**

```json
Base: {
  "walls_external": [
    {"u_value": 1.2}
  ]
}
Delta: {
  "walls_external": [
    {"u_value": 0.21}
  ]
}
Expected: Error("Delta array item missing id/ifc_guid")
```

---

## ⚠️ Edge Cases

### **1. Leere Arrays**

```json
Base: {"walls_external": []}
Delta: {"walls_external": [{"id": "wall_1", "u_value": 0.21}]}
Expected: {"walls_external": [{"id": "wall_1", "u_value": 0.21}]}
```

### **2. Delta löscht Array**

```json
Base: {"walls_external": [{"id": "wall_1"}]}
Delta: {"walls_external": null}
Expected: {"walls_external": null}
```

### **3. Mehrere Deltas auf gleiches Element**

```json
Base: {"walls_external": [{"id": "wall_1", "u_value": 1.2, "area": 35.2}]}
Delta: {"walls_external": [
  {"id": "wall_1", "u_value": 0.21},
  {"id": "wall_1", "area": 40.0}
]}
Expected: {"walls_external": [{"id": "wall_1", "u_value": 0.21, "area": 40.0}]}
```

**Regel:** Letztes Delta-Element gewinnt (Array-Reihenfolge)

---

## 🔒 Invarianten (Garantien)

### **1. Idempotenz**

```
merge(merge(base, delta), delta) === merge(base, delta)
```

Mehrfaches Anwenden des gleichen Deltas ändert nichts.

### **2. Kommutativität (NICHT garantiert)**

```
merge(base, delta1 + delta2) ≠ merge(base, delta2 + delta1)
```

Reihenfolge von Deltas ist wichtig!

### **3. Base bleibt unverändert**

```javascript
const merged = merge(base, delta)
// base ist unverändert (Deep Clone)
```

---

## 🛠️ Implementierungs-Hinweise

### **JavaScript/TypeScript:**

```typescript
import { cloneDeep, mergeWith } from 'lodash'

function mergeSidecar(base: Sidecar, scenario: Scenario): Sidecar {
  const merged = cloneDeep(base)
  merged.input = merge(merged.input, scenario.delta)
  return merged
}
```

### **Python:**

```python
import copy

def merge_sidecar(base: dict, scenario: dict) -> dict:
    merged = copy.deepcopy(base)
    merged['input'] = merge(merged['input'], scenario['delta'])
    return merged
```

### **Performance:**

- Deep Clone kann bei großen Dateien langsam sein
- Alternative: Immutable Data Structures (Immer.js, Immutable.js)
- Für Production: Caching von gemergten Szenarien

---

## 📚 Referenzen

- **JSON Merge Patch (RFC 7386)** - Ähnliches Konzept
- **JSON Patch (RFC 6902)** - Alternative (komplexer)
- **Schema v2.1:** `schema/v2.1-complete.json`
- **Konzept:** `docs/SCHEMA_V2.1_CONCEPT.md`

---

## ✅ Status

**Algorithmus:** ✅ **SPECIFIED** (31. März 2026)

- ✅ Formale Spezifikation
- ✅ Test-Cases definiert
- ⏳ Implementierung (JavaScript/Python)
- ⏳ Unit-Tests

---

**Erstellt:** 31. März 2026  
**Version:** 1.0  
**Status:** Specification Complete
