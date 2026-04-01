# Workflow FINAL (Revised): CASCADOS → IFC + XML → DIN18599 Sidecar

**Datum:** 01.04.2026  
**Status:** FINAL - Basierend auf Real-World Constraints

---

## 🎯 KLARSTELLUNG: EVEBI Export-Optionen

**User-Feedback:**
> "Ich kann aus EVEBI keine XML exportieren. Ich kann höchstens die Projektdatei hochladen oder diese Text Datei."

**Verfügbare Dateien:**
1. ✅ `DIN18599Test.xml` - **CASCADOS Export** (bereits vorhanden!)
2. ✅ `DIN18599TestIFCv2.ifc` - **IFC-Geometrie** (CASCADOS)
3. ⚠️ `DIN18599Test.evex` - **EVEBI Projekt** (Binary, schwer zu parsen)
4. ⚠️ `DIN18599TestErg.txt` - **EVEBI Ergebnisse** (nur Berechnungsergebnisse, keine Bauteile)

---

## 💡 LÖSUNG: CASCADOS XML ist ausreichend!

**Wichtige Erkenntnis:**
Die `DIN18599Test.xml` (CASCADOS Export) enthält **bereits alle nötigen Daten**:
- ✅ Geometrie (Flächen, Orientierung, Neigung)
- ✅ Positionsnummern (`PosNo`)
- ✅ Raum-Struktur
- ✅ U-Werte (wenn in CASCADOS definiert)

**Was EVEBI hinzufügt:**
- Detaillierte Bilanzierung (Heizwärmebedarf, etc.)
- Berechnungsergebnisse nach DIN 18599
- Energieausweis-Daten

**→ Für Sidecar-Generierung reicht CASCADOS XML!**

---

## 🔄 WORKFLOW (Simplified)

### **Schritt 1: BIM-Modell erstellen (CASCADOS)**

**User erstellt:**
- Gebäude-Geometrie (Wände, Dächer, Räume)
- Geschosse (EG, OG, DG)
- Bauteile mit **Positionsnummern** (001, 002, 003, ...)
- U-Werte (optional, kann auch später ergänzt werden)

**Export:**
```
CASCADOS → Export → DIN18599 XML
CASCADOS → Export → IFC2x3
```

**Output:**
- `DIN18599Test.xml` (CASCADOS Export mit Bauteilen + PosNo)
- `DIN18599TestIFCv2.ifc` (3D-Geometrie mit PosNo)

---

### **Schritt 2: Energetische Bilanzierung (EVEBI) - Optional**

**User:**
1. Erstellt neues EVEBI-Projekt
2. Importiert `DIN18599Test.xml` (CASCADOS Export)
3. Ergänzt fehlende Daten (falls nötig)
4. Berechnet Energiebedarf nach DIN 18599

**Output:**
- `DIN18599Test.evex` (EVEBI Projekt)
- `DIN18599TestErg.txt` (Berechnungsergebnisse)

**Wichtig:** EVEBI-Daten sind **optional** für Sidecar-Generierung!

---

### **Schritt 3: DIN18599 Sidecar generieren (DWEapp)**

**Input:**
- `DIN18599TestIFCv2.ifc` (Geometrie)
- `DIN18599Test.xml` (CASCADOS Export mit Bauteilen)

**Parser:**
1. **IFC Parser:**
   ```python
   ifc_elements = parse_ifc(ifc_file)
   # Extrahiert:
   # - IFC-GUID: '1ybs9cI0P0uhJtYtcGuM9Q'
   # - PosNo: '001'
   # - Type: 'IFCWALLSTANDARDCASE'
   ```

2. **CASCADOS XML Parser:**
   ```python
   cascados_faces = parse_cascados_xml(xml_file)
   # Extrahiert:
   # - Face-GUID: '{2819422A-7650-404A-BCE8-C355A4FE3E9C}'
   # - PosNo: '001'
   # - Area: 15.49 m²
   # - Orientation: 270° (West)
   # - Inclination: 90° (vertikal)
   # - U-Value: 1.2 W/(m²K)
   ```

3. **Mapping (PosNo-basiert):**
   ```python
   mapping = {}
   for ifc_elem in ifc_elements:
       for cascados_face in cascados_faces:
           if ifc_elem.posno == cascados_face.posno:
               mapping[ifc_elem.guid] = cascados_face
   ```

