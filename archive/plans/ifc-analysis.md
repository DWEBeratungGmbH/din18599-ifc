# IFC-Analyse: DIN18599TestIFC.ifc

**Datum:** 01.04.2026  
**Datei:** `/opt/din18599-ifc/sources/DIN18599TestIFC.ifc`  
**Format:** IFC2X3  
**Software:** CASCADOS_V12 12.1.1381.0

---

## 🏗️ IFC-Struktur

### Hierarchie
```
IFCPROJECT
└── IFCSITE (Gelände)
    └── IFCBUILDING (<Standard>)
        └── IFCBUILDINGSTOREY (Erdgeschoss, -0.2m)
            ├── IFCSPACE (Raum 1, Raum 2)
            ├── IFCWALLSTANDARDCASE (6 Wände)
            ├── IFCSLAB (1 Bodenplatte, 2 Dachflächen)
            └── IFCROOF (Dach 1)
```

### Gefundene Elemente

**Wände (6x IFCWALLSTANDARDCASE):**
- `#135` - Wand - 001
- `#188` - Wand - 002
- `#870` - Wand - 003
- `#6235` - Wand - 004
- `#6900` - Wand - 005
- `#6953` - Wand - 006

**Dach (IFCROOF + 2x IFCSLAB):**
- `#7003` - IFCROOF 'Dach 1'
- `#6991` - IFCSLAB (ROOF) - Süd-Dachfläche
- `#7002` - IFCSLAB (ROOF) - Nord-Dachfläche

**Boden (IFCSLAB):**
- `#7041` - IFCSLAB (FLOOR) 'Deckenplatte - 001'

---

## 📐 Geometrie-Typ

**Alle Elemente nutzen:** `IFCEXTRUDEDAREASOLID`

**Beispiel Wand #135:**
```
#135=IFCWALLSTANDARDCASE(...)
  └── IFCPRODUCTDEFINITIONSHAPE
      └── IFCSHAPEREPRESENTATION ('SweptSolid')
          └── IFCEXTRUDEDAREASOLID
              ├── Profile: IFCARBITRARYCLOSEDPROFILEDEF (Polyline)
              ├── Position: IFCAXIS2PLACEMENT3D
              ├── Direction: Z-Achse
              └── Depth: Extrusion-Höhe
```

**Beispiel Dach #6991:**
```
#6991=IFCSLAB(..., .ROOF.)
  └── IFCEXTRUDEDAREASOLID
      ├── Profile: Rechteck
      ├── Direction: Schräg (nicht Z-Achse!)
      └── Depth: 0.220676m (Dachdicke)
```

---

## 🔄 IFC → Solid Geometry Mapping

### Problem: IFC ist zu detailliert

**IFC-Ansatz:**
- Jede Wand ist ein separates `IFCWALLSTANDARDCASE`
- Jede Dachfläche ist ein separates `IFCSLAB`
- Geometrie ist extrusion-basiert (nicht parametrisch)

**Unser Solid-Ansatz:**
- Ein `BOX` für das gesamte Geschoss
- Ein `TRIANGULAR_PRISM` für das gesamte Dach
- Parametrisch (length, width, height)

### Mapping-Strategie

**Option A: IFC → Solids konvertieren (Verlustbehaftet)**
```
6x IFCWALLSTANDARDCASE → 1x BOX (Bounding Box)
2x IFCSLAB (ROOF) → 1x TRIANGULAR_PRISM (approximiert)
```

**Vorteile:**
- Einfache Geometrie
- Schnelle Berechnung
- Editierbar

**Nachteile:**
- Verlust von Details (Wandöffnungen, exakte Geometrie)
- Approximation

**Option B: IFC-Linked Modus (Geometrie bleibt in IFC)**
```json
{
  "meta": {
    "mode": "IFC_LINKED",
    "ifc_file": "DIN18599TestIFC.ifc"
  },
  "envelope": {
    "walls_external": [
      {
        "id": "wall_001",
        "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
        "u_value_undisturbed": 1.2
      }
    ]
  }
}
```

**Vorteile:**
- Keine Geometrie-Konvertierung
- Volle IFC-Details erhalten
- Nur energetische Daten im JSON

**Nachteile:**
- IFC-Datei muss verfügbar sein
- Viewer muss IFC parsen können

---

## 🎯 Empfehlung: Hybrid-Ansatz

### Zwei Modi im Schema

**1. Solid Geometry Modus (Neu erstellt/Einfach)**
```json
{
  "meta": {"mode": "SOLID_GEOMETRY"},
  "geometry": {
    "solids": [
      {"type": "BOX", "dimensions": {...}},
      {"type": "TRIANGULAR_PRISM", "dimensions": {...}}
    ]
  },
  "envelope": {
    "walls_external": [
      {"solid_ref": "eg_main", "face_index": 0}
    ]
  }
}
```

**2. IFC-Linked Modus (Aus IFC importiert)**
```json
{
  "meta": {
    "mode": "IFC_LINKED",
    "ifc_file": "DIN18599TestIFC.ifc"
  },
  "envelope": {
    "walls_external": [
      {
        "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
        "area": 20.5,
        "orientation": 180,
        "u_value_undisturbed": 1.2
      }
    ]
  }
}
```

**Viewer-Logik:**
```typescript
if (meta.mode === 'SOLID_GEOMETRY') {
  // Geometrie aus JSON generieren
  renderSolids(geometry.solids)
} else if (meta.mode === 'IFC_LINKED') {
  // Geometrie aus IFC laden
  loadIFC(meta.ifc_file)
  // Oder: Schematische Darstellung aus area/orientation
  renderSchematic(envelope)
}
```

---

## 📊 IFC-Geometrie Details

### Koordinatensystem
- **Origin:** (0, 0, 0)
- **X-Achse:** (1, 0, 0) - Ost
- **Y-Achse:** (0, 1, 0) - Nord
- **Z-Achse:** (0, 0, 1) - Oben

✅ **Passt zu unserem System!**

### Erdgeschoss
- **Höhe:** -0.2m (unter Null)
- **Räume:** 2x IFCSPACE
- **Wände:** 6x IFCWALLSTANDARDCASE
- **Höhe:** ~4.5-4.7m

### Dach
- **Typ:** IFCROOF mit 2x IFCSLAB
- **Neigung:** Aus Extrusion-Direction berechenbar
- **Dicke:** 0.220676m

---

## ✅ Nächste Schritte

1. **Viewer-Modi implementieren:**
   - Solid Geometry Modus (Priorität)
   - IFC-Linked Modus (später)

2. **IFC-Import Tool (Optional):**
   - IFC parsen
   - Bounding Box berechnen
   - Solids generieren
   - Sidecar JSON erstellen

3. **Schema erweitern:**
   - `meta.mode` Feld hinzufügen
   - IFC-GUID Felder optional machen

---

**Status:** ✅ IFC analysiert, Mapping-Strategie definiert  
**Nächster Schritt:** Viewer mit Solid Geometry Modus implementieren
