# Solid Geometry Research - Perplexity Findings

**Datum:** 01.04.2026  
**Quelle:** Perplexity AI + IFC Standards

---

## 🔍 Key Findings

### 1. IFC Geometry Standards

**Spatial Hierarchy:**
- IFC erfordert strikte räumliche Hierarchie
- Jede Geometrie muss einem `IfcBuildingStorey` zugeordnet sein
- `IfcBuilding` → `IfcBuildingStorey` → `IfcBuildingElement`
- Verknüpfung via `IfcRelAggregates` Relationship

**Koordinatensystem:**
- `IfcLocalPlacement` für relative Positionierung
- `PlacementRelTo` für Parent-Child Beziehungen
- Absolute Platzierung im World Coordinate System möglich

**Building Elements:**
- Abstract `IfcBuildingElement` Supertype
- Konkrete Klassen: `IfcWall`, `IfcSlab`, `IfcRoof`, etc.
- Geometrie via `IfcProductDefinitionShape`

**Wichtig für uns:**
- ✅ Parent-Child Hierarchie ist IFC-Standard
- ✅ Relative Positionierung ist Best Practice
- ✅ Lokale Koordinatensysteme pro Element

---

### 2. Three.js BufferGeometry

**Box Geometry (Quader):**

**Vertex-Reihenfolge (24 Vertices, 6 Faces):**
```javascript
// Face 0: Back (-Z)
[-width/2, -height/2, -depth/2],  // V0
[ width/2, -height/2, -depth/2],  // V1
[ width/2,  height/2, -depth/2],  // V2
[-width/2,  height/2, -depth/2],  // V3

// Face 1: Front (+Z)
[-width/2, -height/2,  depth/2],  // V4
[ width/2, -height/2,  depth/2],  // V5
[ width/2,  height/2,  depth/2],  // V6
[-width/2,  height/2,  depth/2],  // V7

// Face 2: Left (-X)
[-width/2, -height/2, -depth/2],  // V8
[-width/2,  height/2, -depth/2],  // V9
[-width/2,  height/2,  depth/2],  // V10
[-width/2, -height/2,  depth/2],  // V11

// Face 3: Right (+X)
[ width/2, -height/2, -depth/2],  // V12
[ width/2,  height/2, -depth/2],  // V13
[ width/2,  height/2,  depth/2],  // V14
[ width/2, -height/2,  depth/2],  // V15

// Face 4: Top (+Y)
[-width/2,  height/2, -depth/2],  // V16
[ width/2,  height/2, -depth/2],  // V17
[ width/2,  height/2,  depth/2],  // V18
[-width/2,  height/2,  depth/2],  // V19

// Face 5: Bottom (-Y)
[-width/2, -height/2, -depth/2],  // V20
[ width/2, -height/2, -depth/2],  // V21
[ width/2, -height/2,  depth/2],  // V22
[-width/2, -height/2,  depth/2]   // V23
```

**Indices (Counter-Clockwise):**
```javascript
[
  0,1,2,  0,2,3,    // Back
  4,5,6,  4,6,7,    // Front
  8,9,10, 8,10,11,  // Left
  12,13,14, 12,14,15, // Right
  16,17,18, 16,18,19, // Top
  20,21,22, 20,22,23  // Bottom
]
```

**Code-Template:**
```javascript
const geometry = new THREE.BufferGeometry();
geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
geometry.setIndex(new THREE.BufferAttribute(indices, 1));
geometry.computeVertexNormals(); // Automatische Normal-Berechnung
```

**Wichtig:**
- ✅ `computeVertexNormals()` für automatische Beleuchtung
- ✅ Counter-Clockwise Winding Order (CCW)
- ✅ 24 Vertices (4 pro Face) für saubere Normalen

---

### 3. Face Indexing Standard

**Standard Box Face Order:**
```
0: Back  (-Z)
1: Front (+Z)
2: Left  (-X)
3: Right (+X)
4: Top   (+Y)
5: Bottom (-Y)
```

**Für Gebäude (angepasst):**
```
0: Süd   (Y=0,    orientation=180°)
1: Ost   (X=max,  orientation=90°)
2: Nord  (Y=max,  orientation=0°)
3: West  (X=0,    orientation=270°)
4: Oben  (Z=max,  Dach/Decke)
5: Unten (Z=0,    Boden)
```

**Winding Order:**
- ✅ **Counter-Clockwise (CCW)** von außen betrachtet
- ✅ Three.js Default: CCW für Front-Facing
- ✅ Backface Culling aktiviert

---

### 4. Building Coordinate System

**BIM/IFC Standard:**
```
X-Achse: Ost-West   (positiv = Ost)
Y-Achse: Nord-Süd   (positiv = Nord)
Z-Achse: Vertikal   (positiv = Oben)
```

