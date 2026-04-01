# Parametric IFC Generator - Design Document

**Datum:** 01.04.2026  
**Strategie:** Parametrische Solids → IFC-Datei → Standard-Viewer/Import

---

## 🎯 VISION

**Statt eigenes Geometrie-Format:**
```
Parametric Solids (JSON) → Custom Viewer → Custom Format
```

**Besser: Standard IFC nutzen:**
```
Parametric Solids (JSON) → IFC Generator → Standard IFC → Beliebiger Viewer
```

---

## ✅ VORTEILE

### 1. **Standard-Kompatibilität**
- IFC ist ISO-Standard (ISO 16739)
- Jede BIM-Software kann IFC importieren
- Keine Custom-Viewer nötig

### 2. **Interoperabilität**
- Export nach Revit, ArchiCAD, Allplan, etc.
- Import in DWEapp aus beliebiger BIM-Software
- Kein Vendor Lock-in

### 3. **Einfachheit**
- Nur ein Format (IFC)
- Keine Dual-Maintenance (JSON + IFC)
- Viewer-Logik bereits vorhanden (IFC.js, Three.js)

### 4. **Rückverfolgbarkeit**
- IFC-GUIDs für alle Elemente
- Mapping zwischen DIN18599 und IFC
- Audit Trail

---

## 🏗️ ARCHITEKTUR

### Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EINGABE: Parametric Solids (JSON)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. GENERATOR: Parametric IFC Generator                     │
│    - BOX → IFCWALLSTANDARDCASE (4 Wände)                   │
│    - TRIANGULAR_PRISM → IFCROOF + IFCSLAB (2 Dachflächen)  │
│    - Hierarchie: IFCPROJECT → IFCSITE → IFCBUILDING        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. OUTPUT: Standard IFC-Datei (ISO-10303-21)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. VERWENDUNG:                                              │
│    - Import in BIM-Software (Revit, ArchiCAD, etc.)        │
│    - Viewer (IFC.js, Three.js)                             │
│    - DIN18599 Sidecar (IFC_LINKED Modus)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 MAPPING: Solids → IFC

### BOX → IFC

**Input:**
```json
{
  "id": "eg_main",
  "type": "BOX",
  "dimensions": {
    "length": 10.0,
    "width": 8.0,
    "height": 2.5
  },
  "origin": [0, 0, 0]
}
```

**Output IFC:**
```
IFCBUILDINGSTOREY (Erdgeschoss)
├── IFCWALLSTANDARDCASE (Wand Süd)
│   ├── GUID: generiert
│   ├── Position: (0, 0, 0)
│   ├── Length: 10.0m
│   ├── Height: 2.5m
│   └── Thickness: 0.365m (Standard)
│
├── IFCWALLSTANDARDCASE (Wand Ost)
│   ├── Position: (10, 0, 0)
│   ├── Length: 8.0m
│   └── ...
│
├── IFCWALLSTANDARDCASE (Wand Nord)
│   ├── Position: (10, 8, 0)
│   └── ...
│
└── IFCWALLSTANDARDCASE (Wand West)
    ├── Position: (0, 8, 0)
    └── ...
```

**Geometrie:**
```
IFCEXTRUDEDAREASOLID
├── Profile: IFCRECTANGLEPROFILEDEF (Length × Thickness)
├── Position: IFCAXIS2PLACEMENT3D
├── Direction: (0, 0, 1) - Z-Achse
└── Depth: Height
```

---

### TRIANGULAR_PRISM → IFC

**Input:**
```json
{
  "id": "roof_main",
  "type": "TRIANGULAR_PRISM",
  "dimensions": {
    "length": 10.0,
    "width": 8.0,
    "height": 3.0,
    "ridge_direction": "X"
  },
  "parent_ref": "eg_main",
  "offset": [0, 0, 2.5]
}
```