4. **Sidecar Generator:**
   ```python
   sidecar = {
       "meta": {
           "mode": "IFC_LINKED",
           "ifc_file": "DIN18599TestIFCv2.ifc",
           "cascados_source": "DIN18599Test.xml"
       },
       "envelope": {
           "walls_external": [
               {
                   "id": "wall_001",
                   "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
                   "cascados_guid": "{2819422A-...}",
                   "posno": "001",
                   "area": 15.49,
                   "orientation": 270,
                   "u_value_undisturbed": 1.2
               }
           ]
       }
   }
   ```

**Output:** `DIN18599Test.din18599.json` (Sidecar)

---

## 📐 DATENFLUSS-DIAGRAMM (Simplified)

```
┌─────────────────────────────────────────────────────────────┐
│ CASCADOS (BIM-Software)                                     │
│ - Gebäude-Modell erstellen                                  │
│ - Positionsnummern vergeben (001, 002, ...)                 │
│ - U-Werte definieren (optional)                             │
└─────────────────────────────────────────────────────────────┘
                    │
                    ├─────────────────┬─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────────┐  ┌──────────────┐  ┌──────────────┐
        │ DIN18599Test.xml  │  │ IFC-Datei    │  │ Projekt-Datei│
        │ (CASCADOS Export) │  │ (Geometrie)  │  │ (.cad)       │
        │ + PosNo           │  │ + PosNo      │  │              │
        │ + U-Werte         │  │              │  │              │
        └───────────────────┘  └──────────────┘  └──────────────┘
                    │                 │
                    │                 │
        ┌───────────┴─────────────────┴───────────┐
        │ Optional: EVEBI                         │
        │ - Import XML                            │
        │ - Bilanzierung                          │
        │ - Ergebnisse (.txt)                     │
        └─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │ DWEapp Parser     │
        │ - IFC Parser      │
        │ - CASCADOS Parser │
        │ - PosNo Mapping   │
        └───────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │ Sidecar JSON      │
        │ (DIN18599 Format) │
        │ + IFC-Links       │
        └───────────────────┘
```

---

## 🔗 CASCADOS XML STRUKTUR

### Face Element (CASCADOS Export)

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

**Wichtige Felder:**
- `GUID`: CASCADOS-interne GUID
- `PosNo`: **Positionsnummer** (Link zu IFC!)
- `Area`: Fläche in m²
- `Neigungswinkel`: Neigung in Grad
- `Uvalue`: U-Wert in W/(m²K)
- `Orientation`: Himmelsrichtung (N, S, E, W, H)
- `OrientationAngle`: Azimut in Grad
- `Type`: Bauteil-Typ (Wall, Roof, Floor, etc.)
- `Opposite`: Angrenzend an (Aussenluft, Erdreich, Raum)

---

## 🔧 PARSER IMPLEMENTATION

### CASCADOS XML Parser (Python)

```python
import xml.etree.ElementTree as ET
from typing import List, Dict

class CASCADOSFace:
    def __init__(self, elem):
        self.guid = elem.get('GUID')
        self.posno = elem.get('PosNo')
        self.area = float(elem.get('Area', 0))
        self.inclination = float(elem.get('Neigungswinkel', 0))
        self.u_value = float(elem.get('Uvalue', 0))
        self.type = elem.get('Type')
        self.orientation = elem.get('Orientation')
        self.orientation_angle = float(elem.get('OrientationAngle', 0))
        self.opposite = elem.get('Opposite')
        self.code = elem.get('Code')
        self.cad_elem = elem.get('CadElem')
        self.floor_ref = elem.get('Floor')
        self.room_ref = elem.get('Room')

def parse_cascados_xml(file_path: str) -> Dict:
    """Parst CASCADOS XML Export"""
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
                    face = CASCADOSFace(face_elem)
                    room_data['faces'].append(face)
                    result['faces'].append(face)
                
                floor_data['rooms'].append(room_data)
            
            building_data['floors'].append(floor_data)
        
        result['buildings'].append(building_data)
    
    return result

def extract_external_faces(cascados_data: Dict) -> List[CASCADOSFace]:
    """Extrahiert nur Außenbauteile (relevant für DIN18599)"""
    external_faces = []
    
    for face in cascados_data['faces']:
        if face.opposite in ['Aussenluft', 'Erdreich']:
            external_faces.append(face)
    
    return external_faces
```

