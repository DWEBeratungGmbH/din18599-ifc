# EVEBI Format Analysis

**Datum:** 01.04.2026  
**Quelle:** `/opt/din18599-ifc/sources/IFC_EVBI/`  
**Software:** CASCADOS_V12 12.1.1381.0

---

## 📁 DATEIEN

| Datei | Größe | Format | Zweck |
|-------|-------|--------|-------|
| `DIN18599TestIFCv2.ifc` | 1.0 MB | IFC2X3 | Geometrie (Wände, Dächer, Räume) |
| `DIN18599Test.xml` | 110 KB | XML | Energetische Daten (U-Werte, Flächen) |
| `DIN18599Test.evex` | 887 KB | Binary | EVEBI Projekt (komplett) |
| `DIN18599Test_260401.evea` | 887 KB | Binary | EVEBI Archiv |
| `DIN18599Test.lca.xml` | 341 B | XML | LCA Daten (minimal) |

**Wichtig:** `DIN18599Test.xml` ist die **Export-Datei** mit allen energetischen Daten!

---

## 🏗️ EVEBI XML STRUKTUR

### Root Structure

```xml
<?xml version="1.0" encoding="ISO-8859-1"?>
<Root Version="3">
    <Creator Product="CASCADOS_V12" Version="12.1.1381.0"/>
    <Project UID="{...}" Name="..." Description="...">
        <UValueGroups>...</UValueGroups>
        <Buildings>
            <Building UID="{...}">
                <Geometry>...</Geometry>
                <Floors>
                    <Floor UID="{...}">
                        <Rooms>
                            <Room UID="{...}">
                                <Faces>
                                    <Face GUID="{...}"/>
                                </Faces>
                            </Room>
                        </Rooms>
                    </Floor>
                </Floors>
            </Building>
        </Buildings>
    </Project>
</Root>
```

---

## 📐 FACE ELEMENT (Wichtigste Datenstruktur)

### Face Attributes

```xml
<Face 
    GUID="{2819422A-7650-404A-BCE8-C355A4FE3E9C}"
    refNum="2"
    Count="1"
    Area="15.492396"
    Neigungswinkel="90.00"
    RefUvalue="{76729BF2-00A2-4420-8326-0F52982D323B}"
    Uvalue="0.000000"
    Type="Wall"
    Orientation="W"
    OrientationAngle="270.00"
    Opposite="Aussenluft"
    Code="WA"
    PosNo="004"
    CadElem="{674608B0-833B-4E79-8AF1-7F3F2B5C796A}"
    Floor="{2F228CF6-6E46-4929-9791-B763DA4EBB3A}"
    Room="{E805D3A3-4C33-4CFA-A9A8-C588CBAFDD04}"
/>
```

### Wichtige Felder

| Feld | Typ | Beschreibung | Beispiel |
|------|-----|--------------|----------|
| **GUID** | UUID | Eindeutige ID der Fläche | `{2819422A-7650-404A-BCE8-C355A4FE3E9C}` |
| **Area** | Float | Fläche in m² | `15.492396` |
| **Neigungswinkel** | Float | Neigung in Grad (0=horizontal, 90=vertikal) | `90.00` |
| **Uvalue** | Float | U-Wert in W/(m²K) | `0.000000` |
| **Type** | Enum | Flächentyp | `Wall`, `Roof`, `Floor`, `Ceiling`, `Window`, `Door` |
| **Orientation** | Enum | Himmelsrichtung | `N`, `S`, `E`, `W`, `H` (horizontal) |
| **OrientationAngle** | Float | Azimut in Grad | `270.00` (West) |
| **Opposite** | Enum | Angrenzend an | `Aussenluft`, `Erdreich`, `Raum` |
| **Code** | String | Bauteil-Code | `WA` (Außenwand), `WI` (Innenwand), `DA` (Dach) |
| **CadElem** | UUID | Link zu CAD-Element (IFC?) | `{674608B0-...}` |

---

## 🔗 MAPPING: EVEBI → IFC

### Problem: Kein direkter Link!

