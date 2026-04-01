# Solid Geometry Implementation Plan - Bauklötze-Prinzip

**Version:** 1.0  
**Datum:** 01.04.2026  
**Ziel:** Körper-basierte Geometrie für DIN 18599 Viewer  
**Deadline:** Berlin-Präsentation Mai 2026

---

## 🎯 Projektziel

**Problem:**
- Demo-Datei hat keine echte 3D-Geometrie
- Viewer zeigt nur Platzhalter-Boxen
- Keine realistische Visualisierung

**Lösung:**
- **Bauklötze-Prinzip:** Vordefinierte geometrische Körper (Solids)
- **Relative Positionierung:** Parent-Child Hierarchie mit Offsets
- **Automatische Face-Generierung:** Aus Solid-Parametern
- **Einfach zu editieren:** Nur Dimensionen statt Vertices

**Beispiel:**
```json
{
  "solids": [
    {"id": "eg", "type": "BOX", "dimensions": {"length": 10, "width": 8, "height": 2.5}},
    {"id": "og", "type": "BOX", "parent_ref": "eg", "offset": [0, 0, 2.5]},
    {"id": "dg", "type": "BOX", "parent_ref": "og", "offset": [1, 1, 2.5]},  // 1m Rücksprung
    {"id": "roof", "type": "TRIANGULAR_PRISM", "parent_ref": "dg", "offset": [0, 0, 3]}
  ]
}
```

---

## 📋 Phasen-Übersicht

| Phase | Beschreibung | Aufwand | Status |
|-------|--------------|---------|--------|
| **0** | Perplexity Research | 15min | ⏳ Pending |
| **1** | Schema v2.1 erweitern | 30min | ⏳ Pending |
| **2** | Solid Library (TypeScript) | 45min | ⏳ Pending |
| **3** | Demo-JSON anpassen | 30min | ⏳ Pending |
| **4** | Viewer: Solid-Renderer | 60min | ⏳ Pending |
| **5** | Face-Ableitung | 45min | ⏳ Pending |
| **6** | Testing & Debugging | 30min | ⏳ Pending |
| **7** | Dokumentation | 30min | ⏳ Pending |

**Gesamt:** ~4.5 Stunden

---

## 🔍 Phase 0: Perplexity Research (15min)

### Ziel
Best Practices für 3D Geometry Libraries recherchieren

### Fragen an Perplexity
1. **IFC Geometry Standards:**
   - Wie definiert IFC geometrische Körper (IfcExtrudedAreaSolid)?
   - Welche Primitive sind Standard in BIM?
   - Parent-Child Hierarchien in IFC?

2. **Three.js Best Practices:**
   - Wie rendert man parametrische Geometrie effizient?
   - BufferGeometry vs. Geometry für Bauteile?
   - Instancing für wiederholte Körper?

3. **Coordinate Systems:**
   - Standard-Koordinatensystem für Gebäude (X/Y/Z)?
   - Relative vs. absolute Koordinaten?
   - Transformation Matrices?

4. **Face Indexing:**
   - Standard-Reihenfolge für Box-Faces?
   - Normale-Berechnung für Dachflächen?
   - Winding Order (CW/CCW)?

### Deliverables
- [ ] Research-Notizen in `.plans/solid-geometry-research.md`
- [ ] Entscheidungen für Implementierung dokumentiert

---

## 📐 Phase 1: Schema v2.1 erweitern (30min)

### Ziel
JSON Schema um Solid-Definitionen erweitern

### Aufgaben

**1.1 Solid Types definieren**
```json
{
  "definitions": {
    "solid": {
      "type": "object",
      "required": ["id", "type", "dimensions"],
      "properties": {
        "id": {"type": "string"},
        "type": {"enum": ["BOX", "TRIANGULAR_PRISM", "CYLINDER"]},
        "dimensions": {"$ref": "#/definitions/dimensions"},
        "origin": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
        "parent_ref": {"type": "string"},
        "offset": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
        "rotation": {"type": "number"},
        "description": {"type": "string"}
      }
    }
  }
}
```