---

## 📋 SIDECAR GENERATOR (Simplified)

```python
def generate_sidecar_from_cascados(
    ifc_file_path: str,
    cascados_xml_path: str,
    output_path: str
) -> dict:
    """Generiert DIN18599 Sidecar JSON aus CASCADOS XML + IFC"""
    
    # 1. Parse IFC
    ifc_elements = parse_ifc_elements(ifc_file_path)
    
    # 2. Parse CASCADOS XML
    cascados_data = parse_cascados_xml(cascados_xml_path)
    cascados_faces = extract_external_faces(cascados_data)
    
    # 3. Mapping via PosNo
    mapping_result = map_ifc_to_cascados(ifc_elements, cascados_faces)
    
    # 4. Sidecar JSON erstellen
    sidecar = {
        "meta": {
            "schema_version": "2.1",
            "mode": "IFC_LINKED",
            "ifc_file": os.path.basename(ifc_file_path),
            "cascados_source": os.path.basename(cascados_xml_path),
            "generated_at": datetime.now().isoformat(),
            "mapping_stats": mapping_result['stats']
        },
        "envelope": {
            "walls_external": [],
            "roofs": [],
            "floors": []
        }
    }
    
    # 5. Envelope befüllen
    for ifc_guid, match in mapping_result['mapping'].items():
        ifc_elem = match['ifc']
        cascados_face = match['cascados']
        
        element = {
            "id": f"{cascados_face.code.lower()}_{cascados_face.posno}",
            "ifc_guid": ifc_guid,
            "cascados_guid": cascados_face.guid,
            "posno": cascados_face.posno,
            "name": ifc_elem['name'],
            "area": cascados_face.area,
            "orientation": cascados_face.orientation_angle,
            "inclination": cascados_face.inclination,
            "u_value_undisturbed": cascados_face.u_value,
            "boundary_condition": "EXTERNAL" if cascados_face.opposite == "Aussenluft" else "GROUND"
        }
        
        # Kategorisierung
        if cascados_face.type == 'Wall':
            sidecar['envelope']['walls_external'].append(element)
        elif cascados_face.type == 'Roof':
            sidecar['envelope']['roofs'].append(element)
        elif cascados_face.type == 'Floor':
            sidecar['envelope']['floors'].append(element)
    
    # 6. Speichern
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sidecar, f, indent=2, ensure_ascii=False)
    
    return sidecar
```

---

## ✅ VORTEILE DIESER LÖSUNG

### 1. **Einfacher Workflow**
- ✅ Nur CASCADOS-Daten nötig (XML + IFC)
- ✅ EVEBI ist optional (nur für Bilanzierung)
- ✅ Keine Binary-Parser nötig (.evex)

### 2. **Vollständige Daten**
- ✅ Geometrie aus IFC
- ✅ Bauteile + U-Werte aus CASCADOS XML
- ✅ PosNo-Mapping funktioniert

### 3. **Flexibilität**
- ✅ U-Werte können in CASCADOS definiert werden
- ✅ Oder später in DWEapp ergänzt werden
- ✅ EVEBI-Ergebnisse können optional hinzugefügt werden

---

## 🚀 NÄCHSTE SCHRITTE

### Phase 1: Parser Implementation (2-3h)
1. ✅ IFC Parser (ifcopenshell) - bereits spezifiziert
2. ✅ CASCADOS XML Parser (xml.etree) - neu spezifiziert
3. ✅ PosNo Mapping - bleibt gleich
4. ✅ Sidecar Generator - vereinfacht

### Phase 2: Testing (1h)
1. Test mit Real-World Beispiel (bereits vorhanden!)
2. Validierung der Mapping-Qualität
3. Edge Cases prüfen

### Phase 3: Integration (2h)
1. CLI Tool
2. DWEapp Integration
3. Optional: EVEBI-Ergebnisse hinzufügen

---

**Status:** ✅ Workflow finalisiert, Parser-Strategie angepasst  
**Bereit für:** Implementation mit CASCADOS XML statt EVEBI!
