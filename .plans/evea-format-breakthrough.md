# EVEBI .evea Format - BREAKTHROUGH!

**Datum:** 01.04.2026  
**Status:** ✅ SOLVED - Kein Reverse Engineering nötig!

---

## 🎉 ENTDECKUNG

**`.evea` ist ein ZIP-Archiv mit XML!**

```bash
$ python3 -m zipfile -l DIN18599Test_260401.evea

File Name                                             Modified             Size
blob_{...}.jpg                                   2026-04-01 15:29:20        48945
projekt.xml                                      2026-04-01 15:29:20       550744  ← HIER!
file-hashes                                      2026-04-01 15:29:20         1009
```

---

## 📋 INHALT

### **1. projekt.xml (550 KB)**
- ✅ Vollständiges EVEBI-Projekt
- ✅ U-Werte
- ✅ Konstruktionen (Schichten + λ-Werte)
- ✅ Materialien
- ✅ Bauteile
- ✅ Berechnungsergebnisse

### **2. Bilder (JPG/PNG)**
- Fotos, Pläne, etc.

### **3. file-hashes**
- Checksums für Integrität

---

## 🔍 XML-STRUKTUR

### **Beispiel: Material mit λ-Wert**

```xml
<lambda unit="W/mK">1.0000000</lambda>
<lambda unit="W/mK">0.5500000</lambda>
<lambda unit="W/mK">1.4000000</lambda>
<lambda unit="W/mK">0.0350000</lambda>  <!-- Dämmung -->
```

### **Beispiel: Konstruktion**

```xml
<item GUID="{...}">
  <name>Außenwand</name>
  <schichten>
    <schicht>
      <material>Putz</material>
      <dicke unit="m">0.015</dicke>
      <lambda unit="W/mK">0.87</lambda>
    </schicht>
    <schicht>
      <material>Mauerwerk</material>
      <dicke unit="m">0.365</dicke>
      <lambda unit="W/mK">0.99</lambda>
    </schicht>
  </schichten>
  <u_wert unit="W/(m²K)">1.2</u_wert>
</item>
```

---

## 🔧 PARSER IMPLEMENTATION

### **Python Parser (Einfach!)**

```python
import zipfile
import xml.etree.ElementTree as ET

def parse_evea(evea_file_path: str) -> dict:
    """
    Parst EVEBI .evea Archiv
    
    1. Entpackt ZIP
    2. Liest projekt.xml
    3. Extrahiert Bauteile + U-Werte
    """
    
    # 1. ZIP entpacken
    with zipfile.ZipFile(evea_file_path, 'r') as zip_ref:
        # projekt.xml extrahieren
        xml_content = zip_ref.read('projekt.xml')
    
    # 2. XML parsen
    root = ET.fromstring(xml_content)
    
    # 3. Daten extrahieren
    result = {
        'project': extract_project_info(root),
        'constructions': extract_constructions(root),
        'elements': extract_elements(root),
        'results': extract_results(root)
    }
    
    return result

def extract_constructions(root):
    """Extrahiert Konstruktionen mit U-Werten"""
    constructions = []
    
    for item in root.findall('.//Konstruktion/item'):
        construction = {
            'guid': item.get('GUID'),
            'name': item.findtext('name'),
            'u_value': float(item.findtext('u_wert', 0)),
            'layers': []
        }
        
        for layer in item.findall('.//schicht'):
            construction['layers'].append({
                'material': layer.findtext('material'),
                'thickness': float(layer.findtext('dicke', 0)),
                'lambda': float(layer.findtext('lambda', 0))
            })
        
        constructions.append(construction)
    
    return constructions

def extract_elements(root):
    """Extrahiert Bauteile (Wände, Dächer, etc.)"""
    elements = []
    
    for item in root.findall('.//Bauteil/item'):
        element = {
            'guid': item.get('GUID'),
            'name': item.findtext('name'),
            'type': item.findtext('type'),
            'area': float(item.findtext('flaeche', 0)),
            'orientation': float(item.findtext('orientierung', 0)),
            'u_value': float(item.findtext('u_wert', 0)),
            'construction_ref': item.findtext('konstruktion_ref')
        }
        
        elements.append(element)
    
    return elements
```