**1.2 Dimensions für jeden Solid-Typ**
- BOX: `{length, width, height}`
- TRIANGULAR_PRISM: `{length, width, height, ridge_direction}`
- CYLINDER: `{radius, height}`

**1.3 Face-Referenzen**
```json
{
  "face_ref": {
    "solid_ref": "eg",
    "face_index": 0
  }
}
```

### Dateien
- `schema/v2.1-complete.json` (erweitern)
- `schema/solids.schema.json` (neu)

### Deliverables
- [ ] Schema erweitert
- [ ] Validierung funktioniert
- [ ] Beispiel-JSON validiert

---

## 🧱 Phase 2: Solid Library (TypeScript) (45min)

### Ziel
TypeScript-Bibliothek für Solid-Definitionen und Face-Generierung

### Aufgaben

**2.1 Type Definitions**
```typescript
// viewer/src/types/solids.ts
export type SolidType = 'BOX' | 'TRIANGULAR_PRISM' | 'CYLINDER'

export interface Solid {
  id: string
  type: SolidType
  dimensions: BoxDimensions | PrismDimensions | CylinderDimensions
  origin?: [number, number, number]
  parent_ref?: string
  offset?: [number, number, number]
  rotation?: number
  description?: string
}

export interface BoxDimensions {
  length: number  // X
  width: number   // Y
  height: number  // Z
}

export interface PrismDimensions {
  length: number
  width: number
  height: number
  ridge_direction: 'X' | 'Y'
}
```

**2.2 Solid Generators**
```typescript
// viewer/src/lib/geometry/solids.ts
export class SolidGeometry {
  static generateBox(dimensions: BoxDimensions): {
    vertices: Vector3[]
    faces: Face[]
  }
  
  static generateTriangularPrism(dimensions: PrismDimensions): {
    vertices: Vector3[]
    faces: Face[]
  }
  
  static calculateAbsolutePosition(
    solid: Solid,
    solids: Solid[]
  ): [number, number, number]
}
```

**2.3 Face Utilities**
```typescript
export class FaceUtils {
  static calculateArea(face: Face): number
  static calculateOrientation(face: Face): number
  static calculateInclination(face: Face): number
  static getNormal(face: Face): Vector3
}
```

### Dateien
- `viewer/src/types/solids.ts` (neu)
- `viewer/src/lib/geometry/solids.ts` (neu)
- `viewer/src/lib/geometry/faces.ts` (neu)

### Deliverables
- [ ] Type Definitions komplett
- [ ] Solid Generators implementiert
- [ ] Unit Tests (optional)

---

## 📄 Phase 3: Demo-JSON anpassen (30min)

### Ziel
`efh-demo.din18599.json` mit Solid Geometry erweitern

### Aufgaben

**3.1 Geometry Section hinzufügen**
```json
{
  "meta": {
    "mode": "SOLID_GEOMETRY",
    "lod": "300"
  },
  "geometry": {
    "solids": [
      {
        "id": "eg_main",
        "type": "BOX",
        "dimensions": {"length": 10, "width": 8, "height": 2.5},
        "origin": [0, 0, 0],
        "description": "Erdgeschoss"
      },
      {
        "id": "roof_main",
        "type": "TRIANGULAR_PRISM",
        "dimensions": {"length": 10, "width": 8, "height": 3, "ridge_direction": "X"},
        "parent_ref": "eg_main",
        "offset": [0, 0, 2.5],
        "description": "Satteldach"
      }
    ]
  }
}
```