**Output IFC:**
```
IFCROOF (Dach)
├── IFCSLAB (Dachfläche Süd)
│   ├── GUID: generiert
│   ├── Position: (0, 0, 2.5)
│   ├── Length: 10.0m
│   ├── Width: 5.0m (width/2 / cos(slope))
│   ├── Thickness: 0.22m (Standard)
│   └── Slope: 36.87° (arctan(height / (width/2)))
│
├── IFCSLAB (Dachfläche Nord)
│   └── ...
│
├── IFCWALLSTANDARDCASE (Giebel West)
│   ├── Profile: Dreieck (width × height)
│   └── ...
│
└── IFCWALLSTANDARDCASE (Giebel Ost)
    └── ...
```

**Geometrie Dachfläche:**
```
IFCEXTRUDEDAREASOLID
├── Profile: IFCRECTANGLEPROFILEDEF (Length × Thickness)
├── Position: IFCAXIS2PLACEMENT3D (schräg!)
├── Direction: Senkrecht zur Dachfläche
└── Depth: Thickness
```

**Geometrie Giebel:**
```
IFCEXTRUDEDAREASOLID
├── Profile: IFCARBITRARYCLOSEDPROFILEDEF (Dreieck)
├── Position: IFCAXIS2PLACEMENT3D
├── Direction: (1, 0, 0) - X-Achse
└── Depth: Thickness
```

---

## 🔧 IMPLEMENTIERUNG

### Technologie-Stack

**Backend (IFC Generator):**
- Python (ifc-openshell Library)
- TypeScript (ifc.js für Web)

**Empfehlung:** Python + ifc-openshell
- Mature Library
- Vollständige IFC-Unterstützung
- Einfache API

### Code-Struktur

```
/opt/din18599-ifc/
├── generator/
│   ├── __init__.py
│   ├── ifc_generator.py          # Main Generator
│   ├── converters/
│   │   ├── box_converter.py      # BOX → IFC
│   │   ├── prism_converter.py    # TRIANGULAR_PRISM → IFC
│   │   ├── trapezoid_converter.py
│   │   └── pyramid_converter.py
│   ├── utils/
│   │   ├── geometry.py           # Geometrie-Berechnungen
│   │   ├── guid.py               # GUID-Generierung
│   │   └── materials.py          # Material-Definitionen
│   └── templates/
│       ├── project_template.py   # IFC-Projekt-Struktur
│       └── materials_catalog.py  # Standard-Materialien
│
├── cli/
│   └── generate_ifc.py           # CLI Tool
│
└── tests/
    ├── test_box_converter.py
    └── test_prism_converter.py
```

---

## 📝 API-Design

### Python API

```python
from din18599_ifc.generator import IFCGenerator
from din18599_ifc.types import BoxSolid, TriangularPrismSolid

# Generator initialisieren
generator = IFCGenerator(
    project_name="EFH 1978",
    site_location=(51.45, 7.01),
    true_north_offset=0
)

# Solids hinzufügen
eg = BoxSolid(
    id="eg_main",
    dimensions={"length": 10.0, "width": 8.0, "height": 2.5},
    origin=[0, 0, 0]
)
generator.add_solid(eg)

roof = TriangularPrismSolid(
    id="roof_main",
    dimensions={"length": 10.0, "width": 8.0, "height": 3.0},
    parent_ref="eg_main",
    offset=[0, 0, 2.5]
)
generator.add_solid(roof)

# IFC generieren
ifc_file = generator.generate()
ifc_file.write("output.ifc")
```

### CLI Tool

```bash
# JSON → IFC
python -m din18599_ifc.cli.generate_ifc \
  --input demo.din18599.json \
  --output demo.ifc \
  --mode geometry

# Optionen
--mode geometry          # Nur geometry.solids konvertieren
--mode full             # Vollständiges Sidecar (mit envelope)
--materials catalog.json # Custom Material-Katalog
--validate              # IFC validieren
```

---

## 🔗 INTEGRATION: DIN18599 Sidecar ↔ IFC

### Workflow 1: Neu erstellen (Parametric → IFC)

