# Use-Case FINAL (Correct): DIN18599 Sidecar System

**Datum:** 01.04.2026  
**Status:** FINAL - Basierend auf korrigiertem Verständnis

---

## 🎯 DAS PROBLEM

**CASCADOS XML enthält:**
- ✅ Geometrie (Flächen, Orientierung)
- ✅ Positionsnummern (PosNo)
- ❌ **KEINE U-Werte** (nur Platzhalter mit 0.0)
- ❌ **KEINE energetischen Daten**

**→ CASCADOS XML alleine reicht NICHT aus!**

---

## 💡 DIE RICHTIGE LÖSUNG

### **Konzept: Pluggable Parser System**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. IFC (Geometrie)                                          │
│    - 3D-Modell                                              │
│    - Wände, Dächer, Räume                                   │
│    - IFC-GUIDs                                              │
│    - Positionsnummern (optional)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Energetische Daten (Pluggable Parser)                   │
│    ┌─────────────────────────────────────────────────────┐ │
│    │ Parser A: EVEBI (.evex Binary)                      │ │
│    │ - U-Werte                                           │ │
│    │ - Konstruktionen                                    │ │
│    │ - Berechnungsergebnisse                            │ │
│    └─────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────┐ │
│    │ Parser B: Hottgenroth (später)                      │ │
│    │ - Andere Datenstruktur                             │ │
│    └─────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────┐ │
│    │ Parser C: Dämmwerk (später)                         │ │
│    └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. DIN18599 Sidecar JSON                                    │
│    - IFC-Links (Geometrie)                                  │
│    - Energetische Daten (aus Parser)                        │
│    - Editierbar im Viewer                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Verwendung                                               │
│    - Viewer (3D + Daten anzeigen/editieren)                 │
│    - Export zu anderen Tools (Hottgenroth, etc.)            │
│    - Berechnung (DIN18599 Engine)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 WORKFLOW

### **Phase 1: Import (IFC + EVEBI → Sidecar)**

```
1. User lädt hoch:
   ├─→ IFC-Datei (Geometrie)
   └─→ EVEBI .evex (Energetische Daten)

2. DWEapp Parser:
   ├─→ IFC Parser: Extrahiert Geometrie
   ├─→ EVEBI Parser: Extrahiert U-Werte, Konstruktionen
   └─→ Mapping: Verknüpft IFC ↔ EVEBI (via PosNo oder Geometrie)

3. Output:
   └─→ Sidecar JSON (IFC-Links + Energetische Daten)
```

### **Phase 2: Bearbeitung (Viewer)**

```
1. User öffnet Sidecar im Viewer:
   ├─→ 3D-Modell (aus IFC)
   └─→ Energetische Daten (aus Sidecar)

2. User editiert Daten:
   ├─→ U-Werte anpassen
   ├─→ Konstruktionen ändern
   └─→ Flächen korrigieren

3. Output:
   └─→ Aktualisierter Sidecar JSON
```

### **Phase 3: Export (Sidecar → andere Tools)**

```
1. User exportiert Sidecar:
   ├─→ Export zu Hottgenroth
   ├─→ Export zu Dämmwerk
   └─→ Export zu EVEBI (zurück)

2. DWEapp Exporter:
   └─→ Konvertiert Sidecar in Zielformat

3. Output:
   └─→ Format-spezifische Datei
```

---

## 📐 ARCHITEKTUR

### **1. IFC als Geometrie-Quelle**

**IFC enthält:**
- ✅ 3D-Geometrie (Wände, Dächer, Räume)
- ✅ IFC-GUIDs (eindeutige IDs)
- ✅ Hierarchie (Geschosse, Räume)
- ✅ Optional: Positionsnummern (Tag)

**IFC enthält NICHT:**
- ❌ U-Werte
- ❌ Konstruktionen
- ❌ Energetische Berechnungen

**→ IFC ist Read-Only für Geometrie!**

---

### **2. Pluggable Parser System**