**3.2 Envelope mit Face-Referenzen**
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
      }
    ],
    "roofs": [
      {
        "id": "roof_sued",
        "name": "Dachfläche Süd",
        "solid_ref": "roof_main",
        "face_index": 0,
        "u_value_undisturbed": 0.35,
        "inclination": 37
      }
    ]
  }
}
```

**3.3 Flächen automatisch berechnen**
- `area` Felder aus Geometrie ableiten
- `orientation` aus Face-Index ableiten
- `inclination` für Dachflächen berechnen

### Dateien
- `viewer/public/demo/efh-demo.din18599.json` (erweitern)

### Deliverables
- [ ] Demo-JSON erweitert
- [ ] Validierung erfolgreich
- [ ] Flächen korrekt berechnet

---

## 🎨 Phase 4: Viewer - Solid-Renderer (60min)

### Ziel
Three.js Komponenten für Solid-Rendering

### Aufgaben

**4.1 SolidRenderer Component**
```typescript
// viewer/src/components/SolidRenderer.tsx
export function SolidRenderer({ solid }: { solid: Solid }) {
  const geometry = useMemo(() => {
    switch(solid.type) {
      case 'BOX':
        return SolidGeometry.generateBox(solid.dimensions)
      case 'TRIANGULAR_PRISM':
        return SolidGeometry.generateTriangularPrism(solid.dimensions)
    }
  }, [solid])
  
  const position = useMemo(() => 
    SolidGeometry.calculateAbsolutePosition(solid, allSolids),
    [solid, allSolids]
  )
  
  return (
    <mesh position={position}>
      <bufferGeometry>
        {/* Vertices aus geometry */}
      </bufferGeometry>
      <meshStandardMaterial />
    </mesh>
  )
}
```

**4.2 App.tsx Integration**
```typescript
// Solids rendern statt einzelne Walls/Roofs
{project?.geometry?.solids?.map(solid => (
  <SolidRenderer key={solid.id} solid={solid} />
))}
```

**4.3 Material-Mapping**
- Face-Index → Envelope-Element → U-Wert → Farbe
- Hover-Effekte
- Selection-State

### Dateien
- `viewer/src/components/SolidRenderer.tsx` (neu)
- `viewer/src/components/FaceRenderer.tsx` (neu)
- `viewer/src/App.tsx` (anpassen)

### Deliverables
- [ ] SolidRenderer implementiert
- [ ] Rendering funktioniert
- [ ] Material-Mapping korrekt

---

## 🔗 Phase 5: Face-Ableitung (45min)

### Ziel
Automatische Ableitung von Envelope-Elementen aus Solids

### Aufgaben

**5.1 Face-Generator**
```typescript
// viewer/src/lib/geometry/envelope-mapper.ts
export function generateEnvelopeFromSolids(
  solids: Solid[],
  envelopeData: any
): EnvelopeElement[] {
  const elements: EnvelopeElement[] = []
  
  for (const solid of solids) {
    const faces = SolidGeometry.generateFaces(solid)
    
    for (const [index, face] of faces.entries()) {
      // Finde matching Envelope-Element
      const element = envelopeData.walls_external?.find(
        w => w.solid_ref === solid.id && w.face_index === index
      )
      
      if (element) {
        elements.push({
          ...element,
          area: FaceUtils.calculateArea(face),
          orientation: FaceUtils.calculateOrientation(face),
          vertices: face.vertices
        })
      }
    }
  }
  
  return elements
}
```

**5.2 Store Integration**
```typescript
// viewer/src/store/viewer.store.ts
const enrichedEnvelope = useMemo(() => 
  generateEnvelopeFromSolids(project.geometry.solids, project.envelope),
  [project]
)
```

### Dateien
- `viewer/src/lib/geometry/envelope-mapper.ts` (neu)
- `viewer/src/store/viewer.store.ts` (anpassen)

### Deliverables
- [ ] Face-Ableitung funktioniert
- [ ] Flächen korrekt berechnet
- [ ] Orientierung korrekt

---

## 🧪 Phase 6: Testing & Debugging (30min)

### Ziel
Vollständiger Test der Solid Geometry

### Test-Szenarien

**6.1 Einfaches Haus (EG + Dach)**
- BOX: 10×8×2.5m
- TRIANGULAR_PRISM: 10×8×3m
- Erwartung: 4 Wände + 2 Dachflächen

**6.2 Mehrgeschossig (EG + OG + Dach)**
- BOX: 10×8×2.5m (EG)
- BOX: 10×8×2.5m (OG, offset [0,0,2.5])
- TRIANGULAR_PRISM: 10×8×3m (Dach, offset [0,0,5])

**6.3 Mit Rücksprung (EG + OG + DG + Dach)**
- BOX: 10×8×2.5m (EG)
- BOX: 10×8×2.5m (OG)
- BOX: 8×6×3m (DG, offset [1,1,5])
- TRIANGULAR_PRISM: 8×6×3m (Dach)

**6.4 Validierung**
- [ ] Flächen korrekt berechnet
- [ ] Orientierung korrekt (0°/90°/180°/270°)
- [ ] Neigung korrekt (Dach)
- [ ] Position korrekt (Parent-Child)
- [ ] Rendering ohne Fehler

### Dateien
- `viewer/src/__tests__/solids.test.ts` (optional)

### Deliverables
- [ ] Alle Test-Szenarien funktionieren
- [ ] Keine Rendering-Fehler
- [ ] Performance OK (<100ms)

---

## 📚 Phase 7: Dokumentation (30min)

### Ziel
Vollständige Dokumentation des Solid Geometry Systems

### Aufgaben

**7.1 SOLID_GEOMETRY_LIBRARY.md**
- Konzept & Motivation
- Solid Types (BOX, PRISM, etc.)
- Parameter-Referenz
- Face-Indexing
- Beispiele
- Best Practices

**7.2 Code-Kommentare**
- JSDoc für alle Public Functions
- Beispiele in Kommentaren
- Type Annotations

**7.3 README.md Update**
- Geometry-Section hinzufügen
- Demo-Beispiel zeigen

### Dateien
- `docs/SOLID_GEOMETRY_LIBRARY.md` (neu)
- `README.md` (erweitern)
- Code-Kommentare

### Deliverables
- [ ] Dokumentation komplett
- [ ] Beispiele funktionieren
- [ ] README aktualisiert

---

## 🎯 Success Criteria

### Must Have
- ✅ BOX und TRIANGULAR_PRISM implementiert
- ✅ Demo-JSON mit Solid Geometry
- ✅ Viewer rendert Solids korrekt
- ✅ Flächen automatisch berechnet
- ✅ Parent-Child Hierarchie funktioniert

### Should Have
- ✅ Face-Indexing dokumentiert
- ✅ Material-Mapping (U-Wert → Farbe)
- ✅ Hover & Selection
- ✅ Performance <100ms

### Nice to Have
- ⏳ CYLINDER Solid-Typ
- ⏳ L_SHAPE Solid-Typ
- ⏳ Unit Tests
- ⏳ Instancing für Performance

---

## 🚀 Deployment

### Lokaler Test
```bash
cd /opt/din18599-ifc/viewer
npm run dev
# Browser: http://localhost:5173
# Demo laden → Solids sollten sichtbar sein
```

### Validierung
```bash
# JSON Schema Validierung
npm run validate
```

### Git Commit
```bash
git add -A
git commit -m "feat: Solid Geometry System (Bauklötze-Prinzip)