```
1. User erstellt Gebäude in DWEapp (Parametric UI)
2. DWEapp speichert Solids in JSON
3. Generator erstellt IFC-Datei
4. IFC wird in DWEapp-Projekt verlinkt
5. Sidecar JSON referenziert IFC (IFC_LINKED Modus)
```

**Sidecar JSON:**
```json
{
  "meta": {
    "mode": "IFC_LINKED",
    "ifc_file": "efh-1978.ifc",
    "ifc_generated_from": "geometry.solids",
    "ifc_generated_at": "2026-04-01T12:00:00Z"
  },
  "envelope": {
    "walls_external": [
      {
        "id": "wall_sued",
        "ifc_guid": "3a8f9c2e-1234-5678-90ab-cdef12345678",
        "solid_ref": "eg_main",
        "face_index": 0,
        "u_value_undisturbed": 1.2
      }
    ]
  }
}
```

---

### Workflow 2: IFC importieren (IFC → Parametric)

```
1. User importiert IFC-Datei in DWEapp
2. Parser extrahiert Geometrie
3. Optional: Vereinfachung zu Solids (Bounding Boxes)
4. Sidecar JSON wird erstellt (IFC_LINKED Modus)
5. User ergänzt energetische Daten
```

**Sidecar JSON:**
```json
{
  "meta": {
    "mode": "IFC_LINKED",
    "ifc_file": "bestand.ifc",
    "ifc_imported_at": "2026-04-01T12:00:00Z"
  },
  "envelope": {
    "walls_external": [
      {
        "id": "wall_001",
        "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
        "area": 20.5,
        "orientation": 180,
        "u_value_undisturbed": 1.2
      }
    ]
  }
}
```

---

## 🎯 VORTEILE DIESER STRATEGIE

### 1. **Single Source of Truth: IFC**
- Geometrie nur in IFC (nicht doppelt in JSON)
- JSON enthält nur energetische Daten
- Keine Synchronisations-Probleme

### 2. **Standard-Viewer**
- IFC.js für Web-Viewer
- Keine Custom-Geometrie-Renderer nötig
- Three.js Integration vorhanden

### 3. **BIM-Kompatibilität**
- Export nach Revit, ArchiCAD, etc.
- Import aus beliebiger BIM-Software
- Standard-Workflows

### 4. **Flexibilität**
- Parametric → IFC (neu erstellen)
- IFC → Parametric (importieren)
- IFC → IFC (bearbeiten)

---

## 📊 VERGLEICH: Alt vs. Neu

| Aspekt | Alt (Custom Solids) | Neu (Parametric IFC) |
|--------|---------------------|----------------------|
| **Format** | JSON (Custom) | IFC (Standard) |
| **Viewer** | Custom Three.js | IFC.js (Standard) |
| **Import** | Nur DWEapp | Beliebige BIM-Software |
| **Export** | Nur DWEapp | Beliebige BIM-Software |
| **Maintenance** | Hoch (Custom) | Niedrig (Standard) |
| **Interoperabilität** | ❌ Keine | ✅ Vollständig |
| **Komplexität** | Mittel | Niedrig |

---

## 🚀 IMPLEMENTIERUNGS-PLAN

### Phase 1: MVP (Parametric IFC Generator)
1. ✅ Design Document
2. Python Setup (ifc-openshell)
3. BOX → IFC Converter
4. TRIANGULAR_PRISM → IFC Converter
5. CLI Tool
6. Testing mit Demo-JSON

### Phase 2: Integration (DWEapp)
1. IFC Generator API
2. Sidecar JSON erweitern (ifc_file, ifc_guid)
3. IFC-Viewer Integration (IFC.js)
4. UI: Parametric Editor

### Phase 3: Import (IFC → DWEapp)
1. IFC Parser
2. Geometrie-Extraktion
3. Optional: Vereinfachung zu Solids
4. Sidecar-Generierung

---

## ✅ NÄCHSTER SCHRITT

**Jetzt implementieren:**
1. Python Environment Setup
2. ifc-openshell Installation
3. BOX → IFC Converter (MVP)
4. Test: JSON → IFC → Viewer

**Bereit?** 🎯