**Parser-Interface:**
```python
class EnergyDataParser:
    def parse(self, file_path: str) -> EnergyData:
        """Parst energetische Daten aus beliebigem Format"""
        pass
    
    def extract_elements(self) -> List[Element]:
        """Extrahiert Bauteile mit energetischen Daten"""
        pass
    
    def get_mapping_hints(self) -> MappingHints:
        """Gibt Hinweise für Mapping zu IFC"""
        pass
```

**Implementierungen:**
- `EVEBIParser` - Parst .evex Binary
- `HottgenrothParser` - Parst Hottgenroth-Format (später)
- `DämmwerkParser` - Parst Dämmwerk-Format (später)

---

### **3. Mapping-Strategien**

**Strategie A: PosNo-basiert (wenn vorhanden)**
```python
if ifc_elem.posno and energy_elem.posno:
    if ifc_elem.posno == energy_elem.posno:
        mapping[ifc_elem.guid] = energy_elem
```

**Strategie B: Geometrie-basiert (Fallback)**
```python
if (
    abs(ifc_elem.area - energy_elem.area) / ifc_elem.area < 0.05
    and abs(ifc_elem.orientation - energy_elem.orientation) < 10
    and ifc_elem.type == energy_elem.type
):
    mapping[ifc_elem.guid] = energy_elem
```

**Strategie C: Manuell (UI)**
```
User verknüpft manuell in UI:
IFC Element → Energy Element
```

---

### **4. Sidecar JSON (Single Source of Truth)**

```json
{
  "meta": {
    "schema_version": "2.1",
    "mode": "IFC_LINKED",
    "ifc_file": "building.ifc",
    "energy_data_source": {
      "type": "EVEBI",
      "file": "building.evex",
      "imported_at": "2026-04-01T12:00:00Z"
    }
  },
  "envelope": {
    "walls_external": [
      {
        "id": "wall_001",
        "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
        "energy_source_ref": "EVEBI:{2819422A-...}",
        "area": 15.49,
        "orientation": 270,
        "inclination": 90,
        "u_value_undisturbed": 1.2,
        "construction": {
          "name": "Mauerwerk 365mm",
          "layers": [
            {"material": "Putz", "thickness": 0.015, "lambda": 0.87},
            {"material": "Mauerwerk", "thickness": 0.365, "lambda": 0.99},
            {"material": "Putz", "thickness": 0.015, "lambda": 0.87}
          ]
        },
        "editable": true,
        "last_modified": "2026-04-01T13:00:00Z"
      }
    ]
  }
}
```

**Wichtig:**
- ✅ IFC-GUID für Geometrie-Link
- ✅ `energy_source_ref` für Rückverfolgbarkeit
- ✅ `editable: true` → User kann Daten im Viewer ändern
- ✅ `last_modified` → Audit Trail

---

## 🔧 KOMPONENTEN

### **1. IFC Parser**
```python
# /opt/din18599-ifc/parsers/ifc_parser.py

def parse_ifc_geometry(ifc_file: str) -> IFCGeometry:
    """
    Extrahiert Geometrie aus IFC:
    - Wände, Dächer, Böden
    - IFC-GUIDs
    - Flächen (berechnet)
    - Orientierung (berechnet)
    - Optional: PosNo (Tag)
    """
    pass
```

### **2. EVEBI Parser**
```python
# /opt/din18599-ifc/parsers/evebi_parser.py

def parse_evebi_binary(evex_file: str) -> EVEBIData:
    """
    Parst EVEBI .evex Binary:
    - U-Werte
    - Konstruktionen
    - Flächen
    - Optional: PosNo
    
    Challenge: Binary Format, keine Dokumentation
    Lösung: Reverse Engineering oder EVEBI API
    """
    pass
```

### **3. Mapping Engine**
```python
# /opt/din18599-ifc/core/mapper.py

def map_ifc_to_energy(
    ifc_geometry: IFCGeometry,
    energy_data: EnergyData,
    strategy: MappingStrategy = 'auto'
) -> Mapping:
    """
    Verknüpft IFC-Geometrie mit energetischen Daten:
    - Auto: PosNo → Geometrie → Manuell
    - PosNo: Nur PosNo-basiert
    - Geometry: Nur Geometrie-basiert
    - Manual: User-gesteuert
    """
    pass
```