- BOX und TRIANGULAR_PRISM Solids
- Parent-Child Hierarchie mit Offsets
- Automatische Face-Generierung
- Demo-JSON erweitert
- Viewer-Rendering implementiert
- Dokumentation komplett"
git push origin master
```

---

## 📊 Risiken & Mitigations

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Three.js Performance-Probleme | Mittel | Hoch | BufferGeometry + Instancing nutzen |
| Face-Indexing inkonsistent | Niedrig | Mittel | Standard-Konvention dokumentieren |
| Parent-Child Bugs | Mittel | Mittel | Unit Tests für Position-Berechnung |
| Schema-Breaking Changes | Niedrig | Hoch | Abwärtskompatibilität sicherstellen |

---

## 🔄 Nächste Schritte (nach diesem Sprint)

1. **Fenster-Integration:** Fenster als Löcher in Faces
2. **Mehr Solid-Typen:** CYLINDER, L_SHAPE, GABLE_ROOF
3. **IFC-Import:** IFC → Solid Geometry Konverter
4. **Editor-UI:** Visuelle Bearbeitung von Solids
5. **Templates:** Vordefinierte Gebäude-Templates

---

**Status:** 📝 Plan erstellt, wartet auf Perplexity Review  
**Nächster Schritt:** Phase 0 - Perplexity Research
