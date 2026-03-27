# Geometrie-Validierung für 3D-Viewer

## Problem

Beim 3D-Rendering können folgende Fehler auftreten:
1. **Wände mit Dicke** statt als Flächen
2. **Dach/Boden falsch positioniert**
3. **Fenster nicht sichtbar**
4. **Koordinaten-Inkonsistenzen** (relative vs. absolute)

## Lösungsansätze

### 1. Vereinfachtes Geometrie-Format

**Aktuell:** Komplexe Hierarchie mit `parent_ref`, `local_origin`, `coordinates`

**Vereinfacht:** Nur absolute Koordinaten + Bounding Box

```json
{
  "elements": [
    {
      "id": "AW-SUED",
      "type": "WALL",
      "geometry_simple": {
        "type": "Rectangle3D",
        "corner1": [0, 0, 0],
        "corner2": [10, 2.5, 0]
      }
    }
  ]
}
```

**Vorteile:**
- ✅ Keine Parent-Referenzen nötig
- ✅ Keine Koordinaten-Transformation
- ✅ Direkt renderbar

**Nachteile:**
- ❌ Keine Hierarchie
- ❌ Änderungen nicht propagierbar

---

### 2. Validierungs-Regeln

#### Regel 1: Konsistenz-Check

```javascript
function validateGeometry(data) {
  const errors = [];
  
  // Check 1: Alle Elements mit geometry haben parent_ref
  data.input.elements.forEach(element => {
    if (element.geometry && !element.geometry.parent_ref) {
      errors.push(`Element ${element.id}: Fehlende parent_ref`);
    }
  });
  
  // Check 2: Dach/Boden haben Polygon2D
  data.input.elements.forEach(element => {
    if ((element.type === 'ROOF' || element.type === 'FLOOR') && 
        element.geometry?.type !== 'Polygon2D') {
      errors.push(`Element ${element.id}: ${element.type} muss Polygon2D haben`);
    }
  });
  
  // Check 3: Wände haben Line2D
  data.input.elements.forEach(element => {
    if (element.type === 'WALL' && 
        element.geometry?.type !== 'Line2D') {
      errors.push(`Element ${element.id}: WALL muss Line2D haben`);
    }
  });
  
  // Check 4: Fenster haben Rectangle2D
  data.input.windows?.forEach(window => {
    if (window.geometry?.type !== 'Rectangle2D') {
      errors.push(`Fenster ${window.id}: Muss Rectangle2D haben`);
    }
  });
  
  return errors;
}
```

#### Regel 2: Bounding Box Check

```javascript
function validateBoundingBox(data) {
  const errors = [];
  
  data.input.zones.forEach(zone => {
    if (!zone.geometry) return;
    
    const coords = zone.geometry.coordinates || [];
    if (coords.length < 3) {
      errors.push(`Zone ${zone.id}: Zu wenige Koordinaten (${coords.length})`);
    }
    
    // Check: Alle Koordinaten positiv
    coords.forEach((coord, i) => {
      if (coord[0] < 0 || coord[1] < 0) {
        errors.push(`Zone ${zone.id}: Negative Koordinate bei Index ${i}`);
      }
    });
  });
  
  return errors;
}
```

#### Regel 3: Hierarchie-Check

```javascript
function validateHierarchy(data) {
  const errors = [];
  const validParents = new Set(['BUILDING']);
  
  // Sammle alle Zone-IDs
  data.input.zones?.forEach(zone => {
    validParents.add(zone.id);
    zone.spaces?.forEach(space => {
      validParents.add(space.id);
    });
  });
  
  // Check: Alle parent_ref existieren
  data.input.elements.forEach(element => {
    const parentRef = element.geometry?.parent_ref;
    if (parentRef && !validParents.has(parentRef)) {
      errors.push(`Element ${element.id}: Ungültige parent_ref "${parentRef}"`);
    }
  });
  
  return errors;
}
```

---

### 3. Auto-Korrektur

```javascript
function autoCorrectGeometry(data) {
  const corrections = [];
  
  // Korrektur 1: Fehlende parent_ref → zone_id verwenden
  data.input.elements.forEach(element => {
    if (element.geometry && !element.geometry.parent_ref && element.zone_id) {
      element.geometry.parent_ref = element.zone_id;
      corrections.push(`Element ${element.id}: parent_ref auf ${element.zone_id} gesetzt`);
    }
  });
  
  // Korrektur 2: Fehlende local_origin → [0,0,0]
  data.input.elements.forEach(element => {
    if (element.geometry && !element.geometry.local_origin) {
      element.geometry.local_origin = [0, 0, 0];
      corrections.push(`Element ${element.id}: local_origin auf [0,0,0] gesetzt`);
    }
  });
  
  // Korrektur 3: Dach ohne Geometrie → aus Zone ableiten
  data.input.elements.forEach(element => {
    if (element.type === 'ROOF' && !element.geometry && element.zone_id) {
      const zone = data.input.zones.find(z => z.id === element.zone_id);
      if (zone?.geometry) {
        element.geometry = {
          type: 'Polygon2D',
          parent_ref: element.zone_id,
          local_origin: [0, 0, zone.geometry.ceiling_height || 2.5],
          coordinates: zone.geometry.coordinates
        };
        corrections.push(`Element ${element.id}: Geometrie aus Zone ${element.zone_id} abgeleitet`);
      }
    }
  });
  
  return corrections;
}
```

---

### 4. Rendering-Vereinfachung

**Problem:** Komplexe Hierarchie-Traversierung fehleranfällig

**Lösung:** Flatten vor dem Rendering

```javascript
function flattenGeometry(data) {
  const flattened = {
    walls: [],
    floors: [],
    roofs: [],
    windows: []
  };
  
  data.input.elements.forEach(element => {
    const absolutePos = calculateAbsolutePosition(element, data);
    
    const flat = {
      id: element.id,
      type: element.type,
      color: getColor(element),
      geometry: {
        ...element.geometry,
        absolute_position: absolutePos
      }
    };
    
    if (element.type === 'WALL') {
      flattened.walls.push(flat);
    } else if (element.type === 'ROOF') {
      flattened.roofs.push(flat);
    } else if (element.type === 'FLOOR') {
      flattened.floors.push(flat);
    }
  });
  
  return flattened;
}
```

---

## Empfehlung

**Kurzfristig (für Demo):**
- ✅ Validierung beim Laden (Fehler in Console ausgeben)
- ✅ Auto-Korrektur für fehlende Felder
- ✅ Flatten vor Rendering

**Langfristig (für Production):**
- Schema-Validierung mit JSON Schema
- Geometrie-Editor mit visueller Vorschau
- Export-Funktion für korrigierte Dateien

---

## Integration in Viewer

```javascript
// In 3d-viewer.html nach dem Laden:
function handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            
            // 1. Validieren
            const errors = [
                ...validateGeometry(data),
                ...validateBoundingBox(data),
                ...validateHierarchy(data)
            ];
            
            if (errors.length > 0) {
                console.warn('Geometrie-Fehler gefunden:', errors);
            }
            
            // 2. Auto-Korrektur
            const corrections = autoCorrectGeometry(data);
            if (corrections.length > 0) {
                console.info('Auto-Korrekturen:', corrections);
            }
            
            // 3. Rendern
            buildModel(data);
            
        } catch (error) {
            alert('Fehler beim Laden: ' + error.message);
        }
    };
    reader.readAsText(file);
}
```