**Three.js Standard:**
```
X-Achse: Rechts
Y-Achse: Oben
Z-Achse: Aus dem Bildschirm
```

**Mapping für unser Projekt:**
```javascript
// BIM → Three.js
X (Ost)   → X (Rechts)
Y (Nord)  → Z (Hinten)
Z (Oben)  → Y (Oben)

// Rotation für Anpassung
scene.rotation.x = -Math.PI / 2; // Y-up → Z-up
```

**Wichtig:**
- ✅ Wir nutzen **BIM-Konvention** (X=Ost, Y=Nord, Z=Oben)
- ✅ Three.js Camera entsprechend positionieren
- ✅ Grid Helper mit korrekter Orientierung

---

### 5. Hierarchical Transformations

**Three.js Parent-Child:**
```javascript
const parent = new THREE.Group();
parent.position.set(10, 0, 0);

const child = new THREE.Mesh(geometry, material);
child.position.set(1, 0, 0); // Relativ zum Parent
parent.add(child);

// World Position = Parent Position + Child Position
// child.worldPosition = [11, 0, 0]
```

**Matrix Calculation:**
```javascript
child.matrixWorld = parent.matrixWorld × child.matrixLocal
```

**Best Practices:**
- ✅ `THREE.Group` für logische Gruppierung
- ✅ Automatisches Matrix-Update via `updateMatrixWorld()`
- ✅ Nur bei Änderung neu berechnen (Performance)

**Für unser Projekt:**
```javascript
// Erdgeschoss
const eg = new THREE.Group();
eg.position.set(0, 0, 0);

// Obergeschoss (auf EG)
const og = new THREE.Group();
og.position.set(0, 0, 2.5); // Relativ zu EG
eg.add(og);

// Dachgeschoss (auf OG, mit Rücksprung)
const dg = new THREE.Group();
dg.position.set(1, 1, 2.5); // Relativ zu OG
og.add(dg);
```

---

## 🎯 Entscheidungen für Implementation

### Face-Indexing
**Entscheidung:** Standard Box Order mit Gebäude-Mapping

```javascript
const FACE_MAPPING = {
  BOX: {
    0: { name: 'Süd',   orientation: 180, normal: [0, -1, 0] },
    1: { name: 'Ost',   orientation: 90,  normal: [1, 0, 0] },
    2: { name: 'Nord',  orientation: 0,   normal: [0, 1, 0] },
    3: { name: 'West',  orientation: 270, normal: [-1, 0, 0] },
    4: { name: 'Oben',  orientation: null, normal: [0, 0, 1] },
    5: { name: 'Unten', orientation: null, normal: [0, 0, -1] }
  },
  TRIANGULAR_PRISM: {
    0: { name: 'Süd-Dachfläche', inclination: 37 },
    1: { name: 'Nord-Dachfläche', inclination: 37 },
    2: { name: 'West-Giebel', inclination: 90 },
    3: { name: 'Ost-Giebel', inclination: 90 }
  }
}
```

### Koordinatensystem
**Entscheidung:** BIM-Standard (X=Ost, Y=Nord, Z=Oben)

```javascript
// Dimensions Mapping
{
  length: X-Achse (Ost-West),
  width:  Y-Achse (Nord-Süd),
  height: Z-Achse (Vertikal)
}
```

### Hierarchie
**Entscheidung:** Parent-Child mit Offsets

```json
{
  "id": "og",
  "parent_ref": "eg",
  "offset": [0, 0, 2.5]  // [X, Y, Z] relativ zu Parent
}
```

### Geometrie-Generierung
**Entscheidung:** BufferGeometry mit `computeVertexNormals()`

```javascript
function generateBoxGeometry(dimensions) {
  const geometry = new THREE.BufferGeometry();
  const vertices = calculateBoxVertices(dimensions);
  const indices = BOX_INDICES; // Konstante
  
  geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  geometry.computeVertexNormals();
  
  return geometry;
}
```

---

## 📚 Referenzen

1. **IFC Standards:**
   - buildingSMART IFC4 Documentation
   - `IfcLocalPlacement`, `IfcBuildingStorey`, `IfcRelAggregates`

2. **Three.js:**
   - BufferGeometry Documentation
   - Object3D Hierarchy
   - Matrix Transformations

3. **BIM Coordinate Systems:**
   - IFC: X=East, Y=North, Z=Up
   - Revit/ArchiCAD: Same convention

---

## ✅ Next Steps

1. ✅ Implementiere `SolidGeometry` Klasse mit `generateBox()` und `generateTriangularPrism()`
2. ✅ Nutze FACE_MAPPING für automatische Orientierung
3. ✅ Implementiere Parent-Child Positionierung mit `THREE.Group`
4. ✅ Teste mit Demo-JSON (EG + Dach)

---

**Status:** ✅ Research komplett  
**Nächster Schritt:** Phase 1 - Schema v2.1 erweitern
