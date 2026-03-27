# Boundary Representation (B-Rep) Geometrie-Modell

## Konzept

**Boundary Representation (B-Rep)** ist der Standard in BIM-Programmen (IFC, Revit, ArchiCAD).

### Hierarchie

\`\`\`
Solid (Körper)
  └─ Shell (Hülle)
      └─ Faces (Flächen)
          └─ Loops (Umrandungen)
              └─ Edges (Kanten)
                  └─ Vertices (Ecken/Punkte)
\`\`\`

### Topologische Verknüpfung

**Vertices** (Punkte) werden von mehreren **Edges** geteilt.
**Edges** (Kanten) werden von mehreren **Faces** geteilt.
**Faces** (Flächen) bilden zusammen eine geschlossene **Shell**.

---

## Beispiel: Rechteckiger Raum (10m × 8m × 2.5m)

### Vereinfachtes B-Rep (ohne explizite Edges)

Für Energieberatung reicht meist ein vereinfachtes Modell:

\`\`\`json
{
  "geometry_brep": {
    "vertices": [
      {"id": "V0", "coords": [0, 0, 0]},
      {"id": "V1", "coords": [10, 0, 0]},
      {"id": "V2", "coords": [10, 8, 0]},
      {"id": "V3", "coords": [0, 8, 0]},
      {"id": "V4", "coords": [0, 0, 2.5]},
      {"id": "V5", "coords": [10, 0, 2.5]},
      {"id": "V6", "coords": [10, 8, 2.5]},
      {"id": "V7", "coords": [0, 8, 2.5]}
    ],
    "faces": [
      {
        "id": "AW-SUED",
        "name": "Außenwand Süd",
        "type": "WALL",
        "boundary_condition": "EXTERIOR",
        "u_value": 0.24,
        "vertices": ["V0", "V1", "V5", "V4"]
      },
      {
        "id": "DACH",
        "name": "Dach",
        "type": "ROOF",
        "boundary_condition": "EXTERIOR",
        "u_value": 0.18,
        "vertices": ["V4", "V5", "V6", "V7"]
      }
    ]
  }
}
\`\`\`

**Edges werden implizit abgeleitet:** Zwischen aufeinanderfolgenden Vertices.

---

## Vorteile

1. **Keine Transformation** - Direkte 3D-Koordinaten
2. **Wiederverwendbare Vertices** - Ecken werden geteilt
3. **Automatische Flächenberechnung** - Aus Vertex-Koordinaten
4. **Nachbarschafts-Analyse** - Welche Faces teilen Edges?
5. **Konsistenz-Prüfung** - Ist die Hülle geschlossen?

---

## Topologische Abfragen

### Welche Faces teilen sich eine Edge?

\`\`\`javascript
function findAdjacentFaces(v1, v2, faces) {
  return faces.filter(face => {
    const vertices = face.vertices;
    for (let i = 0; i < vertices.length; i++) {
      const curr = vertices[i];
      const next = vertices[(i + 1) % vertices.length];
      if ((curr === v1 && next === v2) || (curr === v2 && next === v1)) {
        return true;
      }
    }
    return false;
  });
}
\`\`\`

### Automatische Flächenberechnung

\`\`\`javascript
function calculateFaceArea(face, vertexMap) {
  const coords = face.vertices.map(vId => vertexMap[vId].coords);
  
  // Shoelace-Formel für planare Polygone
  let area = 0;
  for (let i = 0; i < coords.length; i++) {
    const j = (i + 1) % coords.length;
    area += coords[i][0] * coords[j][1];
    area -= coords[j][0] * coords[i][1];
  }
  return Math.abs(area) / 2;
}
\`\`\`

---

## Migration vom alten Format

\`\`\`javascript
function convertToBrep(oldFormat) {
  const vertices = [];
  const faces = [];
  const vertexMap = new Map();
  let vertexId = 0;
  
  function getOrCreateVertex(coords) {
    const key = coords.join(',');
    if (!vertexMap.has(key)) {
      const id = \`V\${vertexId++}\`;
      vertices.push({id, coords});
      vertexMap.set(key, id);
    }
    return vertexMap.get(key);
  }
  
  oldFormat.input.elements.forEach(element => {
    if (element.geometry?.type === 'Line2D') {
      const start = element.geometry.start;
      const end = element.geometry.end;
      const height = element.geometry.height || 2.5;
      const origin = element.geometry.local_origin || [0, 0, 0];
      
      const v0 = getOrCreateVertex([origin[0] + start[0], origin[1] + start[1], origin[2]]);
      const v1 = getOrCreateVertex([origin[0] + end[0], origin[1] + end[1], origin[2]]);
      const v2 = getOrCreateVertex([origin[0] + end[0], origin[1] + end[1], origin[2] + height]);
      const v3 = getOrCreateVertex([origin[0] + start[0], origin[1] + start[1], origin[2] + height]);
      
      faces.push({
        id: element.id,
        name: element.name,
        type: element.type,
        boundary_condition: element.boundary_condition,
        u_value: element.u_value_undisturbed,
        vertices: [v0, v1, v2, v3]
      });
    }
  });
  
  return {vertices, faces};
}
\`\`\`