**EVEBI hat:**
- `Face.GUID`: EVEBI-interne GUID
- `Face.CadElem`: UUID, aber **nicht IFC-GUID!**

**IFC hat:**
- `IFCWALLSTANDARDCASE.GlobalId`: IFC-GUID (z.B. `1ybs9cI0P0uhJtYtcGuM9Q`)

**→ Kein automatisches Mapping möglich!**

---

## 🎯 MAPPING-STRATEGIE

### Option 1: Geometrie-basiertes Matching

**Algorithmus:**
```python
def match_evebi_to_ifc(evebi_faces, ifc_elements):
    matches = []
    
    for evebi_face in evebi_faces:
        for ifc_elem in ifc_elements:
            # Vergleiche:
            # 1. Fläche (±5% Toleranz)
            # 2. Orientierung (±10° Toleranz)
            # 3. Typ (Wall, Roof, etc.)
            
            if (
                abs(evebi_face.area - ifc_elem.area) / evebi_face.area < 0.05
                and abs(evebi_face.orientation - ifc_elem.orientation) < 10
                and evebi_face.type == ifc_elem.type
            ):
                matches.append({
                    'evebi_guid': evebi_face.guid,
                    'ifc_guid': ifc_elem.guid,
                    'confidence': calculate_confidence(...)
                })
    
    return matches
```

**Vorteile:**
- ✅ Automatisch (keine manuelle Arbeit)
- ✅ Robust gegen kleine Abweichungen

**Nachteile:**
- ⚠️ Kann falsch matchen bei ähnlichen Flächen
- ⚠️ Confidence Score nötig

---

### Option 2: Manuelles Mapping (UI)

**UI-Konzept:**
```
┌─────────────────────────────────────────────────────────────┐
│ EVEBI Faces              │  IFC Elements                    │
├─────────────────────────────────────────────────────────────┤
│ ☐ Außenwand Süd          │  ☐ Wall_001 (GUID: 1ybs9c...)   │
│   Area: 15.49 m²         │     Area: 15.50 m²               │
│   Orientation: W (270°)  │     Orientation: W (270°)        │
│   U-Value: 1.2 W/(m²K)   │                                  │
│                          │                                  │
│ ☐ Außenwand Nord         │  ☐ Wall_002 (GUID: 0wsGtp...)   │
│   Area: 29.00 m²         │     Area: 28.95 m²               │
│   Orientation: N (0°)    │     Orientation: N (0°)          │
│   U-Value: 1.2 W/(m²K)   │                                  │
│                          │                                  │
│ [Auto-Match (Geometry)]  │  [Save Mapping]                  │
└─────────────────────────────────────────────────────────────┘
```

**Workflow:**
1. Parser extrahieren beide Listen
2. Auto-Match schlägt Matches vor (Confidence Score)
3. User überprüft und korrigiert
4. Mapping wird gespeichert

---

### Option 3: Hybrid (Auto + Manual)

**Best of Both:**
1. Geometrie-basiertes Matching (automatisch)
2. High-Confidence Matches (>90%) automatisch akzeptieren
3. Low-Confidence Matches (<90%) manuell überprüfen

---

## 📊 EVEBI DATEN-EXTRAKTION

### Face Types

| Type | Code | Beschreibung | Opposite |
|------|------|--------------|----------|
| **Wall** | `WA` | Außenwand | `Aussenluft` |
| **Wall** | `WI` | Innenwand | `Raum` |
| **Roof** | `DA` | Dach | `Aussenluft` |
| **Floor** | `KE` | Kellerdecke/Bodenplatte | `Erdreich` |
| **Ceiling** | `DI` | Decke (innen) | `Raum` |
| **Window** | `F` | Fenster | `Aussenluft` |
| **Door** | `T` | Tür | - |

### Orientation Mapping

| EVEBI | Angle | IFC | DIN18599 |
|-------|-------|-----|----------|
| `N` | 0° | North | Nord |
| `E` | 90° | East | Ost |
| `S` | 180° | South | Süd |
| `W` | 270° | West | West |
| `H` | - | Horizontal | Horizontal |

---

## 🔧 PARSER IMPLEMENTATION