---

## 🔗 MAPPING-STRATEGIE

### **Option 1: GUID-Mapping (wenn vorhanden)**

```python
# EVEBI XML enthält möglicherweise IFC-GUIDs
for element in evebi_elements:
    if element.ifc_guid:
        mapping[element.ifc_guid] = element
```

### **Option 2: Name-Mapping**

```python
# Matching via Bauteil-Name
ifc_name = "Außenwand Süd"
evebi_name = "Außenwand Süd"

if ifc_name == evebi_name:
    mapping[ifc_guid] = evebi_element
```

### **Option 3: Geometrie-Matching (Fallback)**

```python
# Matching via Fläche + Orientierung
if (
    abs(ifc_area - evebi_area) / ifc_area < 0.05
    and abs(ifc_orientation - evebi_orientation) < 10
):
    mapping[ifc_guid] = evebi_element
```

---

## ✅ VORTEILE

1. ✅ **Kein Reverse Engineering** nötig
2. ✅ **Standard XML** - einfach zu parsen
3. ✅ **Vollständige Daten** - U-Werte, Konstruktionen, Materialien
4. ✅ **Schnell** - ZIP + XML Parser sind Standard-Libraries

---

## 🚀 NÄCHSTE SCHRITTE

### **Phase 1: Parser Implementation (2-3h)**

1. **EVEBI Parser**
   ```python
   # /opt/din18599-ifc/parsers/evebi_parser.py
   
   def parse_evea(evea_file: str) -> EVEBIData:
       # ZIP entpacken
       # XML parsen
       # Bauteile + U-Werte extrahieren
       pass
   ```

2. **IFC Parser**
   ```python
   # /opt/din18599-ifc/parsers/ifc_parser.py
   
   def parse_ifc(ifc_file: str) -> IFCGeometry:
       # Geometrie extrahieren
       # IFC-GUIDs
       # Flächen, Orientierung
       pass
   ```

3. **Mapping Engine**
   ```python
   # /opt/din18599-ifc/core/mapper.py
   
   def map_ifc_to_evebi(ifc_geometry, evebi_data):
       # GUID → Name → Geometrie
       # Confidence Score
       pass
   ```

4. **Sidecar Generator**
   ```python
   # /opt/din18599-ifc/core/generator.py
   
   def generate_sidecar(ifc_geometry, evebi_data, mapping):
       # Kombiniert IFC + EVEBI
       # Generiert Sidecar JSON
       pass
   ```

### **Phase 2: Testing (1h)**
- Test mit Real-World Daten (bereits vorhanden!)
- Validierung

### **Phase 3: CLI Tool (1h)**
```bash
python -m din18599_ifc.cli generate \
  --ifc building.ifc \
  --evebi building.evea \
  --output building.din18599.json
```

---

## 📊 WORKFLOW (Final)

```
┌─────────────────────────────────────┐
│ 1. User lädt hoch:                  │
│    - IFC-Datei                      │
│    - EVEBI .evea                    │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 2. Parser:                          │
│    - IFC Parser → Geometrie         │
│    - EVEBI Parser → U-Werte         │
│    - Mapping Engine → Verknüpfung   │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 3. Sidecar JSON:                    │
│    - IFC-Links (Geometrie)          │
│    - U-Werte (aus EVEBI)            │
│    - Konstruktionen (aus EVEBI)     │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ 4. Viewer:                          │
│    - 3D-Modell (IFC)                │
│    - Daten anzeigen/editieren       │
└─────────────────────────────────────┘
```

---

**Status:** ✅ Format analysiert, Parser-Strategie definiert  
**Bereit für:** Implementation!