### **4. Sidecar Generator**
```python
# /opt/din18599-ifc/core/generator.py

def generate_sidecar(
    ifc_geometry: IFCGeometry,
    energy_data: EnergyData,
    mapping: Mapping
) -> SidecarJSON:
    """
    Generiert DIN18599 Sidecar JSON:
    - Kombiniert IFC + Energy Data
    - Fügt Metadata hinzu
    - Validiert gegen Schema
    """
    pass
```

### **5. Viewer (React + Three.js)**
```typescript
// /opt/din18599-ifc/viewer/src/components/Viewer.tsx

interface ViewerProps {
  ifcFile: string
  sidecar: DIN18599Data
  onEdit: (element: Element, changes: Partial<Element>) => void
}

// Features:
// - 3D-Modell (IFC.js)
// - Bauteil-Selektion
// - Daten-Anzeige (U-Werte, Konstruktionen)
// - Inline-Editing
// - Änderungen speichern
```

### **6. Exporter (Pluggable)**
```python
# /opt/din18599-ifc/exporters/base.py

class Exporter:
    def export(self, sidecar: SidecarJSON, output_path: str):
        """Exportiert Sidecar in Zielformat"""
        pass

# Implementierungen:
# - HottgenrothExporter
# - DämmwerkExporter
# - EVEBIExporter (zurück)
```

---

## 🎯 MVP SCOPE

### **Phase 1: Import (MVP)**
1. ✅ IFC Parser (Geometrie)
2. ✅ EVEBI Parser (.evex Binary) - **Challenge!**
3. ✅ Mapping Engine (PosNo + Geometrie)
4. ✅ Sidecar Generator

### **Phase 2: Viewer (MVP)**
1. ✅ 3D-Modell anzeigen (IFC.js)
2. ✅ Bauteile selektieren
3. ✅ Daten anzeigen (U-Werte)
4. ⚠️ Inline-Editing (später)

### **Phase 3: Export (später)**
1. ⚠️ Hottgenroth Exporter
2. ⚠️ Dämmwerk Exporter

---

## 🚧 HERAUSFORDERUNGEN

### **1. EVEBI Binary Format (.evex)**

**Problem:** 
- .evex ist Binary-Format
- Keine öffentliche Dokumentation
- Keine offizielle API

**Lösungen:**
1. **Reverse Engineering** (schwierig, zeitaufwändig)
2. **EVEBI API** (falls vorhanden)
3. **EVEBI Export** (falls XML-Export möglich)
4. **Manuelle Eingabe** (Fallback)

**→ Müssen wir mit EVEBI-Hersteller klären!**

---

### **2. Mapping ohne PosNo**

**Problem:**
- Nicht alle IFC-Dateien haben PosNo
- Nicht alle EVEBI-Daten haben PosNo

**Lösung:**
- Geometrie-basiertes Matching (Fläche + Orientierung)
- Confidence Score
- Manuelle Korrektur in UI

---

### **3. Daten-Editierung**

**Problem:**
- IFC ist Read-Only
- Änderungen nur in Sidecar

**Lösung:**
- Sidecar als Single Source of Truth
- IFC nur für Geometrie-Referenz
- Viewer zeigt Sidecar-Daten (nicht IFC-Daten)

---

## ✅ NÄCHSTE SCHRITTE

### **Sofort:**
1. **EVEBI Binary Format klären**
   - Gibt es eine API?
   - Gibt es Dokumentation?
   - Können wir XML exportieren?

2. **MVP definieren**
   - Was brauchen wir JETZT?
   - Was kann später kommen?

### **Dann:**
1. IFC Parser implementieren
2. EVEBI Parser implementieren (je nach Lösung)
3. Mapping Engine implementieren
4. Sidecar Generator implementieren
5. Viewer (Basic) implementieren

---

**Status:** ✅ Use-Case korrekt definiert  
**Blocker:** EVEBI Binary Format (.evex) - Wie parsen?  
**Nächster Schritt:** EVEBI Format-Frage klären
