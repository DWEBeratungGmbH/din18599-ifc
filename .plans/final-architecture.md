# Final Architecture: IFC + Sidecar System

**Datum:** 01.04.2026  
**Status:** FINAL - Basierend auf User-Feedback

---

## 🎯 USE-CASE KLARSTELLUNG

### **Realität bei DWE Beratung:**

1. ✅ **Berater haben BIM-Software** (z.B. EVEBI, ArchiCAD, etc.)
2. ✅ **IFC wird IMMER erstellt** (Standard-Workflow)
3. ✅ **EVEBI Export-Format** existiert (energetische Daten)
4. ❌ **Kein Link zwischen IFC und EVEBI** (manuelles Mapping nötig)
5. ✅ **IFC ist Read-Only** (keine Änderungen, nur Kommentare)
6. ✅ **Korrekturen nur in Sidecar** (nicht in IFC)

---

## 🏗️ ZWEI WORKFLOWS

### **Workflow 1: IFC + EVEBI Import (Bestandsgebäude)**

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT:                                                      │
│ - IFC-Datei (Geometrie, Wände, Dächer)                     │
│ - EVEBI-Datei (U-Werte, Flächen, energetische Daten)       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ PARSER:                                                     │
│ 1. IFC Parser → Extrahiert Geometrie                       │
│    - IFCWALLSTANDARDCASE → walls_external[]                │
│    - IFCROOF/IFCSLAB → roofs[]                             │
│    - IFC-GUID, Fläche, Orientierung                        │
│                                                             │
│ 2. EVEBI Parser → Extrahiert energetische Daten            │
│    - U-Werte, Konstruktionen                               │
│    - Flächen (ohne IFC-Link!)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ MANUELLES MAPPING (UI):                                    │
│ User verlinkt:                                              │
│ - EVEBI Wand "Außenwand Süd" → IFC GUID "1ybs9cI0..."     │
│ - EVEBI Dach "Satteldach" → IFC GUID "07zbdpGN..."        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: DIN18599 Sidecar JSON                               │
│ {                                                           │
│   "meta": {                                                 │
│     "mode": "IFC_LINKED",                                   │
│     "ifc_file": "bestand.ifc",                             │
│     "evebi_source": "bestand.evebi"                        │
│   },                                                        │
│   "envelope": {                                             │
│     "walls_external": [                                     │
│       {                                                     │
│         "id": "wall_sued",                                  │
│         "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",              │
│         "evebi_ref": "Außenwand Süd",                      │
│         "area": 20.5,                                       │
│         "orientation": 180,                                 │
│         "u_value_undisturbed": 1.2                         │
│       }                                                     │
│     ]                                                       │
│   }                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Wichtig:**
- IFC bleibt **unverändert** (Read-Only)
- Sidecar enthält **Links** zu IFC (via GUID)
- Korrekturen nur in Sidecar (z.B. U-Wert anpassen)
- Optional: Kommentar in IFC als Property

---

### **Workflow 2: Parametric Bauklötze (Schnelle Analyse)**

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: Parametric Solids (UI)                              │
│ User erstellt:                                              │
│ - EG: BOX (10m × 8m × 2.5m)                                │
│ - Dach: TRIANGULAR_PRISM (10m × 8m × 3m)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GENERATOR:                                                  │
│ 1. IFC Generator                                            │
│    - BOX → 4x IFCWALLSTANDARDCASE                          │
│    - TRIANGULAR_PRISM → IFCROOF + 2x IFCSLAB + 2x Giebel  │
│    - GUIDs generieren                                       │
│                                                             │
│ 2. Sidecar Generator                                        │
│    - envelope.walls_external[] mit IFC-GUIDs               │
│    - envelope.roofs[] mit IFC-GUIDs                        │
│    - Flächen, Orientierung automatisch                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT:                                                     │
│ - building.ifc (Standard IFC)                              │
│ - building.din18599.json (Sidecar mit IFC-Links)           │
└─────────────────────────────────────────────────────────────┘
```

**Wichtig:**
- Beide Dateien werden **zusammen** generiert
- Perfekte Synchronisation (GUIDs)
- User kann IFC in BIM-Software importieren
- User kann Sidecar für Berechnung nutzen

---

## 📐 SIDECAR SCHEMA (Final)

### Meta Section

```json
{
  "meta": {
    "schema_version": "2.1",
    "mode": "IFC_LINKED",
    "ifc_file": "building.ifc",
    "ifc_generated": false,
    "evebi_source": "building.evebi",
    "site": {
      "latitude": 51.45,
      "longitude": 7.01,
      "true_north_offset": 0
    }
  }
}
```

**Felder:**
- `mode`: `"IFC_LINKED"` (immer, da IFC immer vorhanden)
- `ifc_file`: Pfad zur IFC-Datei (relativ oder absolut)
- `ifc_generated`: `true` wenn aus Bauklötzen generiert, `false` wenn importiert
- `evebi_source`: Optional, wenn aus EVEBI importiert

---

### Envelope Section (mit IFC-Links)

```json
{
  "envelope": {
    "walls_external": [
      {
        "id": "wall_sued",
        "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
        "name": "Außenwand Süd",
        "evebi_ref": "AW_Sued_001",
        "area": 20.5,
        "orientation": 180,
        "inclination": 90,
        "u_value_undisturbed": 1.2,
        "thermal_bridge_delta_u": 0.15,
        "construction_catalog_ref": "Mauerwerk_365mm_Baujahr_1978",
        "corrections": {
          "area_override": null,
          "u_value_override": null,
          "comment": "U-Wert aus EVEBI übernommen"
        }
      }
    ]
  }
}
```

**Wichtig:**
- `ifc_guid`: **Pflicht** (Link zu IFC)
- `evebi_ref`: Optional (Link zu EVEBI)
- `area`, `orientation`, `inclination`: Aus IFC extrahiert
- `corrections`: Korrekturen/Overrides (nur in Sidecar!)

---

## 🔧 IMPLEMENTIERUNGS-KOMPONENTEN

### 1. **EVEBI Parser**
```python
# /opt/din18599-ifc/parsers/evebi_parser.py

def parse_evebi(file_path: str) -> dict:
    """
    Parst EVEBI-Datei und extrahiert:
    - Wände (Name, U-Wert, Fläche)
    - Dächer (Name, U-Wert, Fläche, Neigung)
    - Fenster, Türen
    - Technik (Heizung, Lüftung)
    
    Returns: Dict mit strukturierten Daten
    """
    pass
```

### 2. **IFC Parser (Geometrie-Extraktion)**
```python
# /opt/din18599-ifc/parsers/ifc_parser.py

def extract_geometry(ifc_file: str) -> dict:
    """
    Extrahiert aus IFC:
    - IFCWALLSTANDARDCASE → walls[]
      - GUID, Name, Fläche, Orientierung, Neigung
    - IFCROOF/IFCSLAB → roofs[]
      - GUID, Name, Fläche, Orientierung, Neigung
    
    Returns: Dict mit Geometrie-Daten
    """
    pass
```

### 3. **Mapping Tool (UI)**
```typescript
// /opt/din18599-ifc/viewer/src/components/MappingTool.tsx

interface MappingToolProps {
  ifcElements: IFCElement[]
  evebiElements: EVEBIElement[]
  onMapping: (mapping: Mapping[]) => void
}

// UI: Drag & Drop oder Select
// EVEBI Element → IFC Element
```

### 4. **Parametric IFC Generator**
```python
# /opt/din18599-ifc/generator/parametric_ifc_generator.py

def generate_ifc_from_solids(solids: list[Solid]) -> IFCFile:
    """
    Generiert IFC aus Parametric Solids:
    - BOX → 4x IFCWALLSTANDARDCASE
    - TRIANGULAR_PRISM → IFCROOF + IFCSLAB + Giebel
    
    Returns: IFC-Datei
    """
    pass

def generate_sidecar_from_solids(solids: list[Solid], ifc_file: IFCFile) -> dict:
    """
    Generiert Sidecar mit IFC-Links:
    - envelope.walls_external[] mit ifc_guid
    - Flächen, Orientierung automatisch
    
    Returns: Sidecar JSON
    """
    pass
```

### 5. **Viewer (IFC.js + Sidecar Overlay)**
```typescript
// /opt/din18599-ifc/viewer/src/components/IFCViewer.tsx

interface IFCViewerProps {
  ifcFile: string
  sidecar: DIN18599Data
  highlightElement?: string  // IFC-GUID
}

// IFC.js für Geometrie
// Sidecar für Overlay (U-Werte, Farben, etc.)
```

---

## 📊 DATENFLUSS

### Import-Workflow (IFC + EVEBI)

```
IFC-Datei + EVEBI-Datei
         │
         ├─→ IFC Parser → {walls: [{guid, area, orientation}]}
         │
         └─→ EVEBI Parser → {walls: [{name, u_value, area}]}
                    │
                    ▼
            Mapping Tool (UI)
            User verlinkt manuell
                    │
                    ▼
            Sidecar Generator
            {walls_external: [{ifc_guid, evebi_ref, ...}]}
                    │
                    ▼
            Sidecar JSON (gespeichert)
```

### Parametric-Workflow (Bauklötze)

```
User Input (UI)
{solids: [BOX, TRIANGULAR_PRISM]}
         │
         ├─→ IFC Generator → building.ifc
         │
         └─→ Sidecar Generator → building.din18599.json
                    │
                    ▼
            Beide Dateien verlinkt
            (ifc_guid Mapping perfekt)
```

---

## ✅ NÄCHSTER SCHRITT

**Bitte EVEBI-Beispieldatei hochladen!**

Dann kann ich:
1. EVEBI-Format analysieren
2. Parser implementieren
3. Mapping-Tool designen
4. Vollständigen Workflow testen

**Bereit für Upload!** 📤