### Python Parser (Pseudocode)

```python
import xml.etree.ElementTree as ET
from typing import List, Dict

class EVEBIFace:
    def __init__(self, elem):
        self.guid = elem.get('GUID')
        self.area = float(elem.get('Area'))
        self.inclination = float(elem.get('Neigungswinkel'))
        self.u_value = float(elem.get('Uvalue'))
        self.type = elem.get('Type')
        self.orientation = elem.get('Orientation')
        self.orientation_angle = float(elem.get('OrientationAngle', 0))
        self.opposite = elem.get('Opposite')
        self.code = elem.get('Code')
        self.cad_elem = elem.get('CadElem')
        self.floor_ref = elem.get('Floor')
        self.room_ref = elem.get('Room')

def parse_evebi_xml(file_path: str) -> Dict:
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    result = {
        'project': {},
        'buildings': [],
        'faces': []
    }
    
    # Parse Project
    project = root.find('Project')
    result['project'] = {
        'uid': project.get('UID'),
        'name': project.get('Name'),
        'description': project.get('Description')
    }
    
    # Parse Buildings
    for building in root.findall('.//Building'):
        building_data = {
            'uid': building.get('UID'),
            'name': building.get('Name'),
            'floors': []
        }
        
        # Parse Floors
        for floor in building.findall('.//Floor'):
            floor_data = {
                'uid': floor.get('UID'),
                'name': floor.get('Description'),
                'level': floor.get('Level'),
                'rooms': []
            }
            
            # Parse Rooms
            for room in floor.findall('.//Room'):
                room_data = {
                    'uid': room.get('UID'),
                    'name': room.get('Description'),
                    'faces': []
                }
                
                # Parse Faces
                for face_elem in room.findall('.//Face'):
                    face = EVEBIFace(face_elem)
                    room_data['faces'].append(face)
                    result['faces'].append(face)
                
                floor_data['rooms'].append(room_data)
            
            building_data['floors'].append(floor_data)
        
        result['buildings'].append(building_data)
    
    return result

def extract_external_faces(evebi_data: Dict) -> List[EVEBIFace]:
    """Extrahiert nur Außenbauteile (relevant für DIN18599)"""
    external_faces = []
    
    for face in evebi_data['faces']:
        if face.opposite in ['Aussenluft', 'Erdreich']:
            external_faces.append(face)
    
    return external_faces
```

---

## 📋 SIDECAR MAPPING

### Mapping-Datei (JSON)

```json
{
  "mapping_version": "1.0",
  "created_at": "2026-04-01T13:00:00Z",
  "ifc_file": "DIN18599TestIFCv2.ifc",
  "evebi_file": "DIN18599Test.xml",
  "mappings": [
    {
      "evebi_guid": "{2819422A-7650-404A-BCE8-C355A4FE3E9C}",
      "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
      "confidence": 0.95,
      "method": "geometry_match",
      "verified": true,
      "notes": "Außenwand West, automatisch gematched"
    },
    {
      "evebi_guid": "{0618F966-72F9-43F3-8655-2A3DFCDCDEC8}",
      "ifc_guid": "0wsGtpUkT56hELnVLS8x9z",
      "confidence": 0.87,
      "method": "manual",
      "verified": true,
      "notes": "Außenwand Nord, manuell korrigiert"
    }
  ]
}
```

---

## ✅ NÄCHSTE SCHRITTE

### Phase 1: Parser Implementation
1. ✅ EVEBI XML Parser (Python)
2. ✅ IFC Parser (ifcopenshell)
3. ✅ Geometrie-basiertes Matching

### Phase 2: Mapping Tool (UI)
1. Mapping-Vorschau (EVEBI + IFC Listen)
2. Auto-Match mit Confidence Score
3. Manuelles Korrektur-Interface
4. Mapping speichern

### Phase 3: Sidecar Generator
1. Mapping laden
2. EVEBI Daten + IFC GUIDs kombinieren
3. Sidecar JSON generieren

---

**Status:** ✅ EVEBI Format analysiert, Parser-Strategie definiert  
**Bereit für:** Parser Implementation + Mapping Tool
